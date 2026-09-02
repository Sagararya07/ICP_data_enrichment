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
        print("Resetting all companies to pending state for re-enrichment...")
        result = await conn.execute("""
            UPDATE leads 
            SET enrichment_status = 'pending', 
                industry = NULL,
                icp_status = 'Unknown',
                icp_fit_score = 0,
                scraped_email = NULL,
                scraped_phone = NULL
        """)
        print(f"Update result: {result}")
    await db_ops.close()

if __name__ == "__main__":
    asyncio.run(run())
