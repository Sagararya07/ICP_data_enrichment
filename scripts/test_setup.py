#!/usr/bin/env python3
"""
Test script to verify setup is working.
Run: python scripts/test_setup.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from database.db_operations import db_ops
from utils.logger import logger


async def test_database():
    """Test database connection"""
    logger.info("Testing database connection...")
    success = await db_ops.connect()
    if success:
        stats = await db_ops.get_processing_stats()
        logger.info(f"Database OK. Total companies: {stats['total']}")
        await db_ops.close()
        return True
    else:
        logger.error("Database connection failed")
        return False


async def test_scraping():
    """Test web scraping"""
    from scrapers.scraper import AsyncScraper

    logger.info("Testing web scraping...")
    test_urls = ['https://example.com', 'https://www.iana.org']

    async with AsyncScraper() as scraper:
        results = await scraper.scrape_batch(test_urls)
        for i, result in enumerate(results):
            if result and 'title' in result:
                logger.info(f"Scraped {test_urls[i]}: Title: {result.get('title', 'N/A')}")
            else:
                logger.warning(f"Could not scrape {test_urls[i]} (network egress may be restricted)")

    return True


async def test_analysis():
    """Test AI analysis"""
    from analyzers.analyzer import AIAnalyzer

    logger.info("Testing AI analysis...")
    analyzer = AIAnalyzer()

    test_text = (
        "We are a SaaS company providing cloud-based HR software to enterprises. "
        "Plans start at $99 per month. We're hiring across engineering and sales."
    )

    industry, score = analyzer.detect_industry(test_text)
    logger.info(f"Industry detected: {industry} (score: {score})")

    model, model_score = analyzer.detect_business_model(test_text)
    logger.info(f"Business model: {model} (score: {model_score})")

    value = analyzer.estimate_customer_value(test_text, industry, {})
    logger.info(f"Estimated annual customer value: ${value:,.2f}")

    assert value == 99 * 12, "Monthly price should be annualized to $1,188"

    return True


async def main():
    logger.info("Running setup tests...")

    db_ok = await test_database()
    if not db_ok:
        logger.error("Database test failed. Check your .env / docker-compose configuration.")
        return

    await test_scraping()
    await test_analysis()

    logger.info("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
