"""CreditCard ORM model.

Tracks credit card details including credit limit, usage,
billing cycle, and due dates for payment reminders.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from expense_tracker.database.base import BaseModel


class CreditCard(BaseModel):
    """Credit card with usage tracking.

    Attributes:
        user_id: FK to the owning user.
        card_name: User-assigned name (e.g., 'HDFC Regalia').
        card_network: Card network (visa, mastercard, etc.).
        last_four_digits: Last 4 digits for identification.
        credit_limit: Total credit limit.
        used_amount: Current outstanding balance.
        billing_cycle_day: Day of month for billing cycle start.
        due_date: Next payment due date.
        is_active: Whether the card is currently active.
        currency: ISO 4217 currency code.
        user: Owning user relationship.
    """

    __tablename__ = "credit_cards"
    __table_args__ = (
        CheckConstraint("credit_limit > 0", name="positive_credit_limit"),
        CheckConstraint("used_amount >= 0", name="non_negative_used_amount"),
        CheckConstraint(
            "billing_cycle_day >= 1 AND billing_cycle_day <= 31",
            name="valid_billing_cycle_day",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    card_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    card_network: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="other",
        server_default="other",
    )
    last_four_digits: Mapped[str] = mapped_column(
        String(4),
        nullable=False,
    )
    credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    used_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )
    billing_cycle_day: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        default=None,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
        server_default="INR",
    )

    # ── Relationships ────────────────────────────────────────
    user: Mapped["User"] = relationship(  # noqa: F821
        back_populates="credit_cards",
    )

    @property
    def available_limit(self) -> Decimal:
        """Calculate the remaining available credit.

        Returns:
            Credit limit minus used amount.
        """
        return self.credit_limit - self.used_amount

    @property
    def utilization_pct(self) -> float:
        """Calculate credit utilization percentage.

        Returns:
            Utilization as a float (0.0 to 100.0+).
        """
        if self.credit_limit == 0:
            return 0.0
        return float((self.used_amount / self.credit_limit) * 100)

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"<CreditCard(id={self.id}, name='{self.card_name}', "
            f"limit={self.credit_limit}, used={self.used_amount})>"
        )
