import asyncio
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database.db_operations import db_ops
from utils.logger import logger

async def run_migration():
    if not await db_ops.connect():
        logger.error("Failed to connect to database for migration.")
        return

    try:
        async with db_ops.pool.acquire() as conn:
            logger.info("Adding leader columns to 'leads' table...")
            await conn.execute("""
                ALTER TABLE leads
                ADD COLUMN IF NOT EXISTS leader_name TEXT,
                ADD COLUMN IF NOT EXISTS leader_role TEXT,
                ADD COLUMN IF NOT EXISTS leader_social_media TEXT;
            """)
            logger.info("Successfully added leader columns.")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
    finally:
        await db_ops.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
