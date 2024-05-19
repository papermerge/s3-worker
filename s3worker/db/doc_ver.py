from uuid import UUID
from sqlalchemy.orm import Session

from s3worker import schemas
from s3worker.db.models import (Document, DocumentVersion, Page)


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


def get_first_page(
    db_session: Session,
    doc_ver_id: UUID
) -> schemas.Page:
    """
    Returns first page of the document version
    identified by doc_ver_id
    """
    with db_session as session:  # noqa
        stmt = select(Page).where(
            Page.document_version_id == doc_ver_id,
        ).order_by(
            Page.number.asc()
        ).limit(1)
        try:
            db_page = session.scalars(stmt).one()
        except exc.NoResultFound:
            session.close()
            raise PageNotFound(
                f"DocVerID={doc_ver_id} does not have pages."
                " Maybe it does not have associated file yet?"
            )
        model = schemas.Page.model_validate(db_page)

    return model
