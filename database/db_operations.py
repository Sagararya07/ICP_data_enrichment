import asyncpg
import json
from datetime import datetime
from config import config
from utils.logger import logger


class DatabaseOperations:
    def __init__(self):
        self.pool = None
        self.last_error = None

    async def connect(self):
        """Create connection pool to database"""
        try:
            db_host = config.DB_HOST
            db_port = config.DB_PORT
            db_user = config.DB_USER
            
            ssl_mode = 'require' if db_host and 'supabase.co' in db_host else False

            # Vercel AWS Lambda does not support IPv6 well, which Supabase uses on port 5432.
            # Force the use of the Supabase connection pooler on port 6543 (IPv4)
            if db_host and 'supabase.co' in db_host:
                db_port = '6543'
                project_ref = db_host.split('.')[1]
                if '.' not in db_user:
                    db_user = f"{db_user}.{project_ref}"

            self.pool = await asyncpg.create_pool(
                host=db_host,
                port=db_port,
                database=config.DB_NAME,
                user=db_user,
                password=config.DB_PASSWORD,
                min_size=5,
                max_size=20,
                ssl=ssl_mode
            )
            logger.info("Database connected successfully")
            return True
        except Exception as e:
            self.last_error = f"Tried connecting to {db_host}:{db_port} - {str(e)}"
            logger.error(f"Database connection failed: {self.last_error}")
            return False

    async def get_unprocessed_companies(self, limit=1000):
        """Get companies that haven't been enriched yet"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, company_name, website, email, phone, employees, revenue, location, social_media
                FROM leads
                WHERE (industry IS NULL OR industry = 'Unknown')
                AND (enrichment_status IS NULL OR enrichment_status = 'pending')
                AND website IS NOT NULL
                AND website != ''
                ORDER BY created_date ASC
                LIMIT $1
            """, limit)

            companies = [
                {
                    'id': row['id'],
                    'company_name': row['company_name'],
                    'website': row['website'],
                    'email': row['email'],
                    'phone': row['phone'],
                    'employees': row['employees'],
                    'revenue': row['revenue'],
                    'location': row['location'],
                    'social_media': row['social_media']
                }
                for row in rows
            ]

            logger.info(f"Found {len(companies)} companies to process")
            return companies

    async def update_company_enrichment(self, company_id, enriched_data):
        """Update company with enrichment results"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE leads SET
                    industry = $1,
                    business_model = $2,
                    avg_customer_value = $3,
                    growth_signals = $4,
                    marketing_maturity = $5,
                    current_ads = $6,
                    social_condition = $7,
                    seo_condition = $8,
                    enrichment_status = 'completed',
                    processed_date = $9,
                    icp_fit_score = $10,
                    icp_status = $11
                WHERE id = $12
            """,
                enriched_data.get('industry'),
                enriched_data.get('business_model'),
                enriched_data.get('customer_value'),
                json.dumps(enriched_data.get('growth_signals', {})),
                enriched_data.get('marketing_maturity'),
                enriched_data.get('has_ads', False),
                'Active' if len(enriched_data.get('social_links', [])) > 0 else 'Inactive',
                'Medium' if enriched_data.get('has_blog', False) else 'Weak',
                datetime.now(),
                enriched_data.get('icp_fit_score', 0),
                enriched_data.get('icp_status', 'Unknown'),
                company_id
            )

            logger.debug(f"Updated company ID: {company_id}")

    async def mark_failed(self, company_id):
        """Mark a company as failed so it doesn't get retried forever in this run
        while still being distinguishable from 'pending'."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE leads SET enrichment_status = 'failed', processed_date = $1
                WHERE id = $2
            """, datetime.now(), company_id)

    async def get_processing_stats(self):
        """Get processing statistics"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN industry IS NOT NULL AND industry != 'Unknown' THEN 1 END) as enriched,
                    COUNT(CASE WHEN enrichment_status = 'failed' THEN 1 END) as failed,
                    COUNT(CASE WHEN icp_status = 'Eligible Company' THEN 1 END) as eligible_companies,
                    COUNT(CASE WHEN icp_status = 'Strong Fit' THEN 1 END) as strong_fits,
                    COUNT(CASE WHEN icp_status = 'Potential Fit' THEN 1 END) as potential_fits,
                    COUNT(CASE WHEN icp_status = 'Not a Fit' THEN 1 END) as not_fits
                FROM leads
            """)

            return {
                'total': rows[0]['total'],
                'enriched': rows[0]['enriched'],
                'failed': rows[0]['failed'],
                'eligible_companies': rows[0]['eligible_companies'] or 0,
                'strong_fits': rows[0]['strong_fits'] or 0,
                'potential_fits': rows[0]['potential_fits'] or 0,
                'not_fits': rows[0]['not_fits'] or 0
            }

    async def get_enriched_leads(self, fit_status=None):
        """Get enriched leads, optionally filtered by icp_status"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT 
                    company_name, website, email, phone, employees, revenue, location, social_media,
                    leader_name, leader_role, leader_social_media,
                    industry, business_model, avg_customer_value, marketing_maturity, 
                    icp_fit_score, icp_status
                FROM leads
                WHERE enrichment_status = 'completed'
            """
            if fit_status and fit_status != 'All':
                query += f" AND icp_status = '{fit_status}'"
            
            query += " ORDER BY icp_fit_score DESC NULLS LAST"
            
            rows = await conn.fetch(query)
            
            # Convert to list of dicts
            return [dict(row) for row in rows]

    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection closed")


db_ops = DatabaseOperations()
