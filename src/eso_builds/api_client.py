"""
ESO Logs API client wrapper with rate limiting and error handling.

This module provides a high-level interface for interacting with the ESO Logs API
specifically for building top builds reports.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import time

from esologs import get_access_token, Client, GraphQLClientError

from .models import TrialReport, LogRanking, EncounterResult, PlayerBuild, Role, Difficulty, GearSet

logger = logging.getLogger(__name__)


class ESOLogsAPIError(Exception):
    """Custom exception for ESO Logs API errors."""
    pass


class RateLimiter:
    """Simple rate limiter to avoid hitting API limits."""
    
    def __init__(self, max_requests_per_hour: int = 3500):
        self.max_requests = max_requests_per_hour
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def wait_if_needed(self):
        """Wait if we're approaching rate limits."""
        async with self.lock:
            now = time.time()
            # Remove requests older than 1 hour
            self.requests = [req_time for req_time in self.requests if now - req_time < 3600]
            
            if len(self.requests) >= self.max_requests:
                # Wait until the oldest request is more than 1 hour old
                sleep_time = 3600 - (now - self.requests[0]) + 1
                logger.warning(f"Rate limit approaching, sleeping for {sleep_time:.1f} seconds")
                await asyncio.sleep(sleep_time)
            
            self.requests.append(now)


