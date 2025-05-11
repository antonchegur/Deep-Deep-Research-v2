"""
PDF Formatters Module

This module provides classes for styling and formatting PDF report elements
such as text, tables, and charts.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union, Tuple, Any


class TextAlignment(Enum):
    """Text alignment options."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


@dataclass
class ColorScheme:
    """Defines a color scheme for a report."""
    primary: str = "#1a73e8"     # Google Blue
    secondary: str = "#4285f4"   # Lighter blue
    accent: str = "#fbbc04"      # Yellow
    text: str = "#202124"        # Dark gray
    background: str = "#ffffff"  # White
    heading: str = "#1967d2"     # Darker blue
    table_header: str = "#e8f0fe"# Light blue
    table_even_row: str = "#f8f9fa" # Light gray
    table_odd_row: str = "#ffffff"  # White
    table_border: str = "#dadce0"   # Medium gray
    chart_colors: List[str] = field(default_factory=lambda: [
        "#4285f4",  # Blue
        "#ea4335",  # Red
        "#fbbc04",  # Yellow
        "#34a853",  # Green
        "#8ab4f8",  # Light blue
        "#f6aea9",  # Light red
        "#fde293",  # Light yellow
        "#a8dab5",  # Light green
        "#1967d2",  # Dark blue 
        "#c5221f",  # Dark red
        "#f29900",  # Dark yellow
        "#188038"   # Dark green
    ])
    
    def get_color(self, name: str) -> str:
        """Get a color by name from the scheme."""
        if hasattr(self, name):
            return getattr(self, name)
        return self.text  # Default to text color


@dataclass
class TextStyle:
    """Style properties for text elements."""
    font_family: str = "Helvetica"
    font_size: int = 12
    color: str = "#202124"  # Dark gray
    alignment: TextAlignment = TextAlignment.LEFT
    line_spacing: float = 1.2
    bold: bool = False
    italic: bool = False
    underline: bool = False
    paragraph_spacing: float = 6.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for PDF library consumption."""
        return {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "color": self.color,
            "alignment": self.alignment.value,
            "line_spacing": self.line_spacing,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "paragraph_spacing": self.paragraph_spacing
        }


@dataclass
class TableStyle:
    """Style properties for table elements."""
    header_background: str = "#e8f0fe"  # Light blue
    header_text_color: str = "#202124"  # Dark gray
    even_row_background: str = "#f8f9fa"  # Light gray
    odd_row_background: str = "#ffffff"  # White
    text_color: str = "#202124"  # Dark gray
    border_color: str = "#dadce0"  # Medium gray
    border_width: float = 0.5
    header_font_size: int = 12
    cell_font_size: int = 10
    font_family: str = "Helvetica"
    header_bold: bool = True
    padding: float = 5.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for PDF library consumption."""
        return {
            "header_background": self.header_background,
            "header_text_color": self.header_text_color,
            "even_row_background": self.even_row_background,
            "odd_row_background": self.odd_row_background,
            "text_color": self.text_color,
            "border_color": self.border_color,
            "border_width": self.border_width,
            "header_font_size": self.header_font_size,
            "cell_font_size": self.cell_font_size,
            "font_family": self.font_family,
            "header_bold": self.header_bold,
            "padding": self.padding
        }


@dataclass
class ChartStyle:
    """Style properties for chart elements."""
    colors: List[str] = field(default_factory=lambda: [
        "#4285f4", "#ea4335", "#fbbc04", "#34a853",  # Google colors
        "#8ab4f8", "#f6aea9", "#fde293", "#a8dab5"   # Lighter versions
    ])
    background_color: str = "#ffffff"  # White
    title_font_size: int = 14
    axis_font_size: int = 10
    tick_font_size: int = 8
    font_family: str = "Helvetica"
    grid_color: str = "#f1f3f4"  # Very light gray
    line_width: float = 2.0
    point_size: float = 5.0
    show_grid: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for PDF library consumption."""
        return {
            "colors": self.colors,
            "background_color": self.background_color,
            "title_font_size": self.title_font_size,
            "axis_font_size": self.axis_font_size,
            "tick_font_size": self.tick_font_size,
            "font_family": self.font_family,
            "grid_color": self.grid_color,
            "line_width": self.line_width,
            "point_size": self.point_size,
            "show_grid": self.show_grid
        }


@dataclass
class StyleSheet:
    """A complete set of styles for a PDF report."""
    
    color_scheme: ColorScheme = field(default_factory=ColorScheme)
    
    # Text styles for different purposes
    heading1: TextStyle = field(default_factory=lambda: TextStyle(
        font_size=24, bold=True, paragraph_spacing=12.0
    ))
    
    heading2: TextStyle = field(default_factory=lambda: TextStyle(
        font_size=18, bold=True, paragraph_spacing=10.0
    ))
    
    heading3: TextStyle = field(default_factory=lambda: TextStyle(
        font_size=14, bold=True, paragraph_spacing=8.0
    ))
    
    body: TextStyle = field(default_factory=TextStyle)
    
    caption: TextStyle = field(default_factory=lambda: TextStyle(
        font_size=10, italic=True, color="#5f6368"  # Gray
    ))
    
    table: TableStyle = field(default_factory=TableStyle)
    
    chart: ChartStyle = field(default_factory=ChartStyle)
    
    def apply_color_scheme(self, color_scheme: ColorScheme) -> None:
        """Update all styles to use colors from the provided color scheme."""
        self.color_scheme = color_scheme
        
        # Update text styles
        self.heading1.color = color_scheme.heading
        self.heading2.color = color_scheme.heading
        self.heading3.color = color_scheme.heading
        self.body.color = color_scheme.text
        
        # Update table styles
        self.table.header_background = color_scheme.table_header
        self.table.header_text_color = color_scheme.text
        self.table.even_row_background = color_scheme.table_even_row
        self.table.odd_row_background = color_scheme.table_odd_row
        self.table.text_color = color_scheme.text
        self.table.border_color = color_scheme.table_border
        
        # Update chart styles
        self.chart.colors = color_scheme.chart_colors
        self.chart.grid_color = color_scheme.table_border
        
    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert the entire stylesheet to a dictionary."""
        return {
            "color_scheme": {k: v for k, v in self.color_scheme.__dict__.items() if not k.startswith("_")},
            "heading1": self.heading1.to_dict(),
            "heading2": self.heading2.to_dict(),
            "heading3": self.heading3.to_dict(),
            "body": self.body.to_dict(),
            "caption": self.caption.to_dict(),
            "table": self.table.to_dict(),
            "chart": self.chart.to_dict()
        }


