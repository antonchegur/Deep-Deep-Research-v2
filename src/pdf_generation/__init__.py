"""
PDF Generation Module

This module provides a flexible API for generating PDF reports with
tables, charts, and formatted text using various PDF libraries.
"""

from .pdf_base import (
    PDFReport, ReportConfig, PDFGenerator, ReportElement, 
    ReportLibrary
)

from .elements import (
    TextElement, TableElement, ChartElement, ImageElement,
    HeaderElement, FooterElement, ListElement, PageBreakElement
)

from .formatters import (
    TextFormatter, TableFormatter, ChartFormatter,
    ColorScheme, StyleSheet, TextStyle, TextAlignment
)

from .charts import (
    LineChart, BarChart, PieChart, ScatterPlot
)

from .reportlab_generator import ReportLabPDFGenerator
from .fpdf_generator import FPDFGenerator
from .report_service import ReportService, create_simple_report

__all__ = [
    # Base classes
    'PDFReport', 'ReportConfig', 'PDFGenerator', 'ReportElement',
    'ReportLibrary',
    
    # Elements
    'TextElement', 'TableElement', 'ChartElement', 'ImageElement',
    'HeaderElement', 'FooterElement', 'ListElement', 'PageBreakElement',
    
    # Formatters
    'TextFormatter', 'TableFormatter', 'ChartFormatter',
    'ColorScheme', 'StyleSheet', 'TextStyle', 'TextAlignment',
    
    # Charts
    'LineChart', 'BarChart', 'PieChart', 'ScatterPlot',
    
    # Generators
    'ReportLabPDFGenerator', 'FPDFGenerator',
    
    # High-level API
    'ReportService', 'create_simple_report'
] 