import asyncio
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from database.db_operations import db_ops
from utils.logger import logger

async def main():
    connected = await db_ops.connect()
    if not connected:
        logger.error("Failed to connect to database.")
        return

    try:
        async with db_ops.pool.acquire() as conn:
            # Check if columns exist, if not add them
            logger.info("Adding icp_fit_score and icp_status columns to leads table...")
            await conn.execute("""
                ALTER TABLE leads 
                ADD COLUMN IF NOT EXISTS icp_fit_score INTEGER,
                ADD COLUMN IF NOT EXISTS icp_status TEXT;
            """)
            
            # Create an index on icp_status for fast querying
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_leads_icp_status ON leads (icp_status);
            """)
            
            logger.info("Successfully updated database schema!")
    except Exception as e:
        logger.error(f"Error updating schema: {e}")
    finally:
        await db_ops.close()

if __name__ == "__main__":
    asyncio.run(main())
