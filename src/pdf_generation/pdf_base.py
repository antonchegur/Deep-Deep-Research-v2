"""
Base classes for PDF report generation.

This module provides abstract base classes and core functionality
for the PDF report generation system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Any, Optional, Union, Tuple
import os
from pathlib import Path
import datetime
import uuid

# For type hints
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from src.pdf_generation.formatters import StyleSheet, ColorScheme


class ReportLibrary(Enum):
    """Enum representing the available PDF generation libraries."""
    REPORTLAB = "REPORTLAB"
    FPDF = "FPDF"


@dataclass
class ReportConfig:
    """Configuration for PDF report generation."""
    title: str
    author: str = "Deep Deep Research v2"
    subject: str = "Research Report"
    keywords: List[str] = field(default_factory=list)
    page_size: str = "letter"  # "letter", "A4", etc.
    orientation: str = "portrait"  # "portrait" or "landscape"
    margins: Dict[str, float] = field(default_factory=lambda: {"left": 72, "right": 72, "top": 72, "bottom": 72})
    header_text: Optional[str] = None
    footer_text: Optional[str] = None
    include_toc: bool = True
    include_page_numbers: bool = True
    color_scheme: Dict[str, str] = field(default_factory=lambda: {
        "primary": "#1a73e8",
        "secondary": "#4285f4",
        "accent": "#fbbc04",
        "text": "#202124",
        "background": "#ffffff"
    })
    font_family: str = "Helvetica"
    library: ReportLibrary = ReportLibrary.REPORTLAB
    stylesheet: StyleSheet = field(default_factory=StyleSheet)
    
    def __post_init__(self):
        # Apply the initial color scheme and font family from StyleSheet defaults if not overridden
        # Or, allow ReportConfig to override StyleSheet's defaults
        initial_color_scheme = ColorScheme(
            primary=self.stylesheet.color_scheme.primary, # Example of how to pass specific colors
            text=self.stylesheet.color_scheme.text
            # ... potentially other colors if ReportConfig had direct color fields
        )
        self.stylesheet.apply_color_scheme(initial_color_scheme)
        # The font_family in individual TextStyle objects within StyleSheet will take precedence.
        # If a global font_family was intended for ReportConfig, it would need to be propagated
        # to the TextStyle objects within the stylesheet here, e.g.:
        # self.stylesheet.body.font_family = self.font_family # if self.font_family existed

    def get_page_size_tuple(self) -> Tuple[float, float]:
        """Convert page size string to a tuple of width and height."""
        sizes = {
            "letter": (612, 792),  # 8.5 x 11 inches
            "a4": (595, 842),      # 210 x 297 mm
            "legal": (612, 1008),  # 8.5 x 14 inches
            "tabloid": (792, 1224) # 11 x 17 inches
        }
        
        size = sizes.get(self.page_size.lower(), sizes["letter"])
        
        # Swap dimensions if landscape
        if self.orientation.lower() == "landscape":
            return (size[1], size[0])
        return size
    
    def get_reportlab_pagesize(self):
        """Get the corresponding ReportLab pagesize."""
        page_sizes = {
            "letter": letter,
            "a4": A4
        }
        
        # Default to letter if not found
        size = page_sizes.get(self.page_size.lower(), letter)
        
        # Return the correct orientation
        if self.orientation.lower() == "landscape":
            return size[1], size[0]
        return size


class ReportElement(ABC):
    """Base class for all report elements."""
    
    def __init__(self, element_id: Optional[str] = None):
        """Initialize a report element with an optional ID."""
        self.element_id = element_id or str(uuid.uuid4())
    
    @abstractmethod
    def render(self, pdf_generator: 'PDFGenerator') -> None:
        """Render the element to the PDF."""
        pass
    
    def __repr__(self) -> str:
        """String representation of the element."""
        return f"{self.__class__.__name__}(id={self.element_id})"


class PDFReport:
    """Represents a complete PDF report."""
    
    def __init__(self, config: ReportConfig):
        """Initialize a PDF report with the given configuration."""
        self.config = config
        self.elements: List[ReportElement] = []
        self.metadata: Dict[str, Any] = {
            "creation_date": datetime.datetime.now(),
            "version": "1.0",
            "generated_by": "Deep Deep Research v2"
        }
    
    def add_element(self, element: ReportElement) -> None:
        """Add an element to the report."""
        self.elements.append(element)
        
    def add_elements(self, elements: List[ReportElement]) -> None:
        """Add multiple elements to the report."""
        self.elements.extend(elements)
    
    def generate(self, output_path: Union[str, Path]) -> str:
        """Generate the PDF report and save it to the specified path."""
        # Create the appropriate PDF generator based on the config
        if self.config.library == ReportLibrary.REPORTLAB:
            from src.pdf_generation.reportlab_generator import ReportLabPDFGenerator
            generator = ReportLabPDFGenerator(self.config)
        else:  # FPDF
            from src.pdf_generation.fpdf_generator import FPDFGenerator
            generator = FPDFGenerator(self.config)
        
        # Generate the PDF
        return generator.generate(self, output_path)
    
    def update_metadata(self, key: str, value: Any) -> None:
        """Update a metadata value."""
        self.metadata[key] = value


class PDFGenerator(ABC):
    """Abstract base class for PDF generation implementations."""
    
    def __init__(self, config: ReportConfig):
        """Initialize with the given configuration."""
        self.config = config
    
    @abstractmethod
    def generate(self, report: PDFReport, output_path: Union[str, Path]) -> str:
        """Generate a PDF from a report and save it to the specified path."""
        pass
    
    @abstractmethod
    def add_page(self) -> None:
        """Add a new page to the PDF."""
        pass
    
    @abstractmethod
    def add_text(self, 
                 text: str, 
                 x: float, 
                 y: float, 
                 width: Optional[float] = None, 
                 text_style: Optional[Any] = None, # Optional[TextStyle]
                 # Deprecated direct style attributes:
                 font_size: Optional[int] = None, 
                 font_name: Optional[str] = None, 
                 color: Optional[str] = None, 
                 align: Optional[str] = None,
                 line_spacing: Optional[float] = None) -> None:
        """Add text to the PDF.

        Args:
            text: The text content to display.
            x: X-coordinate position.
            y: Y-coordinate position.
            width: Optional width for the text area (for wrapping).
            text_style: Optional TextStyle object containing all styling information.
            font_size: (Deprecated) Font size. Use text_style.
            font_name: (Deprecated) Font name. Use text_style.
            color: (Deprecated) Text color. Use text_style.
            align: (Deprecated) Text alignment. Use text_style.
            line_spacing: (Deprecated) Line spacing. Use text_style.
        """
        pass
    
    @abstractmethod
    def add_table(self, data: List[List[Any]], x: float, y: float, 
                  col_widths: List[float] = None, header: bool = True) -> None:
        """Add a table to the PDF."""
        pass
    
    @abstractmethod
    def add_image(self, image_path: Union[str, Path], x: float, y: float, 
                  width: float = None, height: float = None) -> None:
        """Add an image to the PDF."""
        pass
    
    @abstractmethod
    def add_chart(self, 
                  chart_type: str, 
                  data: Any,  # Core plot data (e.g., x_values, y_series)
                  x: float, 
                  y: float, 
                  width: float, 
                  height: float,
                  title: Optional[str] = None,
                  x_label: Optional[str] = None,
                  y_label: Optional[str] = None,
                  legend: bool = True,
                  style: Optional[Any] = None) -> None: # style: Optional[ChartStyle] - forward ref issue
        """Add a chart to the PDF.
        
        Args:
            chart_type: Type of chart (e.g., 'line', 'bar').
            data: Core data for the chart (e.g., x_values, y_series).
            x: X-coordinate position.
            y: Y-coordinate position.
            width: Width of the chart.
            height: Height of the chart.
            title: Optional chart title.
            x_label: Optional X-axis label.
            y_label: Optional Y-axis label.
            legend: Whether to display a legend.
            style: Optional ChartStyle object for styling.
        """
        pass 