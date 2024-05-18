from pathlib import Path
from celery import shared_task
from s3worker.client import upload, delete, add_doc_vers, remove_doc_vers


@shared_task(name='s3_worker_upload')
def upload_task(target: str, keyname: str):
    upload(
        target_path=Path(target),
        object_path=Path(keyname)
    )


@shared_task(name='s3_worker_delete')
def delete_task(keynames: list[str]):
    delete(object_paths=[Path(k) for k in keynames])


@shared_task(name='s3_worker_add_doc_vers')
def add_doc_vers_task(doc_ver_ids: list[str]):
    add_doc_vers(doc_ver_ids)


@shared_task(name='s3_worker_remove_doc_vers')
def remove_doc_vers_task(doc_ver_ids: list[str]):
    remove_doc_vers(doc_ver_ids)
