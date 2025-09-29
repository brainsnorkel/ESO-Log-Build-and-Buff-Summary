#!/usr/bin/env python3
"""
Comprehensive test to find where the talent-ability pattern appears on ESO Logs.

This script searches for the ability pattern across different pages and contexts.
"""

import asyncio
import json
import logging
import re
import sys
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ESOLogsComprehensiveSearcher:
    """Comprehensive searcher for ability patterns across ESO Logs."""
    
    def __init__(self):
        """Initialize the searcher."""
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
    
    def search_all_patterns(self, url: str) -> dict:
        """
        Search for all possible ability-related patterns in a page.
        
        Args:
            url: The URL to search
        
        Returns:
            Dictionary containing all found patterns
        """
        try:
            logger.info(f"Comprehensive search on: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = {
                'url': url,
                'title': soup.title.string if soup.title else '',
                'patterns_found': {}
            }
            
            # Define all patterns to search for
            patterns = {
                'talent-ability-exact': r'^talent-ability-\d+-\d+$',
                'talent-ability-partial': r'talent-ability-\d+',
                'ability-id-exact': r'^ability-\d+$',
                'ability-id-partial': r'ability-\d+',
                'talent-id-exact': r'^talent-\d+$',
                'talent-id-partial': r'talent-\d+',
                'skill-id-exact': r'^skill-\d+$',
                'skill-id-partial': r'skill-\d+',
                'spell-id-exact': r'^spell-\d+$',
                'spell-id-partial': r'spell-\d+',
                'any-number-id': r'\d{5,}',  # IDs that are 5+ digits (typical for game IDs)
            }
            
            # Search for each pattern
            for pattern_name, pattern in patterns.items():
                elements = soup.find_all(attrs={'id': re.compile(pattern)})
                
                pattern_results = []
                for element in elements:
                    element_data = {
                        'id': element.get('id', ''),
                        'text': element.get_text(strip=True),
                        'class': element.get('class', []),
                        'tag': element.name,
                        'html': str(element)[:200]  # First 200 chars
                    }
                    pattern_results.append(element_data)
                
                results['patterns_found'][pattern_name] = {
                    'count': len(pattern_results),
                    'elements': pattern_results
                }
                
                if pattern_results:
                    logger.info(f"Pattern '{pattern_name}': {len(pattern_results)} matches")
                    for elem in pattern_results[:3]:  # Show first 3
                        logger.info(f"  - {elem['id']}: '{elem['text']}'")
            
            # Also search in the raw HTML for any mentions of the pattern
            html_content = response.text
            html_patterns = {
                'talent-ability-in-html': r'talent-ability-\d+-\d+',
                'ability-id-in-html': r'ability-\d+',
                'game-id-in-html': r'"id":\s*(\d{5,})',
                'ability-name-in-html': r'"name":\s*"([^"]+)"',
            }
            
            html_results = {}
            for pattern_name, pattern in html_patterns.items():
                matches = re.findall(pattern, html_content)
                if matches:
                    html_results[pattern_name] = list(set(matches))  # Remove duplicates
                    logger.info(f"HTML pattern '{pattern_name}': {len(html_results[pattern_name])} matches")
            
            results['html_patterns'] = html_results
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search patterns on {url}: {e}")
            return {'error': str(e), 'url': url}
    
    def search_multiple_pages(self, report_code: str, fight_id: int, source_id: int) -> dict:
        """
        Search multiple page types for ability patterns.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: The source/player ID
        
        Returns:
            Dictionary containing search results from all pages
        """
        results = {
            'report_code': report_code,
            'fight_id': fight_id,
            'source_id': source_id,
            'timestamp': datetime.now().isoformat(),
            'pages': {}
        }
        
        # Try different page types and contexts
        page_configs = [
            # Standard pages
            {'type': 'summary', 'source': source_id},
            {'type': 'casts', 'source': source_id},
            {'type': 'damage-done', 'source': source_id},
            {'type': 'healing', 'source': source_id},
            {'type': 'buffs', 'source': source_id},
            {'type': 'debuffs', 'source': source_id},
            
            # Without source filter (all players)
            {'type': 'summary', 'source': None},
            {'type': 'casts', 'source': None},
            {'type': 'damage-done', 'source': None},
            
            # Different contexts
            {'type': 'events', 'source': source_id},
            {'type': 'timelines', 'source': source_id},
        ]
        
        for config in page_configs:
            # Construct URL
            base_url = f"https://www.esologs.com/reports/{report_code}?fight={fight_id}&type={config['type']}"
            if config['source']:
                base_url += f"&source={config['source']}"
            
            page_key = f"{config['type']}_source_{config['source'] or 'all'}"
            
            logger.info(f"Searching page: {page_key}")
            
            page_results = self.search_all_patterns(base_url)
            results['pages'][page_key] = page_results
            
            # Add delay between requests
            import time
            time.sleep(1)
        
        return results


