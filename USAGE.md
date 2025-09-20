# ESO Logs Build and Buff Summary - Usage Guide

This guide provides detailed instructions and examples for using the ESO Logs Build and Buff Summary analyzer.

## 📚 Table of Contents

1. [Quick Start](#quick-start)
2. [Understanding Report Codes](#understanding-report-codes)
3. [Output Formats](#output-formats)
4. [Command Examples](#command-examples)
5. [Report Structure](#report-structure)
6. [Supported Trials](#supported-trials)
7. [Advanced Usage](#advanced-usage)
8. [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

### 1. Basic Analysis

The simplest way to analyze a log:

```bash
# Using report ID
python single_report_tool.py 3gjVGWB2dxCL8XAw

# Using full URL (automatically extracts report ID)
python single_report_tool.py "https://www.esologs.com/reports/3gjVGWB2dxCL8XAw"
```

This will:
- Analyze all boss encounters in the log
- Display results in the console
- Show player builds and intelligent buff/debuff uptimes
- Conditionally track effects based on equipped gear

### 2. Generate Files

To save reports to files:

```bash
python single_report_tool.py 3gjVGWB2dxCL8XAw --output all
```

This creates three files in the `reports/` directory:
- Markdown (.md) for documentation
- Discord (.txt) for chat sharing
- PDF (.pdf) for professional presentation

### 3. Anonymize Reports

To generate anonymized reports that remove player names, URLs, and identifying information:

```bash
python single_report_tool.py 3gjVGWB2dxCL8XAw --output all --anonymize
```

Anonymized reports will:
- Replace all player names with "anon1", "anon2", etc.
- Remove log URLs from the output
- Change the report title to "Anonymous Trial - Summary Report"
- Keep all gear and buff/debuff information for analysis purposes

## 🔍 Understanding Report Codes

### Where to Find Them

ESO Logs URLs contain the report code:

| URL Example | Report Code |
|-------------|-------------|
| `https://www.esologs.com/reports/3gjVGWB2dxCL8XAw` | `3gjVGWB2dxCL8XAw` |
| `https://www.esologs.com/reports/xbMVztd6Z4CBmFWQ` | `xbMVztd6Z4CBmFWQ` |
| `https://www.esologs.com/reports/gcrLFMZqdA3T6DzV` | `gcrLFMZqdA3T6DzV` |

**💡 Pro Tip:** You can use either the report code or the full URL - the tool automatically detects and extracts the report ID from URLs!

### Valid Report Codes

- Always 16 characters long
- Mix of letters and numbers
- Case-sensitive
- Examples: `3gjVGWB2dxCL8XAw`, `mtFqVzQPNBcCrd1h`

## 📄 Output Formats

### Console (Default)

Shows a summary in your terminal:

```bash
python single_report_tool.py 3gjVGWB2dxCL8XAw
```

**Output:**
```
🔍 Analyzing ESO Logs Report: 3gjVGWB2dxCL8XAw
==================================================
✅ Found 18 encounters
  • Red Witch Gedna Relvel (Veteran) - ✅ KILL
    Players: 2 tanks, 1 healers, 9 dps
  • Hall of Fleshcraft (Veteran Hard Mode) - ❌ WIPE (15.2%)
    Players: 2 tanks, 2 healers, 9 dps
```

### Markdown Format

Perfect for GitHub, documentation, or sharing:

```bash
python single_report_tool.py 3gjVGWB2dxCL8XAw --output markdown
```

**Features:**
- Clean tables with player builds
- Clickable table of contents
- Buff/debuff uptime tables
- Kill/wipe status with percentages

### Discord Format

Optimized for Discord chat:

```bash
python single_report_tool.py 3gjVGWB2dxCL8XAw --output markdown
```

**Features:**
- Discord-friendly formatting
- Bold text for emphasis
- Compact layout
- Mobile-friendly

### PDF Format

Professional document format:

```bash
python single_report_tool.py 3gjVGWB2dxCL8XAw --output pdf
```

**Features:**
- **Linked Table of Contents** - click to jump to sections
- Each encounter on separate page
- Professional styling
- Text wrapping in tables
- Print-ready format

## 💻 Command Examples

### Basic Commands

```bash
# Analyze and show in console (using report ID)
python single_report_tool.py 3gjVGWB2dxCL8XAw

# Analyze and show in console (using full URL)
python single_report_tool.py "https://www.esologs.com/reports/3gjVGWB2dxCL8XAw"

# Generate Markdown report
python single_report_tool.py 3gjVGWB2dxCL8XAw --output markdown

# Generate Discord report
python single_report_tool.py 3gjVGWB2dxCL8XAw --output discord

# Generate PDF with table of contents
python single_report_tool.py 3gjVGWB2dxCL8XAw --output pdf

# Generate all formats
python single_report_tool.py 3gjVGWB2dxCL8XAw --output all

# Generate anonymized reports (removes player names, URLs, etc.)
python single_report_tool.py 3gjVGWB2dxCL8XAw --output all --anonymize
```

### Custom Output Directory

```bash
# Save to custom directory
python single_report_tool.py 3gjVGWB2dxCL8XAw --output all --output-dir my_guild_reports

# Save to dated directory
python single_report_tool.py 3gjVGWB2dxCL8XAw --output pdf --output-dir "reports/$(date +%Y-%m-%d)"
```

### Verbose Logging

```bash
# See detailed processing information
python single_report_tool.py 3gjVGWB2dxCL8XAw --verbose

# Redirect verbose output to file
python single_report_tool.py 3gjVGWB2dxCL8XAw --verbose 2> analysis.log
```

### Batch Processing

```bash
# Analyze multiple reports
for code in 3gjVGWB2dxCL8XAw xbMVztd6Z4CBmFWQ gcrLFMZqdA3T6DzV; do
    echo "Processing $code..."
    python single_report_tool.py $code --output all --output-dir "reports/$code"
done
```

## 📊 Report Structure

### What Gets Analyzed

#### Boss Encounters
- **Automatic Detection**: Works with any trial
- **All Difficulties**: Normal, Veteran, Veteran Hard Mode
- **Kill/Wipe Status**: Accurate detection with boss health %

#### Player Builds (All 12 Players)
- **Roles**: 2 Tanks, 2 Healers, 8 DPS
- **Gear Sets**: Complete set analysis with piece counts
- **Special Items**: Arena weapons, mythics, monster sets

#### Buff/Debuff Tracking

**🟢 Buffs (Always Tracked):**
- Major Courage, Major Slayer, Major Berserk
- Major Force, Minor Toughness, Major Resolve
- Powerful Assault

**🟢 Conditional Buffs (Tracked Only When Present):**
- **Aura of Pride** - Only when a player wears **Spaulder of Ruin**

**🔴 Debuffs (Always Tracked):**
- Major Breach, Major Vulnerability, Minor Brittle
- Stagger, Crusher, Off Balance, Weakening

**🔴 Conditional Debuffs (Tracked Only When Present):**
- **Tremorscale** - Only when a player wears **2pc Tremorscale**
- **Line-Breaker** - Only when a player wears **5pc Alkosh**
- **Runic Sunder** - Only when it appears in the fight's debuff list

**⚠️ Special Indicators:**
- **Asterisk (*)** on Major Courage/Major Resolve = Oakensoul Ring wearer in group (may inflate %)
- **0.0%** = Effect not detected or not present in fight

**📊 Calculation Methods:**
- **Powerful Assault**: Uses specific ability ID `61771` only (ignores other variations)
- **All Other Effects**: Uses largest percentage among all ability ID variations
- **Multiple Sources**: Each buff/debuff can have multiple ability IDs from different spells/sources

### Class Name Mapping

**Automatic Class Abbreviations:**
- Arcanist → Arc, Sorcerer → Sorc, DragonKnight → DK
- Necromancer → Cro, Templar → Plar, Warden → Den, Nightblade → NB

**Special Prefixes:**
- **Oaken** prefix added when player wears Oakensoul Ring (e.g., "OakenSorc")

### Gear Set Detection

#### Regular Sets
```
5pc Ansuul's Torment, 5pc Lucent Echoes, 2pc Nazaray
```

#### Arena Weapons (2H = 2 pieces)
```
2pc The Maelstrom's Perfected Inferno Staff
2pc The Master's Perfected Restoration Staff
```

#### Mythic Items (1 piece)
```
1pc Oakensoul Ring
1pc Velothi Ur-Mage's Amulet
```

#### Monster Sets
```
1pc Slimecraw (1-piece bonus)
2pc Nazaray (full set)
```

## 🏰 Supported Trials

The tool automatically detects boss encounters in any trial, including:

### Current Trials
- **Lucent Citadel**: Zilyesset, Cavot Agnan, Orphic Shattered Shard, Baron Rize, Xoryn
- **Sanity's Edge**: Red Witch Gedna Relvel, Hall of Fleshcraft, Jynorah and Skorkhif, Blood Drinker Thisa, Overfiend Kazpian
- **Dreadsail Reef**: Lylanar and Turlassil, Reef Guardian, Tideborn Taleria, Coral Heart, Nazaray
- **Rockgrove**: Oaxiltso, Flame-Herald Bahsei, Xalvakka

### Legacy Trials
- **Cloudrest**: Z'Maja (+ Mini bosses)
- **Sunspire**: Lokkestiiz, Yolnahkriin, Nahviintaas
- **Kyne's Aegis**: Yandir, Vrol, Falgravn
- **And many more...**

## 🔧 Advanced Usage

### Environment Variables

You can set environment variables instead of using a `.env` file:

```bash
export ESO_LOGS_CLIENT_ID="your_client_id"
export ESO_LOGS_CLIENT_SECRET="your_client_secret"
python single_report_tool.py 3gjVGWB2dxCL8XAw
```

### Custom File Naming

The tool generates timestamped filenames automatically:
```
single_report_3gjVGWB2dxCL8XAw_20250920_1243.md
single_report_3gjVGWB2dxCL8XAw_20250920_1243.pdf
single_report_3gjVGWB2dxCL8XAw_20250920_1243_discord.txt
```

### Integration with Other Tools

#### Use with Git
```bash
# Analyze and commit reports
python single_report_tool.py 3gjVGWB2dxCL8XAw --output all
git add reports/
git commit -m "Add analysis for raid 3gjVGWB2dxCL8XAw"
```

#### Use with Discord Webhooks
```bash
# Generate Discord format and post via webhook
python single_report_tool.py 3gjVGWB2dxCL8XAw --output markdown
curl -X POST -H "Content-Type: application/json" \
  -d "@reports/single_report_3gjVGWB2dxCL8XAw_*_discord.txt" \
  YOUR_WEBHOOK_URL
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### "No encounter data found"

**Possible Causes:**
- Invalid report code
- Private/restricted report
- Very old report with incomplete data

**Solutions:**
```bash
# Verify the report code
python single_report_tool.py 3gjVGWB2dxCL8XAw --verbose

# Check if the report exists on ESO Logs website
# Visit: https://www.esologs.com/reports/3gjVGWB2dxCL8XAw
```

#### "API authentication failed"

**Check your credentials:**
```bash
# Verify .env file exists and has correct format
cat .env

# Should contain:
# ESO_LOGS_CLIENT_ID=your_client_id_here
# ESO_LOGS_CLIENT_SECRET=your_client_secret_here
```

#### "Rate limit exceeded"

**Solution:**
```bash
# Wait 60 seconds and try again
sleep 60
python single_report_tool.py 3gjVGWB2dxCL8XAw
```

#### "Module not found" errors

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Reinstall requirements
pip install -r requirements.txt
```

### Debug Mode

For detailed troubleshooting:

```bash
# Run with maximum verbosity
python single_report_tool.py 3gjVGWB2dxCL8XAw --verbose 2>&1 | tee debug.log

# Check the debug.log file for detailed information
```

### Getting Help

If you encounter issues:

1. **Check the logs** with `--verbose`
2. **Verify the report code** on ESO Logs website
3. **Check your API credentials**
4. **Create an issue** on GitHub with:
   - Python version: `python --version`
   - Error message (full traceback)
   - Report code you're analyzing
   - Your operating system

## 📈 Performance Tips

### Faster Analysis
- Use console output for quick checks
- Generate files only when needed
- Analyze reports during off-peak hours for better API response

### Batch Processing
```bash
# Create a script for multiple reports
#!/bin/bash
reports=(
    "3gjVGWB2dxCL8XAw"
    "xbMVztd6Z4CBmFWQ" 
    "gcrLFMZqdA3T6DzV"
)

for report in "${reports[@]}"; do
    echo "Analyzing $report..."
    python single_report_tool.py "$report" --output all
    sleep 5  # Rate limiting
done
```

---

**Need more help?** Check the main [README.md](README.md) or create an issue on GitHub!
