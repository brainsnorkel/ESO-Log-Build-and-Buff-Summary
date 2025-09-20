# Release Notes

## Version 0.1.0-beta

**Release Date**: TBD

### 🎉 Initial Beta Release

This is the first beta release of ESO Log Build and Buff Summary, providing comprehensive analysis of ESO trial logs.

### ✨ Features

- **Single Report Analysis**: Analyze any ESO Logs report by providing its code
- **Automatic Boss Detection**: Works with any trial - automatically detects boss encounters
- **Multi-Format Output**: Generate reports in Markdown, Discord markup, and PDF formats
- **Comprehensive Build Analysis**: 
  - Player gear sets with proper piece counting (2H weapons = 2 pieces)
  - Arena weapons, mythic items, and monster sets
  - Perfected and non-perfected set merging
- **Intelligent Buff/Debuff Tracking**: 
  - Track important raid buffs and debuffs with uptime percentages
  - Conditional tracking based on equipped gear (Aura of Pride, Tremorscale, Line-Breaker)
  - Oakensoul Ring detection with visual indicators
- **Professional PDF Reports**: 
  - Table of contents with navigation
  - Proper page breaks between encounters
  - Text wrapping in tables
- **Anonymization Support**: 
  - Option to generate anonymized reports with player names replaced by "anon1", "anon2", etc.
  - Removes URLs and identifying information while preserving all gear and buff data
- **Kill/Wipe Status**: Accurate fight outcome detection with boss health percentages

### 📦 Installation Options

- **Windows Installer**: Full installation with Start Menu shortcuts and uninstaller
- **Portable Version**: Single executable file, no installation required
- **Source Installation**: For developers and advanced users

### 🔧 Technical Details

- Built with Python 3.9+
- Uses ESO Logs API for data retrieval
- Supports all major ESO trials and encounters
- Cross-platform compatibility (Windows, macOS, Linux)

### 🐛 Known Issues

- This is a beta release - some features may be experimental
- Large reports may take longer to process
- API rate limits may apply during heavy usage

### 🚀 Getting Started

1. Download the installer from the [Releases](https://github.com/brainsnorkel/ESO-Log-Build-and-Buff-Summary/releases) page
2. Set up your ESO Logs API credentials
3. Run the tool with a report code: `ESO-Log-Build-and-Buff-Summary.exe --help`

### 📝 Feedback

This is a beta release, so feedback is welcome! Please report issues or suggestions on the [GitHub Issues](https://github.com/brainsnorkel/ESO-Log-Build-and-Buff-Summary/issues) page.

---

**Note**: This is a beta release intended for testing and feedback. The API and features may change in future versions.
