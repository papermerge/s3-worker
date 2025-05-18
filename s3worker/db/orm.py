from uuid import UUID
from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from s3worker.types import ImagePreviewStatus

class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column('node_id', primary_key=True)
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
    # `preview_status`
    #  NULL   = no preview available -> image_url will be empty
    #  Ready  = preview available -> image_url will point to preview image
    #  Failed = preview generation failed -> image_url is empty
    #        in which case `preview_error` will contain error why preview
    #        generation failed
    preview_status_sm: Mapped[str] = mapped_column(Enum(ImagePreviewStatus, name="preview_status"), nullable=True)
    preview_status_md: Mapped[str] = mapped_column(Enum(ImagePreviewStatus, name="preview_status"), nullable=True)
    preview_status_lg: Mapped[str] = mapped_column(Enum(ImagePreviewStatus, name="preview_status"), nullable=True)
    preview_status_xl: Mapped[str] = mapped_column(Enum(ImagePreviewStatus, name="preview_status"), nullable=True)
    # `preview_error`
    # only for troubleshooting purposes. Relevant only in case
    # `preview_status` = Failed
    preview_error_sm: Mapped[str] = mapped_column(Enum(ImagePreviewStatus, name="preview_status"), nullable=True)
    preview_error_md: Mapped[str] = mapped_column(Enum(ImagePreviewStatus, name="preview_status"), nullable=True)
    preview_error_lg: Mapped[str] = mapped_column(Enum(ImagePreviewStatus, name="preview_status"), nullable=True)
    preview_error_xl: Mapped[str] = mapped_column(Enum(ImagePreviewStatus, name="preview_status"), nullable=True)
