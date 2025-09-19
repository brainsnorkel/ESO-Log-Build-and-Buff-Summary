# ESO Top Builds

A Python project that analyzes Elder Scrolls Online logs using the esologs.com API to generate reports of top builds for different boss encounters.

## Overview

This project uses the [esologs-python](https://github.com/knowlen/esologs-python) library to access the esologs.com API. The API uses GraphQL and the full schema documentation is available at [https://www.esologs.com/v2-api-docs/eso/](https://www.esologs.com/v2-api-docs/eso/).

For each trial, it takes the five top scoring logged encounters for the current update and builds a report for each boss encounter showing the class and gear of DPS, tanks, and healers.

## Output Format

For each boss encounter, the report will show:

```
Boss Name (e.g., Ossein Cage)
Rank 1: {url to log}
Hall of Fleshcraft
Tank 1: Dragonknight, 5pc Perfected Pearlescent Ward, 5pc Lucent Echoes, 2pc Nazaray
Tank 2: Templar, 5pc Saxhleel, 5pc Powerful Assault...
Healer 1: Arcanist, ...
Healer 2: Warden, ...
DPS 1: Necromancer, ...
DPS 2: ...
...
DPS 8: 

Rank 2: ...
```

## Setup

1. Clone the repository:
```bash
git clone https://github.com/brainsnorkel/ESO-Top-Builds.git
cd ESO-Top-Builds
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your esologs.com API credentials (see Configuration section)

## Configuration

### ESO Logs API Credentials

To use this project, you need to obtain API credentials from esologs.com:

1. **Register your application** at https://www.esologs.com/api/clients
2. **Get your credentials**: You'll receive a `client_id` and `client_secret`
3. **Set up environment variables** (recommended for security):

```bash
export ESOLOGS_ID="your_client_id_here"
export ESOLOGS_SECRET="your_client_secret_here"
```

**Alternative: .env file** (make sure it's in your .gitignore):
```
ESOLOGS_ID=your_client_id_here
ESOLOGS_SECRET=your_client_secret_here
```

### Test Your Connection

Run the connection test to verify your setup:

```bash
# Activate virtual environment first
source venv/bin/activate

# Run the connection test
python test_connection.py
```

This will verify:
- ✅ API credentials are configured
- ✅ Authentication is working  
- ✅ Basic API queries are successful

## Usage

### Basic Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Test your connection
python test_connection.py

# Generate report for a specific trial (when implemented)
python -m src.eso_builds --trial "Ossein Cage" --output markdown

# Analyze a specific log report (planned feature)
python -m src.eso_builds --report 3gjVGWB2dxCL8XAw --output markdown
```

### Output Formats

The tool supports multiple output formats:

- **Console Output**: Human-readable text format matching the specification
- **Markdown Reports**: Professional markdown files with tables and links
- **Multiple Trials**: Combined reports for multiple trials

### Example Output Structure

```
Ossein Cage
Rank 1: https://www.esologs.com/reports/abc123
Encounter: Hall of Fleshcraft Veteran Hard Mode
Tank 1: Dragonknight, 5pc Perfected Pearlescent Ward, 5pc Lucent Echoes, 2pc Nazaray
Tank 2: Templar, 5pc Saxhleel, 5pc Powerful Assault...
Healer 1: Arcanist, ...
Healer 2: Warden, ...
DPS 1: Necromancer, ...
DPS 2-8: ...

Encounter: Jynorah and Skorkhif Veteran Hard Mode
[All encounters for this ranking...]

Rank 2: [Next best log...]
```

## Project Status

### ✅ Completed Features

- **🏗️ Core Architecture**: Complete data models and API client framework
- **🔌 ESO Logs Integration**: Working API client with rate limiting and error handling  
- **⚙️ Comprehensive Gear Detection**: All ESO set combinations (5+5+2, 5+4+3, etc.)
- **🛡️ Build Classification**: Automatic tank/healer/DPS build detection
- **📊 Report Formatting**: Console and markdown output formats
- **🧪 Comprehensive Testing**: Full test suite with 15+ gear combinations

### 🔄 In Progress

- **📝 Markdown Reports**: Professional markdown files per trial *(in progress)*
- **🎯 Trial Report Generation**: Complete end-to-end report creation

### 📋 Planned Features

#### Core Functionality
- **🏆 Top Rankings Analysis**: Get top 5 scoring encounters per trial
- **🔗 Clickable URLs**: Include links to original logs  
- **🎛️ Trial Selection**: Choose which trials to analyze
- **💻 CLI Tool**: Command-line interface for easy usage

#### Advanced Features  
- **📄 Single Report Mode**: Analyze specific log IDs (e.g. `3gjVGWB2dxCL8XAw`)
- **🔍 Direct Log Parsing**: Parse individual reports from URLs
- **✅ Report Validation**: Validate report IDs and check existence
- **💾 File Output**: Save markdown reports to files
- **🧪 Integration Tests**: Real API testing with credentials

### 🚧 Development Roadmap

1. **Phase 1**: ✅ Foundation & Data Models *(Complete)*
2. **Phase 2**: ✅ Gear Detection & Parsing *(Complete)*  
3. **Phase 3**: 🔄 Report Generation & CLI *(In Progress)*
4. **Phase 4**: 📋 Advanced Features & Polish *(Planned)*

## Development

This project is actively under development. See the [CHANGELOG.md](CHANGELOG.md) for detailed updates.

### Architecture

```
src/eso_builds/
├── models.py           # Data structures (TrialReport, PlayerBuild, etc.)
├── api_client.py       # ESO Logs API client with rate limiting
├── gear_parser.py      # Comprehensive gear set detection
├── report_formatter.py # Console output formatting  
├── markdown_formatter.py # Markdown report generation
└── api_queries.py      # GraphQL query templates
```

### Testing

```bash
# Test data models and core functionality
python test_phase1.py

# Test gear detection (all ESO set combinations)
python test_gear_combinations.py

# Test Phase 2 components  
python test_phase2.py
```

### API Reference

- **ESO Logs Python Library**: [esologs-python](https://github.com/knowlen/esologs-python)
- **ESO Logs GraphQL API**: [Schema Documentation](https://www.esologs.com/v2-api-docs/eso/)
- **ESO Logs Website**: [esologs.com](https://www.esologs.com)

## Contributing

This project follows the development practices specified in the user requirements:

- **Automated Testing**: Test cases for new features documented in [TESTING.md](TESTING.md)
- **Change Tracking**: All changes logged in [CHANGELOG.md](CHANGELOG.md)  
- **Frequent Commits**: Regular git commits with descriptive messages
- **Documentation**: README kept up-to-date with project progress

### Current TODO List

#### Core Features (High Priority)
- [ ] Generate complete trial reports (Trial → Rank 1-5 → All Encounters → All Players)
- [ ] Include clickable URLs to original logs for each rank
- [ ] Add trial selection (choose which trials to analyze)  
- [ ] Create command-line interface for running analysis
- [ ] Add comprehensive integration tests with API

#### Advanced Features (Medium Priority)  
- [ ] Generate markdown report files per trial with proper formatting
- [ ] Create markdown formatter with tables, headers, and links
- [ ] Save generated reports to markdown files (e.g. `ossein_cage_report.md`)

#### Stretch Goals (Low Priority)
- [ ] Single report analysis mode - specify report ID to analyze specific log
- [ ] Parse individual ESO Logs reports directly from URLs  
- [ ] Validate ESO Logs report ID format and check if report exists

### Getting Involved

1. **Fork the repository**
2. **Set up your development environment** (see Setup section)
3. **Pick a TODO item** from the list above
4. **Write tests** following [TESTING.md](TESTING.md) guidelines
5. **Submit a pull request** with your changes

## License

MIT License - See LICENSE file for details
