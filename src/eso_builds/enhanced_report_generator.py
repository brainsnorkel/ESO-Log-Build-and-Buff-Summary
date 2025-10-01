"""
Enhanced Report Generator with API-based Action Bar Integration.

This module extends the existing report generation to include action bar data
obtained directly from the ESO Logs API using includeCombatantInfo=True.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from .api_client import ESOLogsClient
from .single_report_analyzer import SingleReportAnalyzer
from .models import TrialReport, LogRanking, EncounterResult, PlayerBuild, Role, Difficulty

logger = logging.getLogger(__name__)


class EnhancedReportGenerator:
    """
    Enhanced report generator that uses API data for both gear and action bars.
    
    This generator:
    1. Uses the ESO Logs API client to get player builds and encounter data
    2. Extracts action bars directly from API combatant info
    3. Generates comprehensive reports with both gear and ability information
    """
    
    def __init__(self):
        """
        Initialize the enhanced report generator.
        """
        self.api_client = ESOLogsClient()
        self.analyzer = SingleReportAnalyzer()
        
    async def generate_enhanced_report(self, report_code: str) -> TrialReport:
        """
        Generate an enhanced trial report with action bar data from API.
        
        Args:
            report_code: The ESO Logs report code
            
        Returns:
            TrialReport with action bar data from API
        """
        logger.info(f"Generating enhanced report for: {report_code}")
        
        # Get encounter data using existing analyzer (now includes abilities from API)
        logger.info("Fetching encounter data from API...")
        trial_report = await self.analyzer.analyze_report(report_code)
        
        if not trial_report:
            logger.warning("No report data found")
            return None
        
        logger.info(f"Generated enhanced report with {len(trial_report.rankings[0].encounters)} encounters")
        return trial_report