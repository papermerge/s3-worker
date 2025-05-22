from enum import Enum
from pathlib import Path
from pydantic_settings import BaseSettings


class FileServer(str, Enum):
    LOCAL = 'local'
    S3 = 's3'
    # Don't use "s3-local-test" in production!
    # It is meant only for local testing
    S3_LOCAL_TEST = 's3-local-test'  # used only for testing



class Settings(BaseSettings):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region_name: str | None = None
    papermerge__main__file_server: FileServer = FileServer.S3
    papermerge__s3__bucket_name: str
    papermerge__redis__url: str | None = None
    papermerge__main__prefix: str = ''
    papermerge__main__media_root: str
    papermerge__main__logging_cfg: Path | None = None
    papermerge__database__url: str = 'sqlite:////db/db.sqlite3'
    papermerge__preview__page_size_sm: int = 200  # pixels
    papermerge__preview__page_size_md: int = 600  # pixels
    papermerge__preview__page_size_lg: int = 900  # pixels
    papermerge__preview__page_size_xl: int = 1600  # pixels
    papermerge__thumbnail__size: int = 100  # pixels


def get_settings():
    return Settings()
