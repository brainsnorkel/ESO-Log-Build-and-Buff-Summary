#!/usr/bin/env python3
"""
Test script to scrape ability IDs using requests and BeautifulSoup (no browser required).

This script tests scraping ability data from ESO Logs using a simpler approach
that doesn't require Chrome or Selenium.
"""

import asyncio
import json
import logging
import re
import sys
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ESOLogsSimpleScraper:
    """Simple web scraper using requests and BeautifulSoup."""
    
    def __init__(self):
        """Initialize the scraper."""
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
    
    def construct_fight_url(self, report_code: str, fight_id: int, source_id: int = None, 
                          data_type: str = "summary") -> str:
        """Construct ESO Logs web URL for a specific fight and source."""
        base_url = f"https://www.esologs.com/reports/{report_code}?fight={fight_id}&type={data_type}"
        if source_id:
            base_url += f"&source={source_id}"
        return base_url
    
    def scrape_page(self, url: str) -> dict:
        """
        Scrape a single ESO Logs page.
        
        Args:
            url: The URL to scrape
        
        Returns:
            Dictionary containing scraped data
        """
        try:
            logger.info(f"Scraping URL: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            scraped_data = {
                'url': url,
                'title': soup.title.string if soup.title else '',
                'status_code': response.status_code,
                'content_length': len(response.content),
                'abilities': [],
                'scripts': [],
                'data_attributes': [],
                'ability_related_elements': [],
                'page_source_preview': response.text[:2000]  # First 2000 chars
            }
            
            # Extract ability-related elements
            ability_selectors = [
                '[data-ability-id]',
                '[class*="ability"]',
                '[id*="ability"]',
                '[data-ability]',
                '.ability-name',
                '.cast-ability',
                '[title*="ability"]'
            ]
            
            for selector in ability_selectors:
                elements = soup.select(selector)
                for element in elements:
                    ability_data = {
                        'selector': selector,
                        'text': element.get_text(strip=True),
                        'html': str(element)[:300],
                        'attributes': dict(element.attrs) if element.attrs else {}
                    }
                    scraped_data['ability_related_elements'].append(ability_data)
            
            # Extract script tags that might contain ability data
            scripts = soup.find_all('script')
            for i, script in enumerate(scripts):
                if script.string:
                    script_content = script.string.strip()
                    if len(script_content) > 100:
                        # Look for ability-related data in scripts
                        if any(keyword in script_content.lower() for keyword in 
                               ['ability', 'cast', 'damage', 'fight', 'player', 'source']):
                            scraped_data['scripts'].append({
                                'index': i,
                                'preview': script_content[:500],
                                'full_length': len(script_content)
                            })
            
            # Extract elements with data attributes
            data_elements = soup.find_all(attrs={'data-ability-id': True})
            for element in data_elements:
                scraped_data['data_attributes'].append({
                    'ability_id': element.get('data-ability-id'),
                    'text': element.get_text(strip=True),
                    'attributes': dict(element.attrs)
                })
            
            # Look for JSON data in script tags
            json_data = self._extract_json_from_scripts(soup)
            scraped_data['json_data'] = json_data
            
            logger.info(f"Found {len(scraped_data['ability_related_elements'])} ability elements")
            logger.info(f"Found {len(scraped_data['scripts'])} relevant scripts")
            logger.info(f"Found {len(scraped_data['data_attributes'])} data attributes")
            
            return scraped_data
            
        except Exception as e:
            logger.error(f"Failed to scrape page {url}: {e}")
            return {'error': str(e), 'url': url}
    
    def _extract_json_from_scripts(self, soup: BeautifulSoup) -> list:
        """Extract JSON data from script tags."""
        json_data = []
        
        scripts = soup.find_all('script')
        for i, script in enumerate(scripts):
            if script.string:
                script_content = script.string.strip()
                
                # Look for JSON objects in the script
                json_patterns = [
                    r'window\.(\w+)\s*=\s*({.*?});',
                    r'var\s+(\w+)\s*=\s*({.*?});',
                    r'let\s+(\w+)\s*=\s*({.*?});',
                    r'const\s+(\w+)\s*=\s*({.*?});',
                ]
                
                for pattern in json_patterns:
                    matches = re.findall(pattern, script_content, re.DOTALL)
                    for var_name, json_str in matches:
                        try:
                            # Clean up the JSON string
                            json_str = json_str.strip()
                            if json_str.startswith('{') and json_str.endswith('}'):
                                parsed = json.loads(json_str)
                                json_data.append({
                                    'variable_name': var_name,
                                    'data': parsed,
                                    'script_index': i
                                })
                                logger.debug(f"Found JSON data in variable: {var_name}")
                        except json.JSONDecodeError:
                            continue
        
        return json_data
    
    def scrape_fight_data(self, report_code: str, fight_id: int, source_id: int) -> dict:
        """
        Scrape data from multiple pages for a fight.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: The source/player ID
        
        Returns:
            Dictionary containing all scraped data
        """
        results = {
            'report_code': report_code,
            'fight_id': fight_id,
            'source_id': source_id,
            'timestamp': datetime.now().isoformat(),
            'pages': {}
        }
        
        # Test different page types
        data_types = ['summary', 'casts', 'damage-done', 'healing', 'buffs', 'debuffs']
        
        for data_type in data_types:
            url = self.construct_fight_url(report_code, fight_id, source_id, data_type)
            logger.info(f"Scraping {data_type} page...")
            
            page_data = self.scrape_page(url)
            results['pages'][data_type] = page_data
            
            # Add delay between requests to be respectful
            import time
            time.sleep(2)
        
        return results


