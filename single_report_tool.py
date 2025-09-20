#!/usr/bin/env python3
"""
Focused single report analysis tool.

This tool analyzes individual ESO Logs reports with real player data.
"""

import argparse
import asyncio
import logging
import os
import sys

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.eso_builds.single_report_analyzer import SingleReportAnalyzer
from src.eso_builds.report_formatter import ReportFormatter
from src.eso_builds.markdown_formatter import MarkdownFormatter
from src.eso_builds.discord_formatter import DiscordReportFormatter


def setup_logging(verbose: bool = False):
    """Set up logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')


async def analyze_single_report(report_code: str, output_format: str = "console", output_dir: str = "."):
    """Analyze a single ESO Logs report."""
    print(f"🔍 Analyzing ESO Logs Report: {report_code}")
    print("=" * 50)
    
    try:
        analyzer = SingleReportAnalyzer()
        
        # Analyze the report
        trial_report = await analyzer.analyze_report(report_code)
        
        if not trial_report.rankings or not trial_report.rankings[0].encounters:
            print(f"❌ No encounter data found in report {report_code}")
            return False
        
        ranking = trial_report.rankings[0]
        print(f"✅ Found {len(ranking.encounters)} encounters")
        
        # Show summary
        for encounter in ranking.encounters:
            print(f"  • {encounter.encounter_name} ({encounter.difficulty.value})")
            print(f"    Players: {len(encounter.tanks)} tanks, {len(encounter.healers)} healers, {len(encounter.dps)} dps")
        
        # Generate output
        if output_format in ["console", "both"]:
            formatter = ReportFormatter()
            console_output = formatter.format_trial_report(trial_report)
            print("\n" + "=" * 60)
            print("REPORT OUTPUT:")
            print("=" * 60)
            print(console_output)
        
        if output_format in ["markdown", "both"]:
            os.makedirs(output_dir, exist_ok=True)
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            
            # Generate Markdown report
            markdown_formatter = MarkdownFormatter()
            markdown_filename = f"single_report_{report_code}_{timestamp}.md"
            markdown_filepath = os.path.join(output_dir, markdown_filename)
            
            markdown_content = markdown_formatter.format_trial_report(trial_report)
            with open(markdown_filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"\n💾 Markdown report saved to: {markdown_filepath}")
            
            # Generate Discord report
            discord_formatter = DiscordReportFormatter()
            discord_filename = f"single_report_{report_code}_{timestamp}_discord.txt"
            discord_filepath = os.path.join(output_dir, discord_filename)
            
            discord_content = discord_formatter.format_trial_report(trial_report)
            with open(discord_filepath, 'w', encoding='utf-8') as f:
                f.write(discord_content)
            
            print(f"💬 Discord report saved to: {discord_filepath}")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="ESO Single Report Analyzer - Analyze individual ESO Logs reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a specific report
  python single_report_tool.py mtFqVzQPNBcCrd1h
  
  # Generate markdown output
  python single_report_tool.py mtFqVzQPNBcCrd1h --output markdown
  
  # Both console and markdown
  python single_report_tool.py mtFqVzQPNBcCrd1h --output both --output-dir reports
        """
    )
    
    parser.add_argument('report_code', type=str,
                       help='ESO Logs report code (e.g. mtFqVzQPNBcCrd1h)')
    
    parser.add_argument('--output', choices=['console', 'markdown', 'both'], default='console',
                       help='Output format (default: console)')
    
    parser.add_argument('--output-dir', type=str, default='.',
                       help='Directory for output files (default: current directory)')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Check for credentials
    if not os.getenv('ESOLOGS_ID') or not os.getenv('ESOLOGS_SECRET'):
        print("❌ ESO Logs API credentials not configured!")
        print("\nPlease set up your credentials:")
        print("1. Register at https://www.esologs.com/api/clients")
        print("2. Set environment variables or create .env file:")
        print("   ESOLOGS_ID=your_client_id")
        print("   ESOLOGS_SECRET=your_client_secret")
        sys.exit(1)
    
    # Validate report code format
    if not args.report_code or len(args.report_code) < 10:
        print("❌ Invalid report code format")
        print("Report codes should be like: mtFqVzQPNBcCrd1h")
        sys.exit(1)
    
    # Run analysis
    try:
        success = asyncio.run(analyze_single_report(args.report_code, args.output, args.output_dir))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Analysis cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
