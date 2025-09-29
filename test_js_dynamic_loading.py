#!/usr/bin/env python3
"""
Test script to check if ability data is loaded dynamically via JavaScript.

This script uses Selenium to wait for JavaScript to load content and then search
for the talent-ability pattern.
"""

import asyncio
import json
import logging
import re
import sys
import os
from datetime import datetime

# Try to import Selenium components
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium not available - will use requests fallback")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ESOJSAbilitySearcher:
    """Searcher that waits for JavaScript to load ability data."""
    
    def __init__(self, headless: bool = True):
        """Initialize the searcher."""
        self.headless = headless
        self.driver = None
        self.selenium_available = SELENIUM_AVAILABLE
        
        if not self.selenium_available:
            logger.warning("Selenium not available - using requests fallback")
            import requests
            from bs4 import BeautifulSoup
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            })
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self.selenium_available:
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
        if not self.selenium_available:
            return
            
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Try to use webdriver-manager
            try:
                self.driver = webdriver.Chrome(
                    service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
                logger.info("WebDriver initialized successfully with webdriver-manager")
            except Exception as e:
                logger.warning(f"WebDriver with webdriver-manager failed: {e}")
                # Fallback: try system Chrome
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("WebDriver initialized successfully with system Chrome")
                
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            self.selenium_available = False
    
    async def search_with_selenium(self, url: str) -> dict:
        """Search for ability patterns using Selenium (waits for JS to load)."""
        if not self.selenium_available or not self.driver:
            return {'error': 'Selenium not available'}
        
        try:
            logger.info(f"Loading page with Selenium: {url}")
            
            # Load the page
            self.driver.get(url)
            
            # Wait for the page to load
            logger.info("Waiting for page to load...")
            await asyncio.sleep(3)
            
            # Wait for potential dynamic content to load
            logger.info("Waiting for dynamic content to load...")
            
            # Try to wait for common elements that might indicate the page is ready
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                logger.warning("Timeout waiting for body element")
            
            # Wait additional time for JavaScript to execute
            await asyncio.sleep(5)
            
            # Search for ability patterns
            results = self._search_ability_patterns_selenium()
            
            # Also try to trigger any lazy loading by scrolling
            logger.info("Scrolling to trigger lazy loading...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            await asyncio.sleep(2)
            
            # Search again after scrolling
            results_after_scroll = self._search_ability_patterns_selenium()
            
            # Combine results
            combined_results = {
                'initial_search': results,
                'after_scroll_search': results_after_scroll,
                'total_abilities': len(results.get('abilities', [])) + len(results_after_scroll.get('abilities', []))
            }
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Selenium search failed: {e}")
            return {'error': str(e)}
    
    def _search_ability_patterns_selenium(self) -> dict:
        """Search for ability patterns in the current DOM."""
        results = {
            'abilities': [],
            'patterns_found': {}
        }
        
        # Define patterns to search for
        patterns = {
            'talent-ability': r'^talent-ability-\d+-\d+$',
            'ability-id': r'ability-\d+',
            'talent-id': r'talent-\d+',
            'skill-id': r'skill-\d+',
            'spell-id': r'spell-\d+',
        }
        
        for pattern_name, pattern in patterns.items():
            try:
                # Find elements with IDs matching the pattern
                elements = self.driver.find_elements(By.CSS_SELECTOR, f"[id*='{pattern_name.split('-')[0]}']")
                
                pattern_results = []
                for element in elements:
                    element_id = element.get_attribute('id')
                    if re.search(pattern, element_id):
                        element_text = element.text.strip()
                        element_class = element.get_attribute('class')
                        
                        element_data = {
                            'id': element_id,
                            'text': element_text,
                            'class': element_class,
                            'tag': element.tag_name
                        }
                        
                        pattern_results.append(element_data)
                        
                        # If it's a talent-ability pattern, add to abilities list
                        if pattern_name == 'talent-ability' and element_text:
                            match = re.match(r'^talent-ability-(\d+)-\d+$', element_id)
                            if match:
                                ability_id = match.group(1)
                                results['abilities'].append({
                                    'ability_id': ability_id,
                                    'ability_name': element_text,
                                    'span_id': element_id,
                                    'span_class': element_class
                                })
                                logger.info(f"Found ability: {element_text} (ID: {ability_id})")
                
                results['patterns_found'][pattern_name] = {
                    'count': len(pattern_results),
                    'elements': pattern_results
                }
                
                if pattern_results:
                    logger.info(f"Pattern '{pattern_name}': {len(pattern_results)} matches")
            
            except Exception as e:
                logger.warning(f"Error searching pattern '{pattern_name}': {e}")
        
        return results
    
    def search_with_requests(self, url: str) -> dict:
        """Fallback search using requests (no JavaScript execution)."""
        try:
            logger.info(f"Fallback search with requests: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = {
                'method': 'requests_fallback',
                'abilities': [],
                'patterns_found': {}
            }
            
            # Search for the talent-ability pattern
            ability_spans = soup.find_all('span', {'id': re.compile(r'^talent-ability-\d+-\d+$')})
            
            for span in ability_spans:
                span_id = span.get('id', '')
                ability_name = span.get_text(strip=True)
                
                match = re.match(r'^talent-ability-(\d+)-\d+$', span_id)
                if match and ability_name:
                    ability_id = match.group(1)
                    results['abilities'].append({
                        'ability_id': ability_id,
                        'ability_name': ability_name,
                        'span_id': span_id,
                        'span_class': span.get('class', [])
                    })
            
            results['patterns_found']['talent-ability'] = {
                'count': len(ability_spans),
                'elements': [{'id': span.get('id'), 'text': span.get_text(strip=True)} for span in ability_spans]
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Requests fallback failed: {e}")
            return {'error': str(e)}
    
    async def search_abilities(self, url: str) -> dict:
        """Search for abilities using the best available method."""
        if self.selenium_available and self.driver:
            return self.search_with_selenium(url)
        else:
            return self.search_with_requests(url)


async def test_js_dynamic_loading():
    """Test if ability data is loaded dynamically via JavaScript."""
    
    logger.info("Testing JavaScript dynamic loading of ability data")
    logger.info("=" * 80)
    
    # Test URLs
    urls_to_test = [
        "https://www.esologs.com/reports/7KAWyZwPCkaHfc8j?fight=17&type=summary&source=1",
        "https://www.esologs.com/reports/7KAWyZwPCkaHfc8j?fight=17&type=casts&source=1",
        "https://www.esologs.com/reports/7KAWyZwPCkaHfc8j?fight=17&type=damage-done&source=1",
    ]
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'urls_tested': [],
        'summary': {}
    }
    
    async with ESOJSAbilitySearcher(headless=True) as searcher:
        for url in urls_to_test:
            logger.info(f"Testing URL: {url}")
            
            url_results = await searcher.search_abilities(url)
            
            results['urls_tested'].append({
                'url': url,
                'results': url_results
            })
            
            # Log results
            if 'error' in url_results:
                logger.error(f"Error testing {url}: {url_results['error']}")
            else:
                abilities_found = url_results.get('total_abilities', len(url_results.get('abilities', [])))
                logger.info(f"Found {abilities_found} abilities on {url}")
                
                if url_results.get('abilities'):
                    for ability in url_results['abilities']:
                        logger.info(f"  - {ability['ability_name']} (ID: {ability['ability_id']})")
    
    # Save results
    output_file = f"js_dynamic_loading_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to: {output_file}")
    
    # Summary
    total_abilities = sum(
        len(url_data['results'].get('abilities', [])) 
        for url_data in results['urls_tested']
        if 'error' not in url_data['results']
    )
    
    logger.info("=" * 80)
    logger.info(f"SUMMARY: Found {total_abilities} total abilities across all URLs")
    
    if total_abilities > 0:
        logger.info("✅ SUCCESS: Ability data IS loaded dynamically via JavaScript!")
        logger.info("This confirms that the talent-ability pattern appears after JS execution")
    else:
        logger.info("❌ No abilities found even with JavaScript execution")
        logger.info("This could mean:")
        logger.info("  - The pattern appears under different conditions")
        logger.info("  - User interaction is required to load the data")
        logger.info("  - The data is loaded from a different source")
    
    return results


async def main():
    """Run the JavaScript dynamic loading test."""
    
    logger.info("Starting JavaScript dynamic loading test for ability data")
    logger.info("=" * 80)
    
    if not SELENIUM_AVAILABLE:
        logger.warning("Selenium not available - will use requests fallback")
        logger.warning("This means we can't test JavaScript dynamic loading")
    
    results = await test_js_dynamic_loading()
    
    logger.info("=" * 80)
    logger.info("JavaScript dynamic loading test completed!")


if __name__ == "__main__":
    asyncio.run(main())
