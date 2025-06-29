from s3worker import types
from s3worker.db import orm
from s3worker.db import api as dbapi


def test_get_doc_ver_from_page(db_session, make_page):
    page: orm.Page =  make_page()
    doc_ver_id, file_name = dbapi.get_doc_ver_from_page(db_session, page_id=page.id)

    assert doc_ver_id == page.document_version_id
    assert file_name == page.document_version.file_name

def test_get_page_number(db_session, make_page):
    page: orm.Page = make_page()

    page_number = dbapi.get_page_number(
        db_session,
        page_id=page.id,
    )

    assert page_number == page.number


