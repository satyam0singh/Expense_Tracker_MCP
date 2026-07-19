"""Credit Card Service.

Handles business logic for credit cards, including card creation,
updating, and recording payments/charges.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from expense_tracker.core.constants import AuditAction
from expense_tracker.core.exceptions import DuplicateError, ValidationError
from expense_tracker.core.logging import get_logger
from expense_tracker.database.models.credit_card import CreditCard
from expense_tracker.repositories.credit_card_repository import CreditCardRepository
from expense_tracker.schemas.credit_card import (
    CreditCardCreate,
    CreditCardUpdate,
    CreditCardUsageUpdate,
)
from expense_tracker.services.base import BaseService

logger = get_logger(__name__)


class CreditCardService(BaseService):
    """Service for managing credit cards."""

    def __init__(self, repo: CreditCardRepository | None = None) -> None:
        """Initialize the credit card service.

        Args:
            repo: Optional CreditCardRepository.
        """
        super().__init__()
        self.repo = repo or CreditCardRepository()

    async def create_card(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        data: CreditCardCreate,
    ) -> CreditCard:
        """Create a new credit card.

        Args:
            session: The async database session.
            user_id: The UUID of the user.
            data: Card creation data.

        Returns:
            The created CreditCard.

        Raises:
            DuplicateError: If a card with this name already exists.
        """
        # 1. Check for duplicates
        exists = await self.repo.name_exists(
            session, card_name=data.card_name, user_id=user_id
        )
        if exists:
            raise DuplicateError(f"Credit card '{data.card_name}' already exists.")

        # 2. Create card
        card_data = data.model_dump()
        card_data["user_id"] = user_id

        card = await self.repo.create(session, **card_data)

        # 3. Audit
        await self._audit(
            session=session,
            entity_type="CreditCard",
            entity_id=card.id,
            action=AuditAction.CREATE,
            changes={"card_name": card.card_name, "credit_limit": float(card.credit_limit)},
            user_id=user_id,
        )

        return card

    async def update_card(
        self,
        session: AsyncSession,
        card_id: uuid.UUID,
        user_id: uuid.UUID,
        data: CreditCardUpdate,
    ) -> CreditCard:
        """Update an existing credit card.

        Args:
            session: The async database session.
            card_id: The credit card UUID.
            user_id: The UUID of the user.
            data: Card update data.

        Returns:
            The updated CreditCard.

        Raises:
            DuplicateError: If updating to a name that already exists.
        """
        # 1. Verify existence
        card = await self.repo.get_by_id_or_raise(session, card_id)

        # 2. Extract updates
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return card

        # 3. Check for duplicates if name is being changed
        if "card_name" in update_data and update_data["card_name"] != card.card_name:
            exists = await self.repo.name_exists(
                session,
                card_name=update_data["card_name"],
                user_id=user_id,
                exclude_id=card_id,
            )
            if exists:
                raise DuplicateError(f"Credit card '{update_data['card_name']}' already exists.")

        # 4. Capture before state for audit
        before_state = {k: getattr(card, k) for k in update_data.keys()}
        
        # Serialize Decimals for JSON
        for k, v in before_state.items():
            if hasattr(v, 'as_tuple'):  # Simple Decimal check
                before_state[k] = float(v)

        # 5. Update
        updated_card = await self.repo.update(session, card_id, **update_data)

        # 6. Audit
        after_state = {k: getattr(updated_card, k) for k in update_data.keys()}
        for k, v in after_state.items():
            if hasattr(v, 'as_tuple'):
                after_state[k] = float(v)

        await self._audit(
            session=session,
            entity_type="CreditCard",
            entity_id=card_id,
            action=AuditAction.UPDATE,
            changes={"before": before_state, "after": after_state},
            user_id=user_id,
        )

        return updated_card

    async def update_usage(
        self,
        session: AsyncSession,
        card_id: uuid.UUID,
        user_id: uuid.UUID,
        data: CreditCardUsageUpdate,
    ) -> CreditCard:
        """Record a payment or charge against a credit card.

        Args:
            session: The async database session.
            card_id: The credit card UUID.
            user_id: The UUID of the user.
            data: Usage update data.

        Returns:
            The updated CreditCard.

        Raises:
            ValidationError: If a payment would result in negative usage.
        """
        card = await self.repo.get_by_id_or_raise(session, card_id)

        if data.is_payment and data.amount > card.used_amount:
            raise ValidationError(
                f"Payment amount ({data.amount}) exceeds current usage ({card.used_amount})."
            )

        old_usage = card.used_amount
        
        updated_card = await self.repo.update_usage(
            session,
            card_id=card_id,
            amount=data.amount,
            is_payment=data.is_payment,
        )

        # Audit the usage change
        await self._audit(
            session=session,
            entity_type="CreditCard",
            entity_id=card_id,
            action=AuditAction.UPDATE,
            changes={
                "action": "payment" if data.is_payment else "charge",
                "amount": float(data.amount),
                "before_usage": float(old_usage),
                "after_usage": float(updated_card.used_amount),
            },
            user_id=user_id,
        )

        return updated_card

    async def get_active_cards(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[CreditCard]:
        """Get all active credit cards for a user.

        Args:
            session: The async database session.
            user_id: The UUID of the user.

        Returns:
            List of active credit cards.
        """
        return await self.repo.get_active_cards(session, user_id=user_id)

    async def get_upcoming_due(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        days_ahead: int = 30,
    ) -> list[dict[str, Any]]:
        """Get cards with upcoming due dates and format alerts.

        Args:
            session: The async database session.
            user_id: The UUID of the user.
            days_ahead: Number of days to look ahead.

        Returns:
            List of dicts with card details and days remaining.
        """
        cards = await self.repo.get_upcoming_due(
            session, days_ahead=days_ahead, user_id=user_id
        )

        today = date.today()
        results = []
        for card in cards:
            if not card.due_date:
                continue
                
            days_remaining = (card.due_date - today).days
            
            alert_level = "info"
            if days_remaining <= 3:
                alert_level = "critical"
            elif days_remaining <= 7:
                alert_level = "warning"

            results.append({
                "card_id": str(card.id),
                "card_name": card.card_name,
                "due_date": card.due_date.isoformat(),
                "days_remaining": days_remaining,
                "amount_due": float(card.used_amount),
                "currency": card.currency,
                "alert_level": alert_level,
            })

        return results
