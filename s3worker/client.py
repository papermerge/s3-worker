import logging
from uuid import UUID
import boto3

from botocore.client import BaseClient
from pathlib import Path
from s3worker import config, utils, db
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
    keyname = get_prefix() / object_path
    s3_client.upload_file(
        str(target_path),
        Bucket=get_bucket_name(),
        Key=str(keyname)
    )


def delete(object_paths: list[Path]):
    """Delete one or multiple objects from S3 bucket

    Reference:
        - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/delete_objects.html  # noqa
    """
    s3_client = get_client()
    keynames = [
        str(get_prefix() / obj_path) for obj_path in object_paths
    ]
    s3_client.delete_objects(
        Bucket=get_bucket_name(),
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

    keyname = get_prefix() / plib.docver_path(uid, file_name)
    target_path = _doc_ver_base(uid) / Path(file_name)
    logger.debug(
        f"Uploading keyname={keyname} to bucket={get_bucket_name()}"
    )
    client.upload_file(
        str(target_path),
        Bucket=get_bucket_name(),
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

    prefix = str(get_prefix() / plib.docver_base_path(uid))
    remove_files(
        client,
        bucket_name=get_bucket_name(),
        prefix=prefix
    )

def remove_doc_thumbnail(uid: UUID):
    logger.info(f"Removing thumbnail of doc_id={uid} from the bucket")
    s3_client = get_client()
    prefix = str(get_prefix() / plib.thumbnail_path(uid))
    remove_files(
        client=s3_client,
        bucket_name=get_bucket_name(),
        prefix=prefix
    )

def upload_file(rel_file_path: Path):
    """Uploads to S3 file specified by relative path

    Path is relative to `media root`.
    E.g. path "thumbnails/jpg/bd/f8/bdf862be/100.jpg", means that
    file absolute path on the file system is:
        <media root>/thumbnails/jpg/bd/f8/bdf862be/100.jpg

    The S3 keyname will then be:
        <prefix>/thumbnails/jpg/bd/f8/bdf862be/100.jpg
    """
    s3_client = get_client()
    keyname = get_prefix() / rel_file_path
    target: Path = plib.rel2abs(rel_file_path)

    if not target.exists():
        logger.error(f"Target {target} does not exist. Upload to S3 canceled.")
        return

    if not target.is_file():
        logger.error(f"Target {target} is not a file. Upload to S3 canceled.")
        return

    logger.debug(f"target={target} keyname={keyname}")

    s3_client.upload_file(
        str(target),
        Bucket=get_bucket_name(),
        Key=str(keyname)
    )


def upload_doc_previews(doc_ver_id: UUID):
    pass


def _doc_ver_base(uid: UUID) -> Path:
    """Returns absolute base directory of the document version"""
    return plib.rel2abs(plib.docver_base_path(uid))


def remove_files(client: BaseClient, bucket_name: str, prefix: str):
    """Removes all objects in `bucket_name` starting with `prefix`"""
    objects_to_delete = client.list_objects_v2(
        Bucket=bucket_name,
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
        f"Deleting keynames={keynames} from bucket={bucket_name}"
    )
    client.delete_objects(
        Bucket=bucket_name,
        Delete={
            'Objects': [{'Key': k} for k in keynames]
        }
    )


def delete_page(uid: UUID):
    """Delete all thumbnails/previews associated with given page ID"""
    s3_client = get_client()
    prefix = str(get_prefix() / plib.base_thumbnail_path(uid))
    remove_files(
        s3_client,
        bucket_name=get_bucket_name(),
        prefix=prefix
    )


def get_bucket_name():
    return settings.papermerge__s3__bucket_name


def get_prefix():
    return settings.papermerge__s3__object_prefix
