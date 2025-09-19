#!/usr/bin/env python3
"""
Test script for real ESO Logs API integration.

This script tests the complete system against the real ESO Logs API
to generate actual trial reports with real player data.
"""

import asyncio
import logging
import os
from src.eso_builds.api_client import ESOLogsClient
from src.eso_builds.report_generator import ReportGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_real_api_connection():
    """Test connection to real ESO Logs API."""
    print("🔌 Testing Real ESO Logs API Connection")
    print("=" * 50)
    
    try:
        async with ESOLogsClient() as client:
            print("✅ API client connected successfully")
            
            # Get available trials
            trials = await client.get_available_trials()
            print(f"📊 Found {len(trials)} trials available")
            
            # Show some trial options
            print("\nAvailable Trials:")
            for trial in trials[:10]:  # Show first 10
                print(f"  - {trial['name']} (ID: {trial['id']}) - {len(trial['encounters'])} encounters")
            
            return trials
            
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return None


async def test_real_trial_report(trial_id: int, trial_name: str):
    """Test generating a real trial report."""
    print(f"\n🏆 Testing Real Trial Report: {trial_name}")
    print("=" * 50)
    
    try:
        async with ESOLogsClient() as client:
            # Get top rankings for this trial
            print(f"📈 Getting top rankings for {trial_name}...")
            rankings = await client.get_top_rankings_for_trial(trial_id, limit=3)
            
            if not rankings:
                print(f"⚠️ No rankings found for {trial_name}")
                return False
            
            print(f"✅ Found {len(rankings)} rankings")
            
            # Show ranking info
            for ranking in rankings:
                print(f"  Rank {ranking['rank']}: {ranking['code']} (Score: {ranking['score']:.1f})")
                if ranking['guild_name']:
                    print(f"    Guild: {ranking['guild_name']}")
            
            # Test encounter details for first ranking
            if rankings:
                first_ranking = rankings[0]
                print(f"\n⚔️ Getting encounter details for {first_ranking['code']}...")
                
                encounters = await client.get_encounter_details(first_ranking['code'])
                print(f"✅ Found {len(encounters)} encounters")
                
                for encounter in encounters:
                    print(f"  - {encounter.encounter_name} ({encounter.difficulty.value})")
                    print(f"    Players: {len(encounter.tanks)} tanks, {len(encounter.healers)} healers, {len(encounter.dps)} dps")
                    
                    # Show first few players as example
                    if encounter.players:
                        print("    Sample players:")
                        for player in encounter.players[:3]:
                            gear_summary = f"{len(player.gear_sets)} sets" if player.gear_sets else "no gear data"
                            print(f"      {player.name} ({player.character_class}, {player.role.value}) - {gear_summary}")
            
            return True
            
    except Exception as e:
        print(f"❌ Real trial report test failed: {e}")
        return False


async def generate_real_report():
    """Generate a complete real report."""
    print(f"\n📋 Generating Complete Real Report")
    print("=" * 50)
    
    generator = ReportGenerator()
    
    # Try to generate real reports for popular trials
    trial_targets = [
        (19, "Ossein Cage"),  # Most recent trial
        (18, "Lucent Citadel"),
        (17, "Sanity's Edge")
    ]
    
    for zone_id, trial_name in trial_targets:
        print(f"\n🎯 Generating real report for {trial_name}...")
        
        try:
            # Generate with real API
            trial_report = await generator.generate_trial_report(trial_name, zone_id, use_real_api=True)
            
            print(f"✅ Generated report with {len(trial_report.rankings)} rankings")
            
            # Save markdown report
            os.makedirs("real_reports", exist_ok=True)
            markdown_file = generator.save_markdown_report(trial_report, "real_reports")
            print(f"💾 Saved real report to: {markdown_file}")
            
            # Show preview of first encounter
            if trial_report.rankings and trial_report.rankings[0].encounters:
                first_encounter = trial_report.rankings[0].encounters[0]
                print(f"\n📊 Preview of {first_encounter.encounter_name}:")
                print(f"  Team: {len(first_encounter.tanks)} tanks, {len(first_encounter.healers)} healers, {len(first_encounter.dps)} dps")
                
                # Show first tank as example
                if first_encounter.tanks:
                    tank = first_encounter.tanks[0]
                    gear_str = ", ".join(str(g) for g in tank.gear_sets) if tank.gear_sets else "no gear data"
                    print(f"  Tank 1 @{tank.name}: {tank.character_class}, {gear_str}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to generate real report for {trial_name}: {e}")
            return False


async def main():
    """Main test function."""
    print("🚀 Real ESO Logs API Integration Test")
    print("=" * 60)
    
    # Check if credentials are available
    if not os.getenv('ESOLOGS_ID') or not os.getenv('ESOLOGS_SECRET'):
        print("❌ ESO Logs API credentials not found!")
        print("Please set ESOLOGS_ID and ESOLOGS_SECRET environment variables")
        print("or create a .env file with your credentials.")
        return
    
    # Test API connection
    trials = await test_real_api_connection()
    if not trials:
        return
    
    # Find Ossein Cage for testing
    ossein_cage = next((t for t in trials if "Ossein Cage" in t['name']), None)
    if ossein_cage:
        success = await test_real_trial_report(ossein_cage['id'], ossein_cage['name'])
        if success:
            # Generate complete real reports
            await generate_real_report()
    else:
        print("⚠️ Ossein Cage not found in trials list")
    
    print("\n🎉 Real API integration test complete!")
    print("Check 'real_reports/' directory for actual ESO Logs data!")


if __name__ == "__main__":
    asyncio.run(main())
