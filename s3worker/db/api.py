import uuid
import logging
from uuid import UUID
from sqlalchemy import select

from typing import Tuple, Dict

from s3worker import schemas, types, constants
from s3worker.config import get_settings
from s3worker.db.orm import (
    Document,
    DocumentVersion,
    Page,
    Ownership,
    Folder,
    SpecialFolder
)
from s3worker.db.engine import Session
from s3worker.types import ImagePreviewStatus


settings = get_settings()
logger = logging.getLogger(__name__)


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
) -> DocumentVersion | None:
    """Get a specific document version"""
    stmt = select(DocumentVersion).where(DocumentVersion.id == version_id)
    db_ver = db_session.execute(stmt).scalar_one_or_none()
    
    if db_ver is None:
        return None
    
    return db_ver


def create_document_version(
    db_session: Session,
    document_id: UUID,
    number: int,
    file_name: str,
    size: int,
    mime_type: str,
    created_by: UUID,
    lang: str,
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
        created_by=created_by,
        updated_by=created_by,
        page_count=page_count,
        is_original=is_original,
        source_version_id=source_version_id,
        creation_reason=creation_reason,
        lang=lang
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


def set_owner(
    db_session: Session,
    resource: schemas.Resource,
    owner: schemas.Owner
) -> Ownership:
    """
    Set or update the owner of a resource.

    Creates ownership record if it doesn't exist, updates if it does.
    """
    stmt = select(Ownership).where(
        Ownership.resource_type == resource.type.value,
        Ownership.resource_id == resource.id
    )
    ownership = db_session.execute(stmt).scalar_one_or_none()

    if ownership:
        # Update existing ownership
        ownership.owner_type = owner.owner_type.value
        ownership.owner_id = owner.owner_id
    else:
        # Create new ownership
        ownership = Ownership(
            owner_type=owner.owner_type.value,
            owner_id=owner.owner_id,
            resource_type=resource.type.value,
            resource_id=resource.id
        )
        db_session.add(ownership)

    db_session.flush()
    return ownership


def create_special_folders_for_user(
    db_session: Session,
    user_id: UUID,
) -> Dict[str, UUID]:
    """
    Create home and inbox folders for a user.

    Args:
        db_session: Database session
        user_id: User ID

    Returns:
        Dictionary with 'home' and 'inbox' keys mapping to folder IDs
    """
    owner = schemas.Owner.create_from(user_id=user_id)
    home_id = uuid.uuid4()
    inbox_id = uuid.uuid4()

    # Create the actual folder nodes WITHOUT user_id
    home_folder = Folder(
        id=home_id,
        title=constants.HOME_TITLE,
        ctype=constants.CTYPE_FOLDER,
        lang="xxx",
        created_by=constants.SYSTEM_USER_ID,
        updated_by=constants.SYSTEM_USER_ID,
    )
    inbox_folder = Folder(
        id=inbox_id,
        title=constants.INBOX_TITLE,
        ctype=constants.CTYPE_FOLDER,
        lang="xxx",
        created_by=constants.SYSTEM_USER_ID,
        updated_by=constants.SYSTEM_USER_ID,
    )

    db_session.add(home_folder)
    db_session.add(inbox_folder)
    db_session.flush()

    set_owner(
        db_session=db_session,
        resource=schemas.NodeResource(id=home_id),
        owner=owner,
    )

    set_owner(
        db_session=db_session,
        resource=schemas.NodeResource(id=inbox_id),
        owner=owner
    )

    home_special = SpecialFolder(
        owner_type=types.OwnerType.USER.value,
        owner_id=user_id,
        folder_type=types.FolderType.HOME.value,
        folder_id=home_id
    )
    inbox_special = SpecialFolder(
        owner_type=types.OwnerType.USER.value,
        owner_id=user_id,
        folder_type=types.FolderType.INBOX.value,
        folder_id=inbox_id
    )

    db_session.add_all([home_special, inbox_special])
    db_session.flush()

    return {
        'home': home_id,
        'inbox': inbox_id
    }
