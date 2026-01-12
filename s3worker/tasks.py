import logging
import uuid
import tempfile
from pathlib import Path
from uuid import UUID

import botocore.exceptions
import img2pdf
from pikepdf import Pdf
from sqlalchemy import select
from celery import shared_task

from s3worker import generate, client, db, plib, exc, utils, types
from s3worker.config import get_settings
from s3worker import constants as const
from s3worker.db.engine import Session
from s3worker.types import ImagePreviewSize, ImagePreviewStatus
from s3worker.types import MimeType, DocumentProcessingStatus
from s3worker.db.orm import DocumentVersion

settings = get_settings()
logger = logging.getLogger(__name__)
IMAGE_SIZES = (ImagePreviewSize.sm, ImagePreviewSize.md, ImagePreviewSize.lg, ImagePreviewSize.xl)



@shared_task(name=const.S3_WORKER_ADD_DOC_VER)
def add_doc_vers_task(doc_ver_ids: list[str]):
    logger.debug('Task started')
    client.add_doc_vers(doc_ver_ids)


@shared_task(name=const.S3_WORKER_REMOVE_DOC_VER)
def remove_doc_vers_task(doc_ver_ids: list[str]):
    logger.debug('Task started')
    try:
        client.remove_doc_vers(doc_ver_ids)
    except Exception as ex:
        logger.exception(ex)


@shared_task(name=const.S3_WORKER_REMOVE_DOC_THUMBNAIL)
def remove_doc_thumbnail_task(doc_id: str):
    logger.debug('Task started')
    try:
        client.remove_doc_thumbnail(uuid.UUID(doc_id))
    except Exception as ex:
        logger.exception(ex)


@shared_task(name=const.S3_WORKER_REMOVE_DOCS_THUMBNAIL)  # plural
def remove_docs_thumbnail_task(doc_ids: list[str]):  # multiple docs
    logger.debug('Task started')
    try:
        for doc_id in doc_ids:
            client.remove_doc_thumbnail(uuid.UUID(doc_id))
    except Exception as ex:
        logger.exception(ex)

@shared_task(name=const.S3_WORKER_REMOVE_PAGE_THUMBNAIL)
def remove_page_thumbnail_task(page_ids: list[str]):
    logger.debug('Task started')
    try:
        for page_id in page_ids:
            client.delete_page(uuid.UUID(page_id))
    except Exception as ex:
        logger.exception(ex)


@shared_task(
    name=const.S3_WORKER_GENERATE_DOC_THUMBNAIL,
    autoretry_for = (exc.S3DocumentNotFound,),
    # Wait for 10 seconds before starting each new try. At most retry 6 times.
    retry_kwargs = {"max_retries": 6, "countdown": 10},
)
def generate_doc_thumbnail_task(doc_id: str):
    """Generate thumbnail image and upload it to S3 storage"""
    logger.debug('Task started')

    with Session() as db_session:
        status = db.get_doc_img_preview_status(db_session, UUID(doc_id))
        if status is not None:
            # which means somebody else already started working on this
            # task
            return

        db.update_doc_img_preview_status(
            db_session,
            UUID(doc_id),
            status=ImagePreviewStatus.pending
        )

    try:
        with Session() as db_session:
            doc_ver = db.get_last_version(db_session, doc_id=UUID(doc_id))

        logger.debug(f"doc_ver.id = {doc_ver.id}")

        client.download_docver(
            docver_id=doc_ver.id,
            file_name=doc_ver.file_name
        )

        with Session() as db_session:
            thumb_path = generate.doc_thumbnail(db_session, UUID(doc_id))

        try:
            if settings.pm_storage_backend != types.StorageBackend.LOCAL:
                client.upload_file(thumb_path)  # upload to S3
            with Session() as db_session:
                db.update_doc_img_preview_status(
                    db_session,
                    UUID(doc_id),
                    status=ImagePreviewStatus.ready
                )

        except botocore.exceptions.BotoCoreError as e:
            with Session() as db_session:
                db.update_doc_img_preview_status(
                    db_session,
                    UUID(doc_id),
                    status=ImagePreviewStatus.failed,
                    error=str(e)
                )

    except Exception as ex:
        logger.exception(ex)


