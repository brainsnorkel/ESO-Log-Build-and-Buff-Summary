"""
Excel-based LibSets parser to extract ESO gear set information from the official LibSets Excel file.

This module downloads and parses the LibSets_SetData.xlsm file from GitHub to extract
set piece requirements and other set information for dynamic gear set analysis.
"""

import logging
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests
import os
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ExcelSetInfo:
    """Information about a gear set from LibSets Excel data."""
    name: str
    set_id: int
    set_type: str
    is_perfected: bool
    perfected_set_id: Optional[int] = None
    
    @property
    def max_pieces(self) -> int:
        """Determine max pieces based on set type."""
        if self.set_type in ['LIBSETS_SETTYPE_MONSTER', 'LIBSETS_SETTYPE_IMPERIALCITY_MONSTER']:
            return 2
        elif self.set_type == 'LIBSETS_SETTYPE_MYTHIC':
            return 1
        elif self.set_type == 'LIBSETS_SETTYPE_ARENA':
            return 2  # Arena weapons are typically 2-piece
        else:
            return 5  # Regular sets (dungeon, trial, overland, crafted, etc.)
    
    @property
    def set_type_category(self) -> str:
        """Get a simplified set type category."""
        if self.set_type in ['LIBSETS_SETTYPE_MONSTER', 'LIBSETS_SETTYPE_IMPERIALCITY_MONSTER']:
            return 'monster'
        elif self.set_type == 'LIBSETS_SETTYPE_MYTHIC':
            return 'mythic'
        elif self.set_type == 'LIBSETS_SETTYPE_ARENA':
            return 'arena'
        else:
            return 'regular'


