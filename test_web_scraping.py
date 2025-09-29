#!/usr/bin/env python3
"""
Test script to scrape ability IDs and bar positions from ESO Logs.

This script tests the web scraping functionality to extract ability data
from the specific ESO Logs report provided.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from eso_builds.web_scraper import ESOLogsWebScraper, scrape_fight_data

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_ability_scraping():
    """Test scraping ability data from the specific ESO Logs report."""
    
    # Test data from the provided URL
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    source_id = 1
    
    logger.info(f"Testing ability scraping from report: {report_code}, fight: {fight_id}, source: {source_id}")
    
    try:
        # Test the web scraper
        async with ESOLogsWebScraper(headless=False) as scraper:  # Set to False to see what's happening
            logger.info("Web scraper initialized successfully")
            
            # Test 1: Scrape ability data
            logger.info("=" * 60)
            logger.info("TEST 1: Scraping ability data from casts page")
            logger.info("=" * 60)
            
            ability_data = await scraper.scrape_ability_data(report_code, fight_id, source_id)
            
            logger.info(f"Found {len(ability_data)} ability entries:")
            for ability_id, data in ability_data.items():
                logger.info(f"  - {ability_id}: {data}")
            
            # Test 2: Scrape action bar data
            logger.info("=" * 60)
            logger.info("TEST 2: Scraping action bar data from summary page")
            logger.info("=" * 60)
            
            action_bar_data = await scraper.scrape_action_bar_data(report_code, fight_id, source_id)
            
            logger.info(f"Found {len(action_bar_data)} potential action bar elements:")
            for element_id, data in action_bar_data.items():
                logger.info(f"  - {element_id}: {data}")
            
            # Test 3: Scrape gear data
            logger.info("=" * 60)
            logger.info("TEST 3: Scraping gear data")
            logger.info("=" * 60)
            
            gear_data = await scraper.scrape_player_gear_data(report_code, fight_id, source_id)
            
            logger.info(f"Found {len(gear_data)} gear elements:")
            for gear_id, data in gear_data.items():
                logger.info(f"  - {gear_id}: {data}")
            
            # Test 4: Try different data types
            logger.info("=" * 60)
            logger.info("TEST 4: Testing different page types")
            logger.info("=" * 60)
            
            data_types = ["casts", "damage-done", "healing", "summary"]
            for data_type in data_types:
                logger.info(f"Testing {data_type} page...")
                url = scraper.construct_fight_url(report_code, fight_id, source_id, data_type)
                logger.info(f"URL: {url}")
                
                # Navigate to the page and wait
                scraper.driver.get(url)
                await asyncio.sleep(3)
                
                # Get page title and some basic info
                title = scraper.driver.title
                logger.info(f"Page title: {title}")
                
                # Look for any ability-related elements
                ability_elements = scraper.driver.find_elements("css selector", "[class*='ability'], [data-ability], [id*='ability']")
                logger.info(f"Found {len(ability_elements)} ability-related elements on {data_type} page")
                
                # Save page source for manual inspection (first 1000 chars)
                page_source = scraper.driver.page_source[:1000]
                logger.info(f"Page source preview: {page_source}")
                
                await asyncio.sleep(2)  # Be nice to the server
            
            # Compile results
            results = {
                'report_code': report_code,
                'fight_id': fight_id,
                'source_id': source_id,
                'timestamp': datetime.now().isoformat(),
                'abilities': ability_data,
                'action_bars': action_bar_data,
                'gear': gear_data,
                'test_summary': {
                    'total_abilities_found': len(ability_data),
                    'total_action_bar_elements': len(action_bar_data),
                    'total_gear_elements': len(gear_data)
                }
            }
            
            # Save results to file
            output_file = f"scraping_results_{report_code}_{fight_id}_{source_id}.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {output_file}")
            
            return results
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def test_convenience_function():
    """Test the convenience function for scraping all data."""
    
    logger.info("=" * 60)
    logger.info("TEST: Convenience function scrape_fight_data")
    logger.info("=" * 60)
    
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    source_id = 1
    
    try:
        results = await scrape_fight_data(report_code, fight_id, source_id, headless=False)
        
        logger.info("Convenience function results:")
        logger.info(f"Abilities: {len(results['abilities'])}")
        logger.info(f"Action bars: {len(results['action_bars'])}")
        logger.info(f"Gear: {len(results['gear'])}")
        
        # Save convenience function results
        output_file = f"convenience_scraping_results_{report_code}_{fight_id}_{source_id}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Convenience function results saved to: {output_file}")
        
        return results
        
    except Exception as e:
        logger.error(f"Convenience function test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def analyze_page_structure():
    """Analyze the page structure to understand how data is organized."""
    
    logger.info("=" * 60)
    logger.info("TEST: Page structure analysis")
    logger.info("=" * 60)
    
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    source_id = 1
    
    try:
        async with ESOLogsWebScraper(headless=False) as scraper:
            # Go to the summary page
            url = scraper.construct_fight_url(report_code, fight_id, source_id, "summary")
            logger.info(f"Analyzing page structure at: {url}")
            
            scraper.driver.get(url)
            await asyncio.sleep(5)  # Wait longer for dynamic content
            
            # Analyze page structure
            logger.info("Page structure analysis:")
            
            # Get all script tags
            scripts = scraper.driver.find_elements("tag name", "script")
            logger.info(f"Found {len(scripts)} script tags")
            
            # Look for data in script tags
            for i, script in enumerate(scripts[:5]):  # Check first 5 scripts
                try:
                    script_content = script.get_attribute('innerHTML')
                    if script_content and len(script_content) > 100:
                        logger.info(f"Script {i+1} preview: {script_content[:200]}...")
                        
                        # Look for ability-related data
                        if any(keyword in script_content.lower() for keyword in ['ability', 'cast', 'damage', 'fight']):
                            logger.info(f"Script {i+1} contains relevant data!")
                except Exception as e:
                    logger.debug(f"Could not read script {i+1}: {e}")
            
            # Get all elements with data attributes
            data_elements = scraper.driver.find_elements("css selector", "[data-*]")
            logger.info(f"Found {len(data_elements)} elements with data attributes")
            
            for i, element in enumerate(data_elements[:10]):  # Check first 10
                try:
                    attributes = scraper.driver.execute_script("""
                        var attrs = arguments[0].attributes;
                        var result = {};
                        for (var i = 0; i < attrs.length; i++) {
                            if (attrs[i].name.startsWith('data-')) {
                                result[attrs[i].name] = attrs[i].value;
                            }
                        }
                        return result;
                    """, element)
                    
                    if attributes:
                        logger.info(f"Element {i+1} data attributes: {attributes}")
                except Exception as e:
                    logger.debug(f"Could not read element {i+1} attributes: {e}")
            
            # Check for specific ESO Logs elements
            eso_elements = scraper.driver.find_elements("css selector", "[class*='warcraftlogs'], [id*='warcraftlogs'], [class*='esologs'], [id*='esologs']")
            logger.info(f"Found {len(eso_elements)} ESO Logs specific elements")
            
            # Save page source for manual analysis
            page_source_file = f"page_source_{report_code}_{fight_id}_{source_id}.html"
            with open(page_source_file, 'w', encoding='utf-8') as f:
                f.write(scraper.driver.page_source)
            
            logger.info(f"Full page source saved to: {page_source_file}")
            
    except Exception as e:
        logger.error(f"Page structure analysis failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")


async def main():
    """Run all tests."""
    
    logger.info("Starting ESO Logs web scraping tests")
    logger.info("=" * 80)
    
    # Test 1: Basic ability scraping
    results1 = await test_ability_scraping()
    
    # Test 2: Convenience function
    results2 = await test_convenience_function()
    
    # Test 3: Page structure analysis
    await analyze_page_structure()
    
    logger.info("=" * 80)
    logger.info("All tests completed!")
    
    if results1:
        logger.info(f"Test 1 - Found {len(results1['abilities'])} abilities, {len(results1['action_bars'])} action bar elements, {len(results1['gear'])} gear elements")
    
    if results2:
        logger.info(f"Test 2 - Found {len(results2['abilities'])} abilities, {len(results2['action_bars'])} action bar elements, {len(results2['gear'])} gear elements")


if __name__ == "__main__":
    asyncio.run(main())
