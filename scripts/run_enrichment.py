#!/usr/bin/env python3
"""
Entry point for running the enrichment engine.
Usage: python scripts/run_enrichment.py [--batch BATCH_SIZE] [--limit MAX_BATCHES]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import argparse
from main import EnrichmentEngine
from utils.logger import logger


def parse_args():
    parser = argparse.ArgumentParser(description='Run ICP Enrichment Engine')
    parser.add_argument('--batch', type=int, default=500, help='Batch size')
    parser.add_argument('--limit', type=int, default=None, help='Max batches to process')
    return parser.parse_args()


async def run():
    args = parse_args()
    logger.info(f"Starting with batch size: {args.batch}")

    engine = EnrichmentEngine()
    engine.batch_size = args.batch

    # FIX: run() now delegates fully to engine.run(max_batches=...), which
    # already contains the correct loop-termination and stats-logging logic.
    # The original script duplicated that loop here with a subtly different
    # (and looser) exit condition - two copies of the same logic that could
    # drift apart. Single source of truth now.
    await engine.run(max_batches=args.limit)


if __name__ == "__main__":
    asyncio.run(run())
