"""
Skill line abbreviations module for ESO builds tool.

This module provides functionality to abbreviate skill line names for use in subclass displays.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional
from .config_manager import get_config_manager

logger = logging.getLogger(__name__)


class SkillLineAbbreviations:
    """Handles skill line abbreviations for subclass displays."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the skill line abbreviations.
        
        Args:
            config_file: Path to the skill line abbreviations JSON file. If None, uses default config.
        """
        if config_file is None:
            config_manager = get_config_manager()
            config_file = str(config_manager.get_config_path("skill_line_abbreviations.json"))
        
        self.config_file = Path(config_file)
        self.abbreviations: Dict[str, str] = {}
        self._load_abbreviations()
    
    def _load_abbreviations(self):
        """Load skill line abbreviations from the configuration file."""
        try:
            if not self.config_file.exists():
                logger.warning(f"Skill line abbreviations config file not found: {self.config_file}")
                logger.info("Using default skill line abbreviations")
                self._load_default_abbreviations()
                return
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.abbreviations = data.get('skill_lines', {})
            logger.info(f"Loaded {len(self.abbreviations)} skill line abbreviations from {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error loading skill line abbreviations from {self.config_file}: {e}")
            logger.info("Falling back to default skill line abbreviations")
            self._load_default_abbreviations()
    
    def _load_default_abbreviations(self):
        """Load default skill line abbreviations."""
        self.abbreviations = {
            "Ardent Flame": "Flame",
            "Earthen Heart": "Earthen",
            "Draconic Power": "Draconic",
            "Assassination": "Ass",
            "Shadow": "Shadow",
            "Siphoning": "Siphon",
            "Dawn's Wrath": "Dawn's",
            "Restoring Light": "Restoring",
            "Aedric Spear": "Aedric",
            "Storm Calling": "Storm",
            "Dark Magic": "Dark",
            "Destruction Staff": "Destruction",
            "Winter's Embrace": "Winter's",
            "Green Balance": "Green",
            "Animal Companions": "Animal",
            "Bone Tyrant": "Bone",
            "Grave Lord": "Grave",
            "Living Death": "Living",
            "Soul Magic": "Soul",
            "Spellcrafting": "Spellcraft",
            "Psijic Order": "Psijic",
            "Dual Wield": "Dual",
            "Two Handed": "2H",
            "One Hand and Shield": "S&B",
            "Bow": "Bow",
            "Destruction Staff": "Destro",
            "Restoration Staff": "Resto",
            "Heavy Armor": "Heavy",
            "Light Armor": "Light",
            "Medium Armor": "Medium",
            "Fighters Guild": "FG",
            "Mages Guild": "MG",
            "Undaunted": "Und",
            "Thieves Guild": "TG",
            "Dark Brotherhood": "DB",
            "Legerdemain": "Leger",
            "Vampire": "Vamp",
            "Werewolf": "Were"
        }
        logger.info(f"Loaded {len(self.abbreviations)} default skill line abbreviations")
    
    def abbreviate_skill_line(self, skill_line: str) -> str:
        """
        Get the abbreviation for a skill line name.
        
        Args:
            skill_line: The full skill line name
            
        Returns:
            The abbreviated skill line name, or the original if no abbreviation exists
        """
        if not skill_line:
            return skill_line
        
        # Try exact match first
        if skill_line in self.abbreviations:
            return self.abbreviations[skill_line]
        
        # Try case-insensitive match
        for full_name, abbreviation in self.abbreviations.items():
            if full_name.lower() == skill_line.lower():
                return abbreviation
        
        # No abbreviation found, return original
        return skill_line
    
    def get_abbreviation(self, skill_line: str) -> str:
        """Alias for abbreviate_skill_line for consistency with other abbreviation modules."""
        return self.abbreviate_skill_line(skill_line)


# Global instance for easy access
_skill_line_abbreviations_instance: Optional[SkillLineAbbreviations] = None


def get_skill_line_abbreviations() -> SkillLineAbbreviations:
    """Get the global skill line abbreviations instance."""
    global _skill_line_abbreviations_instance
    if _skill_line_abbreviations_instance is None:
        _skill_line_abbreviations_instance = SkillLineAbbreviations()
    return _skill_line_abbreviations_instance


def abbreviate_skill_line(skill_line: str) -> str:
    """
    Abbreviate a skill line name using the global abbreviations.
    
    Args:
        skill_line: The full skill line name
        
    Returns:
        The abbreviated skill line name
    """
    return get_skill_line_abbreviations().abbreviate_skill_line(skill_line)


