#!/usr/bin/env python3
"""
Test the ReportMasterData approach to get actual abilities from the log.
"""

import asyncio
import sys
from dotenv import load_dotenv

# Add src to path and load env
sys.path.append('src')
load_dotenv()

from src.eso_builds.api_client import ESOLogsClient

async def test_master_data():
    """Test getting master data from a report."""
    print("🔍 Testing ReportMasterData abilities extraction")
    print("=" * 60)
    
    async with ESOLogsClient() as client:
        try:
            report_code = "mtFqVzQPNBcCrd1h"
            
            print(f"📡 Fetching master data for report {report_code}...")
            master_data = await client.get_report_master_data(report_code)
            
            abilities = master_data.get('abilities', [])
            actors = master_data.get('actors', [])
            
            print(f"✅ Master data retrieved!")
            print(f"🎯 Found {len(abilities)} abilities")
            print(f"👥 Found {len(actors)} players")
            
            if abilities:
                print(f"\n📋 Sample Abilities (first 20):")
                for i, ability in enumerate(abilities[:20]):
                    name = ability.get('name', 'Unknown')
                    game_id = ability.get('gameID', 'Unknown')
                    ability_type = ability.get('type', 'Unknown')
                    print(f"  {i+1}. {name} (ID: {game_id}, Type: {ability_type})")
                
                # Look for common ESO abilities
                print(f"\n🔍 Looking for common DPS abilities...")
                dps_abilities = []
                for ability in abilities:
                    name = ability.get('name', '')
                    if any(keyword in name.lower() for keyword in ['crystal', 'force', 'elemental', 'flame', 'shock', 'ice', 'whip', 'claw']):
                        dps_abilities.append(name)
                
                if dps_abilities:
                    print(f"🗡️ DPS Abilities Found ({len(dps_abilities)}):")
                    for ability in dps_abilities[:10]:
                        print(f"  • {ability}")
                else:
                    print("❌ No recognizable DPS abilities found")
            else:
                print("❌ No abilities found in master data")
            
            if actors:
                print(f"\n👥 Sample Players:")
                for i, actor in enumerate(actors[:10]):
                    name = actor.get('name', 'Unknown')
                    actor_type = actor.get('type', 'Unknown')
                    sub_type = actor.get('subType', 'Unknown')
                    print(f"  {i+1}. {name} (Type: {actor_type}, SubType: {sub_type})")
            else:
                print("❌ No player actors found in master data")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_master_data())
