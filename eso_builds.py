#!/usr/bin/env python3
"""
ESO Top Builds - Command Line Interface

Main CLI tool for generating ESO trial build reports from esologs.com data.
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

# Load .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.eso_builds.api_client import ESOLogsClient, ESOLogsAPIError
from src.eso_builds.report_generator import ReportGenerator


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def list_available_trials():
    """List all available trials."""
    print("📊 Available ESO Trials")
    print("=" * 30)
    
    try:
        async with ESOLogsClient() as client:
            trials = await client.get_available_trials()
            
            for trial in trials:
                print(f"• {trial['name']} (ID: {trial['id']})")
                print(f"  Encounters: {', '.join(enc['name'] for enc in trial['encounters'])}")
                print()
            
            return trials
            
    except ESOLogsAPIError as e:
        print(f"❌ API Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


async def generate_trial_report(trial_name: Optional[str] = None, zone_id: Optional[int] = None, 
                               output_format: str = "console", output_dir: str = "."):
    """Generate a trial report."""
    generator = ReportGenerator()
    
    try:
        async with ESOLogsClient() as client:
            # If no specific trial provided, use Ossein Cage as default
            if not trial_name and not zone_id:
                trials = await client.get_available_trials()
                ossein_cage = next((t for t in trials if "Ossein Cage" in t['name']), None)
                if ossein_cage:
                    trial_name = ossein_cage['name']
                    zone_id = ossein_cage['id']
                else:
                    print("❌ Could not find default trial (Ossein Cage)")
                    return False
            
            # If trial name provided but no ID, find the ID
            if trial_name and not zone_id:
                trials = await client.get_available_trials()
                matching_trial = next((t for t in trials if trial_name.lower() in t['name'].lower()), None)
                if matching_trial:
                    zone_id = matching_trial['id']
                    trial_name = matching_trial['name']  # Use exact name
                else:
                    print(f"❌ Trial '{trial_name}' not found")
                    print("Use --list-trials to see available trials")
                    return False
            
            print(f"🎯 Generating report for: {trial_name} (Zone ID: {zone_id})")
            print("-" * 50)
            
            # Generate the report
            trial_report = await client.build_trial_report(trial_name, zone_id)
            
            print(f"✅ Generated report with {len(trial_report.rankings)} rankings")
            
            if output_format == "console":
                # Display console output
                console_output = generator.format_console_report(trial_report)
                print("\n" + "=" * 60)
                print(console_output)
                
            elif output_format == "markdown":
                # Save markdown file
                os.makedirs(output_dir, exist_ok=True)
                markdown_file = generator.save_markdown_report(trial_report, output_dir)
                print(f"💾 Markdown report saved to: {markdown_file}")
                
            elif output_format == "both":
                # Both console and markdown
                console_output = generator.format_console_report(trial_report)
                print("\n" + "=" * 60)
                print(console_output)
                
                os.makedirs(output_dir, exist_ok=True)
                markdown_file = generator.save_markdown_report(trial_report, output_dir)
                print(f"\n💾 Markdown report also saved to: {markdown_file}")
            
            return True
            
    except ESOLogsAPIError as e:
        print(f"❌ API Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def analyze_single_report(report_code: str, output_format: str = "console", output_dir: str = "."):
    """Analyze a single ESO Logs report."""
    print(f"🔍 Analyzing Single Report: {report_code}")
    print("=" * 50)
    
    generator = ReportGenerator()
    
    try:
        async with ESOLogsClient() as client:
            # Get encounter details for this report
            encounters = await client.get_encounter_details(report_code)
            
            if not encounters:
                print(f"❌ No encounter data found for report {report_code}")
                return False
            
            print(f"✅ Found {len(encounters)} encounters in report")
            
            # Create a single-report trial report
            from src.eso_builds.models import TrialReport, LogRanking
            from datetime import datetime
            
            ranking = LogRanking(
                rank=1,
                log_url=f"https://www.esologs.com/reports/{report_code}",
                log_code=report_code,
                score=100.0,
                encounters=encounters,
                date=datetime.now()
            )
            
            trial_report = TrialReport(
                trial_name=f"Single Report Analysis",
                zone_id=0,
                rankings=[ranking]
            )
            
            if output_format == "console":
                console_output = generator.format_console_report(trial_report)
                print("\n" + "=" * 60)
                print(console_output)
                
            elif output_format == "markdown":
                os.makedirs(output_dir, exist_ok=True)
                markdown_file = generator.save_markdown_report(trial_report, output_dir)
                print(f"💾 Report saved to: {markdown_file}")
                
            elif output_format == "both":
                console_output = generator.format_console_report(trial_report)
                print("\n" + "=" * 60)
                print(console_output)
                
                os.makedirs(output_dir, exist_ok=True)
                markdown_file = generator.save_markdown_report(trial_report, output_dir)
                print(f"\n💾 Report also saved to: {markdown_file}")
            
            return True
            
    except Exception as e:
        print(f"❌ Single report analysis failed: {e}")
        return False


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="ESO Top Builds - Generate reports from ESO Logs data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available trials
  python eso_builds.py --list-trials
  
  # Generate report for Ossein Cage
  python eso_builds.py --trial "Ossein Cage"
  
  # Generate markdown report for Lucent Citadel
  python eso_builds.py --trial "Lucent Citadel" --output markdown --output-dir reports
  
  # Analyze a specific log report
  python eso_builds.py --report 3gjVGWB2dxCL8XAw --output both
        """
    )
    
    parser.add_argument('--list-trials', action='store_true',
                       help='List all available trials')
    
    parser.add_argument('--trial', type=str,
                       help='Generate report for specific trial (e.g. "Ossein Cage")')
    
    parser.add_argument('--report', type=str,
                       help='Analyze specific report code (e.g. 3gjVGWB2dxCL8XAw)')
    
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
        print("2. Set environment variables:")
        print("   export ESOLOGS_ID='your_client_id'")
        print("   export ESOLOGS_SECRET='your_client_secret'")
        print("\nOr create a .env file with your credentials.")
        sys.exit(1)
    
    # Run the appropriate command
    try:
        if args.list_trials:
            asyncio.run(list_available_trials())
        elif args.report:
            success = asyncio.run(analyze_single_report(args.report, args.output, args.output_dir))
            sys.exit(0 if success else 1)
        elif args.trial:
            success = asyncio.run(generate_trial_report(args.trial, None, args.output, args.output_dir))
            sys.exit(0 if success else 1)
        else:
            # Default: generate Ossein Cage report
            success = asyncio.run(generate_trial_report(None, None, args.output, args.output_dir))
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
