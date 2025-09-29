#!/usr/bin/env python3
"""
Test script to scrape ability IDs using the discovered pattern.

Based on the user's discovery that ability data appears as:
<span id="talent-ability-183006-0" class="school-1" style="">Cephaliarch's Flail</span>
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


class ESOLogsAbilityScraper:
    """Enhanced scraper specifically for ability IDs using the discovered pattern."""
    
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
    
    def scrape_ability_ids(self, url: str) -> list:
        """
        Scrape ability IDs using the discovered pattern.
        
        Pattern: <span id="talent-ability-{ability_id}-{something}" class="school-X" style="">{ability_name}</span>
        
        Args:
            url: The URL to scrape
        
        Returns:
            List of dictionaries containing ability data
        """
        try:
            logger.info(f"Scraping ability IDs from: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            abilities = []
            
            # Look for spans with the talent-ability pattern
            ability_spans = soup.find_all('span', {'id': re.compile(r'^talent-ability-\d+-\d+$')})
            
            logger.info(f"Found {len(ability_spans)} ability spans")
            
            for span in ability_spans:
                span_id = span.get('id', '')
                ability_name = span.get_text(strip=True)  # Strip whitespace
                span_class = span.get('class', [])
                
                # Extract ability ID from the span ID
                # Pattern: talent-ability-{ability_id}-{something}
                match = re.match(r'^talent-ability-(\d+)-\d+$', span_id)
                if match:
                    ability_id = match.group(1)
                    
                    ability_data = {
                        'ability_id': ability_id,
                        'ability_name': ability_name,
                        'span_id': span_id,
                        'span_class': span_class,
                        'html': str(span)
                    }
                    
                    abilities.append(ability_data)
                    logger.info(f"Found ability: {ability_name} (ID: {ability_id})")
                else:
                    logger.warning(f"Could not parse ability ID from span ID: {span_id}")
            
            # Also look for other potential patterns
            other_patterns = [
                r'ability-(\d+)',  # ability-{id}
                r'talent-(\d+)',   # talent-{id}
                r'skill-(\d+)',    # skill-{id}
                r'spell-(\d+)',    # spell-{id}
            ]
            
            for pattern in other_patterns:
                elements = soup.find_all(attrs={'id': re.compile(pattern)})
                logger.info(f"Found {len(elements)} elements matching pattern: {pattern}")
                
                for element in elements:
                    element_id = element.get('id', '')
                    element_text = element.get_text(strip=True)
                    
                    match = re.search(pattern, element_id)
                    if match and element_text:
                        ability_id = match.group(1)
                        
                        ability_data = {
                            'ability_id': ability_id,
                            'ability_name': element_text,
                            'span_id': element_id,
                            'span_class': element.get('class', []),
                            'html': str(element),
                            'pattern': pattern
                        }
                        
                        abilities.append(ability_data)
                        logger.info(f"Found ability (pattern {pattern}): {element_text} (ID: {ability_id})")
            
            # Remove duplicates based on ability_id
            seen_ids = set()
            unique_abilities = []
            for ability in abilities:
                if ability['ability_id'] not in seen_ids:
                    unique_abilities.append(ability)
                    seen_ids.add(ability['ability_id'])
                else:
                    logger.debug(f"Duplicate ability ID found: {ability['ability_id']}")
            
            logger.info(f"Total unique abilities found: {len(unique_abilities)}")
            return unique_abilities
            
        except Exception as e:
            logger.error(f"Failed to scrape ability IDs from {url}: {e}")
            return []
    
    def scrape_fight_abilities(self, report_code: str, fight_id: int, source_id: int) -> dict:
        """
        Scrape abilities from multiple page types for a fight.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: The source/player ID
        
        Returns:
            Dictionary containing all scraped ability data
        """
        results = {
            'report_code': report_code,
            'fight_id': fight_id,
            'source_id': source_id,
            'timestamp': datetime.now().isoformat(),
            'pages': {},
            'all_abilities': {}
        }
        
        # Test different page types - focus on those most likely to have ability data
        data_types = ['casts', 'damage-done', 'healing', 'summary']
        
        for data_type in data_types:
            url = self.construct_fight_url(report_code, fight_id, source_id, data_type)
            logger.info(f"Scraping {data_type} page...")
            
            abilities = self.scrape_ability_ids(url)
            results['pages'][data_type] = {
                'url': url,
                'abilities': abilities,
                'count': len(abilities)
            }
            
            # Merge into all_abilities dict
            for ability in abilities:
                ability_id = ability['ability_id']
                if ability_id not in results['all_abilities']:
                    results['all_abilities'][ability_id] = ability
                    results['all_abilities'][ability_id]['found_on_pages'] = [data_type]
                else:
                    results['all_abilities'][ability_id]['found_on_pages'].append(data_type)
            
            # Add delay between requests to be respectful
            import time
            time.sleep(2)
        
        results['total_unique_abilities'] = len(results['all_abilities'])
        return results


async def test_ability_id_scraping():
    """Test scraping ability IDs using the discovered pattern."""
    
    logger.info("Testing ability ID scraping with discovered pattern")
    logger.info("=" * 80)
    
    # Test data from the provided URL
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    source_id = 1
    
    scraper = ESOLogsAbilityScraper()
    
    try:
        # Test scraping the specific URL
        url = f"https://www.esologs.com/reports/{report_code}?fight={fight_id}&type=summary&source={source_id}"
        logger.info(f"Testing URL: {url}")
        
        # Single page test
        single_page_abilities = scraper.scrape_ability_ids(url)
        
        logger.info(f"Single page results: {len(single_page_abilities)} abilities found")
        for ability in single_page_abilities:
            logger.info(f"  - {ability['ability_name']} (ID: {ability['ability_id']})")
        
        # Save single page result
        output_file = f"ability_ids_single_{report_code}_{fight_id}_{source_id}.json"
        with open(output_file, 'w') as f:
            json.dump(single_page_abilities, f, indent=2, default=str)
        
        logger.info(f"Single page results saved to: {output_file}")
        
        # Full fight data test
        logger.info("Scraping all page types for the fight...")
        full_results = scraper.scrape_fight_abilities(report_code, fight_id, source_id)
        
        # Save full results
        full_output_file = f"ability_ids_full_{report_code}_{fight_id}_{source_id}.json"
        with open(full_output_file, 'w') as f:
            json.dump(full_results, f, indent=2, default=str)
        
        logger.info(f"Full results saved to: {full_output_file}")
        
        # Print summary
        logger.info("=" * 80)
        logger.info("ABILITY SCRAPING SUMMARY:")
        logger.info("=" * 80)
        
        logger.info(f"Total unique abilities found: {full_results['total_unique_abilities']}")
        
        for page_type, data in full_results['pages'].items():
            logger.info(f"{page_type.upper()} PAGE: {data['count']} abilities")
            for ability in data['abilities']:
                logger.info(f"  - {ability['ability_name']} (ID: {ability['ability_id']})")
        
        logger.info("=" * 80)
        logger.info("ALL UNIQUE ABILITIES:")
        logger.info("=" * 80)
        
        for ability_id, ability_data in full_results['all_abilities'].items():
            logger.info(f"ID {ability_id}: {ability_data['ability_name']} (found on: {ability_data['found_on_pages']})")
        
        return full_results
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def test_specific_ability_pattern():
    """Test the specific ability pattern provided by the user."""
    
    logger.info("=" * 80)
    logger.info("TESTING SPECIFIC ABILITY PATTERN")
    logger.info("=" * 80)
    
    # The pattern from the user
    test_html = '''
    <span id="talent-ability-183006-0" class="school-1" style="">
                                                                                                     Cephaliarch's Flail                                                                                                     
    </span>
    '''
    
    soup = BeautifulSoup(test_html, 'html.parser')
    span = soup.find('span')
    
    if span:
        span_id = span.get('id', '')
        ability_name = span.get_text(strip=True)
        
        logger.info(f"Span ID: {span_id}")
        logger.info(f"Ability name: '{ability_name}'")
        
        # Test the regex pattern
        match = re.match(r'^talent-ability-(\d+)-\d+$', span_id)
        if match:
            ability_id = match.group(1)
            logger.info(f"Extracted ability ID: {ability_id}")
            logger.info("✅ Pattern matching works correctly!")
        else:
            logger.error("❌ Pattern matching failed!")
    
    return True


async def main():
    """Run all ability ID scraping tests."""
    
    logger.info("Starting ESO Logs ability ID scraping tests")
    logger.info("=" * 80)
    
    # Test 1: Test the specific pattern
    await test_specific_ability_pattern()
    
    # Test 2: Full ability ID scraping
    results = await test_ability_id_scraping()
    
    logger.info("=" * 80)
    logger.info("All tests completed!")
    
    if results:
        logger.info(f"Successfully found {results['total_unique_abilities']} unique ability IDs")


if __name__ == "__main__":
    asyncio.run(main())
