import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional
import json
from .models import Role
from .build_name_mapper import BuildNameMapper
from .ability_abbreviations import abbreviate_ability_name

logger = logging.getLogger(__name__)

class DiscordWebhookClient:
    """Client for posting ESO trial reports to Discord via webhooks."""
    
    # Role icons for visual identification
    ROLE_ICONS = {
        Role.TANK: '🛡️',
        Role.HEALER: '💚',
        Role.DPS: '⚔️'
    }
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize the Discord webhook client.
        
        Args:
            webhook_url: Discord webhook URL. If not provided, will look for DISCORD_WEBHOOK_URL env var.
        """
        self.webhook_url = webhook_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.build_name_mapper = BuildNameMapper()
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def post_individual_fights(self, encounters: list, report_title: str, log_url: str) -> bool:
        """
        Post individual boss fights as separate Discord messages.
        
        Args:
            encounters: List of encounter objects (both kill and wipe fights)
            report_title: Title for the report
            log_url: ESO Logs URL
            
        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            logger.error("Discord webhook URL not provided")
            return False
        
        if not self.session:
            logger.error("Discord webhook client not initialized. Use async context manager.")
            return False
        
        try:
            # Calculate kill and wipe counts using the same logic as PDF TOC
            kill_fights = [e for e in encounters if e.kill or e.boss_percentage <= 0.1]
            wipe_fights = [e for e in encounters if not (e.kill or e.boss_percentage <= 0.1)]
            total_kills = len(kill_fights)
            total_wipes = len(wipe_fights)
            total_fights = total_kills + total_wipes
            
            fight_number = 1
            
            # Post each kill fight as a separate message
            for encounter in kill_fights:
                # Format individual fight content
                fight_content = self._format_individual_fight(encounter)
                title = f"⚔️ {encounter.encounter_name} ({encounter.difficulty.value}) - ✅ KILL"
                if encounter.group_dps_total:
                    formatted_dps = self._format_dps_with_suffix(encounter.group_dps_total)
                    title += f" - **{formatted_dps} DPS**"
                
                # Create embed for individual fight
                embed = self._create_fight_embed(title, fight_content, fight_number, total_fights)
                
                payload = {"embeds": [embed]}
                
                async with self.session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:
                        logger.info(f"Successfully posted kill fight {fight_number} to Discord")
                    else:
                        logger.error(f"Failed to post fight to Discord: {response.status} - {await response.text()}")
                        return False
                
                fight_number += 1
            
            # Post each wipe fight as a separate message
            for encounter in wipe_fights:
                # Format individual fight content
                fight_content = self._format_individual_fight(encounter)
                title = f"⚔️ {encounter.encounter_name} ({encounter.difficulty.value}) - ❌ WIPE ({encounter.boss_percentage:.1f}%)"
                if encounter.group_dps_total:
                    formatted_dps = self._format_dps_with_suffix(encounter.group_dps_total)
                    title += f" - **{formatted_dps} DPS**"
                
                # Create embed for individual fight (red color for wipes)
                embed = self._create_fight_embed(title, fight_content, fight_number, total_fights, color=0xff0000)
                
                payload = {"embeds": [embed]}
                
                async with self.session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:
                        logger.info(f"Successfully posted wipe fight {fight_number} to Discord")
                    else:
                        logger.error(f"Failed to post fight to Discord: {response.status} - {await response.text()}")
                        return False
                
                fight_number += 1
            
            # Post summary with ESO logs URL
            summary_embed = self._create_summary_embed(report_title, log_url, total_kills, total_wipes)
            summary_payload = {"embeds": [summary_embed]}
            
            async with self.session.post(self.webhook_url, json=summary_payload) as response:
                if response.status == 204:
                    logger.info("Successfully posted summary with ESO logs URL")
                else:
                    logger.error(f"Failed to post summary to Discord: {response.status} - {await response.text()}")
                    return False
            
            logger.info(f"Successfully posted {total_fights} individual fights ({total_kills} kills, {total_wipes} wipes) and summary to Discord")
            return True
            
        except Exception as e:
            logger.error(f"Error posting individual fights to Discord webhook: {e}")
            return False

    async def post_report(self, report_content: str, title: str = "ESO Trial Report") -> bool:
        """
        Post a trial report to Discord via webhook.
        
        Args:
            report_content: The formatted report content to post
            title: Title for the Discord message
            
        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            logger.error("Discord webhook URL not provided")
            return False
        
        if not self.session:
            logger.error("Discord webhook client not initialized. Use async context manager.")
            return False
        
        # Discord has a 2000 character limit per message
        # Split content into multiple messages if needed
        messages = self._split_content(report_content, max_length=1900)  # Leave room for formatting
        
        try:
            for i, message_content in enumerate(messages):
                embed = self._create_embed(title, message_content, i, len(messages))
                payload = {"embeds": [embed]}
                
                async with self.session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:  # Discord returns 204 on success
                        logger.info(f"Successfully posted message {i+1}/{len(messages)} to Discord")
                    else:
                        logger.error(f"Failed to post to Discord: {response.status} - {await response.text()}")
                        return False
            
            logger.info(f"Successfully posted complete report to Discord ({len(messages)} messages)")
            return True
            
        except Exception as e:
            logger.error(f"Error posting to Discord webhook: {e}")
            return False
    
    def _split_content(self, content: str, max_length: int = 1900) -> list[str]:
        """
        Split content into multiple messages respecting Discord's character limit.
        
        Args:
            content: Content to split
            max_length: Maximum length per message
            
        Returns:
            List of message chunks
        """
        if len(content) <= max_length:
            return [content]
        
        messages = []
        lines = content.split('\n')
        current_message = ""
        
        for line in lines:
            # If adding this line would exceed the limit, start a new message
            if len(current_message) + len(line) + 1 > max_length:
                if current_message:
                    messages.append(current_message.rstrip())
                    current_message = line
                else:
                    # Line itself is too long, split it
                    while len(line) > max_length:
                        messages.append(line[:max_length])
                        line = line[max_length:]
                    current_message = line
            else:
                current_message += line + '\n'
        
        if current_message:
            messages.append(current_message.rstrip())
        
        return messages
    
    def _create_embed(self, title: str, content: str, message_index: int, total_messages: int) -> Dict[str, Any]:
        """
        Create a Discord embed for the message.
        
        Args:
            title: Title for the embed
            content: Content of the message
            message_index: Index of this message (0-based)
            total_messages: Total number of messages
            
        Returns:
            Discord embed dictionary
        """
        embed = {
            "title": title if message_index == 0 else f"{title} (Part {message_index + 1})",
            "description": content,
            "color": 0x00ff00,  # Green color
            "timestamp": None,  # Will be set to current time by Discord
            "footer": {
                "text": f"ESO Log Build & Buff Summary v0.2.1"
            }
        }
        
        # Add part indicator in footer if multiple messages
        if total_messages > 1:
            embed["footer"]["text"] += f" • Part {message_index + 1}/{total_messages}"
        
        return embed
    
    def _format_individual_fight(self, encounter) -> str:
        """
        Format an individual fight for Discord posting.
        
        Args:
            encounter: EncounterResult object
            
        Returns:
            Formatted fight content
        """
        lines = []
        
        
        # Buffs/Debuffs
        if encounter.buff_uptimes:
            # buff_uptimes is a Dict[str, float] where keys are buff names and values are uptime percentages
            buff_items = [f"{name} {uptime:.1f}%" for name, uptime in encounter.buff_uptimes.items()]
            if buff_items:
                lines.append(f"**Buffs:** {', '.join(buff_items)}")
            lines.append("")  # Empty line
        
        # Team composition
        tanks = encounter.tanks
        healers = encounter.healers
        dps = encounter.dps
        
        if tanks:
            lines.append("**Tanks**")
            for player in tanks:
                role_icon = self.ROLE_ICONS.get(player.role, '')
                player_name = f"`{player.name}`" if "@" in player.name else player.name
                gear_text = self._format_gear_sets_compact(player.gear_sets)
                
                # Add set problem indicator if needed
                if self._has_incomplete_sets(player.gear_sets):
                    gear_text = f"**Set Problem?:** {gear_text}"
                
                class_name = self._get_class_display_name(player.character_class, player)
                lines.append(f"{role_icon} {player_name}: {class_name} - {gear_text}")
                
                # Add action bars if available
                if player.abilities and (player.abilities.get('bar1') or player.abilities.get('bar2')):
                    action_bars = self._format_action_bars_for_discord(player)
                    if action_bars:
                        lines.append(f"  ↳ {action_bars}")
            
            lines.append("")  # Empty line
        
        if healers:
            lines.append("**Healers**")
            for player in healers:
                role_icon = self.ROLE_ICONS.get(player.role, '')
                player_name = f"`{player.name}`" if "@" in player.name else player.name
                gear_text = self._format_gear_sets_compact(player.gear_sets)
                
                # Add set problem indicator if needed
                if self._has_incomplete_sets(player.gear_sets):
                    gear_text = f"**Set Problem?:** {gear_text}"
                
                class_name = self._get_class_display_name(player.character_class, player)
                lines.append(f"{role_icon} {player_name}: {class_name} - {gear_text}")
                
                # Add action bars if available
                if player.abilities and (player.abilities.get('bar1') or player.abilities.get('bar2')):
                    action_bars = self._format_action_bars_for_discord(player)
                    if action_bars:
                        lines.append(f"  ↳ {action_bars}")
            
            lines.append("")  # Empty line
        
        if dps:
            lines.append("**DPS**")
            # Sort DPS players by damage percentage (highest first)
            dps_sorted = sorted(dps, key=lambda p: p.dps_data.get('dps_percentage', 0) if p.dps_data else 0, reverse=True)
            
            for player in dps_sorted:
                role_icon = self.ROLE_ICONS.get(player.role, '')
                player_name = player.name
                
                # Add DPS percentage to player name for DPS players
                if player.dps_data and 'dps_percentage' in player.dps_data:
                    dps_percentage = player.dps_data['dps_percentage']
                    player_name = f"{player_name} ({dps_percentage:.1f}%)"
                
                player_name = f"`{player_name}`" if "@" in player_name else player_name
                gear_text = self._format_gear_sets_compact(player.gear_sets)
                
                # Add set problem indicator if needed
                if self._has_incomplete_sets(player.gear_sets):
                    gear_text = f"**Set Problem?:** {gear_text}"
                
                class_name = self._get_class_display_name(player.character_class, player)
                lines.append(f"{role_icon} {player_name}: {class_name} - {gear_text}")
                
                # Add action bars if available
                if player.abilities and (player.abilities.get('bar1') or player.abilities.get('bar2')):
                    action_bars = self._format_action_bars_for_discord(player)
                    if action_bars:
                        lines.append(f"  ↳ {action_bars}")
        
        return "\n".join(lines)
    
    def _format_gear_sets_compact(self, gear_sets) -> str:
        """Format gear sets in compact Discord format."""
        if not gear_sets:
            return "No gear data"
        
        # First, apply build name mapping on full set names
        full_gear_sets = []
        for gear_set in gear_sets:
            set_str = f"{gear_set.piece_count}pc {gear_set.name}"
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
            # For Discord webhook, we don't use the abbreviate_set_name function
            # since it's not imported. We'll just convert to the Discord format.
            return f"{piece_count}x{set_name}"
        elif 'x' in set_str:
            # Already in abbreviated format
            return set_str
        else:
            # Fallback
            return set_str
    
    def _format_top_abilities_compact(self, top_abilities) -> str:
        """Format top abilities in compact Discord format."""
        if not top_abilities:
            return "*No abilities*"
        
        formatted_abilities = []
        for ability in top_abilities:
            name = ability.get('name', 'Unknown')
            percentage = ability.get('percentage', 0.0)
            formatted_abilities.append(f"{name} ({percentage:.1f}%)")
        
        return ", ".join(formatted_abilities)
    
    def _format_cast_counts_compact(self, top_abilities) -> str:
        """Format cast counts in compact Discord format."""
        if not top_abilities:
            return "*No abilities*"
        
        formatted_abilities = []
        for ability in top_abilities:
            name = ability.get('name', 'Unknown')
            casts = ability.get('casts', 0)
            formatted_abilities.append(f"{name} ({casts})")
        
        return ", ".join(formatted_abilities)
    
    def _has_incomplete_sets(self, gear_sets) -> bool:
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
        class_mapping = {
            'Arcanist': 'Arc',
            'Sorcerer': 'Sorc',
            'DragonKnight': 'DK',
            'Necromancer': 'Cro',
            'Templar': 'Plar',
            'Warden': 'Den',
            'Nightblade': 'NB'
        }
        
        mapped_class = class_mapping.get(class_name, class_name)
        
        # Check for Oakensoul Ring if player_build is provided
        if player_build and player_build.gear_sets:
            has_oakensoul = any(
                'oakensoul' in gear_set.name.lower() 
                for gear_set in player_build.gear_sets
            )
            if has_oakensoul:
                return f"Oaken{mapped_class}"
        
        return mapped_class
    
    def _format_action_bars_for_discord(self, player) -> str:
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
        """Format DPS value with k/m suffixes to one decimal place."""
        if dps_value >= 1000000:
            return f"{dps_value / 1000000:.1f}m"
        elif dps_value >= 1000:
            return f"{dps_value / 1000:.1f}k"
        else:
            return str(dps_value)
    
    def _create_fight_embed(self, title: str, content: str, fight_number: int, total_fights: int, color: int = 0x00ff00) -> Dict[str, Any]:
        """Create a Discord embed for an individual fight."""
        # Ensure content fits within Discord limits
        if len(content) > 4000:  # Discord embed description limit is 4096, leave some buffer
            content = content[:3950] + "\n... *[Content truncated]*"
        
        embed = {
            "title": title,
            "description": content,
            "color": color,  # Green for kills (0x00ff00), red for wipes (0xff0000)
            "timestamp": None,  # Will be set to current time by Discord
            "footer": {
                "text": f"ESO Log Build & Buff Summary v0.2.1 • Fight {fight_number}/{total_fights}"
            }
        }
        
        return embed
    
    def _create_summary_embed(self, report_title: str, log_url: str, total_kills: int, total_wipes: int = 0) -> Dict[str, Any]:
        """Create a Discord embed for the summary with ESO logs URL."""
        content = f"**📊 Trial Analysis Complete**\n\n"
        content += f"**Total Kills:** {total_kills}\n"
        content += f"**Total Wipes:** {total_wipes}\n"
        content += f"**Log URL:** {log_url}\n\n"
        content += f"*Generated by ESO Log Build & Buff Summary*"
        
        embed = {
            "title": f"🎮 {report_title} - Summary",
            "description": content,
            "color": 0x0099ff,  # Blue color for summary
            "timestamp": None,
            "footer": {
                "text": "ESO Log Build & Buff Summary v0.2.1"
            }
        }
        
        return embed
    
    async def post_simple_message(self, message: str) -> bool:
        """
        Post a simple text message to Discord (not as embed).
        
        Args:
            message: Message to post
            
        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            logger.error("Discord webhook URL not provided")
            return False
        
        if not self.session:
            logger.error("Discord webhook client not initialized. Use async context manager.")
            return False
        
        # Split message if too long
        messages = self._split_content(message, max_length=1900)
        
        try:
            for message_content in messages:
                payload = {"content": message_content}
                
                async with self.session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:
                        logger.info("Successfully posted simple message to Discord")
                    else:
                        logger.error(f"Failed to post to Discord: {response.status} - {await response.text()}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error posting simple message to Discord: {e}")
            return False


# Convenience function for easy usage
async def post_report_to_discord(webhook_url: str, report_content: str, title: str = "ESO Trial Report") -> bool:
    """
    Convenience function to post a report to Discord.
    
    Args:
        webhook_url: Discord webhook URL
        report_content: Formatted report content
        title: Title for the report
        
    Returns:
        True if successful, False otherwise
    """
    async with DiscordWebhookClient(webhook_url) as client:
        return await client.post_report(report_content, title)
