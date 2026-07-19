"""Base Service.

Provides a foundational class for all business services.
Services are instantiated per request/command and are responsible for
orchestrating repository calls and applying business logic.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from expense_tracker.core.constants import AuditAction
from expense_tracker.core.logging import get_logger
from expense_tracker.repositories.audit_log_repository import AuditLogRepository

logger = get_logger(__name__)


class BaseService:
    """Base class for business logic services.

    Provides common functionality for auditing mutations.
    """

    def __init__(self, audit_repo: AuditLogRepository | None = None) -> None:
        """Initialize the base service.

        Args:
            audit_repo: Optional AuditLogRepository for tracking mutations.
                If not provided, a new instance is created.
        """
        self.audit_repo = audit_repo or AuditLogRepository()

    async def _audit(
        self,
        session: AsyncSession,
        entity_type: str,
        entity_id: uuid.UUID,
        action: AuditAction,
        changes: dict[str, Any] | None = None,
        user_id: uuid.UUID | None = None,
    ) -> None:
        """Log a mutation in the audit trail.

        Args:
            session: The async database session.
            entity_type: Type of the entity affected.
            entity_id: UUID of the affected entity.
            action: Action performed (CREATE, UPDATE, DELETE).
            changes: JSON-serializable dict of before/after changes.
            user_id: Optional UUID of the user who performed the action.
        """
        try:
            await self.audit_repo.log_action(
                session=session,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action.value,
                changes=changes,
                user_id=user_id,
            )
        except Exception as exc:
            # We log the error but don't fail the transaction if auditing fails
            # In a strict compliance environment, this should probably raise.
            logger.exception(
                "audit_log_failed",
                entity_type=entity_type,
                entity_id=str(entity_id),
                action=action.value,
                error=str(exc),
            )
