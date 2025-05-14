from uuid import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(
        'node_id',
        ForeignKey("nodes.id"), primary_key=True
    )
    preview_status: Mapped[str] = mapped_column(nullable=True)
    preview_error: Mapped[str] = mapped_column(nullable=True)


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    number: Mapped[int]
    file_name: Mapped[str]
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.node_id")
    )


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    number: Mapped[int]
    document_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_versions.id")
    )
