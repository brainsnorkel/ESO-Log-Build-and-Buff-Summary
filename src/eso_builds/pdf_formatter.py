"""
PDF Report Formatter for ESO Builds

This module formats TrialReport objects into PDF documents using ReportLab.
"""

from typing import List
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen.canvas import Canvas

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
            fontSize=18,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=6,
            textColor=colors.darkgreen
        ))
        
        # Encounter heading style
        self.styles.add(ParagraphStyle(
            name='EncounterHeading',
            parent=self.styles['Heading3'],
            fontSize=11,
            spaceAfter=4,
            textColor=colors.darkred
        ))
        
        # Role heading style
        self.styles.add(ParagraphStyle(
            name='RoleHeading',
            parent=self.styles['Heading4'],
            fontSize=9,
            spaceAfter=3,
            textColor=colors.black
        ))
        
        # TOC styles
        self.styles.add(ParagraphStyle(
            name='TOCHeading',
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=16,
            spaceBefore=8,
            spaceAfter=8,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='TOCEntry',
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            leftIndent=15
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
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=36
        )
        
        # Build the story (content)
        story = []
        
        # Add title
        title = Paragraph(trial_report.trial_name, self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 6))
        
        # Add metadata
        metadata_text = f"""
        <b>Generated:</b> {trial_report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}<br/>
        <b>Zone ID:</b> {trial_report.zone_id}<br/>
        """
        metadata = Paragraph(metadata_text, self.styles['Normal'])
        story.append(metadata)
        story.append(Spacer(1, 12))
        
        # Add Table of Contents
        story.extend(self._format_table_of_contents_pdf(trial_report))
        story.append(PageBreak())
        
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
        
        # Add anchor for Report Analysis section with report title
        report_analysis_title = f'<a name="report-analysis"/>Report Analysis - {ranking.log_code}'
        story.append(Paragraph(report_analysis_title, self.styles['Subtitle']))
        
        # Log URL - make full URL clickable
        log_url_text = f'<b>Log URL:</b> <link href="{ranking.log_url}" color="blue">{ranking.log_url}</link>'
        story.append(Paragraph(log_url_text, self.styles['Normal']))
        
        if ranking.date:
            date_text = f"<b>Date:</b> {ranking.date.strftime('%Y-%m-%d %H:%M UTC')}"
            story.append(Paragraph(date_text, self.styles['Normal']))
        
        story.append(Spacer(1, 8))
        
        # Process encounters with index for linking
        for i, encounter in enumerate(ranking.encounters):
            story.extend(self._format_encounter_pdf(encounter, is_first=(i == 0), encounter_index=i))
            story.append(Spacer(1, 6))
        
        return story
    
    def _format_encounter_pdf(self, encounter: EncounterResult, is_first: bool = False, encounter_index: int = 0) -> List:
        """Format a single encounter as PDF elements."""
        story = []
        
        # Add page break before each encounter (except the first one)
        # This ensures each encounter starts fresh and tables don't cross page boundaries
        if not is_first:
            story.append(PageBreak())
        
        # Create anchor for linking from TOC
        clean_name = encounter.encounter_name.lower().replace(' ', '-').replace("'", '')
        encounter_anchor = f"encounter-{encounter_index}-{clean_name}"
        
        # Encounter title with kill/wipe status and bookmark
        if encounter.kill or encounter.boss_percentage <= 0.1:
            status_text = "✅ KILL"
        else:
            status_text = f"❌ WIPE ({encounter.boss_percentage:.1f}%)"
        
        encounter_title = f'<a name="{encounter_anchor}"/>⚔️ {encounter.encounter_name} ({encounter.difficulty.value}) - {status_text}'
        story.append(Paragraph(encounter_title, self.styles['EncounterHeading']))
        story.append(Spacer(1, 6))
        
        # Buff/Debuff uptimes table
        if encounter.buff_uptimes:
            story.extend(self._format_buff_debuff_table_pdf(encounter.buff_uptimes))
            story.append(Spacer(1, 8))
        
        # Player tables by role
        tanks = encounter.tanks
        healers = encounter.healers
        dps = encounter.dps
        
        if tanks:
            story.extend(self._format_role_table_pdf("🛡️ Tanks", tanks))
            story.append(Spacer(1, 6))
        
        if healers:
            story.extend(self._format_role_table_pdf("💚 Healers", healers))
            story.append(Spacer(1, 6))
        
        if dps:
            story.extend(self._format_role_table_pdf("⚔️ DPS", dps))
            story.append(Spacer(1, 6))
        
        return story
    
    def _format_buff_debuff_table_pdf(self, buff_uptimes: dict) -> List:
        """Format buff/debuff uptimes as a PDF table."""
        story = []
        
        # Table title
        story.append(Paragraph("📊 Buff/Debuff Uptimes", self.styles['RoleHeading']))
        story.append(Spacer(1, 3))
        
        # Define all tracked buffs and debuffs
        buffs = ['Major Courage', 'Major Slayer', 'Major Berserk', 'Major Force', 'Minor Toughness', 'Major Resolve', 'Pillager\'s Profit', 'Powerful Assault']
        debuffs = ['Major Breach', 'Major Vulnerability', 'Minor Brittle', 'Stagger', 'Crusher', 'Off Balance', 'Weakening']
        
        # Create table data with Paragraph objects for text wrapping
        table_data = [
            [Paragraph('<b>🔺 Buffs</b>', self.styles['Normal']), 
             Paragraph('<b>Uptime</b>', self.styles['Normal']), 
             Paragraph('<b>🔻 Debuffs</b>', self.styles['Normal']), 
             Paragraph('<b>Uptime</b>', self.styles['Normal'])]
        ]
        
        max_rows = max(len(buffs), len(debuffs))
        for i in range(max_rows):
            # Get buff info for this row
            if i < len(buffs):
                buff_name = buffs[i]
                buff_uptime = f"{buff_uptimes.get(buff_name, 0.0):.1f}%"
                buff_cell = Paragraph(buff_name, self.styles['Normal'])
                buff_uptime_cell = Paragraph(buff_uptime, self.styles['Normal'])
            else:
                buff_cell = Paragraph("", self.styles['Normal'])
                buff_uptime_cell = Paragraph("", self.styles['Normal'])
            
            # Get debuff info for this row
            if i < len(debuffs):
                debuff_name = debuffs[i]
                debuff_uptime = f"{buff_uptimes.get(debuff_name, 0.0):.1f}%"
                debuff_cell = Paragraph(debuff_name, self.styles['Normal'])
                debuff_uptime_cell = Paragraph(debuff_uptime, self.styles['Normal'])
            else:
                debuff_cell = Paragraph("", self.styles['Normal'])
                debuff_uptime_cell = Paragraph("", self.styles['Normal'])
            
            table_data.append([buff_cell, buff_uptime_cell, debuff_cell, debuff_uptime_cell])
        
        # Create and style the table with text wrapping
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
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        # Wrap table in KeepTogether to prevent page breaks within the table
        story.append(KeepTogether([table]))
        return story
    
    def _format_role_table_pdf(self, role_title: str, players: List[PlayerBuild]) -> List:
        """Format a role section as a PDF table."""
        story = []
        
        # Role title
        story.append(Paragraph(role_title, self.styles['RoleHeading']))
        story.append(Spacer(1, 3))
        
        # Create table data with Paragraph objects for text wrapping
        table_data = [
            [Paragraph('<b>Player</b>', self.styles['Normal']), 
             Paragraph('<b>Class</b>', self.styles['Normal']), 
             Paragraph('<b>Gear Sets</b>', self.styles['Normal'])]
        ]
        
        for player in players:
            gear_str = self._format_gear_sets_for_pdf(player.gear_sets)
            table_data.append([
                Paragraph(player.name, self.styles['Normal']),
                Paragraph(player.character_class, self.styles['Normal']),
                Paragraph(gear_str, self.styles['Normal'])
            ])
        
        # Create and style the table with proper wrapping
        table = Table(table_data, colWidths=[1.5*inch, 1.2*inch, 4.0*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        # Wrap table in KeepTogether to prevent page breaks within the table
        story.append(KeepTogether([table]))
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
    
    def _format_table_of_contents_pdf(self, trial_report: TrialReport) -> List:
        """Format a table of contents for the PDF with clickable links."""
        story = []
        
        # TOC Title
        story.append(Paragraph("📋 Table of Contents", self.styles['TOCHeading']))
        story.append(Spacer(1, 8))
        
        # TOC entries
        if trial_report.rankings:
            for ranking in trial_report.rankings:
                # Report Analysis entry (linked)
                report_link = f'<link href="#report-analysis" color="blue">• Report Analysis</link>'
                story.append(Paragraph(report_link, self.styles['TOCEntry']))
                story.append(Spacer(1, 4))
                
                # Encounter entries with clickable links
                for i, encounter in enumerate(ranking.encounters):
                    # Determine kill status
                    if encounter.kill or encounter.boss_percentage <= 0.1:
                        status_text = "✅ KILL"
                    else:
                        status_text = f"❌ WIPE ({encounter.boss_percentage:.1f}%)"
                    
                    # Create anchor name for linking
                    clean_name = encounter.encounter_name.lower().replace(' ', '-').replace("'", '')
                    encounter_anchor = f"encounter-{i}-{clean_name}"
                    
                    # Create clickable link
                    entry_text = f'<link href="#{encounter_anchor}" color="blue">  - {encounter.encounter_name} ({encounter.difficulty.value}) - {status_text}</link>'
                    story.append(Paragraph(entry_text, self.styles['TOCEntry']))
                    story.append(Spacer(1, 2))
        
        return story
    
    def get_filename(self, trial_name: str) -> str:
        """Generate a safe filename for the trial report."""
        # Clean the trial name for use as filename
        safe_name = trial_name.lower()
        safe_name = safe_name.replace(":", "").replace(" ", "_")
        safe_name = safe_name.replace("report_analysis_", "")
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        return f"{safe_name}_{timestamp}.pdf"
