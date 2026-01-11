from uuid import UUID
from sqlalchemy import select

from typing import Tuple
from s3worker import schemas, types
from s3worker.db.orm import (Document, DocumentVersion, Page)
from s3worker.db.engine import Session
from s3worker.types import ImagePreviewStatus


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


def get_doc_img_preview_status(
    db_session: Session,
    doc_id: UUID
) -> ImagePreviewStatus | None:
    stmt = select(Document).where(Document.id == doc_id)
    doc = db_session.execute(stmt).scalar_one_or_none()

    return doc.preview_status

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


def get_page_number(
    db_session: Session,
    page_id: UUID,
) -> int | None:
    stmt = select(Page.number).where(Page.id == page_id)
    row = db_session.execute(stmt).one_or_none()
    return row.number


def get_document_processing_status(
    db_session: Session,
    doc_id: UUID
) -> str | None:
    """Get processing status of a document"""
    stmt = select(Document).where(Document.id == doc_id)
    doc = db_session.execute(stmt).scalar_one_or_none()
    
    if doc is None:
        return None
    
    return doc.processing_status


def update_document_processing_status(
    db_session: Session,
    doc_id: UUID,
    status: str,
    error: str | None = None
):
    """Update document processing status"""
    stmt = select(Document).where(Document.id == doc_id)
    doc = db_session.execute(stmt).scalar_one_or_none()
    
    if doc is None:
        raise ValueError(f"Document with ID {doc_id} not found")
    
    doc.processing_status = status
    doc.processing_error = error
    
    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e


def get_document_version(
    db_session: Session,
    version_id: UUID
) -> schemas.DocumentVersion | None:
    """Get a specific document version"""
    stmt = select(DocumentVersion).where(DocumentVersion.id == version_id)
    db_ver = db_session.execute(stmt).scalar_one_or_none()
    
    if db_ver is None:
        return None
    
    return schemas.DocumentVersion.model_validate(db_ver)


def create_document_version(
    db_session: Session,
    document_id: UUID,
    number: int,
    file_name: str,
    size: int,
    mime_type: str,
    page_count: int = 0,
    is_original: bool = False,
    source_version_id: UUID | None = None,
    creation_reason: str = "upload"
) -> schemas.DocumentVersion:
    """Create a new document version"""
    version = DocumentVersion(
        document_id=document_id,
        number=number,
        file_name=file_name,
        size=size,
        mime_type=mime_type,
        page_count=page_count,
        is_original=is_original,
        source_version_id=source_version_id,
        creation_reason=creation_reason
    )
    
    db_session.add(version)
    
    try:
        db_session.commit()
        db_session.refresh(version)
    except Exception as e:
        db_session.rollback()
        raise e
    
    return schemas.DocumentVersion.model_validate(version)


def create_pages_for_version(
    db_session: Session,
    version_id: UUID,
    page_count: int,
    lang: str = "deu"
) -> list[schemas.Page]:
    """Create page records for a document version"""
    pages = []
    
    for page_number in range(1, page_count + 1):
        page = Page(
            number=page_number,
            page_count=page_count,
            lang=lang,
            document_version_id=version_id
        )
        pages.append(page)
        db_session.add(page)
    
    try:
        db_session.commit()
        for page in pages:
            db_session.refresh(page)
    except Exception as e:
        db_session.rollback()
        raise e
    
    return [schemas.Page.model_validate(p) for p in pages]


def update_version_page_count(
    db_session: Session,
    version_id: UUID,
    page_count: int
):
    """Update the page count for a document version"""
    stmt = select(DocumentVersion).where(DocumentVersion.id == version_id)
    version = db_session.execute(stmt).scalar_one_or_none()
    
    if version is None:
        raise ValueError(f"DocumentVersion with ID {version_id} not found")
    
    version.page_count = page_count
    
    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e

