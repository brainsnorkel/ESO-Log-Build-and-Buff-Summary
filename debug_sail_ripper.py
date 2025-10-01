#!/usr/bin/env python3
"""Debug script to understand Sail Ripper missing gear data."""

import asyncio
import logging
import json
import os
from dotenv import load_dotenv
from src.eso_builds.api_client import ESOLogsClient

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_fight_data():
    """Debug the Sail Ripper fight data structure."""
    client = ESOLogsClient()
    await client._initialize_client()  # Initialize the client

    report_code = "N37HBwrjQGYJ6mbv"

    # Get the fight list
    report_data = await client._make_request("get_report_by_code", code=report_code)
    fights = report_data.report_data.report.fights

    # Find Sail Ripper (fight 8) and Lylanar (fight 4)
    sail_ripper = None
    lylanar = None

    for fight in fights:
        if fight.name == "Sail Ripper":
            sail_ripper = fight
            logger.info(f"Found Sail Ripper: fight_id={fight.id}, start={fight.start_time}, end={fight.end_time}")
        elif fight.name == "Lylanar and Turlassil":
            lylanar = fight
            logger.info(f"Found Lylanar: fight_id={fight.id}, start={fight.start_time}, end={fight.end_time}")

    # Get table data for both fights
    for fight_name, fight in [("Sail Ripper", sail_ripper), ("Lylanar", lylanar)]:
        if not fight:
            continue

        logger.info(f"\n{'='*60}")
        logger.info(f"Analyzing {fight_name} (ID: {fight.id})")
        logger.info(f"{'='*60}")

        table_data = await client._make_request(
            "get_report_table",
            code=report_code,
            start_time=int(fight.start_time),
            end_time=int(fight.end_time),
            data_type="Summary",
            hostility_type="Friendlies",
            includeCombatantInfo=True
        )

        if table_data and hasattr(table_data, 'report_data'):
            data = table_data.report_data.report.table['data']

            if 'playerDetails' in data:
                player_details = data['playerDetails']

                # Check DPS section
                if 'dps' in player_details:
                    dps_players = player_details['dps']
                    logger.info(f"\nDPS players found: {len(dps_players)}")

                    for i, player in enumerate(dps_players[:2]):  # Check first 2 DPS
                        logger.info(f"\n  Player {i+1}: {player.get('name', 'unknown')}")
                        logger.info(f"    Has 'combatantInfo': {'combatantInfo' in player}")

                        if 'combatantInfo' in player:
                            combatant_info = player['combatantInfo']
                            logger.info(f"    combatantInfo type: {type(combatant_info)}")

                            if isinstance(combatant_info, dict):
                                logger.info(f"    combatantInfo keys: {list(combatant_info.keys())}")
                                if 'gear' in combatant_info:
                                    gear = combatant_info['gear']
                                    logger.info(f"    Gear items: {len(gear) if gear else 0}")
                                    if gear:
                                        logger.info(f"    First gear item: {gear[0]}")
                                else:
                                    logger.info(f"    NO 'gear' key in combatantInfo!")
                            elif isinstance(combatant_info, list):
                                logger.info(f"    ⚠️ combatantInfo is a LIST with {len(combatant_info)} items!")
                                if combatant_info:
                                    logger.info(f"    First item type: {type(combatant_info[0])}")
                                    if isinstance(combatant_info[0], dict):
                                        logger.info(f"    First item keys: {list(combatant_info[0].keys())}")
                        else:
                            logger.info(f"    Player data keys: {list(player.keys())}")

                # Check tanks
                if 'tanks' in player_details:
                    tanks = player_details['tanks']
                    logger.info(f"\nTank players found: {len(tanks)}")

                    for i, player in enumerate(tanks):
                        logger.info(f"\n  Tank {i+1}: {player.get('name', 'unknown')}")
                        logger.info(f"    Has 'combatantInfo': {'combatantInfo' in player}")
                        if 'combatantInfo' in player:
                            combatant_info = player['combatantInfo']
                            logger.info(f"    Has 'gear': {'gear' in combatant_info}")

if __name__ == "__main__":
    asyncio.run(debug_fight_data())
