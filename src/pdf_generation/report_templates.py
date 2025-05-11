"""
Report Templates Module

This module provides templates for generating various types of reports
from research results.
"""

import json
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, cast

from src.pdf_generation import (
    PDFReport, ReportConfig, ReportLibrary, ReportElement,
    TextElement, TableElement, ChartElement, ImageElement,
    HeaderElement, FooterElement, ListElement, PageBreakElement,
    StyleSheet, ColorScheme
)


class ReportTemplate:
    """Base class for report templates."""
    
    def __init__(self, 
                 title: str,
                 author: str = "Deep Deep Research v2",
                 page_size: str = "letter",
                 orientation: str = "portrait",
                 include_toc: bool = True,
                 include_page_numbers: bool = True,
                 library: ReportLibrary = ReportLibrary.REPORTLAB):
        """Initialize a report template with basic configuration.
        
        Args:
            title: Report title
            author: Report author
            page_size: Page size (e.g., "letter", "A4")
            orientation: Page orientation ("portrait" or "landscape")
            include_toc: Whether to include a table of contents
            include_page_numbers: Whether to include page numbers
            library: PDF generation library to use
        """
        self.config = ReportConfig(
            title=title,
            author=author,
            subject="Research Report",
            keywords=["research", "analysis", "findings"],
            page_size=page_size,
            orientation=orientation,
            include_toc=include_toc,
            include_page_numbers=include_page_numbers,
            library=library
        )
        
        self.report = PDFReport(self.config)
        self.add_standard_elements()
    
    def add_standard_elements(self) -> None:
        """Add standard elements like header and footer to the report."""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Add header and footer
        self.report.add_element(HeaderElement(
            text=self.config.title,
            height=50,
            include_date=True,
            include_page_number=True
        ))
        
        self.report.add_element(FooterElement(
            text=f"Generated on {today} by {self.config.author}",
            height=30,
            include_page_number=True
        ))
    
    def generate(self, output_path: Union[str, Path]) -> str:
        """Generate the report and save it to the specified path."""
        return self.report.generate(output_path)


