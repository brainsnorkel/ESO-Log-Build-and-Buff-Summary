#!/usr/bin/env python3
"""
Build Name Mapping System

This module provides functionality to map common two-set combinations to shorter build names.
For example: "5xDeadly Strike, 5xNull Arca" -> "Deadly/Null Arca"
"""

import logging
import json
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BuildMapping:
    """Represents a build name mapping."""
    set1: str
    set2: str
    combined_name: str
    
    def __post_init__(self):
        # Normalize set names for matching
        self.set1_normalized = self._normalize_set_name(self.set1)
        self.set2_normalized = self._normalize_set_name(self.set2)
        # Create a frozenset for order-independent matching
        self.set_pair = frozenset([self.set1_normalized, self.set2_normalized])
    
    def _normalize_set_name(self, set_name: str) -> str:
        """Normalize set name for matching (remove 'Perfected'/'Perfect' prefixes, case insensitive)."""
        # Remove 'Perfected' or 'Perfect' prefix and make lowercase
        normalized = set_name.lower().strip()
        if normalized.startswith('perfected '):
            normalized = normalized[10:]  # Remove 'perfected '
        elif normalized.startswith('perfect '):
            normalized = normalized[8:]   # Remove 'perfect '
        return normalized.strip()
    
    def matches_sets(self, set1: str, set2: str) -> bool:
        """Check if this mapping matches the given two sets (order independent)."""
        norm1 = self._normalize_set_name(set1)
        norm2 = self._normalize_set_name(set2)
        
        # Create a frozenset for the input sets and compare
        input_set_pair = frozenset([norm1, norm2])
        return input_set_pair == self.set_pair


