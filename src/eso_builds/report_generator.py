"""
Complete report generation for ESO Logs Build and Buff Summary.

This module orchestrates the entire report generation process from
API data retrieval to formatted output.
"""

import logging
import asyncio
from typing import List, Optional
from datetime import datetime

from .models import TrialReport, LogRanking, EncounterResult, PlayerBuild, Role, Difficulty, GearSet
from .api_client import ESOLogsClient
from .gear_parser import GearParser
from .report_formatter import ReportFormatter
from .markdown_formatter import MarkdownFormatter

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Main class for generating ESO top builds reports."""
    
    def __init__(self):
        """Initialize the report generator."""
        self.gear_parser = GearParser()
        self.console_formatter = ReportFormatter()
        self.markdown_formatter = MarkdownFormatter()
    
    async def generate_trial_report(self, trial_name: str, zone_id: int, 
                                   use_real_api: bool = True) -> TrialReport:
        """Generate a complete trial report."""
        logger.info(f"Generating report for {trial_name} (zone {zone_id})")
        
        if use_real_api:
            # Use real API calls
            try:
                async with ESOLogsClient() as client:
                    return await client.build_trial_report(trial_name, zone_id)
            except Exception as e:
                logger.error(f"Real API failed, falling back to sample data: {e}")
                return self._generate_sample_trial_report(trial_name, zone_id)
        else:
            # Generate sample report for demonstration
            return self._generate_sample_trial_report(trial_name, zone_id)
    
    def _generate_sample_trial_report(self, trial_name: str, zone_id: int) -> TrialReport:
        """Generate a realistic sample trial report for demonstration."""
        logger.info(f"Generating sample report for {trial_name}")
        
        trial_report = TrialReport(trial_name=trial_name, zone_id=zone_id)
        
        # Generate 5 sample rankings
        for rank in range(1, 6):
            ranking = self._create_sample_ranking(rank, trial_name)
            trial_report.add_ranking(ranking)
        
        return trial_report
    
    def _create_sample_ranking(self, rank: int, trial_name: str) -> LogRanking:
        """Create a sample ranking with realistic data."""
        # Sample log codes
        sample_codes = [
            "3gjVGWB2dxCL8XAw",
            "7mKpR9Ns4YtH2vBc", 
            "1xZqE8Jf6WuL3nMo",
            "5dTgY2Vk9PsI7rAe",
            "9wXcF4Bh8QzN6kUj"
        ]
        
        code = sample_codes[rank - 1]
        score = 100.0 - (rank - 1) * 2.5  # Decreasing scores
        
        ranking = LogRanking(
            rank=rank,
            log_url=f"https://www.esologs.com/reports/{code}",
            log_code=code,
            score=score,
            guild_name=f"Sample Guild {rank}",
            date=datetime.now()
        )
        
        # Add encounters based on trial
        if "Ossein Cage" in trial_name:
            encounters = [
                ("Hall of Fleshcraft", Difficulty.VETERAN_HARD_MODE),
                ("Jynorah and Skorkhif", Difficulty.VETERAN_HARD_MODE),
                ("Overfiend Kazpian", Difficulty.VETERAN_HARD_MODE)
            ]
        elif "Lucent Citadel" in trial_name:
            encounters = [
                ("Count Ryelaz and Zilyesset", Difficulty.VETERAN_HARD_MODE),
                ("Orphic Shattered Shard", Difficulty.VETERAN_HARD_MODE),
                ("Xoryn", Difficulty.VETERAN_HARD_MODE)
            ]
        else:
            # Generic encounters
            encounters = [
                ("First Boss", Difficulty.VETERAN_HARD_MODE),
                ("Second Boss", Difficulty.VETERAN_HARD_MODE),
                ("Final Boss", Difficulty.VETERAN_HARD_MODE)
            ]
        
        for encounter_name, difficulty in encounters:
            encounter = self._create_sample_encounter(encounter_name, difficulty, rank)
            ranking.encounters.append(encounter)
        
        return ranking
    
    def _create_sample_encounter(self, encounter_name: str, difficulty: Difficulty, rank: int) -> EncounterResult:
        """Create a sample encounter with realistic player builds."""
        encounter = EncounterResult(encounter_name=encounter_name, difficulty=difficulty)
        
        # Create sample players with realistic builds
        players = []
        
        # Tanks (2)
        tank_builds = [
            ("Tank1", "Dragonknight", [
                GearSet("Pearlescent Ward", 5, True),
                GearSet("Lucent Echoes", 5, False),
                GearSet("Nazaray", 2, False)
            ]),
            ("Tank2", "Templar", [
                GearSet("Saxhleel Champion", 5, False),
                GearSet("Powerful Assault", 5, False),
                GearSet("Lord Warden", 2, False)
            ])
        ]
        
        for name, class_name, gear_sets in tank_builds:
            player = PlayerBuild(name=name, character_class=class_name, role=Role.TANK, gear_sets=gear_sets)
            players.append(player)
        
        # Healers (2)
        healer_builds = [
            ("Healer1", "Arcanist", [
                GearSet("Spell Power Cure", 5, True),
                GearSet("Jorvuld's Guidance", 5, False),
                GearSet("Symphony of Blades", 2, False)
            ]),
            ("Healer2", "Warden", [
                GearSet("Hollowfang Thirst", 5, False),
                GearSet("Worm's Raiment", 5, False),
                GearSet("Sentinel of Rkugamz", 2, False)
            ])
        ]
        
        for name, class_name, gear_sets in healer_builds:
            player = PlayerBuild(name=name, character_class=class_name, role=Role.HEALER, gear_sets=gear_sets)
            players.append(player)
        
        # DPS (8) - Vary builds based on rank for realism
        dps_builds = [
            ("DPS1", "Necromancer", [
                GearSet("Relequen", 5, True),
                GearSet("Kinras's Wrath", 5, False),
                GearSet("Slimecraw", 2, False)
            ]),
            ("DPS2", "Dragonknight", [
                GearSet("Bahsei's Mania", 5, True),
                GearSet("Coral Riptide", 5, False),
                GearSet("Kjalnar's Nightmare", 2, False)
            ]),
            ("DPS3", "Sorcerer", [
                GearSet("Ansuul's Torment", 5, True),
                GearSet("Sul-Xan's Torment", 5, False),
                GearSet("Grundwulf", 2, False)
            ]),
            ("DPS4", "Nightblade", [
                GearSet("Pillar of Nirn", 5, False),
                GearSet("Relequen", 5, True),
                GearSet("Selene", 2, False)
            ]),
            ("DPS5", "Templar", [
                GearSet("Deadly Strike", 5, False),
                GearSet("Kinras's Wrath", 5, False),
                GearSet("Kra'gh", 2, False)
            ]),
            ("DPS6", "Arcanist", [
                GearSet("Coral Riptide", 5, True),
                GearSet("Pillar of Nirn", 5, False),
                GearSet("Slimecraw", 2, False)
            ]),
            ("DPS7", "Warden", [
                GearSet("Relequen", 5, True),
                GearSet("Tzogvin's Warband", 5, False),
                GearSet("Velidreth", 2, False)
            ]),
            ("DPS8", "Necromancer", [
                GearSet("Bahsei's Mania", 5, True),
                GearSet("Ansuul's Torment", 5, False),
                GearSet("Zaan", 2, False)
            ])
        ]
        
        for name, class_name, gear_sets in dps_builds:
            player = PlayerBuild(name=name, character_class=class_name, role=Role.DPS, gear_sets=gear_sets)
            players.append(player)
        
        encounter.players = players
        return encounter
    
    def format_console_report(self, trial_report: TrialReport) -> str:
        """Format trial report for console output."""
        return self.console_formatter.format_trial_report(trial_report)
    
    def format_markdown_report(self, trial_report: TrialReport) -> str:
        """Format trial report for markdown output."""
        return self.markdown_formatter.format_trial_report(trial_report)
    
    def save_markdown_report(self, trial_report: TrialReport, output_dir: str = ".") -> str:
        """Save markdown report to file and return filename."""
        import os
        
        filename = self.markdown_formatter.get_filename(trial_report.trial_name)
        filepath = os.path.join(output_dir, filename)
        
        markdown_content = self.format_markdown_report(trial_report)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Markdown report saved to: {filepath}")
        return filepath
