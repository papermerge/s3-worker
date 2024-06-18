from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region_name: str | None = None
    papermerge__s3__bucket_name: str
    papermerge__redis__url: str | None = None
    papermerge__main__prefix: str = ''
    papermerge__main__media_root: str
    papermerge__main__logging_cfg: Path | None = None
    papermerge__database__url: str = 'sqlite:////db/db.sqlite3'

@lru_cache()
def get_settings():
    return Settings()

