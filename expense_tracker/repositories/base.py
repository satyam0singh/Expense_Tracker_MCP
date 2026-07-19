"""Generic async repository with CRUD operations.

Provides a type-safe base repository that handles the most common
data access patterns: create, read, update, soft-delete, restore,
and hard-delete. All entity-specific repositories extend this base
and add domain-specific query methods.

Design Decisions:
    - Generic over model type T for full type safety.
    - Soft-delete filtering is ON by default (exclude deleted records).
    - Pagination returns (items, total_count) for client-side paging.
    - Session is passed per-call, not stored on the instance, to support
      both request-scoped and unit-of-work patterns.
    - All methods are async for non-blocking database access.

Usage:
    class ExpenseRepository(BaseRepository[Expense]):
        def __init__(self) -> None:
            super().__init__(Expense)

        async def find_by_category(
            self, session: AsyncSession, category_id: UUID
        ) -> list[Expense]:
            ...
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from expense_tracker.core.exceptions import DatabaseError, NotFoundError
from expense_tracker.core.logging import get_logger
from expense_tracker.database.base import BaseModel

logger = get_logger(__name__)

# Type variable bound to BaseModel — ensures all repos work with ORM entities
T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """Generic async repository providing standard CRUD operations.

    All queries automatically exclude soft-deleted records unless
    explicitly requested via include_deleted=True.

    Attributes:
        model: The SQLAlchemy ORM model class this repository manages.
    """

    def __init__(self, model: type[T]) -> None:
        """Initialize the repository with a model class.

        Args:
            model: The SQLAlchemy ORM model class (e.g., Expense, Budget).
        """
        self.model = model
        self._model_name = model.__name__

    # ── Create ───────────────────────────────────────────────

    async def create(self, session: AsyncSession, **kwargs: Any) -> T:
        """Create and persist a new entity.

        Args:
            session: The async database session.
            **kwargs: Column values for the new entity.

        Returns:
            The created entity with server-generated fields populated.

        Raises:
            DatabaseError: If the insert operation fails.
        """
        try:
            entity = self.model(**kwargs)
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            logger.debug(
                "entity_created",
                model=self._model_name,
                entity_id=str(entity.id),
            )
            return entity
        except Exception as exc:
            logger.exception(
                "create_failed",
                model=self._model_name,
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to create {self._model_name}.",
            ) from exc

    async def create_from_entity(self, session: AsyncSession, entity: T) -> T:
        """Persist a pre-built entity instance.

        Use this when the entity is constructed outside the repository
        (e.g., with complex relationship setup).

        Args:
            session: The async database session.
            entity: The pre-built ORM entity to persist.

        Returns:
            The persisted entity with server-generated fields populated.

        Raises:
            DatabaseError: If the insert operation fails.
        """
        try:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            logger.debug(
                "entity_created",
                model=self._model_name,
                entity_id=str(entity.id),
            )
            return entity
        except Exception as exc:
            logger.exception(
                "create_failed",
                model=self._model_name,
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to create {self._model_name}.",
            ) from exc

    # ── Read ─────────────────────────────────────────────────

    async def get_by_id(
        self,
        session: AsyncSession,
        entity_id: uuid.UUID,
        *,
        include_deleted: bool = False,
    ) -> T | None:
        """Retrieve a single entity by its UUID primary key.

        Args:
            session: The async database session.
            entity_id: The UUID of the entity to retrieve.
            include_deleted: If True, also return soft-deleted records.

        Returns:
            The entity if found, None otherwise.
        """
        stmt = select(self.model).where(self.model.id == entity_id)
        if not include_deleted:
            stmt = self._apply_soft_delete_filter(stmt)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(
        self,
        session: AsyncSession,
        entity_id: uuid.UUID,
        *,
        include_deleted: bool = False,
    ) -> T:
        """Retrieve a single entity or raise NotFoundError.

        Args:
            session: The async database session.
            entity_id: The UUID of the entity to retrieve.
            include_deleted: If True, also return soft-deleted records.

        Returns:
            The entity.

        Raises:
            NotFoundError: If the entity does not exist.
        """
        entity = await self.get_by_id(
            session, entity_id, include_deleted=include_deleted
        )
        if entity is None:
            raise NotFoundError(self._model_name, str(entity_id))
        return entity

    async def get_all(
        self,
        session: AsyncSession,
        *,
        offset: int = 0,
        limit: int = 50,
        include_deleted: bool = False,
        order_by: Any | None = None,
    ) -> tuple[list[T], int]:
        """Retrieve all entities with pagination.

        Args:
            session: The async database session.
            offset: Number of records to skip (0-indexed).
            limit: Maximum number of records to return.
            include_deleted: If True, include soft-deleted records.
            order_by: SQLAlchemy column or expression for ordering.
                Defaults to created_at descending.

        Returns:
            Tuple of (list of entities, total count across all pages).
        """
        base_stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)

        if not include_deleted:
            base_stmt = self._apply_soft_delete_filter(base_stmt)
            count_stmt = count_stmt.where(
                self.model.deleted_at.is_(None),
            )

        # Total count
        count_result = await session.execute(count_stmt)
        total = count_result.scalar_one()

        # Paginated results
        if order_by is not None:
            base_stmt = base_stmt.order_by(order_by)
        else:
            base_stmt = base_stmt.order_by(self.model.created_at.desc())

        base_stmt = base_stmt.offset(offset).limit(limit)
        result = await session.execute(base_stmt)
        items = list(result.scalars().all())

        return items, total

    # ── Update ───────────────────────────────────────────────

    async def update(
        self,
        session: AsyncSession,
        entity_id: uuid.UUID,
        **kwargs: Any,
    ) -> T:
        """Update an existing entity's fields.

        Only provided kwargs are updated; None values are set explicitly.
        Fields not in kwargs are left unchanged.

        Args:
            session: The async database session.
            entity_id: The UUID of the entity to update.
            **kwargs: Column name to new value mappings.

        Returns:
            The updated entity.

        Raises:
            NotFoundError: If the entity does not exist.
            DatabaseError: If the update operation fails.
        """
        entity = await self.get_by_id_or_raise(session, entity_id)
        try:
            for key, value in kwargs.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            await session.flush()
            await session.refresh(entity)
            logger.debug(
                "entity_updated",
                model=self._model_name,
                entity_id=str(entity_id),
                fields=list(kwargs.keys()),
            )
            return entity
        except NotFoundError:
            raise
        except Exception as exc:
            logger.exception(
                "update_failed",
                model=self._model_name,
                entity_id=str(entity_id),
                error=str(exc),
            )
            raise DatabaseError(
                f"Failed to update {self._model_name}.",
            ) from exc

    # ── Soft Delete / Restore ────────────────────────────────

    async def soft_delete(
        self,
        session: AsyncSession,
        entity_id: uuid.UUID,
    ) -> T:
        """Soft-delete an entity by setting deleted_at.

        The record remains in the database but is excluded from
        default queries.

        Args:
            session: The async database session.
            entity_id: The UUID of the entity to soft-delete.

        Returns:
            The soft-deleted entity.

        Raises:
            NotFoundError: If the entity does not exist.
        """
        entity = await self.get_by_id_or_raise(session, entity_id)
        entity.deleted_at = datetime.now(timezone.utc)  # type: ignore[assignment]
        await session.flush()
        await session.refresh(entity)
        logger.debug(
            "entity_soft_deleted",
            model=self._model_name,
            entity_id=str(entity_id),
        )
        return entity

    async def restore(
        self,
        session: AsyncSession,
        entity_id: uuid.UUID,
    ) -> T:
        """Restore a soft-deleted entity by clearing deleted_at.

        Args:
            session: The async database session.
            entity_id: The UUID of the entity to restore.

        Returns:
            The restored entity.

        Raises:
            NotFoundError: If the entity does not exist (even when deleted).
        """
        entity = await self.get_by_id(
            session, entity_id, include_deleted=True
        )
        if entity is None:
            raise NotFoundError(self._model_name, str(entity_id))
        entity.deleted_at = None  # type: ignore[assignment]
        await session.flush()
        await session.refresh(entity)
        logger.debug(
            "entity_restored",
            model=self._model_name,
            entity_id=str(entity_id),
        )
        return entity

    # ── Hard Delete ──────────────────────────────────────────

    async def hard_delete(
        self,
        session: AsyncSession,
        entity_id: uuid.UUID,
    ) -> bool:
        """Permanently delete an entity from the database.

        Use with caution — this is irreversible.

        Args:
            session: The async database session.
            entity_id: The UUID of the entity to delete.

        Returns:
            True if the entity was deleted.

        Raises:
            NotFoundError: If the entity does not exist.
        """
        entity = await self.get_by_id(
            session, entity_id, include_deleted=True
        )
        if entity is None:
            raise NotFoundError(self._model_name, str(entity_id))
        await session.delete(entity)
        await session.flush()
        logger.debug(
            "entity_hard_deleted",
            model=self._model_name,
            entity_id=str(entity_id),
        )
        return True

    # ── Count ────────────────────────────────────────────────

    async def count(
        self,
        session: AsyncSession,
        *,
        include_deleted: bool = False,
    ) -> int:
        """Count total entities.

        Args:
            session: The async database session.
            include_deleted: If True, include soft-deleted records.

        Returns:
            The total number of entities.
        """
        stmt = select(func.count()).select_from(self.model)
        if not include_deleted:
            stmt = stmt.where(self.model.deleted_at.is_(None))
        result = await session.execute(stmt)
        return result.scalar_one()

    async def exists(
        self,
        session: AsyncSession,
        entity_id: uuid.UUID,
        *,
        include_deleted: bool = False,
    ) -> bool:
        """Check if an entity exists by ID.

        Args:
            session: The async database session.
            entity_id: The UUID to check.
            include_deleted: If True, include soft-deleted records.

        Returns:
            True if the entity exists.
        """
        entity = await self.get_by_id(
            session, entity_id, include_deleted=include_deleted
        )
        return entity is not None

    # ── Internal Helpers ─────────────────────────────────────

    def _apply_soft_delete_filter(self, stmt: Select[tuple[T]]) -> Select[tuple[T]]:
        """Add soft-delete exclusion to a query.

        Args:
            stmt: The SQLAlchemy select statement.

        Returns:
            The statement with deleted_at IS NULL filter applied.
        """
        return stmt.where(self.model.deleted_at.is_(None))
