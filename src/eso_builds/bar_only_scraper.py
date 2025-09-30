"""
Bar-only encounter scraper for ESO Logs.

This module scrapes ability data for all players in an encounter and generates
clean bar1: and bar2: output showing only the action bar abilities.
"""

import asyncio
import json
import logging
import re
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)


class BarOnlyEncounterScraper:
    """Playwright-based scraper for bar-only encounter output."""
    
    def __init__(self, headless: bool = True):
        """
        Initialize the bar-only encounter scraper.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not installed. Install with: pip install playwright && playwright install chromium")
    
    def construct_fight_url(self, report_code: str, fight_id: int, source_id: Optional[int] = None, 
                          data_type: str = "casts") -> str:
        """
        Construct ESO Logs web URL for a specific fight and source.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            source_id: Optional source/player ID
            data_type: Type of data to view (casts, damage-done, healing, summary)
        
        Returns:
            The constructed URL
        """
        base_url = f"https://www.esologs.com/reports/{report_code}?fight={fight_id}&type={data_type}"
        if source_id:
            base_url += f"&source={source_id}"
        return base_url
    
    async def scrape_encounter_bars(self, report_code: str, fight_id: int, max_players: int = 10, timeout_per_player: int = 30) -> str:
        """
        Scrape action bars for key players in an encounter and return formatted output.
        
        Args:
            report_code: The report code
            fight_id: The fight ID
            max_players: Maximum number of players to process
            timeout_per_player: Timeout in seconds per player
        
        Returns:
            Formatted string with bar1: and bar2: for each player
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
            try:
                logger.info(f"Scraping encounter bars for report: {report_code}, fight: {fight_id}")
                
                # Get encounter summary to find all players
                summary_url = self.construct_fight_url(report_code, fight_id, None, "summary")
                logger.info(f"Loading encounter summary: {summary_url}")
                
                await page.goto(summary_url, wait_until='networkidle', timeout=60000)
                await page.wait_for_selector('body', timeout=30000)
                await asyncio.sleep(5)
                
                # Extract player information
                players = await self._extract_players_from_encounter(page)
                logger.info(f"Found {len(players)} players in encounter")
                
                # Filter to key players only
                key_players = self._filter_key_players(players)
                logger.info(f"Processing {len(key_players)} key players (max {max_players})")
                
                # Scrape bars for each key player with timeout
                output_lines = []
                output_lines.append(f"Encounter: {report_code} Fight {fight_id}")
                output_lines.append("=" * 60)
                
                processed_count = 0
                for player in key_players:
                    if processed_count >= max_players:
                        logger.info(f"Reached maximum player limit: {max_players}")
                        break
                        
                    logger.info(f"Scraping bars for player: {player['name']} (ID: {player['id']}) [{processed_count + 1}/{max_players}]")
                    
                    try:
                        # Use asyncio.wait_for to implement timeout per player
                        player_bars = await asyncio.wait_for(
                            self._scrape_player_bars(page, report_code, fight_id, player['id'], player['name']),
                            timeout=timeout_per_player
                        )
                        
                        if player_bars:
                            output_lines.append(f"\n{player['name']}")
                            output_lines.append(f"bar1: {player_bars['bar1']}")
                            output_lines.append(f"bar2: {player_bars['bar2']}")
                            logger.info(f"✅ Successfully scraped bars for {player['name']}")
                        else:
                            logger.warning(f"⚠️ No bars found for {player['name']}")
                            
                    except asyncio.TimeoutError:
                        logger.error(f"⏰ Timeout ({timeout_per_player}s) for player: {player['name']}")
                        continue
                    except Exception as e:
                        logger.error(f"❌ Error scraping {player['name']}: {e}")
                        continue
                    
                    processed_count += 1
                
                await browser.close()
                logger.info(f"Completed processing {processed_count} players")
                return "\n".join(output_lines)
                
            except Exception as e:
                logger.error(f"Encounter scraping failed: {e}")
                await browser.close()
                raise
    
    async def _extract_players_from_encounter(self, page) -> List[Dict]:
        """Extract player information from the encounter summary page."""
        players = []
        
        try:
            # Look for player elements
            player_elements = await page.query_selector_all(
                "tr[data-source], .player-row, [class*='player'], [data-player-id]"
            )
            
            logger.info(f"Found {len(player_elements)} potential player elements")
            
            for element in player_elements:
                try:
                    player_data = await self._extract_player_data_from_element(element)
                    if player_data:
                        players.append(player_data)
                except Exception as e:
                    logger.debug(f"Could not extract player data from element: {e}")
            
            # Alternative methods if no players found
            if not players:
                players = await self._extract_players_alternative_methods(page)
            
            return players
            
        except Exception as e:
            logger.error(f"Error extracting players from encounter: {e}")
            return []
    
    async def _extract_player_data_from_element(self, element) -> Optional[Dict]:
        """Extract player data from a single element."""
        try:
            # Try different attributes and selectors
            player_id = await element.get_attribute('data-source')
            if not player_id:
                player_id = await element.get_attribute('data-player-id')
            if not player_id:
                # Try to find player ID in onclick handlers
                onclick = await element.get_attribute('onclick')
                if onclick:
                    match = re.search(r'source[=:](\d+)', onclick)
                    if match:
                        player_id = match.group(1)
            
            if not player_id:
                return None
            
            # Extract player name
            player_name = await element.text_content()
            if player_name:
                player_name = player_name.strip()
            
            return {
                'id': player_id,
                'name': player_name or f"Player {player_id}"
            }
            
        except Exception as e:
            logger.debug(f"Error extracting player data: {e}")
            return None
    
    async def _extract_players_alternative_methods(self, page) -> List[Dict]:
        """Try alternative methods to extract player information."""
        players = []
        
        try:
            # Look for links that might contain player IDs
            links = await page.query_selector_all('a[href*="source="]')
            for link in links:
                href = await link.get_attribute('href')
                if href:
                    match = re.search(r'source=(\d+)', href)
                    if match:
                        player_id = match.group(1)
                        player_name = await link.text_content()
                        if player_name:
                            players.append({
                                'id': player_id,
                                'name': player_name.strip()
                            })
            
            # Look for player data in JavaScript
            page_content = await page.content()
            player_matches = re.findall(r'"name":\s*"([^"]+)",\s*"id":\s*(\d+)', page_content)
            for name, player_id in player_matches:
                if player_id not in [p['id'] for p in players]:
                    players.append({
                        'id': player_id,
                        'name': name
                    })
            
            # For testing, create some dummy players if none found
            if not players:
                logger.warning("No players found with standard methods, creating test players")
                players = [
                    {'id': '1', 'name': 'Test Player 1'},
                    {'id': '2', 'name': 'Test Player 2'},
                    {'id': '3', 'name': 'Test Player 3'},
                ]
            
            return players
            
        except Exception as e:
            logger.error(f"Error in alternative player extraction: {e}")
            return []
    
    def _filter_key_players(self, players: List[Dict]) -> List[Dict]:
        """Filter to key players only, removing pets and duplicates."""
        key_players = []
        
        for player in players:
            # Skip pets and duplicate entries
            if any(skip in player['name'].lower() for skip in [
                'twilight matriarch', 'blighted blastbones', 'blastbones'
            ]):
                continue
                
            # Skip numbered players (1, 2, 3, etc.) as they're likely duplicates
            if player['name'].strip().isdigit():
                continue
                
            # Skip anonymous players with very generic names
            if 'anonymous' in player['name'].lower() and len(player['name']) < 15:
                continue
                
            key_players.append(player)
        
        return key_players

    async def _scrape_player_bars(self, page, report_code: str, fight_id: int, 
                                player_id: str, player_name: str) -> Optional[Dict]:
        """Scrape action bars for a specific player from the summary-talents-0 table."""
        try:
            # Navigate to the player's summary page (not casts page)
            player_url = self.construct_fight_url(report_code, fight_id, player_id, "summary")
            logger.info(f"Loading player summary page: {player_url}")
            
            await page.goto(player_url, wait_until='networkidle', timeout=45000)
            await page.wait_for_selector('body', timeout=30000)
            await asyncio.sleep(3)  # Reduced wait time
            
            # Wait for the summary-talents-0 table to load
            await page.wait_for_selector('#summary-talents-0', timeout=30000)
            await asyncio.sleep(2)  # Give time for content to load
            
            # Extract abilities from the summary-talents-0 table
            abilities = await self._extract_abilities_from_summary_table(page)
            
            # Analyze action bars (only bar1 and bar2)
            action_bars = self._analyze_action_bars_bars_only(abilities)
            
            return action_bars
            
        except Exception as e:
            logger.error(f"Error scraping bars for player {player_name}: {e}")
            return None
    
    async def _trigger_ability_loading(self, page):
        """Trigger ability data loading by interacting with the page."""
        try:
            # Look for ability elements with onclick handlers
            ability_elements = await page.query_selector_all("td[onclick*='addPinWithAbility']")
            logger.info(f"Found {len(ability_elements)} ability elements with onclick handlers")
            
            # Click on each ability element to trigger data loading
            for i, element in enumerate(ability_elements[:10]):  # Limit to first 10
                try:
                    if await element.is_visible():
                        await element.click()
                        await asyncio.sleep(0.5)  # Shorter wait between clicks
                except Exception as e:
                    logger.debug(f"Could not click ability element {i+1}: {e}")
            
            # Wait for any triggered loading to complete
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.warning(f"Error triggering ability loading: {e}")
    
    async def _extract_abilities_from_summary_table(self, page) -> List[Dict]:
        """Extract ability data from the #summary-talents-0 table."""
        abilities = []
        
        try:
            # Wait for the summary-talents-0 table to be present
            await page.wait_for_selector('#summary-talents-0', timeout=10000)
            
            # Extract abilities from the Action Bars section within the summary-talents-0 table
            # Look for ability spans within the table
            ability_spans = await page.query_selector_all('#summary-talents-0 span[id^="ability-"]')
            logger.info(f"Found {len(ability_spans)} ability spans in summary-talents-0 table")
            
            for index, span in enumerate(ability_spans):
                try:
                    span_id = await span.get_attribute('id')
                    span_text = await span.text_content()
                    
                    if span_text and span_text.strip():
                        # Parse ability ID
                        match = re.match(r'^ability-(\d+)-(\d+)$', span_id or '')
                        ability_id = match.group(1) if match else None
                        position_in_id = int(match.group(2)) if match and match.group(2) else 0
                        
                        ability_data = {
                            'dom_index': index,
                            'ability_id': ability_id,
                            'ability_name': span_text.strip(),
                            'position_in_id': position_in_id
                        }
                        
                        abilities.append(ability_data)
                        
                except Exception as e:
                    logger.debug(f"Error extracting ability from span {index}: {e}")
            
            # If no ability spans found, try alternative extraction methods
            if not abilities:
                logger.info("No ability spans found, trying alternative extraction methods...")
                abilities = await self._extract_abilities_alternative_methods(page)
            
            return abilities
            
        except Exception as e:
            logger.error(f"Error extracting abilities from summary table: {e}")
            return []
    
    async def _extract_abilities_alternative_methods(self, page) -> List[Dict]:
        """Try alternative methods to extract abilities from the summary table."""
        abilities = []
        
        try:
            # Method 1: Look for ability names in table cells
            table_cells = await page.query_selector_all('#summary-talents-0 td')
            logger.info(f"Found {len(table_cells)} table cells in summary-talents-0")
            
            for index, cell in enumerate(table_cells):
                try:
                    cell_text = await cell.text_content()
                    if cell_text and cell_text.strip():
                        # Look for ability names (filter out common non-ability text)
                        if (len(cell_text.strip()) > 3 and 
                            not cell_text.strip().lower() in ['action bars', 'gear', 'summary', ''] and
                            not cell_text.strip().startswith('CP:') and
                            not cell_text.strip().startswith('Type:') and
                            not cell_text.strip().startswith('Slot:') and
                            not cell_text.strip().startswith('Set:') and
                            not cell_text.strip().startswith('Trait:') and
                            not cell_text.strip().startswith('Enchant:')):
                            
                            ability_data = {
                                'dom_index': index,
                                'ability_id': None,  # No ID available in summary table
                                'ability_name': cell_text.strip(),
                                'position_in_id': 0
                            }
                            
                            abilities.append(ability_data)
                            
                except Exception as e:
                    logger.debug(f"Error extracting text from cell {index}: {e}")
            
            # Method 2: Look for specific Action Bars section
            if not abilities:
                logger.info("Trying to find Action Bars section specifically...")
                action_bars_section = await page.query_selector('#summary-talents-0')
                if action_bars_section:
                    # Look for text content that might be ability names
                    all_text = await action_bars_section.text_content()
                    if all_text:
                        # Split by common delimiters and filter
                        potential_abilities = [text.strip() for text in all_text.split('\n') if text.strip()]
                        for index, ability_name in enumerate(potential_abilities):
                            if (len(ability_name) > 3 and 
                                not ability_name.lower() in ['action bars', 'gear', 'summary', 'main action bar', 'backup action bar'] and
                                not ability_name.startswith('CP:') and
                                not ability_name.startswith('Type:')):
                                
                                ability_data = {
                                    'dom_index': index,
                                    'ability_id': None,
                                    'ability_name': ability_name,
                                    'position_in_id': 0
                                }
                                
                                abilities.append(ability_data)
            
            return abilities
            
        except Exception as e:
            logger.error(f"Error in alternative ability extraction: {e}")
            return []

    async def _extract_abilities(self, page) -> List[Dict]:
        """Extract ability data from the page (legacy method for casts page)."""
        abilities = []
        
        try:
            # Search for ability spans
            ability_spans = await page.query_selector_all("span[id^='ability-']")
            logger.info(f"Found {len(ability_spans)} ability spans")
            
            for index, span in enumerate(ability_spans):
                try:
                    span_id = await span.get_attribute('id')
                    span_text = await span.text_content()
                    
                    if span_text and span_text.strip():
                        # Parse ability ID
                        match = re.match(r'^ability-(\d+)-(\d+)$', span_id or '')
                        ability_id = match.group(1) if match else None
                        position_in_id = int(match.group(2)) if match and match.group(2) else 0
                        
                        ability_data = {
                            'dom_index': index,
                            'ability_id': ability_id,
                            'ability_name': span_text.strip(),
                            'position_in_id': position_in_id
                        }
                        
                        abilities.append(ability_data)
                        
                except Exception as e:
                    logger.debug(f"Error extracting ability from span {index}: {e}")
            
            return abilities
            
        except Exception as e:
            logger.error(f"Error extracting abilities: {e}")
            return []
    
    def _analyze_action_bars_bars_only(self, abilities: List[Dict]) -> Dict:
        """Analyze action bar positions - only return bar1 and bar2."""
        # Sort by DOM index to maintain order
        sorted_abilities = sorted(abilities, key=lambda x: x.get('dom_index', 0))
        
        # Strategy: First 6 = Primary bar, Next 6 = Secondary bar
        bar1 = sorted_abilities[:6] if len(sorted_abilities) >= 6 else sorted_abilities
        bar2 = sorted_abilities[6:12] if len(sorted_abilities) >= 12 else []
        
        return {
            'bar1': ", ".join([a['ability_name'] for a in bar1]),
            'bar2': ", ".join([a['ability_name'] for a in bar2])
        }


# Convenience function for easy usage
async def scrape_encounter_bars_only(report_code: str, fight_id: int, headless: bool = True, 
                                   max_players: int = 10, timeout_per_player: int = 30) -> str:
    """
    Convenience function to scrape an encounter and return bar-only output.
    
    Args:
        report_code: The report code
        fight_id: The fight ID
        headless: Whether to run browser in headless mode
        max_players: Maximum number of players to process
        timeout_per_player: Timeout in seconds per player
    
    Returns:
        Formatted string with only bar1: and bar2: for each player
    """
    scraper = BarOnlyEncounterScraper(headless=headless)
    return await scraper.scrape_encounter_bars(report_code, fight_id, max_players, timeout_per_player)
