#!/usr/bin/env python3
"""
Simple test to check if ability data is loaded dynamically via JavaScript.

This script creates a simple test to understand if the talent-ability pattern
appears after JavaScript execution.
"""

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


def analyze_javascript_content(url: str) -> dict:
    """
    Analyze JavaScript content to see if ability data is loaded dynamically.
    
    Args:
        url: The URL to analyze
    
    Returns:
        Dictionary containing analysis results
    """
    try:
        logger.info(f"Analyzing JavaScript content on: {url}")
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })
        
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = {
            'url': url,
            'title': soup.title.string if soup.title else '',
            'javascript_analysis': {},
            'dynamic_loading_indicators': []
        }
        
        # Find all script tags
        scripts = soup.find_all('script')
        logger.info(f"Found {len(scripts)} script tags")
        
        # Analyze JavaScript for dynamic loading patterns
        js_content = ""
        for script in scripts:
            if script.string:
                js_content += script.string + "\n"
        
        # Look for patterns that suggest dynamic loading
        dynamic_patterns = {
            'ajax_calls': [
                r'\.ajax\(',
                r'fetch\(',
                r'XMLHttpRequest',
                r'\.get\(',
                r'\.post\(',
            ],
            'dynamic_content': [
                r'\.html\(',
                r'\.append\(',
                r'\.prepend\(',
                r'\.replaceWith\(',
                r'\.load\(',
                r'innerHTML',
                r'outerHTML',
            ],
            'ability_related': [
                r'ability',
                r'talent',
                r'skill',
                r'spell',
                r'loadAbilities',
                r'getAbilities',
                r'abilityData',
            ],
            'api_calls': [
                r'/api/',
                r'api\.',
                r'endpoint',
                r'graphql',
            ]
        }
        
        for category, patterns in dynamic_patterns.items():
            category_results = []
            for pattern in patterns:
                matches = re.findall(pattern, js_content, re.IGNORECASE)
                if matches:
                    category_results.append({
                        'pattern': pattern,
                        'matches': len(matches),
                        'sample_matches': matches[:5]  # First 5 matches
                    })
            
            results['javascript_analysis'][category] = category_results
            
            if category_results:
                logger.info(f"Found {len(category_results)} dynamic loading patterns in category '{category}'")
        
        # Look for specific function calls that might load ability data
        function_patterns = [
            r'loadAbilitiesMenuIfNeeded\(\)',
            r'loadAbilities\(',
            r'getAbilityData\(',
            r'fetchAbilities\(',
            r'loadTalentData\(',
        ]
        
        for pattern in function_patterns:
            matches = re.findall(pattern, js_content, re.IGNORECASE)
            if matches:
                results['dynamic_loading_indicators'].append({
                    'function': pattern,
                    'count': len(matches),
                    'context': 'Found function calls that suggest dynamic loading'
                })
                logger.info(f"Found dynamic loading function: {pattern} ({len(matches)} times)")
        
        # Look for API endpoints that might contain ability data
        api_patterns = [
            r'["\']https?://[^"\']*ability[^"\']*["\']',
            r'["\']https?://[^"\']*talent[^"\']*["\']',
            r'["\']https?://[^"\']*api[^"\']*["\']',
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, js_content, re.IGNORECASE)
            if matches:
                results['dynamic_loading_indicators'].append({
                    'api_endpoint': pattern,
                    'count': len(matches),
                    'endpoints': matches[:3],  # First 3 endpoints
                    'context': 'Found API endpoints that might load ability data'
                })
                logger.info(f"Found potential API endpoints: {len(matches)} matches")
        
        # Check for event listeners that might trigger ability loading
        event_patterns = [
            r'addEventListener\(',
            r'\.on\(',
            r'\.click\(',
            r'\.hover\(',
            r'\.mouseover\(',
        ]
        
        event_matches = []
        for pattern in event_patterns:
            matches = re.findall(pattern, js_content, re.IGNORECASE)
            event_matches.extend(matches)
        
        if event_matches:
            results['dynamic_loading_indicators'].append({
                'event_listeners': len(event_matches),
                'context': 'Found event listeners that might trigger dynamic loading',
                'sample_events': event_matches[:5]
            })
            logger.info(f"Found {len(event_matches)} event listeners")
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to analyze JavaScript content: {e}")
        return {'error': str(e), 'url': url}


