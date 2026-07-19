"""Application constants, enumerations, and category definitions.

Centralizes all magic values, enum types, and the category taxonomy
derived from the original categories.py prototype.
"""

from __future__ import annotations

import enum


# ── Payment Methods ──────────────────────────────────────────────


class PaymentMethod(str, enum.Enum):
    """Supported payment methods for expenses.

    Uses str mixin for JSON serialization compatibility.
    """

    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    UPI = "upi"
    BANK_TRANSFER = "bank_transfer"
    WALLET = "wallet"
    OTHER = "other"


# ── Currency ─────────────────────────────────────────────────────


class Currency(str, enum.Enum):
    """Supported currency codes (ISO 4217).

    Starts with common currencies. Extend as needed.
    """

    INR = "INR"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    AUD = "AUD"
    CAD = "CAD"
    SGD = "SGD"
    AED = "AED"


# ── Audit Actions ────────────────────────────────────────────────


class AuditAction(str, enum.Enum):
    """Actions recorded in the audit log."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RESTORE = "restore"
    IMPORT = "import"
    EXPORT = "export"
    BACKUP = "backup"
    RESTORE_BACKUP = "restore_backup"


# ── Card Networks ────────────────────────────────────────────────


class CardNetwork(str, enum.Enum):
    """Supported credit/debit card networks."""

    VISA = "visa"
    MASTERCARD = "mastercard"
    RUPAY = "rupay"
    AMEX = "amex"
    DINERS = "diners"
    DISCOVER = "discover"
    OTHER = "other"


# ── Report Formats ───────────────────────────────────────────────


class ReportFormat(str, enum.Enum):
    """Supported report export formats."""

    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"


# ── Entity Types (for audit logging) ────────────────────────────


class EntityType(str, enum.Enum):
    """Entity types tracked in the audit log."""

    EXPENSE = "expense"
    CATEGORY = "category"
    SUBCATEGORY = "subcategory"
    BUDGET = "budget"
    CREDIT_CARD = "credit_card"
    USER = "user"


# ── Application Constants ───────────────────────────────────────

DEFAULT_PAGE_SIZE: int = 50
MAX_PAGE_SIZE: int = 200
MIN_AMOUNT: float = 0.01
MAX_AMOUNT: float = 99_999_999.99

# Maximum title/note lengths
MAX_TITLE_LENGTH: int = 255
MAX_NOTE_LENGTH: int = 2000
MAX_CARD_NAME_LENGTH: int = 100

# Slow query warning threshold (milliseconds)
SLOW_QUERY_THRESHOLD_MS: int = 100

# System user ID placeholder (used until multi-user auth is implemented)
SYSTEM_USER_NAME: str = "system"
SYSTEM_USER_EMAIL: str = "system@expense-tracker.local"

def get_system_user_id() -> __import__('uuid').UUID:
    """Get the system user ID from the environment, or use the default fallback."""
    import os, uuid
    env_id = os.getenv("USER_ID")
    if env_id:
        try:
            return uuid.UUID(env_id)
        except ValueError:
            pass
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


# ── Default Category Taxonomy ────────────────────────────────────

# Derived from the original categories.py prototype.
# Used by the category import tool to seed the database.

DEFAULT_CATEGORIES: dict[str, list[str]] = {
    "food": [
        "groceries",
        "fruits_vegetables",
        "dairy_bakery",
        "dining_out",
        "coffee_tea",
        "snacks",
        "delivery_fees",
        "other",
    ],
    "transport": [
        "fuel",
        "public_transport",
        "cab_ride_hailing",
        "parking",
        "tolls",
        "vehicle_service",
        "other",
    ],
    "housing": [
        "rent",
        "maintenance_hoa",
        "property_tax",
        "repairs_service",
        "cleaning",
        "furnishing",
        "other",
    ],
    "utilities": [
        "electricity",
        "water",
        "gas",
        "internet_broadband",
        "mobile_phone",
        "tv_dth",
        "other",
    ],
    "health": [
        "medicines",
        "doctor_consultation",
        "diagnostics_labs",
        "insurance_health",
        "fitness_gym",
        "other",
    ],
    "education": [
        "books",
        "courses",
        "online_subscriptions",
        "exam_fees",
        "workshops",
        "other",
    ],
    "family_kids": [
        "school_fees",
        "daycare",
        "toys_games",
        "clothes",
        "events_birthdays",
        "other",
    ],
    "entertainment": [
        "movies_events",
        "streaming_subscriptions",
        "games_apps",
        "outing",
        "other",
    ],
    "shopping": [
        "clothing",
        "footwear",
        "accessories",
        "electronics_gadgets",
        "appliances",
        "home_decor",
        "other",
    ],
    "subscriptions": [
        "saas_tools",
        "cloud_ai",
        "newsletters",
        "music_video",
        "storage_backup",
        "other",
    ],
    "personal_care": [
        "salon_spa",
        "grooming",
        "cosmetics",
        "hygiene",
        "other",
    ],
    "gifts_donations": [
        "gifts_personal",
        "charity_donation",
        "festivals",
        "other",
    ],
    "finance_fees": [
        "bank_charges",
        "late_fees",
        "interest",
        "brokerage",
        "other",
    ],
    "business": [
        "software_tools",
        "hosting_domains",
        "marketing_ads",
        "contractor_payments",
        "travel_business",
        "office_supplies",
        "other",
    ],
    "travel": [
        "flights",
        "hotels",
        "train_bus",
        "visa_passport",
        "local_transport",
        "food_travel",
        "other",
    ],
    "home": [
        "household_supplies",
        "cleaning_supplies",
        "kitchenware",
        "small_repairs",
        "pest_control",
        "other",
    ],
    "pet": [
        "food",
        "vet",
        "grooming",
        "supplies",
        "other",
    ],
    "taxes": [
        "income_tax",
        "gst",
        "professional_tax",
        "filing_fees",
        "other",
    ],
    "investments": [
        "mutual_funds",
        "stocks",
        "fd_rd",
        "gold",
        "crypto",
        "brokerage_fees",
        "other",
    ],
    "misc": [
        "uncategorized",
        "rounding",
        "other",
    ],
}
