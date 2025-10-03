"""
Discord markup formatting for ESO Top Builds.

This module handles formatting trial reports into Discord-friendly markup format
optimized for chat readability with proper Discord formatting syntax.
"""

import logging
from typing import List, Dict
from datetime import datetime
from .models import TrialReport, LogRanking, EncounterResult, PlayerBuild, Role, GearSet, calculate_kills_and_wipes
from .set_abbreviations import abbreviate_set_name
from .build_name_mapper import BuildNameMapper
from .ability_abbreviations import abbreviate_ability_name

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
    
    # Role icons for visual identification
    ROLE_ICONS = {
        Role.TANK: '🛡️',
        Role.HEALER: '💚',
        Role.DPS: '⚔️'
    }
    
    def __init__(self):
        """Initialize the discord formatter with build name mapper."""
        self.build_name_mapper = BuildNameMapper()
    
    def _get_class_display_name(self, class_name: str, player_build=None) -> str:
        """Get the shortened display name for a class, with subclass info and Oaken prefix if Oakensoul Ring equipped."""
        # Use subclass information if available
        if player_build and player_build.subclass_info:
            from .subclass_analyzer import ESOSubclassAnalyzer
            analyzer = ESOSubclassAnalyzer()
            skill_lines = player_build.subclass_info.get('skill_lines', [])
            confidence = player_build.subclass_info.get('confidence', 0.0)
            subclass_name = analyzer.get_subclass_display_name(class_name, skill_lines, confidence)
            
            # Check for Oakensoul Ring
            if player_build.gear_sets:
                has_oakensoul = any(
                    'oakensoul' in gear_set.name.lower() 
                    for gear_set in player_build.gear_sets
                )
                if has_oakensoul:
                    return f"Oaken{subclass_name}"
            
            return subclass_name
        
        # Fallback to original logic
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
            
            # Add kill/wipe summary
            if ranking.encounters:
                total_kills, total_wipes = calculate_kills_and_wipes(ranking.encounters)
                lines.extend([
                    f"**📊 Trial Summary:** {total_kills} Kills, {total_wipes} Wipes",
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
        
        # Format header with group DPS if available
        header = f"### ⚔️ **{encounter.encounter_name}** ({encounter.difficulty.value}) - {status_text}"
        if encounter.group_dps_total:
            formatted_dps = self._format_dps_with_suffix(encounter.group_dps_total)
            header += f" - **{formatted_dps} DPS**"
        
        lines = [
            header,
            ""
        ]
        
        # Add Buff/Debuff Uptime Table
        if encounter.buff_uptimes:
            lines.extend(self._format_buff_debuff_discord(encounter.buff_uptimes))
            lines.append("")
        
        # Create consolidated player list
        all_players = []
        
        # Add tanks first
        if encounter.tanks:
            all_players.extend(encounter.tanks)
        
        # Add healers second
        if encounter.healers:
            all_players.extend(encounter.healers)
        
        # Add DPS last, sorted by DPS number (highest first)
        if encounter.dps:
            dps_sorted = sorted(encounter.dps, key=lambda p: p.dps_data.get('dps', 0) if p.dps_data else 0, reverse=True)
            all_players.extend(dps_sorted)
        
        # Format as single consolidated section
        if all_players:
            lines.extend(self._format_consolidated_players_discord(all_players))
            lines.append("")
        
        return lines
    
    def _format_buff_debuff_discord(self, buff_uptimes: Dict[str, str]) -> List[str]:
        """Format buff/debuff uptimes for Discord as simple lists."""
        lines = []
        
        # Define all tracked buffs and debuffs (base names without asterisks)
        base_buffs = ['Major Courage', 'Major Slayer', 'Major Berserk', 'Major Force', 'Minor Toughness', 'Major Resolve', 'Powerful Assault']
        base_debuffs = ['Major Breach', 'Major Vulnerability', 'Minor Brittle', 'Stagger', 'Crusher', 'Off Balance', 'Weakening']
        
        # Format buffs as simple list
        buff_items = []
        for base_buff_name in base_buffs:
            # Look for the buff with or without asterisk
            buff_key = None
            uptime = 0.0
            if base_buff_name in buff_uptimes:
                buff_key = base_buff_name
                uptime = float(buff_uptimes[buff_key])
            elif f"{base_buff_name}*" in buff_uptimes:
                buff_key = f"{base_buff_name}*"
                uptime = float(buff_uptimes[buff_key])
            
            if buff_key:
                buff_items.append(f"{buff_key} {uptime:.1f}%")
        lines.append(f"Buffs: {', '.join(buff_items)}")
        
        # Format debuffs as simple list
        debuff_items = []
        for base_debuff_name in base_debuffs:
            # Look for the debuff with or without asterisk
            debuff_key = None
            uptime = 0.0
            if base_debuff_name in buff_uptimes:
                debuff_key = base_debuff_name
                uptime = float(buff_uptimes[debuff_key])
            elif f"{base_debuff_name}*" in buff_uptimes:
                debuff_key = f"{base_debuff_name}*"
                uptime = float(buff_uptimes[debuff_key])
            
            if debuff_key:
                debuff_items.append(f"{debuff_key} {uptime:.1f}%")
        lines.append(f"Debuffs: {', '.join(debuff_items)}")
        
        return lines
    
    def _format_role_discord(self, role_header: str, players: List[PlayerBuild]) -> List[str]:
        """Format players of a specific role for Discord."""
        lines = [role_header]
        
        for i, player in enumerate(players, 1):
            # Player header - escape @ symbols with backticks to prevent Discord pings
            base_name = player.name if player.name != "anonymous" else f"anonymous{i}"
            
            # Add role icon and DPS number to player name
            role_icon = self.ROLE_ICONS.get(player.role, '')
            player_name = f"{role_icon} {base_name}"
            
            if player.dps_data and 'dps' in player.dps_data:
                dps_value = player.dps_data['dps']
                formatted_dps = self._format_dps_with_suffix(int(dps_value))
                player_name = f"{role_icon} {base_name} {formatted_dps}"
            
            escaped_name = f"`{player_name}`" if "@" in player_name else player_name
            
            # Gear sets in a compact format
            gear_text = self._format_gear_sets_discord(player.gear_sets)
            
            # Add "Set Problem?:" indicator if player has incomplete sets
            if self._has_incomplete_sets(player.gear_sets):
                gear_text = f"**Set Problem?:** {gear_text}"
            
            # Combine character class and gear sets on one line with a dash separator
            class_name = self._get_class_display_name(player.character_class, player)
            lines.append(f"{escaped_name}: {class_name} - {gear_text}")
            
            # Add action bars if available
            if player.abilities and (player.abilities.get('bar1') or player.abilities.get('bar2')):
                action_bars = self._format_action_bars_for_discord(player)
                if action_bars:
                    lines.append(f"  ↳ {action_bars}")
        
        return lines
    
    def _format_consolidated_players_discord(self, all_players: List[PlayerBuild]) -> List[str]:
        """Format all players in a single consolidated section for Discord."""
        lines = []
        
        for player in all_players:
            # Player header - escape @ symbols with backticks to prevent Discord pings
            base_name = player.name if player.name != "anonymous" else f"anonymous{all_players.index(player) + 1}"
            
            # Add role icon and DPS number to player name
            role_icon = self.ROLE_ICONS.get(player.role, '')
            player_name = f"{role_icon} {base_name}"
            
            if player.dps_data and 'dps' in player.dps_data:
                dps_value = player.dps_data['dps']
                formatted_dps = self._format_dps_with_suffix(int(dps_value))
                player_name = f"{role_icon} {base_name} {formatted_dps}"
            
            escaped_name = f"`{player_name}`" if "@" in player_name else player_name
            
            # Gear sets in a compact format
            gear_text = self._format_gear_sets_discord(player.gear_sets)
            
            # Add "Set Problem?:" indicator if player has incomplete sets
            if self._has_incomplete_sets(player.gear_sets):
                gear_text = f"**Set Problem?:** {gear_text}"
            
            # Combine character class and gear sets on one line with a dash separator
            class_name = self._get_class_display_name(player.character_class, player)
            lines.append(f"{escaped_name}: {class_name} - {gear_text}")
            
            # Add action bars if available
            if player.abilities and (player.abilities.get('bar1') or player.abilities.get('bar2')):
                action_bars = self._format_action_bars_for_discord(player)
                if action_bars:
                    lines.append(f"  ↳ {action_bars}")
        
        return lines
    
    def _format_gear_sets_discord(self, gear_sets: List) -> str:
        """Format gear sets for Discord in a compact way."""
        if not gear_sets:
            return "No gear data"
        
        # First, apply build name mapping on full set names
        full_gear_sets = []
        for gear_set in gear_sets:
            set_str = str(gear_set)  # Use GearSet.__str__() which handles mythic items properly
            full_gear_sets.append(set_str)
        
        gear_str = ", ".join(full_gear_sets)
        # Apply build name mapping first
        gear_str = self.build_name_mapper.apply_build_mapping(gear_str)
        
        # Then apply abbreviations to the result
        return self._apply_abbreviations_to_gear_string(gear_str)
    
    def _apply_abbreviations_to_gear_string(self, gear_str: str) -> str:
        """Apply abbreviations to a gear string that may contain build names."""
        # Split by comma and process each part
        parts = [part.strip() for part in gear_str.split(',')]
        abbreviated_parts = []
        
        for part in parts:
            # Check if this part contains a build name (contains '/')
            if '/' in part:
                # This is likely a build name, keep as-is
                abbreviated_parts.append(part)
            else:
                # This is a regular gear set, apply abbreviations
                abbreviated_part = self._apply_abbreviations_to_single_set(part)
                abbreviated_parts.append(abbreviated_part)
        
        return ', '.join(abbreviated_parts)
    
    def _apply_abbreviations_to_single_set(self, set_str: str) -> str:
        """Apply abbreviations to a single gear set string."""
        # Extract piece count and set name
        if 'pc ' in set_str:
            piece_count, set_name = set_str.split('pc ', 1)
            abbreviated_name = abbreviate_set_name(set_name)
            return f"{piece_count}x{abbreviated_name}"
        elif 'x' in set_str:
            # Already in abbreviated format
            return set_str
        else:
            # Fallback
            return set_str
    
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
    
    def _format_top_abilities_for_discord(self, top_abilities: List) -> str:
        """Format top abilities with percentages for Discord."""
        if not top_abilities:
            return "*No abilities*"
        
        # Format each ability with its percentage
        formatted_abilities = []
        for ability in top_abilities:
            name = ability.get('name', 'Unknown')
            percentage = ability.get('percentage', 0.0)
            formatted_abilities.append(f"{name} ({percentage:.1f}%)")
        
        return ", ".join(formatted_abilities)
    
    def _format_cast_counts_for_discord(self, top_abilities: List) -> str:
        """Format top abilities with cast counts for Discord."""
        if not top_abilities:
            return "*No abilities*"
        
        # Format each ability with its cast count
        formatted_abilities = []
        for ability in top_abilities:
            name = ability.get('name', 'Unknown')
            casts = ability.get('casts', 0)
            formatted_abilities.append(f"{name} ({casts})")
        
        return ", ".join(formatted_abilities)
    
    def _format_action_bars_for_discord(self, player: PlayerBuild) -> str:
        """Format action bars for Discord."""
        if not player.abilities:
            return ""
        
        bars = []
        
        # Format bar1 if available
        if player.abilities.get('bar1'):
            bar1_abilities = ", ".join(abbreviate_ability_name(ability) for ability in player.abilities['bar1'])
            bars.append(f"1: {bar1_abilities}")
        
        # Format bar2 if available
        if player.abilities.get('bar2'):
            bar2_abilities = ", ".join(abbreviate_ability_name(ability) for ability in player.abilities['bar2'])
            bars.append(f"2: {bar2_abilities}")
        
        return "\n  ↳ ".join(bars)
    
    def _format_dps_with_suffix(self, dps_value: int) -> str:
        """Format DPS value with k/m suffixes as whole numbers."""
        if dps_value >= 1000000:
            return f"{int(round(dps_value / 1000000))}m"
        elif dps_value >= 1000:
            return f"{int(round(dps_value / 1000))}k"
        else:
            return str(dps_value)
    
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
