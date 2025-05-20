import uuid
import pytest


from s3worker.db.base import Base
from s3worker.db.engine import get_engine, Session
from s3worker.db import orm

from s3worker.config import get_settings
from s3worker import constants

config = get_settings()


@pytest.fixture()
def make_user(db_session):
    print("make_user FIXTURE")
    def _maker(username: str):
        user_id = uuid.uuid4()
        home_id = uuid.uuid4()
        inbox_id = uuid.uuid4()

        db_user = orm.User(
            id=user_id,
            username=username,
            email=f"{username}@mail.com",
            first_name=f"{username}_first",
            last_name=f"{username}_last",
            password="pwd",
        )
        db_inbox = orm.Folder(
            id=inbox_id,
            title=constants.INBOX_TITLE,
            ctype=constants.CTYPE_FOLDER,
            lang="de",
            user_id=user_id,
        )
        db_home = orm.Folder(
            id=home_id,
            title=constants.HOME_TITLE,
            ctype=constants.CTYPE_FOLDER,
            lang="de",
            user_id=user_id,
        )
        db_session.add(db_inbox)
        db_session.add(db_home)
        db_session.add(db_user)
        db_session.commit()
        db_user.home_folder_id = db_home.id
        db_user.inbox_folder_id = db_inbox.id
        db_session.commit()

        return db_user

    return _maker


@pytest.fixture(scope="function")
def db_session():
    print("Creating tables...")
    engine = get_engine()
    Base.metadata.create_all(engine, checkfirst=False)
    with Session() as session:
        yield session

    print("Dropping tables...")
    Base.metadata.drop_all(engine, checkfirst=False)


@pytest.fixture()
def make_page(db_session: Session, user: orm.User):
    print("make_page FIXTURE")
    def _make():
        db_pages = []
        for number in range(1, 4):
            db_page = orm.Page(number=number, text="blah", page_count=3)
            db_pages.append(db_page)

        doc_id = uuid.uuid4()
        db_doc = orm.Document(
            id=doc_id,
            ctype="document",
            title=f"Document {doc_id}",
            user_id=user.id,
            parent_id=user.home_folder_id,
            lang="de",
        )
        db_doc_ver = orm.DocumentVersion(pages=db_pages, document=db_doc)
        db_session.add(db_doc)
        db_session.add(db_doc_ver)
        db_session.commit()

        return db_pages[0]

    return _make


@pytest.fixture()
def user(make_user) -> orm.User:
    print("user FIXTURE")
    return make_user(username="random")
