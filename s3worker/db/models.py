from uuid import UUID
from sqlalchemy import Column, ForeignKey, String, Table, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass



class Document(Base):
    __tablename__ = "core_document"

    id: Mapped[UUID] = mapped_column(
        'basetreenode_ptr_id',
        ForeignKey("core_basetreenode.id"), primary_key=True
    )


class DocumentVersion(Base):
    __tablename__ = "core_documentversion"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    number: Mapped[int]
    file_name: Mapped[str]
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_document.basetreenode_ptr_id")
    )


class Page(Base):
    __tablename__ = "core_page"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    number: Mapped[int]
    document_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_documentversion.id")
    )
