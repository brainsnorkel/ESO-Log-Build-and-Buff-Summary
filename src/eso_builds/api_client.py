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
            # Get the full report data with detailed fight information
            query = """
            query GetDetailedReport($code: String!) {
              reportData {
                report(code: $code) {
                  code
                  title
                  startTime
                  endTime
                  zone {
                    id
                    name
                  }
                  fights {
                    id
                    name
                    startTime
                    endTime
                    difficulty
                    kill
                    bossPercentage
                    fightPercentage
                    encounterID
                    size
                    averageItemLevel
                  }
                }
              }
            }
            """
            
            # Execute the custom query to get detailed fight data
            http_response = await self._client.execute(query, variables={'code': report_code})
            
            if http_response.status_code != 200:
                logger.error(f"HTTP error {http_response.status_code}: {http_response.text}")
                return []
            
            response_data = http_response.json()
            
            if 'errors' in response_data:
                logger.error(f"GraphQL errors: {response_data['errors']}")
                return []
            
            # Extract fight data from the response
            if ('data' in response_data and 
                'reportData' in response_data['data'] and 
                response_data['data']['reportData'] and
                'report' in response_data['data']['reportData'] and
                response_data['data']['reportData']['report'] and
                'fights' in response_data['data']['reportData']['report']):
                
                fights_data = response_data['data']['reportData']['report']['fights']
                
                # Convert to a format similar to the old response
                class FightData:
                    def __init__(self, fight_dict):
                        for key, value in fight_dict.items():
                            # Convert camelCase to snake_case for consistency
                            if key == 'startTime':
                                setattr(self, 'start_time', value)
                            elif key == 'endTime':
                                setattr(self, 'end_time', value)
                            elif key == 'bossPercentage':
                                setattr(self, 'boss_percentage', value)
                            elif key == 'fightPercentage':
                                setattr(self, 'fight_percentage', value)
                            elif key == 'encounterID':
                                setattr(self, 'encounter_id', value)
                            elif key == 'averageItemLevel':
                                setattr(self, 'average_item_level', value)
                            else:
                                setattr(self, key, value)
                
                # Create fight objects
                fights = [FightData(fight_dict) for fight_dict in fights_data]
                
            else:
                logger.warning(f"No fight data found in response structure")
                return []
            
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
            if not hasattr(table, 'data'):
                logger.warning(f"No table data found for report {report_code}")
                return {}
            
            # Debug: log what we got
            logger.debug(f"Table data attributes: {list(table.data.__dict__.keys()) if hasattr(table.data, '__dict__') else 'No __dict__'}")
            
            if not hasattr(table.data, 'entries'):
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

    async def get_report_master_data(self, report_code: str) -> Dict[str, Any]:
        """
        Get master data for a report including all abilities used.
        
        Returns a dictionary with:
        {
            "abilities": [{"gameID": 123, "name": "Ability Name", "icon": "...", "type": "..."}],
            "actors": [{"name": "Player Name", "id": 123, "gameID": 456, "type": "Player"}]
        }
        """
        try:
            # GraphQL query for master data
            query = """
            query GetReportMasterData($code: String!) {
              reportData {
                report(code: $code) {
                  masterData {
                    abilities {
                      gameID
                      name
                      icon
                      type
                    }
                    actors(type: "Player") {
                      name
                      id
                      gameID
                      type
                      subType
                    }
                  }
                }
              }
            }
            """
            
            # Use the execute method to run custom GraphQL query
            # Note: execute() returns httpx.Response, need to parse JSON
            http_response = await self._client.execute(query, variables={'code': report_code})
            
            if http_response.status_code != 200:
                logger.error(f"HTTP error {http_response.status_code}: {http_response.text}")
                return {"abilities": [], "actors": []}
            
            # Parse the JSON response
            response_data = http_response.json()
            
            if not response_data:
                logger.warning(f"No response data for report {report_code}")
                return {"abilities": [], "actors": []}
            
            # Check for GraphQL errors
            if 'errors' in response_data:
                logger.error(f"GraphQL errors: {response_data['errors']}")
                return {"abilities": [], "actors": []}
            
            # Navigate the JSON response structure
            if 'data' not in response_data:
                logger.warning(f"No data in response for {report_code}")
                return {"abilities": [], "actors": []}
            
            data = response_data['data']
            if 'reportData' not in data or not data['reportData']:
                logger.warning(f"No reportData found for {report_code}")
                return {"abilities": [], "actors": []}
            
            report_data = data['reportData']
            if 'report' not in report_data or not report_data['report']:
                logger.warning(f"No report found for {report_code}")
                return {"abilities": [], "actors": []}
            
            report = report_data['report']
            if 'masterData' not in report or not report['masterData']:
                logger.warning(f"Report {report_code} does not have masterData")
                return {"abilities": [], "actors": []}
            
            master_data = report['masterData']
            if not master_data:
                logger.warning(f"No master data found for report {report_code}")
                return {"abilities": [], "actors": []}
            
            # Extract abilities from JSON
            abilities = []
            if 'abilities' in master_data and master_data['abilities']:
                for ability in master_data['abilities']:
                    abilities.append({
                        'gameID': ability.get('gameID'),
                        'name': ability.get('name', 'Unknown'),
                        'icon': ability.get('icon'),
                        'type': ability.get('type')
                    })
            
            # Extract actors (players) from JSON
            actors = []
            if 'actors' in master_data and master_data['actors']:
                for actor in master_data['actors']:
                    actors.append({
                        'name': actor.get('name', 'Unknown'),
                        'id': actor.get('id'),
                        'gameID': actor.get('gameID'),
                        'type': actor.get('type'),
                        'subType': actor.get('subType')
                    })
            
            logger.info(f"Retrieved master data: {len(abilities)} abilities, {len(actors)} players")
            return {"abilities": abilities, "actors": actors}
                
        except Exception as e:
            logger.error(f"Failed to get master data: {e}")
            return {"abilities": [], "actors": []}

    async def get_buff_debuff_uptimes_table(self, report_code: str, start_time: int, end_time: int) -> Dict[str, float]:
        """
        Get buff/debuff uptimes using the table API method.
        
        Special handling:
        - Major Vulnerability: Finds all sources and uses the highest percentage
        - Off Balance: Aggregates all variations into a single value
        
        Returns a dictionary mapping buff/debuff names to their uptime percentages.
        """
        try:
            from esologs import TableDataType
            
            uptimes = {}
            
            # Get buff data using table API
            buff_table = await self._client.get_report_table(
                code=report_code,
                data_type=TableDataType.Buffs,
                start_time=float(start_time),
                end_time=float(end_time),
                hostility_type='Friendlies'
            )
            
            # Get debuff data using table API (debuffs are applied TO enemies)
            debuff_table = await self._client.get_report_table(
                code=report_code,
                data_type=TableDataType.Debuffs,
                start_time=float(start_time),
                end_time=float(end_time),
                hostility_type='Enemies'
            )
            
            # Target buff/debuff names we want to track
            target_buffs = [
                'Major Courage', 'Major Slayer', 'Major Berserk', 'Major Force', 
                'Minor Toughness', 'Major Resolve', 'Pillager\'s Profit', 'Powerful Assault'
            ]
            target_debuffs = [
                'Major Breach', 'Major Vulnerability', 'Minor Brittle', 'Stagger', 
                'Crusher', 'Off Balance', 'Weakening'
            ]
            
            # Off Balance variations to aggregate
            off_balance_variations = ['Off Balance', 'off-balance', 'offbalance', 'Off-Balance', 'OffBalance']
            
            # Major Vulnerability variations/sources to find highest %
            major_vulnerability_variations = ['Major Vulnerability', 'major-vulnerability', 'majorvulnerability', 'Major-Vulnerability', 'MajorVulnerability']
            
            # Process buff table data
            if (buff_table and hasattr(buff_table, 'report_data') and 
                buff_table.report_data and hasattr(buff_table.report_data, 'report') and
                buff_table.report_data.report and hasattr(buff_table.report_data.report, 'table')):
                
                table_data = buff_table.report_data.report.table
                if isinstance(table_data, dict) and 'data' in table_data:
                    data = table_data['data']
                    if 'auras' in data and 'totalTime' in data:
                        auras = data['auras']
                        total_time = data['totalTime']
                        
                        for aura in auras:
                            if isinstance(aura, dict) and 'name' in aura:
                                aura_name = aura['name']
                                if aura_name in target_buffs and 'totalUptime' in aura:
                                    uptime_ms = aura['totalUptime']
                                    uptime_percent = (uptime_ms / total_time) * 100 if total_time > 0 else 0
                                    uptimes[aura_name] = uptime_percent
            
            # Process debuff table data
            if (debuff_table and hasattr(debuff_table, 'report_data') and 
                debuff_table.report_data and hasattr(debuff_table.report_data, 'report') and
                debuff_table.report_data.report and hasattr(debuff_table.report_data.report, 'table')):
                
                table_data = debuff_table.report_data.report.table
                if isinstance(table_data, dict) and 'data' in table_data:
                    data = table_data['data']
                    if 'auras' in data and 'totalTime' in data:
                        auras = data['auras']
                        total_time = data['totalTime']
                        
                        for aura in auras:
                            if isinstance(aura, dict) and 'name' in aura:
                                aura_name = aura['name']
                                
                                # Special handling for Major Vulnerability - find all sources and use highest %
                                if aura_name in major_vulnerability_variations and 'totalUptime' in aura:
                                    uptime_ms = aura['totalUptime']
                                    uptime_percent = (uptime_ms / total_time) * 100 if total_time > 0 else 0
                                    if 'Major Vulnerability' in uptimes:
                                        # Keep the highest percentage
                                        uptimes['Major Vulnerability'] = max(uptimes['Major Vulnerability'], uptime_percent)
                                    else:
                                        uptimes['Major Vulnerability'] = uptime_percent
                                    logger.debug(f"Found Major Vulnerability source '{aura_name}': {uptime_percent:.1f}%")
                                
                                # Check for exact matches of other debuffs
                                elif aura_name in target_debuffs and 'totalUptime' in aura:
                                    uptime_ms = aura['totalUptime']
                                    uptime_percent = (uptime_ms / total_time) * 100 if total_time > 0 else 0
                                    uptimes[aura_name] = uptime_percent
                                
                                # Special handling for Off Balance variations
                                elif aura_name in off_balance_variations and 'totalUptime' in aura:
                                    uptime_ms = aura['totalUptime']
                                    uptime_percent = (uptime_ms / total_time) * 100 if total_time > 0 else 0
                                    # Aggregate all variations under 'Off Balance'
                                    if 'Off Balance' in uptimes:
                                        uptimes['Off Balance'] += uptime_percent
                                    else:
                                        uptimes['Off Balance'] = uptime_percent
                                    logger.debug(f"Found Off Balance variation '{aura_name}': {uptime_percent:.1f}%")
            
            logger.info(f"Retrieved {len(uptimes)} buff/debuff uptimes using table API")
            return uptimes
            
        except Exception as e:
            logger.error(f"Failed to get buff/debuff uptimes using table API: {e}")
            return {}

    async def get_buff_debuff_uptimes_graph(self, report_code: str, start_time: int, end_time: int) -> Dict[str, float]:
        """
        Get buff/debuff uptimes using the graph API method.
        
        Returns a dictionary mapping buff/debuff names to their uptime percentages.
        """
        try:
            from esologs import GraphDataType
            
            uptimes = {}
            
            # Get buff data using graph API
            buff_graph = await self._client.get_report_graph(
                code=report_code,
                data_type=GraphDataType.Buffs,
                start_time=float(start_time),
                end_time=float(end_time),
                hostility_type='Friendlies'
            )
            
            # Get debuff data using graph API  
            debuff_graph = await self._client.get_report_graph(
                code=report_code,
                data_type=GraphDataType.Debuffs,
                start_time=float(start_time),
                end_time=float(end_time),
                hostility_type='Friendlies'
            )
            
            # Target buff/debuff names we want to track
            target_buffs = [
                'Major Courage', 'Major Slayer', 'Major Berserk', 'Major Force', 
                'Minor Toughness', 'Major Resolve', 'Major Breach', 
                'Major Vulnerability', 'Minor Brittle'
            ]
            
            # Process buff graph data
            if (buff_graph and buff_graph.report_data and buff_graph.report_data.report and 
                hasattr(buff_graph.report_data.report, 'graph') and buff_graph.report_data.report.graph):
                
                graph_data = buff_graph.report_data.report.graph
                if isinstance(graph_data, dict) and 'data' in graph_data:
                    series_data = graph_data['data'].get('series', [])
                    
                    for series in series_data:
                        if isinstance(series, dict) and 'name' in series:
                            ability_name = series['name']
                            
                            # Check if this matches any target buff
                            for target_buff in target_buffs:
                                if target_buff.lower() in ability_name.lower():
                                    # Calculate uptime from graph data
                                    if 'total' in series and 'totalTime' in graph_data['data']:
                                        total_time = graph_data['data']['totalTime']
                                        if total_time > 0:
                                            uptime_percentage = (series['total'] / total_time) * 100
                                            uptimes[target_buff] = uptime_percentage
                                            logger.info(f"Graph buff {target_buff}: {uptime_percentage:.1f}% uptime")
                                    break
            
            # Process debuff graph data
            if (debuff_graph and debuff_graph.report_data and debuff_graph.report_data.report and 
                hasattr(debuff_graph.report_data.report, 'graph') and debuff_graph.report_data.report.graph):
                
                graph_data = debuff_graph.report_data.report.graph
                if isinstance(graph_data, dict) and 'data' in graph_data:
                    series_data = graph_data['data'].get('series', [])
                    
                    for series in series_data:
                        if isinstance(series, dict) and 'name' in series:
                            ability_name = series['name']
                            
                            # Check if this matches any target debuff
                            for target_buff in target_buffs:
                                if target_buff.lower() in ability_name.lower():
                                    # Calculate uptime from graph data
                                    if 'total' in series and 'totalTime' in graph_data['data']:
                                        total_time = graph_data['data']['totalTime']
                                        if total_time > 0:
                                            uptime_percentage = (series['total'] / total_time) * 100
                                            uptimes[target_buff] = uptime_percentage
                                            logger.info(f"Graph debuff {target_buff}: {uptime_percentage:.1f}% uptime")
                                    break
            
            logger.info(f"Retrieved {len(uptimes)} buff/debuff uptimes using graph API")
            return uptimes
            
        except Exception as e:
            logger.error(f"Failed to get buff/debuff uptimes via graph API: {e}")
            # Fall back to event-based method
            return await self.get_buff_debuff_uptimes_events(report_code, start_time, end_time)

    async def get_buff_debuff_uptimes(self, report_code: str, start_time: int, end_time: int) -> Dict[str, float]:
        """
        Get buff/debuff uptimes for a specific fight.
        
        Primary method that tries table API first, falls back to events.
        """
        # Try table API first (most reliable)
        table_uptimes = await self.get_buff_debuff_uptimes_table(report_code, start_time, end_time)
        if table_uptimes:
            return table_uptimes
        
        # Fall back to events API if table fails
        return await self.get_buff_debuff_uptimes_events(report_code, start_time, end_time)

    async def get_buff_debuff_uptimes_events(self, report_code: str, start_time: int, end_time: int) -> Dict[str, float]:
        """
        Get buff/debuff uptimes for a specific fight.
        
        Returns a dictionary mapping buff/debuff names to their uptime percentages:
        {
            "Major Courage": 85.5,
            "Major Slayer": 92.1,
            "Major Breach": 78.3,
            ...
        }
        """
        try:
            # Use the execute method to run custom GraphQL query for buffs via events
            query = """
            query GetBuffDebuffUptimes($code: String!, $startTime: Float!, $endTime: Float!) {
              reportData {
                report(code: $code) {
                  events(
                    dataType: Buffs
                    hostilityType: Friendlies
                    startTime: $startTime
                    endTime: $endTime
                  ) {
                    data
                  }
                }
              }
            }
            """
            
            # Execute the query
            http_response = await self._client.execute(query, variables={
                'code': report_code,
                'startTime': float(start_time),
                'endTime': float(end_time)
            })
            
            if http_response.status_code != 200:
                logger.error(f"HTTP error {http_response.status_code}: {http_response.text}")
                return {}
            
            # Parse the JSON response
            response_data = http_response.json()
            
            if 'errors' in response_data:
                logger.error(f"GraphQL errors: {response_data['errors']}")
                return {}
            
            # Extract buff/debuff data from events
            uptimes = {}
            
            if ('data' in response_data and 
                'reportData' in response_data['data'] and 
                response_data['data']['reportData'] and
                'report' in response_data['data']['reportData'] and
                response_data['data']['reportData']['report'] and
                'events' in response_data['data']['reportData']['report']):
                
                events = response_data['data']['reportData']['report']['events']
                
                if 'data' in events and events['data']:
                    events_data = events['data']
                    
                    # Parse real buff/debuff events from the API
                    logger.info(f"Received {len(events_data) if isinstance(events_data, list) else 'unknown'} buff/debuff events")
                    
                    # Map abilityGameID to buff/debuff names we want to track
                    # These IDs are from ESO's game data - mapping common buff/debuff IDs
                    target_ability_ids = {
                        # Major Courage - various sources
                        61716: 'Major Courage',
                        123652: 'Major Courage', 
                        # Major Slayer - trial buffs
                        172621: 'Major Slayer',
                        # Major Berserk - various sources  
                        38901: 'Major Berserk',
                        # Add more mappings as we discover them
                    }
                    
                    # Calculate fight duration
                    fight_duration = end_time - start_time
                    
                    # Track active buffs/debuffs and their durations
                    buff_states = {}  # buff_name -> {active_since, total_duration}
                    
                    if isinstance(events_data, list):
                        for event in events_data:
                            if not isinstance(event, dict):
                                continue
                                
                            event_type = event.get('type', '')
                            ability_id = event.get('abilityGameID', 0)
                            timestamp = event.get('timestamp', 0)
                            
                            # Check if this ability ID matches any of our target buffs/debuffs
                            if ability_id in target_ability_ids:
                                buff_name = target_ability_ids[ability_id]
                                
                                if buff_name not in buff_states:
                                    buff_states[buff_name] = {'active_since': None, 'total_duration': 0}
                                
                                if event_type in ['applybuff', 'applydebuff']:
                                    # Buff/debuff applied
                                    if buff_states[buff_name]['active_since'] is None:
                                        buff_states[buff_name]['active_since'] = timestamp
                                        logger.debug(f"Applied {buff_name} at {timestamp}")
                                
                                elif event_type in ['removebuff', 'removedebuff']:
                                    # Buff/debuff removed
                                    if buff_states[buff_name]['active_since'] is not None:
                                        duration = timestamp - buff_states[buff_name]['active_since']
                                        buff_states[buff_name]['total_duration'] += duration
                                        buff_states[buff_name]['active_since'] = None
                                        logger.debug(f"Removed {buff_name} at {timestamp}, duration: {duration}")
                    
                    # Calculate final uptimes - account for buffs still active at fight end
                    for buff_name, state in buff_states.items():
                        if state['active_since'] is not None:
                            # Buff was still active at fight end
                            duration = end_time - state['active_since']
                            state['total_duration'] += duration
                            logger.debug(f"{buff_name} still active at fight end, added {duration} duration")
                        
                        # Calculate uptime percentage
                        if fight_duration > 0:
                            uptime_percentage = (state['total_duration'] / fight_duration) * 100
                            uptimes[buff_name] = uptime_percentage
                            logger.info(f"Calculated {buff_name}: {uptime_percentage:.1f}% uptime ({state['total_duration']}/{fight_duration})")
            
            logger.info(f"Retrieved {len(uptimes)} buff/debuff uptimes for fight")
            return uptimes
            
        except Exception as e:
            logger.error(f"Failed to get buff/debuff uptimes: {e}")
            return {}
