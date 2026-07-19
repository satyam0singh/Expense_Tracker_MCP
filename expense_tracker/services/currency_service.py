"""Currency Service.

Handles currency conversions and rates. Currently a stub for future
integration with an external exchange rate API (e.g., OpenExchangeRates).
"""

from __future__ import annotations

import httpx
from decimal import Decimal

from expense_tracker.core.constants import Currency
from expense_tracker.core.logging import get_logger
from expense_tracker.services.base import BaseService

logger = get_logger(__name__)


class CurrencyService(BaseService):
    """Service for currency conversion via Frankfurter API."""

    def __init__(self):
        super().__init__()
        # In a real setup, we might inject an httpx.AsyncClient here.
        self._api_url = "https://api.frankfurter.app/latest"

    async def convert(
        self,
        amount: Decimal,
        from_currency: Currency,
        to_currency: Currency,
    ) -> Decimal:
        """Convert an amount from one currency to another.

        Uses Frankfurter API (no authentication required).
        Falls back to hardcoded rates if the API is unavailable.

        Args:
            amount: The amount to convert.
            from_currency: Source currency.
            to_currency: Target currency.

        Returns:
            The converted amount.
        """
        if from_currency == to_currency:
            return amount

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    self._api_url,
                    params={
                        "base": from_currency.value,
                        "symbols": to_currency.value,
                    }
                )
                response.raise_for_status()
                data = response.json()
                rate = Decimal(str(data["rates"][to_currency.value]))
                
                converted = amount * rate
                logger.debug(
                    "currency_converted",
                    amount=float(amount),
                    from_currency=from_currency.value,
                    to_currency=to_currency.value,
                    rate=float(rate),
                )
                return converted.quantize(Decimal("0.01"))
                
        except Exception as exc:
            logger.warning(
                "currency_api_failed_using_fallback",
                error=str(exc),
                from_currency=from_currency.value,
                to_currency=to_currency.value,
            )
            # Simplified hardcoded rates (Base: USD) as fallback
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
                return amount

            amount_in_usd = amount / usd_rates[from_currency]
            converted = amount_in_usd * usd_rates[to_currency]
            return converted.quantize(Decimal("0.01"))

