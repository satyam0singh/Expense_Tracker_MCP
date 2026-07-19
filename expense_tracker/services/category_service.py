"""Category Service.

Handles business logic for categories and subcategories,
including resolving category names to UUIDs.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from expense_tracker.core.constants import DEFAULT_CATEGORIES
from expense_tracker.core.exceptions import NotFoundError, ValidationError
from expense_tracker.core.logging import get_logger
from expense_tracker.database.models.category import Category
from expense_tracker.repositories.category_repository import CategoryRepository
from expense_tracker.services.base import BaseService

logger = get_logger(__name__)


class CategoryService(BaseService):
    """Service for managing categories and subcategories."""

    def __init__(self, repo: CategoryRepository | None = None) -> None:
        """Initialize the category service.

        Args:
            repo: Optional CategoryRepository.
        """
        super().__init__()
        self.repo = repo or CategoryRepository()

    async def get_all_categories(
        self,
        session: AsyncSession,
    ) -> list[Category]:
        """Get all categories with subcategories.

        Args:
            session: The async database session.

        Returns:
            List of categories.
        """
        return await self.repo.get_all_with_subcategories(session)

    async def resolve_category_id(
        self,
        session: AsyncSession,
        category_id: uuid.UUID | None = None,
        category_name: str | None = None,
    ) -> uuid.UUID:
        """Resolve a category ID from either an ID or a name.

        Args:
            session: The async database session.
            category_id: The category UUID (if known).
            category_name: The category name (if UUID is unknown).

        Returns:
            The resolved category UUID.

        Raises:
            ValidationError: If neither ID nor name is provided.
            NotFoundError: If the category does not exist.
        """
        if category_id is not None:
            # Verify it exists
            exists = await self.repo.exists(session, category_id)
            if not exists:
                raise NotFoundError("Category", str(category_id))
            return category_id

        if category_name is not None:
            category = await self.repo.find_by_name(session, category_name)
            if category is None:
                raise NotFoundError("Category", category_name)
            return category.id

        raise ValidationError("Either category_id or category_name must be provided")

    async def resolve_subcategory_id(
        self,
        session: AsyncSession,
        category_id: uuid.UUID,
        subcategory_id: uuid.UUID | None = None,
        subcategory_name: str | None = None,
    ) -> uuid.UUID | None:
        """Resolve a subcategory ID from either an ID or a name.

        Args:
            session: The async database session.
            category_id: The parent category UUID.
            subcategory_id: The subcategory UUID (if known).
            subcategory_name: The subcategory name (if UUID is unknown).

        Returns:
            The resolved subcategory UUID, or None if neither was provided.

        Raises:
            NotFoundError: If the subcategory does not exist in the parent category.
        """
        if subcategory_id is None and subcategory_name is None:
            return None

        # To resolve or verify a subcategory, we need the parent category
        # loaded with its subcategories.
        category = await self.repo.get_with_subcategories(session, category_id)
        if category is None:
            raise NotFoundError("Category", str(category_id))

        if subcategory_id is not None:
            for sub in category.subcategories:
                if sub.id == subcategory_id:
                    return sub.id
            raise NotFoundError("Subcategory", str(subcategory_id))

        if subcategory_name is not None:
            target_name = subcategory_name.lower()
            for sub in category.subcategories:
                if sub.name.lower() == target_name:
                    return sub.id
            raise NotFoundError("Subcategory", subcategory_name)

        return None

    async def initialize_default_categories(
        self,
        session: AsyncSession,
    ) -> dict[str, int]:
        """Seed the database with the default category taxonomy.

        Args:
            session: The async database session.

        Returns:
            Dict with 'imported' and 'skipped' counts.
        """
        return await self.repo.bulk_upsert(session, DEFAULT_CATEGORIES)
