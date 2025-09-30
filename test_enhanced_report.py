#!/usr/bin/env python3
"""
Test script for Enhanced Report Generator with Action Bar Integration.

This script demonstrates how to generate encounter reports that include
both gear information (from API) and action bar data (from web scraping).
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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_enhanced_report_generation():
    """Test the enhanced report generation with action bars."""
    
    logger.info("Testing Enhanced Report Generation with Action Bars")
    logger.info("=" * 60)
    
    # Test data - using the specific report from the web search
    report_code = "7KAWyZwPCkaHfc8j"
    
    try:
        # Generate enhanced report with action bars
        logger.info(f"Generating enhanced report for: {report_code}")
        
        trial_report = await generate_enhanced_report(
            report_code=report_code,
            include_action_bars=True,
            headless=True,
            timeout_per_player=20,
            max_players=8
        )
        
        logger.info(f"Generated trial report: {trial_report.trial_name}")
        logger.info(f"Number of rankings: {len(trial_report.rankings)}")
        
        if trial_report.rankings:
            ranking = trial_report.rankings[0]
            logger.info(f"Number of encounters: {len(ranking.encounters)}")
            
            for encounter in ranking.encounters:
                logger.info(f"  - {encounter.encounter_name}: {len(encounter.players)} players")
                
                # Check if any players have action bar data
                players_with_bars = 0
                for player in encounter.players:
                    if player.abilities and (player.abilities.get('bar1') or player.abilities.get('bar2')):
                        players_with_bars += 1
                
                logger.info(f"    Players with action bars: {players_with_bars}")
        
        return trial_report
        
    except Exception as e:
        logger.error(f"Enhanced report generation failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


def test_markdown_formatting(trial_report):
    """Test markdown formatting of the enhanced report."""
    
    logger.info("=" * 60)
    logger.info("Testing Markdown Formatting with Action Bars")
    logger.info("=" * 60)
    
    try:
        formatter = ReportFormatter()
        markdown_output = formatter.format_trial_report(trial_report)
        
        # Save markdown output
        output_file = f"enhanced_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(output_file, 'w') as f:
            f.write(markdown_output)
        
        logger.info(f"Markdown output saved to: {output_file}")
        
        # Print a sample of the output
        logger.info("=" * 60)
        logger.info("SAMPLE MARKDOWN OUTPUT:")
        logger.info("=" * 60)
        
        lines = markdown_output.split('\n')
        for i, line in enumerate(lines[:50]):  # Show first 50 lines
            print(f"{i+1:2d}: {line}")
        
        if len(lines) > 50:
            print("... (truncated)")
        
        return markdown_output
        
    except Exception as e:
        logger.error(f"Markdown formatting failed: {e}")
        return None


def test_pdf_formatting(trial_report):
    """Test PDF formatting of the enhanced report."""
    
    logger.info("=" * 60)
    logger.info("Testing PDF Formatting with Action Bars")
    logger.info("=" * 60)
    
    try:
        pdf_formatter = PDFReportFormatter()
        pdf_bytes = pdf_formatter.format_trial_report(trial_report)
        
        # Save PDF output
        output_file = f"enhanced_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        with open(output_file, 'wb') as f:
            f.write(pdf_bytes)
        
        logger.info(f"PDF output saved to: {output_file}")
        logger.info(f"PDF size: {len(pdf_bytes):,} bytes")
        
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"PDF formatting failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


def demonstrate_action_bar_data(trial_report):
    """Demonstrate the action bar data that was scraped."""
    
    logger.info("=" * 60)
    logger.info("ACTION BAR DATA DEMONSTRATION")
    logger.info("=" * 60)
    
    if not trial_report.rankings:
        logger.info("No rankings found in trial report")
        return
    
    ranking = trial_report.rankings[0]
    
    for encounter in ranking.encounters:
        logger.info(f"\nEncounter: {encounter.encounter_name}")
        logger.info("-" * 40)
        
        for player in encounter.players:
            if player.abilities and (player.abilities.get('bar1') or player.abilities.get('bar2')):
                logger.info(f"\n{player.name} ({player.character_class} {player.role.value}):")
                
                if player.abilities.get('bar1'):
                    logger.info(f"  bar1: {', '.join(player.abilities['bar1'])}")
                
                if player.abilities.get('bar2'):
                    logger.info(f"  bar2: {', '.join(player.abilities['bar2'])}")
            else:
                logger.debug(f"{player.name}: No action bar data available")


async def main():
    """Run all enhanced report tests."""
    
    logger.info("Starting Enhanced Report Generation Tests")
    logger.info("=" * 60)
    logger.info("Testing integration of API data with web-scraped action bars")
    logger.info("=" * 60)
    
    # Test 1: Generate enhanced report
    trial_report = await test_enhanced_report_generation()
    
    if not trial_report:
        logger.error("Failed to generate trial report")
        return
    
    # Test 2: Demonstrate action bar data
    demonstrate_action_bar_data(trial_report)
    
    # Test 3: Test markdown formatting
    markdown_output = test_markdown_formatting(trial_report)
    
    # Test 4: Test PDF formatting
    pdf_bytes = test_pdf_formatting(trial_report)
    
    logger.info("=" * 60)
    logger.info("Enhanced report tests completed!")
    
    if trial_report and markdown_output and pdf_bytes:
        logger.info("✅ SUCCESS: Generated enhanced reports with action bars!")
        logger.info("🎯 Perfect: Combined API gear data with web-scraped action bars")
        logger.info("📄 Generated both Markdown and PDF formats")
        logger.info("🚀 Ready for production integration!")
    else:
        logger.info("❌ Some tests failed - check logs above")


if __name__ == "__main__":
    asyncio.run(main())
