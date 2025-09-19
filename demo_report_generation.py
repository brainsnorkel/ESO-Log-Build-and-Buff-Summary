#!/usr/bin/env python3
"""
Demo script showing complete report generation.

This script demonstrates the full report generation process with
realistic sample data, showing both console and markdown output.
"""

import asyncio
import logging
from src.eso_builds.report_generator import ReportGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_report_generation():
    """Demonstrate complete report generation."""
    print("🚀 ESO Top Builds - Report Generation Demo")
    print("=" * 60)
    
    generator = ReportGenerator()
    
    # Generate sample reports for multiple trials
    trials = [
        ("Ossein Cage", 19),
        ("Lucent Citadel", 18),
        ("Sanity's Edge", 17)
    ]
    
    for trial_name, zone_id in trials:
        print(f"\n📊 Generating report for: {trial_name}")
        print("-" * 40)
        
        # Generate the trial report
        trial_report = await generator.generate_trial_report(trial_name, zone_id)
        
        print(f"✅ Generated report with {len(trial_report.rankings)} rankings")
        print(f"📅 Generated at: {trial_report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show console output (first ranking only for brevity)
        console_output = generator.format_console_report(trial_report)
        console_lines = console_output.split('\n')
        
        print("\n📝 Console Output Preview (First Ranking):")
        print("=" * 50)
        
        # Show first ranking only
        in_first_ranking = False
        line_count = 0
        for line in console_lines:
            if line.startswith("Rank 1:"):
                in_first_ranking = True
            elif line.startswith("Rank 2:"):
                break
            
            if in_first_ranking:
                print(line)
                line_count += 1
                if line_count > 25:  # Limit output for demo
                    print("... (truncated for demo)")
                    break
        
        # Save markdown report
        print(f"\n💾 Saving markdown report...")
        markdown_file = generator.save_markdown_report(trial_report, "reports")
        print(f"✅ Saved to: {markdown_file}")
        
        # Show markdown preview
        markdown_output = generator.format_markdown_report(trial_report)
        markdown_lines = markdown_output.split('\n')
        
        print(f"\n📋 Markdown Preview (First 20 lines):")
        print("=" * 50)
        for i, line in enumerate(markdown_lines[:20]):
            print(line)
        print("... (see full file for complete report)")
        
        print(f"\n" + "="*60)


def show_sample_encounter():
    """Show what a single encounter looks like in detail."""
    print("\n🔍 Detailed Encounter Example")
    print("=" * 40)
    
    sample_encounter = """
Encounter: Hall of Fleshcraft Veteran Hard Mode
Tank 1: Dragonknight, 5pc Perfected Pearlescent Ward, 5pc Lucent Echoes, 2pc Nazaray
Tank 2: Templar, 5pc Saxhleel Champion, 5pc Powerful Assault, 2pc Lord Warden
Healer 1: Arcanist, 5pc Perfected Spell Power Cure, 5pc Jorvuld's Guidance, 2pc Symphony of Blades
Healer 2: Warden, 5pc Hollowfang Thirst, 5pc Worm's Raiment, 2pc Sentinel of Rkugamz
DPS 1: Necromancer, 5pc Perfected Relequen, 5pc Kinras's Wrath, 2pc Slimecraw
DPS 2: Dragonknight, 5pc Perfected Bahsei's Mania, 5pc Coral Riptide, 2pc Kjalnar's Nightmare
DPS 3: Sorcerer, 5pc Perfected Ansuul's Torment, 5pc Sul-Xan's Torment, 2pc Grundwulf
DPS 4: Nightblade, 5pc Pillar of Nirn, 5pc Perfected Relequen, 2pc Selene
DPS 5: Templar, 5pc Deadly Strike, 5pc Kinras's Wrath, 2pc Kra'gh
DPS 6: Arcanist, 5pc Perfected Coral Riptide, 5pc Pillar of Nirn, 2pc Slimecraw
DPS 7: Warden, 5pc Perfected Relequen, 5pc Tzogvin's Warband, 2pc Velidreth
DPS 8: Necromancer, 5pc Perfected Bahsei's Mania, 5pc Ansuul's Torment, 2pc Zaan
    """
    
    print(sample_encounter.strip())


async def main():
    """Main demo function."""
    # Create reports directory
    import os
    os.makedirs("reports", exist_ok=True)
    
    # Show detailed encounter example first
    show_sample_encounter()
    
    # Run the full demo
    await demo_report_generation()
    
    print("\n🎉 Demo Complete!")
    print("\nWhat you just saw:")
    print("✅ Complete trial reports with 5 rankings each")
    print("✅ Realistic ESO builds with proper gear combinations")
    print("✅ Both console and markdown output formats")
    print("✅ Automatic file saving with timestamps")
    print("✅ Professional formatting with tables and links")
    print("\nCheck the 'reports/' directory for the generated markdown files!")


if __name__ == "__main__":
    asyncio.run(main())
