from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import TIMESTAMP



def utc_now():
    """Returns current time in UTC - always use for database timestamps"""
    return datetime.now(timezone.utc)


class AuditColumns:
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

    # Audit user foreign keys
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT", deferrable=True, initially='DEFERRED'),
        nullable=False
    )
    updated_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT", deferrable=True, initially='DEFERRED'),
        nullable=False
    )
    deleted_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    archived_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