class ExcelLibSetsParser:
    """Parser for LibSets Excel data."""
    
    def __init__(self):
        """Initialize the Excel LibSets parser."""
        self.sets_data: Dict[str, ExcelSetInfo] = {}
        self.set_id_data: Dict[int, ExcelSetInfo] = {}
        self.libsets_excel_url = "https://raw.githubusercontent.com/Baertram/LibSets/LibSets-reworked/LibSets/Data/LibSets_SetData.xlsm"
        self.local_excel_path = Path("config/LibSets_SetData.xlsm")
        self.initialized = False
    
    async def initialize_from_excel(self) -> bool:
        """
        Initialize the parser by downloading and loading the Excel data.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Download the Excel file if it doesn't exist or is outdated
            await self._download_excel_file()
            
            # Load and parse the Excel data
            success = await self._load_excel_data()
            
            if success:
                self.initialized = True
                logger.info(f"Excel LibSets parser initialized successfully with {len(self.sets_data)} sets")
            
            return success
            
        except Exception as e:
            logger.error(f"Error initializing Excel LibSets parser: {e}")
            return False
    
    async def _download_excel_file(self) -> None:
        """Download the Excel file if needed."""
        try:
            if not self.local_excel_path.exists():
                logger.info("Downloading LibSets Excel file...")
                response = requests.get(self.libsets_excel_url, timeout=30)
                response.raise_for_status()
                
                with open(self.local_excel_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded LibSets Excel file: {self.local_excel_path}")
            else:
                logger.info(f"Using existing LibSets Excel file: {self.local_excel_path}")
                
        except Exception as e:
            logger.error(f"Error downloading Excel file: {e}")
            raise
    
    async def _load_excel_data(self) -> bool:
        """
        Load and parse the Excel data.
        
        Returns:
            True if data was loaded successfully, False otherwise
        """
        try:
            logger.info("Loading LibSets data from Excel file...")
            
            # Read the Excel file
            df = pd.read_excel(self.local_excel_path, sheet_name='Sets data', header=1)
            logger.info(f"Loaded Excel data with {len(df)} rows")
            
            # Parse each row
            parsed_count = 0
            for _, row in df.iterrows():
                try:
                    set_info = self._parse_excel_row(row)
                    if set_info:
                        # Store by name (case-insensitive)
                        self.sets_data[set_info.name.lower()] = set_info
                        # Store by set ID
                        self.set_id_data[set_info.set_id] = set_info
                        parsed_count += 1
                        
                except Exception as e:
                    logger.warning(f"Error parsing Excel row {row.get('ESO ingame setId', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {parsed_count} sets from Excel data")
            return parsed_count > 0
            
        except Exception as e:
            logger.error(f"Error loading Excel data: {e}")
            return False
    
    def _parse_excel_row(self, row: pd.Series) -> Optional[ExcelSetInfo]:
        """
        Parse a single Excel row into a SetInfo object.
        
        Args:
            row: Pandas Series representing one row of the Excel data
            
        Returns:
            ExcelSetInfo object if parsing was successful, None otherwise
        """
        try:
            # Extract basic information
            set_id = row.get('ESO ingame setId')
            name_en = row.get('Name EN')
            set_type = row.get('Set Type')
            perfected_info = row.get('IsPerfectedSet=X, or PerfectedSetId=<setId>')
            
            # Skip rows without essential data
            if pd.isna(set_id) or pd.isna(name_en) or pd.isna(set_type):
                return None
            
            # Convert to appropriate types
            set_id = int(set_id)
            name_en = str(name_en).strip()
            # Normalize quotes in set names for consistent lookup
            name_en = name_en.replace('\\\'', '\'')
            set_type = str(set_type).strip()
            
            # Determine if it's a perfected set
            is_perfected = False
            perfected_set_id = None
            
            if pd.notna(perfected_info):
                perfected_str = str(perfected_info).strip()
                if perfected_str == 'X':
                    is_perfected = True
                elif perfected_str.isdigit():
                    perfected_set_id = int(perfected_str)
                    is_perfected = True
            
            return ExcelSetInfo(
                name=name_en,
                set_id=set_id,
                set_type=set_type,
                is_perfected=is_perfected,
                perfected_set_id=perfected_set_id
            )
            
        except Exception as e:
            logger.warning(f"Error parsing Excel row: {e}")
            return None
    
    def get_set_info(self, set_name: str) -> Optional[ExcelSetInfo]:
        """
        Get set information by name.
        
        Args:
            set_name: The name of the set to look up
            
        Returns:
            ExcelSetInfo if found, None otherwise
        """
        if not self.initialized:
            logger.warning("Excel LibSets parser not initialized")
            return None
        
        # Try exact match first (case-insensitive)
        set_name_lower = set_name.lower()
        if set_name_lower in self.sets_data:
            return self.sets_data[set_name_lower]
        
        # Try fuzzy matching for common variations
        for key, set_info in self.sets_data.items():
            if self._is_fuzzy_match(set_name_lower, key):
                return set_info
        
        return None
    
    def get_set_info_by_id(self, set_id: int) -> Optional[ExcelSetInfo]:
        """
        Get set information by set ID.
        
        Args:
            set_id: The ESO set ID to look up
            
        Returns:
            ExcelSetInfo if found, None otherwise
        """
        if not self.initialized:
            logger.warning("Excel LibSets parser not initialized")
            return None
        
        return self.set_id_data.get(set_id)
    
    def get_max_pieces(self, set_name: str) -> int:
        """
        Get the maximum number of pieces for a set.
        
        Args:
            set_name: The name of the set
            
        Returns:
            The maximum number of pieces (default: 5)
        """
        set_info = self.get_set_info(set_name)
        if set_info:
            return set_info.max_pieces
        
        # Fallback to default
        return 5
    
    def is_valid_piece_count(self, set_name: str, piece_count: int) -> bool:
        """
        Check if a piece count is valid for a set.
        
        Args:
            set_name: The name of the set
            piece_count: The number of pieces
            
        Returns:
            True if the piece count is valid, False otherwise
        """
        max_pieces = self.get_max_pieces(set_name)
        return 0 <= piece_count <= max_pieces
    
    def get_all_sets(self) -> List[ExcelSetInfo]:
        """
        Get all parsed sets.
        
        Returns:
            List of all ExcelSetInfo objects
        """
        return list(self.sets_data.values())
    
    def get_sets_by_type(self, set_type: str) -> List[ExcelSetInfo]:
        """
        Get all sets of a specific type.
        
        Args:
            set_type: The set type to filter by
            
        Returns:
            List of ExcelSetInfo objects matching the type
        """
        return [set_info for set_info in self.sets_data.values() 
                if set_info.set_type == set_type]
    
    def _is_fuzzy_match(self, query: str, db_key: str) -> bool:
        """
        Check if a query string matches a database key with fuzzy matching.
        
        Args:
            query: The query string to match
            db_key: The database key to match against
            
        Returns:
            True if there's a fuzzy match, False otherwise
        """
        # Remove common prefixes/suffixes
        query_clean = query.replace('perfected ', '').replace('perfected', '').strip()
        db_key_clean = db_key.replace('perfected ', '').replace('perfected', '').strip()
        
        # Check for exact match after cleaning
        if query_clean == db_key_clean:
            return True
        
        # Check for partial match (query is contained in db_key or vice versa)
        if len(query_clean) >= 3 and len(db_key_clean) >= 3:
            return query_clean in db_key_clean or db_key_clean in query_clean
        
        return False
    
    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.local_excel_path.exists():
            try:
                self.local_excel_path.unlink()
                logger.info("Cleaned up temporary Excel file")
            except Exception as e:
                logger.warning(f"Error cleaning up Excel file: {e}")


# Global instance for easy access
_excel_parser_instance: Optional[ExcelLibSetsParser] = None


async def get_excel_parser() -> ExcelLibSetsParser:
    """Get the global Excel LibSets parser instance."""
    global _excel_parser_instance
    if _excel_parser_instance is None:
        _excel_parser_instance = ExcelLibSetsParser()
        await _excel_parser_instance.initialize_from_excel()
    return _excel_parser_instance


def get_max_pieces(set_name: str) -> int:
    """Convenience function to get max pieces for a set."""
    if _excel_parser_instance and _excel_parser_instance.initialized:
        return _excel_parser_instance.get_max_pieces(set_name)
    return 5  # Default fallback
