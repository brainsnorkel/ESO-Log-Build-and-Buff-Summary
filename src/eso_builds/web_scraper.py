"""
Web scraper for extracting ability IDs and action bar information from ESO Logs.

This module provides functionality to scrape ESO Logs web pages to extract
ability IDs, action bar information, and other data not available through the API.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


class ESOLogsWebScraper:
    """Web scraper for ESO Logs pages to extract ability and action bar data."""
    
    def __init__(self, headless: bool = True, delay_between_requests: float = 2.0):
        """
        Initialize the web scraper.
        
        Args:
            headless: Whether to run browser in headless mode
            delay_between_requests: Delay between requests to respect rate limits
        """
        self.headless = headless
        self.delay_between_requests = delay_between_requests
        self.driver = None
        self.session = requests.Session()
        
        # Set up session headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._setup_driver()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup()
    
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
            
            # Use webdriver-manager to handle Chrome driver
            self.driver = webdriver.Chrome(
                service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            logger.info("WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    async def _cleanup(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
    
    def construct_fight_url(self, report_code: str, fight_id: int, source_id: Optional[int] = None, 
                          data_type: str = "summary") -> str:
        """
        Construct ESO Logs web URL for a specific fight and source.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: Optional source/player ID
            data_type: Type of data to view (summary, damage-done, healing, casts, etc.)
        
        Returns:
            The constructed URL
        """
        base_url = f"https://www.esologs.com/reports/{report_code}?fight={fight_id}&type={data_type}"
        if source_id:
            base_url += f"&source={source_id}"
        return base_url
    
    async def scrape_ability_data(self, report_code: str, fight_id: int, source_id: Optional[int] = None) -> Dict:
        """
        Scrape ability data from an ESO Logs fight page.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: Optional source/player ID
        
        Returns:
            Dictionary containing scraped ability data
        """
        try:
            # Construct URL for the casts page (most likely to have ability data)
            url = self.construct_fight_url(report_code, fight_id, source_id, "casts")
            logger.info(f"Scraping ability data from: {url}")
            
            # Load the page
            self.driver.get(url)
            
            # Wait for the page to load
            await asyncio.sleep(3)
            
            # Try to extract ability data using multiple methods
            ability_data = {}
            
            # Method 1: Try to find ability elements in the casts table
            ability_data.update(await self._extract_abilities_from_casts_table())
            
            # Method 2: Try to find ability data in JavaScript variables
            ability_data.update(await self._extract_abilities_from_js_variables())
            
            # Method 3: Try to find ability data in network requests
            ability_data.update(await self._extract_abilities_from_network_requests())
            
            logger.info(f"Extracted ability data: {len(ability_data)} abilities found")
            return ability_data
            
        except Exception as e:
            logger.error(f"Failed to scrape ability data: {e}")
            return {}
    
    async def _extract_abilities_from_casts_table(self) -> Dict:
        """Extract abilities from the casts table on the page."""
        abilities = {}
        
        try:
            # Wait for the casts table to load
            wait = WebDriverWait(self.driver, 10)
            
            # Look for ability elements in various possible selectors
            ability_selectors = [
                "tr[data-ability-id]",
                ".ability-name",
                ".cast-ability",
                "[class*='ability']",
                "td[title*='ability']"
            ]
            
            for selector in ability_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.debug(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements:
                        ability_id = element.get_attribute('data-ability-id')
                        ability_name = element.text.strip()
                        
                        if ability_id and ability_name:
                            abilities[ability_id] = {
                                'name': ability_name,
                                'source': 'casts_table',
                                'element': element.get_attribute('outerHTML')[:200]  # First 200 chars for debugging
                            }
                            logger.debug(f"Found ability: {ability_name} (ID: {ability_id})")
                
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Failed to extract abilities from casts table: {e}")
        
        return abilities
    
    async def _extract_abilities_from_js_variables(self) -> Dict:
        """Extract ability data from JavaScript variables on the page."""
        abilities = {}
        
        try:
            # Execute JavaScript to look for ability data in global variables
            js_queries = [
                "window.abilities || {}",
                "window.reportData || {}",
                "window.fightData || {}",
                "window.playerData || {}",
                "Object.keys(window).filter(k => k.includes('ability') || k.includes('Ability'))"
            ]
            
            for query in js_queries:
                try:
                    result = self.driver.execute_script(f"return {query};")
                    if result:
                        logger.debug(f"JS query '{query}' returned: {type(result)}")
                        
                        if isinstance(result, dict):
                            for key, value in result.items():
                                if isinstance(value, dict) and ('name' in value or 'id' in value):
                                    abilities[key] = {
                                        'name': value.get('name', key),
                                        'source': 'js_variables',
                                        'data': value
                                    }
                        
                        elif isinstance(result, list):
                            for item in result:
                                if isinstance(item, dict) and ('name' in item or 'id' in item):
                                    abilities[item.get('id', item.get('name'))] = {
                                        'name': item.get('name', 'Unknown'),
                                        'source': 'js_variables',
                                        'data': item
                                    }
                
                except Exception as e:
                    logger.debug(f"JS query '{query}' failed: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Failed to extract abilities from JS variables: {e}")
        
        return abilities
    
    async def _extract_abilities_from_network_requests(self) -> Dict:
        """Extract ability data from network requests made by the page."""
        abilities = {}
        
        try:
            # Enable network logging
            self.driver.execute_cdp_cmd('Network.enable', {})
            
            # Get network logs
            logs = self.driver.get_log('performance')
            
            for log in logs:
                message = log['message']
                if 'Network.responseReceived' in message:
                    # Parse network response for ability data
                    try:
                        import json
                        response_data = json.loads(message)
                        
                        if 'params' in response_data and 'response' in response_data['params']:
                            url = response_data['params']['response'].get('url', '')
                            
                            # Look for API endpoints that might contain ability data
                            if any(keyword in url.lower() for keyword in ['ability', 'cast', 'damage', 'api']):
                                logger.debug(f"Found potential ability API endpoint: {url}")
                                
                                # Try to get the response body (this is complex with Selenium)
                                # For now, just log the URL for manual inspection
                                abilities[f"network_{url}"] = {
                                    'name': 'Network Request',
                                    'source': 'network_requests',
                                    'url': url
                                }
                    
                    except Exception as e:
                        logger.debug(f"Failed to parse network log: {e}")
                        continue
        
        except Exception as e:
            logger.warning(f"Failed to extract abilities from network requests: {e}")
        
        return abilities
    
    async def scrape_action_bar_data(self, report_code: str, fight_id: int, source_id: int) -> Dict:
        """
        Attempt to scrape action bar data from ESO Logs.
        
        Note: This is experimental and may not work as ESO Logs may not expose
        action bar information in a scrapeable format.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: The source/player ID
        
        Returns:
            Dictionary containing any action bar data found
        """
        try:
            url = self.construct_fight_url(report_code, fight_id, source_id, "summary")
            logger.info(f"Attempting to scrape action bar data from: {url}")
            
            self.driver.get(url)
            await asyncio.sleep(3)
            
            action_bar_data = {}
            
            # Look for action bar elements (this is highly speculative)
            action_bar_selectors = [
                ".action-bar",
                ".ability-bar",
                ".skill-bar",
                "[class*='action']",
                "[class*='bar']",
                "[data-bar]",
                "[data-slot]"
            ]
            
            for selector in action_bar_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.debug(f"Found {len(elements)} potential action bar elements with selector: {selector}")
                    
                    for i, element in enumerate(elements):
                        bar_data = {
                            'selector': selector,
                            'index': i,
                            'text': element.text.strip(),
                            'attributes': dict(element.get_property('attributes') or {}),
                            'html': element.get_attribute('outerHTML')[:300]
                        }
                        action_bar_data[f"{selector}_{i}"] = bar_data
                
                except Exception as e:
                    logger.debug(f"Action bar selector {selector} failed: {e}")
                    continue
            
            logger.info(f"Found {len(action_bar_data)} potential action bar elements")
            return action_bar_data
            
        except Exception as e:
            logger.error(f"Failed to scrape action bar data: {e}")
            return {}
    
    async def scrape_player_gear_data(self, report_code: str, fight_id: int, source_id: int) -> Dict:
        """
        Scrape player gear data from ESO Logs.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: The source/player ID
        
        Returns:
            Dictionary containing gear data
        """
        try:
            # Try the summary page first, then character details
            urls_to_try = [
                self.construct_fight_url(report_code, fight_id, source_id, "summary"),
                self.construct_fight_url(report_code, fight_id, source_id, "damage-done"),
            ]
            
            gear_data = {}
            
            for url in urls_to_try:
                logger.info(f"Scraping gear data from: {url}")
                self.driver.get(url)
                await asyncio.sleep(3)
                
                # Look for gear-related elements
                gear_selectors = [
                    ".gear-item",
                    ".equipment",
                    "[data-item-id]",
                    "[data-set-id]",
                    ".item-name",
                    ".set-name"
                ]
                
                for selector in gear_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        logger.debug(f"Found {len(elements)} gear elements with selector: {selector}")
                        
                        for i, element in enumerate(elements):
                            item_data = {
                                'selector': selector,
                                'index': i,
                                'text': element.text.strip(),
                                'item_id': element.get_attribute('data-item-id'),
                                'set_id': element.get_attribute('data-set-id'),
                                'html': element.get_attribute('outerHTML')[:200]
                            }
                            gear_data[f"{selector}_{i}"] = item_data
                    
                    except Exception as e:
                        logger.debug(f"Gear selector {selector} failed: {e}")
                        continue
            
            logger.info(f"Found {len(gear_data)} gear elements")
            return gear_data
            
        except Exception as e:
            logger.error(f"Failed to scrape gear data: {e}")
            return {}


# Convenience function for easy usage
async def scrape_fight_data(report_code: str, fight_id: int, source_id: Optional[int] = None, 
                          headless: bool = True) -> Dict:
    """
    Convenience function to scrape all available data from an ESO Logs fight.
    
    Args:
        report_code: The report code
        fight_id: The fight ID
        source_id: Optional source/player ID
        headless: Whether to run browser in headless mode
    
    Returns:
        Dictionary containing all scraped data
    """
    scraped_data = {
        'abilities': {},
        'action_bars': {},
        'gear': {}
    }
    
    async with ESOLogsWebScraper(headless=headless) as scraper:
        # Scrape ability data
        scraped_data['abilities'] = await scraper.scrape_ability_data(report_code, fight_id, source_id)
        
        # Scrape action bar data if source_id is provided
        if source_id:
            scraped_data['action_bars'] = await scraper.scrape_action_bar_data(report_code, fight_id, source_id)
            scraped_data['gear'] = await scraper.scrape_player_gear_data(report_code, fight_id, source_id)
    
    return scraped_data
