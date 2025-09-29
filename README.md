# ESO Top Builds

A Python tool for analyzing Elder Scrolls Online (ESO) trial logs from [ESO Logs](https://www.esologs.com) to generate detailed build and buff analysis reports.

## 🎯 Features

- **Single Report Analysis**: Analyze any ESO Logs report by providing its code
- **Automatic Boss Detection**: Works with any trial - automatically detects boss encounters
- **Multi-Format Output**: Generate reports in Markdown, Discord markup, and PDF formats
- **Discord Webhook Integration**: Post reports directly to Discord channels via webhooks
- **Comprehensive Build Analysis**: 
  - Player gear sets with proper piece counting (2H weapons = 2 pieces)
  - Arena weapons, mythic items, and monster sets
  - Perfected and non-perfected set merging
  - Dynamic set requirements using LibSets database
  - Set completion warnings for incomplete 5-piece sets
- **Role-Specific Ability Analysis**:
  - Tanks: Top cast abilities with cast counts
  - Healers: Top healing abilities with damage percentages
  - DPS: Top damage abilities with contribution percentages
- **Buff/Debuff Tracking**: Track important raid buffs and debuffs with uptime percentages
- **Professional PDF Reports**: 
  - Table of contents with navigation
  - Proper page breaks between encounters
  - Text wrapping in tables
- **Kill/Wipe Status**: Accurate fight outcome detection with boss health percentages

## ⚡ Quick Start

Analyze any ESO Logs report with a simple command:

```bash
# Basic analysis (console output)
python single_report_tool.py <report_code>

# Generate all formats (markdown, discord, pdf)
python single_report_tool.py <report_code> --output all

# Post to Discord webhook
python single_report_tool.py <report_code> --output discord --discord-webhook "https://discord.com/api/webhooks/..."
```

**Example:**
```bash
python single_report_tool.py 3gjVGWB2dxCL8XAw --output all
```

> 📋 **Report Code**: Extract from any ESO Logs URL: `https://www.esologs.com/reports/3gjVGWB2dxCL8XAw` → `3gjVGWB2dxCL8XAw`

### 📖 Command Help

```bash
python single_report_tool.py --help
```

**Usage:**
```bash
python single_report_tool.py <report_code> [options]

Positional Arguments:
  report_code           ESO Logs report code or full URL (e.g. 3gjVGWB2dxCL8XAw or https://www.esologs.com/reports/3gjVGWB2dxCL8XAw)

Options:
  --output {console,markdown,discord,pdf,all}
                        Output format (default: console)
  --output-dir DIR      Directory for output files (default: reports)
  --discord-webhook URL Discord webhook URL to post reports directly to Discord
  --discord-webhook-post  Post individual boss fights to Discord using DISCORD_WEBHOOK_URL from .env
  --verbose, -v         Enable verbose logging
  --anonymize           Anonymize player names and remove URLs
  --help, -h           Show help message
```

## 📋 Requirements

- Python 3.9+
- ESO Logs API credentials (Client ID and Secret)
- Internet connection for API access

## 🚀 Installation

1. **Clone the repository:**
```bash
git clone https://github.com/brainsnorkel/ESO-Top-Builds.git
cd ESO-Top-Builds
```

2. **Create and activate a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up API credentials:**
   - Go to [ESO Logs API](https://www.esologs.com/api/clients/) and create a new client
   - Create a `.env` file in the project root:
```bash
ESO_LOGS_CLIENT_ID=your_client_id_here
ESO_LOGS_CLIENT_SECRET=your_client_secret_here
```

## 📖 Usage

### Basic Usage

Analyze a single ESO Logs report:

```bash
python single_report_tool.py <report_code>
```

**Examples:**
```bash
# Using report ID
python single_report_tool.py 3gjVGWB2dxCL8XAw

# Using full URL (automatically extracts report ID)
python single_report_tool.py "https://www.esologs.com/reports/3gjVGWB2dxCL8XAw"
```

### Output Formats

Choose your preferred output format:

```bash
# Console output only (default) - using report ID
python single_report_tool.py 3gjVGWB2dxCL8XAw

# Console output only (default) - using full URL
python single_report_tool.py "https://www.esologs.com/reports/3gjVGWB2dxCL8XAw"

# Generate Markdown report
python single_report_tool.py 3gjVGWB2dxCL8XAw --output markdown

# Generate Discord report
python single_report_tool.py 3gjVGWB2dxCL8XAw --output discord

# Generate PDF report
python single_report_tool.py 3gjVGWB2dxCL8XAw --output pdf

# Generate all formats
python single_report_tool.py 3gjVGWB2dxCL8XAw --output all

# Post directly to Discord webhook
python single_report_tool.py 3gjVGWB2dxCL8XAw --output discord --discord-webhook "https://discord.com/api/webhooks/..."

# Post individual boss fights to Discord (uses DISCORD_WEBHOOK_URL from .env)
python single_report_tool.py 3gjVGWB2dxCL8XAw --discord-webhook-post
```

### Advanced Options

```bash
# Specify output directory
python single_report_tool.py 3gjVGWB2dxCL8XAw --output all --output-dir my_reports

# Enable verbose logging
python single_report_tool.py 3gjVGWB2dxCL8XAw --verbose
```

### Complete Command Reference

```bash
python single_report_tool.py <report_code> [options]

Arguments:
  report_code           ESO Logs report code or full URL (e.g., 3gjVGWB2dxCL8XAw or https://www.esologs.com/reports/3gjVGWB2dxCL8XAw)

Options:
  --output {console,markdown,discord,pdf,all}
                        Output format (default: console)
  --output-dir DIR      Directory for output files (default: reports)
  --discord-webhook URL Discord webhook URL to post reports directly to Discord
  --discord-webhook-post  Post individual boss fights to Discord using DISCORD_WEBHOOK_URL from .env (kill fights only)
  --verbose, -v         Enable verbose logging
  --help, -h           Show help message
```

## 🔍 Finding Report Codes

ESO Logs report codes can be found in the URL of any log:

**Example URL:** `https://www.esologs.com/reports/3gjVGWB2dxCL8XAw`
**Report Code:** `3gjVGWB2dxCL8XAw`

## 📊 Report Contents

### What's Analyzed

- **All Boss Encounters**: Automatically detects boss fights in any trial
- **Player Builds**: Complete gear analysis for all 12 players (2 tanks, 2 healers, 8 DPS)
- **Gear Sets**: 
  - Regular sets with proper piece counting
  - Arena weapons (Maelstrom, Master's, etc.)
  - Mythic items (Oakensoul, Velothi Ur-Mage's Amulet, etc.)
  - Monster sets (1-piece and 2-piece)
- **Buff/Debuff Uptimes**: 
  - **Buffs**: Major Courage, Major Slayer, Major Berserk, Major Force, Minor Toughness, Major Resolve, Pillager's Profit, Powerful Assault
  - **Debuffs**: Major Breach, Major Vulnerability, Minor Brittle, Stagger, Crusher, Off Balance, Weakening

### Report Formats

#### 📝 Markdown (.md)
- Clean, readable format for sharing and documentation
- Tables for player builds
- Buff/debuff uptime tables
- Kill/wipe status with boss percentages

#### 💬 Discord (.txt)
- Optimized for Discord chat sharing
- Bold formatting for emphasis
- Compact layout for mobile viewing

#### 📄 PDF (.pdf)
- Professional document format
- **Linked Table of Contents** for easy navigation
- Each encounter on separate page
- Text wrapping in tables
- Proper page break control

## 🏗️ Project Structure

```
ESO-Top-Builds/
├── src/eso_builds/           # Main package
│   ├── api_client.py         # ESO Logs API client
│   ├── models.py             # Data models
│   ├── gear_parser.py        # Gear set detection logic
│   ├── excel_libsets_parser.py # LibSets Excel data parser
│   ├── markdown_formatter.py # Markdown report formatter
│   ├── discord_formatter.py  # Discord report formatter
│   ├── pdf_formatter.py      # PDF report formatter
│   └── single_report_analyzer.py # Single report analysis
├── single_report_tool.py     # CLI tool
├── requirements.txt          # Python dependencies
├── .env                      # API credentials (create this)
├── VERSION                   # Application version
├── examples/                 # Example reports
└── reports/                  # Generated reports (auto-created)
```

## 🛠️ Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Commit your changes: `git commit -m "Add feature"`
7. Push to your branch: `git push origin feature-name`
8. Create a Pull Request

## 📊 Example Reports

Check out these sample reports generated by the tool:

### 📋 [Sunspire Trial Report](examples/single_report_A8TdmkfpP497xvyV_20250921_1506.md)
**Report ID:** `A8TdmkfpP497xvyV` | **Trial:** Sunspire (6 encounters)
- **Features:** Complete gear analysis with Top Casts for tanks, Top Healing for healers, and Top Damage for DPS
- **Highlights:** Shows "Set Problem?:" indicators for incomplete 5-piece sets
- **Formats:** [Markdown](examples/single_report_A8TdmkfpP497xvyV_20250921_1506.md) | [Discord](examples/single_report_A8TdmkfpP497xvyV_20250921_1506_discord.txt) | [PDF](examples/single_report_A8TdmkfpP497xvyV_20250921_1506.pdf)

### 🎯 Key Features Demonstrated
- **Dynamic Set Requirements:** Uses LibSets data to accurately determine piece requirements for all ESO sets
- **Role-Specific Abilities:** 
  - Tanks: Top Casts (with cast counts)
  - Healers: Top Healing abilities (with percentages)
  - DPS: Top Damage abilities (with percentages)
- **Set Completion Warnings:** Bold "Set Problem?:" indicators for incomplete 5-piece sets
- **Multi-Format Output:** Same data formatted for Markdown, Discord, and PDF consumption

## 📝 Example Output

### Console Output
```
🔍 Analyzing ESO Logs Report: 3gjVGWB2dxCL8XAw
==================================================
✅ Found 18 encounters
  • Red Witch Gedna Relvel (Veteran)
    Players: 2 tanks, 1 healers, 9 dps
  • Hall of Fleshcraft (Veteran Hard Mode)
    Players: 2 tanks, 2 healers, 9 dps
  ...

📄 PDF report saved to: reports/single_report_3gjVGWB2dxCL8XAw_20250920_1243.pdf
```

### Generated Files
- `single_report_3gjVGWB2dxCL8XAw_20250920_1243.md` - Markdown format
- `single_report_3gjVGWB2dxCL8XAw_20250920_1243_discord.txt` - Discord format  
- `single_report_3gjVGWB2dxCL8XAw_20250920_1243.pdf` - PDF format with TOC

## 🔧 Troubleshooting

### Common Issues

**"No module named 'esologs'"**
- Make sure you've activated your virtual environment and installed requirements

**"API authentication failed"**
- Check your `.env` file has the correct CLIENT_ID and CLIENT_SECRET
- Verify your ESO Logs API client is active

**"No encounter data found"**
- Verify the report code is correct
- Some very old reports may not have complete data
- Private reports may not be accessible

**"HTTP 429 - Rate Limited"**
- The tool respects ESO Logs rate limits
- Wait a few minutes and try again

### Getting Help

- Check the [Issues](https://github.com/brainsnorkel/ESO-Top-Builds/issues) page
- Create a new issue with:
  - Your Python version
  - Complete error message
  - Report code you're trying to analyze
  - Steps to reproduce

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [ESO Logs](https://www.esologs.com) for providing the API and data
- [esologs-python](https://github.com/Dreemurro/esologs-python) library for API access
- [LibSets](https://github.com/Baertram/LibSets) for providing comprehensive ESO item set data and requirements
- The Elder Scrolls Online community for testing and feedback

## 🔗 Links

- [ESO Logs](https://www.esologs.com)
- [ESO Logs API Documentation](https://www.esologs.com/v2-api-docs/eso/)
- [Elder Scrolls Online](https://www.elderscrollsonline.com/)

---

**Made with ❤️ for the ESO community**