class ResearchReportTemplate(ReportTemplate):
    """Template for generating reports from research results."""
    
    def add_title_page(self, subtitle: Optional[str] = None, logo_path: Optional[Path] = None) -> None:
        """Add a title page to the report.
        
        Args:
            subtitle: Optional subtitle for the report
            logo_path: Optional path to a logo image
        """
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Add title
        self.report.add_element(TextElement(
            text=self.config.title,
            x=72, y=200,
            font_size=24,
            align='center'
        ))
        
        # Add subtitle if provided
        if subtitle:
            self.report.add_element(TextElement(
                text=subtitle,
                x=72, y=240,
                font_size=18,
                align='center'
            ))
        
        # Add logo if provided
        if logo_path:
            self.report.add_element(ImageElement(
                image_path=logo_path,
                x=72, y=100,
                width=450
            ))
        
        # Add author and date
        self.report.add_element(TextElement(
            text=f"Prepared by: {self.config.author}",
            x=72, y=300,
            font_size=14,
            align='center'
        ))
        
        self.report.add_element(TextElement(
            text=f"Date: {today}",
            x=72, y=330,
            font_size=12,
            align='center'
        ))
        
        # Add page break after title page
        self.report.add_element(PageBreakElement())
    
    def add_executive_summary(self, summary_text: str) -> None:
        """Add an executive summary section to the report.
        
        Args:
            summary_text: Text for the executive summary
        """
        # Add section title
        self.report.add_element(TextElement(
            text="Executive Summary",
            x=72, y=72,
            font_size=18,
            font_name="Helvetica-Bold"
        ))
        
        # Add summary text
        self.report.add_element(TextElement(
            text=summary_text,
            x=72, y=100,
            width=450,
            font_size=12
        ))
        
        # Add page break after executive summary
        self.report.add_element(PageBreakElement())
    
    def add_table_of_contents(self) -> None:
        """Add a table of contents section to the report."""
        # This is a placeholder - in a real implementation, 
        # the TOC would be generated during PDF rendering
        self.report.add_element(TextElement(
            text="Table of Contents",
            x=72, y=72,
            font_size=18,
            font_name="Helvetica-Bold"
        ))
        
        # Add page break after TOC
        self.report.add_element(PageBreakElement())
    
    def add_section(self, title: str, content: str, level: int = 1) -> None:
        """Add a section with title and content to the report.
        
        Args:
            title: Section title
            content: Section content text
            level: Heading level (1-3)
        """
        # Calculate y position based on current state - simplified here
        y_position = 72
        
        # Add section title
        font_size = {1: 18, 2: 16, 3: 14}.get(level, 18)
        self.report.add_element(TextElement(
            text=title,
            x=72, y=y_position,
            font_size=font_size,
            font_name="Helvetica-Bold"
        ))
        
        # Add content
        self.report.add_element(TextElement(
            text=content,
            x=72, y=y_position + 30,
            width=450,
            font_size=12
        ))
    
    def add_table_from_data(self, 
                           title: str,
                           data: List[List[Any]],
                           x: float = 72,
                           y: float = 150,
                           col_widths: Optional[List[float]] = None) -> None:
        """Add a table from data with a title.
        
        Args:
            title: Table title
            data: Table data (list of rows, each row is a list of cells)
            x: X-coordinate position
            y: Y-coordinate position
            col_widths: Optional list of column widths
        """
        # Add table title
        self.report.add_element(TextElement(
            text=title,
            x=x, y=y - 30,
            font_size=14
        ))
        
        # Add table
        self.report.add_element(TableElement(
            data=data,
            x=x, y=y,
            col_widths=col_widths,
            header=True
        ))
    
    def add_chart_from_data(self,
                          title: str,
                          chart_type: str,
                          data: Dict[str, Any],
                          x: float = 72,
                          y: float = 150,
                          width: float = 450,
                          height: float = 300) -> None:
        """Add a chart from data with a title.
        
        Args:
            title: Chart title
            chart_type: Type of chart ('line', 'bar', 'pie', 'scatter')
            data: Chart data in the appropriate format
            x: X-coordinate position
            y: Y-coordinate position
            width: Width of the chart
            height: Height of the chart
        """
        # Add chart title
        self.report.add_element(TextElement(
            text=title,
            x=x, y=y - 30,
            font_size=14
        ))
        
        # Add chart
        self.report.add_element(ChartElement(
            chart_type=chart_type,
            data=data,
            x=x, y=y,
            width=width,
            height=height
        ))
    
    def add_conclusion(self, conclusion_text: str, recommendations: Optional[List[str]] = None) -> None:
        """Add a conclusion section with optional recommendations.
        
        Args:
            conclusion_text: Text for the conclusion section
            recommendations: Optional list of recommendations
        """
        # Add section title
        self.report.add_element(TextElement(
            text="Conclusion",
            x=72, y=72,
            font_size=18,
            font_name="Helvetica-Bold"
        ))
        
        # Add conclusion text
        self.report.add_element(TextElement(
            text=conclusion_text,
            x=72, y=100,
            width=450,
            font_size=12
        ))
        
        # Add recommendations if provided
        if recommendations:
            # Add recommendations title
            self.report.add_element(TextElement(
                text="Recommendations",
                x=72, y=250,
                font_size=16,
                font_name="Helvetica-Bold"
            ))
            
            # Add recommendations as a list
            self.report.add_element(ListElement(
                items=recommendations,
                x=92, y=280,
                width=430,
                numbered=False,
                font_size=12
            ))
    
    def add_appendix(self, title: str, content: str) -> None:
        """Add an appendix section to the report.
        
        Args:
            title: Appendix title
            content: Appendix content text
        """
        # Add page break before appendix
        self.report.add_element(PageBreakElement())
        
        # Add appendix title
        self.report.add_element(TextElement(
            text=f"Appendix: {title}",
            x=72, y=72,
            font_size=18,
            font_name="Helvetica-Bold"
        ))
        
        # Add appendix content
        self.report.add_element(TextElement(
            text=content,
            x=72, y=100,
            width=450,
            font_size=12
        ))


