"""
Gear parsing and set detection for ESO builds.

This module handles the complex task of parsing player gear data from ESO Logs
and identifying gear set combinations (5pc + 5pc + 2pc, etc.).
"""

import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

from .models import GearSet, PlayerBuild

logger = logging.getLogger(__name__)


class GearParser:
    """Parser for extracting gear sets from player equipment data."""
    
    def __init__(self):
        """Initialize the gear parser."""
        self.known_sets = {}  # Cache for known set names
        
    def parse_player_gear(self, player_data: Dict[str, Any]) -> List[GearSet]:
        """Parse gear sets from player equipment data with comprehensive set detection."""
        if not player_data or 'gear' not in player_data:
            return []
        
        gear_items = player_data['gear']
        set_counts = defaultdict(int)
        set_info = {}
        slot_info = defaultdict(list)  # Track which slots each set occupies
        
        # Count pieces for each set and track slots
        for item in gear_items:
            if not isinstance(item, dict):
                continue
                
            set_id = item.get('setID')
            set_name = item.get('setName')
            slot = item.get('slot', 'unknown')
            
            if set_id and set_name:
                set_counts[set_id] += 1
                slot_info[set_id].append(slot)
                
                if set_id not in set_info:
                    set_info[set_id] = {
                        'name': self._clean_set_name(set_name),
                        'is_perfected': self._is_perfected_set(set_name),
                        'original_name': set_name
                    }
        
        # Validate and create gear sets
        gear_sets = self._create_validated_gear_sets(set_counts, set_info, slot_info)
        
        # Detect and validate common set combinations
        validated_combination = self._validate_set_combination(gear_sets, sum(set_counts.values()))
        
        logger.debug(f"Parsed {len(validated_combination)} validated gear sets from player data")
        logger.debug(f"Set combination: {[f'{s.piece_count}pc {s.name}' for s in validated_combination]}")
        
        return validated_combination
    
    def _create_validated_gear_sets(self, set_counts: Dict, set_info: Dict, slot_info: Dict) -> List[GearSet]:
        """Create gear sets with validation for meaningful combinations."""
        gear_sets = []
        
        for set_id, count in set_counts.items():
            if count < 2:  # Skip single-piece sets
                continue
                
            info = set_info[set_id]
            slots = slot_info[set_id]
            
            # Validate the set makes sense (not just random pieces)
            if self._is_valid_set_combination(count, slots):
                gear_set = GearSet(
                    name=info['name'],
                    piece_count=count,
                    is_perfected=info['is_perfected']
                )
                gear_sets.append(gear_set)
        
        # Sort by piece count (descending) for consistent ordering
        gear_sets.sort(key=lambda x: x.piece_count, reverse=True)
        return gear_sets
    
    def _is_valid_set_combination(self, count: int, slots: List[str]) -> bool:
        """Validate that a set combination makes sense."""
        # Check for obviously invalid combinations
        if count > 12:  # More pieces than possible equipment slots
            return False
            
        # Check for duplicate slots (shouldn't happen with proper gear)
        unique_slots = set(slots)
        if len(unique_slots) != count:
            logger.warning(f"Set has duplicate slots: {slots}")
            return False
            
        return True
    
    def _validate_set_combination(self, gear_sets: List[GearSet], total_pieces: int) -> List[GearSet]:
        """Validate the overall set combination and detect common patterns."""
        if not gear_sets:
            return gear_sets
            
        # Calculate total pieces in meaningful sets
        set_pieces = sum(gs.piece_count for gs in gear_sets)
        
        # Common valid combinations in ESO:
        valid_combinations = [
            [5, 5, 2],    # 5pc + 5pc + 2pc (most common)
            [5, 4, 3],    # 5pc + 4pc + 3pc
            [5, 3, 2, 2], # 5pc + 3pc + 2pc + 2pc
            [4, 4, 4],    # 4pc + 4pc + 4pc
            [5, 5],       # 5pc + 5pc (when using non-set pieces)
            [5, 4],       # 5pc + 4pc
            [5, 3],       # 5pc + 3pc
            [5, 2],       # 5pc + 2pc
            [4, 4],       # 4pc + 4pc
            [5],          # Single 5pc set
            [4],          # Single 4pc set
            [3],          # Single 3pc set
            [2]           # Single 2pc set
        ]
        
        # Get the piece counts of current sets
        current_combination = sorted([gs.piece_count for gs in gear_sets], reverse=True)
        
        # Check if current combination matches known valid patterns
        is_valid_combination = current_combination in valid_combinations
        
        if not is_valid_combination:
            logger.warning(f"Unusual set combination detected: {current_combination}")
            # Still return the sets, but log the warning
        
        # Additional validation: check total pieces make sense
        expected_gear_slots = 12  # Standard ESO gear slots
        if set_pieces > expected_gear_slots:
            logger.warning(f"Set pieces ({set_pieces}) exceed expected gear slots ({expected_gear_slots})")
        
        return gear_sets
    
    def _clean_set_name(self, set_name: str) -> str:
        """Clean and normalize set names."""
        if not set_name:
            return "Unknown Set"
            
        # Remove common prefixes/suffixes that don't add value
        cleaned = set_name.strip()
        
        # Remove "Perfected" from the display name (we track it separately)
        if cleaned.lower().startswith('perfected '):
            cleaned = cleaned[10:]  # Remove "Perfected "
        elif cleaned.lower().startswith('perf '):
            cleaned = cleaned[5:]   # Remove "Perf "
            
        return cleaned
    
    def _is_perfected_set(self, set_name: str) -> bool:
        """Determine if a set name indicates a perfected set."""
        if not set_name:
            return False
        
        # Check for common perfected set indicators
        perfected_indicators = [
            'perfected',
            'perfect',
            'perf.',
            'perf '
        ]
        
        set_name_lower = set_name.lower()
        return any(indicator in set_name_lower for indicator in perfected_indicators)
    
    def detect_build_archetype(self, gear_sets: List[GearSet], player_role: Optional[str] = None) -> str:
        """Detect the build archetype based on gear sets and role."""
        if not gear_sets:
            return "Unknown Build"
            
        set_names = [gs.name.lower() for gs in gear_sets]
        
        # Tank build detection
        tank_indicators = ['pearlescent ward', 'saxhleel', 'powerful assault', 'nazaray', 'turning tide', 'crimson oath']
        if any(indicator in ' '.join(set_names) for indicator in tank_indicators):
            return "Tank Build"
            
        # Healer build detection  
        healer_indicators = ['spell power cure', 'jorvuld', 'worm', 'sanctuary', 'hollowfang', 'lunar bastion']
        if any(indicator in ' '.join(set_names) for indicator in healer_indicators):
            return "Healer Build"
            
        # DPS build detection
        dps_indicators = ['relequen', 'kinras', 'bahsei', 'pillar of nirn', 'coral riptide', 'ansuul']
        if any(indicator in ' '.join(set_names) for indicator in dps_indicators):
            return "DPS Build"
            
        # Fallback to role if provided
        if player_role:
            return f"{player_role.title()} Build"
            
        return "Generic Build"
    
    async def get_player_gear_from_api(self, api_client, report_code: str, fight_id: int, player_id: int) -> List[GearSet]:
        """Get player gear data from the API and parse it."""
        try:
            # This would use a more specific gear query
            # For now, we'll simulate the structure
            gear_data = await api_client._make_request(
                "get_report_player_details",
                code=report_code,
                fight_id=fight_id,
                player_id=player_id
            )
            
            if gear_data and hasattr(gear_data, 'combatant_info'):
                return self.parse_player_gear({'gear': gear_data.combatant_info.gear})
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get gear for player {player_id}: {e}")
            return []


# Common ESO gear sets for validation and testing
COMMON_GEAR_SETS = {
    'tank_sets': [
        'Pearlescent Ward',
        'Lucent Echoes', 
        'Saxhleel Champion',
        'Powerful Assault',
        'Nazaray',
        'Turning Tide',
        'Crimson Oath\'s Rive'
    ],
    'healer_sets': [
        'Spell Power Cure',
        'Jorvuld\'s Guidance',
        'Worm\'s Raiment',
        'Sanctuary',
        'Hollowfang Thirst',
        'Master Architect',
        'Lunar Bastion'
    ],
    'dps_sets': [
        'Relequen',
        'Kinras\'s Wrath',
        'Bahsei\'s Mania',
        'Pillar of Nirn',
        'Coral Riptide',
        'Ansuul\'s Torment',
        'Sul-Xan\'s Torment',
        'Arms of Relequen'
    ]
}
