import asyncio
from dotenv import load_dotenv
load_dotenv()
from database.db_operations import db_ops

async def run():
    await db_ops.connect()
    async with db_ops.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM leads WHERE industry != 'Unknown' AND enrichment_status = 'completed' LIMIT 1")
        if row:
            print(dict(row))
        else:
            print("No enriched rows found.")
    await db_ops.close()

if __name__ == "__main__":
    asyncio.run(run())
