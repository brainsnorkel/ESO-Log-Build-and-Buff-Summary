#!/usr/bin/env python3
"""
Test script to analyze action bar positions from scraped ability data.

This script investigates whether we can determine the 6 primary and 6 secondary
slotted skills from the web scraping data.
"""

import asyncio
import json
import logging
import re
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from eso_builds.working_ability_scraper import WorkingAbilityScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ActionBarAnalyzer:
    """Analyzer to determine action bar positions from scraped ability data."""
    
    def __init__(self):
        """Initialize the action bar analyzer."""
        pass
    
    def analyze_action_bar_positions(self, abilities_data: Dict) -> Dict:
        """
        Analyze action bar positions from scraped ability data.
        
        Args:
            abilities_data: Dictionary containing scraped ability data
        
        Returns:
            Dictionary with action bar analysis
        """
        logger.info("Analyzing action bar positions from scraped ability data")
        
        abilities = abilities_data.get('abilities', [])
        
        analysis = {
            'total_abilities': len(abilities),
            'action_bar_patterns': {},
            'position_analysis': {},
            'primary_bar': [],
            'secondary_bar': [],
            'unknown_position': [],
            'insights': []
        }
        
        # Analyze the element IDs for position patterns
        for ability in abilities:
            element_id = ability.get('element_id', '')
            ability_name = ability.get('ability_name', '')
            ability_id = ability.get('ability_id', '')
            
            # Parse the element ID pattern: ability-{id}-{position}
            match = re.match(r'^ability-(\d+)-(\d+)$', element_id)
            if match:
                ability_id_from_element = match.group(1)
                position = int(match.group(2))
                
                ability_info = {
                    'ability_id': ability_id,
                    'ability_name': ability_name,
                    'position': position,
                    'element_id': element_id
                }
                
                # Group by position
                if position not in analysis['position_analysis']:
                    analysis['position_analysis'][position] = []
                analysis['position_analysis'][position].append(ability_info)
                
                # Categorize by position (ESO has 6 slots per bar)
                if position < 6:
                    analysis['primary_bar'].append(ability_info)
                    analysis['insights'].append(f"Position {position}: {ability_name} (ID: {ability_id}) - Primary Bar")
                elif position < 12:
                    analysis['secondary_bar'].append(ability_info)
                    analysis['insights'].append(f"Position {position}: {ability_name} (ID: {ability_id}) - Secondary Bar")
                else:
                    analysis['unknown_position'].append(ability_info)
                    analysis['insights'].append(f"Position {position}: {ability_name} (ID: {ability_id}) - Unknown Position")
        
        # Analyze patterns
        positions = list(analysis['position_analysis'].keys())
        analysis['action_bar_patterns'] = {
            'positions_found': positions,
            'position_range': f"{min(positions)} to {max(positions)}" if positions else "None",
            'total_positions': len(positions),
            'abilities_per_position': {pos: len(abilities) for pos, abilities in analysis['position_analysis'].items()}
        }
        
        return analysis
    
    async def scrape_with_position_analysis(self, report_code: str, fight_id: int, source_id: int) -> Dict:
        """
        Scrape abilities and analyze action bar positions.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: The source/player ID
        
        Returns:
            Dictionary with scraping results and action bar analysis
        """
        async with WorkingAbilityScraper(headless=False) as scraper:
            # Scrape the abilities
            scraping_results = await scraper.scrape_all_abilities_for_fight(
                report_code, fight_id, source_id
            )
            
            # Analyze action bar positions
            action_bar_analysis = self.analyze_action_bar_positions(scraping_results)
            
            # Combine results
            combined_results = {
                'scraping_results': scraping_results,
                'action_bar_analysis': action_bar_analysis,
                'timestamp': datetime.now().isoformat()
            }
            
            return combined_results


