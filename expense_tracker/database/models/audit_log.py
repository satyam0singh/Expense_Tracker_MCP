"""AuditLog ORM model.

Immutable log of all data mutations in the system. Records who
changed what, when, and stores before/after diffs in a JSONB
column for compliance, debugging, and undo capability.

Unlike other models, AuditLog does NOT use soft-delete (audit
records are permanent) and inherits only UUID and timestamp mixins.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func, JSON
from sqlalchemy import Uuid as UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from expense_tracker.database.base import Base, UUIDMixin


class AuditLog(UUIDMixin, Base):
    """Immutable audit trail entry.

    Does NOT inherit SoftDeleteMixin — audit records are permanent.

    Attributes:
        user_id: FK to the user who performed the action (nullable for system actions).
        entity_type: Type of entity affected (e.g., 'expense', 'budget').
        entity_id: UUID of the affected entity.
        action: The action performed (create, update, delete, restore).
        changes: JSONB diff of before/after values.
        ip_address: Client IP address (for future web API).
        timestamp: When the action occurred.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_timestamp", "timestamp"),
        Index("ix_audit_user_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    changes: Mapped[dict | None] = mapped_column(  # type: ignore[type-arg]
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
        default=None,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        default=None,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"<AuditLog(id={self.id}, entity={self.entity_type}:"
            f"{self.entity_id}, action='{self.action}')>"
        )
