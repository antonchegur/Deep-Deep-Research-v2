"""
FPDF Implementation of PDF Generator

This module provides a concrete implementation of the PDFGenerator interface
using the FPDF2 library.
"""

import os
import datetime
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple, cast
import io

from fpdf import FPDF
import fpdf

from src.pdf_generation.pdf_base import PDFGenerator, PDFReport, ReportConfig
from src.pdf_generation.charts import LineChart, BarChart, PieChart, ScatterPlot
from src.pdf_generation.formatters import ChartStyle, TextStyle, TextAlignment


class FPDFGenerator(PDFGenerator):
    """FPDF implementation of the PDFGenerator interface."""
    
    def __init__(self, config: ReportConfig):
        """Initialize the FPDF generator with the given configuration."""
        super().__init__(config)
        self.pdf = None
        self.current_y = 0
        self.page_width = 0
        self.page_height = 0
        self._init_pdf()
        
    def _init_pdf(self):
        """Initialize the FPDF object with configuration settings."""
        # Set up the PDF document
        orientation = 'P' if self.config.orientation.lower() == 'portrait' else 'L'
        page_size = self.config.page_size.upper()
        
        # Create the PDF object
        self.pdf = FPDF(orientation=orientation, format=page_size)
        
        # Set document properties
        self.pdf.set_title(self.config.title)
        self.pdf.set_author(self.config.author)
        self.pdf.set_subject(self.config.subject)
        self.pdf.set_creator("Deep Deep Research v2")
        
        # Get page dimensions
        self.page_width = self.pdf.w
        self.page_height = self.pdf.h
        
        # Set default font
        self.pdf.set_font(self.config.font_family, size=12)
        
        # Add default header/footer if configured
        if self.config.header_text or self.config.include_page_numbers:
            # Using FPDF's header/footer mechanism would go here
            # This would normally involve subclassing FPDF and overriding header() and footer()
            pass
        
        # Add first page
        self.pdf.add_page()
        self.current_y = self.config.margins.get("top", 1.0 * 25.4) # in mm
        
    def generate(self, report: PDFReport, output_path: Union[str, Path]) -> str:
        """Generate a PDF from a report and save it to the specified path."""
        output_path = Path(output_path)
        
        # Make sure PDF is initialized
        if self.pdf is None:
            self._init_pdf()
        
        # Reset position
        self.pdf.set_y(self.current_y)
        
        # Add title if available
        if self.config.title:
            self.pdf.set_font(self.config.font_family, 'B', 24)
            self.pdf.cell(0, 15, self.config.title, align='C')
            self.pdf.ln(20)
            self.current_y = self.pdf.get_y()
        
        # Process all report elements
        for element in report.elements:
            # The render method of each element will call the appropriate methods
            # of this generator to render the element to the PDF
            element.render(self)
        
        # Save the PDF
        self.pdf.output(str(output_path))
        
        return str(output_path)
        
    def add_page(self) -> None:
        """Add a new page to the PDF."""
        if self.pdf:
            self.pdf.add_page()
            self.current_y = self.pdf.t_margin
        
    def add_text(self, text: str, x: float, y: float, width: Optional[float] = None, 
                 text_style: Optional[TextStyle] = None,
                 font_size: Optional[int] = None, 
                 font_name: Optional[str] = None, 
                 color: Optional[str] = None, 
                 align: Optional[str] = None,
                 line_spacing: Optional[float] = None
                 ) -> None:
        """Add text to the PDF using FPDF, applying styles from TextStyle."""
        if not self.pdf:
            raise ValueError("PDF object not initialized. Call generate first.")

        # Determine actual style to use
        effective_style = text_style if text_style else self.config.stylesheet.body
        
        # Apply legacy overrides if provided
        fs = font_size if font_size is not None else effective_style.font_size
        ff = font_name if font_name is not None else effective_style.font_family
        clr = color if color is not None else effective_style.color
        # FPDF alignment: L, C, R, J
        al = align[0].upper() if align else effective_style.alignment.value[0].upper()
        ls = line_spacing if line_spacing is not None else effective_style.line_spacing
        
        fpdf_style = ""
        if effective_style.bold: fpdf_style += "B"
        if effective_style.italic: fpdf_style += "I"
        if effective_style.underline: fpdf_style += "U"
        
        self.pdf.set_font(ff, style=fpdf_style, size=fs)
        
        r, g, b = self._parse_color(clr) # _parse_color returns 0-1, FPDF wants 0-255
        self.pdf.set_text_color(int(r*255), int(g*255), int(b*255))
        
        self.pdf.set_xy(x, y)
        
        # FPDF uses cell height which is font_size * line_spacing (approx)
        # For MultiCell, h is line height.
        effective_line_height = fs * ls

        if width:
            self.pdf.multi_cell(w=width, h=effective_line_height, txt=text, align=al)
            # Update current_y after multi_cell, FPDF does this automatically if auto_page_break is on.
            # If not, we might need to track y manually if flowing text.
            # For now, assuming elements are placed absolutely or FPDF handles flow.
        else:
            self.pdf.cell(w=0, h=effective_line_height, txt=text, align=al, ln=1) # ln=1 moves to next line
    
    def add_table(self, data: List[List[Any]], x: float, y: float, 
                 col_widths: List[float] = None, header: bool = True) -> None:
        """Add a table to the PDF."""
        if not self.pdf:
            raise ValueError("PDF not initialized. Call generate first.")
        
        # Save current position
        current_x, current_y = self.pdf.get_x(), self.pdf.get_y()
        
        # Set the position
        self.pdf.set_xy(x, y)
        
        # Calculate column widths if not provided
        if not col_widths and data and data[0]:
            available_width = self.page_width - self.pdf.l_margin - self.pdf.r_margin
            col_widths = [available_width / len(data[0])] * len(data[0])
        
        # Define colors
        header_bg = (232, 240, 254)  # Light blue
        header_text = (0, 0, 0)      # Black
        even_row_bg = (248, 249, 250)  # Light gray
        odd_row_bg = (255, 255, 255)   # White
        border_color = (218, 220, 224)  # Medium gray
        
        # Add table
        line_height = 10
        
        for i, row in enumerate(data):
            # Set background color
            if i == 0 and header:
                self.pdf.set_fill_color(*header_bg)
                self.pdf.set_text_color(*header_text)
                if header:
                    self.pdf.set_font(self.config.font_family, 'B', 12)
            else:
                if i % 2 == 0:
                    self.pdf.set_fill_color(*even_row_bg)
                else:
                    self.pdf.set_fill_color(*odd_row_bg)
                self.pdf.set_text_color(0, 0, 0)
                self.pdf.set_font(self.config.font_family, '', 10)
            
            # Each cell in the row
            for j, cell in enumerate(row):
                width = col_widths[j] if j < len(col_widths) else 30
                self.pdf.cell(width, line_height, str(cell), border=1, fill=True)
                
            self.pdf.ln(line_height)
        
        # Update current Y position
        self.current_y = self.pdf.get_y()
        
        # Restore position
        self.pdf.set_xy(current_x, current_y)
    
    def add_image(self, image_path: Union[str, Path], x: float, y: float, 
                 width: float = None, height: float = None) -> None:
        """Add an image to the PDF."""
        if not self.pdf:
            raise ValueError("PDF not initialized. Call generate first.")
        
        # Save current position
        current_x, current_y = self.pdf.get_x(), self.pdf.get_y()
        
        # Convert Path to string
        image_path_str = str(image_path)
        
        # Add the image
        # FPDF will handle preserving aspect ratio if we only specify one dimension
        self.pdf.image(image_path_str, x=x, y=y, w=width, h=height)
        
        # Update current Y position - this is an approximation
        if height:
            self.current_y = y + height
        
        # Restore position
        self.pdf.set_xy(current_x, current_y)
    
    def add_chart(self, chart_type: str, data: Any, x: float, y: float, 
                 width: float, height: float,
                 title: Optional[str] = None,
                 x_label: Optional[str] = None,
                 y_label: Optional[str] = None,
                 legend: bool = True,
                 style: Optional[ChartStyle] = None
                 ) -> None:
        """Add a chart to the PDF."""
        if not self.pdf:
            raise ValueError("PDF not initialized. Call generate first.")
        
        # Create a temporary file to save the chart
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        chart_style = style if style is not None else ChartStyle()

        try:
            # Create the appropriate chart type
            # The 'data' dictionary now contains only the core plot data
            if chart_type == 'line':
                x_values = data.get('x_values', [])
                y_series = data.get('y_series', {})
                chart = LineChart(title=title, x_label=x_label, y_label=y_label, legend=legend, style=chart_style)
                chart.create_chart(x_values, y_series)
            elif chart_type == 'bar':
                categories = data.get('categories', [])
                series = data.get('series', {})
                stacked = data.get('stacked', False)
                horizontal = data.get('horizontal', False)
                chart = BarChart(title=title, x_label=x_label, y_label=y_label, legend=legend, style=chart_style)
                chart.create_chart(categories, series, stacked, horizontal)
            elif chart_type == 'pie':
                labels = data.get('labels', [])
                values = data.get('values', [])
                explode = data.get('explode', None)
                chart = PieChart(title=title, legend=legend, style=chart_style)
                chart.create_chart(labels, values, explode)
            elif chart_type == 'scatter':
                x_values = data.get('x_values', [])
                y_values = data.get('y_values', [])
                point_labels = data.get('labels', None) # Renamed to avoid conflict
                sizes = data.get('sizes', None)
                chart = ScatterPlot(title=title, x_label=x_label, y_label=y_label, legend=legend, style=chart_style)
                chart.create_chart(x_values, y_values, point_labels, sizes)
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")
            
            # Save the chart to the temporary file
            chart.save_to_file(tmp_path)
            
            # Add the chart image to the PDF
            self.add_image(tmp_path, x, y, width, height)
            
        finally:
            # Clean up the temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def _parse_color(self, color_val: Optional[str]) -> Tuple[float, float, float]:
        """Parse a color string (hex or named) to RGB components (0-255)."""
        if color_val and color_val.startswith('#'):
            # Hex color
            r = int(color_val[1:3], 16)
            g = int(color_val[3:5], 16)
            b = int(color_val[5:7], 16)
            return (r/255, g/255, b/255)
        else:
            # Named color - this is a simplification; in reality, we would
            # have a mapping of color names to RGB values
            # For now, return black as default
            return (0, 0, 0) 