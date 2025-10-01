"""
Talents Cell Scraper for ESO Logs Character Action Bars.

This module scrapes action bar abilities from the talents-cell elements in ESO Logs
character summary tables using the structure:
<td class="talents-cell">
  <a title="Ability Name" href="...">
    <img src="..." class="gear-or-ability-icon">
  </a>
</td>
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Tuple
from playwright.async_api import async_playwright, Page, ElementHandle

logger = logging.getLogger(__name__)


class TalentsCellScraper:
    """Scraper for abilities from talents-cell elements in ESO Logs."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        
    async def scrape_character_action_bars(self, url: str) -> Dict:
        """
        Scrape character action bars from an ESO Logs report page.
        
        Args:
            url: The ESO Logs report URL
            
        Returns:
            Dictionary containing character data with action bars
        """
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
            try:
                logger.info(f"Loading page: {url}")
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(3000)
                
                # Get the character details container
                character_container = await page.query_selector("#table-container > div.character-details > div.character-details-contents")
                
                if not character_container:
                    logger.error("Character container not found")
                    return {}
                
                logger.info("✅ Found character container")
                
                # Extract characters with abilities
                characters = await self._extract_characters_with_action_bars(page, character_container)
                
                return {
                    'url': url,
                    'characters': characters,
                    'total_characters': len(characters)
                }
                
            except Exception as e:
                logger.error(f"Error scraping character action bars: {e}")
                return {}
                
            finally:
                await browser.close()
    
    async def _extract_characters_with_action_bars(self, page: Page, container: ElementHandle) -> List[Dict]:
        """Extract characters with their action bars."""
        characters = []
        
        try:
            # Find all talents-cell elements
            talents_cells = await container.query_selector_all('.talents-cell')
            logger.info(f"Found {len(talents_cells)} talents-cell elements")
            
            processed_characters = set()  # To avoid duplicates
            
            for cell_idx, talents_cell in enumerate(talents_cells):
                try:
                    # Extract abilities from this cell
                    abilities = await self._extract_abilities_from_talents_cell(talents_cell)
                    
                    if not abilities:
                        logger.debug(f"No abilities found in talents-cell {cell_idx + 1}")
                        continue
                    
                    # Find the character name and role for this talents cell
                    character_info = await self._find_character_info_for_talents_cell(page, talents_cell)
                    
                    if not character_info:
                        logger.debug(f"Could not find character info for talents-cell {cell_idx + 1}")
                        continue
                    
                    # Create a unique key to avoid duplicates
                    character_key = f"{character_info['name']}_{character_info['role']}_{len(abilities)}"
                    
                    if character_key in processed_characters:
                        logger.debug(f"Skipping duplicate character: {character_info['name']}")
                        continue
                    
                    processed_characters.add(character_key)
                    
                    # Split abilities into bar1 and bar2
                    bar1, bar2 = self._split_abilities_into_bars(abilities)
                    
                    character_data = {
                        'name': character_info['name'],
                        'class': character_info['class'],
                        'role': character_info['role'],
                        'unit_id': character_info.get('unit_id'),
                        'handle': character_info.get('handle'),
                        'abilities': abilities,
                        'bar1': bar1,
                        'bar2': bar2,
                        'total_abilities': len(abilities)
                    }
                    
                    characters.append(character_data)
                    logger.info(f"Extracted {character_info['name']} ({character_info['role']}): {len(abilities)} abilities")
                    
                except Exception as e:
                    logger.debug(f"Error processing talents-cell {cell_idx + 1}: {e}")
                    continue
                
        except Exception as e:
            logger.error(f"Error extracting characters with action bars: {e}")
        
        return characters
    
    async def _extract_abilities_from_talents_cell(self, talents_cell: ElementHandle) -> List[str]:
        """Extract ability names from a talents-cell element."""
        abilities = []
        
        try:
            # Look for all <a> tags with title attributes
            ability_links = await talents_cell.query_selector_all('a[title]')
            
            for link in ability_links:
                title = await link.get_attribute('title')
                if title:
                    # Clean up the ability name
                    ability_name = title.strip()
                    
                    # Remove any additional info in parentheses (like morphs)
                    if ' (' in ability_name:
                        ability_name = ability_name.split(' (')[0]
                    
                    abilities.append(ability_name)
            
        except Exception as e:
            logger.debug(f"Error extracting abilities from talents-cell: {e}")
        
        return abilities
    
    async def _find_character_info_for_talents_cell(self, page: Page, talents_cell: ElementHandle) -> Optional[Dict]:
        """Find character name, class, role, player handle, and unit ID for a talents-cell."""
        try:
            # Navigate up to find the table row
            row = await talents_cell.query_selector('xpath=ancestor::tr')
            if not row:
                return None
            
            # Get all cells in the row
            cells = await row.query_selector_all('td, th')
            if not cells:
                return None
            
            # Extract character name and player handle from first cell
            first_cell = cells[0]
            cell_text = await first_cell.inner_text()
            cell_text = cell_text.strip()
            
            # Extract unit ID from the link's href attribute
            unit_id = None
            try:
                # Look for the <a> tag with the href containing source parameter
                link_element = await first_cell.query_selector('a[href*="source="]')
                if link_element:
                    href = await link_element.get_attribute('href')
                    if href:
                        # Extract source parameter (unit ID) from href
                        source_match = re.search(r'[?&]source=(\d+)', href)
                        if source_match:
                            unit_id = source_match.group(1)
            except Exception as e:
                logger.debug(f"Error extracting unit ID: {e}")
            
            # First, try to extract handle from text (most reliable)
            player_handle = None
            handle_match = re.search(r'@(\w+)', cell_text)
            if handle_match:
                player_handle = handle_match.group(1)
            
            # If no handle found via regex, try the specific selector
            if not player_handle:
                try:
                    handle_element = await first_cell.query_selector('span.display-name.artifact')
                    if handle_element:
                        player_handle = await handle_element.inner_text()
                        player_handle = player_handle.strip()
                except:
                    pass
            
            # Extract character name (remove handle if present)
            character_name = cell_text
            if player_handle:
                character_name = character_name.replace(f"@{player_handle}", "").strip()
            else:
                # Fallback: try to extract handle from @ symbols
                character_name = re.sub(r'@\w+\s*', '', character_name).strip()
            
            character_name = re.sub(r'\s+', ' ', character_name)
            
            # Skip headers and empty names
            if not character_name or character_name in ['Name', 'Character', 'Player', 'Tanks', 'DPS', 'Healers']:
                return None
            
            # Extract class and role information
            character_class = None
            role = "Unknown"
            
            # Look through cells for class information
            for cell in cells:
                cell_text = await cell.inner_text()
                cell_text = cell_text.strip()
                
                # Check for class names
                for class_name in ['Dragonknight', 'Templar', 'Sorcerer', 'Nightblade', 'Warden', 'Arcanist', 'Necromancer']:
                    if class_name in cell_text:
                        character_class = class_name
                        
                        # Determine role from context
                        if 'tank' in cell_text.lower():
                            role = 'Tank'
                        elif 'healer' in cell_text.lower():
                            role = 'Healer'
                        elif 'dps' in cell_text.lower():
                            role = 'DPS'
                        break
                
                if character_class:
                    break
            
            return {
                'name': character_name,
                'handle': player_handle,
                'unit_id': unit_id,
                'class': character_class or 'Unknown',
                'role': role
            }
            
        except Exception as e:
            logger.debug(f"Error finding character info for talents-cell: {e}")
            return None
    
    def _split_abilities_into_bars(self, abilities: List[str]) -> Tuple[List[str], List[str]]:
        """
        Split abilities into bar1 and bar2.
        
        Args:
            abilities: List of ability names
            
        Returns:
            Tuple of (bar1_abilities, bar2_abilities)
        """
        if len(abilities) >= 12:
            # Standard 12 abilities: first 6 are bar1, next 6 are bar2
            return abilities[:6], abilities[6:12]
        elif len(abilities) >= 6:
            # Less than 12 but at least 6: split evenly
            mid_point = len(abilities) // 2
            return abilities[:mid_point], abilities[mid_point:]
        else:
            # Less than 6 abilities: all go to bar1
            return abilities, []


