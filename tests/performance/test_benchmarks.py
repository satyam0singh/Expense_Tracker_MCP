import pytest
import asyncio
from expense_tracker.schemas.expense import ExpenseCreate
from expense_tracker.services.expense_service import ExpenseService
from expense_tracker.core.constants import Currency
from decimal import Decimal
from datetime import date
from tests.conftest import SYSTEM_USER_ID

def sync_wrapper(coro):
    """Run an async coroutine synchronously for pytest-benchmark."""
    return asyncio.get_event_loop().run_until_complete(coro)

def test_expense_creation_benchmark(benchmark):
    """Benchmark creating a simple expense through the service layer."""
    from expense_tracker.database.models.category import Category
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    from uuid import UUID

    def run_benchmark():
        # Using a sync event loop for benchmark invocation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _run():
            engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with engine.begin() as conn:
                from expense_tracker.database.base import BaseModel
                await conn.run_sync(BaseModel.metadata.create_all)

            async with async_session() as bench_session:
                from expense_tracker.services.category_service import CategoryService
                category_service = CategoryService()
                await category_service.initialize_default_categories(bench_session)
                await bench_session.commit()

                # Find the category
                result = await bench_session.execute(select(Category).where(Category.name == "food"))
                category = result.scalar_one_or_none()
                
                expense_data = ExpenseCreate(
                    title="Benchmark",
                    amount=Decimal("5.00"),
                    currency=Currency.USD,
                    category_id=category.id,
                    expense_date=date.today()
                )

                expense_service = ExpenseService()
                await expense_service.create_expense(bench_session, SYSTEM_USER_ID, expense_data)
            await engine.dispose()

        loop.run_until_complete(_run())
        loop.close()

    # Disable garbage collection during benchmark for consistent timing
    benchmark(run_benchmark)
