#!/usr/bin/env python3
"""
Test script to explore headless web scraping alternatives that don't require external Chrome.

This script tests various approaches:
1. Headless Chrome (internal driver)
2. Firefox with GeckoDriver
3. Requests + BeautifulSoup (no browser)
4. Playwright (modern alternative)
5. HTTP requests with session handling
"""

import asyncio
import json
import logging
import re
import sys
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HeadlessAlternatives:
    """Test various headless web scraping alternatives."""
    
    def __init__(self):
        """Initialize the headless alternatives tester."""
        self.test_url = "https://www.esologs.com/reports/7KAWyZwPCkaHfc8j?fight=17&type=casts&source=1"
    
    async def test_headless_chrome(self) -> Dict:
        """Test headless Chrome (internal driver, no GUI)."""
        logger.info("Testing Headless Chrome...")
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
            
            # Configure headless Chrome
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # No GUI
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Try to use webdriver-manager
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("✅ Headless Chrome initialized with webdriver-manager")
            except Exception as e:
                logger.warning(f"WebDriver with webdriver-manager failed: {e}")
                # Fallback: try system Chrome
                driver = webdriver.Chrome(options=chrome_options)
                logger.info("✅ Headless Chrome initialized with system Chrome")
            
            # Test the page
            driver.get(self.test_url)
            await asyncio.sleep(5)
            
            # Wait for body to be present
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for ability elements
            ability_spans = driver.find_elements(By.CSS_SELECTOR, "span[id^='ability-']")
            logger.info(f"Headless Chrome found {len(ability_spans)} ability spans")
            
            # Extract some abilities
            abilities = []
            for span in ability_spans[:5]:  # First 5
                span_id = span.get_attribute('id')
                span_text = span.text.strip()
                if span_text:
                    abilities.append({
                        'id': span_id,
                        'name': span_text
                    })
            
            driver.quit()
            
            return {
                'method': 'headless_chrome',
                'success': True,
                'abilities_found': len(ability_spans),
                'sample_abilities': abilities,
                'notes': 'Fully headless - no GUI required'
            }
            
        except Exception as e:
            logger.error(f"Headless Chrome failed: {e}")
            return {
                'method': 'headless_chrome',
                'success': False,
                'error': str(e)
            }
    
    async def test_firefox_geckodriver(self) -> Dict:
        """Test Firefox with GeckoDriver (alternative browser)."""
        logger.info("Testing Firefox with GeckoDriver...")
        
        try:
            from selenium import webdriver
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            from selenium.webdriver.firefox.service import Service as FirefoxService
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.firefox import GeckoDriverManager
            
            # Configure headless Firefox
            firefox_options = FirefoxOptions()
            firefox_options.add_argument('--headless')  # No GUI
            firefox_options.add_argument('--width=1920')
            firefox_options.add_argument('--height=1080')
            
            try:
                service = FirefoxService(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=service, options=firefox_options)
                logger.info("✅ Firefox initialized with GeckoDriver")
            except Exception as e:
                logger.warning(f"Firefox with GeckoDriver failed: {e}")
                # Fallback: try system Firefox
                driver = webdriver.Firefox(options=firefox_options)
                logger.info("✅ Firefox initialized with system Firefox")
            
            # Test the page
            driver.get(self.test_url)
            await asyncio.sleep(5)
            
            # Wait for body to be present
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for ability elements
            ability_spans = driver.find_elements(By.CSS_SELECTOR, "span[id^='ability-']")
            logger.info(f"Firefox found {len(ability_spans)} ability spans")
            
            # Extract some abilities
            abilities = []
            for span in ability_spans[:5]:  # First 5
                span_id = span.get_attribute('id')
                span_text = span.text.strip()
                if span_text:
                    abilities.append({
                        'id': span_id,
                        'name': span_text
                    })
            
            driver.quit()
            
            return {
                'method': 'firefox_geckodriver',
                'success': True,
                'abilities_found': len(ability_spans),
                'sample_abilities': abilities,
                'notes': 'Alternative browser - no Chrome required'
            }
            
        except Exception as e:
            logger.error(f"Firefox with GeckoDriver failed: {e}")
            return {
                'method': 'firefox_geckodriver',
                'success': False,
                'error': str(e)
            }
    
    async def test_playwright(self) -> Dict:
        """Test Playwright (modern headless browser automation)."""
        logger.info("Testing Playwright...")
        
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                # Launch headless browser
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                logger.info("✅ Playwright browser launched")
                
                # Test the page
                await page.goto(self.test_url)
                await asyncio.sleep(5)
                
                # Wait for content to load
                await page.wait_for_selector('body')
                
                # Look for ability elements
                ability_spans = await page.query_selector_all("span[id^='ability-']")
                logger.info(f"Playwright found {len(ability_spans)} ability spans")
                
                # Extract some abilities
                abilities = []
                for i, span in enumerate(ability_spans[:5]):  # First 5
                    span_id = await span.get_attribute('id')
                    span_text = await span.text_content()
                    if span_text and span_text.strip():
                        abilities.append({
                            'id': span_id,
                            'name': span_text.strip()
                        })
                
                await browser.close()
                
                return {
                    'method': 'playwright',
                    'success': True,
                    'abilities_found': len(ability_spans),
                    'sample_abilities': abilities,
                    'notes': 'Modern headless automation - no external browser'
                }
                
        except ImportError:
            logger.warning("Playwright not installed. Install with: pip install playwright")
            return {
                'method': 'playwright',
                'success': False,
                'error': 'Playwright not installed'
            }
        except Exception as e:
            logger.error(f"Playwright failed: {e}")
            return {
                'method': 'playwright',
                'success': False,
                'error': str(e)
            }
    
    def test_requests_beautifulsoup(self) -> Dict:
        """Test requests + BeautifulSoup (no browser at all)."""
        logger.info("Testing Requests + BeautifulSoup...")
        
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # Create session with headers
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            })
            
            # Make request
            response = session.get(self.test_url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for ability elements
            ability_spans = soup.find_all('span', {'id': re.compile(r'^ability-')})
            logger.info(f"Requests + BeautifulSoup found {len(ability_spans)} ability spans")
            
            # Extract some abilities
            abilities = []
            for span in ability_spans[:5]:  # First 5
                span_id = span.get('id')
                span_text = span.get_text(strip=True)
                if span_text:
                    abilities.append({
                        'id': span_id,
                        'name': span_text
                    })
            
            return {
                'method': 'requests_beautifulsoup',
                'success': True,
                'abilities_found': len(ability_spans),
                'sample_abilities': abilities,
                'notes': 'No browser required - static HTML only',
                'limitation': 'Cannot execute JavaScript - may miss dynamic content'
            }
            
        except Exception as e:
            logger.error(f"Requests + BeautifulSoup failed: {e}")
            return {
                'method': 'requests_beautifulsoup',
                'success': False,
                'error': str(e)
            }
    
    async def test_httpx_with_session(self) -> Dict:
        """Test httpx with session handling (async alternative to requests)."""
        logger.info("Testing httpx with session handling...")
        
        try:
            import httpx
            from bs4 import BeautifulSoup
            
            # Create async client with headers
            async with httpx.AsyncClient(
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                },
                timeout=30.0
            ) as client:
                
                # Make request
                response = await client.get(self.test_url)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for ability elements
                ability_spans = soup.find_all('span', {'id': re.compile(r'^ability-')})
                logger.info(f"httpx found {len(ability_spans)} ability spans")
                
                # Extract some abilities
                abilities = []
                for span in ability_spans[:5]:  # First 5
                    span_id = span.get('id')
                    span_text = span.get_text(strip=True)
                    if span_text:
                        abilities.append({
                            'id': span_id,
                            'name': span_text
                        })
                
                return {
                    'method': 'httpx_session',
                    'success': True,
                    'abilities_found': len(ability_spans),
                    'sample_abilities': abilities,
                    'notes': 'Async HTTP client - no browser required',
                    'limitation': 'Cannot execute JavaScript - may miss dynamic content'
                }
                
        except Exception as e:
            logger.error(f"httpx failed: {e}")
            return {
                'method': 'httpx_session',
                'success': False,
                'error': str(e)
            }
    
    async def run_all_tests(self) -> Dict:
        """Run all headless alternatives tests."""
        logger.info("Testing all headless alternatives...")
        logger.info("=" * 80)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'test_url': self.test_url,
            'methods_tested': []
        }
        
        # Test 1: Headless Chrome
        chrome_result = await self.test_headless_chrome()
        results['methods_tested'].append(chrome_result)
        
        # Test 2: Firefox with GeckoDriver
        firefox_result = await self.test_firefox_geckodriver()
        results['methods_tested'].append(firefox_result)
        
        # Test 3: Playwright
        playwright_result = await self.test_playwright()
        results['methods_tested'].append(playwright_result)
        
        # Test 4: Requests + BeautifulSoup (sync)
        requests_result = self.test_requests_beautifulsoup()
        results['methods_tested'].append(requests_result)
        
        # Test 5: httpx with session (async)
        httpx_result = await self.test_httpx_with_session()
        results['methods_tested'].append(httpx_result)
        
        return results
    
    def print_results(self, results: Dict):
        """Print the test results."""
        logger.info("=" * 80)
        logger.info("HEADLESS ALTERNATIVES TEST RESULTS:")
        logger.info("=" * 80)
        
        for method in results['methods_tested']:
            method_name = method['method']
            success = method['success']
            
            logger.info(f"\n{method_name.upper()}:")
            logger.info("-" * 40)
            
            if success:
                logger.info(f"✅ SUCCESS: {method['abilities_found']} abilities found")
                logger.info(f"📝 Notes: {method['notes']}")
                
                if method.get('limitation'):
                    logger.info(f"⚠️ Limitation: {method['limitation']}")
                
                if method.get('sample_abilities'):
                    logger.info("🎯 Sample abilities:")
                    for ability in method['sample_abilities']:
                        logger.info(f"  - {ability['name']} (ID: {ability['id']})")
            else:
                logger.info(f"❌ FAILED: {method['error']}")
        
        # Summary
        successful_methods = [m for m in results['methods_tested'] if m['success']]
        logger.info(f"\n📊 SUMMARY: {len(successful_methods)}/{len(results['methods_tested'])} methods successful")
        
        logger.info("\n💡 RECOMMENDATIONS:")
        logger.info("-" * 40)
        
        for method in successful_methods:
            if 'headless' in method['method']:
                logger.info(f"✅ {method['method']}: Best for dynamic content with JavaScript")
            elif 'requests' in method['method'] or 'httpx' in method['method']:
                logger.info(f"⚠️ {method['method']}: Fast but limited to static HTML")
            elif 'playwright' in method['method']:
                logger.info(f"🚀 {method['method']}: Modern, fast, and reliable")


async def main():
    """Run all headless alternatives tests."""
    
    logger.info("Starting Headless Alternatives Tests")
    logger.info("=" * 80)
    
    tester = HeadlessAlternatives()
    
    try:
        # Run all tests
        results = await tester.run_all_tests()
        
        # Save results
        output_file = f"headless_alternatives_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {output_file}")
        
        # Print results
        tester.print_results(results)
        
        return results
        
    except Exception as e:
        logger.error(f"Headless alternatives test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


if __name__ == "__main__":
    asyncio.run(main())
