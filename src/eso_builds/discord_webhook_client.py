import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class DiscordWebhookClient:
    """Client for posting ESO trial reports to Discord via webhooks."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize the Discord webhook client.
        
        Args:
            webhook_url: Discord webhook URL. If not provided, will look for DISCORD_WEBHOOK_URL env var.
        """
        self.webhook_url = webhook_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
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
                "text": f"ESO Log Build & Buff Summary v0.2.0"
            }
        }
        
        # Add part indicator in footer if multiple messages
        if total_messages > 1:
            embed["footer"]["text"] += f" • Part {message_index + 1}/{total_messages}"
        
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
