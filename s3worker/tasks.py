from pathlib import Path
from celery import shared_task
from s3worker.client import upload, delete


@shared_task(name='s3_worker_upload')
def upload_task(target: str, keyname: str):
    upload(
        target_path=Path(target),
        object_path=Path(keyname)
    )


@shared_task(name='s3_worker_delete')
def delete_task(keynames: list[str]):
    delete(object_paths=[Path(k) for k in keynames])
