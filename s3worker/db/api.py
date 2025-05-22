from uuid import UUID
from sqlalchemy import select

from typing import Tuple
from s3worker import schemas, types
from s3worker.db.orm import (Document, DocumentVersion, Page)
from s3worker.db.engine import Session


def get_docs(db_session: Session) -> list[schemas.Document]:
    stmt = select(Document)
    db_docs = db_session.scalars(stmt).all()
    model_docs = [
        schemas.Document.model_validate(db_doc) for db_doc in db_docs
    ]

    return model_docs


def get_last_version(
    db_session: Session,
    doc_id: UUID
) -> schemas.DocumentVersion:
    """
    Returns last version of the document
    identified by doc_id
    """
    stmt = select(DocumentVersion).join(Document).where(
        DocumentVersion.document_id == doc_id,
    ).order_by(
        DocumentVersion.number.desc()
    ).limit(1)
    db_doc_ver = db_session.scalars(stmt).one()
    model_doc_ver = schemas.DocumentVersion.model_validate(db_doc_ver)

    return model_doc_ver


def get_pages(
    db_session: Session,
    doc_ver_id: UUID
) -> list[schemas.Page]:
    """
    Returns first page of the document version
    identified by doc_ver_id
    """
    models = []

    stmt = select(Page).where(
        Page.document_version_id == doc_ver_id,
    ).order_by(
        Page.number.asc()
    )
    db_pages = db_session.scalars(stmt).all()
    models = [
        schemas.Page.model_validate(db_page)
        for db_page in db_pages
    ]

    return list(models)


def update_doc_img_preview_status(
    db_session: Session,
    doc_id: UUID,
    status: str,
    error: str | None = None
):
    stmt = select(Document).where(Document.id == doc_id)
    doc = db_session.execute(stmt).scalar_one_or_none()

    if doc is None:
        raise ValueError(f"Document with ID {doc_id} not found")

    doc.preview_status = status
    doc.preview_error = error

    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e


def get_doc_ver_from_page(
    db_session: Session,
    page_id: UUID
) -> Tuple[UUID | None, str | None]:
    stmt = select(DocumentVersion.id, DocumentVersion.file_name).join(
        Page
    ).where(Page.id == page_id)
    row = db_session.execute(stmt).one_or_none()

    if row:
        return row.id, row.file_name

    return None, None


def update_page_img_preview_status(
    db_session: Session,
    page_id: UUID,
    status: types.ImagePreviewStatus,
    size: types.ImagePreviewSize,
    error: str | None = None
):
    stmt = select(Page).where(Page.id == page_id)
    page = db_session.execute(stmt).scalar_one_or_none()

    if page is None:
        raise ValueError(f"Page with ID {page_id} not found")

    if size == types.ImagePreviewSize.sm:
        page.preview_status_sm = status
        page.preview_error_sm = error
    elif size == types.ImagePreviewSize.md:
        page.preview_status_md = status
        page.preview_error_md = error
    elif size == types.ImagePreviewSize.lg:
        page.preview_status_lg = status
        page.preview_error_lg = error
    elif size == types.ImagePreviewSize.xl:
        page.preview_status_xl = status
        page.preview_error_xl = error

    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e


def get_page_number(
    db_session: Session,
    page_id: UUID,
) -> int | None:
    stmt = select(Page.number).where(Page.id == page_id)
    row = db_session.execute(stmt).one_or_none()
    return row.number

