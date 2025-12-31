from enum import Enum
from pathlib import Path

from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings


class FileServer(str, Enum):
    LOCAL = 'local'
    S3 = 's3'
    # Don't use "s3-local-test" in production!
    # It is meant only for local testing
    S3_LOCAL_TEST = 's3-local-test'  # used only for testing


class Settings(BaseSettings):
    # AWS specific configurations
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region_name: str | None = None

    pm_db_url: PostgresDsn
    pm_redis_url: RedisDsn | None = None

    pm_file_server: FileServer = FileServer.S3
    pm_s3_bucket_name: str

    pm_prefix: str = ''
    pm_media_root: str
    pm_log_config: Path | None = Path("/app/log_config.yaml")

    pm_preview_page_size_sm: int = 200  # pixels
    pm_preview_page_size_md: int = 600  # pixels
    pm_preview_page_size_lg: int = 900  # pixels
    pm_preview_page_size_xl: int = 1600  # pixels
    pm_preview_size: int = 100  # pixels


def get_settings():
    return Settings()
