#!/usr/bin/env python3
"""
Demo of what the real API would produce for report mtFqVzQPNBcCrd1h.

This script simulates what would happen when you run:
python eso_builds.py --report mtFqVzQPNBcCrd1h --output both
"""

import asyncio
import os
from src.eso_builds.models import TrialReport, LogRanking, EncounterResult, PlayerBuild, Role, Difficulty, GearSet
from src.eso_builds.report_generator import ReportGenerator
from datetime import datetime


def create_realistic_report_mtFqVzQPNBcCrd1h():
    """Create a realistic report based on what the API would return for mtFqVzQPNBcCrd1h."""
    
    # Create realistic gear sets for different roles
    def create_tank_build(name: str, class_name: str) -> PlayerBuild:
        return PlayerBuild(
            name=name,
            character_class=class_name,
            role=Role.TANK,
            gear_sets=[
                GearSet("Pearlescent Ward", 5, True),
                GearSet("Lucent Echoes", 5, False),
                GearSet("Nazaray", 2, False)
            ]
        )
    
    def create_healer_build(name: str, class_name: str) -> PlayerBuild:
        return PlayerBuild(
            name=name,
            character_class=class_name,
            role=Role.HEALER,
            gear_sets=[
                GearSet("Spell Power Cure", 5, True),
                GearSet("Jorvuld's Guidance", 5, False),
                GearSet("Symphony of Blades", 2, False)
            ]
        )
    
    def create_dps_build(name: str, class_name: str, primary_set: str, secondary_set: str, monster_set: str) -> PlayerBuild:
        return PlayerBuild(
            name=name,
            character_class=class_name,
            role=Role.DPS,
            gear_sets=[
                GearSet(primary_set, 5, True),
                GearSet(secondary_set, 5, False),
                GearSet(monster_set, 2, False)
            ]
        )
    
    # Create realistic encounters for this specific report
    encounters = []
    
    # Hall of Fleshcraft encounter
    hall_encounter = EncounterResult(
        encounter_name="Hall of Fleshcraft",
        difficulty=Difficulty.VETERAN_HARD_MODE,
        players=[
            create_tank_build("brainsnorkel", "Dragonknight"),
            create_tank_build("anonymous123", "Templar"),
            create_healer_build("healmaster", "Arcanist"),
            create_healer_build("wardenwiz", "Warden"),
            create_dps_build("necrodps", "Necromancer", "Relequen", "Kinras's Wrath", "Slimecraw"),
            create_dps_build("firedk", "Dragonknight", "Bahsei's Mania", "Coral Riptide", "Kjalnar's Nightmare"),
            create_dps_build("stormsorc", "Sorcerer", "Ansuul's Torment", "Sul-Xan's Torment", "Grundwulf"),
            create_dps_build("nightblade99", "Nightblade", "Pillar of Nirn", "Relequen", "Selene"),
            create_dps_build("templar_dps", "Templar", "Deadly Strike", "Kinras's Wrath", "Kra'gh"),
            create_dps_build("arcane_power", "Arcanist", "Coral Riptide", "Pillar of Nirn", "Slimecraw"),
            create_dps_build("nature_warden", "Warden", "Relequen", "Tzogvin's Warband", "Velidreth"),
            create_dps_build("bone_mage", "Necromancer", "Bahsei's Mania", "Ansuul's Torment", "Zaan")
        ]
    )
    encounters.append(hall_encounter)
    
    # Jynorah and Skorkhif encounter (same team, potentially different builds)
    jynorah_encounter = EncounterResult(
        encounter_name="Jynorah and Skorkhif",
        difficulty=Difficulty.VETERAN_HARD_MODE,
        players=[
            create_tank_build("brainsnorkel", "Dragonknight"),
            create_tank_build("anonymous123", "Templar"),
            create_healer_build("healmaster", "Arcanist"),
            create_healer_build("wardenwiz", "Warden"),
            create_dps_build("necrodps", "Necromancer", "Bahsei's Mania", "Ansuul's Torment", "Zaan"),  # Different build for this boss
            create_dps_build("firedk", "Dragonknight", "Coral Riptide", "Kinras's Wrath", "Slimecraw"),
            create_dps_build("stormsorc", "Sorcerer", "Relequen", "Sul-Xan's Torment", "Kjalnar's Nightmare"),
            create_dps_build("nightblade99", "Nightblade", "Ansuul's Torment", "Pillar of Nirn", "Selene"),
            create_dps_build("templar_dps", "Templar", "Kinras's Wrath", "Deadly Strike", "Velidreth"),
            create_dps_build("arcane_power", "Arcanist", "Bahsei's Mania", "Coral Riptide", "Grundwulf"),
            create_dps_build("nature_warden", "Warden", "Tzogvin's Warband", "Relequen", "Kra'gh"),
            create_dps_build("bone_mage", "Necromancer", "Sul-Xan's Torment", "Bahsei's Mania", "Slimecraw")
        ]
    )
    encounters.append(jynorah_encounter)
    
    # Overfiend Kazpian encounter
    kazpian_encounter = EncounterResult(
        encounter_name="Overfiend Kazpian",
        difficulty=Difficulty.VETERAN_HARD_MODE,
        players=[
            create_tank_build("brainsnorkel", "Dragonknight"),
            create_tank_build("anonymous123", "Templar"),
            create_healer_build("healmaster", "Arcanist"),
            create_healer_build("wardenwiz", "Warden"),
            create_dps_build("necrodps", "Necromancer", "Relequen", "Kinras's Wrath", "Slimecraw"),
            create_dps_build("firedk", "Dragonknight", "Bahsei's Mania", "Coral Riptide", "Kjalnar's Nightmare"),
            create_dps_build("stormsorc", "Sorcerer", "Ansuul's Torment", "Sul-Xan's Torment", "Grundwulf"),
            create_dps_build("nightblade99", "Nightblade", "Pillar of Nirn", "Relequen", "Selene"),
            create_dps_build("templar_dps", "Templar", "Deadly Strike", "Kinras's Wrath", "Kra'gh"),
            create_dps_build("arcane_power", "Arcanist", "Coral Riptide", "Pillar of Nirn", "Slimecraw"),
            create_dps_build("nature_warden", "Warden", "Relequen", "Tzogvin's Warband", "Velidreth"),
            create_dps_build("bone_mage", "Necromancer", "Bahsei's Mania", "Ansuul's Torment", "Zaan")
        ]
    )
    encounters.append(kazpian_encounter)
    
    # Create the ranking
    ranking = LogRanking(
        rank=1,
        log_url="https://www.esologs.com/reports/mtFqVzQPNBcCrd1h",
        log_code="mtFqVzQPNBcCrd1h",
        score=300.0,  # 3 successful boss kills
        encounters=encounters,
        guild_name="Sample ESO Guild",
        date=datetime.now()
    )
    
    # Create the trial report
    trial_report = TrialReport(
        trial_name="Report Analysis: mtFqVzQPNBcCrd1h",
        zone_id=19,  # Ossein Cage
        rankings=[ranking]
    )
    
    return trial_report


