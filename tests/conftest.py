import uuid
import pytest

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from s3worker.db.base import Base
from s3worker.db.engine import get_engine, Session
from s3worker.db import orm
from s3worker.db import api

from s3worker.config import get_settings
from s3worker import constants

config = get_settings()


@pytest.fixture()
def system_user(db_session) -> orm.User:
    """
    Retrieve or create the system user with special ID.
    System user owns resources created by background tasks
    and initialization scripts.
    """
    stmt = select(orm.User).where(orm.User.id == constants.SYSTEM_USER_ID)
    result = db_session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = orm.User(
            id=constants.SYSTEM_USER_ID,
            username="system",
            email="system@local",
            password="-",
            created_by=constants.SYSTEM_USER_ID,
            updated_by=constants.SYSTEM_USER_ID,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    return user


@pytest.fixture()
def make_user(db_session, system_user):
    """
    Create test user with special folders.
    """
    def _maker(username: str):
        user_id = uuid.uuid4()

        db_user = orm.User(
            id=user_id,
            username=username,
            email=f"{username}@mail.com",
            first_name=f"{username}_first",
            last_name=f"{username}_last",
            password="pwd",
        )
        db_session.add(db_user)
        db_session.flush()

        api.create_special_folders_for_user(
            db_session,
            user_id
        )

        db_session.commit()
        db_session.refresh(db_user)

        stmt = (
            select(orm.User)
            .options(selectinload(orm.User.special_folders))
            .where(orm.User.id == user_id)
        )
        result = db_session.execute(stmt)
        user = result.scalar_one()

        return user

    return _maker


@pytest.fixture(scope="function")
def db_session():
    engine = get_engine()

    Base.metadata.create_all(engine, checkfirst=False)

    with Session() as session:
        yield session

    Base.metadata.drop_all(engine, checkfirst=False)


@pytest.fixture()
def make_page(db_session: Session, user: orm.User, system_user):

    def _make():
        db_pages = []
        for number in range(1, 4):
            db_page = orm.Page(number=number)
            db_pages.append(db_page)

        doc_id = uuid.uuid4()
        db_doc = orm.Document(
            id=doc_id,
            ctype="document",
            title=f"Document {doc_id}",
            parent_id=user.home_folder_id,
            lang="deu",
            created_by=system_user.id,
            updated_by=system_user.id,
        )
        db_doc_ver = orm.DocumentVersion(
            pages=db_pages,
            document=db_doc,
            created_by=system_user.id,
            updated_by=system_user.id,
        )
        db_session.add(db_doc)
        db_session.add(db_doc_ver)
        db_session.commit()

        return db_pages[0]

    return _make


@pytest.fixture()
def user(make_user) -> orm.User:
    return make_user(username="random")
