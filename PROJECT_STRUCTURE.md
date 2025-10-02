# ESO Builds Tool - Project Structure

This document describes the organized structure of the ESO Builds Tool project.

## Directory Structure

```
eso-builds/
├── config/                          # Configuration files
│   ├── ability_abbreviations.json   # Ability name abbreviations
│   ├── build_name_mappings.json     # Build name mappings
│   ├── set_abbreviations.json       # Set name abbreviations
│   └── LibSets_SetData.xlsm        # LibSets Excel data
├── data/                            # Data files and results
│   └── ability_comparison_results.json
├── docs/                            # Documentation
│   └── DISCORD_WEBHOOK.md
├── examples/                        # Example scripts
│   └── discord_webhook_example.py
├── reports/                         # Generated reports
│   ├── single_report_*.md          # Markdown reports
│   └── single_report_*_discord.txt # Discord reports
├── scripts/                         # Utility scripts
│   ├── create_combined_report.py
│   ├── generate_real_report.py
│   └── debug_sail_ripper.py
├── src/                            # Source code
│   └── eso_builds/
│       ├── __init__.py
│       ├── config_manager.py       # Configuration management
│       ├── models.py               # Data models
│       ├── api_client.py           # ESO Logs API client
│       ├── single_report_analyzer.py # Main analyzer
│       ├── report_formatter.py     # Console formatter
│       ├── markdown_formatter.py   # Markdown formatter
│       ├── discord_formatter.py    # Discord formatter
│       ├── discord_webhook_client.py # Discord webhook
│       ├── pdf_formatter.py        # PDF formatter
│       ├── subclass_analyzer.py    # Subclass analysis
│       ├── ability_abbreviations.py # Ability abbreviations
│       ├── build_name_mapper.py    # Build name mapping
│       ├── set_abbreviations.py    # Set abbreviations
│       └── [other modules]
├── tests/                          # Test files
│   ├── test_abbreviations.py
│   ├── test_action_bar_system.py
│   ├── test_api_abilities_simple.py
│   └── test_api_vs_scraping_abilities.py
├── venv/                           # Virtual environment
├── single_report_tool.py           # Main CLI tool
├── requirements.txt                # Python dependencies
├── README.md                       # Main documentation
├── USAGE.md                        # Usage documentation
└── PROJECT_STRUCTURE.md           # This file
```

## Configuration Management

The project uses a centralized configuration management system via `config_manager.py`:

### Key Features:
- **Automatic Path Resolution**: Automatically detects project root and sets up directory paths
- **Directory Creation**: Ensures all required directories exist
- **File Path Management**: Provides easy access to configuration and data files
- **Validation**: Validates that required configuration files exist

### Configuration Files:
- `config/ability_abbreviations.json` - Maps full ability names to abbreviations
- `config/build_name_mappings.json` - Maps two-set combinations to build names
- `config/set_abbreviations.json` - Maps full set names to abbreviations
- `config/LibSets_SetData.xlsm` - ESO set data from LibSets

## Usage

### Using ConfigManager:
```python
from src.eso_builds.config_manager import get_config_manager

config = get_config_manager()
config_file_path = config.get_config_path("ability_abbreviations.json")
reports_path = config.get_reports_path("my_report.md")
```

### Creating New Modules:
```python
from .config_manager import get_config_manager

class MyModule:
    def __init__(self):
        config_manager = get_config_manager()
        self.config_file = config_manager.get_config_path("my_config.json")
```

## Benefits of This Structure

1. **Separation of Concerns**: Configuration, data, scripts, and tests are clearly separated
2. **Maintainability**: Easy to find and modify configuration files
3. **Scalability**: Easy to add new configuration files or data sources
4. **Testing**: Test files are organized and separate from source code
5. **Documentation**: Clear documentation structure
6. **Deployment**: Easy to package and deploy with clear structure

## Migration Notes

- Configuration files moved from root to `config/` directory
- Test files moved from root to `tests/` directory
- Utility scripts moved from root to `scripts/` directory
- Data files moved from root to `data/` directory
- All modules updated to use `ConfigManager` for path resolution

## Adding New Features

When adding new features:

1. **Configuration**: Add new config files to `config/` directory
2. **Data**: Store data files in `data/` directory
3. **Scripts**: Add utility scripts to `scripts/` directory
4. **Tests**: Add test files to `tests/` directory
5. **Documentation**: Update relevant `.md` files in root or `docs/`
6. **Code**: Add new modules to `src/eso_builds/` and use `ConfigManager` for paths