class BuildNameMapper:
    """Maps common two-set combinations to shorter build names."""
    
    def __init__(self, config_file: str = "config/build_name_mappings.json", mappings: Optional[List[BuildMapping]] = None):
        """
        Initialize the build name mapper.
        
        Args:
            config_file: Path to JSON configuration file. If None, uses default mappings.
            mappings: List of build mappings. If provided, overrides config file.
        """
        if mappings is not None:
            self.mappings = mappings
        else:
            self.mappings = self._load_mappings_from_config(config_file)
        logger.info(f"Initialized BuildNameMapper with {len(self.mappings)} mappings")
    
    def _load_mappings_from_config(self, config_file: str) -> List[BuildMapping]:
        """Load build name mappings from JSON configuration file."""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                logger.warning(f"Build name mapping config file not found: {config_file}, using default mappings")
                return self._get_default_mappings()
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            mappings = []
            
            # Load mappings from the simplified structure
            if 'mappings' in config:
                # New simplified format
                for mapping_data in config['mappings']:
                    mapping = BuildMapping(
                        set1=mapping_data['set1'],
                        set2=mapping_data['set2'],
                        combined_name=mapping_data['combined_name']
                    )
                    mappings.append(mapping)
            else:
                # Legacy categorized format (for backward compatibility)
                for category_name, category_mappings in config.items():
                    if category_name.startswith('_'):
                        continue  # Skip comment fields
                    logger.debug(f"Loading {len(category_mappings)} mappings from category: {category_name}")
                    for mapping_data in category_mappings:
                        mapping = BuildMapping(
                            set1=mapping_data['set1'],
                            set2=mapping_data['set2'],
                            combined_name=mapping_data['combined_name']
                        )
                        mappings.append(mapping)
            
            logger.info(f"Loaded {len(mappings)} build name mappings from {config_file}")
            return mappings
            
        except Exception as e:
            logger.error(f"Error loading build name mappings from {config_file}: {e}")
            logger.warning("Falling back to default mappings")
            return self._get_default_mappings()
    
    def _get_default_mappings(self) -> List[BuildMapping]:
        """Get the default build name mappings."""
        return [
            # Healer builds
            BuildMapping("Roaring Opportunist", "Jorvuld's Guidance", "ROJO"),
            BuildMapping("Pearlescent Ward", "Lucent Echoes", "PW/LE"),
            BuildMapping("Spell Power Cure", "Pillager's Profit", "SPC/Pillager"),
            
            # DPS builds
            BuildMapping("Deadly Strike", "Slivers of the Null Arca", "Deadly/Null Arca"),
            BuildMapping("Ansuul's Torment", "Tide-Born Wildstalker", "Ansuul/Tide-Born"),
            BuildMapping("Ansuul's Torment", "Deadly Strike", "Ansuul/Deadly"),
            BuildMapping("Tide-Born Wildstalker", "Sul-Xan's Torment", "SulXan/Tide-Born"),
            BuildMapping("Highland Sentinel", "Slivers of the Null Arca", "Highland/Null Arca"),
            BuildMapping("Corpseburster", "Azureblight Reaper", "Corpse/Azureblight"),
            BuildMapping("Corpseburster", "Slivers of the Null Arca", "Corpse/Null Arca"),
            BuildMapping("Azureblight Reaper", "Slivers of the Null Arca", "Azureblight/Null Arca"),
            
            # Tank builds
            BuildMapping("Powerful Assault", "Lucent Echoes", "PA/LE"),
            BuildMapping("Pearlescent Ward", "Turning Tide", "PW/TT"),
            
            # Hybrid builds
            BuildMapping("Ansuul's Torment", "Slivers of the Null Arca", "Ansuul/Null Arca"),
            BuildMapping("Deadly Strike", "Tide-Born Wildstalker", "Deadly/Tide-Born"),
            BuildMapping("Highland Sentinel", "Deadly Strike", "Highland/Deadly"),
            BuildMapping("Corpseburster", "Deadly Strike", "Corpse/Deadly"),
        ]
    
    def find_build_mapping(self, gear_sets: List[str]) -> Optional[Tuple[str, Set[str]]]:
        """
        Find a build mapping for the given gear sets.
        
        Args:
            gear_sets: List of gear set names with piece counts (e.g., ["5xDeadly Strike", "5xNull Arca", "2xSlimecraw"])
            
        Returns:
            Tuple of (combined_name, remaining_sets) if a mapping is found, None otherwise.
            remaining_sets contains the sets that weren't part of the mapping.
        """
        if len(gear_sets) < 2:
            return None
        
        # Extract set names and piece counts
        set_info = []
        for gear_set in gear_sets:
            set_name, piece_count = self._parse_gear_set(gear_set)
            if set_name and piece_count >= 5:  # Only consider sets with 5+ pieces
                set_info.append((set_name, piece_count, gear_set))
        
        if len(set_info) < 2:
            return None
        
        # Try to find a mapping for any two sets with 5+ pieces
        for i in range(len(set_info)):
            for j in range(i + 1, len(set_info)):
                set1_name, set1_count, set1_original = set_info[i]
                set2_name, set2_count, set2_original = set_info[j]
                
                # Find matching mapping
                for mapping in self.mappings:
                    if mapping.matches_sets(set1_name, set2_name):
                        # Found a match! Create the combined name and remaining sets
                        combined_name = mapping.combined_name
                        remaining_sets = set(gear_sets) - {set1_original, set2_original}
                        
                        logger.debug(f"Found build mapping: {set1_name} + {set2_name} -> {combined_name}")
                        return combined_name, remaining_sets
        
        return None
    
    def _parse_gear_set(self, gear_set: str) -> Tuple[Optional[str], int]:
        """
        Parse a gear set string to extract set name and piece count.
        
        Args:
            gear_set: String like "5xDeadly Strike", "7xPA", "2xSlimecraw"
            
        Returns:
            Tuple of (set_name, piece_count) or (None, 0) if parsing fails
        """
        try:
            # Handle formats like "5xDeadly Strike", "7xPA", "2xSlimecraw"
            if 'x' in gear_set:
                parts = gear_set.split('x', 1)
                if len(parts) == 2:
                    piece_count = int(parts[0])
                    set_name = parts[1].strip()
                    return set_name, piece_count
            
            # Handle formats like "5pc Deadly Strike"
            if gear_set.startswith(('5pc ', '6pc ', '7pc ')):
                piece_count = int(gear_set[:1])
                set_name = gear_set[4:].strip()
                return set_name, piece_count
            
            # If no piece count found, assume it's just a set name
            return gear_set.strip(), 0
            
        except (ValueError, IndexError):
            logger.debug(f"Failed to parse gear set: {gear_set}")
            return None, 0
    
    def apply_build_mapping(self, gear_text: str) -> str:
        """
        Apply build name mapping to a gear text string.
        
        Args:
            gear_text: Original gear text (e.g., "7xRO, 5xJO, 2xOzezan")
            
        Returns:
            Modified gear text with build names applied
        """
        if not gear_text or not gear_text.strip():
            return gear_text
        
        # Split gear sets by comma
        gear_sets = [gs.strip() for gs in gear_text.split(',') if gs.strip()]
        
        # Try to find a build mapping
        mapping_result = self.find_build_mapping(gear_sets)
        if mapping_result:
            combined_name, remaining_sets = mapping_result
            
            # Reconstruct the gear text with the combined name
            result_parts = [combined_name]
            result_parts.extend(sorted(remaining_sets))
            
            result = ', '.join(result_parts)
            logger.debug(f"Applied build mapping: '{gear_text}' -> '{result}'")
            return result
        
        return gear_text
    
    def add_mapping(self, set1: str, set2: str, combined_name: str):
        """Add a new build mapping."""
        mapping = BuildMapping(set1, set2, combined_name)
        self.mappings.append(mapping)
        logger.info(f"Added build mapping: {set1} + {set2} -> {combined_name}")
    
    def get_mappings(self) -> List[BuildMapping]:
        """Get all current mappings."""
        return self.mappings.copy()
