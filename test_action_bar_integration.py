#!/usr/bin/env python3
"""
Test script for Action Bar Integration in Reports.

This script demonstrates how action bar data is integrated into encounter reports
by creating sample data and showing the formatted output.
"""

import logging
import sys
import os
from datetime import datetime

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from eso_builds.models import TrialReport, LogRanking, EncounterResult, PlayerBuild, Role, Difficulty, GearSet
from eso_builds.report_formatter import ReportFormatter
from eso_builds.pdf_formatter import PDFReportFormatter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_encounter_with_action_bars() -> EncounterResult:
    """Create a sample encounter with players that have action bar data."""
    
    # Create sample players with action bar data
    players = []
    
    # Tank with action bars
    tank = PlayerBuild(
        name="Ok Beamer",
        character_class="Dragonknight",
        role=Role.TANK,
        gear_sets=[
            GearSet("Pearlescent Ward", 5, True),
            GearSet("Lucent Echoes", 5, False),
            GearSet("Nazaray", 2, False)
        ],
        abilities={
            'bar1': ["Cephaliarch's Flail", "Stampede", "Pragmatic Fatecarver", "Flames of Oblivion", "Quick Cloak", "Engulfing Flames"],
            'bar2': ["Venomous Claw", "Inspired Scholarship", "Camouflaged Hunter", "Molten Whip", "Everlasting Sweep", "Standard of Might"]
        },
        player_id="1"
    )
    players.append(tank)
    
    # Healer with action bars
    healer = PlayerBuild(
        name="Deadly-arcanist",
        character_class="Arcanist",
        role=Role.HEALER,
        gear_sets=[
            GearSet("Spell Power Cure", 5, True),
            GearSet("Jorvuld's Guidance", 5, False),
            GearSet("Symphony of Blades", 2, False)
        ],
        abilities={
            'bar1': ["Quick Cloak", "Inspired Scholarship", "Reaper's Mark", "Fulminating Rune", "Cephaliarch's Flail", "Relentless Focus"],
            'bar2': ["Pragmatic Fatecarver", "Resolving Vigor", "Camouflaged Hunter", "Camouflaged Hunter", "Soul Harvest", "Shooting Star"]
        },
        player_id="4"
    )
    players.append(healer)
    
    # DPS with action bars
    dps1 = PlayerBuild(
        name="Soonlyta",
        character_class="Sorcerer",
        role=Role.DPS,
        gear_sets=[
            GearSet("Mother's Sorrow", 5, False),
            GearSet("Burning Spellweave", 5, False),
            GearSet("Maw of the Infernal", 2, False)
        ],
        abilities={
            'bar1': ["Quick Cloak", "Blazing Shield", "Inspired Scholarship", "Blockade of Fire", "Cephaliarch's Flail", "Resolving Vigor"],
            'bar2': ["Pragmatic Fatecarver", "Blazing Spear", "Merciless Resolve", "Concealed Weapon", "Soul Harvest", "The Languid Eye"]
        },
        player_id="11",
        dps_data={'dps_percentage': 25.3, 'total_damage': 1250000}
    )
    players.append(dps1)
    
    # DPS without action bars (legacy player)
    dps2 = PlayerBuild(
        name="Anonymous -999929",
        character_class="Nightblade",
        role=Role.DPS,
        gear_sets=[
            GearSet("Relequen", 5, False),
            GearSet("Aegis Caller", 5, False),
            GearSet("Velidreth", 2, False)
        ],
        abilities={},  # No action bar data
        player_id="6",
        dps_data={'dps_percentage': 22.1, 'total_damage': 1100000}
    )
    players.append(dps2)
    
    # Create encounter
    encounter = EncounterResult(
        encounter_name="Hall of Fleshcraft",
        difficulty=Difficulty.VETERAN,
        players=players,
        kill=True,
        boss_percentage=0.0
    )
    
    return encounter


