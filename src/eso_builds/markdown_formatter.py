"""
Markdown report formatting for ESO Logs Build and Buff Summary.

This module handles formatting trial reports into markdown format with
proper structure, tables, and links for better readability and sharing.
"""

import logging
from typing import List, Dict
from datetime import datetime
from .models import TrialReport, LogRanking, EncounterResult, PlayerBuild, Role

logger = logging.getLogger(__name__)


class MarkdownFormatter:
    """Formats trial reports into markdown format."""
    
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
    
    def _has_oakensoul_wearers(self, encounter: 'EncounterResult') -> bool:
        """Check if any player in the encounter has Oakensoul Ring equipped."""
        for player in encounter.players:
            for gear_set in player.gear_sets:
                if 'oakensoul' in gear_set.name.lower():
                    return True
        return False
    
    def _has_spaulder_of_ruin_wearers(self, encounter: 'EncounterResult') -> bool:
        """Check if any player in the encounter has Spaulder of Ruin equipped."""
        for player in encounter.players:
            for gear_set in player.gear_sets:
                if 'spaulder of ruin' in gear_set.name.lower():
                    return True
        return False
    
    def _has_tremorscale_wearers(self, encounter: 'EncounterResult') -> bool:
        """Check if any player in the encounter has 2pc+ Tremorscale equipped."""
        for player in encounter.players:
            tremorscale_count = 0
            for gear_set in player.gear_sets:
                if 'tremorscale' in gear_set.name.lower():
                    tremorscale_count += gear_set.piece_count
            if tremorscale_count >= 2:
                return True
        return False
    
    def _has_alkosh_wearers(self, encounter: 'EncounterResult') -> bool:
        """Check if any player in the encounter has 5pc+ Alkosh equipped."""
        for player in encounter.players:
            alkosh_count = 0
            for gear_set in player.gear_sets:
                if 'alkosh' in gear_set.name.lower():
                    alkosh_count += gear_set.piece_count
            if alkosh_count >= 5:
                return True
        return False
    
    def format_trial_report(self, trial_report: TrialReport) -> str:
        """Format a complete trial report as markdown."""
        lines = []
        
        # Report header with metadata
        lines.extend(self._format_header(trial_report))
        lines.append("")
        
        # Table of contents
        lines.extend(self._format_table_of_contents(trial_report))
        lines.append("")
        
        # Process each report
        for ranking in trial_report.rankings:
            lines.extend(self._format_ranking_markdown(ranking, 1))
            lines.append("")
        
        # Footer with generation info
        lines.extend(self._format_footer(trial_report))
        
        return "\n".join(lines)
    
    def _format_header(self, trial_report: TrialReport) -> List[str]:
        """Format the markdown header."""
        lines = [
            f"# {trial_report.trial_name} - Summary Report - Logged by Unknown",
            "",
            "---"
        ]
        return lines
    
    def _format_table_of_contents(self, trial_report: TrialReport) -> List[str]:
        """Format a table of contents for the report."""
        lines = [
            "## 📋 Table of Contents",
            ""
        ]
        
        for ranking in trial_report.rankings:
            lines.append(f"- [Report Analysis](#report-analysis)")
            
            for encounter in ranking.encounters:
                clean_name = encounter.encounter_name.lower().replace(' ', '-').replace("'", '')
                encounter_anchor = f"encounter-{clean_name}"
                # Add kill/wipe status to TOC - treat 0.0% or very low boss health as kill
                if encounter.kill or encounter.boss_percentage <= 0.1:
                    status_text = "✅ KILL"
                else:
                    status_text = f"❌ WIPE ({encounter.boss_percentage:.1f}%)"
                lines.append(f"  - [{encounter.encounter_name} ({encounter.difficulty.value}) - {status_text}](#{encounter_anchor})")
        
        return lines
    
    def _format_ranking_markdown(self, ranking: LogRanking, rank_num: int) -> List[str]:
        """Format a single ranking as markdown."""
        lines = [
            f"## Report Analysis {{#report-analysis}}",
            "",
            f"**🔗 Log URL:** [{ranking.log_code}]({ranking.log_url})  "
        ]
        
        if ranking.guild_name:
            lines.append(f"**🏰 Guild:** {ranking.guild_name}  ")
        
        if ranking.date:
            lines.append(f"**📅 Date:** {ranking.date.strftime('%Y-%m-%d %H:%M UTC')}  ")
        
        lines.append("")
        
        # Process each encounter
        for encounter in ranking.encounters:
            lines.extend(self._format_encounter_markdown(encounter, rank_num))
            lines.append("")
        
        
        lines.append("---")
        return lines
    
    def _format_encounter_markdown(self, encounter: EncounterResult, rank_num: int) -> List[str]:
        """Format a single encounter as markdown with tables."""
        clean_name = encounter.encounter_name.lower().replace(' ', '-').replace("'", '')
        encounter_anchor = f"encounter-{clean_name}"
        
        # Determine kill status - treat 0.0% or very low boss health as kill
        if encounter.kill or encounter.boss_percentage <= 0.1:
            status_text = "✅ KILL"
        else:
            status_text = f"❌ WIPE ({encounter.boss_percentage:.1f}%)"
        
        lines = [
            f"### ⚔️ {encounter.encounter_name} ({encounter.difficulty.value}) - {status_text} {{#{encounter_anchor}}}",
            ""
        ]
        
        # Add Buff/Debuff Uptime Table
        if encounter.buff_uptimes:
            lines.extend(self._format_buff_debuff_table(encounter.buff_uptimes, encounter))
            lines.append("")
        
        # Create team composition summary
        tanks = encounter.tanks
        healers = encounter.healers
        dps = encounter.dps
        
        # Format as tables for better readability
        if tanks:
            lines.extend(self._format_role_table("Tanks", tanks))
            lines.append("")
        
        if healers:
            lines.extend(self._format_role_table("Healers", healers))
            lines.append("")
        
        if dps:
            lines.extend(self._format_role_table("DPS", dps))
            lines.append("")
        
        return lines
    
    def _format_role_table(self, role_title: str, players: List[PlayerBuild]) -> List[str]:
        """Format a role section as a markdown table."""
        lines = [
            f"#### {role_title}",
            "",
            "| Player | Class | Gear Sets |",
            "|--------|-------|-----------|"
        ]
        
        for i, player in enumerate(players, 1):
            gear_str = self._format_gear_sets_for_table(player.gear_sets)
            class_name = self._get_class_display_name(player.character_class, player)
            lines.append(f"| {player.name} | {class_name} | {gear_str} |")
        
        # Add empty rows for missing players (especially DPS up to 8)
        if "DPS" in role_title:
            for i in range(len(players) + 1, 9):
                lines.append(f"| @anonymous{i} | - | - |")
        
        return lines
    
    def _format_gear_sets_for_table(self, gear_sets: List) -> str:
        """Format gear sets for markdown table cell."""
        if not gear_sets:
            return "*No gear data*"
        
        # Format each set without perfected highlighting
        formatted_sets = []
        for gear_set in gear_sets:
            set_str = f"{gear_set.piece_count}pc {gear_set.name}"
            formatted_sets.append(set_str)
        
        return ", ".join(formatted_sets)
    
    def _format_footer(self, trial_report: TrialReport) -> List[str]:
        """Format the markdown footer."""
        lines = [
            "---",
            "",
            "## 📊 Report Information",
            "",
            f"- **Trial:** {trial_report.trial_name}",
            f"- **Zone ID:** {trial_report.zone_id}",
            f"- **Reports Analyzed:** {len(trial_report.rankings)}",
            f"- **Generated:** {trial_report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"- **Tool:** ESO Logs Build and Buff Summary Analyzer",
            "",
            "### 🔗 Useful Links",
            "",
            "- [ESO Logs](https://www.esologs.com/)",
            "- [ESO Logs API Documentation](https://www.esologs.com/v2-api-docs/eso/)",
            "- [ESO Logs Build and Buff Summary Project](https://github.com/brainsnorkel/ESO-Logs-Build-and-Buff-Summary)",
            "",
            "---",
            "",
            "*Generated by ESO Logs Build and Buff Summary Analyzer - Analyzing Elder Scrolls Online trial builds from top performing logs.*"
        ]
        return lines
    
    def format_multiple_trials(self, trial_reports: List[TrialReport]) -> str:
        """Format multiple trial reports into a single markdown document."""
        lines = [
            "# ESO Logs Build and Buff Summary - Multiple Trials Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**Trials Analyzed:** {len(trial_reports)}  ",
            "",
            "---",
            "",
            "## 📋 Trials Overview",
            ""
        ]
        
        # Overview table
        lines.extend([
            "| Trial | Reports | Total Encounters |",
            "|-------|---------|------------------|"
        ])
        
        for trial_report in trial_reports:
            total_encounters = sum(len(ranking.encounters) for ranking in trial_report.rankings)
            lines.append(f"| [{trial_report.trial_name}](#{trial_report.trial_name.lower().replace(' ', '-')}) | {len(trial_report.rankings)} | {total_encounters} |")
        
        lines.extend(["", "---", ""])
        
        # Individual trial reports
        for trial_report in trial_reports:
            # Add anchor for navigation
            trial_anchor = trial_report.trial_name.lower().replace(' ', '-')
            lines.append(f"<a name=\"{trial_anchor}\"></a>")
            lines.append("")
            
            # Format the trial report
            trial_content = self.format_trial_report(trial_report)
            # Remove the first header since we're combining reports
            trial_lines = trial_content.split('\n')[3:]  # Skip "# Trial Name - Top Builds Report" and empty lines
            lines.extend(trial_lines)
            lines.extend(["", "---", ""])
        
        return "\n".join(lines)
    
    def _format_buff_debuff_table(self, buff_uptimes: Dict[str, float], encounter: 'EncounterResult') -> List[str]:
        """Format buff/debuff uptimes as a two-column markdown table."""
        lines = [
            "| 🔺 **Buffs** | **Uptime** | 🔻 **Debuffs** | **Uptime** |",
            "|--------------|------------|-----------------|------------|"
        ]
        
        # Check if any player has Oakensoul Ring
        has_oakensoul = self._has_oakensoul_wearers(encounter)
        
        # Check if any player has Spaulder of Ruin
        has_spaulder = self._has_spaulder_of_ruin_wearers(encounter)
        
        # Check if any player has 2pc+ Tremorscale
        has_tremorscale = self._has_tremorscale_wearers(encounter)
        
        # Check if any player has 5pc+ Alkosh
        has_alkosh = self._has_alkosh_wearers(encounter)
        
        # Define all tracked buffs and debuffs
        buffs = ['Major Courage', 'Major Slayer', 'Major Berserk', 'Major Force', 'Minor Toughness', 'Major Resolve', 'Powerful Assault']
        
        # Only add Aura of Pride if Spaulder of Ruin is detected
        if has_spaulder:
            buffs.append('Aura of Pride')
        
        debuffs = ['Major Breach', 'Major Vulnerability', 'Minor Brittle', 'Stagger', 'Crusher', 'Off Balance', 'Weakening', 'Runic Sunder']
        
        # Only add Tremorscale if 2pc+ Tremorscale is detected
        if has_tremorscale:
            debuffs.append('Tremorscale')
        
        # Only add Line-Breaker if 5pc+ Alkosh is detected
        if has_alkosh:
            debuffs.append('Line-Breaker')
        
        # Create rows for the table (pad with empty entries if needed)
        max_rows = max(len(buffs), len(debuffs))
        
        for i in range(max_rows):
            # Get buff info for this row
            if i < len(buffs):
                buff_name = buffs[i]
                buff_uptime = buff_uptimes.get(buff_name, 0.0)
                buff_cell = buff_name
                # Add asterisk for Major Courage and Major Resolve if Oakensoul wearers present
                if has_oakensoul and buff_name in ['Major Courage', 'Major Resolve']:
                    buff_uptime_cell = f"{buff_uptime:.1f}%*"
                else:
                    buff_uptime_cell = f"{buff_uptime:.1f}%"
            else:
                buff_cell = ""
                buff_uptime_cell = ""
            
            # Get debuff info for this row
            if i < len(debuffs):
                debuff_name = debuffs[i]
                debuff_uptime = buff_uptimes.get(debuff_name, 0.0)
                debuff_cell = debuff_name
                debuff_uptime_cell = f"{debuff_uptime:.1f}%"
            else:
                debuff_cell = ""
                debuff_uptime_cell = ""
            
            lines.append(f"| {buff_cell} | {buff_uptime_cell} | {debuff_cell} | {debuff_uptime_cell} |")
        
        return lines
    
    
    def get_filename(self, trial_name: str) -> str:
        """Generate a safe filename for the trial report."""
        # Clean the trial name for use as filename
        safe_name = trial_name.lower()
        safe_name = safe_name.replace(' ', '_')
        safe_name = safe_name.replace("'", '')
        safe_name = safe_name.replace('"', '')
        safe_name = safe_name.replace(':', '')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '_-')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        return f"{safe_name}_report_{timestamp}.md"
