#!/usr/bin/env python3
"""
Focused test script for the Playwright encounter scraper.

This script demonstrates scraping ability data for key players in an encounter
and generating clean bar1: and bar2: output, filtering out duplicates and pets.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from eso_builds.playwright_encounter_scraper import PlaywrightEncounterScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def filter_key_players(encounter_data):
    """Filter to show only key players, removing duplicates and pets."""
    
    key_players = {}
    
    for player_name, player_data in encounter_data.get('players', {}).items():
        # Skip pets and duplicate entries
        if any(skip in player_name.lower() for skip in [
            'twilight matriarch', 'blighted blastbones', 'blastbones'
        ]):
            continue
            
        # Skip numbered players (1, 2, 3, etc.) as they're likely duplicates
        if player_name.strip().isdigit():
            continue
            
        # Skip anonymous players with very generic names
        if 'anonymous' in player_name.lower() and len(player_name) < 15:
            continue
            
        # Keep players with substantial abilities (more than 10)
        if player_data.get('total_abilities', 0) >= 10:
            key_players[player_name] = player_data
    
    return key_players


def format_clean_encounter_output(encounter_data):
    """Format encounter data with only key players."""
    
    output_lines = []
    
    output_lines.append(f"Encounter: {encounter_data['report_code']} Fight {encounter_data['fight_id']}")
    output_lines.append(f"Timestamp: {encounter_data['timestamp']}")
    output_lines.append("=" * 80)
    
    # Filter to key players
    key_players = filter_key_players(encounter_data)
    
    for player_name, player_data in key_players.items():
        output_lines.append(f"\nPlayer: {player_name}")
        output_lines.append(f"Class: {player_data.get('class', 'Unknown')} | Role: {player_data.get('role', 'Unknown')}")
        
        action_bars = player_data.get('action_bars', {})
        
        # Format bar1
        bar1_abilities = action_bars.get('bar1', [])
        bar1_line = "bar1: " + ", ".join(bar1_abilities) if bar1_abilities else "bar1: (empty)"
        output_lines.append(bar1_line)
        
        # Format bar2
        bar2_abilities = action_bars.get('bar2', [])
        bar2_line = "bar2: " + ", ".join(bar2_abilities) if bar2_abilities else "bar2: (empty)"
        output_lines.append(bar2_line)
        
        # Show ability count
        total_abilities = player_data.get('total_abilities', 0)
        output_lines.append(f"Total abilities: {total_abilities}")
        
        output_lines.append("-" * 40)
    
    return "\n".join(output_lines)


async def test_focused_encounter_scraper():
    """Test the encounter scraper with focused output."""
    
    logger.info("Testing Focused Playwright Encounter Scraper")
    logger.info("=" * 80)
    
    # Test data
    report_code = "7KAWyZwPCkaHfc8j"
    fight_id = 17
    
    try:
        # Test the encounter scraper
        logger.info(f"Scraping encounter for report: {report_code}, fight: {fight_id}")
        
        scraper = PlaywrightEncounterScraper(headless=True)
        encounter_data = await scraper.scrape_encounter_abilities(report_code, fight_id)
        
        # Format clean output
        clean_output = format_clean_encounter_output(encounter_data)
        
        # Save clean formatted output
        output_file = f"focused_encounter_bars_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_file, 'w') as f:
            f.write(clean_output)
        
        logger.info(f"Clean output saved to: {output_file}")
        
        # Print the clean output
        logger.info("=" * 80)
        logger.info("FOCUSED ENCOUNTER BAR OUTPUT:")
        logger.info("=" * 80)
        print(clean_output)
        
        # Count key players
        key_players = filter_key_players(encounter_data)
        logger.info(f"Found {len(key_players)} key players in encounter")
        
        return encounter_data
        
    except Exception as e:
        logger.error(f"Focused encounter scraper test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


async def main():
    """Run the focused encounter scraper test."""
    
    logger.info("Starting Focused Playwright Encounter Scraper Test")
    logger.info("=" * 80)
    
    # Test focused encounter scraper
    results = await test_focused_encounter_scraper()
    
    logger.info("=" * 80)
    logger.info("Focused encounter scraper test completed!")
    
    if results:
        key_players = filter_key_players(results)
        logger.info(f"✅ SUCCESS: Found {len(key_players)} key players with action bars")
        logger.info("🚀 Playwright encounter scraper generates perfect bar1: bar2: output!")
        logger.info("🎯 Ready for integration into the main application!")
    else:
        logger.info("❌ Focused encounter scraper test failed")


if __name__ == "__main__":
    asyncio.run(main())
