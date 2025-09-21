#!/usr/bin/env python3
"""
Focused single report analysis tool.

This tool analyzes individual ESO Logs reports with real player data.
"""

import argparse
import asyncio
import logging
import os
import re
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
from src.eso_builds.discord_webhook_client import DiscordWebhookClient


def extract_report_id(input_string: str) -> str:
    """
    Extract ESO Logs report ID from either a full URL or just the report ID.
    
    Args:
        input_string: Either a full ESO Logs URL or just the report ID
        
    Returns:
        The extracted report ID
        
    Raises:
        ValueError: If the input is invalid or doesn't contain a valid report ID
    """
    if not input_string or not input_string.strip():
        raise ValueError("Input cannot be empty")
    
    input_string = input_string.strip()
    
    # If it looks like a URL, extract the report ID
    if input_string.startswith('http'):
        # Pattern to match ESO Logs report URLs
        url_pattern = r'https?://(?:www\.)?esologs\.com/reports/([a-zA-Z0-9]+)'
        match = re.search(url_pattern, input_string)
        if match:
            return match.group(1)
        else:
            raise ValueError("Invalid ESO Logs URL format")
    
    # If it's not a URL, treat it as a report ID directly
    # Validate that it looks like a report ID (alphanumeric, reasonable length)
    if re.match(r'^[a-zA-Z0-9]+$', input_string) and len(input_string) >= 10:
        return input_string
    else:
        raise ValueError("Invalid report ID format")


def setup_logging(verbose: bool = False):
    """Set up logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')


async def analyze_single_report(report_code: str, output_format: str = "console", output_dir: str = ".", anonymize: bool = False, discord_webhook: str = None):
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
            console_output = formatter.format_trial_report(trial_report, anonymize=anonymize)
            print("\n" + "=" * 60)
            print("REPORT OUTPUT:")
            print("=" * 60)
            print(console_output)
        
        # Generate file outputs if requested
        if output_format in ["markdown", "discord", "pdf", "all"]:
            os.makedirs(output_dir, exist_ok=True)
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            
            # Generate Markdown report
            if output_format in ["markdown", "all"]:
                markdown_formatter = MarkdownFormatter()
                markdown_filename = f"single_report_{report_code}_{timestamp}.md"
                markdown_filepath = os.path.join(output_dir, markdown_filename)
                
                markdown_content = markdown_formatter.format_trial_report(trial_report, anonymize=anonymize)
                with open(markdown_filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                print(f"\n💾 Markdown report saved to: {markdown_filepath}")
            
            # Generate Discord report
            if output_format in ["discord", "all"]:
                discord_formatter = DiscordReportFormatter()
                discord_filename = f"single_report_{report_code}_{timestamp}_discord.txt"
                discord_filepath = os.path.join(output_dir, discord_filename)
                
                discord_content = discord_formatter.format_trial_report(trial_report, anonymize=anonymize)
                with open(discord_filepath, 'w', encoding='utf-8') as f:
                    f.write(discord_content)
                
                print(f"💬 Discord report saved to: {discord_filepath}")
                
                # Post to Discord webhook if provided
                if discord_webhook:
                    try:
                        async with DiscordWebhookClient(discord_webhook) as webhook_client:
                            title = f"ESO Trial Report - {report_code}"
                            success = await webhook_client.post_report(discord_content, title)
                            if success:
                                print(f"🚀 Report posted to Discord webhook")
                            else:
                                print(f"❌ Failed to post to Discord webhook")
                    except Exception as e:
                        print(f"❌ Error posting to Discord webhook: {e}")
            
            # Generate PDF report
            if output_format in ["pdf", "all"]:
                from src.eso_builds.pdf_formatter import PDFReportFormatter
                
                pdf_formatter = PDFReportFormatter()
                pdf_filename = f"single_report_{report_code}_{timestamp}.pdf"
                pdf_filepath = os.path.join(output_dir, pdf_filename)
                
                pdf_content = pdf_formatter.format_trial_report(trial_report, anonymize=anonymize)
                with open(pdf_filepath, 'wb') as f:
                    f.write(pdf_content)
                
                print(f"📄 PDF report saved to: {pdf_filepath}")
        
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
  # Analyze a specific report (report ID)
  python single_report_tool.py mtFqVzQPNBcCrd1h
  
  # Analyze a specific report (full URL)
  python single_report_tool.py "https://www.esologs.com/reports/mtFqVzQPNBcCrd1h"
  
  # Generate markdown output
  python single_report_tool.py mtFqVzQPNBcCrd1h --output markdown
  
  # Both console and markdown
  python single_report_tool.py mtFqVzQPNBcCrd1h --output both --output-dir reports
  
  # Post directly to Discord webhook
  python single_report_tool.py mtFqVzQPNBcCrd1h --output discord --discord-webhook "https://discord.com/api/webhooks/..."
        """
    )
    
    parser.add_argument('report_code', type=str,
                       help='ESO Logs report code or full URL (e.g. mtFqVzQPNBcCrd1h or https://www.esologs.com/reports/mtFqVzQPNBcCrd1h)')
    
    parser.add_argument('--output', choices=['console', 'markdown', 'discord', 'pdf', 'all'], default='console',
                       help='Output format: console, markdown, discord, pdf, or all (default: console)')
    
    parser.add_argument('--output-dir', type=str, default='reports',
                       help='Directory for output files (default: reports)')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    parser.add_argument('--anonymize', action='store_true',
                       help='Anonymize the report by replacing player names with anon1, anon2, etc. and removing URLs')
    
    parser.add_argument('--discord-webhook', type=str,
                       help='Discord webhook URL to post the report directly to Discord')
    
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
    
    # Extract and validate report code
    try:
        report_id = extract_report_id(args.report_code)
        print(f"📋 Extracted report ID: {report_id}")
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
        print("Examples:")
        print("  Report ID: mtFqVzQPNBcCrd1h")
        print("  Full URL: https://www.esologs.com/reports/mtFqVzQPNBcCrd1h")
        sys.exit(1)
    
    # Run analysis
    try:
        success = asyncio.run(analyze_single_report(report_id, args.output, args.output_dir, args.anonymize, args.discord_webhook))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Analysis cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