async def test_requests_scraping():
    """Test scraping using requests and BeautifulSoup."""
    
    logger.info("Testing ESO Logs scraping with requests and BeautifulSoup")
    logger.info("=" * 80)
    
    # Test data from the provided URL
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    source_id = 1
    
    scraper = ESOLogsSimpleScraper()
    
    try:
        # Test scraping the specific URL
        url = f"https://www.esologs.com/reports/{report_code}?fight={fight_id}&type=summary&source={source_id}"
        logger.info(f"Testing URL: {url}")
        
        # Single page test
        single_page_result = scraper.scrape_page(url)
        
        # Save single page result
        output_file = f"single_page_scraping_{report_code}_{fight_id}_{source_id}.json"
        with open(output_file, 'w') as f:
            json.dump(single_page_result, f, indent=2, default=str)
        
        logger.info(f"Single page results saved to: {output_file}")
        
        # Full fight data test
        logger.info("Scraping all page types for the fight...")
        full_results = scraper.scrape_fight_data(report_code, fight_id, source_id)
        
        # Save full results
        full_output_file = f"full_scraping_{report_code}_{fight_id}_{source_id}.json"
        with open(full_output_file, 'w') as f:
            json.dump(full_results, f, indent=2, default=str)
        
        logger.info(f"Full results saved to: {full_output_file}")
        
        # Print summary
        logger.info("=" * 80)
        logger.info("SCRAPING SUMMARY:")
        logger.info("=" * 80)
        
        for page_type, data in full_results['pages'].items():
            if 'error' not in data:
                logger.info(f"{page_type.upper()} PAGE:")
                logger.info(f"  - Title: {data.get('title', 'N/A')}")
                logger.info(f"  - Ability elements: {len(data.get('ability_related_elements', []))}")
                logger.info(f"  - Data attributes: {len(data.get('data_attributes', []))}")
                logger.info(f"  - Relevant scripts: {len(data.get('scripts', []))}")
                logger.info(f"  - JSON data found: {len(data.get('json_data', []))}")
                
                # Show any ability IDs found
                ability_ids = [item.get('ability_id') for item in data.get('data_attributes', []) 
                              if item.get('ability_id')]
                if ability_ids:
                    logger.info(f"  - Ability IDs found: {ability_ids}")
                
                # Show any JSON variables with ability data
                ability_vars = [var['variable_name'] for var in data.get('json_data', [])
                               if any(keyword in str(var['data']).lower() 
                                     for keyword in ['ability', 'cast', 'damage'])]
                if ability_vars:
                    logger.info(f"  - Ability-related JSON variables: {ability_vars}")
            else:
                logger.info(f"{page_type.upper()} PAGE: ERROR - {data['error']}")
        
        return full_results
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def analyze_specific_url():
    """Analyze the specific URL provided by the user."""
    
    logger.info("=" * 80)
    logger.info("ANALYZING SPECIFIC URL")
    logger.info("=" * 80)
    
    url = "https://www.esologs.com/reports/7KAWyZwPCkaHfc8j?fight=17&type=summary&source=1"
    
    scraper = ESOLogsSimpleScraper()
    
    try:
        result = scraper.scrape_page(url)
        
        # Save detailed analysis
        analysis_file = f"url_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(analysis_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info(f"URL analysis saved to: {analysis_file}")
        
        # Print key findings
        logger.info("KEY FINDINGS:")
        logger.info(f"Page title: {result.get('title', 'N/A')}")
        logger.info(f"Content length: {result.get('content_length', 0)} bytes")
        
        if result.get('data_attributes'):
            logger.info("Ability IDs found:")
            for attr in result['data_attributes']:
                logger.info(f"  - {attr['ability_id']}: {attr['text']}")
        
        if result.get('json_data'):
            logger.info("JSON data variables found:")
            for json_item in result['json_data']:
                logger.info(f"  - {json_item['variable_name']}: {type(json_item['data'])}")
        
        # Look for specific patterns in the page source
        page_source = result.get('page_source_preview', '')
        
        # Check for common ESO Logs patterns
        patterns_to_check = [
            r'ability[Ii]d["\']?\s*:\s*["\']?(\d+)',
            r'data-ability-id["\']?\s*=\s*["\']?(\d+)',
            r'source[Ii]d["\']?\s*:\s*["\']?(\d+)',
            r'fight[Ii]d["\']?\s*:\s*["\']?(\d+)',
            r'report[Ii]d["\']?\s*:\s*["\']?([a-zA-Z0-9]+)',
        ]
        
        logger.info("PATTERN ANALYSIS:")
        for pattern in patterns_to_check:
            matches = re.findall(pattern, page_source)
            if matches:
                logger.info(f"  Pattern '{pattern}' found: {matches}")
        
        return result
        
    except Exception as e:
        logger.error(f"URL analysis failed: {e}")
        return None


async def main():
    """Run all scraping tests."""
    
    logger.info("Starting ESO Logs web scraping tests with requests")
    logger.info("=" * 80)
    
    # Test 1: Analyze specific URL
    await analyze_specific_url()
    
    # Test 2: Full scraping test
    results = await test_requests_scraping()
    
    logger.info("=" * 80)
    logger.info("All tests completed!")
    
    if results:
        total_abilities = sum(len(page.get('data_attributes', [])) 
                            for page in results['pages'].values() 
                            if 'error' not in page)
        logger.info(f"Total ability IDs found across all pages: {total_abilities}")


if __name__ == "__main__":
    asyncio.run(main())
