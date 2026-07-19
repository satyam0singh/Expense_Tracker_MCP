"""User ORM model.

Represents a user of the expense tracker system. Currently uses
a single system user, but the schema supports multi-user via
foreign keys on all other entities.
"""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from expense_tracker.database.base import BaseModel


class User(BaseModel):
    """User account for the expense tracker.

    Attributes:
        username: Unique login identifier.
        email: Unique email address.
        display_name: Human-readable name for display.
        is_active: Whether the user account is enabled.
        expenses: Related expense records.
        budgets: Related budget records.
        credit_cards: Related credit card records.
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # ── Relationships ────────────────────────────────────────
    expenses: Mapped[list["Expense"]] = relationship(  # noqa: F821
        back_populates="user",
        lazy="selectin",
    )
    budgets: Mapped[list["Budget"]] = relationship(  # noqa: F821
        back_populates="user",
        lazy="selectin",
    )
    credit_cards: Mapped[list["CreditCard"]] = relationship(  # noqa: F821
        back_populates="user",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return f"<User(id={self.id}, username='{self.username}')>"
