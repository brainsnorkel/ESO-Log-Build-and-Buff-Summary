#!/usr/bin/env python3
"""
Test script for the Playwright encounter scraper.

This script demonstrates scraping ability data for all players in an encounter
and generating bar1: and bar2: output for each player.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from eso_builds.playwright_encounter_scraper import PlaywrightEncounterScraper, scrape_encounter_for_bars

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_encounter_scraper():
    """Test the encounter scraper."""
    
    logger.info("Testing Playwright Encounter Scraper")
    logger.info("=" * 80)
    
    # Test data
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    
    try:
        # Test the encounter scraper
        logger.info(f"Scraping encounter for report: {report_code}, fight: {fight_id}")
        
        scraper = PlaywrightEncounterScraper(headless=True)
        encounter_data = await scraper.scrape_encounter_abilities(report_code, fight_id)
        
        # Save raw data
        output_file = f"encounter_scraper_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(encounter_data, f, indent=2, default=str)
        
        logger.info(f"Raw data saved to: {output_file}")
        
        # Format and display the bar output
        formatted_output = scraper.format_encounter_output(encounter_data)
        
        # Save formatted output
        formatted_file = f"encounter_bars_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(formatted_file, 'w') as f:
            f.write(formatted_output)
        
        logger.info(f"Formatted output saved to: {formatted_file}")
        
        # Print the formatted output
        logger.info("=" * 80)
        logger.info("ENCOUNTER BAR OUTPUT:")
        logger.info("=" * 80)
        print(formatted_output)
        
        return encounter_data
        
    except Exception as e:
        logger.error(f"Encounter scraper test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def test_convenience_function():
    """Test the convenience function."""
    
    logger.info("=" * 80)
    logger.info("Testing Convenience Function")
    logger.info("=" * 80)
    
    # Test data
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    
    try:
        # Use the convenience function
        logger.info("Using convenience function: scrape_encounter_for_bars()")
        
        formatted_output = await scrape_encounter_for_bars(report_code, fight_id, headless=True)
        
        logger.info("=" * 80)
        logger.info("CONVENIENCE FUNCTION OUTPUT:")
        logger.info("=" * 80)
        print(formatted_output)
        
        return formatted_output
        
    except Exception as e:
        logger.error(f"Convenience function test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def demo_with_different_fights():
    """Demo with different fights from the same report."""
    
    logger.info("=" * 80)
    logger.info("Demo with Different Fights")
    logger.info("=" * 80)
    
    report_code = "7KAWyZwPCkaHfc8j"
    
    # Test different fights
    fight_ids = [17, 18, 19]  # Try a few different fights
    
    for fight_id in fight_ids:
        try:
            logger.info(f"\n--- Testing Fight {fight_id} ---")
            
            # Quick test - just get the formatted output
            formatted_output = await scrape_encounter_for_bars(report_code, fight_id, headless=True)
            
            logger.info(f"Fight {fight_id} Results:")
            print(formatted_output[:500] + "..." if len(formatted_output) > 500 else formatted_output)
            
        except Exception as e:
            logger.error(f"Error with fight {fight_id}: {e}")


async def main():
    """Run all encounter scraper tests."""
    
    logger.info("Starting Playwright Encounter Scraper Tests")
    logger.info("=" * 80)
    
    # Test 1: Full encounter scraper
    results = await test_encounter_scraper()
    
    # Test 2: Convenience function
    await test_convenience_function()
    
    # Test 3: Demo with different fights
    await demo_with_different_fights()
    
    logger.info("=" * 80)
    logger.info("All encounter scraper tests completed!")
    
    if results and results.get('players'):
        player_count = len(results['players'])
        logger.info(f"✅ SUCCESS: Found {player_count} players in encounter")
        logger.info("🚀 Playwright encounter scraper works perfectly!")
    else:
        logger.info("❌ Encounter scraper test failed")


if __name__ == "__main__":
    asyncio.run(main())
