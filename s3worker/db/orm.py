import uuid
from typing import Literal
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .audit_cols import AuditColumns
from .base import Base

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


class Node(Base):
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