async def test_comprehensive_search():
    """Test comprehensive pattern searching."""
    
    logger.info("Starting comprehensive ability pattern search")
    logger.info("=" * 80)
    
    # Test data
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    source_id = 1
    
    searcher = ESOLogsComprehensiveSearcher()
    
    try:
        # Comprehensive search across multiple pages
        results = searcher.search_multiple_pages(report_code, fight_id, source_id)
        
        # Save results
        output_file = f"comprehensive_search_{report_code}_{fight_id}_{source_id}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Comprehensive search results saved to: {output_file}")
        
        # Print summary
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE SEARCH SUMMARY:")
        logger.info("=" * 80)
        
        total_patterns_found = 0
        pages_with_patterns = 0
        
        for page_key, page_data in results['pages'].items():
            if 'error' not in page_data:
                page_patterns = page_data.get('patterns_found', {})
                page_total = sum(pattern_data['count'] for pattern_data in page_patterns.values())
                
                if page_total > 0:
                    pages_with_patterns += 1
                    total_patterns_found += page_total
                    
                    logger.info(f"{page_key.upper()}: {page_total} total patterns found")
                    
                    # Show which patterns were found
                    for pattern_name, pattern_data in page_patterns.items():
                        if pattern_data['count'] > 0:
                            logger.info(f"  - {pattern_name}: {pattern_data['count']} matches")
                            # Show examples
                            for elem in pattern_data['elements'][:2]:
                                logger.info(f"    Example: {elem['id']} -> '{elem['text']}'")
        
        logger.info("=" * 80)
        logger.info(f"SUMMARY: Found {total_patterns_found} total patterns across {pages_with_patterns} pages")
        
        # Look for the specific talent-ability pattern
        talent_ability_found = False
        for page_key, page_data in results['pages'].items():
            if 'error' not in page_data:
                patterns = page_data.get('patterns_found', {})
                if patterns.get('talent-ability-exact', {}).get('count', 0) > 0:
                    talent_ability_found = True
                    logger.info(f"🎯 FOUND talent-ability pattern on {page_key}!")
                    for elem in patterns['talent-ability-exact']['elements']:
                        logger.info(f"  - {elem['id']}: '{elem['text']}'")
        
        if not talent_ability_found:
            logger.info("❌ No talent-ability pattern found on any page")
            logger.info("This suggests the pattern might appear under different conditions:")
            logger.info("  - Different report/fight")
            logger.info("  - Different page context")
            logger.info("  - Requires user interaction to load")
            logger.info("  - Appears in dynamically loaded content")
        
        return results
        
    except Exception as e:
        logger.error(f"Comprehensive search failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def test_different_report():
    """Test with a different report to see if the pattern appears elsewhere."""
    
    logger.info("=" * 80)
    logger.info("TESTING DIFFERENT REPORT")
    logger.info("=" * 80)
    
    # Try a different report that might have more data
    # Using a public report from the examples
    report_code = "3gjVGWB2dxCL8XAw"  # From the examples
    fight_id = 1  # First fight
    source_id = 1  # First player
    
    searcher = ESOLogsComprehensiveSearcher()
    
    try:
        # Test just the summary page of a different report
        url = f"https://www.esologs.com/reports/{report_code}?fight={fight_id}&type=summary&source={source_id}"
        
        logger.info(f"Testing different report: {url}")
        
        results = searcher.search_all_patterns(url)
        
        # Save results
        output_file = f"different_report_search_{report_code}_{fight_id}_{source_id}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Different report results saved to: {output_file}")
        
        # Check for talent-ability pattern
        patterns = results.get('patterns_found', {})
        talent_ability_count = patterns.get('talent-ability-exact', {}).get('count', 0)
        
        if talent_ability_count > 0:
            logger.info(f"🎯 FOUND {talent_ability_count} talent-ability patterns in different report!")
            for elem in patterns['talent-ability-exact']['elements']:
                logger.info(f"  - {elem['id']}: '{elem['text']}'")
        else:
            logger.info("❌ No talent-ability pattern found in different report either")
        
        return results
        
    except Exception as e:
        logger.error(f"Different report test failed: {e}")
        return None


async def main():
    """Run all comprehensive search tests."""
    
    logger.info("Starting comprehensive ESO Logs ability pattern search")
    logger.info("=" * 80)
    
    # Test 1: Comprehensive search on original report
    results1 = await test_comprehensive_search()
    
    # Test 2: Test different report
    results2 = await test_different_report()
    
    logger.info("=" * 80)
    logger.info("All comprehensive tests completed!")
    
    # Final analysis
    if results1 and results2:
        total_patterns_1 = sum(
            sum(pattern_data['count'] for pattern_data in page_data.get('patterns_found', {}).values())
            for page_data in results1['pages'].values()
            if 'error' not in page_data
        )
        
        total_patterns_2 = sum(
            pattern_data['count'] for pattern_data in results2.get('patterns_found', {}).values()
        )
        
        logger.info(f"Report 1 total patterns: {total_patterns_1}")
        logger.info(f"Report 2 total patterns: {total_patterns_2}")


if __name__ == "__main__":
    asyncio.run(main())
