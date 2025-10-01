"""
Markdown report formatting for ESO Top Builds.

This module handles formatting trial reports into markdown format with
proper structure, tables, and links for better readability and sharing.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from .models import TrialReport, LogRanking, EncounterResult, PlayerBuild, Role, GearSet, calculate_kills_and_wipes
from .set_abbreviations import abbreviate_set_name

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
    
    # Role icons for visual identification
    ROLE_ICONS = {
        Role.TANK: '🛡️',
        Role.HEALER: '💚',
        Role.DPS: '⚔️'
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
    
    def format_trial_report(self, trial_report: TrialReport, anonymize: bool = False) -> str:
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
            f"# {trial_report.trial_name} - Summary Report",
            ""
        ]
        
        # Add kill/wipe summary if we have encounters
        if trial_report.rankings:
            all_encounters = []
            for ranking in trial_report.rankings:
                all_encounters.extend(ranking.encounters)
            
            if all_encounters:
                total_kills, total_wipes = calculate_kills_and_wipes(all_encounters)
                lines.extend([
                    f"**📊 Trial Summary:** {total_kills} Kills, {total_wipes} Wipes",
                    ""
                ])
        
        lines.append("---")
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
        
        # Generate ESO Logs URL for this fight
        report_code = encounter.report_code if hasattr(encounter, 'report_code') else 'UNKNOWN'
        fight_id = encounter.fight_id if hasattr(encounter, 'fight_id') else 1
        eso_logs_url = f"https://www.esologs.com/reports/{report_code}?fight={fight_id}"
        
        # Format header with group DPS if available
        header = f"### ⚔️ {encounter.encounter_name} ({encounter.difficulty.value}) - {status_text} {{#{encounter_anchor}}}"
        if encounter.group_dps_total:
            formatted_dps = self._format_dps_with_suffix(encounter.group_dps_total)
            header += f" - **{formatted_dps} DPS**"
        
        lines = [
            header,
            f"[📊 ESO Logs Fight Summary]({eso_logs_url})",
            ""
        ]
        
        # Add Buff/Debuff Uptime Table
        if encounter.buff_uptimes:
            lines.extend(self._format_buff_debuff_table(encounter.buff_uptimes))
            lines.append("")
        
        # Create consolidated team composition table
        all_players = []
        
        # Add tanks first
        if encounter.tanks:
            all_players.extend(encounter.tanks)
        
        # Add healers second
        if encounter.healers:
            all_players.extend(encounter.healers)
        
        # Add DPS last, sorted by DPS percentage (highest first)
        if encounter.dps:
            sorted_dps = sorted(encounter.dps, key=lambda p: p.dps_data.get('dps_percentage', 0) if p.dps_data else 0, reverse=True)
            all_players.extend(sorted_dps)
        
        # Format as single consolidated table
        if all_players:
            lines.extend(self._format_consolidated_player_table(all_players))
            lines.append("")
        
        return lines
    
    def _format_role_table(self, role_title: str, players: List[PlayerBuild]) -> List[str]:
        """Format a role section as a markdown table."""
        # Use different table structure for DPS, Healers, and Tanks to include abilities
        if "DPS" in role_title or "Healers" in role_title or "Tanks" in role_title:
            lines = [
                "| Player | Class | Gear Sets |",
                "|--------|-------|-----------|"
            ]
            
            for i, player in enumerate(players, 1):
                gear_str = self._format_gear_sets_for_table(player.gear_sets)
                class_name = self._get_class_display_name(player.character_class, player)
                
                # Add role icon and DPS percentage to player name
                role_icon = self.ROLE_ICONS.get(player.role, '')
                player_name = f"{role_icon} {player.name}"
                
                if player.role.value == "DPS" and player.dps_data and 'dps_percentage' in player.dps_data:
                    dps_percentage = player.dps_data['dps_percentage']
                    player_name = f"{role_icon} {player.name} ({dps_percentage:.1f}%)"
                    logger.debug(f"Formatted DPS player {player.name} with percentage: {player_name}")
                elif player.role.value == "DPS":
                    logger.debug(f"DPS player {player.name} - dps_data: {player.dps_data}")
                
                # Add "Set Problem?:" indicator if player has incomplete sets
                if self._has_incomplete_sets(player.gear_sets):
                    gear_str = f"**Set Problem?:** {gear_str}"
                
                lines.append(f"| {player_name} | {class_name} | {gear_str} |")
                
                # Add action bars if available
                if player.abilities and (player.abilities.get('bar1') or player.abilities.get('bar2')):
                    action_bars = self._format_action_bars_for_table(player)
                    if action_bars:
                        lines.append(f"| ↳ {action_bars} |")
            
            # No need to pad tables to fixed numbers - show only actual players
        else:
            # Regular table for other roles (if any)
            lines = [
                f"#### {role_title}",
                "",
                "| Player | Class | Gear Sets |",
                "|--------|-------|-----------|"
            ]
            
            for i, player in enumerate(players, 1):
                gear_str = self._format_gear_sets_for_table(player.gear_sets)
                class_name = self._get_class_display_name(player.character_class, player)
                
                # Add role icon to player name
                role_icon = self.ROLE_ICONS.get(player.role, '')
                player_name = f"{role_icon} {player.name}"
                
                # Add "Set Problem?:" indicator if player has incomplete sets
                if self._has_incomplete_sets(player.gear_sets):
                    gear_str = f"**Set Problem?:** {gear_str}"
                
                lines.append(f"| {player_name} | {class_name} | {gear_str} |")
                
                # Add action bars if available
                if player.abilities and (player.abilities.get('bar1') or player.abilities.get('bar2')):
                    action_bars = self._format_action_bars_for_table(player)
                    if action_bars:
                        lines.append(f"| ↳ {action_bars} |")
        
        return lines
    
    def _format_consolidated_player_table(self, all_players: List[PlayerBuild]) -> List[str]:
        """Format all players in a single consolidated table with role icons."""
        lines = [
            "| Player | Class | Gear Sets |",
            "|--------|-------|-----------|"
        ]
        
        for player in all_players:
            gear_str = self._format_gear_sets_for_table(player.gear_sets)
            class_name = self._get_class_display_name(player.character_class, player)
            
            # Add role icon and DPS percentage to player name
            role_icon = self.ROLE_ICONS.get(player.role, '')
            player_name = f"{role_icon} {player.name}"
            
            # Add DPS percentage for all roles if available
            if player.dps_data and 'dps_percentage' in player.dps_data:
                dps_percentage = player.dps_data['dps_percentage']
                player_name = f"{role_icon} {player.name} ({dps_percentage:.1f}%)"
                logger.debug(f"Formatted {player.role.value} player {player.name} with percentage: {player_name}")
            elif player.role.value == "DPS":
                logger.debug(f"DPS player {player.name} - dps_data: {player.dps_data}")
            
            # Add "Set Problem?:" indicator if player has incomplete sets
            if self._has_incomplete_sets(player.gear_sets):
                gear_str = f"**Set Problem?:** {gear_str}"
            
            lines.append(f"| {player_name} | {class_name} | {gear_str} |")
            
            # Add action bars if available
            if player.abilities and (player.abilities.get('bar1') or player.abilities.get('bar2')):
                action_bars = self._format_action_bars_for_table(player)
                if action_bars:
                    lines.append(f"| ↳ {action_bars} |")
        
        return lines
    
    def _format_gear_sets_for_table(self, gear_sets: List) -> str:
        """Format gear sets for markdown table cell."""
        if not gear_sets:
            return "*No gear data*"
        
        # Format each set without perfected highlighting
        formatted_sets = []
        for gear_set in gear_sets:
            # Use abbreviated set name if available
            abbreviated_name = abbreviate_set_name(gear_set.name)
            set_str = f"{gear_set.piece_count}x{abbreviated_name}"
            formatted_sets.append(set_str)
        
        return ", ".join(formatted_sets)
    
    def _format_abilities_for_table(self, abilities: List[str]) -> str:
        """Format abilities list for markdown table cell."""
        if not abilities:
            return "*No abilities*"
        
        # Show all abilities without truncation or abbreviation
        return ", ".join(abilities)
    
    def _format_dps_with_suffix(self, dps_value: int) -> str:
        """Format DPS value with k/m suffixes to one decimal place."""
        if dps_value >= 1000000:
            return f"{dps_value / 1000000:.1f}m"
        elif dps_value >= 1000:
            return f"{dps_value / 1000:.1f}k"
        else:
            return str(dps_value)
    
    def _format_action_bars_for_table(self, player: PlayerBuild) -> str:
        """Format action bars for markdown table cell."""
        if not player.abilities:
            return ""
        
        bars = []
        
        # Format bar1 if available
        if player.abilities.get('bar1'):
            bar1_abilities = ", ".join(player.abilities['bar1'])
            bars.append(f"1: {bar1_abilities}")
        
        # Format bar2 if available
        if player.abilities.get('bar2'):
            bar2_abilities = ", ".join(player.abilities['bar2'])
            bars.append(f"2: {bar2_abilities}")
        
        return "<br/>".join(bars)
    
    def _format_top_abilities_for_table(self, top_abilities: List[Dict[str, Any]]) -> str:
        """Format top abilities with damage/healing numbers for markdown table cell."""
        if not top_abilities:
            return "*No abilities*"
        
        # Format each ability with its percentage
        formatted_abilities = []
        for ability in top_abilities:
            name = ability.get('name', 'Unknown')
            percentage = ability.get('percentage', 0)
            formatted_abilities.append(f"{name} ({percentage:.1f}%)")
        
        return ", ".join(formatted_abilities)

    def _format_cast_counts_for_table(self, top_abilities: List[Dict[str, Any]]) -> str:
        """Format top abilities with cast counts for markdown table cell."""
        if not top_abilities:
            return "*No abilities*"
        
        # Format each ability with its cast count
        formatted_abilities = []
        for ability in top_abilities:
            name = ability.get('name', 'Unknown')
            casts = ability.get('casts', 0)
            formatted_abilities.append(f"{name} ({casts})")
        
        return ", ".join(formatted_abilities)

    def _has_incomplete_sets(self, gear_sets: List[GearSet]) -> bool:
        """Check if a player has incomplete 5-piece sets that should be flagged."""
        for gear_set in gear_sets:
            # Only flag sets that are actually 5-piece sets (not monster sets, mythics, etc.)
            # and have fewer than 5 pieces
            set_name_lower = gear_set.name.lower()
            
            # Skip monster sets, mythics, and arena weapons - these are not 5-piece sets
            if any(indicator in set_name_lower for indicator in [
                'monster', 'undaunted', 'slimecraw', 'nazaray', 'baron zaudrus', 
                'encratis', 'behemoth', 'zaan', 'velothi', 'oakensoul', 'pearls',
                'maelstrom', 'arena', 'crushing', 'merciless'
            ]):
                continue
                
            # Only flag actual 5-piece sets that have fewer than 5 pieces
            if gear_set.max_pieces == 5 and gear_set.piece_count < 5:
                return True
        return False

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
            f"- **Tool:** ESO Top Builds Analyzer",
            "",
            "### 🔗 Useful Links",
            "",
            "- [ESO Logs](https://www.esologs.com/)",
            "- [ESO Logs API Documentation](https://www.esologs.com/v2-api-docs/eso/)",
            "- [ESO Top Builds Project](https://github.com/brainsnorkel/ESO-Top-Builds)",
            "",
            "---",
            "",
            "*Generated by ESO Top Builds Analyzer - Analyzing Elder Scrolls Online trial builds from top performing logs.*"
        ]
        return lines
    
    def format_multiple_trials(self, trial_reports: List[TrialReport]) -> str:
        """Format multiple trial reports into a single markdown document."""
        lines = [
            "# ESO Top Builds - Multiple Trials Report",
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
    
    def _format_buff_debuff_table(self, buff_uptimes: Dict[str, str]) -> List[str]:
        """Format buff/debuff uptimes as a two-column markdown table."""
        lines = [
            "| 🔺 **Buffs** | **Uptime** | 🔻 **Debuffs** | **Uptime** |",
            "|--------------|------------|-----------------|------------|"
        ]
        
        # Define all tracked buffs and debuffs (base names without asterisks)
        base_buffs = ['Major Courage', 'Major Slayer', 'Major Berserk', 'Major Force', 'Minor Toughness', 'Major Resolve', 'Powerful Assault']
        base_debuffs = ['Major Breach', 'Major Vulnerability', 'Minor Brittle', 'Stagger', 'Crusher', 'Off Balance', 'Weakening']
        
        # Create rows for the table (pad with empty entries if needed)
        max_rows = max(len(base_buffs), len(base_debuffs))
        
        for i in range(max_rows):
            # Get buff info for this row
            if i < len(base_buffs):
                base_buff_name = base_buffs[i]
                # Look for the buff with or without asterisk
                buff_key = None
                buff_uptime = 0.0
                if base_buff_name in buff_uptimes:
                    buff_key = base_buff_name
                    buff_uptime = float(buff_uptimes[buff_key])
                elif f"{base_buff_name}*" in buff_uptimes:
                    buff_key = f"{base_buff_name}*"
                    buff_uptime = float(buff_uptimes[buff_key])
                
                buff_cell = buff_key if buff_key else ""
                buff_uptime_cell = f"{buff_uptime:.1f}%" if buff_key else ""
            else:
                buff_cell = ""
                buff_uptime_cell = ""
            
            # Get debuff info for this row
            if i < len(base_debuffs):
                base_debuff_name = base_debuffs[i]
                # Look for the debuff with or without asterisk
                debuff_key = None
                debuff_uptime = 0.0
                if base_debuff_name in buff_uptimes:
                    debuff_key = base_debuff_name
                    debuff_uptime = float(buff_uptimes[debuff_key])
                elif f"{base_debuff_name}*" in buff_uptimes:
                    debuff_key = f"{base_debuff_name}*"
                    debuff_uptime = float(buff_uptimes[debuff_key])
                
                debuff_cell = debuff_key if debuff_key else ""
                debuff_uptime_cell = f"{debuff_uptime:.1f}%" if debuff_key else ""
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
