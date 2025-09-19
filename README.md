# ESO Top Builds

A Python project that analyzes Elder Scrolls Online logs using the esologs.com API to generate reports of top builds for different boss encounters.

## Overview

This project uses the [esologs-python](https://github.com/knowlen/esologs-python) library to access the esologs.com API. For each trial, it takes the five top scoring logged encounters for the current update and builds a report for each boss encounter showing the class and gear of DPS, tanks, and healers.

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

You'll need to obtain API credentials from esologs.com and configure them for the project.

## Usage

(Usage instructions will be added as the project develops)

## Development

This project is actively under development. See the changelog for recent updates.

## License

(License to be determined)
