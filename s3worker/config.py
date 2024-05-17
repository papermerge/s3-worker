from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    aws_access_key_id: str
    aws_secret_access_key: str
    bucked_name: str
    object_prefix: str = ''
    aws_region_name: str | None = None
    papermerge__redis__url: str | None = None


@lru_cache()
def get_settings():
    return Settings()

