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
        """Get top rankings for a specific trial."""
        logger.info(f"Getting top {limit} rankings for zone {zone_id}")
        
        try:
            # Get reports for this zone, sorted by performance
            reports_response = await self._make_request(
                "get_reports", 
                zone_id=zone_id,
                limit=limit * 2,  # Get more than we need in case some aren't suitable
                page=1
            )
            
            if not reports_response:
                logger.warning(f"No reports found for zone {zone_id}")
                return []
            
            rankings = []
            rank = 1
            
            # Process reports to create rankings
            for report_data in reports_response[:limit]:
                if hasattr(report_data, 'code') and hasattr(report_data, 'fights'):
                    # Calculate a simple score based on successful kills
                    successful_fights = [f for f in report_data.fights if getattr(f, 'kill', False)]
                    score = len(successful_fights) * 100.0  # Simple scoring for now
                    
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
                    rank += 1
                    
                    if len(rankings) >= limit:
                        break
            
            logger.info(f"Found {len(rankings)} rankings for zone {zone_id}")
            return rankings
            
        except Exception as e:
            logger.error(f"Failed to get rankings for zone {zone_id}: {e}")
            raise ESOLogsAPIError(f"Failed to get trial rankings: {e}")
    
    async def get_encounter_details(self, report_code: str) -> List[EncounterResult]:
        """Get detailed encounter information from a report."""
        logger.info(f"Getting encounter details for report {report_code}")
        
        try:
            # Get the full report data
            report = await self._make_request("get_report_by_code", code=report_code)
            
            if not report or not hasattr(report, 'fights'):
                logger.warning(f"No fight data found for report {report_code}")
                return []
            
            encounters = []
            
            for fight in report.fights:
                if not getattr(fight, 'kill', False):
                    continue  # Skip failed attempts
                
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
                
                # Get player details for this fight
                players = await self._get_fight_players(report_code, fight.id)
                encounter.players = players
                
                encounters.append(encounter)
                logger.debug(f"Processed encounter: {encounter.encounter_name} with {len(players)} players")
            
            logger.info(f"Extracted {len(encounters)} encounters from report {report_code}")
            return encounters
            
        except Exception as e:
            logger.error(f"Failed to get encounter details for {report_code}: {e}")
            raise ESOLogsAPIError(f"Failed to extract encounter details: {e}")
    
    async def _get_fight_players(self, report_code: str, fight_id: int) -> List[PlayerBuild]:
        """Get player builds for a specific fight."""
        try:
            # Get fight table data to see players
            table_data = await self._make_request(
                "get_report_table",
                code=report_code,
                fight_ids=[fight_id],
                data_type="Summary",
                hostility_type="Friendlies"
            )
            
            players = []
            
            if table_data and hasattr(table_data, 'data') and hasattr(table_data.data, 'entries'):
                for entry in table_data.data.entries:
                    if hasattr(entry, 'name') and hasattr(entry, 'type'):
                        # Determine role based on type/spec
                        role = self._determine_role(entry)
                        
                        # Get class name
                        character_class = getattr(entry, 'type', 'Unknown')
                        
                        player = PlayerBuild(
                            name=entry.name,
                            character_class=character_class,
                            role=role,
                            gear_sets=[]  # TODO: Implement gear extraction
                        )
                        players.append(player)
            
            logger.debug(f"Found {len(players)} players for fight {fight_id}")
            return players
            
        except Exception as e:
            logger.error(f"Failed to get players for fight {fight_id}: {e}")
            return []
    
    def _determine_role(self, player_entry) -> Role:
        """Determine player role from entry data."""
        # This is a simplified role detection - in reality we'd need more sophisticated logic
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
        
        # Default fallback
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
