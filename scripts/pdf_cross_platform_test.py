#!/usr/bin/env python3
"""
PDF Cross-Platform Testing and Optimization Tool

This script generates test PDFs with different settings and optimization levels
to help with cross-platform compatibility testing and performance tuning.
"""

import os
import sys
import time
import argparse
import platform
import subprocess
from pathlib import Path
from datetime import datetime

# Add the src directory to the path
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir.parent))

from src.pdf_generation import (
    PDFReport, ReportConfig, ReportLibrary, ReportElement,
    TextElement, TableElement, ChartElement, ImageElement,
    HeaderElement, FooterElement, ListElement, PageBreakElement,
    StyleSheet, ColorScheme, TextStyle, TextAlignment
)


def generate_test_report(
    library: ReportLibrary,
    output_dir: Path,
    template: str = "standard",
    complexity: str = "medium",
    optimize: bool = False
) -> Path:
    """
    Generate a test PDF report with the specified settings.
    
    Args:
        library: The PDF library to use (ReportLab or FPDF)
        output_dir: Directory to save the generated PDF
        template: The type of template to use
        complexity: Complexity level affecting size and generation time
        optimize: Whether to apply optimization techniques
        
    Returns:
        Path to the generated PDF file
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure the report based on template and complexity
    pages = 1 if complexity == "low" else 5 if complexity == "medium" else 15
    elements_per_page = 3 if complexity == "low" else 8 if complexity == "medium" else 15
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{template}_{complexity}_{'opt' if optimize else 'std'}_{library.name.lower()}_{timestamp}.pdf"
    output_path = output_dir / filename
    
    # Set up report configuration
    config = ReportConfig(
        title=f"Cross-Platform Test: {template.capitalize()} Template",
        author="PDF Test Suite",
        subject=f"Testing PDF generation with {library.name}",
        keywords=["test", "pdf", "cross-platform", library.name.lower()],
        library=library,
        page_size="letter",  # Default for basic testing
        orientation="portrait"
    )
    
    # Apply optimization if requested
    if optimize:
        # These settings might help with file size and compatibility
        config.include_toc = False
        # Apply other optimization techniques based on the library
        if library == ReportLibrary.REPORTLAB:
            # ReportLab specific optimizations could go here
            pass
        else:  # FPDF
            # FPDF specific optimizations could go here
            pass
    
    # Create the report
    report = PDFReport(config)
    
    # Generate content based on the template
    if template == "standard":
        _generate_standard_template(report, pages, elements_per_page)
    elif template == "research":
        _generate_research_template(report, pages, elements_per_page)
    elif template == "technical":
        _generate_technical_template(report, pages, elements_per_page)
    else:
        raise ValueError(f"Unknown template type: {template}")
    
    # Generate the PDF
    start_time = time.time()
    report.generate(output_path)
    end_time = time.time()
    
    # Print generation stats
    generation_time = end_time - start_time
    file_size = output_path.stat().st_size / 1024  # Size in KB
    
    print(f"\nGenerated PDF: {output_path}")
    print(f"Generation Time: {generation_time:.2f} seconds")
    print(f"File Size: {file_size:.2f} KB")
    
    return output_path


def _generate_standard_template(report: PDFReport, pages: int, elements_per_page: int) -> None:
    """Generate a standard report template with basic elements."""
    # Add header and footer
    report.add_element(HeaderElement(
        text="Standard Test Report",
        height=50,
        include_date=True,
        include_page_number=True
    ))
    
    report.add_element(FooterElement(
        text=f"Generated on {datetime.now().strftime('%Y-%m-%d')}",
        height=30,
        include_page_number=True
    ))
    
    # Add content for each page
    for page in range(pages):
        # Add page break after first page
        if page > 0:
            report.add_element(PageBreakElement())
        
        # Add title for the page
        report.add_element(TextElement(
            text=f"Standard Test Page {page + 1}",
            x=72, y=72,
            style_name="heading1"
        ))
        
        # Add description text
        report.add_element(TextElement(
            text=f"This is a standard test page generated for cross-platform compatibility testing. "
                 f"Page {page + 1} of {pages}. This text should be readable in all PDF viewers, "
                 f"with proper font rendering and text wrapping. " * 2,
            x=72, y=110,
            width=450,
            style_name="body"
        ))
        
        # Add text elements
        for i in range(elements_per_page // 3):
            report.add_element(TextElement(
                text=f"Paragraph {i + 1}: Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                     f"Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. " * 2,
                x=72, y=170 + i * 40,
                width=450,
                style_name="body"
            ))
        
        # Add table on even pages
        if page % 2 == 0:
            table_data = [
                ["Header A", "Header B", "Header C"],
                ["Value 1", "Value 2", "Value 3"],
                ["Value 4", "Value 5", "Value 6"],
                ["Value 7", "Value 8", "Value 9"]
            ]
            
            report.add_element(TextElement(
                text="Sample Table:",
                x=72, y=300,
                style_name="heading2"
            ))
            
            report.add_element(TableElement(
                data=table_data,
                x=72, y=330,
                col_widths=[120, 150, 150],
                header=True
            ))
        
        # Add chart on odd pages
        if page % 2 == 1:
            chart_data = {
                "x_values": [2019, 2020, 2021, 2022, 2023],
                "y_series": {
                    "Series A": [10, 15, 13, 17, 20],
                    "Series B": [5, 10, 8, 12, 15],
                    "Series C": [8, 7, 11, 9, 12]
                }
            }
            
            report.add_element(TextElement(
                text="Sample Chart:",
                x=72, y=300,
                style_name="heading2"
            ))
            
            report.add_element(ChartElement(
                chart_type="line",
                data=chart_data,
                x=72, y=330,
                width=450,
                height=300,
                title="Data Trends Over Time",
                x_label="Year",
                y_label="Value"
            ))


def _generate_research_template(report: PDFReport, pages: int, elements_per_page: int) -> None:
    """Generate a research report template with academic styling."""
    # Add header and footer
    report.add_element(HeaderElement(
        text="Research Report Template",
        height=50,
        include_date=True,
        include_page_number=True
    ))
    
    report.add_element(FooterElement(
        text=f"Confidential Research Document",
        height=30,
        include_page_number=True
    ))
    
    # Add title page
    report.add_element(TextElement(
        text="Cross-Platform Compatibility Research",
        x=72, y=200,
        style_name="heading1"
    ))
    
    report.add_element(TextElement(
        text="A Study of PDF Generation Technologies",
        x=72, y=250,
        style_name="heading2"
    ))
    
    report.add_element(TextElement(
        text=f"Generated: {datetime.now().strftime('%B %d, %Y')}",
        x=72, y=320,
        style_name="body"
    ))
    
    report.add_element(TextElement(
        text="PDF Test Team",
        x=72, y=350,
        style_name="heading2"
    ))
    
    # Add abstract on the first page
    report.add_element(TextElement(
        text="Abstract",
        x=72, y=450,
        style_name="heading2"
    ))
    
    report.add_element(TextElement(
        text="This document tests the cross-platform compatibility of PDF generation "
             "libraries, with focus on text rendering, font embedding, chart generation, "
             "and general layout consistency across different PDF viewers. The study "
             "compares ReportLab and FPDF libraries for performance and output quality.",
        x=72, y=480,
        width=450,
        style_name="body"
    ))
    
    # Add content pages
    for page in range(1, pages):
        report.add_element(PageBreakElement())
        
        # Section title
        section_titles = [
            "Introduction", "Methodology", "Results", 
            "Discussion", "Conclusions", "References"
        ]
        
        section_idx = min(page - 1, len(section_titles) - 1)
        
        report.add_element(TextElement(
            text=f"{section_titles[section_idx]}",
            x=72, y=72,
            style_name="heading1"
        ))
        
        # Add content based on section
        if section_titles[section_idx] == "Introduction":
            report.add_element(TextElement(
                text="PDF (Portable Document Format) is a file format developed by Adobe in the 1990s "
                     "to present documents independently of application software, hardware, and "
                     "operating systems. Each PDF file encapsulates a complete description of a "
                     "fixed-layout document, including text, fonts, images, and 2D vector graphics.",
                x=72, y=120,
                width=450,
                style_name="body"
            ))
            
            report.add_element(TextElement(
                text="This study compares different PDF generation libraries for their compatibility "
                     "across platforms, focusing on:",
                x=72, y=200,
                width=450,
                style_name="body"
            ))
            
            report.add_element(ListElement(
                items=[
                    "Text rendering and font embedding",
                    "Table formatting and consistency",
                    "Chart and image integration",
                    "Performance and file size optimization",
                    "Cross-platform compatibility"
                ],
                x=92, y=240,
                width=430,
                numbered=False
            ))
        elif section_titles[section_idx] == "Methodology":
            report.add_element(TextElement(
                text="We generated identical reports using both ReportLab and FPDF libraries with "
                     "variations in content complexity, styling, and optimization settings. The "
                     "resulting PDFs were tested on the following platforms:",
                x=72, y=120,
                width=450,
                style_name="body"
            ))
            
            # Add table of test platforms
            platforms_data = [
                ["Platform", "Version", "PDF Viewer"],
                ["Windows", "10/11", "Adobe Reader, Edge, Chrome"],
                ["macOS", "Monterey/Ventura", "Preview, Safari, Chrome"],
                ["Linux", "Ubuntu 22.04", "Evince, Firefox, Chrome"],
                ["iOS", "16", "Books, Safari"],
                ["Android", "12/13", "Adobe Reader, Chrome"]
            ]
            
            report.add_element(TableElement(
                data=platforms_data,
                x=72, y=190,
                col_widths=[100, 100, 250],
                header=True
            ))
            
            report.add_element(TextElement(
                text="Test Procedure:",
                x=72, y=300,
                style_name="heading2"
            ))
            
            report.add_element(ListElement(
                items=[
                    "Generated PDFs with identical content using both libraries",
                    "Applied optimization techniques to a subset of the test documents",
                    "Distributed PDFs to testers across different platforms",
                    "Collected feedback on rendering quality, performance, and issues",
                    "Measured file sizes and generation performance"
                ],
                x=92, y=330,
                width=430,
                numbered=True
            ))
        elif section_titles[section_idx] == "Results":
            # Add results text
            report.add_element(TextElement(
                text="The performance testing yielded the following key metrics:",
                x=72, y=120,
                width=450,
                style_name="body"
            ))
            
            # Add sample chart for performance comparison
            perf_data = {
                "categories": ["Low Complexity", "Medium Complexity", "High Complexity"],
                "series": {
                    "ReportLab": [0.8, 2.5, 8.3],
                    "FPDF": [0.5, 1.7, 5.1]
                }
            }
            
            report.add_element(ChartElement(
                chart_type="bar",
                data=perf_data,
                x=72, y=150,
                width=450,
                height=250,
                title="Generation Time Comparison (seconds)",
                x_label="Complexity Level",
                y_label="Time (seconds)"
            ))
            
            # Add file size comparison
            size_data = {
                "categories": ["Low Complexity", "Medium Complexity", "High Complexity"],
                "series": {
                    "ReportLab": [125, 320, 780],
                    "FPDF": [95, 245, 610]
                }
            }
            
            report.add_element(ChartElement(
                chart_type="bar",
                data=size_data,
                x=72, y=430,
                width=450,
                height=250,
                title="File Size Comparison (KB)",
                x_label="Complexity Level",
                y_label="Size (KB)"
            ))
        else:
            # Generic content for other sections
            lorem_ipsum = (
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor "
                "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud "
                "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute "
                "irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
                "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia "
                "deserunt mollit anim id est laborum."
            )
            
            for i in range(elements_per_page // 2):
                report.add_element(TextElement(
                    text=lorem_ipsum,
                    x=72, y=120 + i * 140,
                    width=450,
                    style_name="body"
                ))


def _generate_technical_template(report: PDFReport, pages: int, elements_per_page: int) -> None:
    """Generate a technical report template with code samples and diagrams."""
    # Add header and footer
    report.add_element(HeaderElement(
        text="Technical Documentation",
        height=50,
        include_date=True,
        include_page_number=True
    ))
    
    report.add_element(FooterElement(
        text=f"PDF Generation System - Technical Report",
        height=30,
        include_page_number=True
    ))
    
    # Add title page
    report.add_element(TextElement(
        text="PDF Generation System",
        x=72, y=200,
        style_name="heading1"
    ))
    
    report.add_element(TextElement(
        text="Technical Implementation Guide",
        x=72, y=250,
        style_name="heading2"
    ))
    
    report.add_element(TextElement(
        text=f"Version 1.0 - {datetime.now().strftime('%B %d, %Y')}",
        x=72, y=320,
        style_name="body"
    ))
    
    # Add content pages
    for page in range(1, pages):
        report.add_element(PageBreakElement())
        
        # Technical sections
        tech_sections = [
            "System Architecture", "Class Hierarchy", "Implementation Details",
            "API Reference", "Performance Optimization", "Cross-Platform Considerations"
        ]
        
        section_idx = min(page - 1, len(tech_sections) - 1)
        
        report.add_element(TextElement(
            text=f"{tech_sections[section_idx]}",
            x=72, y=72,
            style_name="heading1"
        ))
        
        # Add content based on section
        if tech_sections[section_idx] == "System Architecture":
            report.add_element(TextElement(
                text="The PDF Generation System is designed with a layered architecture "
                     "that separates concerns and provides flexibility in implementation. "
                     "The main components are:",
                x=72, y=120,
                width=450,
                style_name="body"
            ))
            
            # Add technical list
            report.add_element(ListElement(
                items=[
                    "Core Abstract Classes (PDFReport, ReportElement, PDFGenerator)",
                    "Concrete Element Implementations (TextElement, TableElement, etc.)",
                    "Library-Specific Generators (ReportLabPDFGenerator, FPDFGenerator)",
                    "Formatting and Styling System (StyleSheet, TextStyle, etc.)",
                    "Template System (ReportTemplate, ResearchReportTemplate, etc.)"
                ],
                x=92, y=180,
                width=430,
                numbered=False
            ))
            
            # Add code sample
            code_text = """class PDFReport:
    \"\"\"Represents a complete PDF report.\"\"\"
    
    def __init__(self, config: ReportConfig):
        \"\"\"Initialize a PDF report with the given configuration.\"\"\"
        self.config = config
        self.elements: List[ReportElement] = []
        self.metadata: Dict[str, Any] = {...}
    
    def add_element(self, element: ReportElement) -> None:
        \"\"\"Add an element to the report.\"\"\"
        self.elements.append(element)
        
    def generate(self, output_path: Union[str, Path]) -> str:
        \"\"\"Generate the PDF report and save it to the specified path.\"\"\"
        # Create the appropriate PDF generator based on the config
        if self.config.library == ReportLibrary.REPORTLAB:
            generator = ReportLabPDFGenerator(self.config)
        else:  # FPDF
            generator = FPDFGenerator(self.config)
        
        # Generate the PDF
        return generator.generate(self, output_path)"""
            
            report.add_element(TextElement(
                text="Example Core Class Implementation:",
                x=72, y=300,
                style_name="heading2"
            ))
            
            report.add_element(TextElement(
                text=code_text,
                x=72, y=330,
                width=450,
                style_name="code"  # Assume we have a code style
            ))
        elif tech_sections[section_idx] == "Class Hierarchy":
            report.add_element(TextElement(
                text="The system uses a flexible class hierarchy with abstract base classes "
                     "and concrete implementations. This allows for different PDF generation "
                     "libraries to be used interchangeably through a common interface.",
                x=72, y=120,
                width=450,
                style_name="body"
            ))
            
            # Add some technical details about class relationships
            class_details = [
                ["Base Class", "Concrete Implementations", "Purpose"],
                ["PDFGenerator", "ReportLabPDFGenerator, FPDFGenerator", "Generate PDF output"],
                ["ReportElement", "TextElement, TableElement, ChartElement, etc.", "Define report content"],
                ["ReportTemplate", "ResearchReportTemplate, TechnicalReportTemplate", "Pre-defined layouts"],
                ["StyleSheet", "N/A (Singleton pattern)", "Define document styling"]
            ]
            
            report.add_element(TableElement(
                data=class_details,
                x=72, y=180,
                col_widths=[120, 180, 150],
                header=True
            ))
        else:
            # Add technical content placeholder for other sections
            report.add_element(TextElement(
                text="This section contains technical documentation related to "
                     f"the {tech_sections[section_idx]} of the PDF Generation System. "
                     "It would typically include detailed explanations, code samples, "
                     "diagrams, and implementation guidance.",
                x=72, y=120,
                width=450,
                style_name="body"
            ))
            
            # Add some code-like text for technical appearance
            tech_placeholder = """
