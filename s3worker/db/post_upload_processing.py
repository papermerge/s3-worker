"""
Process uploaded document after upload to storage.

It handles:
    1. For PDFs: Count pages, create page records
    2. For Images (PNG/JPEG/TIFF): Convert to PDF, upload, count pages, create page records
"""
import logging
from uuid import UUID
import tempfile
from pathlib import Path

import img2pdf
from sqlalchemy import select
from pikepdf import Pdf

from s3worker import utils, plib, types, client, db, config
from s3worker.db.orm import DocumentVersion
from s3worker.db.engine import Session
from s3worker.types import DocumentProcessingStatus, MimeType


settings = config.get_settings()
logger = logging.getLogger(__name__)


def get_page_count(abs_path: Path):
    page_count = 0

    with open(abs_path, 'rb') as f:
        pdf = Pdf.open(f)
        page_count = len(pdf.pages)
        pdf.close()

    return page_count


def process_pdf_document(
    db_session: Session,
    doc_id: UUID,
    ver_id: UUID,
    lang: str,
    version: DocumentVersion
):
    """Post upload processing for PDFs"""
    db.update_document_processing_status(
        db_session,
        doc_id,
        status=DocumentProcessingStatus.processing_pages.value
    )

    if not utils.make_sure_file_exists_for(
        doc_id=doc_id,
        docver_id=ver_id,
        file_name=version.file_name
    ):
        name = version.file_name
        msg = f"Failed to retrieve file locally {name=} {doc_id=} {ver_id=}"
        logger.error(msg)
        return

    original_path = plib.abs_docver_path(ver_id, version.file_name)

    page_count = get_page_count(original_path)

    logger.info(f"PDF has {page_count} pages")

    db.update_version_page_count(db_session, ver_id, page_count)

    # Create page records (use default lang if not available)
    db.create_pages_for_version(
        db_session,
        version_id=ver_id,
        page_count=page_count,
        lang=lang
    )

    # Mark as ready
    db.update_document_processing_status(
        db_session,
        doc_id,
        status=DocumentProcessingStatus.ready.value
    )

    logger.info(f"PDF processing complete for doc={doc_id}")


def process_non_pdf_document(
    db_session: Session,
    doc_id: UUID,
    ver_id: UUID,
    user_id: UUID,
    lang: str,
    version: DocumentVersion
):
    """Post upload processing for non PDFs"""
    db.update_document_processing_status(
        db_session,
        doc_id,
        status=DocumentProcessingStatus.converting.value
    )

    if not utils.make_sure_file_exists_for(
        doc_id=doc_id,
        docver_id=ver_id,
        file_name=version.file_name
    ):
        name = version.file_name
        msg = f"Failed to retrieve file locally {name=} {doc_id=} {ver_id=}"
        logger.error(msg)
        return

    original_path = plib.abs_docver_path(ver_id, version.file_name)

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
                created_by=user_id,
                lang=lang,
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

            with open(pdf_path, 'rb') as src,open(pdf_storage_path,'wb') as dst:
                dst.write(src.read())

            if settings.storage_backend != types.StorageBackend.LOCAL:
                # Upload to S3/R2
                logger.info(f"Uploading converted PDF to storage")
                s3_client = client.get_client()
                client.add_doc_ver(s3_client, pdf_ver_id)

            # Update original version page count

            db.update_version_page_count(db_session, ver_id, page_count)

            # Create page records for original version
            db.create_pages_for_version(
                db_session,
                version_id=ver_id,
                page_count=page_count
            )

            # Create page records for PDF version
            db.create_pages_for_version(
                db_session,
                version_id=pdf_ver_id,
                page_count=page_count
            )
            # Mark as ready
            db.update_document_processing_status(
                db_session,
                doc_id,
                status=DocumentProcessingStatus.ready.value
            )

            logger.info(f"Image processing complete for doc={doc_id}")
    except img2pdf.ImageOpenError as e:
        logger.error(f"Image conversion failed: {e}")
        db.update_document_processing_status(
            db_session,
            doc_id,
            status=DocumentProcessingStatus.failed.value,
            error=f"Image conversion failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during image processing: {e}")
        db.update_document_processing_status(
            db_session,
            doc_id,
            status=DocumentProcessingStatus.failed.value,
            error=f"Processing failed: {str(e)}"
        )
        raise
