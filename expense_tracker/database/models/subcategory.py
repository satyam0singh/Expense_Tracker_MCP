"""Subcategory ORM model.

Represents a child of a Category (e.g., 'groceries' under 'food').
Each subcategory belongs to exactly one category.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, Uuid

from sqlalchemy.orm import Mapped, mapped_column, relationship

from expense_tracker.database.base import BaseModel


class Subcategory(BaseModel):
    """Subcategory within a parent category.

    Attributes:
        category_id: FK to the parent category.
        name: Machine-readable identifier (unique within its category).
        display_name: Human-readable name.
        sort_order: Display ordering within the parent category.
        category: Parent category relationship.
        expenses: Related expense records.
    """

    __tablename__ = "subcategories"
    __table_args__ = (
        UniqueConstraint("category_id", "name", name="uq_subcategory_category_name"),
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ── Relationships ────────────────────────────────────────
    category: Mapped["Category"] = relationship(  # noqa: F821
        back_populates="subcategories",
    )
    expenses: Mapped[list["Expense"]] = relationship(  # noqa: F821
        back_populates="subcategory",
        lazy="noload",
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return f"<Subcategory(id={self.id}, name='{self.name}')>"