class ResearchResultsReport(ReportTemplate):
    """Template specifically for generating reports from research_results.json."""
    
    def populate_from_json(self, json_path: Union[str, Path]) -> None:
        """Populate the report from a research_results.json file.
        
        Args:
            json_path: Path to the research_results.json file
        """
        # Load the research results
        with open(json_path, 'r') as f:
            research_results = json.load(f)
        
        # Create title page
        self.add_title_page(research_results)
        
        # Add summary
        self.add_summary_section(research_results)
        
        # Add main findings
        self.add_findings_section(research_results)
        
        # Add sources analysis
        self.add_sources_section(research_results)
        
        # Add conclusion
        self.add_conclusion_section(research_results)
    
    def add_title_page(self, research_results: Dict[str, Any]) -> None:
        """Add a title page based on research results.
        
        Args:
            research_results: Research results data
        """
        # Extract metadata
        query = research_results.get('metadata', {}).get('query', 'Research Query')
        timestamp = research_results.get('metadata', {}).get('timestamp', datetime.datetime.now().isoformat())
        
        try:
            date_obj = datetime.datetime.fromisoformat(timestamp)
            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            formatted_date = timestamp
        
        # Add title
        self.report.add_element(TextElement(
            text=self.config.title,
            x=72, y=150,
            font_size=24,
            align='center'
        ))
        
        # Add query
        self.report.add_element(TextElement(
            text=f"Query: {query}",
            x=72, y=200,
            font_size=16,
            align='center'
        ))
        
        # Add author and date
        self.report.add_element(TextElement(
            text=f"Generated by: {self.config.author}",
            x=72, y=250,
            font_size=14,
            align='center'
        ))
        
        self.report.add_element(TextElement(
            text=f"Date: {formatted_date}",
            x=72, y=280,
            font_size=12,
            align='center'
        ))
        
        # Add page break after title page
        self.report.add_element(PageBreakElement())
    
    def add_summary_section(self, research_results: Dict[str, Any]) -> None:
        """Add a summary section based on research results.
        
        Args:
            research_results: Research results data
        """
        # Extract summary
        summary = research_results.get('summary', 'No summary available.')
        
        # Add section title
        self.report.add_element(TextElement(
            text="Executive Summary",
            x=72, y=72,
            font_size=18,
            font_name="Helvetica-Bold"
        ))
        
        # Add summary text
        self.report.add_element(TextElement(
            text=summary,
            x=72, y=100,
            width=450,
            font_size=12
        ))
        
        # Add page break after summary
        self.report.add_element(PageBreakElement())
    
    def add_findings_section(self, research_results: Dict[str, Any]) -> None:
        """Add a findings section based on research results.
        
        Args:
            research_results: Research results data
        """
        # Extract findings
        findings = research_results.get('findings', [])
        
        if not findings:
            return
        
        # Add section title
        self.report.add_element(TextElement(
            text="Key Findings",
            x=72, y=72,
            font_size=18,
            font_name="Helvetica-Bold"
        ))
        
        y_position = 100
        
        # Add each finding
        for i, finding in enumerate(findings):
            finding_title = finding.get('title', f'Finding {i+1}')
            finding_content = finding.get('content', 'No content available.')
            
            # Add finding title
            self.report.add_element(TextElement(
                text=finding_title,
                x=72, y=y_position,
                font_size=16,
                font_name="Helvetica-Bold"
            ))
            
            # Add finding content
            self.report.add_element(TextElement(
                text=finding_content,
                x=72, y=y_position + 30,
                width=450,
                font_size=12
            ))
            
            y_position += 150
            
            # Add page break if needed
            if y_position > 700:
                self.report.add_element(PageBreakElement())
                y_position = 72
        
        # Add page break after findings
        self.report.add_element(PageBreakElement())
    
    def add_sources_section(self, research_results: Dict[str, Any]) -> None:
        """Add a sources section based on research results.
        
        Args:
            research_results: Research results data
        """
        # Extract sources
        sources = research_results.get('sources', [])
        
        if not sources:
            return
        
        # Add section title
        self.report.add_element(TextElement(
            text="Sources",
            x=72, y=72,
            font_size=18,
            font_name="Helvetica-Bold"
        ))
        
        # Create table data
        table_data = [["Source", "Title", "Relevance"]]
        for source in sources:
            title = source.get('title', 'Untitled')
            url = source.get('url', 'No URL')
            relevance = source.get('relevance', 'N/A')
            table_data.append([url, title, relevance])
        
        # Add sources table
        self.report.add_element(TableElement(
            data=table_data,
            x=72, y=100,
            col_widths=[180, 180, 90],
            header=True
        ))
        
        # Add page break after sources
        self.report.add_element(PageBreakElement())
    
    def add_conclusion_section(self, research_results: Dict[str, Any]) -> None:
        """Add a conclusion section based on research results.
        
        Args:
            research_results: Research results data
        """
        # Extract conclusion
        conclusion = research_results.get('conclusion', 'No conclusion available.')
        
        # Add section title
        self.report.add_element(TextElement(
            text="Conclusion",
            x=72, y=72,
            font_size=18,
            font_name="Helvetica-Bold"
        ))
        
        # Add conclusion text
        self.report.add_element(TextElement(
            text=conclusion,
            x=72, y=100,
            width=450,
            font_size=12
        ))


def create_report_from_research_results(json_path: Union[str, Path], 
                                       output_path: Union[str, Path],
                                       title: str = "Research Results Report",
                                       library: ReportLibrary = ReportLibrary.REPORTLAB) -> str:
    """Create a report from a research_results.json file.
    
    Args:
        json_path: Path to the research_results.json file
        output_path: Path to save the generated PDF report
        title: Report title
        library: PDF generation library to use

    Returns:
        Path to the generated PDF file
    """
    report_template = ResearchResultsReport(
        title=title,
        library=library
    )
    
    report_template.populate_from_json(json_path)
    
    return report_template.generate(output_path) 