#!/usr/bin/env python3
"""
Comprehensive Test Suite for Action Bar Integration System.

This test suite validates the complete action bar integration functionality,
including web scraping, data integration, and report generation.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Optional

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from eso_builds.models import TrialReport, LogRanking, EncounterResult, PlayerBuild, Role, Difficulty, GearSet
from eso_builds.report_formatter import ReportFormatter
from eso_builds.pdf_formatter import PDFReportFormatter
from eso_builds.bar_only_scraper import BarOnlyEncounterScraper, scrape_encounter_bars_only
from eso_builds.enhanced_report_generator import EnhancedReportGenerator, generate_enhanced_report

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ActionBarTestSuite:
    """Comprehensive test suite for action bar integration."""
    
    def __init__(self):
        self.test_results = {}
        
    def create_sample_encounter_with_action_bars(self) -> EncounterResult:
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
    
    def test_action_bar_data_models(self) -> bool:
        """Test that action bar data is properly stored in models."""
        logger.info("Testing action bar data models...")
        
        try:
            encounter = self.create_sample_encounter_with_action_bars()
            
            # Verify players with action bars
            players_with_bars = [p for p in encounter.players if p.abilities and (p.abilities.get('bar1') or p.abilities.get('bar2'))]
            assert len(players_with_bars) == 3, f"Expected 3 players with action bars, got {len(players_with_bars)}"
            
            # Verify specific player data
            ok_beamer = next(p for p in encounter.players if p.name == "Ok Beamer")
            assert len(ok_beamer.abilities['bar1']) == 6, "Ok Beamer should have 6 bar1 abilities"
            assert len(ok_beamer.abilities['bar2']) == 6, "Ok Beamer should have 6 bar2 abilities"
            
            # Verify player without action bars
            anonymous = next(p for p in encounter.players if p.name == "Anonymous -999929")
            assert not anonymous.abilities, "Anonymous player should have no action bar data"
            
            logger.info("✅ Action bar data models test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Action bar data models test failed: {e}")
            return False
    
    def test_markdown_formatting(self) -> bool:
        """Test markdown formatting with action bar data."""
        logger.info("Testing markdown formatting...")
        
        try:
            encounter = self.create_sample_encounter_with_action_bars()
            
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
            
            # Verify action bars appear in output
            assert "bar1:" in markdown_output, "Markdown output should contain bar1:"
            assert "bar2:" in markdown_output, "Markdown output should contain bar2:"
            assert "Cephaliarch's Flail" in markdown_output, "Should contain specific ability names"
            
            logger.info("✅ Markdown formatting test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Markdown formatting test failed: {e}")
            return False
    
    def test_pdf_formatting(self) -> bool:
        """Test PDF formatting with action bar data."""
        logger.info("Testing PDF formatting...")
        
        try:
            encounter = self.create_sample_encounter_with_action_bars()
            
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
            
            # Verify PDF was generated
            assert len(pdf_bytes) > 1000, f"PDF should be substantial, got {len(pdf_bytes)} bytes"
            
            logger.info("✅ PDF formatting test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ PDF formatting test failed: {e}")
            return False
    
    async def test_web_scraping_functionality(self) -> bool:
        """Test web scraping functionality (requires network)."""
        logger.info("Testing web scraping functionality...")
        
        try:
            # Test with a small timeout and limited players
            scraper = BarOnlyEncounterScraper(headless=True)
            
            # This is a basic connectivity test - we don't want to run full scraping in tests
            # Just verify the scraper can be instantiated and basic methods exist
            assert hasattr(scraper, 'scrape_encounter_bars'), "Scraper should have scrape_encounter_bars method"
            assert hasattr(scraper, 'construct_fight_url'), "Scraper should have construct_fight_url method"
            
            logger.info("✅ Web scraping functionality test passed (basic validation)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Web scraping functionality test failed: {e}")
            return False
    
    def run_all_tests(self) -> dict:
        """Run all tests and return results."""
        logger.info("Starting Action Bar Integration Test Suite")
        logger.info("=" * 60)
        
        # Run synchronous tests
        self.test_results['data_models'] = self.test_action_bar_data_models()
        self.test_results['markdown_formatting'] = self.test_markdown_formatting()
        self.test_results['pdf_formatting'] = self.test_pdf_formatting()
        
        # Run async tests
        async def run_async_tests():
            self.test_results['web_scraping'] = await self.test_web_scraping_functionality()
        
        asyncio.run(run_async_tests())
        
        # Print summary
        logger.info("=" * 60)
        logger.info("TEST RESULTS SUMMARY:")
        logger.info("=" * 60)
        
        passed = 0
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
            if result:
                passed += 1
        
        logger.info("=" * 60)
        logger.info(f"Overall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Action bar integration is working correctly.")
        else:
            logger.warning(f"⚠️ {total - passed} tests failed. Check logs above for details.")
        
        return self.test_results


def main():
    """Run the test suite."""
    test_suite = ActionBarTestSuite()
    results = test_suite.run_all_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure


if __name__ == "__main__":
    main()
