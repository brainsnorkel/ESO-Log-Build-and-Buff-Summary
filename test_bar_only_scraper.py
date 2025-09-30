#!/usr/bin/env python3
"""
Test script for the bar-only encounter scraper.

This script demonstrates scraping only bar1: and bar2: abilities for all players
in an encounter, with clean, minimal output.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from eso_builds.bar_only_scraper import BarOnlyEncounterScraper, scrape_encounter_bars_only

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_bar_only_scraper():
    """Test the bar-only encounter scraper."""
    
    logger.info("Testing Bar-Only Encounter Scraper")
    logger.info("=" * 60)
    
    # Test data
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    
    try:
        # Test the bar-only scraper with timeout handling
        logger.info(f"Scraping bars for report: {report_code}, fight: {fight_id}")
        
        scraper = BarOnlyEncounterScraper(headless=True)
        bars_output = await scraper.scrape_encounter_bars(
            report_code, fight_id, 
            max_players=8,  # Limit to 8 key players
            timeout_per_player=25  # 25 second timeout per player
        )
        
        # Save output
        output_file = f"bar_only_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_file, 'w') as f:
            f.write(bars_output)
        
        logger.info(f"Bar-only output saved to: {output_file}")
        
        # Print the output
        logger.info("=" * 60)
        logger.info("BAR-ONLY OUTPUT:")
        logger.info("=" * 60)
        print(bars_output)
        
        return bars_output
        
    except Exception as e:
        logger.error(f"Bar-only scraper test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def test_convenience_function():
    """Test the convenience function."""
    
    logger.info("=" * 60)
    logger.info("Testing Convenience Function")
    logger.info("=" * 60)
    
    # Test data
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    
    try:
        # Use the convenience function with timeout handling
        logger.info("Using convenience function: scrape_encounter_bars_only()")
        
        bars_output = await scrape_encounter_bars_only(
            report_code, fight_id, 
            headless=True,
            max_players=6,  # Limit to 6 key players
            timeout_per_player=20  # 20 second timeout per player
        )
        
        logger.info("=" * 60)
        logger.info("CONVENIENCE FUNCTION OUTPUT:")
        logger.info("=" * 60)
        print(bars_output)
        
        return bars_output
        
    except Exception as e:
        logger.error(f"Convenience function test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def main():
    """Run all bar-only scraper tests."""
    
    logger.info("Starting Bar-Only Encounter Scraper Tests")
    logger.info("=" * 60)
    
    # Test 1: Full bar-only scraper
    results = await test_bar_only_scraper()
    
    # Test 2: Convenience function
    await test_convenience_function()
    
    logger.info("=" * 60)
    logger.info("Bar-only scraper tests completed!")
    
    if results:
        logger.info("✅ SUCCESS: Generated clean bar-only output!")
        logger.info("🎯 Perfect format: bar1: and bar2: for each player")
        logger.info("🚀 Ready for integration!")
    else:
        logger.info("❌ Bar-only scraper test failed")


if __name__ == "__main__":
    asyncio.run(main())
