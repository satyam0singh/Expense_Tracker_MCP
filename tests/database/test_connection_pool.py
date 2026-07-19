import asyncio
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

@pytest.mark.asyncio
@pytest.mark.postgres
async def test_postgres_connection_pool_concurrency(postgres_engine: AsyncEngine):
    """Test that connection pooling can handle concurrent database requests."""
    
    async def run_query(idx):
        async with postgres_engine.connect() as conn:
            result = await conn.execute(text("SELECT pg_sleep(0.1), CAST(:idx AS INT) as val"), {"idx": idx})
            row = result.fetchone()
            return row.val if row else None

    # Run 20 concurrent queries. The pool size is 5 + 10 max_overflow = 15.
    # It should block/queue without raising a TimeoutError because it waits.
    # We use gather to run them concurrently.
    tasks = [run_query(i) for i in range(20)]
    
    results = await asyncio.gather(*tasks, return_exceptions=False)
    
    assert len(results) == 20
    assert sorted(results) == list(range(20))
