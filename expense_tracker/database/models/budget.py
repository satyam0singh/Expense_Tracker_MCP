"""Budget ORM model.

Tracks monthly spending budgets per category per user.
The spent_amount is auto-updated by the expense service
when expenses are added, edited, or deleted.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from expense_tracker.database.base import BaseModel


class Budget(BaseModel):
    """Monthly budget for a specific category.

    Attributes:
        user_id: FK to the owning user.
        category_id: FK to the budget category.
        month: First day of the budget month (e.g., 2026-07-01).
        budget_amount: The planned spending limit.
        spent_amount: Current total spent (auto-updated).
        currency: ISO 4217 currency code.
        user: Owning user relationship.
        category: Category relationship.
    """

    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "category_id",
            "month",
            name="uq_budget_user_category_month",
        ),
        CheckConstraint("budget_amount > 0", name="positive_budget_amount"),
        CheckConstraint("spent_amount >= 0", name="non_negative_spent_amount"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    month: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="First day of the budget month (e.g., 2026-07-01).",
    )
    budget_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    spent_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
        server_default="INR",
    )

    # ── Relationships ────────────────────────────────────────
    user: Mapped["User"] = relationship(  # noqa: F821
        back_populates="budgets",
    )
    category: Mapped["Category"] = relationship(  # noqa: F821
        back_populates="budgets",
    )

    @property
    def remaining(self) -> Decimal:
        """Calculate the remaining budget.

        Returns:
            Budget amount minus spent amount. Can be negative if overspent.
        """
        return self.budget_amount - self.spent_amount

    @property
    def percentage_used(self) -> float:
        """Calculate the percentage of budget used.

        Returns:
            Percentage as a float (0.0 to 100.0+).
        """
        if self.budget_amount == 0:
            return 0.0
        return float((self.spent_amount / self.budget_amount) * 100)

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"<Budget(id={self.id}, month={self.month}, "
            f"budget={self.budget_amount}, spent={self.spent_amount})>"
        )
