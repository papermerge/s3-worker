import logging
from uuid import UUID
import boto3

from botocore.client import BaseClient
from pathlib import Path
from s3worker import config, utils
from s3worker import pathlib as plib

settings = config.get_settings()
logger = logging.getLogger(__name__)


def get_client() -> BaseClient:
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
        Bucket=settings.bucket_name,
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
        Bucket=settings.bucket_name,
        Delete={
            'Objects': [{'Key': key} for key in keynames]
        }
    )


def add_doc_vers(doc_ver_ids: list[str]):
    """Given a list of UUID (as str) - add those documents to S3"""
    s3_client = get_client()
    for ver in doc_ver_ids:
        uid = UUID(ver)
        add_doc_ver(s3_client, uid)


def add_doc_ver(client: BaseClient, uid: UUID):
    logger.info(f"Adding doc_ver {uid} to the Bucket")

    # get filename to be uploaded based on the UUID of the doc version
    file_name = utils.get_filename_in_dir(
        _doc_ver_base(uid)
    )
    if file_name is None:
        logger.error(
            f"No filename found in {_doc_ver_base(uid)} directory. "
            f"Skipping S3 upload for doc version {uid}."
        )
        return

    logger.debug(f"file_name={file_name}")

    keyname = settings.object_prefix / plib.docver_path(uid, file_name)
    target_path = _doc_ver_base(uid) / Path(file_name)
    logger.debug(
        f"Uploading keyname={keyname} to bucket={settings.bucket_name}"
    )
    client.upload_file(
        str(target_path),
        Bucket=settings.bucket_name,
        Key=str(keyname)
    )


def remove_doc_vers(doc_ver_ids: list[str]):
    """Given a list of UUID (as str) - remove those documents from S3"""
    s3_client = get_client()
    for ver in doc_ver_ids:
        uid = UUID(ver)
        remove_doc_ver(s3_client, uid)


def remove_doc_ver(client: BaseClient, uid: UUID):
    logger.info(f"Removing doc_ver {uid} from the bucket")

    prefix = str(settings.object_prefix / plib.docver_base_path(uid))
    objects_to_delete = client.list_objects_v2(
        Bucket=settings.bucket_name,
        Prefix=prefix
    )
    if 'Contents' not in objects_to_delete:
        logger.error(f"Empty content for prefix={prefix}. Nothing to delete.")
        return

    keynames = []
    for i in objects_to_delete['Contents']:
        if 'Key' in i:
            keynames.append(i['Key'])
        else:
            logger.warning(
                f"Item {i} does not have Key attribute. API changed?"
            )

    logger.debug(
        f"Deleting keynames={keynames} from bucket={settings.bucket_name}"
    )
    client.delete_objects(
        Bucket=settings.bucket_name,
        Delete={
            'Objects': [{'Key': k} for k in keynames]
        }
    )


def upload_doc_thumbnail(doc_ver_id: UUID):
    pass


def upload_doc_ver_previews(doc_ver_id: UUID):
    pass


def _doc_ver_base(uid: UUID) -> Path:
    """Returns absolute base directory of the document version"""
    return plib.rel2abs(plib.docver_base_path(uid))
