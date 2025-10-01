#!/usr/bin/env python3
"""
Create a combined report that merges API gear data with scraped action bar data.

This script reads the existing reports and creates a comprehensive combined report.
"""

import os
import re
from datetime import datetime

def create_combined_report():
    """Create a combined report with API gear data and action bars."""
    
    report_code = "7KAWyZwPCkaHfc8j"
    
    # Read the main API report
    api_report_file = f"reports/single_report_{report_code}_20250930_1707.md"
    action_bars_file = f"reports/action_bars_{report_code}_fight_17_20250930_170400.txt"
    
    if not os.path.exists(api_report_file):
        print(f"❌ API report not found: {api_report_file}")
        return
    
    if not os.path.exists(action_bars_file):
        print(f"❌ Action bars file not found: {action_bars_file}")
        return
    
    print(f"📖 Reading API report: {api_report_file}")
    with open(api_report_file, 'r') as f:
        api_content = f.read()
    
    print(f"🎯 Reading action bars: {action_bars_file}")
    with open(action_bars_file, 'r') as f:
        action_bars_content = f.read()
    
    # Parse action bars data
    action_bars_data = {}
    lines = action_bars_content.strip().split('\n')
    current_player = None
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('Encounter:') or line.startswith('='):
            continue
        
        if 'bar1:' in line:
            if current_player:
                action_bars_data[current_player]['bar1'] = line.replace('bar1:', '').strip()
        elif 'bar2:' in line:
            if current_player:
                action_bars_data[current_player]['bar2'] = line.replace('bar2:', '').strip()
        else:
            # This is a player name
            current_player = line
            action_bars_data[current_player] = {}
    
    print(f"✅ Parsed action bars for {len(action_bars_data)} players")
    
    # Create combined report
    combined_content = f"""# Combined ESO Logs Report with Action Bar Integration
**Report Code:** {report_code}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**URL:** https://www.esologs.com/reports/{report_code}

---

## 🎯 Action Bar Integration Summary

This report combines:
- **API Data**: Gear sets, DPS data, encounter analysis
- **Web-Scraped Data**: Complete action bars (bar1 and bar2) for each player

**Action Bars Extracted for Fight 17:**
{len(action_bars_data)} players with complete action bar data

---

## 📊 Original API Report

{api_content}

---

## 🎮 Complete Action Bar Data

### Fight 17 - Orphic Shattered Shard (Veteran)

"""
    
    # Add action bar data
    for player_name, bars in action_bars_data.items():
        combined_content += f"\n**{player_name}**\n"
        if 'bar1' in bars:
            combined_content += f"- **Bar 1:** {bars['bar1']}\n"
        if 'bar2' in bars:
            combined_content += f"- **Bar 2:** {bars['bar2']}\n"
        combined_content += "\n"
    
    combined_content += f"""
---

## 🔗 Data Sources

- **ESO Logs API**: Gear analysis, DPS data, encounter statistics
- **Web Scraping**: Action bar extraction from player summary pages
- **Integration**: Combined analysis for comprehensive build understanding

---

## 📝 Technical Notes

This report demonstrates the action bar integration feature that:
1. Fetches comprehensive gear and performance data from the ESO Logs API
2. Web-scrapes detailed action bar information from individual player pages
3. Combines both data sources for complete build analysis

The action bar data shows the actual abilities slotted on each player's primary (bar1) and secondary (bar2) action bars during the encounter.
"""
    
    # Save combined report
    combined_filename = f"reports/combined_report_{report_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(combined_filename, 'w') as f:
        f.write(combined_content)
    
    print(f"✅ Combined report saved: {combined_filename}")
    
    # Also create a summary version
    summary_content = f"""# ESO Logs Report Summary with Action Bars
**Report:** {report_code} | **Fight 17** | **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎮 Player Action Bars (Fight 17)

"""
    
    for player_name, bars in action_bars_data.items():
        summary_content += f"### {player_name}\n"
        if 'bar1' in bars:
            summary_content += f"**Bar 1:** {bars['bar1']}\n\n"
        if 'bar2' in bars:
            summary_content += f"**Bar 2:** {bars['bar2']}\n\n"
        summary_content += "---\n\n"
    
    summary_filename = f"reports/action_bars_summary_{report_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(summary_filename, 'w') as f:
        f.write(summary_content)
    
    print(f"✅ Action bars summary saved: {summary_filename}")
    
    return [combined_filename, summary_filename]


if __name__ == "__main__":
    print("🚀 Creating Combined Report with Action Bar Integration")
    print("=" * 60)
    
    files = create_combined_report()
    
    print("=" * 60)
    print("✅ Combined report generation completed!")
    print(f"📄 Generated {len(files)} combined reports:")
    for file in files:
        print(f"  - {file}")
    
    print("\n🎯 The combined report includes:")
    print("  • Complete API gear analysis")
    print("  • DPS performance data")
    print("  • Web-scraped action bars")
    print("  • Integrated build analysis")
