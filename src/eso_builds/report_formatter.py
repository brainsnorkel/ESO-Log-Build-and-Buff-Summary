"""
Report formatting for ESO Logs Build and Buff Summary.

This module handles formatting the trial reports into the exact output format
specified in the project overview.
"""

import logging
from typing import List
from .models import TrialReport, LogRanking, EncounterResult, PlayerBuild, Role

logger = logging.getLogger(__name__)


class ReportFormatter:
    """Formats trial reports into the specified output format."""
    
    # Class name mapping for shorter display names
    CLASS_MAPPING = {
        'Arcanist': 'Arc',
        'Sorceror': 'Sorc',
        'DragonKnight': 'DK',
        'Necromancer': 'Cro',
        'Templar': 'Plar',
        'Warden': 'Warden',
        'Nightblade': 'NB'
    }
    
    # Role icons for visual identification
    ROLE_ICONS = {
        Role.TANK: '🛡️',
        Role.HEALER: '💚',
        Role.DPS: '⚔️'
    }
    
    def _get_class_display_name(self, class_name: str) -> str:
        """Get the shortened display name for a class."""
        return self.CLASS_MAPPING.get(class_name, class_name)
    
    def _get_anonymous_name(self, original_name: str, name_counter: dict) -> str:
        """Generate an anonymous name for a player."""
        if original_name not in name_counter:
            name_counter[original_name] = len(name_counter) + 1
        return f"anon{name_counter[original_name]}"
    
    def format_trial_report(self, trial_report: TrialReport, anonymize: bool = False) -> str:
        """Format a complete trial report."""
        lines = []
        
        # Trial header
        lines.append(trial_report.trial_name)
        
        # Process each ranking
        for ranking in trial_report.rankings:
            lines.extend(self._format_ranking(ranking, anonymize=anonymize))
            lines.append("")  # Empty line between rankings
        
        return "\n".join(lines)
    
    def _format_ranking(self, ranking: LogRanking, anonymize: bool = False) -> List[str]:
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
        for tank in tanks:
            role_icon = self.ROLE_ICONS.get(tank.role, '')
            lines.append(f"{role_icon} {tank.name}: {self._format_player_build_without_name(tank)}")
        
        # Format healers
        for healer in healers:
            role_icon = self.ROLE_ICONS.get(healer.role, '')
            lines.append(f"{role_icon} {healer.name}: {self._format_player_build_without_name(healer)}")
        
        # Format DPS
        for dps_player in dps:
            role_icon = self.ROLE_ICONS.get(dps_player.role, '')
            lines.append(f"{role_icon} {dps_player.name}: {self._format_player_build_without_name(dps_player)}")
        
        lines.append("")  # Empty line after encounter
        return lines
    
    def _format_player_build(self, player: PlayerBuild) -> str:
        """Format a single player's build."""
        if not player.gear_sets:
            return f"{player.character_class}, (no gear data)"
        
        gear_str = ", ".join(str(gear) for gear in player.gear_sets)
        
        # Add action bar information if available
        action_bars_info = self._format_action_bars(player)
        if action_bars_info:
            return f"{player.character_class}, {gear_str}\n{action_bars_info}"
        
        return f"{player.character_class}, {gear_str}"
    
    def _format_player_build_without_name(self, player: PlayerBuild) -> str:
        """Format a single player's build without the player name (for use with handles)."""
        if not player.gear_sets:
            return f"{player.character_class}, (no gear data)"
        
        gear_str = ", ".join(str(gear) for gear in player.gear_sets)
        
        # Add action bar information if available
        action_bars_info = self._format_action_bars(player)
        if action_bars_info:
            return f"{player.character_class}, {gear_str}\n{action_bars_info}"
        
        return f"{player.character_class}, {gear_str}"
    
    def _format_action_bars(self, player: PlayerBuild) -> str:
        """Format a player's action bars if available."""
        if not player.abilities:
            return ""
        
        bar_lines = []
        
        # Format bar1 if available
        if 'bar1' in player.abilities and player.abilities['bar1']:
            bar1_abilities = ", ".join(player.abilities['bar1'])
            bar_lines.append(f"  bar1: {bar1_abilities}")
        
        # Format bar2 if available
        if 'bar2' in player.abilities and player.abilities['bar2']:
            bar2_abilities = ", ".join(player.abilities['bar2'])
            bar_lines.append(f"  bar2: {bar2_abilities}")
        
        return "\n".join(bar_lines)
    
    def format_multiple_trials(self, trial_reports: List[TrialReport]) -> str:
        """Format multiple trial reports."""
        formatted_reports = []
        
        for trial_report in trial_reports:
            formatted_reports.append(self.format_trial_report(trial_report))
        
        return "\n\n".join(formatted_reports)
