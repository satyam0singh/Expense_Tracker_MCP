"""ExpenseAttachment ORM model.

Stores metadata about files attached to expenses (receipts, invoices).
The actual file content is stored on the filesystem; this model
tracks the path and metadata for retrieval.

Future-ready for OCR receipt scanning — the AI receipt_parser
module will create attachment records when processing receipts.
"""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from expense_tracker.database.base import BaseModel


class ExpenseAttachment(BaseModel):
    """File attachment linked to an expense.

    Attributes:
        expense_id: FK to the parent expense.
        file_name: Original file name as uploaded.
        file_path: Server-side path to the stored file.
        file_type: MIME type (e.g., 'image/jpeg', 'application/pdf').
        file_size: File size in bytes.
        expense: Parent expense relationship.
    """

    __tablename__ = "expense_attachments"

    expense_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("expenses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="application/octet-stream",
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    # ── Relationships ────────────────────────────────────────
    expense: Mapped["Expense"] = relationship(  # noqa: F821
        back_populates="attachments",
    )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"<ExpenseAttachment(id={self.id}, "
            f"file_name='{self.file_name}')>"
        )
