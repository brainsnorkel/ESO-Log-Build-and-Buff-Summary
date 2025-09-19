#!/usr/bin/env python3
"""
Extract real player data from ESO Logs API.

This script demonstrates how to correctly parse the API response
to get real player names and gear sets.
"""

import asyncio
import logging

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.eso_builds.api_client import ESOLogsClient
from src.eso_builds.gear_parser import GearParser
from src.eso_builds.models import PlayerBuild, Role, GearSet

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def extract_real_players():
    """Extract real player data from the working API call."""
    report_code = "mtFqVzQPNBcCrd1h"
    
    try:
        async with ESOLogsClient() as client:
            # Get report info
            report_response = await client._make_request("get_report_by_code", code=report_code)
            report = report_response.report_data.report
            
            # Find Hall of Fleshcraft fight
            hall_fight = None
            for fight in report.fights:
                if "Hall of Fleshcraft" in fight.name and hasattr(fight, 'difficulty') and fight.difficulty == 121:
                    hall_fight = fight
                    break
            
            if not hall_fight:
                print("❌ Could not find Hall of Fleshcraft fight")
                return
            
            print(f"🎯 Analyzing: {hall_fight.name} (Fight ID: {hall_fight.id})")
            print(f"Duration: {(hall_fight.end_time - hall_fight.start_time) / 1000:.1f} seconds")
            
            # Get table data
            table_data = await client._make_request(
                "get_report_table",
                code=report_code,
                start_time=int(hall_fight.start_time),
                end_time=int(hall_fight.end_time),
                data_type="Summary",
                hostility_type="Friendlies"
            )
            
            print(f"\n📊 Table Data Structure:")
            table = table_data.report_data.report.table
            print(f"Table type: {type(table)}")
            
            if isinstance(table, dict):
                print(f"Table keys: {list(table.keys())}")
                
                # Check the data section
                if 'data' in table:
                    data_section = table['data']
                    print(f"Data section keys: {list(data_section.keys())}")
                    
                    # Check for playerDetails in data
                    if 'playerDetails' in data_section:
                        player_details = data_section['playerDetails']
                        print(f"Player details keys: {list(player_details.keys())}")
                    else:
                        print("❌ No playerDetails in data section")
                        return
                elif 'playerDetails' in table:
                    player_details = table['playerDetails']
                    print(f"Player details keys: {list(player_details.keys())}")
                    
                # Extract real players
                all_players = []
                gear_parser = GearParser()
                
                for role_name, role_enum in [('tanks', Role.TANK), ('healers', Role.HEALER), ('dps', Role.DPS)]:
                    if role_name in player_details:
                        section_players = player_details[role_name]
                        print(f"\n🛡️ {role_name.title()}: {len(section_players)} players")
                        
                        for i, player_data in enumerate(section_players, 1):
                            name = player_data.get('name', f'Unknown{i}')
                            display_name = player_data.get('displayName', '')
                            character_class = player_data.get('type', 'Unknown')
                            
                            # Extract gear
                            gear_sets = []
                            if 'combatantInfo' in player_data and 'gear' in player_data['combatantInfo']:
                                gear_items = player_data['combatantInfo']['gear']
                                
                                # Convert to our format
                                gear_data = {'gear': []}
                                for gear_item in gear_items:
                                    if gear_item.get('setID', 0) > 0:
                                        gear_data['gear'].append({
                                            'setID': gear_item.get('setID'),
                                            'setName': gear_item.get('setName'),
                                            'slot': gear_item.get('slot', 'unknown')
                                        })
                                
                                gear_sets = gear_parser.parse_player_gear(gear_data)
                            
                            # Use display name if available
                            final_name = display_name if display_name else name
                            
                            player = PlayerBuild(
                                name=final_name,
                                character_class=character_class,
                                role=role_enum,
                                gear_sets=gear_sets
                            )
                            all_players.append(player)
                            
                            # Show the player
                            gear_str = ", ".join(str(g) for g in gear_sets) if gear_sets else "no gear data"
                            print(f"  {role_name.title()} {i} {final_name}: {character_class}, {gear_str}")
                
                print(f"\n🎉 Successfully extracted {len(all_players)} real players!")
                return all_players
            else:
                print("❌ No playerDetails found in table")
            
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function."""
    print("🔍 Real Player Data Extraction Test")
    print("=" * 40)
    
    players = await extract_real_players()
    
    if players:
        print(f"\n📋 SUMMARY:")
        print(f"Total players extracted: {len(players)}")
        
        for role in [Role.TANK, Role.HEALER, Role.DPS]:
            role_players = [p for p in players if p.role == role]
            print(f"{role.value}s: {len(role_players)}")
            for player in role_players:
                print(f"  - {player.name} ({player.character_class})")


if __name__ == "__main__":
    asyncio.run(main())
