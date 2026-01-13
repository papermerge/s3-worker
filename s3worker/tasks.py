import logging
import uuid
from uuid import UUID

import botocore.exceptions
from celery import shared_task

from s3worker import generate, client, db, exc, types
from s3worker.config import get_settings
from s3worker import constants as const
from s3worker.db.engine import Session
from s3worker.db import post_upload_processing
from s3worker.types import ImagePreviewSize, ImagePreviewStatus
from s3worker.types import MimeType, DocumentProcessingStatus


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
            if settings.storage_backend != types.StorageBackend.LOCAL:
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
def process_upload_task(
    document_id: str,
    document_version_id: str,
    user_id: str,
    lang: str
):
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
            version = db.get_document_version(db_session, ver_id)
            
            if version is None:
                logger.error(f"Document version {ver_id} not found")
                return

            if version.mime_type == MimeType.application_pdf.value:
                post_upload_processing.process_pdf_document(
                    db_session,
                    doc_id=doc_id,
                    ver_id=ver_id,
                    lang=lang,
                    version=version,
                )
            else:
                post_upload_processing.process_non_pdf_document(
                    db_session,
                    doc_id=doc_id,
                    ver_id=ver_id,
                    lang=lang,
                    user_id=UUID(user_id),
                    version=version,
                )
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
