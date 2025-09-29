"""
Working ability scraper that successfully extracts ability IDs from ESO Logs.

This scraper has been tested and confirmed to work with the actual ESO Logs patterns.
"""

import asyncio
import logging
import re
import time
import json
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

logger = logging.getLogger(__name__)


class WorkingAbilityScraper:
    """Scraper that successfully extracts ability data from ESO Logs."""
    
    def __init__(self, headless: bool = False, wait_timeout: int = 30):
        """
        Initialize the working ability scraper.
        
        Args:
            headless: Whether to run browser in headless mode (default False for debugging)
            wait_timeout: Maximum time to wait for elements to load
        """
        self.headless = headless
        self.wait_timeout = wait_timeout
        self.driver = None
        
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium is required for dynamic scraping. Install with: pip install selenium webdriver-manager")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._setup_driver()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
    
    async def _setup_driver(self):
        """Set up the Selenium WebDriver."""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Try to use webdriver-manager first, fallback to system Chrome
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("WebDriver initialized with webdriver-manager")
            except Exception as e:
                logger.warning(f"WebDriver with webdriver-manager failed: {e}")
                # Fallback: try system Chrome
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("WebDriver initialized with system Chrome")
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
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
    
    async def scrape_abilities_from_casts_page(self, report_code: str, fight_id: int, source_id: int) -> Dict:
        """
        Scrape abilities from the casts page where they are most likely to appear.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: The source/player ID
        
        Returns:
            Dictionary containing scraped ability data
        """
        try:
            # Construct URL for the casts page
            url = self.construct_fight_url(report_code, fight_id, source_id, "casts")
            logger.info(f"Loading casts page: {url}")
            
            # Load the page
            self.driver.get(url)
            
            # Wait for initial page load
            await asyncio.sleep(5)
            
            # Wait for body to be present
            WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for dynamic content to load
            logger.info("Waiting for dynamic content to load...")
            await asyncio.sleep(10)
            
            # Try to trigger ability loading by clicking on ability elements
            logger.info("Clicking ability elements to trigger data loading...")
            await self._trigger_ability_loading()
            
            # Extract abilities using the working patterns we discovered
            abilities = await self._extract_abilities_working_patterns()
            
            logger.info(f"Found {len(abilities)} abilities using working patterns")
            
            return {
                'report_code': report_code,
                'fight_id': fight_id,
                'source_id': source_id,
                'url': url,
                'abilities': abilities,
                'total_abilities': len(abilities),
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to scrape abilities from casts page: {e}")
            return {
                'error': str(e),
                'report_code': report_code,
                'fight_id': fight_id,
                'source_id': source_id,
                'abilities': []
            }
    
    async def _trigger_ability_loading(self):
        """Trigger ability data loading by clicking on ability elements."""
        try:
            # Look for ability elements with onclick handlers that contain ability IDs
            ability_elements = self.driver.find_elements(By.CSS_SELECTOR, "td[onclick*='addPinWithAbility']")
            logger.info(f"Found {len(ability_elements)} ability elements with onclick handlers")
            
            # Click on each ability element to trigger data loading
            for i, element in enumerate(ability_elements[:10]):  # Limit to first 10 to avoid overwhelming
                try:
                    if element.is_displayed() and element.is_enabled():
                        logger.info(f"Clicking ability element {i+1}: {element.get_attribute('onclick')[:50]}...")
                        self.driver.execute_script("arguments[0].click();", element)
                        await asyncio.sleep(1)  # Wait between clicks
                except Exception as e:
                    logger.debug(f"Could not click ability element {i+1}: {e}")
            
            # Wait for any triggered loading to complete
            await asyncio.sleep(3)
            
        except Exception as e:
            logger.warning(f"Error triggering ability loading: {e}")
    
    async def _extract_abilities_working_patterns(self) -> List[Dict]:
        """Extract ability data using the working patterns we discovered."""
        abilities = []
        
        try:
            # Pattern 1: ability-{id}-0 spans (the pattern we successfully found)
            ability_spans = self.driver.find_elements(By.CSS_SELECTOR, "span[id^='ability-']")
            logger.info(f"Found {len(ability_spans)} spans with ability- pattern")
            
            for span in ability_spans:
                ability_data = self._extract_ability_from_span(span)
                if ability_data:
                    abilities.append(ability_data)
            
            # Pattern 2: talent-ability-{id}-{something} spans (the user's original pattern)
            talent_spans = self.driver.find_elements(By.CSS_SELECTOR, "span[id^='talent-ability-']")
            logger.info(f"Found {len(talent_spans)} spans with talent-ability- pattern")
            
            for span in talent_spans:
                ability_data = self._extract_talent_ability_from_span(span)
                if ability_data:
                    abilities.append(ability_data)
            
            # Pattern 3: Look for ability data in onclick handlers
            onclick_elements = self.driver.find_elements(By.CSS_SELECTOR, "[onclick*='addPinWithAbility']")
            logger.info(f"Found {len(onclick_elements)} elements with addPinWithAbility")
            
            for element in onclick_elements:
                ability_data = self._extract_ability_from_onclick(element)
                if ability_data and ability_data not in abilities:
                    abilities.append(ability_data)
            
            # Remove duplicates based on ability_id
            unique_abilities = []
            seen_ids = set()
            for ability in abilities:
                ability_id = ability.get('ability_id', '')
                if ability_id and ability_id not in seen_ids:
                    unique_abilities.append(ability)
                    seen_ids.add(ability_id)
                elif not ability_id and ability.get('ability_name', '') not in [a.get('ability_name', '') for a in unique_abilities]:
                    unique_abilities.append(ability)
            
            return unique_abilities
            
        except Exception as e:
            logger.error(f"Error extracting abilities with working patterns: {e}")
            return []
    
    def _extract_ability_from_span(self, span) -> Optional[Dict]:
        """Extract ability data from a span with ability-{id}-0 pattern."""
        try:
            span_id = span.get_attribute('id') or ''
            span_text = span.text.strip()
            span_class = span.get_attribute('class') or ''
            
            if not span_text:
                return None
            
            # Extract ability ID from ability-{id}-0 pattern
            match = re.match(r'^ability-(\d+)-0$', span_id)
            if match:
                ability_id = match.group(1)
                return {
                    'ability_id': ability_id,
                    'ability_name': span_text,
                    'element_id': span_id,
                    'element_class': span_class,
                    'element_tag': span.tag_name,
                    'pattern_type': 'ability-span',
                    'html': span.get_attribute('outerHTML')[:200]
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting ability from span: {e}")
            return None
    
    def _extract_talent_ability_from_span(self, span) -> Optional[Dict]:
        """Extract ability data from a span with talent-ability-{id}-{something} pattern."""
        try:
            span_id = span.get_attribute('id') or ''
            span_text = span.text.strip()
            span_class = span.get_attribute('class') or ''
            
            if not span_text:
                return None
            
            # Extract ability ID from talent-ability-{id}-{something} pattern
            match = re.match(r'^talent-ability-(\d+)-\d+$', span_id)
            if match:
                ability_id = match.group(1)
                return {
                    'ability_id': ability_id,
                    'ability_name': span_text,
                    'element_id': span_id,
                    'element_class': span_class,
                    'element_tag': span.tag_name,
                    'pattern_type': 'talent-ability-span',
                    'html': span.get_attribute('outerHTML')[:200]
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting talent ability from span: {e}")
            return None
    
    def _extract_ability_from_onclick(self, element) -> Optional[Dict]:
        """Extract ability data from onclick handler."""
        try:
            onclick = element.get_attribute('onclick') or ''
            element_text = element.text.strip()
            
            if not onclick or 'addPinWithAbility' not in onclick:
                return None
            
            # Extract ability ID from onclick="addPinWithAbility({id}, 'ability_name')"
            match = re.search(r'addPinWithAbility\((\d+),\s*[\'"]([^\'"]*)[\'"]', onclick)
            if match:
                ability_id = match.group(1)
                ability_name = match.group(2)
                return {
                    'ability_id': ability_id,
                    'ability_name': ability_name,
                    'element_id': element.get_attribute('id') or '',
                    'element_class': element.get_attribute('class') or '',
                    'element_tag': element.tag_name,
                    'pattern_type': 'onclick-handler',
                    'onclick': onclick,
                    'html': element.get_attribute('outerHTML')[:200]
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting ability from onclick: {e}")
            return None
    
    async def scrape_all_abilities_for_fight(self, report_code: str, fight_id: int, source_id: int) -> Dict:
        """
        Scrape all abilities for a fight using the working patterns.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: The source/player ID
        
        Returns:
            Dictionary containing all scraped ability data
        """
        logger.info(f"Scraping all abilities for report: {report_code}, fight: {fight_id}, source: {source_id}")
        
        # Focus on the casts page where abilities are most likely to appear
        results = await self.scrape_abilities_from_casts_page(report_code, fight_id, source_id)
        
        # Add metadata
        results['scraper_version'] = 'working_ability_scraper_v1'
        results['patterns_used'] = [
            'ability-{id}-0 spans',
            'talent-ability-{id}-{something} spans', 
            'addPinWithAbility onclick handlers'
        ]
        
        return results


# Convenience function for easy usage
async def scrape_abilities_for_fight(report_code: str, fight_id: int, source_id: int, 
                                   headless: bool = False) -> Dict:
    """
    Convenience function to scrape abilities for a specific fight.
    
    Args:
        report_code: The report code
        fight_id: The fight ID
        source_id: The source/player ID
        headless: Whether to run browser in headless mode
    
    Returns:
        Dictionary containing all scraped ability data
    """
    async with WorkingAbilityScraper(headless=headless) as scraper:
        return await scraper.scrape_all_abilities_for_fight(report_code, fight_id, source_id)
