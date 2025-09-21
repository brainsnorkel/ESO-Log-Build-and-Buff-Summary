# Discord Webhook Integration

The ESO Log Build & Buff Summary tool now supports posting trial reports directly to Discord channels using webhooks. This feature allows you to automatically share trial analysis results with your guild or team.

## 🚀 Quick Start

### 1. Set up Discord Webhook

1. Go to your Discord server settings
2. Navigate to **Integrations** > **Webhooks**
3. Click **Create Webhook**
4. Configure the webhook:
   - **Name**: ESO Trial Reports (or your preferred name)
   - **Channel**: Select the channel where reports should be posted
   - **Avatar**: Optional custom avatar
5. Click **Copy Webhook URL**

### 2. Configure Webhook URL

Add the webhook URL to your `.env` file:

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE
```

### 3. Post Reports to Discord

Use the `--discord-webhook` parameter when running the tool:

```bash
# Post report directly to Discord
python single_report_tool.py A8TdmkfpP497xvyV --output discord --discord-webhook "https://discord.com/api/webhooks/..."

# Or use environment variable (if set in .env)
python single_report_tool.py A8TdmkfpP497xvyV --output discord --discord-webhook "$DISCORD_WEBHOOK_URL"

# Post individual boss fights (kill fights only) using DISCORD_WEBHOOK_URL from .env
python single_report_tool.py A8TdmkfpP497xvyV --discord-webhook-post
```

## 📋 Features

### Individual Fight Posting (`--discord-webhook-post`)
- **Kill Fights Only**: Automatically filters out wipe attempts, posting only successful boss kills
- **Separate Messages**: Each boss fight is posted as an individual Discord message
- **Rich Embeds**: Each fight gets its own embed with:
  - Fight-specific title and status
  - Team composition (tanks, healers, DPS)
  - Buff/debuff uptimes
  - Individual player builds and abilities
  - Fight counter (e.g., "Fight 1/3")
- **Summary Post**: After all fights, posts a summary with:
  - Total number of kills
  - ESO Logs URL for the full report
  - Generation timestamp

### Automatic Message Splitting
- Reports are automatically split into multiple messages if they exceed Discord's 2000 character limit
- Each message is clearly labeled with part numbers (e.g., "Part 1/3")

### Rich Embeds
- Reports are posted as Discord embeds with:
  - Green color scheme for kills, blue for summaries
  - Timestamps
  - Footer with version information
  - Part indicators for multi-part reports

### Error Handling
- Comprehensive error handling and logging
- Graceful fallback if webhook posting fails
- Local file generation continues even if Discord posting fails

## 🎯 Use Cases

### Guild Trial Analysis
Post trial reports directly to your guild's trial discussion channel for immediate analysis and discussion.

### Automated Reporting
Set up automated workflows to post reports after trial sessions.

### Team Coordination
Share build analysis and performance data with your trial team.

## 🔧 Advanced Usage

### Programmatic Usage

```python
import asyncio
from src.eso_builds.discord_webhook_client import DiscordWebhookClient

async def post_custom_report():
    webhook_url = "https://discord.com/api/webhooks/YOUR_URL"
    
    async with DiscordWebhookClient(webhook_url) as client:
        success = await client.post_report(
            report_content="Your report content here",
            title="Custom Trial Report"
        )
        
        if success:
            print("Posted successfully!")
        else:
            print("Failed to post")

# Run the function
asyncio.run(post_custom_report())
```

### Simple Messages

For non-report messages, use the simple message posting:

```python
async with DiscordWebhookClient(webhook_url) as client:
    await client.post_simple_message("🎮 Trial analysis complete!")
```

## 🔒 Security Notes

- **Keep webhook URLs private**: Never commit webhook URLs to version control
- **Use environment variables**: Store webhook URLs in `.env` files
- **Monitor usage**: Discord webhooks have rate limits
- **Revoke if compromised**: If a webhook URL is exposed, revoke and recreate it

## 📊 Example Output

When posted to Discord, reports appear as rich embeds with:

```
🎮 ESO Trial Report - A8TdmkfpP497xvyV

⚔️ Sunspire - Lylanar and Turlassil (Normal) - ✅ KILL

Tanks
• @Guardiantwofour: Plar - 4pc Pillager's Profit, 4pc Pillager's Profit
  ↳ Top Casts: Inner Rage (45), Pierce Armor (38), Heroic Slash (32)

Healers
• @HandOfTheGods: Plar - 4pc Spell Power Cure, 4pc Spell Power Cure  
  ↳ Top Healing: Combat Prayer (23.4%), Breath of Life (18.7%)

DPS
• @Katarany: OakenSorc - 1pc Oakensoul Ring, 4pc Sergeant's Mail
  ↳ Top Damage: Unstable Wall (18.7%), Lightning Flood (15.3%)

ESO Log Build & Buff Summary v0.2.0
```

## 🐛 Troubleshooting

### Common Issues

**"Resource not accessible by integration"**
- Check that the webhook URL is correct
- Ensure the webhook hasn't been deleted
- Verify the bot has permission to post in the channel

**"Failed to post to Discord webhook"**
- Check your internet connection
- Verify the webhook URL format
- Check Discord's service status

**Messages not appearing**
- Check the webhook is pointing to the correct channel
- Verify the webhook is enabled
- Check Discord permissions

### Debug Mode

Enable verbose logging to see detailed webhook information:

```bash
python single_report_tool.py A8TdmkfpP497xvyV --output discord --discord-webhook "URL" --verbose
```

## 📚 Related Documentation

- [Main Usage Guide](../README.md)
- [API Configuration](API_SETUP.md)
- [Output Formats](OUTPUT_FORMATS.md)
