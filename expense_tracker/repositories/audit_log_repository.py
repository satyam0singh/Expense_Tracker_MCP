"""AuditLog repository — data access for audit records.

Extends BaseRepository with audit-specific queries: logging actions,
fetching entity history, and querying by action type.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from expense_tracker.core.logging import get_logger
from expense_tracker.database.models.audit_log import AuditLog
from expense_tracker.repositories.base import BaseRepository

logger = get_logger(__name__)


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for audit log access.

    Provides methods to append immutable audit records and query
    entity mutation history. Does not support updates or deletes.
    """

    def __init__(self) -> None:
        """Initialize with the AuditLog model."""
        super().__init__(AuditLog)

    async def log_action(
        self,
        session: AsyncSession,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        changes: dict[str, Any] | None = None,
        user_id: uuid.UUID | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """Record a new action in the audit log.

        Args:
            session: The async database session.
            entity_type: Type of the entity affected.
            entity_id: UUID of the affected entity.
            action: Action performed (e.g., CREATE, UPDATE, DELETE).
            changes: JSON-serializable dict of before/after changes.
            user_id: UUID of the user who performed the action.
            ip_address: Optional IP address of the requester.

        Returns:
            The created AuditLog entry.
        """
        log_entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changes=changes,
            user_id=user_id,
            ip_address=ip_address,
            timestamp=datetime.now(timezone.utc),
        )
        session.add(log_entry)
        await session.flush()
        
        # Don't strictly need to refresh if we don't return it, but
        # helpful for completeness and testing
        await session.refresh(log_entry)
        
        logger.debug(
            "audit_log_created",
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
        )
        return log_entry

    async def get_entity_history(
        self,
        session: AsyncSession,
        entity_type: str,
        entity_id: uuid.UUID,
        *,
        limit: int = 100,
    ) -> list[AuditLog]:
        """Get the audit history for a specific entity.

        Args:
            session: The async database session.
            entity_type: Type of the entity.
            entity_id: UUID of the entity.
            limit: Maximum number of records to return.

        Returns:
            List of audit logs ordered by timestamp descending (newest first).
        """
        stmt = (
            select(AuditLog)
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.unique().scalars().all())

    # Override mutable methods to prevent modification of audit logs
    
    async def update(self, *args: Any, **kwargs: Any) -> AuditLog:
        """Prevent updates to audit logs."""
        raise NotImplementedError("Audit logs are immutable and cannot be updated.")
        
    async def soft_delete(self, *args: Any, **kwargs: Any) -> AuditLog:
        """Prevent soft-deletion of audit logs."""
        raise NotImplementedError("Audit logs cannot be soft-deleted.")
        
    async def restore(self, *args: Any, **kwargs: Any) -> AuditLog:
        """Prevent restore of audit logs."""
        raise NotImplementedError("Audit logs cannot be restored.")
        
    async def hard_delete(self, *args: Any, **kwargs: Any) -> bool:
        """Prevent hard-deletion of audit logs."""
        raise NotImplementedError("Audit logs are immutable and cannot be deleted.")
