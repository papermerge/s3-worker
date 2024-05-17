import boto3
from pathlib import Path
from s3worker import config

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
    """Uploads `target_path` to S3 bucket"""
    s3_client = get_client()
    keyname = settings.object_prefix / object_path
    s3_client.upload_file(
        str(target_path),
        Bucket=settings.bucked_name,
        Key=str(keyname)
    )


def delete(object_paths: list[Path]):
    """Delete one or multiple objects from S3 bucket

    Reference:
        - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/delete_objects.html  # noqa
    """
    s3_client = get_client()
    keynames = [
        str(settings.object_prefix / obj_path) for obj_path in object_paths
    ]
    s3_client.delete_objects(
        Bucket=settings.bucked_name,
        Delete={
            'Objects': [{'Key': key} for key in keynames]
        }
    )
