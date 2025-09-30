#!/usr/bin/env python3
"""
Test script for Playwright-based ESO Logs ability scraper.

This script demonstrates Playwright's ability to scrape ability IDs and action bar
information from ESO Logs pages with full JavaScript execution.
"""

import asyncio
import json
import logging
import re
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlaywrightESOScraper:
    """ESO Logs scraper using Playwright for headless browser automation."""
    
    def __init__(self, headless: bool = True):
        """
        Initialize the Playwright scraper.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        
        try:
            from playwright.async_api import async_playwright
            self.playwright_available = True
        except ImportError:
            self.playwright_available = False
            logger.error("Playwright not installed. Install with: pip install playwright && playwright install chromium")
    
    def construct_fight_url(self, report_code: str, fight_id: int, source_id: Optional[int] = None, 
                          data_type: str = "casts") -> str:
        """
        Construct ESO Logs web URL for a specific fight and source.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: Optional source/player ID
            data_type: Type of data to view (casts, damage-done, healing, summary)
        
        Returns:
            The constructed URL
        """
        base_url = f"https://www.esologs.com/reports/{report_code}?fight={fight_id}&type={data_type}"
        if source_id:
            base_url += f"&source={source_id}"
        return base_url
    
    async def scrape_abilities_with_playwright(self, report_code: str, fight_id: int, source_id: int) -> Dict:
        """
        Scrape abilities using Playwright with full JavaScript execution.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: The source/player ID
        
        Returns:
            Dictionary containing scraped ability data
        """
        if not self.playwright_available:
            return {'error': 'Playwright not available'}
        
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                # Launch browser (completely headless)
                logger.info("Launching Playwright browser...")
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()
                
                # Construct URL
                url = self.construct_fight_url(report_code, fight_id, source_id, "casts")
                logger.info(f"Loading page: {url}")
                
                # Navigate to page
                await page.goto(url, wait_until='networkidle')
                
                # Wait for initial content
                logger.info("Waiting for page content to load...")
                await page.wait_for_selector('body', timeout=30000)
                await asyncio.sleep(5)
                
                # Wait for dynamic content to load
                logger.info("Waiting for dynamic content...")
                await asyncio.sleep(10)
                
                # Try to trigger ability loading by clicking elements
                logger.info("Attempting to trigger ability loading...")
                await self._trigger_ability_loading_playwright(page)
                
                # Extract abilities
                abilities = await self._extract_abilities_playwright(page)
                
                # Analyze action bar positions
                action_bar_analysis = self._analyze_action_bars_from_abilities(abilities)
                
                await browser.close()
                
                return {
                    'report_code': report_code,
                    'fight_id': fight_id,
                    'source_id': source_id,
                    'url': url,
                    'abilities': abilities,
                    'total_abilities': len(abilities),
                    'action_bar_analysis': action_bar_analysis,
                    'timestamp': datetime.now().isoformat(),
                    'scraper': 'playwright'
                }
                
        except Exception as e:
            logger.error(f"Playwright scraping failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'error': str(e),
                'report_code': report_code,
                'fight_id': fight_id,
                'source_id': source_id,
                'abilities': []
            }
    
    async def _trigger_ability_loading_playwright(self, page):
        """Trigger ability data loading by interacting with the page."""
        try:
            # Look for ability elements with onclick handlers
            ability_elements = await page.query_selector_all("td[onclick*='addPinWithAbility']")
            logger.info(f"Found {len(ability_elements)} ability elements with onclick handlers")
            
            # Click on each ability element to trigger data loading
            for i, element in enumerate(ability_elements[:10]):  # Limit to first 10
                try:
                    if await element.is_visible():
                        logger.info(f"Clicking ability element {i+1}")
                        await element.click()
                        await asyncio.sleep(1)  # Wait between clicks
                except Exception as e:
                    logger.debug(f"Could not click ability element {i+1}: {e}")
            
            # Wait for any triggered loading to complete
            await asyncio.sleep(3)
            
        except Exception as e:
            logger.warning(f"Error triggering ability loading: {e}")
    
    async def _extract_abilities_playwright(self, page) -> List[Dict]:
        """Extract ability data from the page."""
        abilities = []
        
        try:
            # Search for ability spans
            ability_spans = await page.query_selector_all("span[id^='ability-']")
            logger.info(f"Found {len(ability_spans)} ability spans")
            
            for index, span in enumerate(ability_spans):
                try:
                    span_id = await span.get_attribute('id')
                    span_text = await span.text_content()
                    span_class = await span.get_attribute('class')
                    
                    if span_text and span_text.strip():
                        # Parse ability ID
                        match = re.match(r'^ability-(\d+)-(\d+)$', span_id or '')
                        ability_id = match.group(1) if match else None
                        position_in_id = int(match.group(2)) if match and match.group(2) else 0
                        
                        ability_data = {
                            'dom_index': index,
                            'ability_id': ability_id,
                            'ability_name': span_text.strip(),
                            'element_id': span_id,
                            'element_class': span_class,
                            'position_in_id': position_in_id,
                            'html': await span.inner_html()
                        }
                        
                        abilities.append(ability_data)
                        logger.info(f"DOM {index}: {span_text.strip()} (ID: {ability_id})")
                        
                except Exception as e:
                    logger.debug(f"Error extracting ability from span {index}: {e}")
            
            # Also look for onclick handlers with ability data
            onclick_elements = await page.query_selector_all("[onclick*='addPinWithAbility']")
            logger.info(f"Found {len(onclick_elements)} onclick ability elements")
            
            for element in onclick_elements:
                try:
                    onclick = await element.get_attribute('onclick')
                    if onclick and 'addPinWithAbility' in onclick:
                        # Extract ability ID from onclick handler
                        match = re.search(r'addPinWithAbility\((\d+),\s*[\'"]([^\'"]*)[\'"]', onclick)
                        if match:
                            ability_id = match.group(1)
                            ability_name = match.group(2)
                            
                            # Check if we already have this ability
                            if not any(a['ability_id'] == ability_id for a in abilities):
                                abilities.append({
                                    'dom_index': len(abilities),
                                    'ability_id': ability_id,
                                    'ability_name': ability_name,
                                    'element_id': await element.get_attribute('id'),
                                    'element_class': await element.get_attribute('class'),
                                    'position_in_id': 0,
                                    'html': await element.inner_html(),
                                    'source': 'onclick_handler'
                                })
                                logger.info(f"From onclick: {ability_name} (ID: {ability_id})")
                                
                except Exception as e:
                    logger.debug(f"Error extracting ability from onclick: {e}")
            
            return abilities
            
        except Exception as e:
            logger.error(f"Error extracting abilities: {e}")
            return []
    
    def _analyze_action_bars_from_abilities(self, abilities: List[Dict]) -> Dict:
        """Analyze action bar positions from the extracted abilities."""
        analysis = {
            'total_abilities': len(abilities),
            'primary_bar': [],
            'secondary_bar': [],
            'utility_abilities': [],
            'dom_order_analysis': []
        }
        
        # Sort by DOM index to maintain order
        sorted_abilities = sorted(abilities, key=lambda x: x.get('dom_index', 0))
        
        # Strategy 1: First 6 = Primary bar, Next 6 = Secondary bar
        if len(sorted_abilities) >= 12:
            analysis['primary_bar'] = sorted_abilities[:6]
            analysis['secondary_bar'] = sorted_abilities[6:12]
            analysis['utility_abilities'] = sorted_abilities[12:]
            
            analysis['dom_order_analysis'].append("Strategy 1: First 6 = Primary, Next 6 = Secondary")
        
        # Add DOM order analysis
        for ability in sorted_abilities:
            analysis['dom_order_analysis'].append(
                f"DOM {ability.get('dom_index', 0)}: {ability['ability_name']} (ID: {ability['ability_id']})"
            )
        
        return analysis


async def test_playwright_scraper():
    """Test the Playwright scraper."""
    
    logger.info("Testing Playwright ESO Logs Scraper")
    logger.info("=" * 80)
    
    # Test data
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    source_id = 1
    
    scraper = PlaywrightESOScraper(headless=True)  # Completely headless
    
    try:
        # Test the scraper
        results = await scraper.scrape_abilities_with_playwright(report_code, fight_id, source_id)
        
        # Save results
        output_file = f"playwright_scraper_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {output_file}")
        
        # Print results
        if 'error' in results:
            logger.error(f"❌ Scraping failed: {results['error']}")
            return results
        
        logger.info("=" * 80)
        logger.info("PLAYWRIGHT SCRAPER RESULTS:")
        logger.info("=" * 80)
        
        total_abilities = results.get('total_abilities', 0)
        logger.info(f"✅ Total abilities found: {total_abilities}")
        
        abilities = results.get('abilities', [])
        if abilities:
            logger.info(f"\n🎯 ABILITIES FOUND (in DOM order):")
            logger.info("-" * 60)
            
            for ability in abilities:
                dom_index = ability.get('dom_index', 0)
                ability_name = ability.get('ability_name', 'No name')
                ability_id = ability.get('ability_id', 'No ID')
                element_id = ability.get('element_id', 'No element ID')
                logger.info(f"  {dom_index:2d}: {ability_name} (ID: {ability_id}) [element: {element_id}]")
        
        # Action bar analysis
        action_bar_analysis = results.get('action_bar_analysis', {})
        
        logger.info(f"\n🎯 INFERRED PRIMARY BAR:")
        logger.info("-" * 60)
        primary_bar = action_bar_analysis.get('primary_bar', [])
        for ability in primary_bar:
            dom_index = ability.get('dom_index', 0)
            logger.info(f"  {dom_index:2d}: {ability['ability_name']} (ID: {ability['ability_id']})")
        
        logger.info(f"\n🎯 INFERRED SECONDARY BAR:")
        logger.info("-" * 60)
        secondary_bar = action_bar_analysis.get('secondary_bar', [])
        for ability in secondary_bar:
            dom_index = ability.get('dom_index', 0)
            logger.info(f"  {dom_index:2d}: {ability['ability_name']} (ID: {ability['ability_id']})")
        
        if action_bar_analysis.get('utility_abilities'):
            logger.info(f"\n🎯 UTILITY ABILITIES:")
            logger.info("-" * 60)
            utility = action_bar_analysis.get('utility_abilities', [])
            for ability in utility:
                dom_index = ability.get('dom_index', 0)
                logger.info(f"  {dom_index:2d}: {ability['ability_name']} (ID: {ability['ability_id']})")
        
        # Summary
        primary_count = len(primary_bar)
        secondary_count = len(secondary_bar)
        
        logger.info("\n" + "=" * 80)
        logger.info("PLAYWRIGHT SCRAPER SUMMARY:")
        logger.info("=" * 80)
        
        logger.info(f"✅ SUCCESS: Playwright scraper found {total_abilities} abilities!")
        logger.info(f"Primary bar: {primary_count} abilities")
        logger.info(f"Secondary bar: {secondary_count} abilities")
        logger.info("🚀 Playwright: Completely headless, no external browser required!")
        
        if primary_count == 6 and secondary_count == 6:
            logger.info("🎉 PERFECT: Found exactly 6 abilities per action bar!")
        elif primary_count >= 5 and secondary_count >= 5:
            logger.info("✅ GOOD: Found 5+ abilities per action bar")
        
        return results
        
    except Exception as e:
        logger.error(f"Playwright scraper test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def main():
    """Run the Playwright scraper test."""
    
    logger.info("Starting Playwright ESO Logs Scraper Test")
    logger.info("=" * 80)
    
    # Test Playwright scraper
    results = await test_playwright_scraper()
    
    logger.info("=" * 80)
    logger.info("Playwright scraper test completed!")
    
    if results and results.get('total_abilities', 0) > 0:
        logger.info(f"✅ SUCCESS: Playwright found {results['total_abilities']} abilities")
        logger.info("🚀 Playwright is an excellent choice for headless ESO Logs scraping!")
    else:
        logger.info("❌ Playwright scraper test failed")


if __name__ == "__main__":
    asyncio.run(main())
