import asyncio
from expense_tracker.services.currency_service import CurrencyService
from expense_tracker.core.constants import Currency
from decimal import Decimal
async def main():
    s = CurrencyService()
    print(await s.convert(Decimal('100'), Currency.USD, Currency.INR))
asyncio.run(main())
