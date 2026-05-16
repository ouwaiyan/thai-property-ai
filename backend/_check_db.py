import asyncio
from app.database import engine
from sqlalchemy import inspect

async def check():
    async with engine.begin() as conn:
        tables = await conn.run_sync(lambda c: inspect(c).get_table_names())
        print("Tables:", tables)

asyncio.run(check())
