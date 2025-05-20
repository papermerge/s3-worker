from s3worker import types
from s3worker.db import orm
from s3worker.db import api as dbapi


def test_get_doc_ver_from_page(db_session, make_page):
    page: orm.Page =  make_page()
    doc_ver_id, file_name = dbapi.get_doc_ver_from_page(db_session, page_id=page.id)

    assert doc_ver_id == page.document_version_id
    assert file_name == page.document_version.file_name

def test_update_page_img_preview_status(db_session, make_page):
    page: orm.Page = make_page()

    assert page.preview_status_md is None

    dbapi.update_page_img_preview_status(
        db_session,
        page_id=page.id,
        status=types.ImagePreviewStatus.pending,
        size=types.ImagePreviewSize.md
    )

    refreshed_page = db_session.get(orm.Page, page.id)
    assert refreshed_page.preview_status_md == types.ImagePreviewStatus.pending


