import uuid
from typing import Literal
from sqlalchemy import ForeignKey, Enum, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from s3worker.types import ImagePreviewStatus

CType = Literal["document", "folder"]


class Base(DeclarativeBase):
    pass



class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, insert_default=uuid.uuid4())
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    first_name: Mapped[str] = mapped_column(default=" ")
    last_name: Mapped[str] = mapped_column(default=" ")
    password: Mapped[str] = mapped_column(nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    nodes: Mapped[list["Node"]] = relationship(
        back_populates="user", primaryjoin="User.id == Node.user_id", cascade="delete"
    )
    home_folder_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("folders.node_id", deferrable=True, ondelete="CASCADE"),
        nullable=True,
    )
    home_folder: Mapped["Folder"] = relationship(
        primaryjoin="User.home_folder_id == Folder.id",
        back_populates="user",
        viewonly=True,
        cascade="delete",
    )
    inbox_folder_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("folders.node_id", deferrable=True, ondelete="CASCADE"),
        nullable=True,
    )
    inbox_folder: Mapped["Folder"] = relationship(
        primaryjoin="User.inbox_folder_id == Folder.id",
        back_populates="user",
        viewonly=True,
        cascade="delete",
    )


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, insert_default=uuid.uuid4())
    title: Mapped[str] = mapped_column(String(200))
    ctype: Mapped[CType]
    lang: Mapped[str] = mapped_column(String(8), default="deu")
    user: Mapped["User"] = relationship(
        back_populates="nodes",
        primaryjoin="User.id == Node.user_id",
        remote_side=User.id,
        cascade="delete",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id", use_alter=True, name="nodes_user_id_fkey", ondelete="CASCADE"
        ),
        nullable=True,
    )

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



class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column('node_id', primary_key=True)
    preview_status: Mapped[str] = mapped_column(nullable=True)
    preview_error: Mapped[str] = mapped_column(nullable=True)


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    number: Mapped[int]
    file_name: Mapped[str]
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.node_id")
    )


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    number: Mapped[int]
    document_version_id: Mapped[uuid.UUID] = mapped_column(
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
