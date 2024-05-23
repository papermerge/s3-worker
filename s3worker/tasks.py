import logging
from uuid import UUID
from celery import shared_task

from s3worker import generate, client, db
from s3worker import constants as const


logger = logging.getLogger(__name__)


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
        client.remove_doc_thumbnail(doc_id)
    except Exception as ex:
        logger.exception(ex)


@shared_task(name=const.S3_WORKER_GENERATE_PREVIEW)
def generate_preview_task(doc_id: str):
    logger.debug('Task started')
    try:
        Session = db.get_db()
        with Session() as db_session:
            thumb_path = generate.doc_thumbnail(db_session, UUID(doc_id))

        client.upload_file(thumb_path)

        with Session() as db_session:
            file_paths = generate.doc_previews(db_session, UUID(doc_id))

        for file_path in file_paths:
            client.upload_file(file_path)
    except Exception as ex:
        logger.exception(ex)
