"""
Data models for ESO Top Builds analysis.

This module defines the core data structures for representing trials, encounters,
players, and their gear builds.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import datetime


class Role(Enum):
    """Player roles in ESO."""
    TANK = "Tank"
    HEALER = "Healer"
    DPS = "DPS"


class Difficulty(Enum):
    """Encounter difficulty levels."""
    NORMAL = "Normal"
    VETERAN = "Veteran"
    VETERAN_HARD_MODE = "Veteran Hard Mode"


@dataclass
class GearSet:
    """Represents a gear set (like 5pc Perfected Pearlescent Ward)."""
    name: str
    piece_count: int
    is_perfected: bool = False
    
    def __str__(self) -> str:
        prefix = "Perfected " if self.is_perfected else ""
        return f"{self.piece_count}pc {prefix}{self.name}"


@dataclass
class PlayerBuild:
    """Represents a player's complete build for an encounter."""
    name: str
    character_class: str
    role: Role
    gear_sets: List[GearSet] = field(default_factory=list)
    
    def __str__(self) -> str:
        gear_str = ", ".join(str(gear) for gear in self.gear_sets)
        return f"{self.character_class}, {gear_str}"


@dataclass
class EncounterResult:
    """Represents the results of a single boss encounter."""
    encounter_name: str
    difficulty: Difficulty
    players: List[PlayerBuild] = field(default_factory=list)
    kill: bool = False
    boss_percentage: float = 0.0
    buff_uptimes: Dict[str, float] = field(default_factory=dict)
    
    @property
    def tanks(self) -> List[PlayerBuild]:
        """Get all tank players."""
        return [p for p in self.players if p.role == Role.TANK]
    
    @property
    def healers(self) -> List[PlayerBuild]:
        """Get all healer players."""
        return [p for p in self.players if p.role == Role.HEALER]
    
    @property
    def dps(self) -> List[PlayerBuild]:
        """Get all DPS players."""
        return [p for p in self.players if p.role == Role.DPS]


@dataclass
class LogRanking:
    """Represents a single ranked log with all its encounters."""
    rank: int
    log_url: str
    log_code: str
    score: float
    encounters: List[EncounterResult] = field(default_factory=list)
    date: Optional[datetime.datetime] = None
    guild_name: Optional[str] = None


@dataclass
class TrialReport:
    """Complete report for a trial showing top 5 rankings."""
    trial_name: str
    zone_id: int
    rankings: List[LogRanking] = field(default_factory=list)
    generated_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    
    def add_ranking(self, ranking: LogRanking) -> None:
        """Add a ranking to this trial report."""
        self.rankings.append(ranking)
        # Keep rankings sorted by rank
        self.rankings.sort(key=lambda x: x.rank)


@dataclass
class BuildsReport:
    """Complete builds report containing multiple trials."""
    trials: List[TrialReport] = field(default_factory=list)
    generated_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    
    def add_trial(self, trial: TrialReport) -> None:
        """Add a trial report to this builds report."""
        self.trials.append(trial)
