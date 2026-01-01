from enum import Enum
from pathlib import Path

from pydantic import PostgresDsn, RedisDsn, computed_field, model_validator
from pydantic_settings import BaseSettings


class FileServer(str, Enum):
    LOCAL = 'local'
    S3 = 's3'
    # Don't use "s3-local-test" in production!
    # It is meant only for local testing
    S3_LOCAL_TEST = 's3-local-test'  # used only for testing


class StorageBackend(str, Enum):
    """Storage backend type - AWS S3 or Cloudflare R2"""
    AWS = 'aws'
    CLOUDFLARE = 'cloudflare'


class Settings(BaseSettings):
    # Storage backend selection (aws or cloudflare)
    storage_backend: StorageBackend = StorageBackend.AWS

    # AWS S3 specific configurations
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region_name: str | None = None

    # Cloudflare R2 specific configurations
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_account_id: str | None = None

    pm_db_url: PostgresDsn
    pm_redis_url: RedisDsn | None = None

    pm_file_server: FileServer = FileServer.S3
    pm_s3_bucket_name: str  # Used for both S3 and R2

    pm_prefix: str = ''
    pm_media_root: str
    pm_log_config: Path | None = Path("/app/log_config.yaml")

    pm_preview_page_size_sm: int = 200  # pixels
    pm_preview_page_size_md: int = 600  # pixels
    pm_preview_page_size_lg: int = 900  # pixels
    pm_preview_page_size_xl: int = 1600  # pixels
    pm_thumbnail_size: int = 100  # pixels

    # Presigned URL expiration (in seconds) - used for R2
    presigned_url_expires: int = 3600  # 1 hour

    @computed_field
    @property
    def db_url(self) -> str:
        return str(self.pm_db_url).replace("postgresql://", "postgresql+psycopg://", 1)

    @computed_field
    @property
    def r2_endpoint_url(self) -> str | None:
        """Cloudflare R2 S3-compatible endpoint URL"""
        if self.r2_account_id:
            return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"
        return None

    @model_validator(mode='after')
    def validate_backend_credentials(self):
        """Validate that required credentials are set for the selected backend."""
        if self.storage_backend == StorageBackend.AWS:
            if not self.aws_access_key_id or not self.aws_secret_access_key:
                raise ValueError(
                    "AWS backend requires aws_access_key_id and aws_secret_access_key"
                )
        elif self.storage_backend == StorageBackend.CLOUDFLARE:
            if not self.r2_access_key_id or not self.r2_secret_access_key:
                raise ValueError(
                    "Cloudflare backend requires r2_access_key_id and r2_secret_access_key"
                )
            if not self.r2_account_id:
                raise ValueError(
                    "Cloudflare backend requires r2_account_id"
                )
        return self


def get_settings():
    return Settings()
