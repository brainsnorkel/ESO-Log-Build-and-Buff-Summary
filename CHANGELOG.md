# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial project setup with GitHub repository
- Python virtual environment configuration
- esologs-python dependency installation
- Basic project structure with README, .gitignore, and requirements.txt
- Project overview documentation
- Connection test script (`test_connection.py`) for verifying ESO Logs API setup
- Support for .env files with python-dotenv
- Comprehensive API credentials setup documentation
- ESO Logs GraphQL schema reference in documentation
- **Phase 1: Core Data Retrieval Foundation**
  - Complete data model architecture (Role, Difficulty, GearSet, PlayerBuild, etc.)
  - ESO Logs API client framework with rate limiting and error handling
  - GraphQL query templates for reports, fights, and gear data
  - Comprehensive testing framework for data models
- **Phase 2: Comprehensive Gear Detection**
  - All ESO set combinations detection (5+5+2, 5+4+3, 5+3+2+2, 4+4+4, etc.)
  - Perfected vs non-perfected set identification
  - Set name cleaning and normalization
  - Build archetype classification (Tank/Healer/DPS)
  - Slot validation and piece count validation
  - Edge case handling for unusual combinations
  - 15+ test cases covering all common ESO builds
- **Report Formatting**
  - Console output formatter matching project specification
  - Markdown report formatter with tables, headers, and links
  - Support for multiple output formats
- **Enhanced API Client**
  - Rate limiting (3500 requests/hour)
  - Comprehensive error handling and logging
  - Async context manager pattern
  - Methods for trials, rankings, and encounter details

### Changed
- Updated README.md with detailed setup instructions and API references
- Enhanced requirements.txt with python-dotenv dependency
- **Major README overhaul** with project status, roadmap, and comprehensive TODO list
- Restructured project documentation with clear development phases

### Fixed
- Connection test script import issues with esologs library
- API client initialization and GraphQL query structure

## [0.1.0] - 2025-09-19

### Added
- Initial commit with project overview
- GitHub private repository setup
- Basic project documentation
