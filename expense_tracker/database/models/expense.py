"""Expense ORM model.

The core entity of the application. Represents a single financial
expense with category classification, payment method, and audit fields.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from expense_tracker.database.base import BaseModel


class Expense(BaseModel):
    """Individual expense record.

    Attributes:
        user_id: FK to the owning user.
        title: Short description of the expense.
        amount: Expense amount (must be > 0).
        currency: ISO 4217 currency code.
        category_id: FK to the expense category.
        subcategory_id: Optional FK to the subcategory.
        payment_method: How the expense was paid.
        expense_date: The date the expense occurred.
        notes: Optional detailed notes.
        user: Owning user relationship.
        category: Category relationship.
        subcategory: Subcategory relationship.
        attachments: Related file attachments (receipts, etc.).
    """

    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="positive_amount"),
        Index("ix_expenses_user_date", "user_id", "expense_date"),
        Index("ix_expenses_expense_date", "expense_date"),
        Index("ix_expenses_category_id", "category_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
        server_default="INR",
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    subcategory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subcategories.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    payment_method: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="cash",
        server_default="cash",
    )
    expense_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    # ── Relationships ────────────────────────────────────────
    user: Mapped["User"] = relationship(  # noqa: F821
        back_populates="expenses",
    )
    category: Mapped["Category"] = relationship(  # noqa: F821
        back_populates="expenses",
    )
    subcategory: Mapped["Subcategory | None"] = relationship(  # noqa: F821
        back_populates="expenses",
    )
    attachments: Mapped[list["ExpenseAttachment"]] = relationship(  # noqa: F821
        back_populates="expense",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"<Expense(id={self.id}, title='{self.title}', "
            f"amount={self.amount}, date={self.expense_date})>"
        )
