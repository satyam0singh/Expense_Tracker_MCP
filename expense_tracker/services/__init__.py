"""Service layer — business logic and orchestration.

Services sit between the MCP tools (presentation layer) and the
repositories (data layer). They orchestrate business workflows,
handle cross-entity transactions (e.g., updating a budget when an
expense is added), and interact with the AuditLog.
"""

from expense_tracker.services.base import BaseService
from expense_tracker.services.budget_service import BudgetService
from expense_tracker.services.category_service import CategoryService
from expense_tracker.services.credit_card_service import CreditCardService
from expense_tracker.services.expense_service import ExpenseService

__all__ = [
    "BaseService",
    "BudgetService",
    "CategoryService",
    "CreditCardService",
    "ExpenseService",
]
