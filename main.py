import asyncio

from config import config
from scrapers.scraper import AsyncScraper
from analyzers.analyzer import AIAnalyzer
from database.db_operations import db_ops
from utils.logger import logger


class EnrichmentEngine:
    def __init__(self):
        self.analyzer = AIAnalyzer()
        self.db = db_ops
        self.batch_size = config.BATCH_SIZE
        self.processed_count = 0
        self.failed_count = 0

    async def setup(self):
        """Setup database connection"""
        success = await self.db.connect()
        if not success:
            logger.error("Failed to connect to database")
            return False
        return True

    async def process_company(self, company):
        """Process a single company. Returns the enriched dict, or None on failure."""
        try:
            logger.debug(f"Processing: {company['company_name']} ({company['website']})")

            async with AsyncScraper() as scraper:
                scraped_data = await scraper.scrape_company(company['website'])

            if not scraped_data:
                logger.warning(f"No data scraped for {company['company_name']}")
                return None

            analysis = self.analyzer.analyze_company(scraped_data, company)

            if 'error' in analysis:
                logger.warning(f"Analysis error for {company['company_name']}: {analysis['error']}")
                return None

            return {
                'industry': analysis['industry'],
                'business_model': analysis['business_model'],
                'customer_value': analysis['customer_value'],
                'growth_signals': analysis['growth_signals'],
                'marketing_maturity': analysis['marketing_maturity'],
                'has_ads': scraped_data.get('has_ads', False),
                'social_links': scraped_data.get('social_links', []),
                'has_blog': scraped_data.get('has_blog', False),
                'has_careers': scraped_data.get('has_careers', False),
                'has_pricing': scraped_data.get('has_pricing', False)
            }

        except Exception as e:
            logger.error(f"Error processing {company['company_name']}: {str(e)}")
            return None

    async def process_batch(self, companies):
        """Process a batch of companies concurrently and persist results."""
        tasks = [self.process_company(company) for company in companies]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful_updates = 0

        for i, result in enumerate(results):
            company = companies[i]

            if isinstance(result, Exception):
                logger.error(f"Batch error for {company['company_name']}: {str(result)}")
                await self.db.mark_failed(company['id'])
                self.failed_count += 1
                continue

            if result:
                await self.db.update_company_enrichment(company['id'], result)
                successful_updates += 1
                self.processed_count += 1
            else:
                # FIX: previously a failed company was left with industry=NULL
                # and enrichment_status untouched, so the next batch fetch
                # would pick it up again forever, making run() loop
                # indefinitely instead of terminating. Marking it 'failed'
                # excludes it from the next SELECT.
                await self.db.mark_failed(company['id'])
                self.failed_count += 1

        logger.info(f"Batch complete: {successful_updates} updated, {len(companies) - successful_updates} failed")
        return successful_updates

    async def run(self, max_batches=None):
        """Main processing loop"""
        logger.info("Starting Enrichment Engine")

        if not await self.setup():
            logger.error("Setup failed")
            return

        batch_number = 0

        while True:
            if max_batches and batch_number >= max_batches:
                break

            batch_number += 1
            logger.info(f"Processing batch {batch_number}")

            companies = await self.db.get_unprocessed_companies(self.batch_size)

            if not companies:
                logger.info("No more companies to process")
                break

            await self.process_batch(companies)

            stats = await self.db.get_processing_stats()
            logger.info(f"Progress: {stats['enriched']}/{stats['total']} enriched, {stats['failed']} failed")

        logger.info(f"Processing complete. Processed: {self.processed_count}, Failed: {self.failed_count}")
        await self.db.close()


async def main():
    engine = EnrichmentEngine()
    await engine.run()


if __name__ == "__main__":
    asyncio.run(main())
