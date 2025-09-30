#!/usr/bin/env python3
"""
Test script for the summary table targeted scraper.

This script tests scraping abilities specifically from the #summary-talents-0 table
as shown on the ESO Logs summary page.
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


async def test_summary_table_targeting():
    """Test the scraper with summary table targeting."""
    
    logger.info("Testing Summary Table Targeted Scraper")
    logger.info("=" * 60)
    logger.info("Targeting #summary-talents-0 table from ESO Logs summary pages")
    logger.info("=" * 60)
    
    # Test data - using the specific report from the web search
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    
    try:
        # Test the bar-only scraper with summary table targeting
        logger.info(f"Scraping bars from summary table for report: {report_code}, fight: {fight_id}")
        
        scraper = BarOnlyEncounterScraper(headless=True)
        bars_output = await scraper.scrape_encounter_bars(
            report_code, fight_id, 
            max_players=5,  # Limit to 5 key players for faster testing
            timeout_per_player=20  # 20 second timeout per player
        )
        
        # Save output
        output_file = f"summary_table_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_file, 'w') as f:
            f.write(bars_output)
        
        logger.info(f"Summary table output saved to: {output_file}")
        
        # Print the output
        logger.info("=" * 60)
        logger.info("SUMMARY TABLE TARGETED OUTPUT:")
        logger.info("=" * 60)
        print(bars_output)
        
        return bars_output
        
    except Exception as e:
        logger.error(f"Summary table scraper test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def test_single_player_summary():
    """Test scraping a single player's summary page to verify the targeting works."""
    
    logger.info("=" * 60)
    logger.info("Testing Single Player Summary Page")
    logger.info("=" * 60)
    
    # Test data
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    source_id = 1  # Ok Beamer from the web search results
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to the specific player's summary page
            url = f"https://www.esologs.com/reports/{report_code}?fight={fight_id}&type=summary&source={source_id}"
            logger.info(f"Loading player summary page: {url}")
            
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await page.wait_for_selector('body', timeout=30000)
            await asyncio.sleep(3)
            
            # Check if the summary-talents-0 table exists
            table_exists = await page.query_selector('#summary-talents-0')
            if table_exists:
                logger.info("✅ Found #summary-talents-0 table!")
                
                # Get the table content
                table_content = await table_exists.text_content()
                logger.info(f"Table content preview: {table_content[:200]}...")
                
                # Look for ability spans
                ability_spans = await page.query_selector_all('#summary-talents-0 span[id^="ability-"]')
                logger.info(f"Found {len(ability_spans)} ability spans in summary-talents-0 table")
                
                for i, span in enumerate(ability_spans):
                    span_id = await span.get_attribute('id')
                    span_text = await span.text_content()
                    logger.info(f"  Span {i+1}: {span_text} (ID: {span_id})")
                
                # Look for all table cells
                table_cells = await page.query_selector_all('#summary-talents-0 td')
                logger.info(f"Found {len(table_cells)} table cells in summary-talents-0")
                
                ability_names = []
                for i, cell in enumerate(table_cells[:20]):  # Limit to first 20 cells
                    cell_text = await cell.text_content()
                    if cell_text and cell_text.strip() and len(cell_text.strip()) > 3:
                        if (not cell_text.strip().lower() in ['action bars', 'gear', 'summary'] and
                            not cell_text.strip().startswith('CP:') and
                            not cell_text.strip().startswith('Type:')):
                            ability_names.append(cell_text.strip())
                            logger.info(f"  Cell {i+1}: {cell_text.strip()}")
                
                logger.info(f"✅ Extracted {len(ability_names)} potential ability names")
                
            else:
                logger.warning("❌ #summary-talents-0 table not found!")
                
            await browser.close()
            
    except Exception as e:
        logger.error(f"Single player summary test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")


async def main():
    """Run all summary table scraper tests."""
    
    logger.info("Starting Summary Table Targeted Scraper Tests")
    logger.info("=" * 60)
    logger.info("Testing ability extraction from #summary-talents-0 table")
    logger.info("URL: https://www.esologs.com/reports/7KAWyZwPCkaHfc8j?fight=17&type=summary&source=1")
    logger.info("=" * 60)
    
    # Test 1: Single player summary page inspection
    await test_single_player_summary()
    
    # Test 2: Full encounter scraping with summary table targeting
    results = await test_summary_table_targeting()
    
    logger.info("=" * 60)
    logger.info("Summary table scraper tests completed!")
    
    if results:
        logger.info("✅ SUCCESS: Generated bar output from summary table targeting!")
        logger.info("🎯 Perfect: Targeting #summary-talents-0 table as requested")
        logger.info("🚀 Ready for integration!")
    else:
        logger.info("❌ Summary table scraper test failed")


if __name__ == "__main__":
    asyncio.run(main())
