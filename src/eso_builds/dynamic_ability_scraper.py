"""
Dynamic ability scraper for ESO Logs that handles JavaScript-loaded content.

This module provides functionality to scrape ability IDs and action bar information
from ESO Logs pages after JavaScript has loaded the dynamic content.
"""

import asyncio
import logging
import re
import time
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


class DynamicAbilityScraper:
    """Scraper that handles JavaScript-loaded ability data from ESO Logs."""
    
    def __init__(self, headless: bool = True, wait_timeout: int = 30):
        """
        Initialize the dynamic ability scraper.
        
        Args:
            headless: Whether to run browser in headless mode
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
                          data_type: str = "summary") -> str:
        """
        Construct ESO Logs web URL for a specific fight and source.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: Optional source/player ID
            data_type: Type of data to view (summary, casts, damage-done, healing, etc.)
        
        Returns:
            The constructed URL
        """
        base_url = f"https://www.esologs.com/reports/{report_code}?fight={fight_id}&type={data_type}"
        if source_id:
            base_url += f"&source={source_id}"
        return base_url
    
    async def scrape_abilities_with_js_wait(self, report_code: str, fight_id: int, source_id: int) -> Dict:
        """
        Scrape abilities from ESO Logs with JavaScript execution and waiting.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: The source/player ID
        
        Returns:
            Dictionary containing scraped ability data
        """
        try:
            # Construct URL for the casts page (most likely to have ability data)
            url = self.construct_fight_url(report_code, fight_id, source_id, "casts")
            logger.info(f"Loading page with JavaScript execution: {url}")
            
            # Load the page
            self.driver.get(url)
            
            # Wait for initial page load
            await asyncio.sleep(3)
            
            # Wait for body to be present
            WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for dynamic content to load
            logger.info("Waiting for dynamic content to load...")
            await asyncio.sleep(5)
            
            # Try to trigger any lazy loading by scrolling
            logger.info("Scrolling to trigger lazy loading...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            await asyncio.sleep(2)
            
            # Try to interact with elements that might trigger ability loading
            await self._try_trigger_ability_loading()
            
            # Search for ability data
            abilities = await self._extract_abilities_from_dom()
            
            logger.info(f"Found {len(abilities)} abilities after JavaScript execution")
            
            return {
                'report_code': report_code,
                'fight_id': fight_id,
                'source_id': source_id,
                'url': url,
                'abilities': abilities,
                'total_abilities': len(abilities)
            }
            
        except Exception as e:
            logger.error(f"Failed to scrape abilities with JavaScript: {e}")
            return {
                'error': str(e),
                'report_code': report_code,
                'fight_id': fight_id,
                'source_id': source_id,
                'abilities': []
            }
    
    async def _try_trigger_ability_loading(self):
        """Try to trigger ability data loading through various interactions."""
        try:
            # Try to click on elements that might load ability data
            click_selectors = [
                "button[onclick*='ability']",
                "[onclick*='loadAbilities']",
                ".ability-filter",
                ".talent-filter",
                "[data-toggle*='ability']"
            ]
            
            for selector in click_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Clicking element to trigger loading: {selector}")
                            self.driver.execute_script("arguments[0].click();", element)
                            await asyncio.sleep(1)
                except Exception as e:
                    logger.debug(f"Could not click element {selector}: {e}")
            
            # Try to hover over elements that might trigger loading
            hover_selectors = [
                "[onmouseover*='loadAbilities']",
                ".ability-menu-trigger",
                ".talent-menu-trigger"
            ]
            
            for selector in hover_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            logger.info(f"Hovering over element: {selector}")
                            self.driver.execute_script("arguments[0].dispatchEvent(new Event('mouseover'));", element)
                            await asyncio.sleep(1)
                except Exception as e:
                    logger.debug(f"Could not hover over element {selector}: {e}")
            
            # Wait for any triggered loading to complete
            await asyncio.sleep(3)
            
        except Exception as e:
            logger.warning(f"Error triggering ability loading: {e}")
    
    async def _extract_abilities_from_dom(self) -> List[Dict]:
        """Extract ability data from the current DOM state."""
        abilities = []
        
        try:
            # Search for the specific talent-ability pattern
            ability_selectors = [
                "span[id^='talent-ability-']",
                "[id*='talent-ability-']",
                "span[id*='ability-']",
                "[data-ability-id]",
                "[class*='ability']"
            ]
            
            for selector in ability_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements:
                        ability_data = self._extract_ability_from_element(element)
                        if ability_data:
                            abilities.append(ability_data)
                            
                except Exception as e:
                    logger.debug(f"Error with selector {selector}: {e}")
            
            # Also try to find abilities by searching for ability names in spans
            all_spans = self.driver.find_elements(By.TAG_NAME, "span")
            for span in all_spans:
                span_text = span.text.strip()
                if span_text and len(span_text) > 3:  # Likely ability names
                    span_id = span.get_attribute('id') or ''
                    span_class = span.get_attribute('class') or ''
                    
                    # Check if this looks like an ability span
                    if any(keyword in span_id.lower() for keyword in ['ability', 'talent', 'skill', 'spell']):
                        ability_data = self._extract_ability_from_element(span)
                        if ability_data and ability_data not in abilities:
                            abilities.append(ability_data)
            
            # Remove duplicates
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
            logger.error(f"Error extracting abilities from DOM: {e}")
            return []
    
    def _extract_ability_from_element(self, element) -> Optional[Dict]:
        """Extract ability data from a single element."""
        try:
            element_id = element.get_attribute('id') or ''
            element_text = element.text.strip()
            element_class = element.get_attribute('class') or ''
            element_tag = element.tag_name
            
            if not element_text:
                return None
            
            # Try to extract ability ID from various patterns
            ability_id = None
            patterns = [
                r'^talent-ability-(\d+)-\d+$',  # talent-ability-{id}-{something}
                r'ability-(\d+)',               # ability-{id}
                r'talent-(\d+)',                # talent-{id}
                r'skill-(\d+)',                 # skill-{id}
                r'spell-(\d+)',                 # spell-{id}
                r'(\d{5,})',                    # Any 5+ digit number (likely game ID)
            ]
            
            for pattern in patterns:
                match = re.search(pattern, element_id)
                if match:
                    ability_id = match.group(1)
                    break
            
            # If no ID found in element ID, try to extract from other attributes
            if not ability_id:
                data_ability_id = element.get_attribute('data-ability-id')
                if data_ability_id:
                    ability_id = data_ability_id
            
            return {
                'ability_id': ability_id,
                'ability_name': element_text,
                'element_id': element_id,
                'element_class': element_class,
                'element_tag': element_tag,
                'html': element.get_attribute('outerHTML')[:200]  # First 200 chars
            }
            
        except Exception as e:
            logger.debug(f"Error extracting ability from element: {e}")
            return None
    
    async def scrape_multiple_pages(self, report_code: str, fight_id: int, source_id: int) -> Dict:
        """
        Scrape abilities from multiple page types.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: The source/player ID
        
        Returns:
            Dictionary containing abilities from all pages
        """
        results = {
            'report_code': report_code,
            'fight_id': fight_id,
            'source_id': source_id,
            'timestamp': time.time(),
            'pages': {},
            'all_abilities': {}
        }
        
        # Try different page types that might have ability data
        page_types = ['casts', 'damage-done', 'healing', 'summary']
        
        for page_type in page_types:
            try:
                logger.info(f"Scraping {page_type} page...")
                
                url = self.construct_fight_url(report_code, fight_id, source_id, page_type)
                
                # Load page
                self.driver.get(url)
                await asyncio.sleep(3)
                
                # Wait for dynamic content
                WebDriverWait(self.driver, self.wait_timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                await asyncio.sleep(5)
                
                # Try to trigger loading
                await self._try_trigger_ability_loading()
                
                # Extract abilities
                abilities = await self._extract_abilities_from_dom()
                
                results['pages'][page_type] = {
                    'url': url,
                    'abilities': abilities,
                    'count': len(abilities)
                }
                
                # Merge into all_abilities
                for ability in abilities:
                    ability_id = ability.get('ability_id', ability.get('ability_name', ''))
                    if ability_id not in results['all_abilities']:
                        results['all_abilities'][ability_id] = ability
                        results['all_abilities'][ability_id]['found_on_pages'] = [page_type]
                    else:
                        results['all_abilities'][ability_id]['found_on_pages'].append(page_type)
                
                logger.info(f"Found {len(abilities)} abilities on {page_type} page")
                
            except Exception as e:
                logger.error(f"Error scraping {page_type} page: {e}")
                results['pages'][page_type] = {
                    'error': str(e),
                    'abilities': [],
                    'count': 0
                }
        
        results['total_unique_abilities'] = len(results['all_abilities'])
        return results


# Convenience function for easy usage
async def scrape_abilities_for_fight(report_code: str, fight_id: int, source_id: int, 
                                   headless: bool = True) -> Dict:
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
    async with DynamicAbilityScraper(headless=headless) as scraper:
        return await scraper.scrape_multiple_pages(report_code, fight_id, source_id)
