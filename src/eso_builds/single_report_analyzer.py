"""
Focused single report analyzer for ESO Logs.

This module provides a simplified, reliable approach to analyzing
individual ESO Logs reports with real player data extraction.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import TrialReport, LogRanking, EncounterResult, PlayerBuild, Role, Difficulty, GearSet
from .api_client import ESOLogsClient, ESOLogsAPIError
from .gear_parser import GearParser

logger = logging.getLogger(__name__)


class SingleReportAnalyzer:
    """Simplified analyzer focused on single report analysis."""
    
    def __init__(self):
        """Initialize the analyzer."""
        self.gear_parser = GearParser()
    
    async def analyze_report(self, report_code: str) -> TrialReport:
        """Analyze a single ESO Logs report and extract all encounter data."""
        logger.info(f"Analyzing single report: {report_code}")
        
        async with ESOLogsClient() as client:
            # Get basic report info
            report_info = await self._get_report_info(client, report_code)
            
            # Get encounters with player data
            encounters = await self._extract_encounters_with_players(client, report_code, report_info)
            
            # Create trial report structure
            ranking = LogRanking(
                rank=1,
                log_url=f"https://www.esologs.com/reports/{report_code}",
                log_code=report_code,
                score=len(encounters) * 100.0,  # Score based on encounters found
                encounters=encounters,
                guild_name=report_info.get('guild_name', ''),
                date=datetime.fromtimestamp(report_info.get('start_time', 0) / 1000) if report_info.get('start_time') else datetime.now()
            )
            
            # Use the actual report title from the API
            report_title = report_info.get('title', f'Report {report_code}')
            
            trial_report = TrialReport(
                trial_name=report_title,
                zone_id=report_info.get('zone_id', 0),
                rankings=[ranking]
            )
            
            return trial_report
    
    async def _get_report_info(self, client: ESOLogsClient, report_code: str) -> Dict[str, Any]:
        """Get basic report information."""
        try:
            report_response = await client._make_request("get_report_by_code", code=report_code)
            
            if not report_response or not hasattr(report_response, 'report_data'):
                raise ESOLogsAPIError(f"No report data found for {report_code}")
            
            report = report_response.report_data.report
            
            return {
                'title': getattr(report, 'title', 'Unknown'),
                'zone_name': getattr(report.zone, 'name', 'Unknown') if hasattr(report, 'zone') else 'Unknown',
                'zone_id': getattr(report.zone, 'id', 0) if hasattr(report, 'zone') else 0,
                'start_time': getattr(report, 'start_time', None),
                'end_time': getattr(report, 'end_time', None),
                'fights': report.fights if hasattr(report, 'fights') else []
            }
            
        except Exception as e:
            logger.error(f"Failed to get report info: {e}")
            raise ESOLogsAPIError(f"Could not retrieve report {report_code}: {e}")
    
    async def _get_detailed_fight_data(self, client: ESOLogsClient, report_code: str) -> List:
        """Get detailed fight data with kill/percentage information."""
        try:
            # Custom GraphQL query for detailed fight data
            query = """
            query GetDetailedFights($code: String!) {
              reportData {
                report(code: $code) {
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
                  }
                }
              }
            }
            """
            
            # Execute the query
            http_response = await client._client.execute(query, variables={'code': report_code})
            
            if http_response.status_code != 200:
                logger.error(f"HTTP error {http_response.status_code}: {http_response.text}")
                return []
            
            response_data = http_response.json()
            
            if 'errors' in response_data:
                logger.error(f"GraphQL errors: {response_data['errors']}")
                return []
            
            # Extract fight data
            if ('data' in response_data and 
                'reportData' in response_data['data'] and 
                response_data['data']['reportData'] and
                'report' in response_data['data']['reportData'] and
                response_data['data']['reportData']['report'] and
                'fights' in response_data['data']['reportData']['report']):
                
                fights_data = response_data['data']['reportData']['report']['fights']
                
                # Convert to fight objects with proper field names
                class DetailedFight:
                    def __init__(self, fight_dict):
                        self.id = fight_dict['id']
                        self.name = fight_dict['name']
                        self.start_time = fight_dict['startTime']
                        self.end_time = fight_dict['endTime']
                        self.difficulty = fight_dict.get('difficulty')
                        self.kill = fight_dict.get('kill', False)
                        self.boss_percentage = fight_dict.get('bossPercentage', 0.0)
                        self.fight_percentage = fight_dict.get('fightPercentage', 0.0)
                        self.encounter_id = fight_dict.get('encounterID', 0)
                        self.size = fight_dict.get('size', 12)
                
                fights = [DetailedFight(fight_dict) for fight_dict in fights_data]
                logger.info(f"Retrieved detailed data for {len(fights)} fights")
                return fights
            else:
                logger.warning("No fight data found in detailed query response")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get detailed fight data: {e}")
            return []
    
    async def _extract_encounters_with_players(self, client: ESOLogsClient, report_code: str, report_info: Dict) -> List[EncounterResult]:
        """Extract encounters with real player data using the table approach."""
        encounters = []
        
        # Get detailed fight data with kill/percentage information
        detailed_fights = await self._get_detailed_fight_data(client, report_code)
        
        # Focus on boss encounters - automatically detect by difficulty field
        boss_fights = []
        for fight in detailed_fights:
            # Boss encounters have a difficulty value (120=Normal, 121=Veteran, 122=Veteran HM)
            # Trash fights and non-boss encounters typically have difficulty=None
            if hasattr(fight, 'difficulty') and fight.difficulty is not None:
                # Additional filters to exclude non-boss encounters that might have difficulty
                fight_name = fight.name.lower()
                
                # Skip obvious trash/add fights
                skip_keywords = [
                    'unknown', 'trash', 'add', 'acolyte', 'atronach', 'lurker', 
                    'slasher', 'iridescent', 'sandroach', 'mirrorworm'
                ]
                
                # Skip if fight name contains obvious trash indicators
                if any(keyword in fight_name for keyword in skip_keywords):
                    continue
                
                # Skip very short fights (likely trash) - less than 30 seconds
                fight_duration = getattr(fight, 'end_time', 0) - getattr(fight, 'start_time', 0)
                if fight_duration < 30000:  # 30 seconds in milliseconds
                    continue
                
                boss_fights.append(fight)
                logger.info(f"🎯 Detected boss encounter: {fight.name} (difficulty: {fight.difficulty})")
        
        logger.info(f"Found {len(boss_fights)} boss encounters to analyze")
        
        for fight in boss_fights:
            try:
                # Get player data using table method with time ranges
                players = await self._get_players_simple(client, report_code, fight)
                
                # Determine difficulty
                difficulty = Difficulty.NORMAL
                if fight.difficulty == 121:
                    difficulty = Difficulty.VETERAN
                elif fight.difficulty == 122:
                    difficulty = Difficulty.VETERAN_HARD_MODE
                
                # Get kill status and boss percentage
                kill_status = getattr(fight, 'kill', False)
                boss_percentage = getattr(fight, 'boss_percentage', 0.0)
                
                # Get buff/debuff uptimes for this fight (tries table API first, falls back to events)
                start_time = int(getattr(fight, 'start_time', 0))
                end_time = int(getattr(fight, 'end_time', start_time + 300000))
                buff_uptimes = await client.get_buff_debuff_uptimes(
                    report_code, start_time, end_time
                )
                
                encounter = EncounterResult(
                    encounter_name=fight.name,
                    difficulty=difficulty,
                    players=players,
                    kill=kill_status,
                    boss_percentage=boss_percentage,
                    buff_uptimes=buff_uptimes
                )
                
                encounters.append(encounter)
                logger.info(f"Processed {fight.name}: {len(players)} players")
                
            except Exception as e:
                logger.error(f"Failed to process fight {fight.name}: {e}")
                continue
        
        return encounters
    
    async def _get_players_simple(self, client: ESOLogsClient, report_code: str, fight) -> List[PlayerBuild]:
        """Extract real player data using the working table structure."""
        try:
            # Get table data with time ranges
            table_data = await client._make_request(
                "get_report_table",
                code=report_code,
                start_time=int(fight.start_time),
                end_time=int(fight.end_time),
                data_type="Summary",
                hostility_type="Friendlies"
            )
            
            
            players = []
            
            # Parse the correct table structure: table['data']['playerDetails']
            if table_data and hasattr(table_data, 'report_data'):
                table = table_data.report_data.report.table
                
                if isinstance(table, dict) and 'data' in table:
                    data_section = table['data']
                    
                    if 'playerDetails' in data_section:
                        player_details = data_section['playerDetails']
                        
                        # Process each role section
                        for role_name, role_enum in [('tanks', Role.TANK), ('healers', Role.HEALER), ('dps', Role.DPS)]:
                            if role_name in player_details:
                                section_players = player_details[role_name]
                                
                                for player_data in section_players:
                                    # Extract basic info
                                    name = player_data.get('name', 'Unknown')
                                    display_name = player_data.get('displayName', '')
                                    character_class = player_data.get('type', 'Unknown')
                                    
                                    # Extract gear sets
                                    gear_sets = []
                                    if 'combatantInfo' in player_data and 'gear' in player_data['combatantInfo']:
                                        gear_items = player_data['combatantInfo']['gear']
                                        
                                        # Convert to our parser format
                                        gear_data = {'gear': []}
                                        for gear_item in gear_items:
                                            if gear_item.get('setID', 0) > 0:
                                                # Include the individual item name for arena weapon detection
                                                gear_data['gear'].append({
                                                    'setID': gear_item.get('setID'),
                                                    'setName': gear_item.get('setName'),
                                                    'name': gear_item.get('name', ''),  # Add individual item name
                                                    'slot': gear_item.get('slot', 'unknown')
                                                })
                                        
                                        if gear_data['gear']:
                                            gear_sets = self.gear_parser.parse_player_gear(gear_data)
                                    
                                    # Use display name if available, otherwise character name with @
                                    if display_name and display_name.startswith('@'):
                                        final_name = display_name  # Already has @ symbol
                                    elif display_name:
                                        final_name = f"@{display_name}"  # Add @ to display name
                                    elif name and not name.startswith('@'):
                                        final_name = f"@{name}"  # Add @ to character name
                                    else:
                                        final_name = name or "@anonymous"  # Use as-is or fallback
                                    
                                    # Replace @nil with @anonymous for better readability
                                    if final_name == "@nil":
                                        final_name = "@anonymous"
                                    
                                    
                                    player = PlayerBuild(
                                        name=final_name,
                                        character_class=character_class,
                                        role=role_enum,
                                        gear_sets=gear_sets
                                    )
                                    players.append(player)
                                    
                                    logger.debug(f"Added {final_name} ({character_class}, {role_enum.value}) with {len(gear_sets)} sets")
            
            logger.info(f"Extracted {len(players)} real players for {fight.name}")
            return players
            
        except Exception as e:
            logger.error(f"Failed to get players for fight: {e}")
            return []
