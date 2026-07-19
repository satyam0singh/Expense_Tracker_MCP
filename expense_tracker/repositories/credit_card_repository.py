"""CreditCard repository — data access for credit card records.

Extends BaseRepository with card-specific queries: get active cards,
upcoming due dates, and usage updates.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from expense_tracker.core.logging import get_logger
from expense_tracker.database.models.credit_card import CreditCard
from expense_tracker.repositories.base import BaseRepository

logger = get_logger(__name__)


class CreditCardRepository(BaseRepository[CreditCard]):
    """Repository for credit card data access.

    Manages credit cards, usage limits, and billing cycles.
    """

    def __init__(self) -> None:
        """Initialize with the CreditCard model."""
        super().__init__(CreditCard)

    async def get_active_cards(
        self,
        session: AsyncSession,
        *,
        user_id: uuid.UUID | None = None,
    ) -> list[CreditCard]:
        """Get all active credit cards for a user.

        Args:
            session: The async database session.
            user_id: Optional filter by user.

        Returns:
            List of active credit cards.
        """
        conditions: list[Any] = [
            CreditCard.deleted_at.is_(None),
            CreditCard.is_active.is_(True),
        ]
        if user_id is not None:
            conditions.append(CreditCard.user_id == user_id)

        stmt = select(CreditCard).where(*conditions).order_by(CreditCard.card_name.asc())
        result = await session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_upcoming_due(
        self,
        session: AsyncSession,
        days_ahead: int = 30,
        *,
        user_id: uuid.UUID | None = None,
    ) -> list[CreditCard]:
        """Get credit cards with due dates within the next N days.

        Args:
            session: The async database session.
            days_ahead: Number of days to look ahead.
            user_id: Optional filter by user.

        Returns:
            List of credit cards with upcoming due dates.
        """
        today = date.today()
        target_date = today + timedelta(days=days_ahead)

        conditions: list[Any] = [
            CreditCard.deleted_at.is_(None),
            CreditCard.is_active.is_(True),
            CreditCard.due_date.isnot(None),
            CreditCard.due_date >= today,
            CreditCard.due_date <= target_date,
            CreditCard.used_amount > 0,
        ]
        if user_id is not None:
            conditions.append(CreditCard.user_id == user_id)

        stmt = select(CreditCard).where(*conditions).order_by(CreditCard.due_date.asc())
        result = await session.execute(stmt)
        return list(result.unique().scalars().all())

    async def update_usage(
        self,
        session: AsyncSession,
        card_id: uuid.UUID,
        amount: Decimal,
        *,
        is_payment: bool = False,
    ) -> CreditCard:
        """Update the used amount on a credit card.

        Args:
            session: The async database session.
            card_id: The credit card UUID.
            amount: The amount to add to (or subtract from) usage.
            is_payment: If True, subtract amount (payment). If False, add (charge).

        Returns:
            The updated credit card.
        """
        card = await self.get_by_id_or_raise(session, card_id)
        
        if is_payment:
            # Payment decreases usage (can't go below 0 via check constraint)
            card.used_amount -= amount  # type: ignore[assignment]
        else:
            # Charge increases usage
            card.used_amount += amount  # type: ignore[assignment]
            
        await session.flush()
        await session.refresh(card)
        logger.debug(
            "credit_card_usage_updated",
            card_id=str(card_id),
            used_amount=float(card.used_amount),
            is_payment=is_payment,
        )
        return card

    async def name_exists(
        self,
        session: AsyncSession,
        card_name: str,
        *,
        user_id: uuid.UUID | None = None,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        """Check if a credit card name already exists for the user.

        Args:
            session: The async database session.
            card_name: The card name to check.
            user_id: Optional filter by user.
            exclude_id: Optional card ID to exclude (for updates).

        Returns:
            True if the name is already taken.
        """
        conditions: list[Any] = [
            CreditCard.deleted_at.is_(None),
            func.lower(CreditCard.card_name) == card_name.lower(),
        ]
        if user_id is not None:
            conditions.append(CreditCard.user_id == user_id)
        if exclude_id is not None:
            conditions.append(CreditCard.id != exclude_id)

        stmt = select(func.count()).select_from(CreditCard).where(*conditions)
        result = await session.execute(stmt)
        return result.scalar_one() > 0
