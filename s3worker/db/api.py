from uuid import UUID
from sqlalchemy import select

from s3worker import schemas, exc
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
