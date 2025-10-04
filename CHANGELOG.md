# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Executable wrapper `eso-report` for easy command-line usage
- Installation script `install.sh` for setting up the command
- Comprehensive documentation structure in `docs/` directory
- CONTRIBUTING.md with contribution guidelines
- CHANGELOG.md for tracking changes

### Changed
- Reorganized documentation into structured directories:
  - `docs/user-guide/` - User-facing documentation
  - `docs/features/` - Feature documentation
  - `docs/development/` - Development notes and guides
  - `docs/api/` - API documentation (future)

## [0.3.0] - 2025-10-04

### Added
- Discord webhook improvements with per-fight posting
- Fight URLs in Discord webhook messages
- Kills-only default behavior (wipes optional with `--include-wipes`)
- Combined team composition format
- Whole number DPS display (e.g., `52k` instead of `52.3k` or percentages)
- Set abbreviations for mythic items
- Skill line abbreviations and subclass analysis
- Build name mappings for common gear combinations

### Changed
- Removed markdown output format (simplified to console and Discord only)
- Removed "Team Composition" heading from reports
- Removed "Buffs:" and "Debuffs:" prefixes (combined into single line)
- Changed "Set Problem?" to "Check Sets"
- Backticks now only around @handles (not entire line)
- Split player info into two lines (name/class, then gear)
- Increased Discord embed content limit to 4050 characters
- Shortened truncation message to "[truncated]"
- DPS players now show role icons (⚔️)
- Buffs displayed in consistent predefined order

### Fixed
- Mythic item abbreviations now work correctly
- Test import errors resolved
- Set abbreviations now applied to webhook reports

## [0.2.0] - 2025-10-03

### Added
- Action bar integration with API-based ability extraction
- Subclass analysis (e.g., Stamplar, MagSorc)
- Enhanced report generator with API-based action bars
- Build name mapper for common gear combinations
- Comprehensive buff/debuff tracking

### Changed
- Improved gear parser with 2H weapon handling
- Better LibSets integration
- Enhanced PDF formatting

### Fixed
- Arena weapon piece counting
- Mythic item handling
- Set completion detection

## [0.1.0] - Initial Release

### Added
- Single report analysis
- Multi-format output (Markdown, Discord, PDF)
- Gear set analysis
- Role detection
- Buff/debuff tracking
- Discord webhook integration

---

## Version History Legend

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes

