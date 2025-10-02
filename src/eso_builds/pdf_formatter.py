"""
PDF Report Formatter for ESO Builds

This module formats TrialReport objects into PDF documents using ReportLab.
"""

from typing import List, Dict
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen.canvas import Canvas

from .models import TrialReport, LogRanking, EncounterResult, PlayerBuild, GearSet, Role, calculate_kills_and_wipes
from .ability_abbreviations import abbreviate_ability_name


class PDFReportFormatter:
    """Formats TrialReport objects into PDF documents."""
    
    # Class name mapping for shorter display names
    CLASS_MAPPING = {
        'Arcanist': 'Arc',
        'Sorcerer': 'Sorc',
        'DragonKnight': 'DK',
        'Necromancer': 'Cro',
        'Templar': 'Plar',
        'Warden': 'Den',
        'Nightblade': 'NB'
    }
    
    # Role icons for visual identification
    ROLE_ICONS = {
        Role.TANK: '🛡️',
        Role.HEALER: '💚',
        Role.DPS: '⚔️'
    }
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _get_class_display_name(self, class_name: str, player_build=None) -> str:
        """Get the shortened display name for a class, with subclass info and Oaken prefix if Oakensoul Ring equipped."""
        # Use subclass information if available
        if player_build and player_build.subclass_info:
            from .subclass_analyzer import ESOSubclassAnalyzer
            analyzer = ESOSubclassAnalyzer()
            skill_lines = player_build.subclass_info.get('skill_lines', [])
            confidence = player_build.subclass_info.get('confidence', 0.0)
            subclass_name = analyzer.get_subclass_display_name(class_name, skill_lines, confidence)
            
            # Check for Oakensoul Ring
            if player_build.gear_sets:
                has_oakensoul = any(
                    'oakensoul' in gear_set.name.lower() 
                    for gear_set in player_build.gear_sets
                )
                if has_oakensoul:
                    return f"Oaken{subclass_name}"
            
            return subclass_name
        
        # Fallback to original logic
        mapped_class = self.CLASS_MAPPING.get(class_name, class_name)
        
        # Check for Oakensoul Ring if player_build is provided
        if player_build and player_build.gear_sets:
            has_oakensoul = any(
                'oakensoul' in gear_set.name.lower() 
                for gear_set in player_build.gear_sets
            )
            if has_oakensoul:
                return f"Oaken{mapped_class}"
        
        return mapped_class
    
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
    
    def format_trial_report(self, trial_report: TrialReport, anonymize: bool = False) -> bytes:
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
        title_text = f"{trial_report.trial_name} - Summary Report"
        title = Paragraph(title_text, self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 6))
        
        # Add metadata
        metadata_text = f"""
        <b>Generated:</b> {trial_report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}<br/>
        <b>Zone ID:</b> {trial_report.zone_id}<br/>
        """
        metadata = Paragraph(metadata_text, self.styles['Normal'])
        story.append(metadata)
        
        # Add kill/wipe summary if we have encounters
        if trial_report.rankings:
            all_encounters = []
            for ranking in trial_report.rankings:
                all_encounters.extend(ranking.encounters)
            
            if all_encounters:
                total_kills, total_wipes = calculate_kills_and_wipes(all_encounters)
                summary_text = f"<b>📊 Trial Summary:</b> {total_kills} Kills, {total_wipes} Wipes"
                summary = Paragraph(summary_text, self.styles['Normal'])
                story.append(summary)
        
        story.append(Spacer(1, 12))
        
        # Add Table of Contents
        story.extend(self._format_table_of_contents_pdf(trial_report))
        story.append(PageBreak())
        
        # Process rankings (for single report, there's typically one ranking)
        if trial_report.rankings:
            for ranking in trial_report.rankings:
                story.extend(self._format_ranking_pdf(ranking, trial_report.trial_name))
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _format_ranking_pdf(self, ranking: LogRanking, trial_name: str) -> List:
        """Format a single ranking as PDF elements."""
        story = []
        
        # Add anchor for Report Analysis section with report title
        report_analysis_title = f'<a name="report-analysis"/>Report Analysis - {trial_name}'
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
        
        # Add group DPS if available
        if encounter.group_dps_total:
            group_dps_text = f"<b>Group DPS:</b> {encounter.group_dps_total:,}"
            story.append(Paragraph(group_dps_text, self.styles['Normal']))
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
            story.extend(self._format_role_table_pdf("Tanks", tanks))
            story.append(Spacer(1, 6))
        
        if healers:
            story.extend(self._format_role_table_pdf("Healers", healers))
            story.append(Spacer(1, 6))
        
        if dps:
            # Sort DPS players by damage percentage (highest first)
            dps_sorted = sorted(dps, key=lambda p: p.dps_data.get('dps_percentage', 0) if p.dps_data else 0, reverse=True)
            story.extend(self._format_role_table_pdf("DPS", dps_sorted))
            story.append(Spacer(1, 6))
        
        return story
    
    def _format_buff_debuff_table_pdf(self, buff_uptimes: Dict[str, str]) -> List:
        """Format buff/debuff uptimes as a PDF table."""
        story = []
        
        # Define all tracked buffs and debuffs (base names without asterisks)
        base_buffs = ['Major Courage', 'Major Slayer', 'Major Berserk', 'Major Force', 'Minor Toughness', 'Major Resolve', 'Powerful Assault']
        base_debuffs = ['Major Breach', 'Major Vulnerability', 'Minor Brittle', 'Stagger', 'Crusher', 'Off Balance', 'Weakening']
        
        # Create table data with Paragraph objects for text wrapping
        table_data = [
            [Paragraph('<b>🔺 Buffs</b>', self.styles['Normal']), 
             Paragraph('<b>Uptime</b>', self.styles['Normal']), 
             Paragraph('<b>🔻 Debuffs</b>', self.styles['Normal']), 
             Paragraph('<b>Uptime</b>', self.styles['Normal'])]
        ]
        
        max_rows = max(len(base_buffs), len(base_debuffs))
        for i in range(max_rows):
            # Get buff info for this row
            if i < len(base_buffs):
                base_buff_name = base_buffs[i]
                # Look for the buff with or without asterisk
                buff_key = None
                buff_uptime = 0.0
                if base_buff_name in buff_uptimes:
                    buff_key = base_buff_name
                    buff_uptime = float(buff_uptimes[buff_key])
                elif f"{base_buff_name}*" in buff_uptimes:
                    buff_key = f"{base_buff_name}*"
                    buff_uptime = float(buff_uptimes[buff_key])
                
                buff_cell = Paragraph(buff_key if buff_key else "", self.styles['Normal'])
                buff_uptime_cell = Paragraph(f"{buff_uptime:.1f}%" if buff_key else "", self.styles['Normal'])
            else:
                buff_cell = Paragraph("", self.styles['Normal'])
                buff_uptime_cell = Paragraph("", self.styles['Normal'])
            
            # Get debuff info for this row
            if i < len(base_debuffs):
                base_debuff_name = base_debuffs[i]
                # Look for the debuff with or without asterisk
                debuff_key = None
                debuff_uptime = 0.0
                if base_debuff_name in buff_uptimes:
                    debuff_key = base_debuff_name
                    debuff_uptime = float(buff_uptimes[debuff_key])
                elif f"{base_debuff_name}*" in buff_uptimes:
                    debuff_key = f"{base_debuff_name}*"
                    debuff_uptime = float(buff_uptimes[debuff_key])
                
                debuff_cell = Paragraph(debuff_key if debuff_key else "", self.styles['Normal'])
                debuff_uptime_cell = Paragraph(f"{debuff_uptime:.1f}%" if debuff_key else "", self.styles['Normal'])
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
            class_name = self._get_class_display_name(player.character_class, player)

            # Add "Set Problem?:" indicator if player has incomplete sets
            if self._has_incomplete_sets(player.gear_sets):
                gear_str = f"<b>Set Problem?:</b> {gear_str}"
            
            # Add role icon and DPS percentage to player name
            role_icon = self.ROLE_ICONS.get(player.role, '')
            player_name = f"{role_icon} {player.name}"
            
            if player.role.value == "DPS" and player.dps_data and 'dps_percentage' in player.dps_data:
                dps_percentage = player.dps_data['dps_percentage']
                player_name = f"{role_icon} {player.name} ({dps_percentage:.1f}%)"
            
            table_data.append([
                Paragraph(player_name, self.styles['Normal']),
                Paragraph(class_name, self.styles['Normal']),
                Paragraph(gear_str, self.styles['Normal'])
            ])
            
            # Add action bars if available
            if player.abilities and (player.abilities.get('bar1') or player.abilities.get('bar2')):
                # Add bar1 if available
                if player.abilities.get('bar1'):
                    bar1_abilities = self._format_action_bar_for_pdf(player.abilities['bar1'])
                    table_data.append([
                        Paragraph("↳ bar1:", self.styles['Normal']),
                        Paragraph("", self.styles['Normal']),
                        Paragraph(bar1_abilities, self.styles['Normal'])
                    ])
                
                # Add bar2 if available
                if player.abilities.get('bar2'):
                    bar2_abilities = self._format_action_bar_for_pdf(player.abilities['bar2'])
                    table_data.append([
                        Paragraph("↳ bar2:", self.styles['Normal']),
                        Paragraph("", self.styles['Normal']),
                        Paragraph(bar2_abilities, self.styles['Normal'])
                    ])
            
            # Add top abilities row for DPS, healers, and tanks (legacy support)
            elif player.abilities and player.abilities.get('top_abilities'):
                if player.role.value == "DPS":
                    ability_type = "Top Damage"
                    abilities_str = self._format_top_abilities_for_pdf(player.abilities.get('top_abilities', []))
                elif player.role.value == "Healer":
                    ability_type = "Top Healing"
                    abilities_str = self._format_top_abilities_for_pdf(player.abilities.get('top_abilities', []))
                else:  # TANK
                    ability_type = "Top Casts"
                    abilities_str = self._format_cast_counts_for_pdf(player.abilities.get('top_abilities', []))
                table_data.append([
                    Paragraph(f"↳ {ability_type}", self.styles['Normal']),
                    Paragraph("", self.styles['Normal']),
                    Paragraph(abilities_str, self.styles['Normal'])
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
    
    def _has_incomplete_sets(self, gear_sets: List[GearSet]) -> bool:
        """Check if a player has incomplete 5-piece sets that should be flagged."""
        for gear_set in gear_sets:
            # Only flag sets that are actually 5-piece sets (not monster sets, mythics, etc.)
            # and have fewer than 5 pieces
            set_name_lower = gear_set.name.lower()
            
            # Skip monster sets, mythics, and arena weapons - these are not 5-piece sets
            if any(indicator in set_name_lower for indicator in [
                'monster', 'undaunted', 'slimecraw', 'nazaray', 'baron zaudrus', 
                'encratis', 'behemoth', 'zaan', 'velothi', 'oakensoul', 'pearls',
                'maelstrom', 'arena', 'crushing', 'merciless'
            ]):
                continue
                
            # Only flag actual 5-piece sets that have fewer than 5 pieces
            if gear_set.max_pieces == 5 and gear_set.piece_count < 5:
                return True
        return False
    
    def _format_action_bar_for_pdf(self, abilities: List[str]) -> str:
        """Format action bar abilities for PDF display."""
        if not abilities:
            return "*No abilities*"
        
        # Join abilities with commas, applying abbreviations, limit length for PDF readability
        abilities_str = ", ".join(abbreviate_ability_name(ability) for ability in abilities)
        
        # Truncate if too long for PDF display
        if len(abilities_str) > 100:
            abilities_str = abilities_str[:97] + "..."
        
        return abilities_str
    
    def _format_top_abilities_for_pdf(self, top_abilities: List) -> str:
        """Format top abilities with percentages for PDF table cell."""
        if not top_abilities:
            return "*No abilities*"
        
        # Format each ability with its percentage
        formatted_abilities = []
        for ability in top_abilities:
            name = ability.get('name', 'Unknown')
            percentage = ability.get('percentage', 0.0)
            formatted_abilities.append(f"{name} ({percentage:.1f}%)")
        
        return ", ".join(formatted_abilities)
    
    def _format_cast_counts_for_pdf(self, top_abilities: List) -> str:
        """Format top abilities with cast counts for PDF table cell."""
        if not top_abilities:
            return "*No abilities*"
        
        # Format each ability with its cast count
        formatted_abilities = []
        for ability in top_abilities:
            name = ability.get('name', 'Unknown')
            casts = ability.get('casts', 0)
            formatted_abilities.append(f"{name} ({casts})")
        
        return ", ".join(formatted_abilities)
    
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
                report_link = f'<link href="#report-analysis" color="blue">Report Analysis</link>'
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
                    entry_text = f'<link href="#{encounter_anchor}" color="blue">{encounter.encounter_name} ({encounter.difficulty.value}) - {status_text}</link>'
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
