from pathlib import Path

from pydantic import PostgresDsn, RedisDsn, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .types import  StorageBackend


class Settings(BaseSettings):
    db_url: PostgresDsn

    media_root: Path = Path("media")
    redis_url: RedisDsn | None = None # redis_url is None during tests

    # Storage backend selection (S3, R2 or Local)
    storage_backend: StorageBackend = StorageBackend.LOCAL

    # AWS S3 specific configurations
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region_name: str | None = None

    # Cloudflare R2 specific configurations
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_account_id: str | None = None

    bucket_name: str | None = None  # Used for both S3 and R2
    prefix: str = ''
    log_config: Path | None = Path("/app/log_config.yaml")

    preview_page_size_sm: int = 200  # pixels
    preview_page_size_md: int = 600  # pixels
    preview_page_size_lg: int = 900  # pixels
    preview_page_size_xl: int = 1600  # pixels
    thumbnail_size: int = 100  # pixels

    # Presigned URL expiration (in seconds) - used for R2
    presigned_url_expires: int = 3600  # 1 hour

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
        if self.storage_backend == StorageBackend.S3:
            if not self.aws_access_key_id or not self.aws_secret_access_key:
                raise ValueError(
                    "AWS backend requires aws_access_key_id and aws_secret_access_key"
                )
        elif self.storage_backend == StorageBackend.R2:
            if not self.r2_access_key_id or not self.r2_secret_access_key:
                raise ValueError(
                    "Cloudflare backend requires r2_access_key_id and r2_secret_access_key"
                )
            if not self.r2_account_id:
                raise ValueError(
                    "Cloudflare backend requires r2_account_id"
                )
        return self

    model_config = SettingsConfigDict(env_prefix='pm_')



def get_settings():
    return Settings()