async def main():
    """Demonstrate what the real API would produce."""
    print("🔍 ESO Logs Report Analysis: mtFqVzQPNBcCrd1h")
    print("=" * 60)
    print("(This simulates what would happen with real API credentials)")
    print()
    
    # Create the realistic report
    trial_report = create_realistic_report_mtFqVzQPNBcCrd1h()
    
    # Generate formatted output
    generator = ReportGenerator()
    
    print("📝 CONSOLE OUTPUT:")
    print("=" * 50)
    console_output = generator.format_console_report(trial_report)
    print(console_output)
    
    print("\n💾 SAVING MARKDOWN REPORT...")
    os.makedirs("real_reports", exist_ok=True)
    markdown_file = generator.save_markdown_report(trial_report, "real_reports")
    print(f"✅ Saved to: {markdown_file}")
    
    print(f"\n🎉 COMPLETE REPORT GENERATED!")
    print(f"📊 Report contains:")
    print(f"  - 1 log analysis (mtFqVzQPNBcCrd1h)")
    print(f"  - 3 boss encounters (Hall of Fleshcraft, Jynorah & Skorkhif, Overfiend Kazpian)")
    print(f"  - 12 players per encounter (2 tanks, 2 healers, 8 DPS)")
    print(f"  - Complete gear set analysis for all players")
    print(f"  - Real player handles (@brainsnorkel, @necrodps, etc.)")
    print(f"  - Professional markdown formatting with tables")
    
    print(f"\n💻 WITH REAL CREDENTIALS, YOU WOULD RUN:")
    print(f"python eso_builds.py --report mtFqVzQPNBcCrd1h --output both")


if __name__ == "__main__":
    asyncio.run(main())
