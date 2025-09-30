#!/usr/bin/env python3
"""
Test script to analyze action bar positions based on DOM order.

This script investigates whether action bar positions can be inferred from the
order abilities appear in the DOM, since the ID pattern doesn't encode position.
"""

import asyncio
import json
import logging
import re
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from eso_builds.working_ability_scraper import WorkingAbilityScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DOMOrderAnalyzer:
    """Analyzer to determine action bar positions from DOM order."""
    
    def __init__(self):
        """Initialize the DOM order analyzer."""
        pass
    
    async def analyze_dom_order(self, report_code: str, fight_id: int, source_id: int) -> Dict:
        """
        Analyze action bar positions based on DOM order.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: The source/player ID
        
        Returns:
            Dictionary with DOM order analysis
        """
        async with WorkingAbilityScraper(headless=False) as scraper:
            try:
                url = scraper.construct_fight_url(report_code, fight_id, source_id, "casts")
                logger.info(f"Analyzing DOM order on: {url}")
                
                # Load page and wait
                scraper.driver.get(url)
                await asyncio.sleep(5)
                
                # Wait for dynamic content
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.webdriver.common.by import By
                
                WebDriverWait(scraper.driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                await asyncio.sleep(10)
                
                # Trigger ability loading
                await scraper._trigger_ability_loading()
                
                # Get all ability spans in DOM order
                ability_spans = scraper.driver.find_elements(By.CSS_SELECTOR, "span[id^='ability-']")
                logger.info(f"Found {len(ability_spans)} ability spans in DOM order")
                
                # Analyze DOM order
                analysis = {
                    'total_abilities': len(ability_spans),
                    'dom_order_analysis': [],
                    'action_bar_inference': {},
                    'timestamp': datetime.now().isoformat()
                }
                
                # Process abilities in DOM order
                for index, span in enumerate(ability_spans):
                    span_id = span.get_attribute('id')
                    span_text = span.text.strip()
                    span_class = span.get_attribute('class')
                    
                    # Parse ability ID
                    match = re.match(r'^ability-(\d+)-(\d+)$', span_id)
                    if match:
                        ability_id = match.group(1)
                        position_in_id = int(match.group(2))
                        
                        # Get DOM position info
                        element_location = span.location
                        element_size = span.size
                        
                        ability_info = {
                            'dom_index': index,
                            'ability_id': ability_id,
                            'ability_name': span_text,
                            'element_id': span_id,
                            'element_class': span_class,
                            'position_in_id': position_in_id,
                            'dom_location': element_location,
                            'dom_size': element_size,
                            'html': span.get_attribute('outerHTML')[:200]
                        }
                        
                        analysis['dom_order_analysis'].append(ability_info)
                        
                        logger.info(f"DOM Index {index}: {span_text} (ID: {ability_id}) at location {element_location}")
                
                # Infer action bar positions based on DOM order
                analysis['action_bar_inference'] = self._infer_action_bars_from_dom_order(analysis['dom_order_analysis'])
                
                return analysis
                
            except Exception as e:
                logger.error(f"DOM order analysis failed: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return {'error': str(e)}
    
    def _infer_action_bars_from_dom_order(self, dom_abilities: List[Dict]) -> Dict:
        """
        Infer action bar positions from DOM order.
        
        Args:
            dom_abilities: List of abilities in DOM order
        
        Returns:
            Dictionary with action bar inference
        """
        inference = {
            'primary_bar': [],
            'secondary_bar': [],
            'utility_abilities': [],
            'inference_logic': [],
            'total_abilities': len(dom_abilities)
        }
        
        logger.info(f"Inferring action bars from {len(dom_abilities)} abilities in DOM order")
        
        # Strategy 1: First 6 abilities = Primary bar, Next 6 = Secondary bar
        if len(dom_abilities) >= 12:
            inference['primary_bar'] = dom_abilities[:6]
            inference['secondary_bar'] = dom_abilities[6:12]
            inference['utility_abilities'] = dom_abilities[12:]
            
            inference['inference_logic'].append("Strategy 1: First 6 = Primary, Next 6 = Secondary")
            logger.info("Using Strategy 1: First 6 abilities = Primary bar, Next 6 = Secondary bar")
        
        # Strategy 2: Look for weapon swap as divider
        weapon_swap_index = None
        for i, ability in enumerate(dom_abilities):
            if 'swap' in ability['ability_name'].lower() or ability['ability_id'] == '28541':
                weapon_swap_index = i
                break
        
        if weapon_swap_index is not None:
            # Abilities before weapon swap might be one bar, after might be another
            before_swap = dom_abilities[:weapon_swap_index]
            after_swap = dom_abilities[weapon_swap_index + 1:]
            
            inference['inference_logic'].append(f"Strategy 2: Weapon swap at index {weapon_swap_index} as divider")
            
            if len(before_swap) <= 6 and len(after_swap) <= 6:
                inference['primary_bar'] = before_swap
                inference['secondary_bar'] = after_swap
                logger.info(f"Using Strategy 2: {len(before_swap)} abilities before swap, {len(after_swap)} after swap")
        
        # Strategy 3: Look for common ESO ability patterns
        # ESO typically has: 5 combat abilities + 1 ultimate per bar
        combat_abilities = []
        ultimates = []
        utility = []
        
        for ability in dom_abilities:
            ability_name = ability['ability_name'].lower()
            
            # Identify ultimates (common patterns)
            if any(keyword in ability_name for keyword in ['standard', 'sentinel', 'fatecarver', 'might']):
                ultimates.append(ability)
            # Identify utility abilities
            elif any(keyword in ability_name for keyword in ['swap', 'dodge', 'restore health', 'purify']):
                utility.append(ability)
            else:
                combat_abilities.append(ability)
        
        if len(ultimates) >= 2 and len(combat_abilities) >= 10:
            # Try to group by ultimates
            inference['inference_logic'].append("Strategy 3: Grouped by ultimates and combat abilities")
            
            # Find first ultimate and second ultimate
            first_ultimate_index = None
            second_ultimate_index = None
            
            for i, ability in enumerate(dom_abilities):
                if any(keyword in ability['ability_name'].lower() for keyword in ['standard', 'sentinel', 'fatecarver', 'might']):
                    if first_ultimate_index is None:
                        first_ultimate_index = i
                    elif second_ultimate_index is None:
                        second_ultimate_index = i
                        break
            
            if first_ultimate_index is not None and second_ultimate_index is not None:
                # Group around ultimates
                first_bar_end = min(first_ultimate_index + 6, len(dom_abilities))
                second_bar_start = max(second_ultimate_index - 5, first_bar_end)
                second_bar_end = min(second_bar_start + 6, len(dom_abilities))
                
                inference['primary_bar'] = dom_abilities[:first_bar_end]
                inference['secondary_bar'] = dom_abilities[second_bar_start:second_bar_end]
                inference['utility_abilities'] = [a for a in dom_abilities if a not in inference['primary_bar'] and a not in inference['secondary_bar']]
                
                logger.info(f"Using Strategy 3: Grouped around ultimates at indices {first_ultimate_index} and {second_ultimate_index}")
        
        # Final validation and logging
        logger.info(f"Inference results:")
        logger.info(f"  Primary bar: {len(inference['primary_bar'])} abilities")
        logger.info(f"  Secondary bar: {len(inference['secondary_bar'])} abilities")
        logger.info(f"  Utility abilities: {len(inference['utility_abilities'])} abilities")
        
        return inference
    
    def print_action_bar_analysis(self, analysis: Dict):
        """Print the action bar analysis results."""
        
        if 'error' in analysis:
            logger.error(f"Analysis failed: {analysis['error']}")
            return
        
        logger.info("=" * 80)
        logger.info("DOM ORDER ACTION BAR ANALYSIS:")
        logger.info("=" * 80)
        
        dom_abilities = analysis.get('dom_order_analysis', [])
        action_bar_inference = analysis.get('action_bar_inference', {})
        
        logger.info(f"Total abilities found: {len(dom_abilities)}")
        
        logger.info("\n🎯 DOM ORDER (as they appear in the page):")
        logger.info("-" * 60)
        for ability in dom_abilities:
            logger.info(f"  {ability['dom_index']:2d}: {ability['ability_name']} (ID: {ability['ability_id']})")
        
        logger.info("\n🎯 INFERRED PRIMARY BAR:")
        logger.info("-" * 60)
        primary_bar = action_bar_inference.get('primary_bar', [])
        for ability in primary_bar:
            logger.info(f"  {ability['dom_index']:2d}: {ability['ability_name']} (ID: {ability['ability_id']})")
        
        logger.info("\n🎯 INFERRED SECONDARY BAR:")
        logger.info("-" * 60)
        secondary_bar = action_bar_inference.get('secondary_bar', [])
        for ability in secondary_bar:
            logger.info(f"  {ability['dom_index']:2d}: {ability['ability_name']} (ID: {ability['ability_id']})")
        
        if action_bar_inference.get('utility_abilities'):
            logger.info("\n🎯 UTILITY ABILITIES:")
            logger.info("-" * 60)
            utility = action_bar_inference.get('utility_abilities', [])
            for ability in utility:
                logger.info(f"  {ability['dom_index']:2d}: {ability['ability_name']} (ID: {ability['ability_id']})")
        
        logger.info("\n💡 INFERENCE LOGIC:")
        logger.info("-" * 60)
        for logic in action_bar_inference.get('inference_logic', []):
            logger.info(f"  - {logic}")
        
        # Summary
        primary_count = len(primary_bar)
        secondary_count = len(secondary_bar)
        
        logger.info("\n" + "=" * 80)
        logger.info("ACTION BAR MAPPING SUMMARY:")
        logger.info("=" * 80)
        
        if primary_count > 0 or secondary_count > 0:
            logger.info(f"✅ SUCCESS: Inferred action bar positions from DOM order!")
            logger.info(f"Primary bar: {primary_count} abilities")
            logger.info(f"Secondary bar: {secondary_count} abilities")
            
            if primary_count == 6 and secondary_count == 6:
                logger.info("🎉 PERFECT: Found exactly 6 abilities per bar!")
            elif primary_count >= 5 and secondary_count >= 5:
                logger.info("✅ GOOD: Found 5+ abilities per bar")
            else:
                logger.info("⚠️ PARTIAL: Found some action bar data")
        else:
            logger.info("❌ Could not infer action bar positions from DOM order")


async def main():
    """Run DOM order analysis."""
    
    logger.info("Starting DOM Order Action Bar Analysis")
    logger.info("=" * 80)
    
    # Test data
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    source_id = 1
    
    analyzer = DOMOrderAnalyzer()
    
    try:
        # Analyze DOM order
        results = await analyzer.analyze_dom_order(report_code, fight_id, source_id)
        
        # Save results
        output_file = f"dom_order_analysis_{report_code}_{fight_id}_{source_id}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {output_file}")
        
        # Print analysis
        analyzer.print_action_bar_analysis(results)
        
        return results
        
    except Exception as e:
        logger.error(f"DOM order analysis failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


if __name__ == "__main__":
    asyncio.run(main())
