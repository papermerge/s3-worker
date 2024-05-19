from uuid import UUID
from celery import shared_task

from s3worker import generate, client
from s3worker import constants as const


@shared_task(name=const.S3_WORKER_ADD_DOC_VER)
def add_doc_vers_task(doc_ver_ids: list[str]):
    client.add_doc_vers(doc_ver_ids)


@shared_task(name=const.S3_WORKER_REMOVE_DOC_VER)
def remove_doc_vers_task(doc_ver_ids: list[str]):
    client.remove_doc_vers(doc_ver_ids)


@shared_task(name=const.S3_WORKER_GENERATE_PREVIEW)
def remove_doc_vers_task(doc_id: str):
    thumb_base = generate.doc_thumbnail(UUID(doc_id))
    client.upload_doc_thumbnail(thumb_base)

    generate.doc_previews(UUID(doc_id))
    client.upload_doc_previews(UUID(doc_id))
