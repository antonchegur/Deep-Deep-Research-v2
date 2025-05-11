"""
PDF Report Elements Module

This module defines various elements that can be added to a PDF report,
such as text, tables, charts, and images.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union, Tuple
import os
from pathlib import Path

from src.pdf_generation.pdf_base import ReportElement, PDFGenerator
from src.pdf_generation.formatters import ChartStyle, TextStyle, StyleSheet, TextAlignment

# ReportLab specific imports for flowables
from reportlab.platypus import Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import ParagraphStyle as RLParagraphStyle # Alias to avoid confusion
from reportlab.lib import colors as rl_colors


class TextElement(ReportElement):
    """Element for displaying text content in the report."""
    
    def __init__(self, 
                 text: str, 
                 x: float, 
                 y: float, 
                 width: Optional[float] = None,
                 height: Optional[float] = None,
                 style_name: Optional[str] = None,
                 style: Optional[TextStyle] = None,
                 font_size: Optional[int] = None,
                 font_name: Optional[str] = None,
                 color: Optional[str] = None,
                 align: Optional[str] = None,
                 line_spacing: Optional[float] = None,
                 element_id: Optional[str] = None):
        """Initialize a text element.
        
        Args:
            text: The text content to display
            x: X-coordinate position
            y: Y-coordinate position
            width: Optional width constraint
            height: Optional height constraint
            style_name: Optional name of a style from the StyleSheet (e.g., 'body', 'heading1')
            style: Optional direct TextStyle object. Overrides style_name if provided.
            font_size: Deprecated. Font size in points (use TextStyle).
            font_name: Deprecated. Font family name (use TextStyle).
            color: Deprecated. Text color (hex string or color name) (use TextStyle).
            align: Deprecated. Text alignment ('left', 'center', 'right', 'justify') (use TextStyle).
            line_spacing: Deprecated. Line spacing multiplier (use TextStyle).
            element_id: Optional unique identifier
        """
        super().__init__(element_id)
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.style_name = style_name
        self.direct_style = style

        self.legacy_font_size = font_size
        self.legacy_font_name = font_name
        self.legacy_color = color
        self.legacy_align = align
        self.legacy_line_spacing = line_spacing
    
    def render(self, pdf_generator: PDFGenerator) -> None:
        """Render the text element to the PDF."""
        resolved_style: Optional[TextStyle] = None
        
        if self.direct_style:
            resolved_style = self.direct_style
        elif self.style_name and hasattr(pdf_generator.config.stylesheet, self.style_name):
            resolved_style = getattr(pdf_generator.config.stylesheet, self.style_name)
        
        if resolved_style:
            pdf_generator.add_text(
                text=self.text,
                x=self.x,
                y=self.y,
                width=self.width,
                text_style=resolved_style
            )
        else:
            pdf_generator.add_text(
                text=self.text,
                x=self.x,
                y=self.y,
                width=self.width,
                font_size=self.legacy_font_size or pdf_generator.config.stylesheet.body.font_size,
                font_name=self.legacy_font_name or pdf_generator.config.stylesheet.body.font_family,
                color=self.legacy_color or pdf_generator.config.stylesheet.body.color,
                align=(self.legacy_align or pdf_generator.config.stylesheet.body.alignment.value),
                line_spacing=self.legacy_line_spacing or pdf_generator.config.stylesheet.body.line_spacing
            )

    def to_reportlab_flowable(self, stylesheet: StyleSheet) -> Optional[Paragraph]:
        """Converts this TextElement to a ReportLab Paragraph flowable."""
        resolved_style: Optional[TextStyle] = None
        if self.direct_style:
            resolved_style = self.direct_style
        elif self.style_name and hasattr(stylesheet, self.style_name):
            resolved_style = getattr(stylesheet, self.style_name)
        else:
            # Fallback to legacy or default body style
            resolved_style = TextStyle(
                font_family=self.legacy_font_name or stylesheet.body.font_family,
                font_size=self.legacy_font_size or stylesheet.body.font_size,
                color=self.legacy_color or stylesheet.body.color,
                alignment=TextAlignment(self.legacy_align.lower() if self.legacy_align else stylesheet.body.alignment.value),
                line_spacing=self.legacy_line_spacing or stylesheet.body.line_spacing,
                bold=False, # Legacy attributes didn't have bold/italic/underline directly
                italic=False,
                underline=False,
                paragraph_spacing=stylesheet.body.paragraph_spacing
            )
        
        if not resolved_style: return None # Should not happen with fallback

        alignment_map = {
            TextAlignment.LEFT: 0, TextAlignment.CENTER: 1,
            TextAlignment.RIGHT: 2, TextAlignment.JUSTIFY: 4
        }
        rl_alignment = alignment_map.get(resolved_style.alignment, 0)

        # Helper to parse color string to ReportLab color
        def parse_rl_color(color_str: str) -> rl_colors.Color:
            if color_str.startswith('#'):
                return rl_colors.HexColor(color_str)
            # Add more color name parsing if needed, default to black
            try: return getattr(rl_colors, color_str.lower(), rl_colors.black)
            except: return rl_colors.black

        reportlab_text_color = parse_rl_color(resolved_style.color)

        paragraph_rl_style = RLParagraphStyle(
            name=f'TextElementStyle_{self.element_id}',
            fontName=resolved_style.font_family,
            fontSize=resolved_style.font_size,
            leading=resolved_style.font_size * resolved_style.line_spacing,
            textColor=reportlab_text_color,
            alignment=rl_alignment,
            spaceBefore=resolved_style.paragraph_spacing / 2,
            spaceAfter=resolved_style.paragraph_spacing / 2,
        )

        styled_text = self.text
        if resolved_style.bold: styled_text = f"<b>{styled_text}</b>"
        if resolved_style.italic: styled_text = f"<i>{styled_text}</i>"
        if resolved_style.underline: styled_text = f"<u>{styled_text}</u>"
        
        # Apply width if specified - ReportLab Paragraphs handle width naturally when in a Frame
        # For now, this method just returns the Paragraph. Width is handled by the Frame in SimpleDocTemplate.
        # If self.width is set, it could be used to create a Frame for this Paragraph specifically, 
        # but that complicates flow. Let's assume full width for now.

        return Paragraph(styled_text, paragraph_rl_style)


class TableElement(ReportElement):
    """Element for displaying tabular data in the report."""
    
    def __init__(self,
                 data: List[List[Any]],
                 x: float,
                 y: float,
                 col_widths: Optional[List[float]] = None,
                 width: Optional[float] = None,
                 height: Optional[float] = None,
                 header: bool = True,
                 style: Optional[Dict[str, Any]] = None,
                 element_id: Optional[str] = None):
        """Initialize a table element.
        
        Args:
            data: Table data as a list of rows, each row is a list of cell values
            x: X-coordinate position
            y: Y-coordinate position
            col_widths: List of column widths (if None, columns will be sized automatically)
            width: Optional total width constraint
            height: Optional height constraint
            header: Whether the first row should be treated as a header
            style: Optional styling parameters
            element_id: Optional unique identifier
        """
        super().__init__(element_id)
        self.data = data
        self.x = x
        self.y = y
        self.col_widths = col_widths
        self.width = width
        self.height = height
        self.header = header
        self.style = style or {}
    
    def render(self, pdf_generator: PDFGenerator) -> None:
        """Render the table element to the PDF."""
        pdf_generator.add_table(
            data=self.data,
            x=self.x,
            y=self.y,
            col_widths=self.col_widths,
            header=self.header
        )


class ChartElement(ReportElement):
    """Element for displaying charts and graphs in the report."""
    
    def __init__(self,
                 chart_type: str,
                 data: Any,
                 x: float,
                 y: float,
                 width: float,
                 height: float,
                 title: Optional[str] = None,
                 x_label: Optional[str] = None,
                 y_label: Optional[str] = None,
                 legend: bool = True,
                 style: Optional[ChartStyle] = None,
                 element_id: Optional[str] = None):
        """Initialize a chart element.
        
        Args:
            chart_type: Type of chart ('bar', 'line', 'pie', 'scatter')
            data: Chart data (core plot data, e.g., x_values, y_series)
            x: X-coordinate position
            y: Y-coordinate position
            width: Width of the chart
            height: Height of the chart
            title: Optional chart title
            x_label: Optional X-axis label
            y_label: Optional Y-axis label
            legend: Whether to display a legend
            style: Optional ChartStyle object for styling
            element_id: Optional unique identifier
        """
        super().__init__(element_id)
        self.chart_type = chart_type
        self.data = data
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.legend = legend
        self.style = style
    
    def render(self, pdf_generator: PDFGenerator) -> None:
        """Render the chart element to the PDF."""
        pdf_generator.add_chart(
            chart_type=self.chart_type,
            data=self.data,
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
            title=self.title,
            x_label=self.x_label,
            y_label=self.y_label,
            legend=self.legend,
            style=self.style
        )


class ImageElement(ReportElement):
    """Element for displaying images in the report."""
    
    def __init__(self,
                 image_path: Union[str, Path],
                 x: float,
                 y: float,
                 width: Optional[float] = None,
                 height: Optional[float] = None,
                 caption: Optional[str] = None,
                 element_id: Optional[str] = None):
        """Initialize an image element.
        
        Args:
            image_path: Path to the image file
            x: X-coordinate position
            y: Y-coordinate position
            width: Optional width constraint (preserves aspect ratio if height is None)
            height: Optional height constraint (preserves aspect ratio if width is None)
            caption: Optional image caption
            element_id: Optional unique identifier
        """
        super().__init__(element_id)
        self.image_path = image_path if isinstance(image_path, Path) else Path(image_path)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.caption = caption
    
    def render(self, pdf_generator: PDFGenerator) -> None:
        """Render the image element to the PDF."""
        pdf_generator.add_image(
            image_path=self.image_path,
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height
        )
        
        # Add caption if provided
        if self.caption:
            caption_y = self.y + (self.height or 0) + 10  # 10 points below the image
            pdf_generator.add_text(
                text=self.caption,
                x=self.x,
                y=caption_y,
                font_size=10,
                align='center'
            )


class HeaderElement(ReportElement):
    """Element for displaying a consistent header on report pages."""
    
    def __init__(self,
                 text: Optional[str] = None,
                 image_path: Optional[Union[str, Path]] = None,
                 height: float = 50,
                 include_date: bool = True,
                 include_page_number: bool = True,
                 element_id: Optional[str] = None):
        """Initialize a header element.
        
        Args:
            text: Optional header text
            image_path: Optional path to a logo image
            height: Height of the header area
            include_date: Whether to include the current date
            include_page_number: Whether to include page numbers
            element_id: Optional unique identifier
        """
        super().__init__(element_id)
        self.text = text
        self.image_path = Path(image_path) if image_path else None
        self.height = height
        self.include_date = include_date
        self.include_page_number = include_page_number
    
    def render(self, pdf_generator: PDFGenerator) -> None:
        """Render the header element to the PDF."""
        # Implementation will be specific to the PDF generator
        # This will need to be implemented in the concrete generator classes


class FooterElement(ReportElement):
    """Element for displaying a consistent footer on report pages."""
    
    def __init__(self,
                 text: Optional[str] = None,
                 height: float = 30,
                 include_date: bool = False,
                 include_page_number: bool = True,
                 element_id: Optional[str] = None):
        """Initialize a footer element.
        
        Args:
            text: Optional footer text
            height: Height of the footer area
            include_date: Whether to include the current date
            include_page_number: Whether to include page numbers
            element_id: Optional unique identifier
        """
        super().__init__(element_id)
        self.text = text
        self.height = height
        self.include_date = include_date
        self.include_page_number = include_page_number
    
    def render(self, pdf_generator: PDFGenerator) -> None:
        """Render the footer element to the PDF."""
        # Implementation will be specific to the PDF generator
        # This will need to be implemented in the concrete generator classes


class ListElement(ReportElement):
    """Element for displaying bulleted or numbered lists."""
    
    def __init__(self,
                 items: List[str],
                 x: float,
                 y: float,
                 width: Optional[float] = None,
                 numbered: bool = False,
                 style_name: Optional[str] = None,
                 style: Optional[TextStyle] = None,
                 font_size: Optional[int] = None,
                 font_name: Optional[str] = None,
                 color: Optional[str] = None,
                 element_id: Optional[str] = None):
        """Initialize a list element.
        
        Args:
            items: List of text items
            x: X-coordinate position
            y: Y-coordinate position
            width: Optional width constraint
            numbered: If True, creates a numbered list; otherwise, a bulleted list
            style_name: Optional name of a style from the StyleSheet (e.g., 'body')
            style: Optional direct TextStyle object. Overrides style_name if provided.
            font_size: Deprecated. Font size for list items (use TextStyle).
            font_name: Deprecated. Font family name (use TextStyle).
            color: Deprecated. Text color (use TextStyle).
            element_id: Optional unique identifier
        """
        super().__init__(element_id)
        self.items = items
        self.x = x
        self.y = y
        self.width = width
        self.numbered = numbered
        self.style_name = style_name
        self.direct_style = style

        self.legacy_font_size = font_size
        self.legacy_font_name = font_name
        self.legacy_color = color
    
    def render(self, pdf_generator: PDFGenerator) -> None:
        """Render the list element to the PDF."""
        # This method will be called by FPDFGenerator or if to_reportlab_flowable returns None
        # For ReportLab, to_reportlab_flowable will be used primarily.
        
        resolved_style: Optional[TextStyle] = None
        if self.direct_style:
            resolved_style = self.direct_style
        elif self.style_name and hasattr(pdf_generator.config.stylesheet, self.style_name):
            resolved_style = getattr(pdf_generator.config.stylesheet, self.style_name)
        
        effective_font_size = (resolved_style.font_size if resolved_style 
                               else self.legacy_font_size or pdf_generator.config.stylesheet.body.font_size)
        effective_font_name = (resolved_style.font_family if resolved_style 
                               else self.legacy_font_name or pdf_generator.config.stylesheet.body.font_family)
        effective_color = (resolved_style.color if resolved_style 
                           else self.legacy_color or pdf_generator.config.stylesheet.body.color)
        effective_line_spacing = (resolved_style.line_spacing if resolved_style 
                                   else pdf_generator.config.stylesheet.body.line_spacing)

        line_height = effective_font_size * effective_line_spacing
        
        for i, item_text_content in enumerate(self.items):
            prefix = f"{i+1}. " if self.numbered else "• "
            full_item_text = f"{prefix}{item_text_content}"
            
            item_text_style = resolved_style or TextStyle(
                font_family=effective_font_name,
                font_size=effective_font_size,
                color=effective_color,
                alignment=TextAlignment.LEFT, # Lists are typically left-aligned
                line_spacing=effective_line_spacing,
                bold=False, italic=False, underline=False, # Assuming no bold/italic for list items by default unless in style
                paragraph_spacing=(pdf_generator.config.stylesheet.body.paragraph_spacing if not resolved_style else resolved_style.paragraph_spacing)
            )
            if resolved_style and resolved_style.bold: item_text_style.bold = True # Apply from resolved style
            if resolved_style and resolved_style.italic: item_text_style.italic = True
            if resolved_style and resolved_style.underline: item_text_style.underline = True

            pdf_generator.add_text(
                text=full_item_text,
                x=self.x,
                y=self.y + i * line_height,
                width=self.width,
                text_style=item_text_style 
                # Fallback attributes are not passed here as text_style is guaranteed to be an object
            )

    def to_reportlab_flowable(self, stylesheet: StyleSheet) -> Optional[ListFlowable]:
        """Converts this ListElement to a ReportLab ListFlowable."""
        resolved_style: Optional[TextStyle] = None
        if self.direct_style:
            resolved_style = self.direct_style
        elif self.style_name and hasattr(stylesheet, self.style_name):
            resolved_style = getattr(stylesheet, self.style_name)
        else:
            resolved_style = TextStyle(
                font_family=self.legacy_font_name or stylesheet.body.font_family,
                font_size=self.legacy_font_size or stylesheet.body.font_size,
                color=self.legacy_color or stylesheet.body.color,
                alignment=TextAlignment.LEFT,
                line_spacing=stylesheet.body.line_spacing,
                bold=False, italic=False, underline=False,
                paragraph_spacing=stylesheet.body.paragraph_spacing
            )
        if not resolved_style: return None

        # Helper to parse color string to ReportLab color
        def parse_rl_color(color_str: str) -> rl_colors.Color:
            if color_str.startswith('#'): return rl_colors.HexColor(color_str)
            try: return getattr(rl_colors, color_str.lower(), rl_colors.black)
            except: return rl_colors.black

        reportlab_text_color = parse_rl_color(resolved_style.color)

        # Base style for list items
        item_rl_style = RLParagraphStyle(
            name=f'ListItemStyle_{self.element_id}',
            fontName=resolved_style.font_family,
            fontSize=resolved_style.font_size,
            leading=resolved_style.font_size * resolved_style.line_spacing,
            textColor=reportlab_text_color,
            spaceBefore=2, spaceAfter=2 # Small spacing for list items
        )

        list_items = []
        for item_text_content in self.items:
            styled_item_text = item_text_content
            if resolved_style.bold: styled_item_text = f"<b>{styled_item_text}</b>"
            if resolved_style.italic: styled_item_text = f"<i>{styled_item_text}</i>"
            if resolved_style.underline: styled_item_text = f"<u>{styled_item_text}</u>"
            list_items.append(Paragraph(styled_item_text, item_rl_style))

        bullet_char = '1.' if self.numbered else '\u2022' # Unicode bullet
        return ListFlowable(
            list_items,
            bulletType='1' if self.numbered else 'bullet',
            bulletFontName=resolved_style.font_family,
            bulletFontSize=resolved_style.font_size,
            # start=bullet_char, # Not needed if using bulletType='1' or 'bullet'
            leftIndent=18, # Standard indent for lists
            # bulletColor=reportlab_text_color # Would be nice, but ListFlowable takes color from paragraph style
        )


class PageBreakElement(ReportElement):
    """Element for forcing a page break in the report."""
    
    def __init__(self, element_id: Optional[str] = None):
        """Initialize a page break element."""
        super().__init__(element_id)
    
    def render(self, pdf_generator: PDFGenerator) -> None:
        """Render the page break element (add a new page)."""
        pdf_generator.add_page() 