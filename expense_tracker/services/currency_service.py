"""Currency Service.

Handles currency conversions and rates. Currently a stub for future
integration with an external exchange rate API (e.g., OpenExchangeRates).
"""

from __future__ import annotations

from decimal import Decimal

from expense_tracker.core.constants import Currency
from expense_tracker.core.logging import get_logger
from expense_tracker.services.base import BaseService

logger = get_logger(__name__)


class CurrencyService(BaseService):
    """Service for currency conversion."""

    # Future: Cache rates in memory or Redis
    # _rates_cache: dict[str, Decimal] = {}

    async def convert(
        self,
        amount: Decimal,
        from_currency: Currency,
        to_currency: Currency,
    ) -> Decimal:
        """Convert an amount from one currency to another.

        Note: Currently a stub returning the same amount if currencies match,
        or applying hardcoded approximations for demonstration.
        In a production environment, this would call an external API.

        Args:
            amount: The amount to convert.
            from_currency: Source currency.
            to_currency: Target currency.

        Returns:
            The converted amount.
        """
        if from_currency == to_currency:
            return amount

        logger.warning(
            "currency_conversion_stubbed",
            from_currency=from_currency.value,
            to_currency=to_currency.value,
        )

        # Simplified hardcoded rates (Base: USD)
        # ONLY FOR PROTOTYPE PURPOSES
        usd_rates = {
            Currency.USD: Decimal("1.0"),
            Currency.INR: Decimal("83.5"),
            Currency.EUR: Decimal("0.92"),
            Currency.GBP: Decimal("0.78"),
            Currency.JPY: Decimal("154.0"),
            Currency.AUD: Decimal("1.52"),
            Currency.CAD: Decimal("1.37"),
            Currency.SGD: Decimal("1.35"),
            Currency.AED: Decimal("3.67"),
        }

        if from_currency not in usd_rates or to_currency not in usd_rates:
            # Fallback if unknown currency (shouldn't happen with Enums)
            return amount

        # Convert from source to USD, then USD to target
        amount_in_usd = amount / usd_rates[from_currency]
        converted = amount_in_usd * usd_rates[to_currency]

        return converted.quantize(Decimal("0.01"))
