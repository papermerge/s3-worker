import boto3
from pathlib import Path
from . import config

settings = config.get_settings()


def get_client():
    session = boto3.Session(
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region_name
    )
    client = session.client('s3')

    return client


def upload(target_path: Path, object_path: Path):
    s3_client = get_client()
    keyname = settings.object_prefix / object_path
    s3_client.upload_file(
        str(target_path),
        settings.bucked_name,
        str(keyname)
    )


def download():
    pass
