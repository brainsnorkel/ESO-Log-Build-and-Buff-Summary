"""
Gear parsing and set detection for ESO builds.

This module handles the complex task of parsing player gear data from ESO Logs
and identifying gear set combinations (5pc + 5pc + 2pc, etc.).
"""

import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

from .models import GearSet, PlayerBuild
from .excel_libsets_parser import get_excel_parser

logger = logging.getLogger(__name__)


class GearParser:
    """Parser for extracting gear sets from player equipment data."""
    
    def __init__(self):
        """Initialize the gear parser."""
        self.known_sets = {}  # Cache for known set names
        self.libsets_initialized = False
    
    async def initialize_libsets(self):
        """Initialize Excel LibSets data if not already done."""
        if not self.libsets_initialized:
            try:
                excel_parser = await get_excel_parser()
                if excel_parser.initialized:
                    self.libsets_initialized = True
                    logger.info("Excel LibSets data initialized successfully")
                else:
                    logger.warning("Failed to initialize Excel LibSets data, falling back to hardcoded assumptions")
            except Exception as e:
                logger.error(f"Error initializing Excel LibSets data: {e}")
                logger.warning("Falling back to hardcoded assumptions")
        
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
                    # Determine if it's a mythic or arena weapon for better logging
                    is_mythic = self._is_mythic_item(individual_name)
                    is_arena = self._is_arena_weapon(individual_name)
                    
                    if is_mythic:
                        logger.info(f"💎 FOUND MYTHIC ITEM: '{individual_name}' from set '{set_name}'")
                    elif is_arena:
                        logger.info(f"🎯 FOUND ARENA WEAPON: '{individual_name}' from set '{set_name}'")
                    else:
                        logger.info(f"🔧 FOUND SPECIAL ITEM: '{individual_name}' from set '{set_name}'")
                    
                    # Always use the set name, not the individual item name
                    cleaned_name = self._clean_set_name(set_name)
                    
                    if self._is_two_handed_weapon(individual_name):
                        # 2-handed weapons count as 2 pieces
                        piece_count = 2
                        logger.info(f"🗡️ 2H WEAPON: '{individual_name}' counts as 2 pieces for set '{cleaned_name}'")
                    else:
                        # 1-handed weapons count as 1 piece
                        piece_count = 1
                        logger.info(f"🔗 1H WEAPON: '{individual_name}' counts as 1 piece for set '{cleaned_name}'")
                        
                    # Add or increment the count for arena weapons
                    if cleaned_name not in set_counts:
                        set_counts[cleaned_name] = piece_count
                        slot_info[cleaned_name] = [slot]
                        
                        set_info[cleaned_name] = {
                            'name': cleaned_name,
                            'is_perfected': False,
                            'original_name': set_name
                        }
                        item_type = "mythic" if is_mythic else "arena weapon" if is_arena else "special item"
                        logger.info(f"✅ Added {item_type}: {piece_count}pc {cleaned_name}")
                    else:
                        # Increment count for grouped special items (like multiple 1H weapons from same set)
                        set_counts[cleaned_name] += piece_count
                        slot_info[cleaned_name].append(slot)
                        item_type = "mythic" if is_mythic else "arena weapon" if is_arena else "special item"
                        logger.info(f"✅ Added to {item_type} set: {piece_count}pc -> {set_counts[cleaned_name]}pc total {cleaned_name}")
                    
                    continue  # Skip the normal set processing for this item
                else:
                    # Use set name for regular sets
                    cleaned_name = self._clean_set_name(set_name)
                    if individual_name and 'maelstrom' in str(individual_name).lower():
                        logger.info(f"❌ MAELSTROM NOT DETECTED AS ARENA: '{individual_name}' -> using setName '{set_name}'")
                
                # Use cleaned name as key to merge perfected/non-perfected
                # 2-handed weapons and staves count as 2 pieces (they occupy 2 gear slots)
                if self._is_two_handed_weapon(item_name):
                    piece_count = 2
                    logger.info(f"🗡️ 2H WEAPON in regular set: '{item_name}' counts as 2 pieces for {set_name}")
                else:
                    piece_count = 1
                    
                    
                set_counts[cleaned_name] += piece_count
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
            
            # Include single-piece sets if they are mythics, arena weapons, or monster sets
            if count < 2 and not (self._is_mythic_or_arena_weapon(original_name) or self._is_monster_set(set_name)):
                logger.debug(f"Skipping single-piece non-special set: {set_name} (original: {original_name})")
                continue
                
            slots = slot_info[set_name]
            
            # Validate the set makes sense (not just random pieces)
            # Special handling for arena weapons, mythics, and monster sets - always valid
            is_special_item = self._is_mythic_or_arena_weapon(original_name) or self._is_monster_set(set_name)
            
            if is_special_item or self._is_valid_set_combination(count, slots):
                max_pieces = self._get_set_max_pieces(info['name'])
                is_incomplete = count < max_pieces
                is_mythic = self._is_mythic_item(original_name)
                
                gear_set = GearSet(
                    name=info['name'],
                    piece_count=count,
                    is_perfected=info['is_perfected'],
                    max_pieces=max_pieces,
                    is_incomplete=is_incomplete,
                    is_mythic=is_mythic
                )
                gear_sets.append(gear_set)
                if is_special_item:
                    logger.debug(f"Added special item (mythic/arena): {count}pc {info['name']}")
                else:
                    logger.debug(f"Added regular set: {count}pc {info['name']}")
                    if is_incomplete:
                        logger.debug(f"  ⚠️  Set is incomplete: {count}/{max_pieces} pieces")
            
        # Sort by piece count (descending) for consistent ordering
        gear_sets.sort(key=lambda x: x.piece_count, reverse=True)
        return gear_sets
    
    def _get_set_max_pieces(self, set_name: str) -> int:
        """Get the maximum number of pieces for a set using Excel LibSets data."""
        if self.libsets_initialized:
            try:
                from .excel_libsets_parser import _excel_parser_instance
                if _excel_parser_instance and _excel_parser_instance.initialized:
                    return _excel_parser_instance.get_max_pieces(set_name)
            except Exception as e:
                logger.warning(f"Error getting max pieces from Excel parser for '{set_name}': {e}")
        
        # Fallback to hardcoded assumptions
        set_lower = set_name.lower()
        
        # Monster sets
        if any(indicator in set_lower for indicator in ['monster', 'undaunted', 'slimecraw', 'nazaray', 'baron zaudrus']):
            return 2
        
        # Mythic items
        if any(indicator in set_lower for indicator in ['mythic', 'oakensoul', 'velothi', 'pearls']):
            return 1
        
        # Arena weapons
        if any(indicator in set_lower for indicator in ['maelstrom', 'arena', 'crushing', 'merciless']):
            is_2h = any(term in set_lower for term in ['staff', 'bow', 'greatsword', 'maul', 'battleaxe'])
            return 2 if is_2h else 1
        
        # Default to 5 for regular sets
        return 5

    def _is_valid_set_combination(self, count: int, slots: List[str]) -> bool:
        """Validate that a set combination makes sense."""
        # Check for obviously invalid combinations
        if count > 12:  # More pieces than possible equipment slots
            return False
            
        # Check for duplicate slots (shouldn't happen with proper gear)
        # Note: For 2-handed weapons, the piece count can be higher than unique slots
        # because a 2-handed weapon in one slot counts as 2 pieces
        unique_slots = set(slots)
        
        if len(unique_slots) > count:
            logger.warning(f"Set has more unique slots than pieces: slots={slots}, count={count}")
            return False
            
        return True
    
    def _validate_set_combination(self, gear_sets: List[GearSet], total_pieces: int) -> List[GearSet]:
        """Validate set completion status and check for obvious errors."""
        if not gear_sets:
            return gear_sets
            
        # Calculate total pieces in meaningful sets
        set_pieces = sum(gs.piece_count for gs in gear_sets)
        
        # Check for obvious errors: more pieces than possible gear slots
        expected_gear_slots = 14  # Standard ESO gear slots: head, shoulder, arms, legs, chest, belt, feet, neck, ring, ring, front weapon, front weapon, back weapon, back weapon
        if set_pieces > expected_gear_slots:
            logger.warning(f"Set pieces ({set_pieces}) exceed expected gear slots ({expected_gear_slots})")
        
        # Log set completion status for debugging
        for gear_set in gear_sets:
            if gear_set.piece_count > gear_set.max_pieces:
                logger.debug(f"Set '{gear_set.name}' has {gear_set.piece_count} pieces but max is {gear_set.max_pieces} - may be parsing error")
            elif gear_set.piece_count < gear_set.max_pieces:
                logger.debug(f"Set '{gear_set.name}' is incomplete: {gear_set.piece_count}/{gear_set.max_pieces} pieces")
            else:
                logger.debug(f"Set '{gear_set.name}' is complete: {gear_set.piece_count}/{gear_set.max_pieces} pieces")
        
        return gear_sets
    
    def _is_monster_set(self, set_name: str) -> bool:
        """Check if a set is a monster set (can be worn as 1pc for the 1-piece bonus)."""
        if not set_name:
            return False
            
        set_lower = set_name.lower()
        
        # Common monster sets that players often wear as 1pc
        monster_set_names = [
            'slimecraw', 'kjalnar', 'valkyn skoria', 'zaan', 'domihaus', 'iceheart',
            'earthgore', 'chokethorn', 'bloodspawn', 'lord warden', 'mighty chudan',
            'troll king', 'bone pirate', 'stormfist', 'selene', 'velidreth',
            'grothdarr', 'ilambris', 'nerien\'eth', 'spawn of mephala', 'tremorscale',
            'thurvokun', 'balorgh', 'maarselok', 'grundwulf', 'stone-talker',
            'nazaray', 'archdruid devyric', 'ozezan the inferno', 'nunatak'
        ]
        
        return any(monster in set_lower for monster in monster_set_names)
    
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
        
        # Monster sets should NOT be treated as individual items - they are 2-piece sets
        # Only include them here if they're actually being used as 1-piece (rare case)
        # Most of the time, monster sets should be parsed as normal 2-piece sets
        monster_set_indicators = [
            # Remove most monster sets - they should be 2pc sets, not individual items
            # Only keep ones that are commonly used as 1pc for specific bonuses
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
    
    def _is_mythic_item(self, set_name: str) -> bool:
        """Check if a set is specifically a mythic item."""
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
        
        return any(mythic in set_lower for mythic in mythic_indicators)
    
    def _is_arena_weapon(self, set_name: str) -> bool:
        """Check if a set is specifically an arena weapon."""
        if not set_name:
            return False
        
        set_lower = set_name.lower()
        
        # Arena weapons (Maelstrom, Dragonstar, Blackrose Prison, Vateshran Hollows)
        arena_weapon_indicators = [
            'maelstrom', 'dragonstar', 'blackrose prison', 'vateshran hollows',
            'master\'s', 'perfected master\'s', 'perfected maelstrom', 'perfected dragonstar',
            'perfected blackrose', 'perfected vateshran'
        ]
        
        return any(arena in set_lower for arena in arena_weapon_indicators)
    
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
