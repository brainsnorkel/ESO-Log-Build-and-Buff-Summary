#!/usr/bin/env python3
"""
Simple test to verify that includeCombatantInfo=True provides abilities data
"""

import asyncio
import os
from src.eso_builds.api_client import ESOLogsClient

async def test_api_abilities():
    """Test if the API with includeCombatantInfo=True provides abilities"""
    
    # Load API credentials from environment
    client_id = os.getenv('ESOLOGS_ID')
    client_secret = os.getenv('ESOLOGS_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Missing API credentials")
        return
    
    async with ESOLogsClient(client_id=client_id, client_secret=client_secret) as client:
        try:
            # Test with a known report
            report_code = "N37HBwrjQGYJ6mbv"
            
            # Get report master data to find fights
            master_data = await client.get_report_master_data(report_code)
            if not master_data:
                print("❌ No master data found")
                return
                
            # Handle both dict and object responses
            if isinstance(master_data, dict):
                fights = master_data.get('fights', [])
            else:
                fights = getattr(master_data, 'fights', [])
                
            if not fights:
                print("❌ No fights found")
                return
                
            # Use the first fight
            fight = fights[0]
            
            # Handle both dict and object fight data
            if isinstance(fight, dict):
                fight_name = fight.get('name', 'Unknown')
                fight_id = fight.get('id', 0)
                start_time = fight.get('startTime', 0)
                end_time = fight.get('endTime', 0)
            else:
                fight_name = getattr(fight, 'name', 'Unknown')
                fight_id = getattr(fight, 'id', 0)
                start_time = getattr(fight, 'startTime', 0)
                end_time = getattr(fight, 'endTime', 0)
                
            print(f"🔍 Testing fight: {fight_name} (ID: {fight_id})")
            
            # Test the API call that's already working in our system
            print("\n📊 Testing API call with includeCombatantInfo=True...")
            
            # This is the same call that's already working in our system
            table_data = await client._make_request(
                "get_report_table",
                code=report_code,
                start_time=int(start_time),
                end_time=int(end_time),
                data_type="Summary",
                hostility_type="Friendlies",
                includeCombatantInfo=True
            )
            
            print(f"✅ API call successful: {type(table_data)}")
            
            # Check if we got player details with combatant info
            if table_data and hasattr(table_data, 'report_data') and hasattr(table_data.report_data, 'report'):
                report = table_data.report_data.report
                if hasattr(report, 'table'):
                    table = report.table
                    if isinstance(table, dict) and 'data' in table:
                        data = table['data']
                        if isinstance(data, dict) and 'data' in data:
                            final_data = data['data']
                            
                            if 'playerDetails' in final_data:
                                player_details = final_data['playerDetails']
                                print(f"📊 Found {len(player_details)} player details")
                                
                                if player_details:
                                    first_player = player_details[0]
                                    print(f"📋 First player type: {type(first_player)}")
                                    
                                    if isinstance(first_player, dict):
                                        print(f"🔍 Player keys: {list(first_player.keys())}")
                                        
                                        # Check for combatant info
                                        if 'combatantInfo' in first_player:
                                            combatant_info = first_player['combatantInfo']
                                            print(f"⚔️ Combatant info found!")
                                            print(f"📊 Combatant info keys: {list(combatant_info.keys()) if isinstance(combatant_info, dict) else 'Not a dict'}")
                                            
                                            # Look for abilities or gear data
                                            if isinstance(combatant_info, dict):
                                                for key, value in combatant_info.items():
                                                    print(f"  {key}: {type(value)} - {str(value)[:100]}...")
                                        else:
                                            print("❌ No combatantInfo found in player data")
                                            print(f"📋 Available keys: {list(first_player.keys())}")
                                            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_abilities())
