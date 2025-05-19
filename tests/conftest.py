import uuid
import pytest


from s3worker.db.base import Base
from s3worker.db.engine import engine, Session
from s3worker.db import orm

from s3worker.config import get_settings

config = get_settings()


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(engine, checkfirst=False)
    with Session() as session:
        yield session

    Base.metadata.drop_all(engine, checkfirst=False)
