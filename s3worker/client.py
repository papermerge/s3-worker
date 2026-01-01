"""
S3-compatible storage client module.

Supports both AWS S3 and Cloudflare R2 backends.
The backend is selected via the STORAGE_BACKEND environment variable:
- 'aws' (default): Use AWS S3
- 'cloudflare': Use Cloudflare R2

Cloudflare R2 is S3-compatible, so we use boto3 with a custom endpoint URL.
Reference: https://developers.cloudflare.com/r2/examples/aws/boto3/
"""
import logging
from uuid import UUID
from typing import Tuple

import boto3
from botocore.client import BaseClient
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
from pathlib import Path

from s3worker import config, utils
from s3worker import plib
from s3worker.exc import S3DocumentNotFound
from s3worker.config import StorageBackend

settings = config.get_settings()
logger = logging.getLogger(__name__)

# Cache the client instance
_client: BaseClient | None = None


def get_client() -> BaseClient:
    """
    Create and return a boto3 S3 client.
    
    For AWS: Uses standard S3 endpoint with region
    For Cloudflare R2: Uses custom endpoint URL with 'auto' region
    """
    global _client
    if _client is not None:
        return _client

    if settings.pm_storage_backend == StorageBackend.AWS:
        session = boto3.Session(
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region_name
        )
        _client = session.client('s3')
    else:
        # Cloudflare R2
        session = boto3.Session(
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
        )
        _client = session.client(
            's3',
            endpoint_url=settings.r2_endpoint_url,
            region_name='auto',  # Required by boto3 but not used by R2
            config=BotoConfig(signature_version='s3v4')
        )

    return _client


def reset_client():
    """Reset the cached client (useful for testing or config changes)."""
    global _client
    _client = None


def upload(target_path: Path, object_path: Path):
    """Uploads `target_path` to S3/R2 bucket"""
    s3_client = get_client()
    keyname = get_prefix() / object_path
    s3_client.upload_file(
        str(target_path),
        Bucket=get_bucket_name(),
        Key=str(keyname)
    )


def delete(object_paths: list[Path]):
    """Delete one or multiple objects from S3/R2 bucket

    Reference:
        - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/delete_objects.html
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
    """Given a list of UUID (as str) - add those documents to S3/R2"""
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
            f"Skipping upload for doc version {uid}."
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
    """Given a list of UUID (as str) - remove those documents from S3/R2"""
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


def upload_file(rel_file_path: Path) -> Tuple[bool, str | None]:
    """Uploads to S3/R2 file specified by relative path

    Path is relative to `media root`.
    E.g. path "thumbnails/jpg/bd/f8/bdf862be/100.jpg", means that
    file absolute path on the file system is:
        <media root>/thumbnails/jpg/bd/f8/bdf862be/100.jpg

    The S3/R2 keyname will then be:
        <prefix>/thumbnails/jpg/bd/f8/bdf862be/100.jpg
    """
    s3_client = get_client()
    keyname = get_prefix() / rel_file_path
    target: Path = plib.rel2abs(rel_file_path)

    if not target.exists():
        msg = f"Upload failed: {target=} does not exist. Upload canceled."
        logger.error(msg)
        return False, msg

    if not target.is_file():
        msg = f"Upload failed: {target=} is not a file. Upload canceled."
        logger.error(msg)
        return False, msg

    logger.debug(f"target={target} keyname={keyname}")

    s3_client.upload_file(
        str(target),
        Bucket=get_bucket_name(),
        Key=str(keyname)
    )

    return True, None


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


def sync():
    s3_client = get_client()
    bucket_name = get_bucket_name()
    for target_path, keyname in media_iter():
        logger.debug(f"target_path: {target_path}, keyname={keyname}")
        if not s3_obj_exists(
            bucket_name=bucket_name,
            keyname=str(keyname)
        ):
            logger.debug(f"Uploading {target_path} to {keyname}")
            s3_client.upload_file(
                str(target_path),
                Bucket=bucket_name,
                Key=str(keyname)
            )
        else:
            logger.debug(f"Skipping {target_path} as {keyname} exists")


def download_docver(docver_id: UUID, file_name: str):
    """Downloads document version from S3/R2"""
    doc_ver_path = plib.abs_docver_path(docver_id, file_name)
    keyname = Path(get_prefix()) / plib.docver_path(docver_id, file_name)

    if doc_ver_path.exists():
        # file exists locally, nothing to do
        logger.debug(f"{doc_ver_path} exists locally")
        return

    if not s3_obj_exists(get_bucket_name(), str(keyname)):
        # no local version + no remote version
        logger.debug(f"{keyname} was not found in storage")
        raise S3DocumentNotFound(f"Storage key {keyname} not found")

    client = get_client()
    doc_ver_path.parent.mkdir(parents=True, exist_ok=True)
    client.download_file(get_bucket_name(), str(keyname), str(doc_ver_path))


def s3_obj_exists(
    bucket_name: str, keyname: str
) -> bool:
    client = get_client()
    try:
        client.head_object(Bucket=bucket_name, Key=keyname)
    except ClientError as e:
        logger.debug(f"OBJECT_EXISTS check: {e}")
        logger.debug(f"keyname={keyname} - not found")
        return False

    logger.debug(f"keyname={keyname} - found")
    return True


def generate_presigned_url(keyname: str, expires_in: int | None = None) -> str:
    """
    Generate a presigned URL for downloading an object.
    
    This is primarily useful for R2, but also works with S3.
    
    Args:
        keyname: The object key in the bucket
        expires_in: URL expiration time in seconds (default from settings)
    
    Returns:
        Presigned URL string
    """
    client = get_client()
    if expires_in is None:
        expires_in = settings.presigned_url_expires
    
    url = client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': get_bucket_name(),
            'Key': keyname
        },
        ExpiresIn=expires_in
    )
    return url


def media_iter():
    paths = Path(get_media_root()).glob("**/*")
    prefix = get_prefix()
    logger.debug(f"PREFIX={prefix}")
    for path in paths:
        if path.is_file():
            str_path = str(path)
            str_media = str(get_media_root())
            str_rel_path = str_path[len(str_media) + 1:]
            keyname = prefix / Path(str_rel_path)
            logger.debug(f"str_path={str_path}")
            logger.debug(f"str_media={str_media}")
            logger.debug(f"str_rel_path={str_rel_path}")
            logger.debug(f"keyname={keyname}")
            logger.debug(f"path={path}")
            yield path, keyname


def get_bucket_name():
    return settings.pm_s3_bucket_name


def get_prefix():
    return Path(settings.pm_prefix) if settings.pm_prefix else Path('')


def get_media_root():
    return settings.pm_media_root


def get_storage_backend_name() -> str:
    """Return human-readable storage backend name."""
    if settings.pm_storage_backend == StorageBackend.AWS:
        return "AWS S3"
    return "Cloudflare R2"
