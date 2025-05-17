import logging
import time
import uuid
from uuid import UUID
from celery import shared_task
import botocore.exceptions
from random import randrange

from s3worker import generate, client, db
from s3worker.config import get_settings
from s3worker import constants as const
from s3worker import exc
from s3worker.db.engine import Session
from s3worker.config import FileServer


settings = get_settings()
logger = logging.getLogger(__name__)


@shared_task(name=const.S3_WORKER_ADD_DOC_VER)
def add_doc_vers_task(doc_ver_ids: list[str]):
    logger.debug('Task started')
    file_server = settings.papermerge__main__file_server
    if file_server == FileServer.S3_LOCAL_TEST:
        name = "PAPERMERGE__MAIN__FILE_SERVER"
        value = FileServer.S3_LOCAL_TEST
        logger.debug(
            f"Task skipped because {name}  is set to {value}"
        )
        return

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
        db.update_doc_img_preview_status(
            db_session,
            UUID(doc_id),
            status=const.ImagePreviewStatus.PENDING
        )

    if settings.papermerge__main__file_server == FileServer.S3_LOCAL_TEST:
        time.sleep(5 + randrange(10))

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
            if settings.papermerge__main__file_server != FileServer.S3_LOCAL_TEST:
                client.upload_file(thumb_path)  # upload to S3
            with Session() as db_session:
                db.update_doc_img_preview_status(
                    db_session,
                    UUID(doc_id),
                    status=const.ImagePreviewStatus.READY
                )

        except botocore.exceptions.BotoCoreError as e:
            with Session() as db_session:
                db.update_doc_img_preview_status(
                    db_session,
                    UUID(doc_id),
                    status=const.ImagePreviewStatus.FAILED,
                    error=str(e)
                )

    except Exception as ex:
        logger.exception(ex)


@shared_task(
    name=const.S3_WORKER_GENERATE_PAGE_IMAGE,
    autoretry_for = (exc.S3DocumentNotFound,),
    # Wait for 10 seconds before starting each new try. At most retry 6 times.
    retry_kwargs = {"max_retries": 6, "countdown": 10},
)
def generate_page_image_task(doc_id: str):
    logger.debug('Task started')

    try:
        with Session() as db_session:
            doc_ver = db.get_last_version(db_session, doc_id=UUID(doc_id))

        logger.debug(f"doc_ver.id = {doc_ver.id}")
        client.download_docver(docver_id=doc_ver.id,
                               file_name=doc_ver.file_name)

        with Session() as db_session:
            thumb_path = generate.doc_thumbnail(db_session, UUID(doc_id))

        try:
            client.upload_file(thumb_path)
            with Session() as db_session:
                db.update_doc_img_preview_status(
                    db_session,
                    UUID(doc_id),
                    status=const.ImagePreviewStatus.READY
                )

        except botocore.exceptions.BotoCoreError as e:
            with Session() as db_session:
                db.update_doc_img_preview_status(
                    db_session,
                    UUID(doc_id),
                    status=const.ImagePreviewStatus.READY,
                    error=str(e)
                )

        with Session() as db_session:
            file_paths = generate.doc_previews(db_session, UUID(doc_id))

        for file_path in file_paths:
            client.upload_file(file_path)
    except Exception as ex:
        logger.exception(ex)
