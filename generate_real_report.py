#!/usr/bin/env python3
"""
Generate real reports for ESO Logs report code with action bar integration.

This script generates comprehensive reports for a real ESO Logs report,
combining API data with web-scraped action bars.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from eso_builds.enhanced_report_generator import EnhancedReportGenerator, generate_enhanced_report
from eso_builds.report_formatter import ReportFormatter
from eso_builds.pdf_formatter import PDFReportFormatter
from eso_builds.discord_formatter import DiscordReportFormatter
from eso_builds.bar_only_scraper import scrape_encounter_bars_only

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def generate_real_report_with_action_bars(report_code: str):
    """Generate comprehensive reports for a real ESO Logs report with action bars."""
    
    logger.info(f"Generating real reports for ESO Logs report: {report_code}")
    logger.info("=" * 60)
    
    try:
        # Generate enhanced report with action bars
        logger.info("Generating enhanced report with action bar integration...")
        trial_report = await generate_enhanced_report(
            report_code=report_code,
            include_action_bars=True,
            headless=True,
            timeout_per_player=25,
            max_players=12
        )
        
        if not trial_report or not trial_report.rankings:
            logger.error("Failed to generate trial report or no rankings found")
            return []
        
        generated_files = []
        
        # Generate Markdown report
        logger.info("Generating Markdown report...")
        formatter = ReportFormatter()
        markdown_content = formatter.format_trial_report(trial_report)
        
        markdown_filename = f"reports/real_report_{report_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(markdown_filename, 'w') as f:
            f.write(markdown_content)
        
        logger.info(f"Generated Markdown report: {markdown_filename}")
        generated_files.append(markdown_filename)
        
        # Generate PDF report
        logger.info("Generating PDF report...")
        pdf_formatter = PDFReportFormatter()
        pdf_bytes = pdf_formatter.format_trial_report(trial_report)
        
        pdf_filename = f"reports/real_report_{report_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        with open(pdf_filename, 'wb') as f:
            f.write(pdf_bytes)
        
        logger.info(f"Generated PDF report: {pdf_filename}")
        generated_files.append(pdf_filename)
        
        # Generate Discord report
        logger.info("Generating Discord report...")
        discord_formatter = DiscordReportFormatter()
        discord_content = discord_formatter.format_trial_report(trial_report)
        
        discord_filename = f"reports/real_report_{report_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_discord.txt"
        with open(discord_filename, 'w') as f:
            f.write(discord_content)
        
        logger.info(f"Generated Discord report: {discord_filename}")
        generated_files.append(discord_filename)
        
        # Also generate raw action bar data
        logger.info("Generating raw action bar data...")
        try:
            # Get the first encounter's fight ID (assuming fight ID 1 for now)
            fight_id = 1
            bars_output = await scrape_encounter_bars_only(
                report_code=report_code,
                fight_id=fight_id,
                headless=True,
                max_players=12,
                timeout_per_player=25
            )
            
            bars_filename = f"reports/action_bars_{report_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(bars_filename, 'w') as f:
                f.write(bars_output)
            
            logger.info(f"Generated action bars data: {bars_filename}")
            generated_files.append(bars_filename)
            
        except Exception as e:
            logger.warning(f"Could not generate action bars data: {e}")
        
        return generated_files
        
    except Exception as e:
        logger.error(f"Error generating real report: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []


async def generate_action_bars_only(report_code: str):
    """Generate action bars only for a specific report."""
    
    logger.info(f"Generating action bars only for report: {report_code}")
    
    try:
        # Generate action bars for multiple fights
        fight_ids = [1, 17]  # Based on the URL pattern we've seen
        
        generated_files = []
        
        for fight_id in fight_ids:
            logger.info(f"Generating action bars for fight {fight_id}...")
            
            try:
                bars_output = await scrape_encounter_bars_only(
                    report_code=report_code,
                    fight_id=fight_id,
                    headless=True,
                    max_players=10,
                    timeout_per_player=20
                )
                
                if bars_output and bars_output.strip():
                    bars_filename = f"reports/action_bars_{report_code}_fight_{fight_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    with open(bars_filename, 'w') as f:
                        f.write(bars_output)
                    
                    logger.info(f"Generated action bars for fight {fight_id}: {bars_filename}")
                    generated_files.append(bars_filename)
                else:
                    logger.warning(f"No action bars data for fight {fight_id}")
                    
            except Exception as e:
                logger.warning(f"Could not generate action bars for fight {fight_id}: {e}")
        
        return generated_files
        
    except Exception as e:
        logger.error(f"Error generating action bars: {e}")
        return []


async def main():
    """Generate real reports for the specified ESO Logs report."""
    
    report_code = "7KAWyZwPCkaHfc8j"
    
    logger.info("Starting Real Report Generation with Action Bar Integration")
    logger.info("=" * 60)
    logger.info(f"Report Code: {report_code}")
    logger.info(f"Report URL: https://www.esologs.com/reports/{report_code}")
    logger.info("=" * 60)
    
    # Generate comprehensive reports with action bars
    logger.info("Generating comprehensive reports with action bar integration...")
    comprehensive_files = await generate_real_report_with_action_bars(report_code)
    
    # Also generate action bars only for comparison
    logger.info("Generating action bars only for comparison...")
    bars_only_files = await generate_action_bars_only(report_code)
    
    all_files = comprehensive_files + bars_only_files
    
    logger.info("=" * 60)
    logger.info("Real report generation completed!")
    
    if all_files:
        logger.info(f"Generated {len(all_files)} reports:")
        for file in all_files:
            logger.info(f"  - {file}")
        
        logger.info("=" * 60)
        logger.info("✅ SUCCESS: Generated real reports with action bar integration!")
        logger.info("🎯 Reports include both API gear data and web-scraped action bars")
        logger.info("📄 Multiple formats: Markdown, PDF, Discord, and raw action bars")
        logger.info("🚀 Ready for analysis!")
    else:
        logger.error("❌ No reports were generated successfully")
    
    return all_files


if __name__ == "__main__":
    asyncio.run(main())
