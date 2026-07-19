import asyncio
from expense_tracker.database.base import Base
from expense_tracker.database.session import init_engine, get_engine, dispose_engine
from expense_tracker.database.models import *

async def main():
    await init_engine()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")
    await dispose_engine()

if __name__ == "__main__":
    asyncio.run(main())