class TextFormatter:
    """Utility for formatting text elements."""
    
    @staticmethod
    def format_paragraph(
        text: str, 
        style: TextStyle = None,
        width: Optional[float] = None,
        max_lines: Optional[int] = None,
        ellipsis: bool = True
    ) -> str:
        """Format a paragraph of text according to style and constraints."""
        # This is a placeholder implementation
        # In a real implementation, this would handle text wrapping, truncation, etc.
        # based on the PDF library being used
        return text
    
    @staticmethod
    def format_heading(
        text: str,
        level: int = 1,
        stylesheet: StyleSheet = None
    ) -> Dict[str, Any]:
        """Format text as a heading with the appropriate style."""
        if stylesheet is None:
            stylesheet = StyleSheet()
        
        style = {
            1: stylesheet.heading1,
            2: stylesheet.heading2,
            3: stylesheet.heading3
        }.get(level, stylesheet.body)
        
        return {
            "text": text,
            "style": style.to_dict()
        }


class TableFormatter:
    """Utility for formatting table elements."""
    
    @staticmethod
    def format_data(
        data: List[List[Any]],
        style: TableStyle = None,
        col_formats: Optional[List[str]] = None
    ) -> List[List[str]]:
        """Format table data according to column formats."""
        if style is None:
            style = TableStyle()
        
        formatted_data = []
        
        for row in data:
            formatted_row = []
            for i, cell in enumerate(row):
                # Apply column-specific formatting if provided
                if col_formats and i < len(col_formats):
                    # Format values based on format string (e.g., "{:.2f}" for 2 decimal places)
                    try:
                        formatted_cell = col_formats[i].format(cell)
                    except (ValueError, TypeError):
                        formatted_cell = str(cell)
                else:
                    formatted_cell = str(cell)
                
                formatted_row.append(formatted_cell)
            
            formatted_data.append(formatted_row)
        
        return formatted_data
    
    @staticmethod
    def calculate_column_widths(
        data: List[List[Any]],
        table_width: float,
        min_col_width: float = 50.0,
        padding: float = 10.0
    ) -> List[float]:
        """Calculate appropriate column widths based on content."""
        if not data or not data[0]:
            return []
        
        num_cols = len(data[0])
        
        # Start with even distribution
        col_widths = [(table_width - (padding * 2)) / num_cols] * num_cols
        
        # In a real implementation, this would analyze content to determine
        # appropriate widths based on content length
        
        return col_widths


class ChartFormatter:
    """Utility for formatting chart data and appearance."""
    
    @staticmethod
    def format_line_chart_data(
        x_values: List[Any],
        y_series: Dict[str, List[float]],
        style: ChartStyle = None
    ) -> Dict[str, Any]:
        """Format data for a line chart."""
        if style is None:
            style = ChartStyle()
            
        return {
            "type": "line",
            "x_values": x_values,
            "y_series": y_series,
            "style": style.to_dict()
        }
    
    @staticmethod
    def format_bar_chart_data(
        categories: List[str],
        series: Dict[str, List[float]],
        style: ChartStyle = None,
        stacked: bool = False,
        horizontal: bool = False
    ) -> Dict[str, Any]:
        """Format data for a bar chart."""
        if style is None:
            style = ChartStyle()
            
        return {
            "type": "bar",
            "categories": categories,
            "series": series,
            "style": style.to_dict(),
            "stacked": stacked,
            "horizontal": horizontal
        }
    
    @staticmethod
    def format_pie_chart_data(
        labels: List[str],
        values: List[float],
        style: ChartStyle = None,
        explode: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """Format data for a pie chart."""
        if style is None:
            style = ChartStyle()
            
        return {
            "type": "pie",
            "labels": labels,
            "values": values,
            "style": style.to_dict(),
            "explode": explode
        }
    
    @staticmethod
    def format_scatter_plot_data(
        x_values: List[float],
        y_values: List[float],
        style: ChartStyle = None,
        labels: Optional[List[str]] = None,
        sizes: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """Format data for a scatter plot."""
        if style is None:
            style = ChartStyle()
            
        return {
            "type": "scatter",
            "x_values": x_values,
            "y_values": y_values,
            "style": style.to_dict(),
            "labels": labels,
            "sizes": sizes
        } 