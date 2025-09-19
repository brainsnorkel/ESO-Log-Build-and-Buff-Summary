#!/usr/bin/env python3
"""
Debug script to understand player data extraction from ESO Logs API.
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

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def debug_player_data():
    """Debug player data extraction."""
    print("🔍 Debugging Player Data Extraction")
    print("=" * 40)
    
    report_code = "mtFqVzQPNBcCrd1h"
    
    try:
        async with ESOLogsClient() as client:
            # Get report details first
            report_response = await client._make_request("get_report_by_code", code=report_code)
            report = report_response.report_data.report
            
            print(f"📊 Report: {report.title}")
            print(f"🏰 Zone: {report.zone.name}")
            print(f"⏱️  Duration: {(report.end_time - report.start_time) / 1000 / 60:.1f} minutes")
            print(f"⚔️  Total Fights: {len(report.fights)}")
            
            # Find a boss fight to test
            boss_fight = None
            for fight in report.fights:
                if hasattr(fight, 'difficulty') and fight.difficulty is not None:
                    if "Hall of Fleshcraft" in fight.name:
                        boss_fight = fight
                        break
            
            if boss_fight:
                print(f"\n🎯 Testing with fight: {boss_fight.name} (ID: {boss_fight.id})")
                print(f"   Difficulty: {boss_fight.difficulty}")
                print(f"   Duration: {(boss_fight.end_time - boss_fight.start_time) / 1000:.1f} seconds")
                
                # Test different approaches to get player data
                print("\n📊 Trying get_report_table with time range...")
                try:
                    table_data = await client._make_request(
                        "get_report_table",
                        code=report_code,
                        start_time=int(boss_fight.start_time),
                        end_time=int(boss_fight.end_time),
                        data_type="Summary",
                        hostility_type="Friendlies"
                    )
                    
                    print(f"✅ Table data received: {type(table_data)}")
                    if hasattr(table_data, 'data'):
                        print(f"   Has data: {type(table_data.data)}")
                        if hasattr(table_data.data, 'entries'):
                            print(f"   Entries: {len(table_data.data.entries)}")
                            
                            # Show first few entries
                            for i, entry in enumerate(table_data.data.entries[:5]):
                                print(f"   Player {i+1}: {getattr(entry, 'name', 'Unknown')} ({getattr(entry, 'type', 'Unknown')})")
                        else:
                            print(f"   Data structure: {table_data.data}")
                    else:
                        print(f"   Structure: {table_data}")
                        
                except Exception as e:
                    print(f"❌ get_report_table failed: {e}")
                
                # Try alternative: get_report_rankings
                print("\n📊 Trying get_report_rankings...")
                try:
                    rankings_data = await client._make_request(
                        "get_report_rankings",
                        code=report_code,
                        fight_ids=[boss_fight.id],
                        metric="dps"
                    )
                    print(f"✅ Rankings data: {type(rankings_data)}")
                    print(f"   Structure: {rankings_data}")
                    
                except Exception as e:
                    print(f"❌ get_report_rankings failed: {e}")
                
                # Try get_report_events
                print("\n📊 Trying get_report_events...")
                try:
                    events_data = await client._make_request(
                        "get_report_events",
                        code=report_code,
                        start_time=int(boss_fight.start_time),
                        end_time=int(boss_fight.end_time),
                        limit=10
                    )
                    print(f"✅ Events data: {type(events_data)}")
                    
                except Exception as e:
                    print(f"❌ get_report_events failed: {e}")
            
            else:
                print("❌ No boss fight found for testing")
                
    except Exception as e:
        print(f"❌ Debug failed: {e}")


async def main():
    """Main debug function."""
    await debug_player_data()


if __name__ == "__main__":
    asyncio.run(main())
