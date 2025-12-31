from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker

from s3worker.config import get_settings

settings = get_settings()

engine = create_engine(settings.db_url)

Session = sessionmaker(engine, expire_on_commit=False)


def get_engine() -> Engine:
    return engine
