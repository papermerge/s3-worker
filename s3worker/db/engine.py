from sqlalchemy import create_engine, Engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker

from s3worker.config import get_settings

settings = get_settings()

SQLALCHEMY_DATABASE_URL = settings.papermerge__database__url

SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
    "postgresql://", "postgresql+psycopg://", 1
)

connect_args = {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    poolclass=NullPool
)

Session = sessionmaker(engine, expire_on_commit=False)


def get_engine() -> Engine:
    return engine
