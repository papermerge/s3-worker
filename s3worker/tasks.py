from celery import shared_task
from s3worker.client import upload, delete, add_doc_vers, remove_doc_vers
from s3worker import constants as const


@shared_task(name=const.S3_WORKER_ADD_DOC_VER)
def add_doc_vers_task(doc_ver_ids: list[str]):
    add_doc_vers(doc_ver_ids)


@shared_task(name=const.S3_WORKER_REMOVE_DOC_VER)
def remove_doc_vers_task(doc_ver_ids: list[str]):
    remove_doc_vers(doc_ver_ids)
