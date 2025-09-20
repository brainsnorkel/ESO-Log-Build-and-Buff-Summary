"""
Discord markup formatting for ESO Top Builds.

This module handles formatting trial reports into Discord-friendly markup format
optimized for chat readability with proper Discord formatting syntax.
"""

import logging
from typing import List, Dict
from datetime import datetime
from .models import TrialReport, LogRanking, EncounterResult, PlayerBuild, Role

logger = logging.getLogger(__name__)

class DiscordReportFormatter:
    """Formats ESO trial reports for Discord chat using Discord markup."""
    
    # Class name mapping for shorter display names
    CLASS_MAPPING = {
        'Arcanist': 'Arc',
        'Sorcerer': 'Sorc',
        'DragonKnight': 'DK',
        'Necromancer': 'Cro',
        'Templar': 'Plar',
        'Warden': 'Den',
        'Nightblade': 'NB'
    }
    
    def __init__(self):
        """Initialize the Discord formatter."""
        pass
    
    def _get_class_display_name(self, class_name: str, player_build=None) -> str:
        """Get the shortened display name for a class, with Oaken prefix if Oakensoul Ring equipped."""
        mapped_class = self.CLASS_MAPPING.get(class_name, class_name)
        
        # Check for Oakensoul Ring if player_build is provided
        if player_build and player_build.gear_sets:
            has_oakensoul = any(
                'oakensoul' in gear_set.name.lower() 
                for gear_set in player_build.gear_sets
            )
            if has_oakensoul:
                return f"Oaken{mapped_class}"
        
        return mapped_class
    
    def format_trial_report(self, trial_report: TrialReport) -> str:
        """Format a complete trial report for Discord."""
        lines = []
        
        # Main header with Discord formatting
        title = f"**{trial_report.trial_name} - Summary Report**"
        lines.extend([
            title,
            "",
            "─" * 50,
            ""
        ])
        
        # For single report analysis, process encounters from the first ranking
        if trial_report.rankings and len(trial_report.rankings) > 0:
            ranking = trial_report.rankings[0]
            lines.extend([
                "## 📋 **Report Analysis**",
                "",
                f"**🔗 Log URL:** <https://www.esologs.com/reports/{ranking.log_code}>",
                f"**📅 Date:** {ranking.date.strftime('%Y-%m-%d %H:%M UTC') if ranking.date else 'N/A'}",
                ""
            ])
            
            for encounter in ranking.encounters:
                lines.extend(self._format_encounter_discord(encounter))
                lines.append("")
        
        # For ranked reports (future expansion)
        else:
            for ranking in trial_report.rankings:
                lines.extend(self._format_ranking_discord(ranking))
                lines.append("")
        
        return "\n".join(lines)
    
    def _format_encounter_discord(self, encounter: EncounterResult) -> List[str]:
        """Format a single encounter for Discord."""
        # Determine kill status - treat 0.0% or very low boss health as kill
        if encounter.kill or encounter.boss_percentage <= 0.1:
            status_text = "✅ KILL"
        else:
            status_text = f"❌ WIPE ({encounter.boss_percentage:.1f}%)"
        
        lines = [
            f"### ⚔️ **{encounter.encounter_name}** ({encounter.difficulty.value}) - {status_text}",
            ""
        ]
        
        # Add Buff/Debuff Uptime Table
        if encounter.buff_uptimes:
            lines.extend(self._format_buff_debuff_discord(encounter.buff_uptimes))
            lines.append("")
        
        # Get player role groups
        tanks = encounter.tanks
        healers = encounter.healers
        dps = encounter.dps
        
        # Format role sections
        if tanks:
            lines.extend(self._format_role_discord("**Tanks**", tanks))
            lines.append("")
        
        if healers:
            lines.extend(self._format_role_discord("**Healers**", healers))
            lines.append("")
        
        if dps:
            lines.extend(self._format_role_discord("**DPS**", dps))
            lines.append("")
        
        return lines
    
    def _format_buff_debuff_discord(self, buff_uptimes: Dict[str, float]) -> List[str]:
        """Format buff/debuff uptimes for Discord as simple lists."""
        lines = []
        
        # Define all tracked buffs and debuffs
        buffs = ['Major Courage', 'Major Slayer', 'Major Berserk', 'Major Force', 'Minor Toughness', 'Major Resolve', 'Pillager\'s Profit', 'Powerful Assault']
        debuffs = ['Major Breach', 'Major Vulnerability', 'Minor Brittle', 'Stagger', 'Crusher', 'Off Balance', 'Weakening']
        
        # Format buffs as simple list
        buff_items = []
        for buff_name in buffs:
            uptime = buff_uptimes.get(buff_name, 0.0)
            buff_items.append(f"{buff_name} {uptime:.1f}%")
        lines.append(f"Buffs: {', '.join(buff_items)}")
        
        # Format debuffs as simple list
        debuff_items = []
        for debuff_name in debuffs:
            uptime = buff_uptimes.get(debuff_name, 0.0)
            debuff_items.append(f"{debuff_name} {uptime:.1f}%")
        lines.append(f"Debuffs: {', '.join(debuff_items)}")
        
        return lines
    
    def _format_role_discord(self, role_header: str, players: List[PlayerBuild]) -> List[str]:
        """Format players of a specific role for Discord."""
        lines = [role_header]
        
        for i, player in enumerate(players, 1):
            # Player header - escape @ symbols with backticks to prevent Discord pings
            player_name = player.name if player.name != "anonymous" else f"anonymous{i}"
            escaped_name = f"`{player_name}`" if "@" in player_name else player_name
            
            # Gear sets in a compact format
            gear_text = self._format_gear_sets_discord(player.gear_sets)
            
            # Combine character class and gear sets on one line with a dash separator
            class_name = self._get_class_display_name(player.character_class, player)
            lines.append(f"{escaped_name}: {class_name} - {gear_text}")
        
        return lines
    
    def _format_gear_sets_discord(self, gear_sets: List) -> str:
        """Format gear sets for Discord in a compact way."""
        if not gear_sets:
            return "No gear data"
        
        formatted_sets = []
        for gear_set in gear_sets:
            # Simple format without bold styling
            formatted_sets.append(f"{gear_set.piece_count}pc {gear_set.name}")
        
        return ", ".join(formatted_sets)
    
    def _format_ranking_discord(self, ranking: LogRanking) -> List[str]:
        """Format a ranking section for Discord (future expansion)."""
        lines = [
            f"## **Report Analysis: {ranking.log_code}**",
            "",
            f"**🔗 Log URL:** <{ranking.log_url}>",
            f"**📅 Date:** {ranking.date.strftime('%Y-%m-%d %H:%M UTC') if ranking.date else 'N/A'}",
            ""
        ]
        
        for encounter in ranking.encounters:
            lines.extend(self._format_encounter_discord(encounter))
            lines.append("")
        
        return lines
    
    def format_multiple_trials(self, trial_reports: List[TrialReport]) -> str:
        """Format multiple trial reports for Discord (future expansion)."""
        lines = [
            "# **ESO Top Builds - Multi-Trial Analysis**",
            "",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
            f"**Trials Analyzed:** {len(trial_reports)}",
            "",
            "─" * 50,
            ""
        ]
        
        for trial_report in trial_reports:
            # Format the trial report
            trial_content = self.format_trial_report(trial_report)
            # Remove the first header since we're combining reports
            trial_lines = trial_content.split('\n')[3:]  # Skip main header and empty lines
            lines.extend(trial_lines)
            lines.extend(["", "─" * 50, ""])
        
        return "\n".join(lines)
    
    def get_filename(self, trial_name: str) -> str:
        """Generate a safe filename for the Discord report."""
        # Clean the trial name for use as filename
        safe_name = trial_name.lower()
        safe_name = safe_name.replace(' ', '_')
        safe_name = safe_name.replace("'", '')
        safe_name = safe_name.replace('"', '')
        safe_name = safe_name.replace(':', '')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '_-')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return f"{safe_name}_{timestamp}_discord.txt"
