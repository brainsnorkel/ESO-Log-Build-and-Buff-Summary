#!/usr/bin/env python3
"""
Test script for configuration manager functionality.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from eso_builds.config_manager import ConfigManager, get_config_manager

def test_config_manager():
    """Test the configuration manager functionality."""
    print("🧪 Testing Configuration Manager")
    print("=" * 40)
    
    # Test initialization
    config = ConfigManager()
    print(f"✅ Project root: {config.project_root}")
    print(f"✅ Config directory: {config.config_dir}")
    print(f"✅ Data directory: {config.data_dir}")
    print(f"✅ Reports directory: {config.reports_dir}")
    
    # Test directory creation
    print(f"✅ Config directory exists: {config.config_dir.exists()}")
    print(f"✅ Data directory exists: {config.data_dir.exists()}")
    print(f"✅ Reports directory exists: {config.reports_dir.exists()}")
    
    # Test path resolution
    config_file = config.get_config_path("test_config.json")
    data_file = config.get_data_path("test_data.json")
    reports_file = config.get_reports_path("test_report.md")
    
    print(f"✅ Config file path: {config_file}")
    print(f"✅ Data file path: {data_file}")
    print(f"✅ Reports file path: {reports_file}")
    
    # Test configuration file listing
    config_files = config.list_config_files()
    print(f"✅ Configuration files: {list(config_files.keys())}")
    
    # Test validation
    validation = config.validate_config_files()
    print(f"✅ Config file validation:")
    for name, exists in validation.items():
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"  {status} {name}")
    
    # Test global instance
    global_config = get_config_manager()
    print(f"✅ Global config manager works: {global_config.project_root == config.project_root}")
    
    return True

if __name__ == "__main__":
    success = test_config_manager()
    if success:
        print("\n🎉 Configuration manager test completed!")
        sys.exit(0)
    else:
        print("\n❌ Configuration manager test failed!")
        sys.exit(1)
