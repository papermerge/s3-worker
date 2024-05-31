from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from s3worker import schemas
from s3worker.db.models import (Document, DocumentVersion, Page)


def get_docs(db_session: Session) -> list[schemas.Document]:
    with db_session as session:  # noqa
        stmt = select(Document)
        db_docs = session.scalars(stmt).all()
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
    with db_session as session:  # noqa
        stmt = select(DocumentVersion).join(Document).where(
            DocumentVersion.document_id == doc_id,
        ).order_by(
            DocumentVersion.number.desc()
        ).limit(1)
        db_doc_ver = session.scalars(stmt).one()
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
    with db_session as session:  # noqa
        stmt = select(Page).where(
            Page.document_version_id == doc_ver_id,
        ).order_by(
            Page.number.asc()
        )
        try:
            db_pages = session.scalars(stmt).all()
        except exc.NoResultFound:
            session.close()
            raise PageNotFound(
                f"DocVerID={doc_ver_id} does not have pages(s)."
                " Maybe it does not have associated file yet?"
            )
        models = [
            schemas.Page.model_validate(db_page)
            for db_page in db_pages
        ]

    return list(models)
