import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import (DateTime, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from s3worker.types import OwnerType, FolderType
from sqlalchemy import Enum as SQLEnum

from typing import Literal
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP

from .audit_cols import AuditColumns
from .base import Base
from .utils import utc_now

CType = Literal["document", "folder"]


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, insert_default=uuid.uuid4())
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    first_name: Mapped[str] = mapped_column(default=" ")
    last_name: Mapped[str] = mapped_column(default=" ")
    password: Mapped[str] = mapped_column(nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    ### User does not use AuditColumns mixin because the mixin mandates
    # that `created_by`/`updated_by` will be NOT NULL. However, "system user"
    # cannot create itself -> for system user `created_by`/`updated_by` must
    # be set to NULL -> for `users` table the `created_by`/`updated_by` are
    # defined to allow NULL values.

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=utc_now,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=utc_now,
        onupdate=func.now(),
        nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True
    )

    # created by NULL only for "system user"
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT", deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    # updated_by NULL only for "system user"
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT", deferrable=True, initially='DEFERRED'),
        nullable=True
    )
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    archived_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    special_folders: Mapped[list["SpecialFolder"]] = relationship(
        "SpecialFolder",
        primaryjoin=(
            "and_("
            "foreign(SpecialFolder.owner_id) == User.id, "
            "SpecialFolder.owner_type == 'user'"
            ")"
        ),
        viewonly=True,
        lazy="selectin",  # Eager load special folders with user
        cascade="delete"  # Delete special folders when user is deleted
    )

    @property
    def home_folder_id(self) -> UUID | None:
        for sf in self.special_folders:
            if sf.folder_type == FolderType.HOME:
                return sf.folder_id
        return None

    @property
    def inbox_folder_id(self) -> UUID | None:
        for sf in self.special_folders:
            if sf.folder_type == FolderType.INBOX:
                return sf.folder_id
        return None

    @property
    def home_folder(self) -> "Folder | None":
        for sf in self.special_folders:
            if sf.folder_type == FolderType.HOME:
                return sf.folder
        return None

    @property
    def inbox_folder(self) -> "Folder | None":
        for sf in self.special_folders:
            if sf.folder_type == FolderType.INBOX:
                return sf.folder
        return None



class Node(Base, AuditColumns):
    __tablename__ = "nodes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, insert_default=uuid.uuid4())
    title: Mapped[str] = mapped_column(String(200))
    ctype: Mapped[CType]
    lang: Mapped[str] = mapped_column(String(8), default="deu")

    parent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nodes.id"), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "node",
        "polymorphic_on": "ctype",
        "confirm_deleted_rows": False,
    }

    def __repr__(self):
        return f"{self.__class__.__name__}({self.title!r})"


class Folder(Node):
    __tablename__ = "folders"

    id: Mapped[uuid.UUID] = mapped_column(
        "node_id",
        ForeignKey("nodes.id", ondelete="CASCADE"),
        primary_key=True,
        insert_default=uuid.uuid4,
    )

    __mapper_args__ = {
        "polymorphic_identity": "folder",
    }


class Document(Node):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        "node_id",
        ForeignKey("nodes.id", ondelete="CASCADE"),
        primary_key=True,
        default=uuid.uuid4,
    )
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document", lazy="selectin"
    )
    
    # Image preview status (for thumbnails)
    preview_status: Mapped[str] = mapped_column(nullable=True)
    preview_error: Mapped[str] = mapped_column(nullable=True)
    
    # Document processing status (for upload processing)
    processing_status: Mapped[str] = mapped_column(nullable=True)
    processing_error: Mapped[str] = mapped_column(nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "document",
    }


class DocumentVersion(Base, AuditColumns):
    __tablename__ = "document_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    number: Mapped[int] = mapped_column(default=1)
    file_name: Mapped[str] = mapped_column(nullable=True)
    size: Mapped[int] = mapped_column(default=0)
    page_count: Mapped[int] = mapped_column(default=0)
    mime_type: Mapped[str] = mapped_column(nullable=True)
    lang: Mapped[str] = mapped_column(default="deu")

    # Version lineage tracking
    is_original: Mapped[bool] = mapped_column(default=False, nullable=True)
    source_version_id: Mapped[uuid.UUID] = mapped_column(nullable=True)
    creation_reason: Mapped[str] = mapped_column(nullable=True)
    
    document: Mapped[Document] = relationship(back_populates="versions")
    pages: Mapped[list["Page"]] = relationship(
        back_populates="document_version", lazy="select"
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.node_id")
    )


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    number: Mapped[int]
    page_count: Mapped[int] = mapped_column(default=0)
    lang: Mapped[str] = mapped_column(default="deu", nullable=True)
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_versions.id")
    )
    document_version: Mapped[DocumentVersion] = relationship(back_populates="pages")


class Ownership(Base):
    """
    Central table managing ownership relationships.

    One resource can have ONE owner (enforced by unique constraint).
    If you need multi-ownership in future, remove the unique constraint.
    """
    __tablename__ = "ownerships"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Who owns it
    owner_type: Mapped[str] = mapped_column(String(20), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    # What is owned
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        # Ensure valid owner types
        CheckConstraint(
            "owner_type IN ('user', 'group')",
            name="ownerships_owner_type_check"
        ),
        # Ensure valid resource types
        CheckConstraint(
            "resource_type IN ('node', 'custom_field', 'document_type', 'tag')",
            name="ownerships_resource_type_check"
        ),
        # ONE owner per resource (remove if you want multi-ownership)
        UniqueConstraint('resource_type', 'resource_id', name='uq_resource_owner'),
    )

class SpecialFolder(Base):
    __tablename__ = "special_folders"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Polymorphic owner (user or group)
    owner_type: Mapped[OwnerType] = mapped_column(
        SQLEnum(
            OwnerType,
            name="owner_type_enum",
            values_callable=lambda x: [e.value for e in x],
            create_type=False
        ),
        nullable=False,
        index=True,
        comment="Type of owner: 'user' or 'group'"
    )

    owner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="UUID of the user or group that owns this special folder"
    )

    # Type of special folder
    folder_type: Mapped[FolderType] = mapped_column(
        SQLEnum(
            FolderType,
            name="folder_type_enum",
            values_callable=lambda x: [e.value for e in x],
            create_type=False
        ),
        nullable=False,
        comment="Type of special folder: 'home', 'inbox', etc."
    )

    # Reference to the actual folder node
    folder_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("folders.node_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the actual folder in the nodes/folders table"
    )

    # Relationship to the folder
    # Note: We use foreign_keys and don't set back_populates
    # because Folder doesn't need to know about SpecialFolder
    folder: Mapped["Folder"] = relationship(
        "Folder",
        foreign_keys=[folder_id],
        lazy="joined",  # Eager load by default for convenience
        viewonly=True   # One-directional relationship
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    __table_args__ = (
        # Each owner can have only ONE folder of each type
        # e.g., a user can have only one HOME folder, one INBOX folder, etc.
        UniqueConstraint(
            'owner_type',
            'owner_id',
            'folder_type',
            name='uq_special_folder_per_owner'
        ),
    )

    def __repr__(self):
        return (
            f"SpecialFolder("
            f"owner={self.owner_type.value}:{self.owner_id}, "
            f"type={self.folder_type.value}, "
            f"folder_id={self.folder_id})"
        )

    def __str__(self):
        return f"{self.owner_type.value}'s {self.folder_type.value} folder"

