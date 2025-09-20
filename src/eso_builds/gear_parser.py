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
        # Use cleaned set name as key to merge perfected/non-perfected versions
        for item in gear_items:
            if not isinstance(item, dict):
                continue
                
            set_id = item.get('setID')
            set_name = item.get('setName')
            item_name = item.get('name', '')  # Individual item name (for arena weapons)
            slot = item.get('slot', 'unknown')
            
            # Debug: Log all gear items to see what we're getting
            logger.debug(f"Processing gear item: setID={set_id}, setName='{set_name}', itemName='{item_name}', slot={slot}")
            # Log all available fields for debugging
            if hasattr(item, '__dict__'):
                logger.debug(f"  All item fields: {list(item.__dict__.keys())}")
            elif isinstance(item, dict):
                logger.debug(f"  All item fields: {list(item.keys())}")
                # Log the full item for debugging
                logger.debug(f"  Full item data: {item}")
            
            # Handle set-based items (normal sets)
            if set_id and set_name:
                # Check if this is an arena weapon by individual item name
                individual_name = item.get('name', '')
                
                # Special debug for Maelstrom items
                if 'maelstrom' in str(individual_name).lower():
                    logger.info(f"🔍 MAELSTROM ITEM FOUND: name='{individual_name}', setName='{set_name}'")
                    is_arena = self._is_mythic_or_arena_weapon(individual_name)
                    logger.info(f"🔍 Arena weapon detection result: {is_arena}")
                
                if individual_name and self._is_mythic_or_arena_weapon(individual_name):
                    # Use the individual item name for arena weapons
                    cleaned_name = self._clean_set_name(individual_name)
                    logger.info(f"🎯 FOUND ARENA WEAPON: '{individual_name}' -> '{cleaned_name}'")
                    
                    # 2-handed weapons and staves count as 2 pieces
                    if self._is_two_handed_weapon(individual_name):
                        piece_count = 2
                        logger.info(f"🗡️ 2H WEAPON: '{individual_name}' counts as 2 pieces")
                    else:
                        piece_count = 1
                        
                    # Set the count for arena weapons (don't increment, set directly)
                    if cleaned_name not in set_counts:
                        set_counts[cleaned_name] = piece_count
                        slot_info[cleaned_name] = [slot]
                        
                        set_info[cleaned_name] = {
                            'name': cleaned_name,
                            'is_perfected': False,
                            'original_name': individual_name
                        }
                        logger.info(f"✅ Added arena weapon: {piece_count}pc {cleaned_name}")
                    else:
                        logger.debug(f"Arena weapon already processed: {cleaned_name}")
                    
                    continue  # Skip the normal set processing for this item
                else:
                    # Use set name for regular sets
                    cleaned_name = self._clean_set_name(set_name)
                    if individual_name and 'maelstrom' in str(individual_name).lower():
                        logger.info(f"❌ MAELSTROM NOT DETECTED AS ARENA: '{individual_name}' -> using setName '{set_name}'")
                
                # Use cleaned name as key to merge perfected/non-perfected
                set_counts[cleaned_name] += 1
                slot_info[cleaned_name].append(slot)
                
                if cleaned_name not in set_info:
                    set_info[cleaned_name] = {
                        'name': cleaned_name,
                        'is_perfected': False,  # Treat all sets the same
                        'original_name': individual_name if individual_name and self._is_mythic_or_arena_weapon(individual_name) else set_name
                    }
            
            # Handle individual items (arena weapons, mythics) that might not have setID
            elif item_name and self._is_mythic_or_arena_weapon(item_name):
                cleaned_name = self._clean_set_name(item_name)
                logger.debug(f"Found individual mythic/arena item: '{item_name}' -> '{cleaned_name}'")
                
                set_counts[cleaned_name] += 1
                slot_info[cleaned_name].append(slot)
                
                if cleaned_name not in set_info:
                    set_info[cleaned_name] = {
                        'name': cleaned_name,
                        'is_perfected': False,
                        'original_name': item_name
                    }
            
            # Handle items without setID but might have setName (possible arena weapons)
            elif not set_id and set_name:
                logger.debug(f"Found item without setID but with setName: '{set_name}', slot={slot}")
                if self._is_mythic_or_arena_weapon(set_name):
                    cleaned_name = self._clean_set_name(set_name)
                    logger.debug(f"Detected as mythic/arena weapon: '{set_name}' -> '{cleaned_name}'")
                    
                    set_counts[cleaned_name] += 1
                    slot_info[cleaned_name].append(slot)
                    
                    if cleaned_name not in set_info:
                        set_info[cleaned_name] = {
                            'name': cleaned_name,
                            'is_perfected': False,
                            'original_name': set_name
                        }
            
            # Log items that don't match any category
            else:
                logger.debug(f"Unhandled item: setID={set_id}, setName='{set_name}', itemName='{item_name}', slot={slot}")
        
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
        
        for set_name, count in set_counts.items():
            info = set_info[set_name]
            original_name = info.get('original_name', set_name)
            
            # Include single-piece sets if they are mythics or arena weapons
            if count < 2 and not self._is_mythic_or_arena_weapon(original_name):
                logger.debug(f"Skipping single-piece non-mythic/arena set: {set_name} (original: {original_name})")
                continue
            slots = slot_info[set_name]
            
            # Validate the set makes sense (not just random pieces)
            # Special handling for arena weapons and mythics - always valid
            is_special_item = self._is_mythic_or_arena_weapon(original_name)
            
            if is_special_item or self._is_valid_set_combination(count, slots):
                gear_set = GearSet(
                    name=info['name'],
                    piece_count=count,
                    is_perfected=info['is_perfected']
                )
                gear_sets.append(gear_set)
                if is_special_item:
                    logger.debug(f"Added special item (mythic/arena): {count}pc {info['name']}")
        
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
    
    def _is_mythic_or_arena_weapon(self, set_name: str) -> bool:
        """Check if a set is a mythic item or arena weapon (typically 1-piece sets)."""
        if not set_name:
            return False
        
        set_lower = set_name.lower()
        
        # Common mythic items (1-piece sets)
        mythic_indicators = [
            'kilt', 'harpooner', 'ring of the pale order', 'ring of the wild hunt',
            'malacath', 'thrassian stranglers', 'snow treaders', 'gaze of sithis',
            'death dealer', 'markyn ring', 'oakensoul', 'velothi ur-mage',
            'mora\'s whispers', 'esoteric environment greaves', 'spaulder of ruin',
            'lefthander\'s aegis belt', 'pearls of ehlnofey', 'shapeshifter\'s chain',
            'sea-serpent\'s coil', 'antiquarian\'s eye', 'torc of tonal constancy'
        ]
        
        # Monster sets (when worn as single pieces for 1pc bonus)
        monster_set_indicators = [
            'slimecraw', 'kjalnar', 'valkyn skoria', 'zaan', 'domihaus', 'iceheart',
            'earthgore', 'chokethorn', 'bloodspawn', 'lord warden', 'mighty chudan',
            'troll king', 'bone pirate', 'stormfist', 'selene', 'velidreth',
            'grothdarr', 'ilambris', 'nerien\'eth', 'spawn of mephala', 'tremorscale',
            'thurvokun', 'balorgh', 'maarselok', 'grundwulf', 'stone-talker',
            'nazaray', 'archdruid devyric', 'ozezan the inferno', 'nunatak'
        ]
        
        # Arena weapons (Maelstrom, Dragonstar, Blackrose Prison, Vateshran Hollows)
        arena_weapon_indicators = [
            'maelstrom', 'dragonstar', 'blackrose prison', 'vateshran hollows',
            'master\'s', 'perfected master\'s', 'perfected maelstrom', 'perfected dragonstar',
            'perfected blackrose', 'perfected vateshran'
        ]
        
        # Check for mythic items
        if any(mythic in set_lower for mythic in mythic_indicators):
            return True
            
        # Check for monster sets (when used as 1pc)
        if any(monster in set_lower for monster in monster_set_indicators):
            return True
            
        # Check for arena weapons
        if any(arena in set_lower for arena in arena_weapon_indicators):
            return True
            
        return False
    
    def _is_two_handed_weapon(self, item_name: str) -> bool:
        """Check if an item is a 2-handed weapon or staff (counts as 2 pieces)."""
        if not item_name:
            return False
            
        item_lower = item_name.lower()
        
        # 2-handed weapon indicators
        two_handed_indicators = [
            'greatsword', 'maul', 'battle axe', 'battleaxe', 'two handed',
            'staff', 'inferno staff', 'ice staff', 'lightning staff',
            'restoration staff', 'destruction staff', 'bow'
        ]
        
        return any(indicator in item_lower for indicator in two_handed_indicators)
    
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
