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
    
    def __init__(self):
        """Initialize the Discord formatter."""
        pass
    
    def format_trial_report(self, trial_report: TrialReport) -> str:
        """Format a complete trial report for Discord."""
        lines = []
        
        # Main header with Discord formatting
        title = f"**{trial_report.trial_name} - Build Analysis Report**"
        lines.extend([
            title,
            "",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
            f"**Zone ID:** {trial_report.zone_id}",
            f"**Reports Analyzed:** {len(trial_report.rankings) if trial_report.rankings else 1}",
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
        # Determine kill status
        if encounter.boss_percentage == 0.0:
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
            lines.extend(self._format_role_discord("🛡️ **Tanks**", tanks))
            lines.append("")
        
        if healers:
            lines.extend(self._format_role_discord("💚 **Healers**", healers))
            lines.append("")
        
        if dps:
            lines.extend(self._format_role_discord("⚔️ **DPS**", dps))
            lines.append("")
        
        return lines
    
    def _format_buff_debuff_discord(self, buff_uptimes: Dict[str, float]) -> List[str]:
        """Format buff/debuff uptimes for Discord."""
        lines = [
            "#### 📊 **Buff/Debuff Uptimes**",
            ""
        ]
        
        # Separate buffs and debuffs
        buffs = ['Major Courage', 'Major Slayer', 'Major Berserk', 'Major Force', 'Minor Toughness', 'Major Resolve']
        debuffs = ['Major Breach', 'Major Vulnerability', 'Minor Brittle']
        
        # Discord doesn't have great table support, so use a compact format
        buff_lines = []
        debuff_lines = []
        
        # Add buffs
        for buff_name in buffs:
            if buff_name in buff_uptimes:
                uptime = buff_uptimes[buff_name]
                buff_lines.append(f"🔺 **{buff_name}**: {uptime:.1f}%")
        
        # Add debuffs
        for debuff_name in debuffs:
            if debuff_name in buff_uptimes:
                uptime = buff_uptimes[debuff_name]
                debuff_lines.append(f"🔻 **{debuff_name}**: {uptime:.1f}%")
        
        # Combine buffs and debuffs
        if buff_lines:
            lines.extend(buff_lines)
        if debuff_lines:
            if buff_lines:
                lines.append("")
            lines.extend(debuff_lines)
        
        # If no data found, show a message
        if not buff_lines and not debuff_lines:
            lines.append("*No buff/debuff data available*")
        
        return lines
    
    def _format_role_discord(self, role_header: str, players: List[PlayerBuild]) -> List[str]:
        """Format players of a specific role for Discord."""
        lines = [role_header, ""]
        
        for i, player in enumerate(players, 1):
            # Player header
            player_name = player.name if player.name != "anonymous" else f"anonymous{i}"
            lines.append(f"**{player_name}:** {player.character_class}")
            
            # Gear sets in a compact format
            gear_text = self._format_gear_sets_discord(player.gear_sets)
            lines.append(f"*{gear_text}*")
            lines.append("")
        
        return lines
    
    def _format_gear_sets_discord(self, gear_sets: List) -> str:
        """Format gear sets for Discord in a compact way."""
        if not gear_sets:
            return "No gear data"
        
        formatted_sets = []
        for gear_set in gear_sets:
            # Use Discord formatting for piece counts
            formatted_sets.append(f"**{gear_set.piece_count}pc** {gear_set.name}")
        
        return ", ".join(formatted_sets)
    
    def _format_ranking_discord(self, ranking: LogRanking) -> List[str]:
        """Format a ranking section for Discord (future expansion)."""
        lines = [
            f"## **Rank {ranking.rank}: {ranking.score:.2f} Score**",
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
