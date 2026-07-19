"""Category ORM model.

Represents a top-level expense category (e.g., 'food', 'transport').
Categories are hierarchical — each has many subcategories.
System categories are seeded from the default taxonomy and cannot
be deleted by users.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from expense_tracker.database.base import BaseModel


class Category(BaseModel):
    """Top-level expense category.

    Attributes:
        name: Machine-readable unique identifier (e.g., 'food').
        display_name: Human-readable name (e.g., 'Food & Dining').
        icon: Optional emoji or icon identifier for UI.
        color: Optional hex color code for UI.
        sort_order: Display ordering (lower = first).
        is_system: Whether this is a built-in system category.
        subcategories: Child subcategory records.
        expenses: Related expense records.
        budgets: Related budget records.
    """

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="",
    )
    icon: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        default=None,
    )
    color: Mapped[str | None] = mapped_column(
        String(7),
        nullable=True,
        default=None,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # ── Relationships ────────────────────────────────────────
    subcategories: Mapped[list["Subcategory"]] = relationship(  # noqa: F821
        back_populates="category",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    expenses: Mapped[list["Expense"]] = relationship(  # noqa: F821
        back_populates="category",
        lazy="noload",
    )
    budgets: Mapped[list["Budget"]] = relationship(  # noqa: F821
        back_populates="category",
        lazy="noload",
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return f"<Category(id={self.id}, name='{self.name}')>"
