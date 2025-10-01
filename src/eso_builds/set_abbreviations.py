"""
Set name abbreviation utility.

This module handles mapping full set names to abbreviated versions
based on configuration from set_abbreviations.json.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SetAbbreviations:
    """Manages set name abbreviations."""

    def __init__(self, config_file: str = "set_abbreviations.json"):
        """Initialize with abbreviation mappings from config file."""
        self.config_file = Path(config_file)
        self.abbreviations: Dict[str, str] = {}
        self.unknown_sets: Dict[str, int] = {}  # Track unknown sets and their frequency
        self._load_abbreviations()
    
    def _load_abbreviations(self):
        """Load abbreviations from the configuration file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.abbreviations = json.load(f)
                logger.info(f"Loaded {len(self.abbreviations)} set abbreviations from {self.config_file}")
            else:
                logger.warning(f"Set abbreviations config file not found: {self.config_file}")
                self.abbreviations = {}
        except Exception as e:
            logger.error(f"Failed to load set abbreviations: {e}")
            self.abbreviations = {}
    
    def abbreviate_set_name(self, set_name: str) -> str:
        """
        Abbreviate a set name if an abbreviation is configured.

        Args:
            set_name: The full set name to abbreviate

        Returns:
            The abbreviated name if configured, otherwise the original name
        """
        # Clean the set name (remove "Perfected " prefix for lookup)
        clean_name = set_name.replace("Perfected ", "")

        # Try to find abbreviation
        abbreviated = self.abbreviations.get(clean_name, None)

        if abbreviated:
            return abbreviated
        else:
            # Track unknown sets
            if clean_name not in self.unknown_sets:
                logger.warning(f"⚠️  Unknown set (no abbreviation): '{clean_name}'")
                self.unknown_sets[clean_name] = 0
            self.unknown_sets[clean_name] += 1

            # Return original name if no abbreviation found
            return set_name
    
    def reload_abbreviations(self):
        """Reload abbreviations from the configuration file."""
        self._load_abbreviations()

    def get_unknown_sets_report(self) -> str:
        """
        Generate a report of unknown sets encountered during processing.

        Returns:
            A formatted string report of unknown sets and their frequencies
        """
        if not self.unknown_sets:
            return "✅ No unknown sets encountered"

        report_lines = [
            f"\n⚠️  Unknown Sets Report (Total: {len(self.unknown_sets)})",
            "=" * 60
        ]

        # Sort by frequency (most common first)
        sorted_sets = sorted(self.unknown_sets.items(), key=lambda x: x[1], reverse=True)

        for set_name, count in sorted_sets:
            report_lines.append(f"  • {set_name:40s} (seen {count} times)")

        report_lines.append("=" * 60)
        report_lines.append("\nSuggested abbreviations:")
        for set_name, _ in sorted_sets:
            suggested = self._suggest_abbreviation(set_name)
            report_lines.append(f'  "{set_name}": "{suggested}",')

        return "\n".join(report_lines)

    def _suggest_abbreviation(self, set_name: str) -> str:
        """
        Suggest an abbreviation for a set name based on common patterns.

        Args:
            set_name: The full set name

        Returns:
            A suggested abbreviation
        """
        # Remove common suffixes
        name = set_name.replace("'s Torment", "").replace("'s", "")

        # If short enough, use as-is
        if len(name) <= 8:
            return name.strip()

        words = name.split()

        # Single word: truncate or use full
        if len(words) == 1:
            return words[0][:8]

        # Two words: use first word if distinctive
        if len(words) == 2:
            return words[0]

        # Three+ words: create acronym
        acronym = "".join(w[0].upper() for w in words if w[0].isupper() or len(w) > 3)
        if len(acronym) >= 2:
            return acronym

        # Fallback: first word
        return words[0]

# Global instance for easy access
_set_abbreviations = None

def get_set_abbreviations() -> SetAbbreviations:
    """Get the global set abbreviations instance."""
    global _set_abbreviations
    if _set_abbreviations is None:
        _set_abbreviations = SetAbbreviations()
    return _set_abbreviations

def abbreviate_set_name(set_name: str) -> str:
    """
    Convenience function to abbreviate a set name.
    
    Args:
        set_name: The full set name to abbreviate
        
    Returns:
        The abbreviated name if configured, otherwise the original name
    """
    return get_set_abbreviations().abbreviate_set_name(set_name)