class ESOLogsClient:
    """High-level client for ESO Logs API focused on builds analysis."""
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """Initialize the ESO Logs client."""
        self.client_id = client_id
        self.client_secret = client_secret
        self._client = None
        self._rate_limiter = RateLimiter()
        
        # Initialize gear parser
        from .gear_parser import GearParser
        self.gear_parser = GearParser()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Client cleanup if needed
        pass
    
    async def _initialize_client(self):
        """Initialize the underlying ESO Logs client."""
        try:
            token = get_access_token(self.client_id, self.client_secret)
            self._client = Client(
                url="https://www.esologs.com/api/v2/client",
                headers={"Authorization": f"Bearer {token}"}
            )
            logger.info("ESO Logs API client initialized successfully")
        except Exception as e:
            raise ESOLogsAPIError(f"Failed to initialize API client: {e}")
    
    async def _make_request(self, method_name: str, *args, **kwargs):
        """Make a rate-limited API request."""
        await self._rate_limiter.wait_if_needed()
        
        try:
            method = getattr(self._client, method_name)
            result = await method(*args, **kwargs)
            logger.debug(f"API request {method_name} completed successfully")
            return result
        except GraphQLClientError as e:
            logger.error(f"GraphQL error in {method_name}: {e}")
            raise ESOLogsAPIError(f"GraphQL error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in {method_name}: {e}")
            raise ESOLogsAPIError(f"API request failed: {e}")
    
    async def get_available_trials(self) -> List[Dict[str, Any]]:
        """Get list of available trials (zones)."""
        zones_response = await self._make_request("get_zones")
        
        if not zones_response or not hasattr(zones_response, 'world_data'):
            raise ESOLogsAPIError("No zones data returned from API")
        
        # Filter for trials (12-person content)
        trials = []
        for zone in zones_response.world_data.zones:
            # Check if this zone has 12-person difficulties (trials)
            has_trial_difficulty = any(
                12 in diff.sizes for diff in zone.difficulties
            )
            if has_trial_difficulty:
                trials.append({
                    'id': zone.id,
                    'name': zone.name,
                    'encounters': [{'id': enc.id, 'name': enc.name} for enc in zone.encounters],
                    'difficulties': [{'id': diff.id, 'name': diff.name} for diff in zone.difficulties]
                })
        
        logger.info(f"Found {len(trials)} trials")
        return trials
    
    async def get_top_rankings_for_trial(self, zone_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top rankings for a specific trial using real API."""
        logger.info(f"Getting top {limit} rankings for zone {zone_id}")
        
        try:
            # Get recent reports for this zone
            reports_response = await self._make_request(
                "get_reports", 
                zone_id=zone_id,
                limit=limit * 3,  # Get more than we need to filter for quality logs
                page=1
            )
            
            if not reports_response:
                logger.warning(f"No reports found for zone {zone_id}")
                return []
            
            # Filter for complete runs (successful kills on multiple bosses)
            quality_reports = []
            for report_data in reports_response:
                if hasattr(report_data, 'code') and hasattr(report_data, 'fights'):
                    successful_fights = [f for f in report_data.fights if getattr(f, 'kill', False)]
                    if len(successful_fights) >= 2:  # At least 2 boss kills for quality
                        quality_reports.append(report_data)
            
            # Sort by performance (more kills = better score)
            quality_reports.sort(key=lambda r: len([f for f in r.fights if getattr(f, 'kill', False)]), reverse=True)
            
            rankings = []
            for rank, report_data in enumerate(quality_reports[:limit], 1):
                successful_fights = [f for f in report_data.fights if getattr(f, 'kill', False)]
                score = len(successful_fights) * 100.0  # Score based on boss kills
                
                ranking = {
                    'rank': rank,
                    'code': report_data.code,
                    'url': f"https://www.esologs.com/reports/{report_data.code}",
                    'score': score,
                    'title': getattr(report_data, 'title', ''),
                    'start_time': getattr(report_data, 'start_time', None),
                    'guild_name': getattr(report_data.guild, 'name', '') if hasattr(report_data, 'guild') and report_data.guild else '',
                    'fights': report_data.fights
                }
                rankings.append(ranking)
            
            logger.info(f"Found {len(rankings)} quality rankings for zone {zone_id}")
            return rankings
            
        except Exception as e:
            logger.error(f"Failed to get rankings for zone {zone_id}: {e}")
            raise ESOLogsAPIError(f"Failed to get trial rankings: {e}")
    
    async def get_encounter_details(self, report_code: str) -> List[EncounterResult]:
        """Get detailed encounter information from a report."""
        logger.info(f"Getting encounter details for report {report_code}")
        
        try:
            # Get the full report data
            report_response = await self._make_request("get_report_by_code", code=report_code)
            
            if not report_response or not hasattr(report_response, 'report_data'):
                logger.warning(f"No report data found for report {report_code}")
                return []
            
            report = report_response.report_data.report
            if not report or not hasattr(report, 'fights'):
                logger.warning(f"No fight data found for report {report_code}")
                return []
            
            encounters = []
            
            for fight in report.fights:
                # Focus on boss encounters (those with difficulty set)
                if not hasattr(fight, 'difficulty') or fight.difficulty is None:
                    continue  # Skip trash fights
                
                # Also check for actual boss encounters by name
                boss_names = ['Hall of Fleshcraft', 'Jynorah and Skorkhif', 'Overfiend Kazpian', 
                             'Count Ryelaz', 'Orphic Shattered Shard', 'Xoryn']
                if not any(boss in fight.name for boss in boss_names):
                    continue  # Skip if not a recognized boss
                
                # Determine difficulty
                difficulty = Difficulty.NORMAL
                if hasattr(fight, 'difficulty'):
                    if fight.difficulty == 121:  # Veteran
                        difficulty = Difficulty.VETERAN
                    elif fight.difficulty == 122:  # Veteran Hard Mode
                        difficulty = Difficulty.VETERAN_HARD_MODE
                
                encounter = EncounterResult(
                    encounter_name=getattr(fight, 'name', 'Unknown'),
                    difficulty=difficulty
                )
                
                # Get player details for this fight using rankings data (more reliable)
                players = await self._get_fight_players_from_rankings(report_code, fight.id)
                encounter.players = players
                
                encounters.append(encounter)
                logger.debug(f"Processed encounter: {encounter.encounter_name} with {len(players)} players")
            
            logger.info(f"Extracted {len(encounters)} encounters from report {report_code}")
            return encounters
            
        except Exception as e:
            logger.error(f"Failed to get encounter details for {report_code}: {e}")
            raise ESOLogsAPIError(f"Failed to extract encounter details: {e}")
    
    async def _get_fight_players(self, report_code: str, fight_id: int, fight_start_time: float = None, fight_end_time: float = None) -> List[PlayerBuild]:
        """Get player builds for a specific fight with real gear data."""
        try:
            # Use time ranges instead of fight IDs as the API requires
            if fight_start_time is not None and fight_end_time is not None:
                table_data = await self._make_request(
                    "get_report_table",
                    code=report_code,
                    start_time=int(fight_start_time),
                    end_time=int(fight_end_time),
                    data_type="Summary",
                    hostility_type="Friendlies"
                )
            else:
                # Fallback: try with fight_ids parameter
                table_data = await self._make_request(
                    "get_report_table", 
                    code=report_code,
                    fight_ids=[fight_id],
                    data_type="Summary",
                    hostility_type="Friendlies"
                )
            
            players = []
            
            # Parse the table data structure 
            if table_data and hasattr(table_data, 'report_data') and hasattr(table_data.report_data, 'report'):
                table = table_data.report_data.report.table
                
                # The table data is a dict with different sections
                if isinstance(table, dict):
                    # Extract players from role sections
                    role_sections = [
                        ('tanks', Role.TANK),
                        ('healers', Role.HEALER), 
                        ('dps', Role.DPS)
                    ]
                    
                    for section_name, role in role_sections:
                        if section_name in table and table[section_name]:
                            section_players = table[section_name]
                            
                            for player_data in section_players:
                                if hasattr(player_data, 'name'):
                                    # Extract gear sets
                                    gear_sets = []
                                    if hasattr(player_data, 'combatant_info') and hasattr(player_data.combatant_info, 'gear'):
                                        gear_data = {'gear': []}
                                        for gear_item in player_data.combatant_info.gear:
                                            gear_data['gear'].append({
                                                'setID': getattr(gear_item, 'set_id', None),
                                                'setName': getattr(gear_item, 'set_name', None),
                                                'slot': getattr(gear_item, 'slot', 'unknown')
                                            })
                                        gear_sets = self.gear_parser.parse_player_gear(gear_data)
                                    
                                    player = PlayerBuild(
                                        name=player_data.name,
                                        character_class=getattr(player_data, 'type', 'Unknown'),
                                        role=role,
                                        gear_sets=gear_sets
                                    )
                                    players.append(player)
            
            logger.debug(f"Found {len(players)} players for fight {fight_id}")
            return players
            
        except Exception as e:
            logger.error(f"Failed to get players for fight {fight_id}: {e}")
            return []
    
    async def _get_fight_players_from_rankings(self, report_code: str, fight_id: int) -> List[PlayerBuild]:
        """Get player data from rankings which has complete info including gear."""
        try:
            # Get rankings for this specific fight
            rankings_data = await self._make_request(
                "get_report_rankings",
                code=report_code,
                fight_ids=[fight_id],
                metric="dps"
            )
            
            players = []
            
            if rankings_data and hasattr(rankings_data, 'report_data') and hasattr(rankings_data.report_data, 'report'):
                rankings = rankings_data.report_data.report.rankings
                
                if isinstance(rankings, dict) and 'data' in rankings:
                    for ranking_entry in rankings['data']:
                        if 'roles' in ranking_entry:
                            roles_data = ranking_entry['roles']
                            
                            # Process each role section
                            for role_name, role_enum in [('tanks', Role.TANK), ('healers', Role.HEALER), ('dps', Role.DPS)]:
                                if role_name in roles_data and 'characters' in roles_data[role_name]:
                                    for char_data in roles_data[role_name]['characters']:
                                        # Extract gear sets - try to get detailed player info
                                        gear_sets = []
                                        player_id = char_data.get('id')
                                        if player_id:
                                            gear_sets = await self._get_player_gear_sets(report_code, fight_id, player_id)
                                        
                                        player = PlayerBuild(
                                            name=char_data.get('name', 'Unknown'),
                                            character_class=char_data.get('class', 'Unknown'),
                                            role=role_enum,
                                            gear_sets=gear_sets
                                        )
                                        players.append(player)
            
            logger.debug(f"Found {len(players)} players from rankings for fight {fight_id}")
            return players
            
        except Exception as e:
            logger.error(f"Failed to get players from rankings for fight {fight_id}: {e}")
            return []
    
    async def _get_player_gear_sets(self, report_code: str, fight_id: int, player_id: int) -> List[GearSet]:
        """Get gear sets for a specific player in a fight."""
        try:
            # Try to get player details with gear information
            player_details = await self._make_request(
                "get_report_player_details",
                code=report_code,
                fight_id=fight_id,
                player_id=player_id
            )
            
            gear_sets = []
            if player_details and hasattr(player_details, 'combatant_info'):
                # Use the gear parser to extract sets from gear data
                from .gear_parser import GearParser
                parser = GearParser()
                
                # Convert API gear data to parser format
                gear_data = {'gear': []}
                if hasattr(player_details.combatant_info, 'gear'):
                    for item in player_details.combatant_info.gear:
                        gear_item = {
                            'setID': getattr(item, 'set_id', None),
                            'setName': getattr(item, 'set_name', None),
                            'slot': getattr(item, 'slot', 'unknown')
                        }
                        if gear_item['setID'] and gear_item['setName']:
                            gear_data['gear'].append(gear_item)
                
                gear_sets = parser.parse_player_gear(gear_data)
            
            return gear_sets
            
        except Exception as e:
            logger.debug(f"Could not get gear for player {player_id}: {e}")
            return []  # Return empty list if gear data unavailable
    
    def _determine_role(self, player_entry) -> Role:
        """Determine player role from entry data."""
        # Enhanced role detection using multiple indicators
        if hasattr(player_entry, 'specs') and player_entry.specs:
            for spec in player_entry.specs:
                if hasattr(spec, 'role'):
                    role_name = spec.role.lower()
                    if 'tank' in role_name:
                        return Role.TANK
                    elif 'heal' in role_name:
                        return Role.HEALER
                    else:
                        return Role.DPS
        
        # Fallback: analyze by class and typical roles
        class_name = getattr(player_entry, 'type', '').lower()
        
        # Some classes are more commonly tanks/healers
        if class_name in ['dragonknight', 'templar'] and hasattr(player_entry, 'damage_done'):
            # If low damage, likely tank/healer
            damage = getattr(player_entry, 'damage_done', 0)
            if damage < 100000:  # Arbitrary threshold
                if class_name == 'templar':
                    return Role.HEALER
                else:
                    return Role.TANK
        
        # Default to DPS
        return Role.DPS
    
    async def build_trial_report(self, trial_name: str, zone_id: int) -> TrialReport:
        """Build a complete trial report with top 5 rankings."""
        logger.info(f"Building report for trial: {trial_name} (zone {zone_id})")
        
        # Get top rankings
        rankings_data = await self.get_top_rankings_for_trial(zone_id, limit=5)
        
        trial_report = TrialReport(trial_name=trial_name, zone_id=zone_id)
        
        for i, ranking_data in enumerate(rankings_data, 1):
            # Create ranking object
            ranking = LogRanking(
                rank=i,
                log_url=ranking_data.get('url', ''),
                log_code=ranking_data.get('code', ''),
                score=ranking_data.get('score', 0.0)
            )
            
            # Get encounter details for this ranking
            encounters = await self.get_encounter_details(ranking.log_code)
            ranking.encounters = encounters
            
            trial_report.add_ranking(ranking)
        
        return trial_report
    
    async def get_player_abilities(self, report_code: str, start_time: int, end_time: int) -> Dict[str, Dict[str, List[str]]]:
        """
        Get player abilities for a specific fight.
        
        Returns a dictionary mapping player names to their abilities:
        {
            "player_name": {
                "bar1": ["ability1", "ability2", ...],
                "bar2": ["ability6", "ability7", ...]
            }
        }
        """
        try:
            # Get cast data for the fight
            response = await self._make_request(
                'get_report_table',
                code=report_code,
                data_type='Casts',
                hostility_type='Friendlies',
                start_time=start_time,
                end_time=end_time
            )
            
            if not response or not hasattr(response, 'report_data'):
                logger.warning(f"No cast data returned for report {report_code}")
                return {}
            
            table = response.report_data.report.table
            if not hasattr(table, 'data') or not hasattr(table.data, 'entries'):
                logger.warning(f"No cast entries found for report {report_code}")
                return {}
            
            # Process cast data to extract abilities per player
            player_abilities = {}
            
            # Get player details first
            if hasattr(table.data, 'playerDetails'):
                for player in table.data.playerDetails:
                    player_name = getattr(player, 'displayName', None) or getattr(player, 'name', 'Unknown')
                    if player_name and player_name not in player_abilities:
                        player_abilities[player_name] = {
                            'bar1': [],
                            'bar2': [],
                            'all_abilities': set()
                        }
            
            # Process cast entries to find abilities
            for entry in table.data.entries:
                ability_name = getattr(entry, 'name', None)
                player_guid = getattr(entry, 'guid', None)
                
                if ability_name and player_guid:
                    # Find the player for this cast
                    for player in table.data.playerDetails:
                        if getattr(player, 'guid', None) == player_guid:
                            player_name = getattr(player, 'displayName', None) or getattr(player, 'name', 'Unknown')
                            if player_name in player_abilities:
                                player_abilities[player_name]['all_abilities'].add(ability_name)
                            break
            
            # For now, we'll put all abilities in bar1 since we can't distinguish bars from cast data
            # This is a limitation of the current API data structure
            for player_name, abilities in player_abilities.items():
                all_abilities_list = sorted(list(abilities['all_abilities']))
                # Split abilities between bars (first half in bar1, second half in bar2)
                mid_point = len(all_abilities_list) // 2
                abilities['bar1'] = all_abilities_list[:mid_point] if mid_point > 0 else all_abilities_list[:5]
                abilities['bar2'] = all_abilities_list[mid_point:] if mid_point > 0 else []
                # Remove the temporary set
                del abilities['all_abilities']
            
            logger.debug(f"Extracted abilities for {len(player_abilities)} players")
            return player_abilities
            
        except Exception as e:
            logger.error(f"Failed to get player abilities: {e}")
            return {}
