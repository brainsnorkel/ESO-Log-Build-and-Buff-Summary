# Feature: Discord-Only with Fight URLs

**Branch:** `feature/discord-only-with-fight-urls`  
**Commits:** `ef5af45`, `6ce9f64`, `ebff39c`

## Summary

This feature simplifies the report generation workflow by:
1. Removing markdown report output
2. Focusing on Discord-formatted reports and webhook posting
3. Adding ESO Logs fight URLs to each Discord webhook message
4. Using combined team composition table (matches markdown format)
5. Posting only kills by default (wipes optional with `--include-wipes`)

## Changes Made

### 1. `single_report_tool.py`
- **Removed:**
  - Markdown output format option
  - `--discord-webhook` argument (redundant)
  - `MarkdownFormatter` import
  - All markdown generation logic

- **Updated:**
  - `--output` now accepts only `console` or `discord` (removed `markdown`, `both`, `all`)
  - Simplified `analyze_single_report()` function signature
  - Updated help text with clearer examples
  - Streamlined the report generation flow

### 2. `src/eso_builds/discord_webhook_client.py`
- **Added fight URLs to webhook titles:**
  - For **KILL** fights: URLs are appended to the title after DPS info
  - For **WIPE** fights: URLs are appended to the title after DPS info
  - Format: `https://www.esologs.com/reports/{report_code}?fight={fight_id}`
  
- **Consolidated team composition table:**
  - Changed from separate **Tanks**, **Healers**, and **DPS** sections
  - Now uses single **Team Composition** section
  - All players shown in one list: tanks → healers → DPS (sorted by percentage)
  - Matches markdown report format for consistency
  
- **Implementation:**
  - Uses `encounter.report_code` and `encounter.fight_id` from the EncounterResult model
  - URLs are added with a newline separator for better readability
  - All players show DPS percentage when available (not just DPS role)

## Usage Examples

### Console Output (unchanged)
```bash
python single_report_tool.py mTbKBVJGW8z6AR4P
```

### Generate Discord File Only
```bash
python single_report_tool.py mTbKBVJGW8z6AR4P --output discord
```

### Post Kills to Discord Webhook (recommended)
```bash
python single_report_tool.py mTbKBVJGW8z6AR4P --discord-webhook-post
```

### Post Kills AND Wipes to Discord Webhook
```bash
python single_report_tool.py mTbKBVJGW8z6AR4P --discord-webhook-post --include-wipes
```

### Both File and Webhook
```bash
python single_report_tool.py mTbKBVJGW8z6AR4P --output discord --discord-webhook-post
```

## Discord Webhook Format

Each fight posted to Discord now includes a clickable URL:

### Example KILL Message:
```
⚔️ Lokkestiiz (Veteran Hard Mode) - ✅ KILL - 443.2k DPS
https://www.esologs.com/reports/mTbKBVJGW8z6AR4P?fight=21

**Buffs:** Major Courage 100.0%, Major Slayer 61.3%, Major Force 43.5%

**Team Composition**
🛡️ Sets us up the bomb 4.6k: DK - 5xEB, 5xWM, 1xSpaulder
🛡️ Meow Knight King 9.7k: DK - 5xXoryn, 5xAS, 2xNazaray
💚 Şerenìty 1.3k: Plar - 2xGrand Rejuvenation, 5xPA, 5xStone-Talker
💚 Angëlbladë 1.3k: NB - 2xGrand Rejuvenation, 5xPillager, 5xOlorime
⚔️ Bleeblue the Formidable 62.8k: Arc - 5xOrders Wrath, 5xAE, 2xCrushing Wall, 1xVelothi
⚔️ Gelred 61.0k: Arc - 5xOrders Wrath, 5xAE, 2xCrushing Wall, 1xVelothi
[... more DPS ...]
```

### Example WIPE Message:
```
⚔️ Nahviintaas (Veteran Hard Mode) - ❌ WIPE (15.3%) - 315.4k DPS
https://www.esologs.com/reports/mTbKBVJGW8z6AR4P?fight=35

**Buffs:** Major Courage 97.1%, Powerful Assault 81.4%, Major Slayer 32.7%

**Team Composition**
🛡️ Sets us up the bomb: DK - 5xEB, 5xWM, 1xSpaulder
🛡️ Meow Knight King: DK - 5xXoryn, 5xAS, 2xNazaray
💚 Şerenìty: Plar - 2xGrand Rejuvenation, 5xPA, 5xStone-Talker
💚 Angëlbladë: NB - 2xGrand Rejuvenation, 5xPillager, 5xOlorime
⚔️ Bleeblue the Formidable (15.1%): Arc - 5xOrders Wrath, 5xAE, 2xCrushing Wall, 1xVelothi
⚔️ Gelred (14.9%): Arc - 5xOrders Wrath, 5xAE, 2xCrushing Wall, 1xVelothi
[... more DPS ...]
```

### 3. Default Behavior Change
- **Discord webhooks now post kills only by default**
- Added `--include-wipes` flag to optionally post wipe attempts
- Reduces Discord spam by focusing on successful attempts
- Wipes are still counted and shown in the summary message

## Benefits

1. **Simplified Workflow:** No more confusion about which output format to use
2. **Direct Links:** Easy access to full ESO Logs data for each fight
3. **Cleaner Codebase:** Removed unused markdown generation code
4. **Better Discord Integration:** Each fight message is self-contained with its own URL
5. **Less Spam:** Default behavior only posts kills, keeping Discord channels clean

## Testing

To test the changes:

```bash
# Clean up old reports
rm -rf reports/*

# Run with your test log
python single_report_tool.py YOUR_LOG_CODE --output discord --discord-webhook-post

# Check that:
# - Discord file is created in reports/
# - URLs appear in Discord webhook messages
# - URLs are clickable and point to the correct fight
```

## Next Steps

1. Test with a live Discord webhook
2. Verify URLs are correctly formatted for all fight types
3. Merge to develop after testing
4. Update main README.md if needed

