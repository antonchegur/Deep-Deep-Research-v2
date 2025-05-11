"""
Report Service Module

This module provides integration between the PDF report generation system and 
the research system, allowing for the generation of complete research reports
with proper references and bibliography.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, cast
from pathlib import Path
import datetime

from src.pdf_generation import (
    PDFReport, ReportConfig, ReportLibrary, ReportElement,
    TextElement, TableElement, ChartElement, ImageElement,
    HeaderElement, FooterElement, ListElement, PageBreakElement,
    StyleSheet, ColorScheme, TextStyle, TextAlignment
)
from src.pdf_generation.report_templates import (
    ResearchReportTemplate, ResearchResultsReport
)

# Import reference management when available
try:
    from src.research.reference_management import ReferenceManager
    REFERENCE_MANAGER_AVAILABLE = True
except ImportError:
    REFERENCE_MANAGER_AVAILABLE = False
    logging.warning("Reference Management System not available. Bibliography generation will be limited.")


class ReportService:
    """Service for generating PDF reports from research results."""
    
    def __init__(self, 
                 template_name: str = "modern",
                 library: ReportLibrary = ReportLibrary.REPORTLAB):
        """Initialize the report service.
        
        Args:
            template_name: Name of the template to use ("modern", "academic", "business")
            library: PDF library to use
        """
        self.template_name = template_name
        self.library = library
        self.ref_manager = None
        
        # If reference manager is available, initialize it
        if REFERENCE_MANAGER_AVAILABLE:
            from src.research.reference_management import ReferenceManager
            from src.research.reference_management import CitationStyle
            
            # Default to APA style
            self.ref_manager = ReferenceManager(style=CitationStyle.APA)
    
    def _get_color_scheme(self, template_name: str) -> ColorScheme:
        """Get color scheme based on template name."""
        if template_name == "modern":
            return ColorScheme(
                primary="#1a73e8",
                secondary="#4285f4",
                accent="#fbbc04",
                text="#202124",
                background="#ffffff",
                heading="#1a73e8"
            )
        elif template_name == "academic":
            return ColorScheme(
                primary="#8c1515",  # Stanford Red
                secondary="#2e2d29",
                accent="#b83a4b",
                text="#2e2d29",
                background="#ffffff",
                heading="#8c1515"
            )
        elif template_name == "business":
            return ColorScheme(
                primary="#0d2240",  # Navy blue
                secondary="#384967",
                accent="#f4b41a",
                text="#333333",
                background="#ffffff",
                heading="#0d2240"
            )
        else:
            # Default to modern
            return ColorScheme()
    
    def _prepare_stylesheet(self, template_name: str) -> StyleSheet:
        """Prepare a stylesheet based on the template name."""
        color_scheme = self._get_color_scheme(template_name)
        
        if template_name == "modern":
            stylesheet = StyleSheet()
            stylesheet.apply_color_scheme(color_scheme)
            stylesheet.title = TextStyle(
                font_family="Helvetica-Bold",
                font_size=24,
                color=color_scheme.primary,
                alignment=TextAlignment.CENTER,
                line_spacing=1.2,
                bold=True
            )
            return stylesheet
        
        elif template_name == "academic":
            stylesheet = StyleSheet()
            stylesheet.apply_color_scheme(color_scheme)
            stylesheet.body = TextStyle(
                font_family="Times-Roman",
                font_size=12,
                color=color_scheme.text,
                alignment=TextAlignment.JUSTIFY,
                line_spacing=1.5
            )
            stylesheet.heading1 = TextStyle(
                font_family="Times-Bold",
                font_size=18,
                color=color_scheme.heading,
                alignment=TextAlignment.LEFT,
                line_spacing=1.2,
                bold=True
            )
            return stylesheet
        
        elif template_name == "business":
            stylesheet = StyleSheet()
            stylesheet.apply_color_scheme(color_scheme)
            stylesheet.body = TextStyle(
                font_family="Helvetica",
                font_size=11,
                color=color_scheme.text,
                alignment=TextAlignment.LEFT,
                line_spacing=1.2
            )
            stylesheet.heading1 = TextStyle(
                font_family="Helvetica-Bold",
                font_size=16,
                color=color_scheme.heading,
                alignment=TextAlignment.LEFT,
                line_spacing=1.2,
                bold=True
            )
            return stylesheet
        
        # Default stylesheet
        return StyleSheet()
    
    def generate_report_from_research_results(self, 
                                              research_results: Dict[str, Any],
                                              output_path: Union[str, Path],
                                              title: Optional[str] = None) -> str:
        """Generate a PDF report from research results.
        
        Args:
            research_results: Dictionary containing research results
            output_path: Path where the PDF report should be saved
            title: Optional title for the report (defaults to research query)
            
        Returns:
            Path to the generated PDF report
        """
        # Default title to the research query
        if title is None and "query" in research_results:
            title = f"Research Report: {research_results['query']}"
        elif title is None:
            title = "Research Report"
        
        # Create configuration with appropriate stylesheet
        config = ReportConfig(
            title=title,
            library=self.library,
            stylesheet=self._prepare_stylesheet(self.template_name)
        )
        
        # Process bibliography if reference manager is available
        if self.ref_manager and "sources" in research_results:
            try:
                # Register all sources with the reference manager
                for source in research_results["sources"]:
                    self.ref_manager.add_reference(source)
                
                # Generate bibliography and add it to research_results
                bibliography = self.ref_manager.generate_bibliography()
                research_results["bibliography"] = bibliography.references
            except Exception as e:
                logging.error(f"Error generating bibliography: {e}")
                # Create empty bibliography if there's an error
                research_results["bibliography"] = []
        
        # Create appropriate template based on template_name
        if self.template_name == "academic":
            # Use ResearchReportTemplate for academic reports
            template = ResearchReportTemplate(
                title=title,
                library=self.library
            )
            
            # Apply custom stylesheet to template
            template.config.stylesheet = config.stylesheet
            
            # Add content using ResearchReportTemplate methods
            if isinstance(research_results, dict):
                # Add title page with optional subtitle
                subtitle = f"Research on: {research_results['query']}" if "query" in research_results else None
                template.add_title_page(subtitle=subtitle)
                
                # Add executive summary if summary is present
                if "summary" in research_results:
                    template.add_executive_summary(research_results["summary"])
                
                # Add table of contents
                if template.config.include_toc:
                    template.add_table_of_contents()
                
                # Add findings as sections
                if "findings" in research_results:
                    for i, finding in enumerate(research_results["findings"]):
                        if isinstance(finding, dict) and "title" in finding and "content" in finding:
                            template.add_section(finding["title"], finding["content"], level=1)
                        elif isinstance(finding, str):
                            template.add_section(f"Finding {i+1}", finding, level=1)
                
                # Add conclusion if present
                if "conclusion" in research_results:
                    template.add_conclusion(research_results["conclusion"])
                
                # Add sources as appendix
                if "sources" in research_results:
                    sources_text = "References:\n\n"
                    for i, source in enumerate(research_results["sources"], 1):
                        title = source.get("title", "Untitled Source")
                        source_name = source.get("source_name", "Unknown Source")
                        url = source.get("url", "")
                        sources_text += f"{i}. {title}\n   {source_name}\n   {url}\n\n"
                    
                    template.add_appendix("References", sources_text)
        else:
            # For modern and business, use ResearchResultsReport which has different methods
            template = ResearchResultsReport(
                title=title,
                library=self.library
            )
            
            # Apply custom stylesheet to template
            template.config.stylesheet = config.stylesheet
            
            # If we have research_results as dictionary, use it directly with ResearchResultsReport methods
            if isinstance(research_results, dict):
                # Add sections based on the research results
                template.add_title_page(research_results)
                template.add_summary_section(research_results)
                template.add_findings_section(research_results)
                
                # Add sources section with bibliography
                template.add_sources_section(research_results)
                
                # Add conclusion section if present
                if "conclusion" in research_results:
                    template.add_conclusion_section(research_results)
        
        # Generate the PDF
        return template.generate(output_path)
    
    def generate_report_from_json(self, 
                                  json_path: Union[str, Path],
                                  output_path: Union[str, Path],
                                  title: Optional[str] = None) -> str:
        """Generate a PDF report from a JSON file containing research results.
        
        Args:
            json_path: Path to the JSON file containing research results
            output_path: Path where the PDF report should be saved
            title: Optional title for the report
            
        Returns:
            Path to the generated PDF report
        """
        # Load research results from JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            research_results = json.load(f)
        
        # Generate report from research results
        return self.generate_report_from_research_results(
            research_results=research_results,
            output_path=output_path,
            title=title
        )


def create_simple_report(
    title: str,
    content: str,
    output_path: Union[str, Path],
    author: str = "Deep Deep Research v2",
    include_date: bool = True,
    library: ReportLibrary = ReportLibrary.REPORTLAB
) -> str:
    """Create a simple PDF report with a title and content.
    
    Args:
        title: Report title
        content: Report content
        output_path: Path where the PDF should be saved
        author: Report author
        include_date: Whether to include the current date
        library: PDF library to use
        
    Returns:
        Path to the generated PDF report
    """
    config = ReportConfig(
        title=title,
        author=author,
        library=library
    )
    
    report = PDFReport(config)
    
    # Add title
    report.add_element(TextElement(
        text=title,
        x=72, y=72,
        style_name="heading1"
    ))
    
    # Add date if requested
    if include_date:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        report.add_element(TextElement(
            text=f"Generated on: {today}",
            x=72, y=100,
            style_name="heading2"
        ))
    
    # Add content
    report.add_element(TextElement(
        text=content,
        x=72, y=130,
        width=450,
        style_name="body"
    ))
    
    # Generate the PDF
    return report.generate(output_path) 