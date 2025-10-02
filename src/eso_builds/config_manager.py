"""
Configuration Manager for ESO Builds Tool.

This module provides centralized configuration management for the ESO builds tool,
handling paths, settings, and configuration file locations.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Centralized configuration manager for the ESO builds tool."""
    
    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            project_root: Root directory of the project. If None, auto-detects.
        """
        if project_root:
            self.project_root = Path(project_root)
        else:
            # Auto-detect project root by looking for src/ directory
            current = Path(__file__).parent
            while current.parent != current:
                if (current / "src").exists() and (current / "src" / "eso_builds").exists():
                    break
                current = current.parent
            self.project_root = current
        
        # Define directory structure
        self.config_dir = self.project_root / "config"
        self.data_dir = self.project_root / "data"
        self.reports_dir = self.project_root / "reports"
        self.tests_dir = self.project_root / "tests"
        self.scripts_dir = self.project_root / "scripts"
        self.docs_dir = self.project_root / "docs"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Configuration file paths
        self.ability_abbreviations_file = self.config_dir / "ability_abbreviations.json"
        self.build_name_mappings_file = self.config_dir / "build_name_mappings.json"
        self.set_abbreviations_file = self.config_dir / "set_abbreviations.json"
        self.libsets_excel_file = self.config_dir / "LibSets_SetData.xlsm"
        
        logger.info(f"ConfigManager initialized with project root: {self.project_root}")
        logger.info(f"Config directory: {self.config_dir}")
        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"Reports directory: {self.reports_dir}")
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.config_dir,
            self.data_dir,
            self.reports_dir,
            self.tests_dir,
            self.scripts_dir,
            self.docs_dir
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    def get_config_path(self, filename: str) -> Path:
        """
        Get the full path to a configuration file.
        
        Args:
            filename: Name of the configuration file
            
        Returns:
            Full path to the configuration file
        """
        return self.config_dir / filename
    
    def get_data_path(self, filename: str) -> Path:
        """
        Get the full path to a data file.
        
        Args:
            filename: Name of the data file
            
        Returns:
            Full path to the data file
        """
        return self.data_dir / filename
    
    def get_reports_path(self, filename: str) -> Path:
        """
        Get the full path to a reports file.
        
        Args:
            filename: Name of the reports file
            
        Returns:
            Full path to the reports file
        """
        return self.reports_dir / filename
    
    def get_tests_path(self, filename: str) -> Path:
        """
        Get the full path to a test file.
        
        Args:
            filename: Name of the test file
            
        Returns:
            Full path to the test file
        """
        return self.tests_dir / filename
    
    def get_scripts_path(self, filename: str) -> Path:
        """
        Get the full path to a script file.
        
        Args:
            filename: Name of the script file
            
        Returns:
            Full path to the script file
        """
        return self.scripts_dir / filename
    
    def get_docs_path(self, filename: str) -> Path:
        """
        Get the full path to a documentation file.
        
        Args:
            filename: Name of the documentation file
            
        Returns:
            Full path to the documentation file
        """
        return self.docs_dir / filename
    
    def list_config_files(self) -> Dict[str, Path]:
        """
        List all configuration files and their paths.
        
        Returns:
            Dictionary mapping configuration names to their paths
        """
        return {
            "ability_abbreviations": self.ability_abbreviations_file,
            "build_name_mappings": self.build_name_mappings_file,
            "set_abbreviations": self.set_abbreviations_file,
            "libsets_excel": self.libsets_excel_file
        }
    
    def validate_config_files(self) -> Dict[str, bool]:
        """
        Validate that all required configuration files exist.
        
        Returns:
            Dictionary mapping config file names to their existence status
        """
        config_files = self.list_config_files()
        validation_results = {}
        
        for name, path in config_files.items():
            exists = path.exists()
            validation_results[name] = exists
            if not exists:
                logger.warning(f"Configuration file not found: {path}")
            else:
                logger.debug(f"Configuration file found: {path}")
        
        return validation_results


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """
    Get the global configuration manager instance.
    
    Returns:
        The global ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def initialize_config(project_root: Optional[str] = None) -> ConfigManager:
    """
    Initialize the global configuration manager.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        The initialized ConfigManager instance
    """
    global _config_manager
    _config_manager = ConfigManager(project_root)
    return _config_manager