# Sample implementation details
class ChartElement(ReportElement):
    def __init__(self, chart_type, data, x, y, width, height, **kwargs):
        super().__init__()
        self.chart_type = chart_type
        self.data = data
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.title = kwargs.get('title')
        self.x_label = kwargs.get('x_label')
        self.y_label = kwargs.get('y_label')
        
    def render(self, pdf_generator):
        pdf_generator.add_chart(
            self.chart_type, self.data, self.x, self.y,
            self.width, self.height,
            title=self.title,
            x_label=self.x_label,
            y_label=self.y_label
        )
"""
            
            report.add_element(TextElement(
                text=tech_placeholder,
                x=72, y=200,
                width=450,
                style_name="code"  # Assume we have a code style
            ))


def open_pdf(pdf_path: Path) -> None:
    """
    Attempt to open the PDF with the system's default viewer.
    
    Args:
        pdf_path: Path to the PDF file to open
    """
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(pdf_path)])
        elif system == "Windows":
            os.startfile(str(pdf_path))
        elif system == "Linux":
            subprocess.run(["xdg-open", str(pdf_path)])
        else:
            print(f"Unsupported platform for automatic opening: {system}")
            return
        
        print(f"Opened PDF with default viewer: {pdf_path}")
    except Exception as e:
        print(f"Error opening PDF: {e}")


def main():
    """Run the PDF cross-platform testing tool."""
    parser = argparse.ArgumentParser(
        description="Generate test PDFs for cross-platform compatibility testing."
    )
    
    parser.add_argument(
        "--library",
        type=str,
        choices=["reportlab", "fpdf", "both"],
        default="both",
        help="PDF library to use (default: both)"
    )
    
    parser.add_argument(
        "--template",
        type=str,
        choices=["standard", "research", "technical", "all"],
        default="standard",
        help="Template style to use (default: standard)"
    )
    
    parser.add_argument(
        "--complexity",
        type=str,
        choices=["low", "medium", "high", "all"],
        default="medium",
        help="Complexity level affecting size and generation time (default: medium)"
    )
    
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Apply optimization techniques to reduce file size"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/cross_platform_tests",
        help="Directory to save generated PDFs (default: outputs/cross_platform_tests)"
    )
    
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open generated PDFs with default viewer after creation"
    )
    
    args = parser.parse_args()
    
    # Determine which libraries to use
    libraries = []
    if args.library == "reportlab" or args.library == "both":
        libraries.append(ReportLibrary.REPORTLAB)
    if args.library == "fpdf" or args.library == "both":
        libraries.append(ReportLibrary.FPDF)
    
    # Determine which templates to use
    templates = []
    if args.template == "all":
        templates = ["standard", "research", "technical"]
    else:
        templates = [args.template]
    
    # Determine which complexity levels to use
    complexities = []
    if args.complexity == "all":
        complexities = ["low", "medium", "high"]
    else:
        complexities = [args.complexity]
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_pdfs = []
    
    # Generate PDFs with all combinations
    for library in libraries:
        for template in templates:
            for complexity in complexities:
                print(f"\nGenerating {template} template with {complexity} complexity using {library.name}...")
                
                output_path = generate_test_report(
                    library=library,
                    output_dir=output_dir,
                    template=template,
                    complexity=complexity,
                    optimize=args.optimize
                )
                
                generated_pdfs.append(output_path)
    
    # Print summary
    print(f"\nGenerated {len(generated_pdfs)} PDF files in {output_dir}")
    
    # Open PDFs if requested
    if args.open and generated_pdfs:
        print("\nOpening PDFs with default viewer...")
        for pdf_path in generated_pdfs:
            open_pdf(pdf_path)
    

if __name__ == "__main__":
    main() 