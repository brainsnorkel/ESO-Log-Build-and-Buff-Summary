"""
Ability abbreviations module for ESO builds.

This module provides functionality to abbreviate ability names for more compact display in reports.
"""

import json
import logging
from typing import Dict, Optional
from pathlib import Path
from .config_manager import get_config_manager

logger = logging.getLogger(__name__)


class AbilityAbbreviations:
    """Handles ability name abbreviations for compact display in reports."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the ability abbreviations handler.
        
        Args:
            config_file: Path to the JSON configuration file containing ability abbreviations.
                        If None, uses the default from config manager.
        """
        if config_file:
            self.config_file = config_file
        else:
            config_manager = get_config_manager()
            self.config_file = str(config_manager.ability_abbreviations_file)
        
        self.abbreviations: Dict[str, str] = {}
        self._load_abbreviations()
    
    def _load_abbreviations(self):
        """Load ability abbreviations from the JSON configuration file."""
        try:
            config_path = Path(self.config_file)
            if not config_path.exists():
                logger.warning(f"Ability abbreviations config file not found: {self.config_file}")
                self.abbreviations = {}
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Load abbreviations from the config
            if 'abilities' in config:
                self.abbreviations = config['abilities']
                logger.info(f"Loaded {len(self.abbreviations)} ability abbreviations from {self.config_file}")
            else:
                logger.warning(f"No 'abilities' section found in {self.config_file}")
                self.abbreviations = {}
                
        except Exception as e:
            logger.error(f"Error loading ability abbreviations from {self.config_file}: {e}")
            self.abbreviations = {}
    
    def abbreviate_ability_name(self, ability_name: str) -> str:
        """
        Get the abbreviated version of an ability name.
        
        Args:
            ability_name: The full ability name to abbreviate.
            
        Returns:
            The abbreviated version if found, otherwise the original name.
        """
        if not ability_name:
            return ability_name
        
        # Try exact match first
        if ability_name in self.abbreviations:
            return self.abbreviations[ability_name]
        
        # Try case-insensitive match
        for full_name, abbreviation in self.abbreviations.items():
            if full_name.lower() == ability_name.lower():
                return abbreviation
        
        # Return original if no abbreviation found
        return ability_name
    
    def get_abbreviations(self) -> Dict[str, str]:
        """
        Get all ability abbreviations.
        
        Returns:
            Dictionary mapping full ability names to abbreviations.
        """
        return self.abbreviations.copy()
    
    def reload(self):
        """Reload abbreviations from the configuration file."""
        self._load_abbreviations()


# Global instance for easy access
_ability_abbreviations: Optional[AbilityAbbreviations] = None


def get_ability_abbreviations() -> AbilityAbbreviations:
    """
    Get the global ability abbreviations instance.
    
    Returns:
        The global AbilityAbbreviations instance.
    """
    global _ability_abbreviations
    if _ability_abbreviations is None:
        _ability_abbreviations = AbilityAbbreviations()
    return _ability_abbreviations


def abbreviate_ability_name(ability_name: str) -> str:
    """
    Abbreviate an ability name using the global abbreviations instance.
    
    Args:
        ability_name: The full ability name to abbreviate.
        
    Returns:
        The abbreviated version if found, otherwise the original name.
    """
    return get_ability_abbreviations().abbreviate_ability_name(ability_name)
