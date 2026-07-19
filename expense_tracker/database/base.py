"""SQLAlchemy declarative base and model mixins.

Provides reusable mixins for UUID primary keys, timestamps,
and soft-delete functionality. All ORM models should inherit
from BaseModel, which composes all three mixins.

Mixins:
    UUIDMixin: Adds a UUID primary key with server-side default.
    TimestampMixin: Adds created_at and updated_at columns.
    SoftDeleteMixin: Adds deleted_at column and is_deleted hybrid property.
    BaseModel: Combines all mixins into a single base class.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column

# Naming convention for constraints and indexes.
# This ensures Alembic can generate deterministic migration names.
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """SQLAlchemy declarative base with naming conventions.

    All ORM models must ultimately inherit from this class
    (typically via BaseModel).
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDMixin:
    """Mixin that adds a UUID primary key.

    The UUID is generated server-side using PostgreSQL's gen_random_uuid()
    for maximum compatibility and performance.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
        sort_order=-10,
    )


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp columns.

    Both columns use server-side defaults for consistency across
    application instances and direct database operations.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False,
        sort_order=100,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
        server_onupdate=func.now(),
        nullable=False,
        sort_order=101,
    )


class SoftDeleteMixin:
    """Mixin that adds soft-delete support via a deleted_at timestamp.

    Records are never physically deleted from the database. Instead,
    deleted_at is set to the current timestamp. Queries should filter
    on is_deleted to exclude soft-deleted records by default.

    The restore operation simply sets deleted_at back to None.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
        sort_order=102,
    )

    @hybrid_property
    def is_deleted(self) -> bool:
        """Whether this record has been soft-deleted.

        Returns:
            True if deleted_at is set, False otherwise.
        """
        return self.deleted_at is not None

    @is_deleted.expression  # type: ignore[no-redef]
    @classmethod
    def is_deleted(cls) -> Any:
        """SQL expression for filtering soft-deleted records.

        Returns:
            SQLAlchemy expression: deleted_at IS NOT NULL.
        """
        return cls.deleted_at.isnot(None)


class BaseModel(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Abstract base model combining UUID, timestamps, and soft-delete.

    All application ORM models (Expense, Category, Budget, etc.)
    should inherit from this class.

    Example:
        class Expense(BaseModel):
            __tablename__ = "expenses"
            title: Mapped[str] = mapped_column(String(255))
            amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    """

    __abstract__ = True

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return f"<{self.__class__.__name__}(id={self.id})>"
