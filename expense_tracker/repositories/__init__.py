"""Repository layer — data access abstraction.

Provides a generic BaseRepository with async CRUD operations
and entity-specific repositories with domain queries.

All database access goes through repositories. Services never
interact with SQLAlchemy sessions directly.
"""

from expense_tracker.repositories.audit_log_repository import AuditLogRepository
from expense_tracker.repositories.base import BaseRepository
from expense_tracker.repositories.budget_repository import BudgetRepository
from expense_tracker.repositories.category_repository import CategoryRepository
from expense_tracker.repositories.credit_card_repository import CreditCardRepository
from expense_tracker.repositories.expense_repository import ExpenseRepository

__all__ = [
    "AuditLogRepository",
    "BaseRepository",
    "BudgetRepository",
    "CategoryRepository",
    "CreditCardRepository",
    "ExpenseRepository",
]
