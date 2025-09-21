"""
Class analyzer for ESO character builds.

This module analyzes character abilities, gear, and other data to determine
skill lines, mundus stones, racial passives, and other class-related information.
"""

import logging
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass

from .models import ClassSummary, PlayerBuild

logger = logging.getLogger(__name__)


class ClassAnalyzer:
    """Analyzes ESO character data to determine skill lines and other class information."""
    
    def __init__(self):
        """Initialize the class analyzer."""
        # Define skill line abilities and their associated skill lines
        self.skill_line_abilities = {
            # Arcanist skill lines
            "Herald of the Tome": [
                "Fatecarver", "Beam", "Cruxweaver Armor", "Impervious Runeward", "Reconstructive Domain",
                "Runeblades", "Cephaliarch's Flail", "Crunemend", "Tome Bearer's Inspiration",
                "The Unblinking Eye", "Gibbering Shield", "Chakram of the Ancient", "Velothi's Truth",
                "Runic Jolt", "Rune of Displacement", "Tentacular Dread", "Abyssal Impact"
            ],
            "Soldier of Apocrypha": [
                "Barbed Trap", "Poison Injection", "Lethal Arrow", "Focused Aim", "Snipe",
                "Volley", "Endless Hail", "Arrow Spray", "Bombard", "Scorched Earth",
                "Razor Caltrops", "Arrow Barrage", "Morphing Arrow", "Venom Arrow",
                "Power of the Light", "Solar Barrage", "Radiant Destruction", "Solar Prison"
            ],
            "Curative Runeforms": [
                "Regeneration", "Combat Prayer", "Blessing of Protection", "Blessing of Restoration",
                "Healing Springs", "Rapid Regeneration", "Combat Prayer", "Luminous Shards",
                "Illustrious Healing", "Healing Ward", "Purifying Light", "Radiant Aura"
            ],
            
            # Sorcerer skill lines
            "Daedric Summoning": [
                "Summon Unstable Clannfear", "Summon Unstable Familiar", "Summon Volatile Familiar",
                "Summon Winged Twilight", "Summon Storm Atronach", "Summon Storm Atronach",
                "Bound Armor", "Bound Armaments", "Conjured Ward", "Empower Ward",
                "Daedric Curse", "Daedric Prey", "Daedric Tomb", "Summon Restoring Twilight"
            ],
            "Dark Magic": [
                "Crystal Shard", "Crystal Fragments", "Crystal Weapon", "Crystal Blast",
                "Encase", "Dark Deal", "Dark Exchange", "Negate Magic", "Suppression Field",
                "Rune Prison", "Rune Cage", "Mage's Wrath", "Mage's Fury"
            ],
            "Storm Calling": [
                "Lightning Splash", "Lightning Form", "Overload", "Lightning Flood",
                "Lightning Bolt", "Crushing Shock", "Lightning Staff", "Surge",
                "Power Surge", "Critical Surge", "Lightning Splash", "Lightning Flood"
            ],
            
            # Dragonknight skill lines
            "Ardent Flame": [
                "Flame Lash", "Flame Whip", "Searing Strike", "Lava Whip",
                "Inferno", "Burning Embers", "Flame Clench", "Flame Lash",
                "Molten Whip", "Flame Lash", "Burning Embers", "Flame Clench"
            ],
            "Draconic Power": [
                "Dragon Blood", "Green Dragon Blood", "Spiked Armor", "Reflective Scales",
                "Dragon Leap", "Take Flight", "Dragonknight Standard", "Banner",
                "Dragon Leap", "Take Flight", "Dragonknight Standard", "Banner"
            ],
            "Earthen Heart": [
                "Stonefist", "Stone Giant", "Obsidian Shard", "Petrify",
                "Magma Armor", "Ash Cloud", "Volcanic Rune", "Eruption",
                "Ash Cloud", "Volcanic Rune", "Eruption", "Magma Armor"
            ],
            
            # Necromancer skill lines
            "Bone Tyrant": [
                "Summon Skeletal Arcanist", "Summon Skeletal Mage", "Summon Skeletal Archer",
                "Summon Skeletal Warrior", "Summon Blastbones", "Summon Skeletal Mage",
                "Bone Armor", "Beckoning Armor", "Summon Skeletal Arcanist", "Summon Skeletal Mage"
            ],
            "Grave Lord": [
                "Bitter Harvest", "Expunge and Modify", "Render Flesh", "Expunge and Modify",
                "Boneyard", "Shocking Siphon", "Skeletal Mage", "Bitter Harvest",
                "Expunge and Modify", "Render Flesh", "Expunge and Modify", "Boneyard"
            ],
            "Living Death": [
                "Restoring Tether", "Braided Tether", "Agony Totem", "Renewing Undeath",
                "Life amid Death", "Braided Tether", "Restoring Tether", "Agony Totem",
                "Renewing Undeath", "Life amid Death", "Braided Tether", "Restoring Tether"
            ],
            
            # Templar skill lines
            "Aedric Spear": [
                "Puncturing Strikes", "Puncturing Sweep", "Burning Light", "Radiant Destruction",
                "Piercing Javelin", "Binding Javelin", "Spear Shards", "Luminous Shards",
                "Solar Prison", "Binding Javelin", "Spear Shards", "Luminous Shards"
            ],
            "Dawn's Wrath": [
                "Sun Fire", "Backlash", "Solar Flare", "Solar Barrage",
                "Nova", "Solar Prison", "Radiant Aura", "Power of the Light",
                "Solar Flare", "Solar Barrage", "Nova", "Solar Prison"
            ],
            "Restoring Light": [
                "Rushed Ceremony", "Breath of Life", "Cleansing Ritual", "Purifying Light",
                "Rite of Passage", "Radiant Aura", "Power of the Light", "Solar Flare",
                "Solar Barrage", "Nova", "Solar Prison", "Radiant Aura"
            ],
            
            # Warden skill lines
            "Animal Companions": [
                "Falcon's Swiftness", "Falcon's Swiftness", "Falcon's Swiftness", "Falcon's Swiftness",
                "Falcon's Swiftness", "Falcon's Swiftness", "Falcon's Swiftness", "Falcon's Swiftness",
                "Falcon's Swiftness", "Falcon's Swiftness", "Falcon's Swiftness", "Falcon's Swiftness"
            ],
            "Green Balance": [
                "Living Vines", "Living Vines", "Living Vines", "Living Vines",
                "Living Vines", "Living Vines", "Living Vines", "Living Vines",
                "Living Vines", "Living Vines", "Living Vines", "Living Vines"
            ],
            "Winter's Embrace": [
                "Frozen Device", "Frozen Device", "Frozen Device", "Frozen Device",
                "Frozen Device", "Frozen Device", "Frozen Device", "Frozen Device",
                "Frozen Device", "Frozen Device", "Frozen Device", "Frozen Device"
            ],
            
            # Nightblade skill lines
            "Assassination": [
                "Teleport Strike", "Ambush", "Mark Target", "Assassin's Blade",
                "Death Stroke", "Incapacitating Strike", "Surprise Attack", "Teleport Strike",
                "Ambush", "Mark Target", "Assassin's Blade", "Death Stroke"
            ],
            "Shadow": [
                "Veiled Strike", "Shadow Cloak", "Shadow Image", "Path of Darkness",
                "Consuming Darkness", "Shadow Cloak", "Shadow Image", "Path of Darkness",
                "Consuming Darkness", "Shadow Cloak", "Shadow Image", "Path of Darkness"
            ],
            "Siphoning": [
                "Strife", "Funnel Health", "Drain Power", "Soul Shred",
                "Soul Assault", "Strife", "Funnel Health", "Drain Power",
                "Soul Shred", "Soul Assault", "Strife", "Funnel Health"
            ]
        }
        
        # Mundus stone detection from gear sets - comprehensive patterns
        self.mundus_stones = {
            "The Thief": ["The Thief", "Thief", "Mundus Stone", "thief mundus", "mundus stone of the thief"],
            "The Lover": ["The Lover", "Lover", "Mundus Stone", "lover mundus", "mundus stone of the lover"],
            "The Shadow": ["The Shadow", "Shadow", "Mundus Stone", "shadow mundus", "mundus stone of the shadow"],
            "The Apprentice": ["The Apprentice", "Apprentice", "Mundus Stone", "apprentice mundus", "mundus stone of the apprentice"],
            "The Warrior": ["The Warrior", "Warrior", "Mundus Stone", "warrior mundus", "mundus stone of the warrior"],
            "The Mage": ["The Mage", "Mage", "Mundus Stone", "mage mundus", "mundus stone of the mage"],
            "The Serpent": ["The Serpent", "Serpent", "Mundus Stone", "serpent mundus", "mundus stone of the serpent"],
            "The Lady": ["The Lady", "Lady", "Mundus Stone", "lady mundus", "mundus stone of the lady"],
            "The Steed": ["The Steed", "Steed", "Mundus Stone", "steed mundus", "mundus stone of the steed"],
            "The Lord": ["The Lord", "Lord", "Mundus Stone", "lord mundus", "mundus stone of the lord"],
            "The Ritual": ["The Ritual", "Ritual", "Mundus Stone", "ritual mundus", "mundus stone of the ritual"],
            "The Atronach": ["The Atronach", "Atronach", "Mundus Stone", "atronach mundus", "mundus stone of the atronach"],
            "The Tower": ["The Tower", "Tower", "Mundus Stone", "tower mundus", "mundus stone of the tower"]
        }
        
        # Racial passive detection from abilities
        self.racial_passives = {
            "High Elf": ["Spell Recharge", "Elemental Talent", "Sylvan Care"],
            "Wood Elf": ["Resist Affliction", "Y'ffre's Endurance", "Hunt Leader"],
            "Dark Elf": ["Dynamic", "Resist Flame", "Ruination"],
            "Nord": ["Resist Frost", "Rugged", "Battle Cry"],
            "Imperial": ["Red Diamond", "Imperial Mettle", "Tough"],
            "Breton": ["Spell Resistance", "Magicka Mastery", "Gift of Magnus"],
            "Redguard": ["Adrenaline Rush", "Way of the Arena", "Conditioning"],
            "Orc": ["Berserker Rage", "Robust", "Swift"],
            "Khajiit": ["Robust", "Lunar Blessings", "Stealthy"],
            "Argonian": ["Amphibious", "Argonian Resistance", "Life Mender"]
        }
    
    def analyze_character(self, player: PlayerBuild, abilities: List[str] = None, buffs: List[str] = None) -> ClassSummary:
        """Analyze a character to determine skill lines, mundus stone, and racial passives."""
        logger.debug(f"Analyzing character: {player.name} ({player.character_class})")
        
        # Determine skill lines from abilities and class
        skill_lines = self._determine_skill_lines(player.character_class, abilities or [])
        
        # Determine mundus stone from buff data (preferred) or gear sets (fallback)
        mundus_stone = self._determine_mundus_stone_from_buffs(buffs or [])
        if not mundus_stone:
            mundus_stone = self._determine_mundus_stone(player.gear_sets)
        
        # If still no mundus detected, try a more aggressive gear search
        if not mundus_stone:
            mundus_stone = self._determine_mundus_stone_aggressive(player.gear_sets)
        
        logger.debug(f"Mundus detection for {player.name}: {mundus_stone}")
        
        # Determine racial passives from abilities
        racial_passives = self._determine_racial_passives(abilities or [])
        
        return ClassSummary(
            character_name=player.name,
            character_class=player.character_class,
            mundus_stone=mundus_stone,
            racial_passives=racial_passives,
            skill_lines=skill_lines
        )
    
    def _determine_skill_lines(self, character_class: str, abilities: List[str]) -> List[str]:
        """Determine skill lines based on character class and abilities used."""
        detected_skill_lines = set()
        
        # Start with the primary skill line for the class
        primary_skill_line = self._get_primary_skill_line(character_class)
        if primary_skill_line:
            detected_skill_lines.add(primary_skill_line)
        
        # Look for abilities that indicate other skill lines
        for skill_line, skill_abilities in self.skill_line_abilities.items():
            if skill_line == primary_skill_line:
                continue  # Skip primary skill line as it's already added
            
            for ability in abilities:
                if ability in skill_abilities:
                    detected_skill_lines.add(skill_line)
                    break
        
        # Ensure we have at least the primary skill line
        if not detected_skill_lines and primary_skill_line:
            detected_skill_lines.add(primary_skill_line)
        
        # Fill remaining slots with "_" if we don't have 3 skill lines
        result = list(detected_skill_lines)
        while len(result) < 3:
            result.append("_")
        
        return result[:3]  # Limit to 3 skill lines
    
    def _get_primary_skill_line(self, character_class: str) -> Optional[str]:
        """Get the primary skill line for a character class."""
        primary_skill_lines = {
            "Arcanist": "Herald of the Tome",
            "Sorcerer": "Storm Calling",
            "DragonKnight": "Ardent Flame",
            "Necromancer": "Grave Lord",
            "Templar": "Aedric Spear",
            "Warden": "Animal Companions",
            "Nightblade": "Assassination"
        }
        return primary_skill_lines.get(character_class)
    
    def _determine_mundus_stone_from_buffs(self, buffs: List[str]) -> Optional[str]:
        """Determine mundus stone from buff data (Boon: prefix)."""
        for buff in buffs:
            if buff.startswith("Boon:"):
                # Extract mundus stone name after "Boon: "
                mundus_name = buff[5:].strip()  # Remove "Boon: " prefix
                logger.debug(f"Found Boon buff: '{buff}' -> mundus: '{mundus_name}'")
                return mundus_name
        return None

    def _determine_mundus_stone(self, gear_sets: List) -> Optional[str]:
        """Determine mundus stone from gear sets."""
        logger.debug(f"Checking {len(gear_sets)} gear sets for mundus stones")
        for gear_set in gear_sets:
            gear_name = gear_set.name.lower()
            logger.debug(f"Checking gear set: '{gear_set.name}' (lowercase: '{gear_name}')")
            for mundus_name, mundus_keywords in self.mundus_stones.items():
                for keyword in mundus_keywords:
                    if keyword.lower() in gear_name:
                        logger.debug(f"Found mundus match: '{keyword.lower()}' in '{gear_name}' -> {mundus_name}")
                        return mundus_name
        logger.debug("No mundus stone detected from gear sets")
        return None

    def _determine_mundus_stone_aggressive(self, gear_sets: List) -> Optional[str]:
        """More aggressive mundus stone detection from gear sets."""
        logger.debug(f"Aggressive mundus search in {len(gear_sets)} gear sets")
        
        # More comprehensive mundus stone patterns
        aggressive_patterns = {
            "The Thief": ["thief", "critical", "crit"],
            "The Lover": ["lover", "penetration", "pen"],
            "The Shadow": ["shadow", "stealth", "stealthy"],
            "The Apprentice": ["apprentice", "magic", "magicka"],
            "The Warrior": ["warrior", "physical", "stamina"],
            "The Mage": ["mage", "magic", "magicka"],
            "The Serpent": ["serpent", "recovery", "regen"],
            "The Lady": ["lady", "resistance", "resist"],
            "The Steed": ["steed", "speed", "movement"],
            "The Lord": ["lord", "health", "hp"],
            "The Ritual": ["ritual", "healing", "heal"],
            "The Atronach": ["atronach", "magicka", "mana"],
            "The Tower": ["tower", "magicka", "mana"]
        }
        
        for gear_set in gear_sets:
            gear_name = gear_set.name.lower()
            logger.debug(f"Aggressive search in: '{gear_set.name}' (lowercase: '{gear_name}')")
            
            for mundus_name, patterns in aggressive_patterns.items():
                for pattern in patterns:
                    if pattern in gear_name:
                        logger.debug(f"Aggressive match: '{pattern}' in '{gear_name}' -> {mundus_name}")
                        return mundus_name
        
        logger.debug("No mundus stone found with aggressive search")
        return None
    
    def _determine_racial_passives(self, abilities: List[str]) -> List[str]:
        """Determine racial passives from abilities used."""
        detected_passives = []
        
        for race, passives in self.racial_passives.items():
            for passive in passives:
                if passive in abilities:
                    detected_passives.append(f"{race}: {passive}")
        
        return detected_passives