@shared_task(
    name="process_upload",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
def process_upload_task(document_id: str, document_version_id: str):
    """
    Process uploaded document after upload to storage.
    
    This task handles:
    1. For PDFs: Count pages, create page records
    2. For Images (PNG/JPEG/TIFF): Convert to PDF, upload, count pages, create page records
    
    Args:
        document_id: UUID of the document
        document_version_id: UUID of the document version (version 1 - the original)
    """

    doc_id = UUID(document_id)
    ver_id = UUID(document_version_id)
    
    logger.info(f"Starting document processing for doc={doc_id}, version={ver_id}")
    
    try:
        with Session() as db_session:
            # Get the document version
            version = db.get_document_version(db_session, ver_id)
            
            if version is None:
                logger.error(f"Document version {ver_id} not found")
                return
            
            # Update status to converting/processing
            if version.mime_type != MimeType.application_pdf.value:
                db.update_document_processing_status(
                    db_session,
                    doc_id,
                    status=DocumentProcessingStatus.converting.value
                )
            else:
                db.update_document_processing_status(
                    db_session,
                    doc_id,
                    status=DocumentProcessingStatus.processing_pages.value
                )
        
        # Download the original file from storage
        logger.info(f"Downloading original file: {version.file_name}")
        
        if not utils.make_sure_file_exists_for(
            doc_id=doc_id,
            docver_id=ver_id,
            file_name=version.file_name
        ):
            name=version.file_name
            msg = f"Failed to retrieve file locally {name=} {doc_id=} {ver_id=}"
            logger.error(msg)
            return
        
        original_path = plib.abs_docver_path(ver_id, version.file_name)
        
        if version.mime_type == MimeType.application_pdf.value:
            # ============================================================
            # PDF Processing (just count pages and create page records)
            # ============================================================
            logger.info(f"Processing PDF: {version.file_name}")
            
            with Session() as db_session:
                db.update_document_processing_status(
                    db_session,
                    doc_id,
                    status=DocumentProcessingStatus.processing_pages.value
                )
            
            # Count pages
            with open(original_path, 'rb') as f:
                pdf = Pdf.open(f)
                page_count = len(pdf.pages)
                pdf.close()
            
            logger.info(f"PDF has {page_count} pages")
            
            # Update version page count
            with Session() as db_session:
                db.update_version_page_count(db_session, ver_id, page_count)
            
            # Create page records (use default lang if not available)
            with Session() as db_session:
                db.create_pages_for_version(
                    db_session,
                    version_id=ver_id,
                    page_count=page_count,
                    lang="deu"  # Default language
                )
            
            # Mark as ready
            with Session() as db_session:
                db.update_document_processing_status(
                    db_session,
                    doc_id,
                    status=DocumentProcessingStatus.ready.value
                )
            
            logger.info(f"PDF processing complete for doc={doc_id}")
            
        else:
            # ============================================================
            # Image Processing (convert to PDF, then process)
            # ============================================================
            logger.info(f"Converting image to PDF: {version.file_name}")
            
            with Session() as db_session:
                db.update_document_processing_status(
                    db_session,
                    doc_id,
                    status=DocumentProcessingStatus.converting.value
                )
            
            # Convert image to PDF
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    pdf_filename = f"{version.file_name}.pdf"
                    pdf_path = Path(tmpdir) / pdf_filename
                    
                    # Convert using img2pdf
                    with open(original_path, 'rb') as img_file:
                        pdf_bytes = img2pdf.convert(img_file)
                    
                    # Write PDF to temp file
                    with open(pdf_path, 'wb') as pdf_file:
                        pdf_file.write(pdf_bytes)
                    
                    # Count pages in converted PDF
                    pdf = Pdf.open(pdf_path)
                    page_count = len(pdf.pages)
                    pdf.close()
                    
                    logger.info(f"Converted image has {page_count} page(s)")
                    
                    # Create version 2 for the PDF
                    with Session() as db_session:
                        # Get current document to find version count
                        stmt = select(DocumentVersion).where(
                            DocumentVersion.document_id == doc_id
                        ).order_by(DocumentVersion.number.desc()).limit(1)
                        last_ver = db_session.execute(stmt).scalar_one()
                        next_number = last_ver.number + 1
                        
                        pdf_version = db.create_document_version(
                            db_session,
                            document_id=doc_id,
                            number=next_number,
                            file_name=pdf_filename,
                            size=len(pdf_bytes),
                            mime_type=MimeType.application_pdf.value,
                            page_count=page_count,
                            is_original=False,
                            source_version_id=ver_id,
                            creation_reason="conversion"
                        )
                        
                        pdf_ver_id = pdf_version.id
                    
                    # Upload converted PDF to storage
                    # First, save to proper location
                    pdf_storage_path = plib.abs_docver_path(pdf_ver_id, pdf_filename)
                    pdf_storage_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(pdf_path, 'rb') as src, open(pdf_storage_path, 'wb') as dst:
                        dst.write(src.read())
                    
                    # Upload to S3/R2
                    logger.info(f"Uploading converted PDF to storage")
                    s3_client = client.get_client()
                    client.add_doc_ver(s3_client, pdf_ver_id)
                    
                    # Update original version page count
                    with Session() as db_session:
                        db.update_version_page_count(db_session, ver_id, page_count)
                    
                    # Create page records for original version
                    with Session() as db_session:
                        db.create_pages_for_version(
                            db_session,
                            version_id=ver_id,
                            page_count=page_count
                        )
                    
                    # Create page records for PDF version
                    with Session() as db_session:
                        db.create_pages_for_version(
                            db_session,
                            version_id=pdf_ver_id,
                            page_count=page_count
                        )
                    
                    # Mark as ready
                    with Session() as db_session:
                        db.update_document_processing_status(
                            db_session,
                            doc_id,
                            status=DocumentProcessingStatus.ready.value
                        )
                    
                    logger.info(f"Image processing complete for doc={doc_id}")
                    
            except img2pdf.ImageOpenError as e:
                logger.error(f"Image conversion failed: {e}")
                with Session() as db_session:
                    db.update_document_processing_status(
                        db_session,
                        doc_id,
                        status=DocumentProcessingStatus.failed.value,
                        error=f"Image conversion failed: {str(e)}"
                    )
                return
            except Exception as e:
                logger.error(f"Unexpected error during image processing: {e}")
                with Session() as db_session:
                    db.update_document_processing_status(
                        db_session,
                        doc_id,
                        status=DocumentProcessingStatus.failed.value,
                        error=f"Processing failed: {str(e)}"
                    )
                raise
                
    except Exception as ex:
        logger.exception(f"Fatal error processing document {doc_id}: {ex}")
        try:
            with Session() as db_session:
                db.update_document_processing_status(
                    db_session,
                    doc_id,
                    status=DocumentProcessingStatus.failed.value,
                    error=str(ex)
                )
        except Exception as db_ex:
            logger.error(f"Failed to update error status: {db_ex}")
        raise
