#!/usr/bin/env python3
"""
Load companies from a CSV into the `leads` table.
Usage: python scripts/load_csv.py [path/to/file.csv]
Defaults to data/sample_companies.csv.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd

from database.db_operations import db_ops
from utils.logger import logger


async def load(csv_path):
    df = pd.read_csv(csv_path)
    required = {'company_name', 'website'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required column(s): {missing}")

    if not await db_ops.connect():
        logger.error("Could not connect to database")
        return

    inserted = 0
    async with db_ops.pool.acquire() as conn:
        # Fetch existing websites to prevent duplicates
        existing_rows = await conn.fetch("SELECT website FROM leads WHERE website IS NOT NULL")
        existing_websites = {row['website'] for row in existing_rows}

        for _, row in df.iterrows():
            website = row.get('website')
            if website in existing_websites:
                continue  # Skip this company, it's already in the database
                
            await conn.execute("""
                INSERT INTO leads (company_name, website, email, phone, employees, revenue, location, social_media)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                row.get('company_name'),
                row.get('website'),
                row.get('email') if pd.notna(row.get('email')) else None,
                str(row.get('phone')) if pd.notna(row.get('phone')) else None,
                int(row['employees']) if pd.notna(row.get('employees')) else None,
                float(row['revenue']) if pd.notna(row.get('revenue')) else None,
                row.get('location') if pd.notna(row.get('location')) else None,
                row.get('social_media') if pd.notna(row.get('social_media')) else None,
            )
            inserted += 1

    logger.info(f"Loaded {inserted} companies from {csv_path}")
    await db_ops.close()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'sample_companies.csv'
    )
    asyncio.run(load(path))
