"""
Enhanced Report Generator with Action Bar Integration.

This module extends the existing report generation to include action bar data
scraped from ESO Logs summary pages using the #summary-talents-0 table.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from .api_client import ESOLogsClient
from .bar_only_scraper import BarOnlyEncounterScraper
from .single_report_analyzer import SingleReportAnalyzer
from .models import TrialReport, LogRanking, EncounterResult, PlayerBuild, Role, Difficulty

logger = logging.getLogger(__name__)


class EnhancedReportGenerator:
    """
    Enhanced report generator that combines API data with web-scraped action bars.
    
    This generator:
    1. Uses the existing API client to get player builds and encounter data
    2. Enhances player data with action bars scraped from summary pages
    3. Generates comprehensive reports with both gear and ability information
    """
    
    def __init__(self, headless: bool = True, timeout_per_player: int = 20, max_players: int = 12):
        """
        Initialize the enhanced report generator.
        
        Args:
            headless: Whether to run browser in headless mode
            timeout_per_player: Timeout in seconds per player for bar scraping
            max_players: Maximum number of players to process per encounter
        """
        self.api_client = ESOLogsClient()
        self.analyzer = SingleReportAnalyzer()
        self.bar_scraper = BarOnlyEncounterScraper(headless=headless)
        self.timeout_per_player = timeout_per_player
        self.max_players = max_players
        
    async def generate_enhanced_report(self, report_code: str, 
                                     include_action_bars: bool = True) -> TrialReport:
        """
        Generate an enhanced trial report with action bar data.
        
        Args:
            report_code: The ESO Logs report code
            include_action_bars: Whether to scrape and include action bar data
            
        Returns:
            Enhanced TrialReport with action bar data
        """
        logger.info(f"Generating enhanced report for: {report_code}")
        
        # Get basic encounter data using existing API client
        logger.info("Fetching encounter data from API...")
        encounters = await self.analyzer._extract_encounters_with_players(
            self.api_client, report_code, {}
        )
        
        if not encounters:
            logger.warning("No encounters found in report")
            return TrialReport(trial_name="Unknown Trial", zone_id=0)
        
        # Enhance encounters with action bar data if requested
        if include_action_bars:
            logger.info("Enhancing encounters with action bar data...")
            await self._enhance_encounters_with_action_bars(report_code, encounters)
        
        # Create trial report
        trial_report = TrialReport(
            trial_name=encounters[0].encounter_name if encounters else "Unknown Trial",
            zone_id=0  # Would need to be determined from report data
        )
        
        # Create a single ranking with all encounters
        ranking = LogRanking(
            rank=1,
            log_url=f"https://www.esologs.com/reports/{report_code}",
            log_code=report_code,
            score=0.0,
            encounters=encounters
        )
        
        trial_report.add_ranking(ranking)
        
        logger.info(f"Generated enhanced report with {len(encounters)} encounters")
        return trial_report
    
    async def _enhance_encounters_with_action_bars(self, report_code: str, 
                                                  encounters: List[EncounterResult]) -> None:
        """
        Enhance encounters with action bar data scraped from summary pages.
        
        Args:
            report_code: The ESO Logs report code
            encounters: List of encounters to enhance
        """
        for encounter in encounters:
            logger.info(f"Enhancing encounter: {encounter.encounter_name}")
            
            # Get fight ID for this encounter (would need to be stored in encounter)
            # For now, we'll assume we can derive it or use a default
            fight_id = await self._get_fight_id_for_encounter(report_code, encounter)
            
            if not fight_id:
                logger.warning(f"Could not determine fight ID for encounter: {encounter.encounter_name}")
                continue
            
            # Scrape action bars for this encounter
            try:
                bars_output = await self.bar_scraper.scrape_encounter_bars(
                    report_code, fight_id, 
                    max_players=self.max_players,
                    timeout_per_player=self.timeout_per_player
                )
                
                # Parse the bars output and update player abilities
                self._parse_and_update_player_abilities(encounter, bars_output)
                
            except Exception as e:
                logger.error(f"Error scraping action bars for encounter {encounter.encounter_name}: {e}")
                continue
    
    async def _get_fight_id_for_encounter(self, report_code: str, 
                                        encounter: EncounterResult) -> Optional[int]:
        """
        Get the fight ID for an encounter.
        
        This is a simplified implementation - in practice, you'd need to store
        fight IDs in the encounter data or derive them from the API response.
        
        Args:
            report_code: The ESO Logs report code
            encounter: The encounter to get fight ID for
            
        Returns:
            Fight ID or None if not found
        """
        # This is a placeholder - in practice, you'd need to:
        # 1. Store fight_id in EncounterResult model, or
        # 2. Query the API to get fight IDs for encounters
        # For now, we'll use a default fight ID (1) for testing
        
        logger.debug(f"Using default fight ID 1 for encounter: {encounter.encounter_name}")
        return 1
    
    def _parse_and_update_player_abilities(self, encounter: EncounterResult, 
                                         bars_output: str) -> None:
        """
        Parse the bars output and update player abilities in the encounter.
        
        Args:
            encounter: The encounter to update
            bars_output: The scraped bars output string
        """
        lines = bars_output.strip().split('\n')
        current_player = None
        
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith('Encounter:') or line.startswith('='):
                continue
            
            # Check if this line is a player name (no colon)
            if ':' not in line:
                current_player = line
                continue
            
            # Parse bar1: and bar2: lines
            if line.startswith('bar1:'):
                bar1_abilities = line.replace('bar1:', '').strip()
                if current_player:
                    self._update_player_abilities(encounter, current_player, 'bar1', bar1_abilities)
            
            elif line.startswith('bar2:'):
                bar2_abilities = line.replace('bar2:', '').strip()
                if current_player:
                    self._update_player_abilities(encounter, current_player, 'bar2', bar2_abilities)
    
    def _update_player_abilities(self, encounter: EncounterResult, player_name: str, 
                               bar_type: str, abilities_str: str) -> None:
        """
        Update a specific player's abilities in the encounter.
        
        Args:
            encounter: The encounter containing the player
            player_name: The name of the player to update
            bar_type: Either 'bar1' or 'bar2'
            abilities_str: Comma-separated list of ability names
        """
        # Find the player in the encounter
        player = None
        for p in encounter.players:
            if p.name == player_name:
                player = p
                break
        
        if not player:
            logger.debug(f"Player not found in encounter: {player_name}")
            return
        
        # Parse abilities (split by comma and clean up)
        abilities = [ability.strip() for ability in abilities_str.split(',') if ability.strip()]
        
        # Update the player's abilities
        player.abilities[bar_type] = abilities
        
        logger.debug(f"Updated {player_name} {bar_type}: {abilities}")


async def generate_enhanced_report(report_code: str, 
                                 include_action_bars: bool = True,
                                 headless: bool = True,
                                 timeout_per_player: int = 20,
                                 max_players: int = 12) -> TrialReport:
    """
    Convenience function to generate an enhanced report with action bars.
    
    Args:
        report_code: The ESO Logs report code
        include_action_bars: Whether to scrape and include action bar data
        headless: Whether to run browser in headless mode
        timeout_per_player: Timeout in seconds per player for bar scraping
        max_players: Maximum number of players to process per encounter
        
    Returns:
        Enhanced TrialReport with action bar data
    """
    generator = EnhancedReportGenerator(
        headless=headless,
        timeout_per_player=timeout_per_player,
        max_players=max_players
    )
    
    return await generator.generate_enhanced_report(report_code, include_action_bars)
