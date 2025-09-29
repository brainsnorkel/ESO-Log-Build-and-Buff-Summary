#!/usr/bin/env python3
"""
Test script for the dynamic ability scraper that handles JavaScript-loaded content.

This script tests the DynamicAbilityScraper to extract ability IDs and names
from ESO Logs pages after JavaScript has loaded the dynamic content.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from eso_builds.dynamic_ability_scraper import DynamicAbilityScraper, scrape_abilities_for_fight

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_dynamic_ability_scraping():
    """Test the dynamic ability scraper."""
    
    logger.info("Testing Dynamic Ability Scraper with JavaScript execution")
    logger.info("=" * 80)
    
    # Test data from the provided URL
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    source_id = 1
    
    try:
        # Test the dynamic scraper
        logger.info(f"Scraping abilities for report: {report_code}, fight: {fight_id}, source: {source_id}")
        
        results = await scrape_abilities_for_fight(report_code, fight_id, source_id, headless=False)
        
        # Save results
        output_file = f"dynamic_abilities_{report_code}_{fight_id}_{source_id}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {output_file}")
        
        # Print summary
        logger.info("=" * 80)
        logger.info("DYNAMIC ABILITY SCRAPING RESULTS:")
        logger.info("=" * 80)
        
        logger.info(f"Total unique abilities found: {results['total_unique_abilities']}")
        
        for page_type, page_data in results['pages'].items():
            if 'error' not in page_data:
                logger.info(f"\n{page_type.upper()} PAGE:")
                logger.info(f"  - Abilities found: {page_data['count']}")
                
                if page_data['abilities']:
                    for ability in page_data['abilities']:
                        ability_id = ability.get('ability_id', 'No ID')
                        ability_name = ability.get('ability_name', 'No name')
                        logger.info(f"    * {ability_name} (ID: {ability_id})")
            else:
                logger.info(f"\n{page_type.upper()} PAGE: ERROR - {page_data['error']}")
        
        # Show all unique abilities
        logger.info("\n" + "=" * 80)
        logger.info("ALL UNIQUE ABILITIES:")
        logger.info("=" * 80)
        
        for ability_id, ability_data in results['all_abilities'].items():
            ability_name = ability_data.get('ability_name', 'No name')
            found_on = ability_data.get('found_on_pages', [])
            logger.info(f"ID {ability_id}: {ability_name} (found on: {', '.join(found_on)})")
        
        # Check if we found the specific pattern the user mentioned
        talent_ability_found = False
        for ability_id, ability_data in results['all_abilities'].items():
            element_id = ability_data.get('element_id', '')
            if 'talent-ability-' in element_id:
                talent_ability_found = True
                logger.info(f"\n🎯 FOUND talent-ability pattern: {element_id} -> {ability_data.get('ability_name')}")
        
        if talent_ability_found:
            logger.info("\n✅ SUCCESS: Found talent-ability pattern with JavaScript execution!")
        else:
            logger.info("\n❌ No talent-ability pattern found even with JavaScript execution")
            logger.info("This could mean:")
            logger.info("  - The data requires specific user interactions")
            logger.info("  - The data is loaded from a different source")
            logger.info("  - The data appears under different conditions")
        
        return results
        
    except Exception as e:
        logger.error(f"Dynamic scraping test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def test_specific_user_pattern():
    """Test specifically for the pattern the user discovered."""
    
    logger.info("=" * 80)
    logger.info("TESTING SPECIFIC USER PATTERN")
    logger.info("=" * 80)
    
    # Test data
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    source_id = 1
    
    async with DynamicAbilityScraper(headless=False) as scraper:
        try:
            # Go to the casts page where abilities are most likely to appear
            url = scraper.construct_fight_url(report_code, fight_id, source_id, "casts")
            logger.info(f"Testing specific pattern on: {url}")
            
            # Load page and wait
            scraper.driver.get(url)
            await asyncio.sleep(5)
            
            # Wait for dynamic content
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            WebDriverWait(scraper.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait longer for JavaScript to execute
            logger.info("Waiting for JavaScript to execute...")
            await asyncio.sleep(10)
            
            # Try to trigger ability loading by interacting with the page
            logger.info("Trying to trigger ability loading...")
            
            # Look for and click on ability-related elements
            try:
                # Try to find and click on ability filters or menus
                ability_elements = scraper.driver.find_elements(By.CSS_SELECTOR, "[onclick*='ability'], [onmouseover*='ability'], .ability-filter, .talent-filter")
                for element in ability_elements:
                    if element.is_displayed():
                        logger.info(f"Clicking ability element: {element.get_attribute('outerHTML')[:100]}")
                        scraper.driver.execute_script("arguments[0].click();", element)
                        await asyncio.sleep(2)
            except Exception as e:
                logger.debug(f"Could not click ability elements: {e}")
            
            # Scroll around to trigger lazy loading
            logger.info("Scrolling to trigger lazy loading...")
            scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(2)
            scraper.driver.execute_script("window.scrollTo(0, 0);")
            await asyncio.sleep(2)
            
            # Search specifically for the talent-ability pattern
            logger.info("Searching for talent-ability pattern...")
            
            talent_ability_elements = scraper.driver.find_elements(By.CSS_SELECTOR, "span[id*='talent-ability-']")
            logger.info(f"Found {len(talent_ability_elements)} elements with talent-ability pattern")
            
            abilities_found = []
            for element in talent_ability_elements:
                element_id = element.get_attribute('id')
                element_text = element.text.strip()
                element_class = element.get_attribute('class')
                
                logger.info(f"Found talent-ability element: {element_id} -> '{element_text}'")
                
                # Extract ability ID
                import re
                match = re.match(r'^talent-ability-(\d+)-\d+$', element_id)
                if match:
                    ability_id = match.group(1)
                    abilities_found.append({
                        'ability_id': ability_id,
                        'ability_name': element_text,
                        'element_id': element_id,
                        'element_class': element_class
                    })
            
            if abilities_found:
                logger.info(f"✅ SUCCESS: Found {len(abilities_found)} abilities with talent-ability pattern!")
                for ability in abilities_found:
                    logger.info(f"  - {ability['ability_name']} (ID: {ability['ability_id']})")
            else:
                logger.info("❌ No abilities found with talent-ability pattern")
                
                # Try to find any ability-related elements
                all_spans = scraper.driver.find_elements(By.TAG_NAME, "span")
                ability_spans = []
                for span in all_spans:
                    span_id = span.get_attribute('id') or ''
                    span_text = span.text.strip()
                    if span_text and ('ability' in span_id.lower() or 'talent' in span_id.lower() or 'skill' in span_id.lower()):
                        ability_spans.append({
                            'id': span_id,
                            'text': span_text,
                            'class': span.get_attribute('class')
                        })
                
                logger.info(f"Found {len(ability_spans)} ability-related spans:")
                for span in ability_spans[:10]:  # Show first 10
                    logger.info(f"  - {span['id']}: '{span['text']}'")
            
            return abilities_found
            
        except Exception as e:
            logger.error(f"Specific pattern test failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []


async def main():
    """Run all dynamic ability scraping tests."""
    
    logger.info("Starting Dynamic Ability Scraper Tests")
    logger.info("=" * 80)
    
    # Test 1: General dynamic scraping
    results1 = await test_dynamic_ability_scraping()
    
    # Test 2: Specific user pattern test
    results2 = await test_specific_user_pattern()
    
    logger.info("=" * 80)
    logger.info("All dynamic scraping tests completed!")
    
    if results1 and results1.get('total_unique_abilities', 0) > 0:
        logger.info(f"✅ General scraping found {results1['total_unique_abilities']} abilities")
    else:
        logger.info("❌ General scraping found no abilities")
    
    if results2:
        logger.info(f"✅ Specific pattern test found {len(results2)} abilities")
    else:
        logger.info("❌ Specific pattern test found no abilities")


if __name__ == "__main__":
    asyncio.run(main())
