import pytest
import pytest_asyncio
import uuid
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from expense_tracker.database.base import BaseModel
from expense_tracker.database.models.user import User

# This matches the postgres container in docker-compose.yml
POSTGRES_TEST_URL = "postgresql+asyncpg://expense_user:expense_password@localhost:5432/expense_db"
SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

@pytest_asyncio.fixture(scope="function")
async def postgres_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create an async SQLAlchemy engine for Postgres testing."""
    engine = create_async_engine(
        POSTGRES_TEST_URL,
        echo=False,
        future=True,
        pool_size=5,
        max_overflow=10,
    )
    
    # Create all tables (tests using this DB should be isolated)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
        await conn.run_sync(BaseModel.metadata.create_all)
        
    yield engine
    
    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
    
    await engine.dispose()

@pytest_asyncio.fixture
async def postgres_session(postgres_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for Postgres tests."""
    async_session = sessionmaker(
        postgres_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        from sqlalchemy import select
        existing_user = await session.execute(select(User).where(User.id == SYSTEM_USER_ID))
        if not existing_user.scalar_one_or_none():
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
