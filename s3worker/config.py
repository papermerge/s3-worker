from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    aws_access_key_id: str
    aws_secret_access_key: str
    bucked_name: Path
    aws_endpoint_url: str | None = None
    aws_region_name: str | None = None
    prefix: Path = ''


@lru_cache()
def get_settings():
    return Settings()

