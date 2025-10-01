#!/usr/bin/env python3
"""
Comprehensive unit test to compare abilities from web scraping vs API with includeCombatantInfo=True
"""

import asyncio
import os
import logging
from typing import Dict, List, Any, Optional
from src.eso_builds.api_client import ESOLogsClient
from src.eso_builds.talents_cell_scraper import TalentsCellScraper
from src.eso_builds.models import Role

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AbilityComparisonTest:
    """Test class to compare abilities from API vs web scraping"""
    
    def __init__(self):
        self.client_id = os.getenv('ESOLOGS_ID')
        self.client_secret = os.getenv('ESOLOGS_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Missing API credentials. Set ESOLOGS_ID and ESOLOGS_SECRET environment variables.")
    
    async def get_api_abilities(self, report_code: str, fight_url: str) -> Dict[str, Any]:
        """Get abilities from API with includeCombatantInfo=True"""
        logger.info(f"🔍 Getting abilities from API for {report_code}")
        
        async with ESOLogsClient(client_id=self.client_id, client_secret=self.client_secret) as client:
            try:
                # Use known time ranges from the working system
                # These are the actual time ranges that work with our current API calls
                start_time = 1750867200000  # Known working start time
                end_time = 1750867374600    # Known working end time
                
                logger.info(f"📊 Using known time range: {start_time} - {end_time}")
                
                # Get table data with includeCombatantInfo=True
                table_data = await client._make_request(
                    "get_report_table",
                    code=report_code,
                    start_time=int(start_time),
                    end_time=int(end_time),
                    data_type="Summary",
                    hostility_type="Friendlies",
                    includeCombatantInfo=True
                )
                
                # Extract player details with abilities
                api_abilities = {}
                
                # Debug: Log the structure of what we got back
                logger.info(f"📊 API Response type: {type(table_data)}")
                if hasattr(table_data, '__dict__'):
                    logger.info(f"📊 API Response attributes: {list(table_data.__dict__.keys())}")
                
                if table_data and hasattr(table_data, 'report_data') and hasattr(table_data.report_data, 'report'):
                    report = table_data.report_data.report
                    logger.info(f"📊 Report type: {type(report)}")
                    if hasattr(report, 'table'):
                        table = report.table
                        logger.info(f"📊 Table type: {type(table)}")
                        if isinstance(table, dict):
                            logger.info(f"📊 Table keys: {list(table.keys())}")
                            if 'data' in table:
                                data = table['data']
                                logger.info(f"📊 Data type: {type(data)}")
                                if isinstance(data, dict):
                                    logger.info(f"📊 Data keys: {list(data.keys())}")
                                    if 'data' in data:
                                        final_data = data['data']
                                        logger.info(f"📊 Final data type: {type(final_data)}")
                                        if isinstance(final_data, dict):
                                            logger.info(f"📊 Final data keys: {list(final_data.keys())}")
                                        
                                        if 'playerDetails' in final_data:
                                            player_details = final_data['playerDetails']
                                            logger.info(f"📊 Found {len(player_details)} player details from API")
                                            
                                            # Debug: Log structure of first player
                                            if player_details and len(player_details) > 0:
                                                first_player = player_details[0]
                                                logger.info(f"📊 First player type: {type(first_player)}")
                                                if isinstance(first_player, dict):
                                                    logger.info(f"📊 First player keys: {list(first_player.keys())}")
                                            
                                            for player in player_details:
                                                if isinstance(player, dict):
                                                    player_name = player.get('name', 'Unknown')
                                                    player_id = player.get('id', 'Unknown')
                                                    
                                                    logger.info(f"📊 Player {player_name}: keys = {list(player.keys())}")
                                                    
                                                    # Check for combatant info with abilities
                                                    if 'combatantInfo' in player:
                                                        combatant_info = player['combatantInfo']
                                                        logger.info(f"📊 Combatant info for {player_name}: {type(combatant_info)}")
                                                        if isinstance(combatant_info, dict):
                                                            logger.info(f"📊 Combatant info keys: {list(combatant_info.keys())}")
                                                            # Look for abilities data
                                                            abilities_data = self._extract_abilities_from_combatant_info(combatant_info)
                                                            if abilities_data:
                                                                api_abilities[player_name] = {
                                                                    'id': player_id,
                                                                    'abilities': abilities_data,
                                                                    'combatant_info': combatant_info
                                                                }
                                                                logger.info(f"✅ Found abilities for {player_name}: {abilities_data}")
                                                            else:
                                                                logger.info(f"❌ No abilities found in combatant info for {player_name}")
                                                    else:
                                                        logger.info(f"❌ No combatantInfo for {player_name}")
                
                return api_abilities
                
            except Exception as e:
                logger.error(f"❌ Error getting API abilities: {e}")
                return {}
    
    def _extract_abilities_from_combatant_info(self, combatant_info: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract abilities from combatant info structure"""
        abilities = {'bar1': [], 'bar2': []}
        
        # Look for common ability-related keys
        ability_keys = ['abilities', 'actionBars', 'bars', 'skills', 'talents']
        
        for key in ability_keys:
            if key in combatant_info:
                ability_data = combatant_info[key]
                logger.info(f"🔍 Found ability data in key '{key}': {type(ability_data)}")
                
                if isinstance(ability_data, list):
                    # Split abilities into bar1 and bar2 (first 6 and next 6)
                    if len(ability_data) >= 12:
                        abilities['bar1'] = [str(ability) for ability in ability_data[:6]]
                        abilities['bar2'] = [str(ability) for ability in ability_data[6:12]]
                    elif len(ability_data) >= 6:
                        abilities['bar1'] = [str(ability) for ability in ability_data[:6]]
                elif isinstance(ability_data, dict):
                    # Check for bar1/bar2 structure
                    if 'bar1' in ability_data:
                        abilities['bar1'] = [str(ability) for ability in ability_data['bar1']]
                    if 'bar2' in ability_data:
                        abilities['bar2'] = [str(ability) for ability in ability_data['bar2']]
                
                if abilities['bar1'] or abilities['bar2']:
                    break
        
        return abilities
    
    async def get_scraped_abilities(self, fight_url: str) -> Dict[str, Any]:
        """Get abilities from web scraping"""
        logger.info(f"🔍 Getting abilities from web scraping for {fight_url}")
        
        scraper = TalentsCellScraper(headless=True)
        
        try:
            # Scrape character action bars
            characters_data = await scraper.scrape_character_action_bars(fight_url)
            
            scraped_abilities = {}
            
            # Handle the return type - it should be a dict with 'characters' key
            if isinstance(characters_data, dict):
                if 'characters' in characters_data:
                    characters_list = characters_data['characters']
                    logger.info(f"📊 Found {len(characters_list)} characters from scraper")
                else:
                    logger.error(f"❌ No 'characters' key in scraper response. Keys: {list(characters_data.keys())}")
                    return {}
            else:
                logger.error(f"❌ Unexpected return type from scraper: {type(characters_data)}")
                return {}
            
            for char_data in characters_list:
                if not isinstance(char_data, dict):
                    logger.error(f"❌ Character data is not a dict: {type(char_data)}")
                    continue
                    
                character_name = char_data.get('name', 'Unknown')
                player_handle = char_data.get('handle', '')
                bar1 = char_data.get('bar1', [])
                bar2 = char_data.get('bar2', [])
                
                if bar1 or bar2:
                    scraped_abilities[character_name] = {
                        'handle': player_handle,
                        'abilities': {
                            'bar1': bar1,
                            'bar2': bar2
                        },
                        'role': char_data.get('role', 'Unknown'),
                        'class': char_data.get('class', 'Unknown')
                    }
                    logger.info(f"✅ Scraped abilities for {character_name}: {len(bar1)} bar1, {len(bar2)} bar2")
            
            return scraped_abilities
            
        except Exception as e:
            logger.error(f"❌ Error scraping abilities: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def compare_abilities(self, api_abilities: Dict[str, Any], scraped_abilities: Dict[str, Any]) -> Dict[str, Any]:
        """Compare abilities from both sources"""
        logger.info("🔍 Comparing abilities from API vs web scraping")
        
        comparison_results = {
            'total_api_players': len(api_abilities),
            'total_scraped_players': len(scraped_abilities),
            'matches': [],
            'api_only': [],
            'scraped_only': [],
            'differences': []
        }
        
        # Find common players
        api_names = set(api_abilities.keys())
        scraped_names = set(scraped_abilities.keys())
        
        common_names = api_names.intersection(scraped_names)
        comparison_results['api_only'] = list(api_names - scraped_names)
        comparison_results['scraped_only'] = list(scraped_names - api_names)
        
        logger.info(f"📊 API players: {len(api_names)}")
        logger.info(f"📊 Scraped players: {len(scraped_names)}")
        logger.info(f"📊 Common players: {len(common_names)}")
        
        # Compare abilities for common players
        for player_name in common_names:
            api_data = api_abilities[player_name]
            scraped_data = scraped_abilities[player_name]
            
            api_abilities_data = api_data.get('abilities', {})
            scraped_abilities_data = scraped_data.get('abilities', {})
            
            match_result = {
                'player_name': player_name,
                'api_abilities': api_abilities_data,
                'scraped_abilities': scraped_abilities_data,
                'bar1_match': False,
                'bar2_match': False,
                'total_match': False
            }
            
            # Compare bar1
            api_bar1 = api_abilities_data.get('bar1', [])
            scraped_bar1 = scraped_abilities_data.get('bar1', [])
            
            if api_bar1 == scraped_bar1:
                match_result['bar1_match'] = True
            else:
                match_result['bar1_differences'] = {
                    'api': api_bar1,
                    'scraped': scraped_bar1
                }
            
            # Compare bar2
            api_bar2 = api_abilities_data.get('bar2', [])
            scraped_bar2 = scraped_abilities_data.get('bar2', [])
            
            if api_bar2 == scraped_bar2:
                match_result['bar2_match'] = True
            else:
                match_result['bar2_differences'] = {
                    'api': api_bar2,
                    'scraped': scraped_bar2
                }
            
            # Overall match
            match_result['total_match'] = match_result['bar1_match'] and match_result['bar2_match']
            
            if match_result['total_match']:
                comparison_results['matches'].append(match_result)
            else:
                comparison_results['differences'].append(match_result)
            
            # Log results
            if match_result['total_match']:
                logger.info(f"✅ {player_name}: Perfect match")
            else:
                logger.warning(f"⚠️ {player_name}: Differences found")
                if not match_result['bar1_match']:
                    logger.warning(f"  Bar1 diff: API={api_bar1} vs Scraped={scraped_bar1}")
                if not match_result['bar2_match']:
                    logger.warning(f"  Bar2 diff: API={api_bar2} vs Scraped={scraped_bar2}")
        
        return comparison_results
    
    async def run_comprehensive_test(self, report_code: str, fight_url: str) -> Dict[str, Any]:
        """Run the complete comparison test"""
        logger.info("🚀 Starting comprehensive abilities comparison test")
        logger.info(f"📋 Report: {report_code}")
        logger.info(f"🔗 Fight URL: {fight_url}")
        
        # Get abilities from both sources
        api_abilities = await self.get_api_abilities(report_code, fight_url)
        scraped_abilities = await self.get_scraped_abilities(fight_url)
        
        # Compare the results
        comparison_results = self.compare_abilities(api_abilities, scraped_abilities)
        
        # Generate summary
        summary = {
            'test_status': 'PASSED' if len(comparison_results['differences']) == 0 else 'FAILED',
            'api_abilities_count': len(api_abilities),
            'scraped_abilities_count': len(scraped_abilities),
            'perfect_matches': len(comparison_results['matches']),
            'differences_count': len(comparison_results['differences']),
            'api_only_count': len(comparison_results['api_only']),
            'scraped_only_count': len(comparison_results['scraped_only'])
        }
        
        logger.info("📊 TEST SUMMARY:")
        logger.info(f"  API abilities found: {summary['api_abilities_count']}")
        logger.info(f"  Scraped abilities found: {summary['scraped_abilities_count']}")
        logger.info(f"  Perfect matches: {summary['perfect_matches']}")
        logger.info(f"  Differences: {summary['differences_count']}")
        logger.info(f"  API only: {summary['api_only_count']}")
        logger.info(f"  Scraped only: {summary['scraped_only_count']}")
        logger.info(f"  Test status: {summary['test_status']}")
        
        return {
            'summary': summary,
            'api_abilities': api_abilities,
            'scraped_abilities': scraped_abilities,
            'comparison_results': comparison_results
        }

async def main():
    """Run the comprehensive test"""
    try:
        test = AbilityComparisonTest()
        
        # Test with known report
        report_code = "N37HBwrjQGYJ6mbv"
        fight_url = f"https://www.esologs.com/reports/{report_code}?fight=1"
        
        results = await test.run_comprehensive_test(report_code, fight_url)
        
        # Save results to file for analysis
        import json
        with open('ability_comparison_results.json', 'w') as f:
            # Convert any non-serializable objects to strings
            def convert_to_serializable(obj):
                if hasattr(obj, '__dict__'):
                    return str(obj)
                return obj
            
            serializable_results = {}
            for key, value in results.items():
                if isinstance(value, dict):
                    serializable_results[key] = {k: convert_to_serializable(v) for k, v in value.items()}
                elif isinstance(value, list):
                    serializable_results[key] = [convert_to_serializable(item) for item in value]
                else:
                    serializable_results[key] = convert_to_serializable(value)
            
            json.dump(serializable_results, f, indent=2)
        
        print(f"\n💾 Results saved to: ability_comparison_results.json")
        print(f"🎯 Test completed: {results['summary']['test_status']}")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
