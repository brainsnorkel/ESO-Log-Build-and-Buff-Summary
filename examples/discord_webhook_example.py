#!/usr/bin/env python3
"""
Example script demonstrating Discord webhook integration for ESO trial reports.

This script shows how to use the Discord webhook functionality to post
trial reports directly to Discord channels.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the webhook client
from src.eso_builds.discord_webhook_client import DiscordWebhookClient

async def example_webhook_usage():
    """Example of how to use the Discord webhook client."""
    
    # Get webhook URL from environment variable
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL environment variable not set!")
        print("\nTo set up Discord webhook:")
        print("1. Go to your Discord server settings")
        print("2. Navigate to Integrations > Webhooks")
        print("3. Create a new webhook")
        print("4. Copy the webhook URL")
        print("5. Set DISCORD_WEBHOOK_URL in your .env file")
        return
    
    # Example report content (this would normally come from the analyzer)
    sample_report = """
**ESO Trial Report - Example**

### ⚔️ **Sunspire - Lylanar and Turlassil** (Normal) - ✅ KILL

**Tanks**
- `@Guardiantwofour`: Plar - 4pc Pillager's Profit, 4pc Pillager's Profit
  ↳ Top Casts: Inner Rage (45), Pierce Armor (38), Heroic Slash (32)

**Healers**  
- `@HandOfTheGods`: Plar - 4pc Spell Power Cure, 4pc Spell Power Cure
  ↳ Top Healing: Combat Prayer (23.4%), Breath of Life (18.7%), Extended Ritual (15.2%)

**DPS**
- `@Katarany`: OakenSorc - 1pc Oakensoul Ring, 4pc Sergeant's Mail
  ↳ Top Damage: Unstable Wall (18.7%), Lightning Flood (15.3%), Force Pulse (12.1%)
"""
    
    # Use the webhook client
    async with DiscordWebhookClient(webhook_url) as client:
        print("🚀 Posting sample report to Discord...")
        
        success = await client.post_report(
            report_content=sample_report,
            title="ESO Trial Report - Example"
        )
        
        if success:
            print("✅ Successfully posted to Discord!")
        else:
            print("❌ Failed to post to Discord")

async def example_individual_fights():
    """Example of posting individual fights (requires mock encounter data)."""
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL not set!")
        return
    
    # Note: This is a simplified example. In real usage, you would get encounter
    # objects from the SingleReportAnalyzer.analyze_report() method.
    print("📝 Note: Individual fight posting requires real encounter data from ESO Logs analysis.")
    print("   Use: python single_report_tool.py <report_id> --discord-webhook-post")
    print("   This will automatically post each kill fight as a separate Discord message.")

async def example_simple_message():
    """Example of posting a simple message (not as embed)."""
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL not set!")
        return
    
    async with DiscordWebhookClient(webhook_url) as client:
        print("🚀 Posting simple message to Discord...")
        
        success = await client.post_simple_message(
            "🎮 ESO Log Build & Buff Summary v0.2.1 is ready!\n"
            "Use the new Discord webhook feature to post trial reports directly to Discord.\n\n"
            "New feature: --discord-webhook-post for individual boss fight analysis!"
        )
        
        if success:
            print("✅ Simple message posted successfully!")
        else:
            print("❌ Failed to post simple message")

if __name__ == "__main__":
    print("Discord Webhook Example")
    print("=" * 30)
    
    # Run the examples
    asyncio.run(example_webhook_usage())
    print()
    asyncio.run(example_individual_fights())
    print()
    asyncio.run(example_simple_message())