async def test_action_bar_analysis():
    """Test action bar position analysis."""
    
    logger.info("Testing Action Bar Position Analysis")
    logger.info("=" * 80)
    
    # Test data
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    source_id = 1
    
    analyzer = ActionBarAnalyzer()
    
    try:
        # Scrape and analyze
        results = await analyzer.scrape_with_position_analysis(report_code, fight_id, source_id)
        
        # Save results
        output_file = f"action_bar_analysis_{report_code}_{fight_id}_{source_id}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {output_file}")
        
        # Print analysis
        logger.info("=" * 80)
        logger.info("ACTION BAR POSITION ANALYSIS:")
        logger.info("=" * 80)
        
        analysis = results['action_bar_analysis']
        
        logger.info(f"Total abilities found: {analysis['total_abilities']}")
        logger.info(f"Positions found: {analysis['action_bar_patterns']['positions_found']}")
        logger.info(f"Position range: {analysis['action_bar_patterns']['position_range']}")
        
        logger.info("\n🎯 PRIMARY BAR (Positions 0-5):")
        logger.info("-" * 50)
        for ability in analysis['primary_bar']:
            logger.info(f"  Position {ability['position']}: {ability['ability_name']} (ID: {ability['ability_id']})")
        
        logger.info("\n🎯 SECONDARY BAR (Positions 6-11):")
        logger.info("-" * 50)
        for ability in analysis['secondary_bar']:
            logger.info(f"  Position {ability['position']}: {ability['ability_name']} (ID: {ability['ability_id']})")
        
        if analysis['unknown_position']:
            logger.info("\n❓ UNKNOWN POSITIONS:")
            logger.info("-" * 50)
            for ability in analysis['unknown_position']:
                logger.info(f"  Position {ability['position']}: {ability['ability_name']} (ID: {ability['ability_id']})")
        
        # Analysis insights
        logger.info("\n💡 INSIGHTS:")
        logger.info("-" * 50)
        for insight in analysis['insights']:
            logger.info(f"  - {insight}")
        
        # Determine if we can map action bars
        primary_count = len(analysis['primary_bar'])
        secondary_count = len(analysis['secondary_bar'])
        
        logger.info("\n" + "=" * 80)
        logger.info("ACTION BAR MAPPING ANALYSIS:")
        logger.info("=" * 80)
        
        if primary_count > 0 or secondary_count > 0:
            logger.info("✅ SUCCESS: Found action bar position data!")
            logger.info(f"Primary bar abilities: {primary_count}")
            logger.info(f"Secondary bar abilities: {secondary_count}")
            
            if primary_count >= 6 and secondary_count >= 6:
                logger.info("🎉 PERFECT: Found complete action bar data (6+ abilities per bar)")
            elif primary_count >= 3 or secondary_count >= 3:
                logger.info("✅ GOOD: Found substantial action bar data (3+ abilities per bar)")
            else:
                logger.info("⚠️ PARTIAL: Found some action bar data but may be incomplete")
        else:
            logger.info("❌ No action bar position data found")
            logger.info("This could mean:")
            logger.info("  - All abilities have position 0 (no bar assignment)")
            logger.info("  - Position data is encoded differently")
            logger.info("  - Need to look for different patterns")
        
        return results
        
    except Exception as e:
        logger.error(f"Action bar analysis failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def investigate_position_patterns():
    """Investigate different position patterns that might exist."""
    
    logger.info("=" * 80)
    logger.info("INVESTIGATING POSITION PATTERNS")
    logger.info("=" * 80)
    
    # Test data
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    source_id = 1
    
    async with WorkingAbilityScraper(headless=False) as scraper:
        try:
            url = scraper.construct_fight_url(report_code, fight_id, source_id, "casts")
            logger.info(f"Investigating position patterns on: {url}")
            
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
            
            await asyncio.sleep(10)
            
            # Trigger ability loading
            await scraper._trigger_ability_loading()
            
            # Look for different position patterns
            logger.info("Searching for position patterns...")
            
            # Pattern 1: ability-{id}-{position}
            ability_spans = scraper.driver.find_elements(By.CSS_SELECTOR, "span[id^='ability-']")
            logger.info(f"Found {len(ability_spans)} ability spans")
            
            position_analysis = {}
            for span in ability_spans:
                span_id = span.get_attribute('id')
                span_text = span.text.strip()
                
                # Parse position
                match = re.match(r'^ability-(\d+)-(\d+)$', span_id)
                if match:
                    ability_id = match.group(1)
                    position = int(match.group(2))
                    
                    if position not in position_analysis:
                        position_analysis[position] = []
                    position_analysis[position].append({
                        'id': ability_id,
                        'name': span_text,
                        'element_id': span_id
                    })
            
            logger.info("\nPosition analysis:")
            for position in sorted(position_analysis.keys()):
                abilities = position_analysis[position]
                logger.info(f"Position {position}: {len(abilities)} abilities")
                for ability in abilities:
                    logger.info(f"  - {ability['name']} (ID: {ability['id']})")
            
            # Look for other patterns that might indicate action bar positions
            logger.info("\nSearching for other position indicators...")
            
            # Look for data attributes
            elements_with_data = scraper.driver.find_elements(By.CSS_SELECTOR, "[data-position], [data-bar], [data-slot]")
            logger.info(f"Found {len(elements_with_data)} elements with position data attributes")
            
            for element in elements_with_data[:5]:  # Show first 5
                logger.info(f"  - {element.tag_name}: {element.get_attribute('outerHTML')[:100]}...")
            
            # Look for classes that might indicate positions
            position_classes = scraper.driver.find_elements(By.CSS_SELECTOR, "[class*='position'], [class*='slot'], [class*='bar']")
            logger.info(f"Found {len(position_classes)} elements with position-related classes")
            
            for element in position_classes[:5]:  # Show first 5
                class_name = element.get_attribute('class')
                logger.info(f"  - Class: {class_name}")
            
        except Exception as e:
            logger.error(f"Position pattern investigation failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")


async def main():
    """Run action bar analysis tests."""
    
    logger.info("Starting Action Bar Analysis Tests")
    logger.info("=" * 80)
    
    # Test 1: Action bar analysis
    results = await test_action_bar_analysis()
    
    # Test 2: Position pattern investigation
    await investigate_position_patterns()
    
    logger.info("=" * 80)
    logger.info("Action bar analysis tests completed!")
    
    if results and results.get('action_bar_analysis', {}).get('primary_bar'):
        primary_count = len(results['action_bar_analysis']['primary_bar'])
        secondary_count = len(results['action_bar_analysis']['secondary_bar'])
        logger.info(f"✅ Found {primary_count} primary bar abilities and {secondary_count} secondary bar abilities")
    else:
        logger.info("❌ No clear action bar position data found")


if __name__ == "__main__":
    asyncio.run(main())
