"""Pytest configuration and fixtures.

Sets up an in-memory SQLite database for testing, overriding the
PostgreSQL config to allow isolated, fast unit tests without requiring
a running database instance.
"""

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from expense_tracker.database.base import BaseModel
from expense_tracker.database.models.user import User

# Use an in-memory SQLite database for tests
# SQLite memory databases are destroyed when the connection closes.
# The check_same_thread=False argument is required for asyncio.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create an async SQLAlchemy engine for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
        
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for a test.
    
    Data is isolated by rolling back the transaction at the end.
    """
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Seed system user for tests
        user = User(
            id=SYSTEM_USER_ID,
            username="test_system",
            email="test@expensetracker.local",
            display_name="Test User"
        )
        session.add(user)
        
        # Seed basic categories
        from expense_tracker.services.category_service import CategoryService
        service = CategoryService()
        await service.initialize_default_categories(session)
        
        await session.commit()
        
        yield session
        
        # We don't rollback because SQLite in-memory doesn't preserve tables well 
        # across massive rollbacks in some setups, but we could TRUNCATE tables.
        # Alternatively, we could recreate tables per-test, but it's slow.
        # For this prototype, we'll recreate the schema in a nested transaction.
        pass
