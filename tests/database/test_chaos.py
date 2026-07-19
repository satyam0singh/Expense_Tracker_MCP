import asyncio
import subprocess
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

# This is the name of the container as seen in `docker ps`
DB_CONTAINER_NAME = "expensetrackermcpserver-db-1"

def pause_db():
    """Simulate a network drop/freeze by pausing the database container."""
    subprocess.run(["docker", "pause", DB_CONTAINER_NAME], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def unpause_db():
    """Restore database connectivity by unpausing the container."""
    subprocess.run(["docker", "unpause", DB_CONTAINER_NAME], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

@pytest.fixture(scope="module", autouse=True)
def ensure_db_unpaused():
    """Ensure the DB is running normally before and after all tests."""
    yield
    unpause_db()

@pytest.mark.asyncio
@pytest.mark.postgres
async def test_db_timeout_recovery(postgres_engine: AsyncEngine):
    """Test that the application can handle a database freeze (timeout) and recover."""
    
    # 1. Verify DB is working
    async with postgres_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1

    # 2. Freeze the DB
    pause_db()

    # 3. Attempt a query and expect a timeout
    try:
        # We wrap in asyncio.wait_for to force a timeout quickly if the DB is frozen,
        # because the default asyncpg timeout might be very long.
        async def run_frozen_query():
            async with postgres_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(run_frozen_query(), timeout=2.0)
    finally:
        # 4. Restore DB
        unpause_db()

    # Give the container a brief moment to resume processing
    await asyncio.sleep(1.0)

    # 5. Verify DB recovered and accepts queries again
    async with postgres_engine.connect() as conn:
        result = await conn.execute(text("SELECT 2"))
        assert result.scalar() == 2
