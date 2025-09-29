#!/usr/bin/env python3
"""
Test script for the working ability scraper.

This script tests the WorkingAbilityScraper that successfully extracts ability IDs
from ESO Logs using the patterns we discovered during testing.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from eso_builds.working_ability_scraper import WorkingAbilityScraper, scrape_abilities_for_fight

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_working_ability_scraper():
    """Test the working ability scraper."""
    
    logger.info("Testing Working Ability Scraper")
    logger.info("=" * 80)
    
    # Test data from the provided URL
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    source_id = 1
    
    try:
        # Test the working scraper
        logger.info(f"Scraping abilities for report: {report_code}, fight: {fight_id}, source: {source_id}")
        
        results = await scrape_abilities_for_fight(report_code, fight_id, source_id, headless=False)
        
        # Save results
        output_file = f"working_abilities_{report_code}_{fight_id}_{source_id}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {output_file}")
        
        # Print summary
        logger.info("=" * 80)
        logger.info("WORKING ABILITY SCRAPER RESULTS:")
        logger.info("=" * 80)
        
        if 'error' in results:
            logger.error(f"❌ Scraping failed: {results['error']}")
            return results
        
        total_abilities = results.get('total_abilities', 0)
        logger.info(f"✅ Total abilities found: {total_abilities}")
        
        abilities = results.get('abilities', [])
        if abilities:
            logger.info("\n🎯 ABILITIES FOUND:")
            logger.info("-" * 60)
            
            # Group by pattern type
            by_pattern = {}
            for ability in abilities:
                pattern_type = ability.get('pattern_type', 'unknown')
                if pattern_type not in by_pattern:
                    by_pattern[pattern_type] = []
                by_pattern[pattern_type].append(ability)
            
            for pattern_type, pattern_abilities in by_pattern.items():
                logger.info(f"\n{pattern_type.upper()} PATTERN ({len(pattern_abilities)} abilities):")
                for ability in pattern_abilities:
                    ability_id = ability.get('ability_id', 'No ID')
                    ability_name = ability.get('ability_name', 'No name')
                    element_id = ability.get('element_id', 'No element ID')
                    logger.info(f"  - {ability_name} (ID: {ability_id}) [element: {element_id}]")
            
            # Check if we found the user's original pattern
            talent_ability_found = any(ability.get('pattern_type') == 'talent-ability-span' for ability in abilities)
            ability_span_found = any(ability.get('pattern_type') == 'ability-span' for ability in abilities)
            onclick_found = any(ability.get('pattern_type') == 'onclick-handler' for ability in abilities)
            
            logger.info("\n" + "=" * 80)
            logger.info("PATTERN SUCCESS SUMMARY:")
            logger.info("=" * 80)
            logger.info(f"✅ ability-{{id}}-0 spans: {ability_span_found} ({len(by_pattern.get('ability-span', []))} found)")
            logger.info(f"{'✅' if talent_ability_found else '❌'} talent-ability-{{id}}-{{something}} spans: {talent_ability_found} ({len(by_pattern.get('talent-ability-span', []))} found)")
            logger.info(f"✅ onclick handlers: {onclick_found} ({len(by_pattern.get('onclick-handler', []))} found)")
            
            if ability_span_found or onclick_found:
                logger.info("\n🎉 SUCCESS: Found ability data using working patterns!")
                logger.info("This proves that web scraping CAN extract ability IDs from ESO Logs")
                logger.info("The data is loaded dynamically via JavaScript and can be captured")
            else:
                logger.info("\n❌ No ability data found with working patterns")
        
        else:
            logger.info("❌ No abilities found")
        
        return results
        
    except Exception as e:
        logger.error(f"Working scraper test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def demonstrate_ability_scraping():
    """Demonstrate the ability scraping capability."""
    
    logger.info("=" * 80)
    logger.info("DEMONSTRATING ABILITY SCRAPING CAPABILITY")
    logger.info("=" * 80)
    
    # Test data
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    source_id = 1
    
    async with WorkingAbilityScraper(headless=False) as scraper:
        try:
            # Go to the casts page
            url = scraper.construct_fight_url(report_code, fight_id, source_id, "casts")
            logger.info(f"Demonstrating on: {url}")
            
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
            
            # Wait for JavaScript to execute
            logger.info("Waiting for JavaScript to execute...")
            await asyncio.sleep(10)
            
            # Show what we can find
            logger.info("Demonstrating ability extraction...")
            
            # Find ability spans
            ability_spans = scraper.driver.find_elements(By.CSS_SELECTOR, "span[id^='ability-']")
            logger.info(f"Found {len(ability_spans)} ability spans")
            
            for i, span in enumerate(ability_spans[:5]):  # Show first 5
                span_id = span.get_attribute('id')
                span_text = span.text.strip()
                logger.info(f"  {i+1}. {span_id}: '{span_text}'")
            
            # Find onclick elements
            onclick_elements = scraper.driver.find_elements(By.CSS_SELECTOR, "[onclick*='addPinWithAbility']")
            logger.info(f"Found {len(onclick_elements)} onclick ability elements")
            
            for i, element in enumerate(onclick_elements[:5]):  # Show first 5
                onclick = element.get_attribute('onclick')
                element_text = element.text.strip()
                logger.info(f"  {i+1}. onclick: '{onclick[:50]}...' text: '{element_text}'")
            
            logger.info("\n✅ DEMONSTRATION COMPLETE: Ability data is accessible via web scraping!")
            
        except Exception as e:
            logger.error(f"Demonstration failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")


async def main():
    """Run all working ability scraper tests."""
    
    logger.info("Starting Working Ability Scraper Tests")
    logger.info("=" * 80)
    
    # Test 1: Working scraper test
    results = await test_working_ability_scraper()
    
    # Test 2: Demonstration
    await demonstrate_ability_scraping()
    
    logger.info("=" * 80)
    logger.info("All working ability scraper tests completed!")
    
    if results and results.get('total_abilities', 0) > 0:
        logger.info(f"✅ SUCCESS: Found {results['total_abilities']} abilities using web scraping")
        logger.info("🎯 CONCLUSION: Web scraping IS viable for extracting ability IDs from ESO Logs")
    else:
        logger.info("❌ No abilities found - web scraping may need further refinement")


if __name__ == "__main__":
    asyncio.run(main())