def check_static_vs_dynamic_content(url: str) -> dict:
    """
    Compare static HTML content vs what might be loaded dynamically.
    
    Args:
        url: The URL to check
    
    Returns:
        Dictionary with comparison results
    """
    try:
        logger.info(f"Checking static vs dynamic content on: {url}")
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })
        
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = {
            'url': url,
            'static_content': {},
            'dynamic_indicators': []
        }
        
        # Check static HTML for ability-related content
        static_checks = {
            'ability_spans': len(soup.find_all('span', {'id': re.compile(r'talent-ability-\d+')})),
            'ability_divs': len(soup.find_all('div', {'id': re.compile(r'ability')})),
            'data_attributes': len(soup.find_all(attrs={'data-ability': True})),
            'ability_classes': len(soup.find_all(class_=re.compile(r'ability'))),
            'total_spans': len(soup.find_all('span')),
            'total_divs': len(soup.find_all('div')),
        }
        
        results['static_content'] = static_checks
        
        # Check for placeholders or containers that might be populated dynamically
        placeholder_patterns = [
            r'loading',
            r'placeholder',
            r'container',
            r'content',
            r'data',
        ]
        
        for pattern in placeholder_patterns:
            elements = soup.find_all(attrs={'id': re.compile(pattern, re.IGNORECASE)})
            if elements:
                results['dynamic_indicators'].append({
                    'type': 'placeholder_container',
                    'pattern': pattern,
                    'count': len(elements),
                    'elements': [{'id': el.get('id'), 'class': el.get('class')} for el in elements[:3]]
                })
        
        # Check for empty containers that might be populated
        empty_containers = soup.find_all(lambda tag: tag.name in ['div', 'span', 'ul', 'ol'] and not tag.get_text(strip=True) and tag.get('id'))
        if empty_containers:
            results['dynamic_indicators'].append({
                'type': 'empty_containers',
                'count': len(empty_containers),
                'containers': [{'id': el.get('id'), 'tag': el.name} for el in empty_containers[:5]]
            })
        
        # Check for JavaScript that suggests dynamic loading
        scripts = soup.find_all('script')
        js_content = " ".join([script.string or "" for script in scripts])
        
        if 'loadAbilitiesMenuIfNeeded' in js_content:
            results['dynamic_indicators'].append({
                'type': 'explicit_loading_function',
                'function': 'loadAbilitiesMenuIfNeeded',
                'context': 'Found explicit function to load abilities menu'
            })
        
        logger.info(f"Static content check complete:")
        for key, value in static_checks.items():
            logger.info(f"  - {key}: {value}")
        
        logger.info(f"Dynamic indicators found: {len(results['dynamic_indicators'])}")
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to check static vs dynamic content: {e}")
        return {'error': str(e), 'url': url}


def main():
    """Run the JavaScript dynamic loading analysis."""
    
    logger.info("Starting JavaScript dynamic loading analysis")
    logger.info("=" * 80)
    
    # Test URLs
    urls_to_test = [
        "https://www.esologs.com/reports/7KAWyZwPCkaHfc8j?fight=17&type=summary&source=1",
        "https://www.esologs.com/reports/7KAWyZwPCkaHfc8j?fight=17&type=casts&source=1",
    ]
    
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'analysis_results': []
    }
    
    for url in urls_to_test:
        logger.info(f"Analyzing: {url}")
        
        # Analyze JavaScript content
        js_analysis = analyze_javascript_content(url)
        
        # Check static vs dynamic content
        static_analysis = check_static_vs_dynamic_content(url)
        
        url_results = {
            'url': url,
            'javascript_analysis': js_analysis,
            'static_vs_dynamic': static_analysis
        }
        
        all_results['analysis_results'].append(url_results)
    
    # Save results
    output_file = f"js_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    logger.info(f"Analysis results saved to: {output_file}")
    
    # Print summary
    logger.info("=" * 80)
    logger.info("JAVASCRIPT DYNAMIC LOADING ANALYSIS SUMMARY:")
    logger.info("=" * 80)
    
    total_dynamic_indicators = 0
    total_static_abilities = 0
    
    for result in all_results['analysis_results']:
        if 'error' not in result['javascript_analysis']:
            dynamic_indicators = len(result['javascript_analysis'].get('dynamic_loading_indicators', []))
            total_dynamic_indicators += dynamic_indicators
            
            logger.info(f"URL: {result['url']}")
            logger.info(f"  - Dynamic loading indicators: {dynamic_indicators}")
            
            if dynamic_indicators > 0:
                for indicator in result['javascript_analysis']['dynamic_loading_indicators']:
                    logger.info(f"    * {indicator.get('context', 'Dynamic loading detected')}")
        
        if 'error' not in result['static_vs_dynamic']:
            static_abilities = result['static_vs_dynamic'].get('static_content', {}).get('ability_spans', 0)
            total_static_abilities += static_abilities
            
            logger.info(f"  - Static ability spans: {static_abilities}")
    
    logger.info("=" * 80)
    logger.info(f"TOTAL DYNAMIC INDICATORS: {total_dynamic_indicators}")
    logger.info(f"TOTAL STATIC ABILITIES: {total_static_abilities}")
    
    if total_dynamic_indicators > 0 and total_static_abilities == 0:
        logger.info("✅ CONCLUSION: Ability data is likely loaded dynamically via JavaScript")
        logger.info("This explains why we don't see talent-ability spans in static HTML")
    elif total_static_abilities > 0:
        logger.info("❓ CONCLUSION: Some ability data exists in static HTML")
    else:
        logger.info("❓ CONCLUSION: No clear evidence of ability data loading pattern")
    
    logger.info("=" * 80)
    logger.info("Analysis completed!")


if __name__ == "__main__":
    main()