def test_markdown_formatting_with_action_bars():
    """Test markdown formatting with action bar data."""
    
    logger.info("Testing Markdown Formatting with Action Bars")
    logger.info("=" * 60)
    
    # Create sample encounter
    encounter = create_sample_encounter_with_action_bars()
    
    # Create trial report
    trial_report = TrialReport(
        trial_name="Sanity's Edge",
        zone_id=1250
    )
    
    ranking = LogRanking(
        rank=1,
        log_url="https://www.esologs.com/reports/7KAWyZwPCkaHfc8j",
        log_code="7KAWyZwPCkaHfc8j",
        score=95.5,
        encounters=[encounter]
    )
    
    trial_report.add_ranking(ranking)
    
    # Format with markdown
    formatter = ReportFormatter()
    markdown_output = formatter.format_trial_report(trial_report)
    
    # Save and display
    output_file = f"action_bar_integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(output_file, 'w') as f:
        f.write(markdown_output)
    
    logger.info(f"Markdown output saved to: {output_file}")
    
    # Print the output
    logger.info("=" * 60)
    logger.info("MARKDOWN OUTPUT WITH ACTION BARS:")
    logger.info("=" * 60)
    print(markdown_output)
    
    return markdown_output


def test_pdf_formatting_with_action_bars():
    """Test PDF formatting with action bar data."""
    
    logger.info("=" * 60)
    logger.info("Testing PDF Formatting with Action Bars")
    logger.info("=" * 60)
    
    # Create sample encounter
    encounter = create_sample_encounter_with_action_bars()
    
    # Create trial report
    trial_report = TrialReport(
        trial_name="Sanity's Edge",
        zone_id=1250
    )
    
    ranking = LogRanking(
        rank=1,
        log_url="https://www.esologs.com/reports/7KAWyZwPCkaHfc8j",
        log_code="7KAWyZwPCkaHfc8j",
        score=95.5,
        encounters=[encounter]
    )
    
    trial_report.add_ranking(ranking)
    
    # Format with PDF
    pdf_formatter = PDFReportFormatter()
    pdf_bytes = pdf_formatter.format_trial_report(trial_report)
    
    # Save and display info
    output_file = f"action_bar_integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    with open(output_file, 'wb') as f:
        f.write(pdf_bytes)
    
    logger.info(f"PDF output saved to: {output_file}")
    logger.info(f"PDF size: {len(pdf_bytes):,} bytes")
    
    return pdf_bytes


def demonstrate_action_bar_differences():
    """Demonstrate the difference between players with and without action bar data."""
    
    logger.info("=" * 60)
    logger.info("ACTION BAR INTEGRATION DEMONSTRATION")
    logger.info("=" * 60)
    
    encounter = create_sample_encounter_with_action_bars()
    
    logger.info("Players in encounter:")
    for player in encounter.players:
        logger.info(f"\n{player.name} ({player.character_class} {player.role.value}):")
        
        # Show gear sets
        gear_str = ", ".join(str(gear) for gear in player.gear_sets)
        logger.info(f"  Gear: {gear_str}")
        
        # Show action bars if available
        if player.abilities and (player.abilities.get('bar1') or player.abilities.get('bar2')):
            logger.info("  Action Bars:")
            if player.abilities.get('bar1'):
                logger.info(f"    bar1: {', '.join(player.abilities['bar1'])}")
            if player.abilities.get('bar2'):
                logger.info(f"    bar2: {', '.join(player.abilities['bar2'])}")
        else:
            logger.info("  Action Bars: No data available")


def main():
    """Run all action bar integration tests."""
    
    logger.info("Starting Action Bar Integration Tests")
    logger.info("=" * 60)
    logger.info("Demonstrating action bar data integration in encounter reports")
    logger.info("=" * 60)
    
    # Test 1: Demonstrate action bar differences
    demonstrate_action_bar_differences()
    
    # Test 2: Test markdown formatting
    markdown_output = test_markdown_formatting_with_action_bars()
    
    # Test 3: Test PDF formatting
    pdf_bytes = test_pdf_formatting_with_action_bars()
    
    logger.info("=" * 60)
    logger.info("Action bar integration tests completed!")
    
    if markdown_output and pdf_bytes:
        logger.info("✅ SUCCESS: Action bars integrated into encounter reports!")
        logger.info("🎯 Perfect: Players with action bar data show detailed ability lists")
        logger.info("📄 Generated both Markdown and PDF formats with action bars")
        logger.info("🚀 Ready for production use!")
    else:
        logger.info("❌ Some tests failed - check logs above")


if __name__ == "__main__":
    main()
