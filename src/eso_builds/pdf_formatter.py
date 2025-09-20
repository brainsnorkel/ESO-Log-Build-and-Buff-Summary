"""
PDF Report Formatter for ESO Builds

This module formats TrialReport objects into PDF documents using ReportLab.
"""

from typing import List
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from .models import TrialReport, LogRanking, EncounterResult, PlayerBuild


class PDFReportFormatter:
    """Formats TrialReport objects into PDF documents."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles for the PDF."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkgreen
        ))
        
        # Encounter heading style
        self.styles.add(ParagraphStyle(
            name='EncounterHeading',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            textColor=colors.darkred
        ))
        
        # Role heading style
        self.styles.add(ParagraphStyle(
            name='RoleHeading',
            parent=self.styles['Heading4'],
            fontSize=10,
            spaceAfter=6,
            textColor=colors.black
        ))
    
    def format_trial_report(self, trial_report: TrialReport) -> bytes:
        """Format a complete trial report as a PDF document."""
        from io import BytesIO
        
        # Create a BytesIO buffer to hold the PDF
        buffer = BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build the story (content)
        story = []
        
        # Add title
        title = Paragraph(trial_report.trial_name, self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Add metadata
        metadata_text = f"""
        <b>Generated:</b> {trial_report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}<br/>
        <b>Zone ID:</b> {trial_report.zone_id}<br/>
        <b>Reports Analyzed:</b> {len(trial_report.rankings) if trial_report.rankings else 1}
        """
        metadata = Paragraph(metadata_text, self.styles['Normal'])
        story.append(metadata)
        story.append(Spacer(1, 20))
        
        # Process rankings (for single report, there's typically one ranking)
        if trial_report.rankings:
            for ranking in trial_report.rankings:
                story.extend(self._format_ranking_pdf(ranking))
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _format_ranking_pdf(self, ranking: LogRanking) -> List:
        """Format a single ranking as PDF elements."""
        story = []
        
        # Ranking header (for single reports, this is just the report info)
        if ranking.rank > 0:
            rank_title = f"Rank {ranking.rank}: {ranking.score:.2f} Score"
        else:
            rank_title = "Report Analysis"
        
        story.append(Paragraph(rank_title, self.styles['Subtitle']))
        
        # Log URL
        log_url_text = f'<b>Log URL:</b> <link href="{ranking.log_url}">{ranking.log_code}</link>'
        story.append(Paragraph(log_url_text, self.styles['Normal']))
        
        # Date if available
        if ranking.date:
            date_text = f"<b>Date:</b> {ranking.date.strftime('%Y-%m-%d %H:%M UTC')}"
            story.append(Paragraph(date_text, self.styles['Normal']))
        
        story.append(Spacer(1, 16))
        
        # Process encounters
        for encounter in ranking.encounters:
            story.extend(self._format_encounter_pdf(encounter))
            story.append(Spacer(1, 12))
        
        return story
    
    def _format_encounter_pdf(self, encounter: EncounterResult) -> List:
        """Format a single encounter as PDF elements."""
        story = []
        
        # Encounter title with kill/wipe status
        if encounter.kill or encounter.boss_percentage <= 0.1:
            status_text = "✅ KILL"
        else:
            status_text = f"❌ WIPE ({encounter.boss_percentage:.1f}%)"
        
        encounter_title = f"⚔️ {encounter.encounter_name} ({encounter.difficulty.value}) - {status_text}"
        story.append(Paragraph(encounter_title, self.styles['EncounterHeading']))
        story.append(Spacer(1, 8))
        
        # Buff/Debuff uptimes table
        if encounter.buff_uptimes:
            story.extend(self._format_buff_debuff_table_pdf(encounter.buff_uptimes))
            story.append(Spacer(1, 12))
        
        # Player tables by role
        tanks = encounter.tanks
        healers = encounter.healers
        dps = encounter.dps
        
        if tanks:
            story.extend(self._format_role_table_pdf("🛡️ Tanks", tanks))
            story.append(Spacer(1, 8))
        
        if healers:
            story.extend(self._format_role_table_pdf("💚 Healers", healers))
            story.append(Spacer(1, 8))
        
        if dps:
            story.extend(self._format_role_table_pdf("⚔️ DPS", dps))
            story.append(Spacer(1, 8))
        
        return story
    
    def _format_buff_debuff_table_pdf(self, buff_uptimes: dict) -> List:
        """Format buff/debuff uptimes as a PDF table."""
        story = []
        
        # Table title
        story.append(Paragraph("📊 Buff/Debuff Uptimes", self.styles['RoleHeading']))
        story.append(Spacer(1, 6))
        
        # Define all tracked buffs and debuffs
        buffs = ['Major Courage', 'Major Slayer', 'Major Berserk', 'Major Force', 'Minor Toughness', 'Major Resolve']
        debuffs = ['Major Breach', 'Major Vulnerability', 'Minor Brittle']
        
        # Create table data
        table_data = [['🔺 Buffs', 'Uptime', '🔻 Debuffs', 'Uptime']]
        
        max_rows = max(len(buffs), len(debuffs))
        for i in range(max_rows):
            # Get buff info for this row
            if i < len(buffs):
                buff_name = buffs[i]
                buff_uptime = f"{buff_uptimes.get(buff_name, 0.0):.1f}%"
            else:
                buff_name = ""
                buff_uptime = ""
            
            # Get debuff info for this row
            if i < len(debuffs):
                debuff_name = debuffs[i]
                debuff_uptime = f"{buff_uptimes.get(debuff_name, 0.0):.1f}%"
            else:
                debuff_name = ""
                debuff_uptime = ""
            
            table_data.append([buff_name, buff_uptime, debuff_name, debuff_uptime])
        
        # Create and style the table
        table = Table(table_data, colWidths=[2.0*inch, 0.8*inch, 2.0*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),  # Buff uptime column
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),  # Debuff uptime column
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(table)
        return story
    
    def _format_role_table_pdf(self, role_title: str, players: List[PlayerBuild]) -> List:
        """Format a role section as a PDF table."""
        story = []
        
        # Role title
        story.append(Paragraph(role_title, self.styles['RoleHeading']))
        story.append(Spacer(1, 6))
        
        # Create table data
        table_data = [['Player', 'Class', 'Gear Sets']]
        
        for player in players:
            gear_str = self._format_gear_sets_for_pdf(player.gear_sets)
            table_data.append([player.name, player.character_class, gear_str])
        
        # Create and style the table
        table = Table(table_data, colWidths=[1.5*inch, 1.2*inch, 4.0*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(table)
        return story
    
    def _format_gear_sets_for_pdf(self, gear_sets: List) -> str:
        """Format gear sets for PDF table cell."""
        if not gear_sets:
            return "No gear data"
        
        # Format each set without perfected highlighting (since PDF doesn't support markdown)
        formatted_sets = []
        for gear_set in gear_sets:
            set_str = f"{gear_set.piece_count}pc {gear_set.name}"
            formatted_sets.append(set_str)
        
        return ", ".join(formatted_sets)
    
    def get_filename(self, trial_name: str) -> str:
        """Generate a safe filename for the trial report."""
        # Clean the trial name for use as filename
        safe_name = trial_name.lower()
        safe_name = safe_name.replace(":", "").replace(" ", "_")
        safe_name = safe_name.replace("report_analysis_", "")
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        return f"{safe_name}_{timestamp}.pdf"
