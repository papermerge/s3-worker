from pathlib import Path
from celery import shared_task
from s3worker.client import upload


@shared_task(name='s3_worker_upload')
def upload_task(target, keyname):
    upload(
        target_path=Path(target),
        object_path=Path(keyname)
    )
