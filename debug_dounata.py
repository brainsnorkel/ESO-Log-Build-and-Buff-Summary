#!/usr/bin/env python3
"""
Debug script to examine Tank 2 @Dounata's gear specifically.
"""

import asyncio
import sys
from dotenv import load_dotenv

# Add src to path and load env
sys.path.append('src')
load_dotenv()

from src.eso_builds.single_report_analyzer import SingleReportAnalyzer
from src.eso_builds.api_client import ESOLogsClient

async def debug_dounata():
    """Debug Tank 2 @Dounata's gear specifically."""
    print("🔍 Debugging Tank 2 @Dounata's gear")
    print("=" * 60)
    
    async with ESOLogsClient() as client:
        # No need for analyzer, we'll access gear parser directly
        
        try:
            report_code = "mtFqVzQPNBcCrd1h"
            
            # Get the report info
            report_info_response = await client._make_request("get_report_by_code", code=report_code)
            report_info = report_info_response.report_data.report
            
            # Focus on the first boss fight
            first_fight = None
            for fight in report_info.fights:
                if hasattr(fight, 'difficulty') and fight.difficulty is not None:
                    boss_names = ['Hall of Fleshcraft', 'Jynorah and Skorkhif', 'Overfiend Kazpian']
                    if any(boss in fight.name for boss in boss_names):
                        first_fight = fight
                        break
            
            if not first_fight:
                print("❌ No boss fight found")
                return
                
            print(f"📊 Analyzing fight: {first_fight.name}")
            
            # Get player data
            table_data = await client._make_request(
                "get_report_table",
                code=report_code,
                start_time=int(first_fight.start_time),
                end_time=int(first_fight.end_time),
                data_type="Summary",
                hostility_type="Friendlies"
            )
            
            if table_data and hasattr(table_data, 'report_data'):
                table = table_data.report_data.report.table
                
                if isinstance(table, dict) and 'data' in table:
                    data_section = table['data']
                    
                    if 'playerDetails' in data_section:
                        player_details = data_section['playerDetails']
                        
                        # Look for Dounata in tanks
                        if 'tanks' in player_details:
                            for tank_data in player_details['tanks']:
                                name = tank_data.get('name', 'Unknown')
                                display_name = tank_data.get('displayName', '')
                                
                                if 'dounata' in name.lower() or 'dounata' in display_name.lower():
                                    print(f"🎯 FOUND DOUNATA: {name} (display: {display_name})")
                                    
                                    # Examine their gear
                                    if 'combatantInfo' in tank_data and 'gear' in tank_data['combatantInfo']:
                                        gear_items = tank_data['combatantInfo']['gear']
                                        print(f"📋 Raw gear items: {len(gear_items)}")
                                        
                                        for idx, item in enumerate(gear_items):
                                            set_name = item.get('setName', 'No Set')
                                            item_name = item.get('name', 'Unknown Item')
                                            slot = item.get('slot', 'unknown')
                                            
                                            if 'powerful' in set_name.lower() or 'powerful' in item_name.lower():
                                                print(f"🔍 POWERFUL ASSAULT ITEM #{idx}:")
                                                print(f"    setName: {set_name}")
                                                print(f"    itemName: {item_name}")
                                                print(f"    slot: {slot}")
                                                print(f"    Full item: {item}")
                                        
                                        # Parse gear with our parser
                                        print(f"🔧 Calling gear parser...")
                                        gear_sets = client.gear_parser.parse_player_gear(gear_items)
                                        print(f"📊 Processed gear sets: {gear_sets}")
                                        
                                        # Look for Powerful Assault specifically
                                        for gear_set in gear_sets:
                                            if 'powerful' in gear_set.name.lower():
                                                print(f"✅ FOUND POWERFUL ASSAULT SET: {gear_set}")
                                        
                                        if not gear_sets:
                                            print("❌ No gear sets processed - checking validation...")
                                        
                                    break
                        
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_dounata())
