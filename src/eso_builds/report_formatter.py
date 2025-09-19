"""
Report formatting for ESO Top Builds.

This module handles formatting the trial reports into the exact output format
specified in the project overview.
"""

import logging
from typing import List
from .models import TrialReport, LogRanking, EncounterResult, PlayerBuild, Role

logger = logging.getLogger(__name__)


class ReportFormatter:
    """Formats trial reports into the specified output format."""
    
    def format_trial_report(self, trial_report: TrialReport) -> str:
        """Format a complete trial report."""
        lines = []
        
        # Trial header
        lines.append(trial_report.trial_name)
        
        # Process each ranking
        for ranking in trial_report.rankings:
            lines.extend(self._format_ranking(ranking))
            lines.append("")  # Empty line between rankings
        
        return "\n".join(lines)
    
    def _format_ranking(self, ranking: LogRanking) -> List[str]:
        """Format a single ranking with all its encounters."""
        lines = []
        
        # Ranking header
        lines.append(f"Rank {ranking.rank}: {ranking.log_url}")
        
        # Process each encounter
        for encounter in ranking.encounters:
            lines.extend(self._format_encounter(encounter))
        
        return lines
    
    def _format_encounter(self, encounter: EncounterResult) -> List[str]:
        """Format a single encounter with all player builds."""
        lines = []
        
        # Encounter header
        encounter_title = f"Encounter: {encounter.encounter_name}"
        if encounter.difficulty.value != "Normal":
            encounter_title += f" {encounter.difficulty.value}"
        lines.append(encounter_title)
        
        # Sort players by role: Tanks, Healers, DPS
        tanks = encounter.tanks
        healers = encounter.healers  
        dps = encounter.dps
        
        # Format tanks
        for i, tank in enumerate(tanks, 1):
            lines.append(f"Tank {i}: {self._format_player_build(tank)}")
        
        # Format healers
        for i, healer in enumerate(healers, 1):
            lines.append(f"Healer {i}: {self._format_player_build(healer)}")
        
        # Format DPS
        for i, dps_player in enumerate(dps, 1):
            lines.append(f"DPS {i}: {self._format_player_build(dps_player)}")
        
        # Add empty DPS slots if fewer than 8
        for i in range(len(dps) + 1, 9):
            lines.append(f"DPS {i}: ")
        
        lines.append("")  # Empty line after encounter
        return lines
    
    def _format_player_build(self, player: PlayerBuild) -> str:
        """Format a single player's build."""
        if not player.gear_sets:
            return f"{player.character_class}, (no gear data)"
        
        gear_str = ", ".join(str(gear) for gear in player.gear_sets)
        return f"{player.character_class}, {gear_str}"
    
    def format_multiple_trials(self, trial_reports: List[TrialReport]) -> str:
        """Format multiple trial reports."""
        formatted_reports = []
        
        for trial_report in trial_reports:
            formatted_reports.append(self.format_trial_report(trial_report))
        
        return "\n\n".join(formatted_reports)
