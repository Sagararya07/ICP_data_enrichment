import asyncio
import os
import sys
import json

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from database.db_operations import db_ops
from analyzers.analyzer import AIAnalyzer
from utils.logger import logger

async def main():
    connected = await db_ops.connect()
    if not connected:
        logger.error("Failed to connect to database.")
        return

    analyzer = AIAnalyzer()

    try:
        async with db_ops.pool.acquire() as conn:
            # Fetch all rows that are completed but have no icp_status
            rows = await conn.fetch("""
                SELECT id, business_model, avg_customer_value, growth_signals, marketing_maturity, employees, revenue
                FROM leads
                WHERE enrichment_status = 'completed'
            """)
            
            logger.info(f"Found {len(rows)} companies to backfill ICP scores.")
            
            for row in rows:
                company_id = row['id']
                business_model = row['business_model'] or 'Unknown'
                customer_value = float(row['avg_customer_value']) if row['avg_customer_value'] else 0.0
                
                # Handle growth_signals which is JSONB in DB
                growth_signals_raw = row['growth_signals']
                if isinstance(growth_signals_raw, str):
                    try:
                        growth_signals = json.loads(growth_signals_raw)
                    except json.JSONDecodeError:
                        growth_signals = {}
                elif isinstance(growth_signals_raw, dict):
                    growth_signals = growth_signals_raw
                else:
                    growth_signals = {}
                    
                marketing_maturity = row['marketing_maturity'] or 'Unknown'
                employees = row['employees'] or 0
                revenue = row['revenue'] or 0
                
                # Calculate the new score
                score, status = analyzer.calculate_icp_fit(
                    business_model, customer_value, growth_signals, marketing_maturity, employees, revenue
                )
                
                # Update the row
                await conn.execute("""
                    UPDATE leads 
                    SET icp_fit_score = $1, icp_status = $2
                    WHERE id = $3
                """, score, status, company_id)
                
            logger.info("Successfully backfilled ICP scores for all completed companies!")
    except Exception as e:
        logger.error(f"Error backfilling ICP scores: {e}")
    finally:
        await db_ops.close()

if __name__ == "__main__":
    asyncio.run(main())
