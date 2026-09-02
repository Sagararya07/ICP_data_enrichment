import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()
from database.db_operations import db_ops

async def run():
    await db_ops.connect()
    async with db_ops.pool.acquire() as conn:
        await conn.execute('ALTER TABLE leads ADD COLUMN IF NOT EXISTS scraped_email TEXT, ADD COLUMN IF NOT EXISTS scraped_phone TEXT;')
    await db_ops.close()

if __name__ == "__main__":
    asyncio.run(run())
