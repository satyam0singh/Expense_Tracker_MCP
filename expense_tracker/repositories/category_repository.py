"""Category repository — data access for categories and subcategories.

Extends BaseRepository with category-specific queries: find by name,
get with subcategories, and bulk upsert for the category import tool.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from expense_tracker.core.logging import get_logger
from expense_tracker.database.models.category import Category
from expense_tracker.database.models.subcategory import Subcategory
from expense_tracker.repositories.base import BaseRepository

logger = get_logger(__name__)


class CategoryRepository(BaseRepository[Category]):
    """Repository for category and subcategory data access.

    Manages the two-level category taxonomy (categories + subcategories).
    """

    def __init__(self) -> None:
        """Initialize with the Category model."""
        super().__init__(Category)

    async def find_by_name(
        self,
        session: AsyncSession,
        name: str,
    ) -> Category | None:
        """Find a category by its unique name.

        Args:
            session: The async database session.
            name: The category name (case-insensitive match).

        Returns:
            The category if found, None otherwise.
        """
        stmt = (
            select(Category)
            .where(
                Category.deleted_at.is_(None),
                func.lower(Category.name) == name.lower(),
            )
            .options(selectinload(Category.subcategories))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_subcategories(
        self,
        session: AsyncSession,
        category_id: uuid.UUID,
    ) -> Category | None:
        """Get a category with its subcategories eagerly loaded.

        Args:
            session: The async database session.
            category_id: The category UUID.

        Returns:
            The category with subcategories loaded, or None.
        """
        stmt = (
            select(Category)
            .where(
                Category.id == category_id,
                Category.deleted_at.is_(None),
            )
            .options(selectinload(Category.subcategories))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_with_subcategories(
        self,
        session: AsyncSession,
    ) -> list[Category]:
        """Get all categories with their subcategories.

        Args:
            session: The async database session.

        Returns:
            List of all active categories with subcategories loaded.
        """
        stmt = (
            select(Category)
            .where(Category.deleted_at.is_(None))
            .options(selectinload(Category.subcategories))
            .order_by(Category.sort_order.asc(), Category.name.asc())
        )
        result = await session.execute(stmt)
        return list(result.unique().scalars().all())

    async def bulk_upsert(
        self,
        session: AsyncSession,
        categories: dict[str, list[str]],
    ) -> dict[str, int]:
        """Bulk import categories and subcategories.

        Uses PostgreSQL ON CONFLICT for upsert behavior — existing
        categories are updated, new ones are inserted.

        Args:
            session: The async database session.
            categories: Dict mapping category names to lists of
                subcategory names.

        Returns:
            Dict with 'imported' and 'skipped' counts.
        """
        imported = 0
        skipped = 0

        for sort_idx, (cat_name, subcategories) in enumerate(categories.items()):
            # Upsert category
            display_name = cat_name.replace("_", " ").title()

            # Check if category already exists
            existing = await self.find_by_name(session, cat_name)

            if existing is None:
                category = Category(
                    name=cat_name,
                    display_name=display_name,
                    sort_order=sort_idx,
                    is_system=True,
                )
                session.add(category)
                await session.flush()
                imported += 1
                cat_id = category.id
            else:
                cat_id = existing.id
                # Update sort order for existing categories
                existing.sort_order = sort_idx
                await session.flush()
                skipped += 1

            # Upsert subcategories
            for sub_idx, sub_name in enumerate(subcategories):
                sub_display = sub_name.replace("_", " ").title()

                # Check if subcategory already exists
                sub_stmt = select(Subcategory).where(
                    Subcategory.category_id == cat_id,
                    func.lower(Subcategory.name) == sub_name.lower(),
                )
                sub_result = await session.execute(sub_stmt)
                existing_sub = sub_result.scalar_one_or_none()

                if existing_sub is None:
                    subcategory = Subcategory(
                        category_id=cat_id,
                        name=sub_name,
                        display_name=sub_display,
                        sort_order=sub_idx,
                    )
                    session.add(subcategory)

            await session.flush()

        logger.info(
            "categories_bulk_upserted",
            imported=imported,
            skipped=skipped,
            total=imported + skipped,
        )

        return {"imported": imported, "skipped": skipped}

    async def name_exists(
        self,
        session: AsyncSession,
        name: str,
    ) -> bool:
        """Check if a category name already exists.

        Args:
            session: The async database session.
            name: The category name to check.

        Returns:
            True if the name is already taken.
        """
        stmt = (
            select(func.count())
            .select_from(Category)
            .where(
                Category.deleted_at.is_(None),
                func.lower(Category.name) == name.lower(),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one() > 0