async def scrape_character_action_bars(url: str, headless: bool = True) -> Dict:
    """
    Convenience function to scrape character action bars from an ESO Logs URL.
    
    Args:
        url: The ESO Logs report URL
        headless: Whether to run browser in headless mode
        
    Returns:
        Dictionary containing character data with action bars
    """
    scraper = TalentsCellScraper(headless=headless)
    return await scraper.scrape_character_action_bars(url)


if __name__ == "__main__":
    # Test the scraper
    async def test():
        url = "https://www.esologs.com/reports/N37HBwrjQGYJ6mbv?fight=4"
        
        print("🎯 Testing Talents-Cell Action Bars Scraper")
        print("=" * 50)
        
        result = await scrape_character_action_bars(url)
        
        if result and result.get('characters'):
            print(f"✅ Successfully extracted {result['total_characters']} characters")
            print("\n📋 Character Action Bars:")
            print("-" * 40)
            
            for i, character in enumerate(result['characters']):
                print(f"\n{i+1}. {character['name']}")
                print(f"   Class: {character['class']}")
                print(f"   Role: {character['role']}")
                print(f"   Total Abilities: {character['total_abilities']}")
                
                if character['bar1']:
                    print(f"   Bar 1: {', '.join(character['bar1'])}")
                if character['bar2']:
                    print(f"   Bar 2: {', '.join(character['bar2'])}")
        else:
            print("❌ No character data extracted")
    
    asyncio.run(test())
