"""
Markdown report formatting for ESO Top Builds.

This module handles formatting trial reports into markdown format with
proper structure, tables, and links for better readability and sharing.
"""

import logging
from typing import List
from datetime import datetime
from .models import TrialReport, LogRanking, EncounterResult, PlayerBuild, Role

logger = logging.getLogger(__name__)


class MarkdownFormatter:
    """Formats trial reports into markdown format."""
    
    def format_trial_report(self, trial_report: TrialReport) -> str:
        """Format a complete trial report as markdown."""
        lines = []
        
        # Report header with metadata
        lines.extend(self._format_header(trial_report))
        lines.append("")
        
        # Table of contents
        lines.extend(self._format_table_of_contents(trial_report))
        lines.append("")
        
        # Process each report
        for ranking in trial_report.rankings:
            lines.extend(self._format_ranking_markdown(ranking, 1))
            lines.append("")
        
        # Footer with generation info
        lines.extend(self._format_footer(trial_report))
        
        return "\n".join(lines)
    
    def _format_header(self, trial_report: TrialReport) -> List[str]:
        """Format the markdown header."""
        lines = [
            f"# {trial_report.trial_name} - Build Analysis Report",
            "",
            f"**Generated:** {trial_report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**Zone ID:** {trial_report.zone_id}  ",
            f"**Reports Analyzed:** {len(trial_report.rankings)}  ",
            "",
            "---"
        ]
        return lines
    
    def _format_table_of_contents(self, trial_report: TrialReport) -> List[str]:
        """Format a table of contents for the report."""
        lines = [
            "## 📋 Table of Contents",
            ""
        ]
        
        for ranking in trial_report.rankings:
            lines.append(f"- [Report Analysis](#report-analysis)")
            
            for encounter in ranking.encounters:
                clean_name = encounter.encounter_name.lower().replace(' ', '-').replace("'", '')
                encounter_anchor = f"encounter-{clean_name}"
                lines.append(f"  - [{encounter.encounter_name} ({encounter.difficulty.value})](#{encounter_anchor})")
        
        return lines
    
    def _format_ranking_markdown(self, ranking: LogRanking, rank_num: int) -> List[str]:
        """Format a single ranking as markdown."""
        lines = [
            f"## Report Analysis {{#report-analysis}}",
            "",
            f"**🔗 Log URL:** [{ranking.log_code}]({ranking.log_url})  "
        ]
        
        if ranking.guild_name:
            lines.append(f"**🏰 Guild:** {ranking.guild_name}  ")
        
        if ranking.date:
            lines.append(f"**📅 Date:** {ranking.date.strftime('%Y-%m-%d %H:%M UTC')}  ")
        
        lines.append("")
        
        # Process each encounter
        for encounter in ranking.encounters:
            lines.extend(self._format_encounter_markdown(encounter, rank_num))
            lines.append("")
        
        lines.append("---")
        return lines
    
    def _format_encounter_markdown(self, encounter: EncounterResult, rank_num: int) -> List[str]:
        """Format a single encounter as markdown with tables."""
        clean_name = encounter.encounter_name.lower().replace(' ', '-').replace("'", '')
        encounter_anchor = f"encounter-{clean_name}"
        
        lines = [
            f"### ⚔️ {encounter.encounter_name} ({encounter.difficulty.value}) {{#{encounter_anchor}}}",
            ""
        ]
        
        # Create team composition summary
        tanks = encounter.tanks
        healers = encounter.healers
        dps = encounter.dps
        
        
        # Format as tables for better readability
        if tanks:
            lines.extend(self._format_role_table("🛡️ Tanks", tanks))
            lines.append("")
        
        if healers:
            lines.extend(self._format_role_table("💚 Healers", healers))
            lines.append("")
        
        if dps:
            lines.extend(self._format_role_table("⚔️ DPS", dps))
            lines.append("")
        
        return lines
    
    def _format_role_table(self, role_title: str, players: List[PlayerBuild]) -> List[str]:
        """Format a role section as a markdown table."""
        lines = [
            f"#### {role_title}",
            "",
            "| Player | Class | Gear Sets |",
            "|--------|-------|-----------|"
        ]
        
        for i, player in enumerate(players, 1):
            gear_str = self._format_gear_sets_for_table(player.gear_sets)
            lines.append(f"| {role_title.split()[1]} {i} {player.name} | {player.character_class} | {gear_str} |")
        
        # Add empty rows for missing players (especially DPS up to 8)
        if "DPS" in role_title:
            for i in range(len(players) + 1, 9):
                lines.append(f"| DPS {i} @anonymous{i} | - | - |")
        
        return lines
    
    def _format_gear_sets_for_table(self, gear_sets: List) -> str:
        """Format gear sets for markdown table cell."""
        if not gear_sets:
            return "*No gear data*"
        
        # Format each set without perfected highlighting
        formatted_sets = []
        for gear_set in gear_sets:
            set_str = f"{gear_set.piece_count}pc {gear_set.name}"
            formatted_sets.append(set_str)
        
        return ", ".join(formatted_sets)
    
    def _format_footer(self, trial_report: TrialReport) -> List[str]:
        """Format the markdown footer."""
        lines = [
            "---",
            "",
            "## 📊 Report Information",
            "",
            f"- **Trial:** {trial_report.trial_name}",
            f"- **Zone ID:** {trial_report.zone_id}",
            f"- **Rankings Analyzed:** {len(trial_report.rankings)}",
            f"- **Generated:** {trial_report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"- **Tool:** ESO Top Builds Analyzer",
            "",
            "### 🔗 Useful Links",
            "",
            "- [ESO Logs](https://www.esologs.com/)",
            "- [ESO Logs API Documentation](https://www.esologs.com/v2-api-docs/eso/)",
            "- [ESO Top Builds Project](https://github.com/brainsnorkel/ESO-Top-Builds)",
            "",
            "---",
            "",
            "*Generated by ESO Top Builds Analyzer - Analyzing Elder Scrolls Online trial builds from top performing logs.*"
        ]
        return lines
    
    def format_multiple_trials(self, trial_reports: List[TrialReport]) -> str:
        """Format multiple trial reports into a single markdown document."""
        lines = [
            "# ESO Top Builds - Multiple Trials Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**Trials Analyzed:** {len(trial_reports)}  ",
            "",
            "---",
            "",
            "## 📋 Trials Overview",
            ""
        ]
        
        # Overview table
        lines.extend([
            "| Trial | Rankings | Total Encounters |",
            "|-------|----------|------------------|"
        ])
        
        for trial_report in trial_reports:
            total_encounters = sum(len(ranking.encounters) for ranking in trial_report.rankings)
            lines.append(f"| [{trial_report.trial_name}](#{trial_report.trial_name.lower().replace(' ', '-')}) | {len(trial_report.rankings)} | {total_encounters} |")
        
        lines.extend(["", "---", ""])
        
        # Individual trial reports
        for trial_report in trial_reports:
            # Add anchor for navigation
            trial_anchor = trial_report.trial_name.lower().replace(' ', '-')
            lines.append(f"<a name=\"{trial_anchor}\"></a>")
            lines.append("")
            
            # Format the trial report
            trial_content = self.format_trial_report(trial_report)
            # Remove the first header since we're combining reports
            trial_lines = trial_content.split('\n')[3:]  # Skip "# Trial Name - Top Builds Report" and empty lines
            lines.extend(trial_lines)
            lines.extend(["", "---", ""])
        
        return "\n".join(lines)
    
    def get_filename(self, trial_name: str) -> str:
        """Generate a safe filename for the trial report."""
        # Clean the trial name for use as filename
        safe_name = trial_name.lower()
        safe_name = safe_name.replace(' ', '_')
        safe_name = safe_name.replace("'", '')
        safe_name = safe_name.replace('"', '')
        safe_name = safe_name.replace(':', '')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '_-')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        return f"{safe_name}_report_{timestamp}.md"
