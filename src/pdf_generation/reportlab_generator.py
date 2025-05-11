"""
ReportLab Implementation of PDF Generator

This module provides a concrete implementation of the PDFGenerator interface
using the ReportLab library.
"""

import os
import datetime
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple, cast
import io

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image, ListFlowable, ListItem
)
from reportlab.pdfgen import canvas
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing

from src.pdf_generation.pdf_base import PDFGenerator, PDFReport, ReportConfig, ReportElement
from src.pdf_generation.charts import LineChart, BarChart, PieChart, ScatterPlot
from src.pdf_generation.formatters import ChartStyle, TextStyle, ColorScheme, StyleSheet
from src.pdf_generation.elements import TextElement, ListElement, PageBreakElement, ChartElement, ImageElement, TableElement


class ReportLabPDFGenerator(PDFGenerator):
    """ReportLab implementation of the PDFGenerator interface."""
    
    def __init__(self, config: ReportConfig):
        """Initialize the ReportLab PDF generator with the given configuration."""
        super().__init__(config)
        self.canvas = None
        self.doc = None
        self.styles = getSampleStyleSheet()
        self.current_y = 0
        self.page_width = 0
        self.page_height = 0
        
    def generate(self, report: PDFReport, output_path: Union[str, Path]) -> str:
        """Generate a PDF from a report and save it to the specified path."""
        output_path = Path(output_path)
        
        # Create the PDF document
        page_size = self.config.get_reportlab_pagesize()
        self.page_width, self.page_height = page_size
        
        # Create the document template
        doc_output_path = str(output_path)
        self.doc = SimpleDocTemplate(
            doc_output_path,
            pagesize=page_size,
            leftMargin=self.config.margins.get("left", 72),
            rightMargin=self.config.margins.get("right", 72),
            topMargin=self.config.margins.get("top", 72),
            bottomMargin=self.config.margins.get("bottom", 72),
            title=self.config.title,
            author=self.config.author,
            subject=self.config.subject,
            keywords=self.config.keywords
        )
        
        # List to hold all flowable elements
        elements = []
        
        # Add title if available using a TextElement converted to flowable
        if self.config.title:
            title_style = self.config.stylesheet.heading1
            title_text_element = TextElement(
                text=self.config.title, 
                x=0, y=0, # x,y are not strictly needed for flowables in main story
                style=title_style
            )
            flowable_title = title_text_element.to_reportlab_flowable(self.config.stylesheet)
            if flowable_title:
                elements.append(flowable_title)
            elements.append(Spacer(1, 12))
        
        # Add table of contents if requested
        if self.config.include_toc:
            # In a real implementation, we would generate a table of contents here
            # This would typically be done in a second pass after the document is built
            pass
        
        # Process all report elements
        for element in report.elements:
            flowable = None
            if hasattr(element, 'to_reportlab_flowable'):
                flowable = element.to_reportlab_flowable(self.config.stylesheet)
            
            if flowable:
                elements.append(flowable)
            elif isinstance(element, PageBreakElement):
                elements.append(PageBreak())
            elif isinstance(element, ChartElement) or isinstance(element, ImageElement):
                # Charts and Images are rendered to a temp file and then added as an Image flowable
                # This requires a canvas, so we'll use a temporary one.
                # This part needs careful implementation to get image bytes and create an Image flowable
                try:
                    # For ChartElement and ImageElement, we need to get an image path or bytes
                    # The add_chart and add_image methods save to a temp file and draw on canvas.
                    # We need to adapt this to get an Image flowable.
                    
                    # Simplified: create a placeholder or use a method to get image path
                    # This is where the direct canvas rendering part of add_chart/add_image would be used
                    # to generate an image, then that image is added as a flowable.
                    
                    # Let's assume elements that don't produce flowables are rendered via their
                    # own `render` method if it uses the main canvas (e.g. header/footer)
                    # or we handle them specifically like charts.

                    # For charts/images, they are typically converted to an Image flowable
                    # The existing add_chart/add_image methods save to temp file.
                    # We need a way to get that path or use the image bytes.

                    if isinstance(element, ChartElement):
                        # Create a temporary file to save the chart
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                            tmp_path = Path(tmp.name)
                        try:
                            chart_style_to_use = element.style or self.config.stylesheet.chart
                            chart_obj = None
                            if element.chart_type == 'line':
                                chart_obj = LineChart(title=element.title, x_label=element.x_label, y_label=element.y_label, legend=element.legend, style=chart_style_to_use)
                                chart_obj.create_chart(element.data.get('x_values',[]), element.data.get('y_series',{}))
                            elif element.chart_type == 'bar':
                                chart_obj = BarChart(title=element.title, x_label=element.x_label, y_label=element.y_label, legend=element.legend, style=chart_style_to_use)
                                chart_obj.create_chart(element.data.get('categories',[]), element.data.get('series',{}), element.data.get('stacked',False), element.data.get('horizontal',False))
                            elif element.chart_type == 'pie':
                                chart_obj = PieChart(title=element.title, legend=element.legend, style=chart_style_to_use)
                                chart_obj.create_chart(element.data.get('labels',[]), element.data.get('values',[]), element.data.get('explode'))
                            elif element.chart_type == 'scatter':
                                chart_obj = ScatterPlot(title=element.title, x_label=element.x_label, y_label=element.y_label, legend=element.legend, style=chart_style_to_use)
                                chart_obj.create_chart(element.data.get('x_values',[]), element.data.get('y_values',[]), element.data.get('labels'), element.data.get('sizes'))
                            
                            if chart_obj:
                                chart_obj.save_to_file(tmp_path)
                                img = Image(tmp_path)
                                # Attempt to scale image if too wide for frame
                                frame_width = self.doc.width
                                if img.imageWidth > frame_width:
                                    ratio = frame_width / img.imageWidth
                                    img.drawWidth = frame_width
                                    img.drawHeight = img.imageHeight * ratio
                                elements.append(img)
                        finally:
                            if os.path.exists(tmp_path):
                                os.unlink(tmp_path)
                    
                    elif isinstance(element, ImageElement):
                        img = Image(str(element.image_path))
                        frame_width = self.doc.width
                        if img.imageWidth > frame_width:
                            ratio = frame_width / img.imageWidth
                            img.drawWidth = frame_width
                            img.drawHeight = img.imageHeight * ratio
                        elements.append(img)
                        if element.caption:
                            caption_style = self.config.stylesheet.caption
                            cap_para = Paragraph(element.caption, RLParagraphStyle(name='caption', parent=self.styles['Normal'], alignment=1, fontName=caption_style.font_family, fontSize=caption_style.font_size, textColor=rl_colors.HexColor(caption_style.color)))
                            elements.append(cap_para)

                    elif isinstance(element, TableElement):
                        # Convert TableElement to ReportLab Table flowable
                        table_data_str = [[str(cell) for cell in row] for row in element.data]
                        rl_table = Table(table_data_str, colWidths=element.col_widths)
                        # Apply basic styling for now, more complex styling can be added
                        # Based on element.style (which is a dict currently)
                        ts = []
                        if element.header:
                            ts.append(('BACKGROUND', (0,0), (-1,0), rl_colors.lightblue))
                            ts.append(('TEXTCOLOR', (0,0), (-1,0), rl_colors.black))
                            ts.append(('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'))
                        ts.append(('GRID', (0,0), (-1,-1), 1, rl_colors.black))
                        rl_table.setStyle(TableStyle(ts))
                        elements.append(rl_table)

                except Exception as e:
                    print(f"Error processing element {element}: {e}") # simple error logging
                    elements.append(Paragraph(f"Error rendering {element.__class__.__name__}", self.styles['Normal']))
            else:
                # Fallback for elements that don't have to_reportlab_flowable or aren't handled above
                # This might be where HeaderElement/FooterElement get processed if they draw on every page via canvas
                # For now, just skip or add a placeholder
                # print(f"Skipping element or needs specific handling: {element}")
                pass # Skip unknown elements for main story for now
        
        # Build the document
        # The onFirstPage and onLaterPages arguments can be used for headers/footers
        self.doc.build(elements, onFirstPage=self._draw_header_footer, onLaterPages=self._draw_header_footer)
        
        return str(output_path)

    def _draw_header_footer(self, canvas_obj: canvas.Canvas, doc: SimpleDocTemplate):
        """Draw header and footer on each page."""
        canvas_obj.saveState()
        # Footer
        if self.config.footer_text or self.config.include_page_numbers:
            footer_parts = []
            if self.config.footer_text: footer_parts.append(self.config.footer_text)
            if self.config.include_page_numbers: footer_parts.append(f"Page {canvas_obj.getPageNumber()}")
            
            footer_style = self.config.stylesheet.caption # Using caption style for footer
            final_footer_text = "  |  ".join(footer_parts)
            
            r_color, g_color, b_color = self._parse_color(footer_style.color)
            canvas_obj.setFillColorRGB(r_color, g_color, b_color)
            canvas_obj.setFont(footer_style.font_family, footer_style.font_size)
            canvas_obj.drawCentredString(self.page_width / 2.0, self.config.margins.get("bottom", 72) / 2, final_footer_text)

        # Header
        if self.config.header_text: # Basic header text for now
            header_style = self.config.stylesheet.body # Or a dedicated header style
            r_color, g_color, b_color = self._parse_color(header_style.color)
            canvas_obj.setFillColorRGB(r_color, g_color, b_color)
            canvas_obj.setFont(header_style.font_family, header_style.font_size)
            canvas_obj.drawString(self.config.margins.get("left", 72), 
                                self.page_height - self.config.margins.get("top", 72) * 0.75, 
                                self.config.header_text)
        canvas_obj.restoreState()
        
    def add_page(self) -> None:
        """Add a new page to the PDF."""
        if self.canvas:
            self.canvas.showPage()
            self.current_y = self.page_height - self.config.margins.get("top", 72)
        
    def add_text(self, #NOSONAR
                 text: str, 
                 x: float, 
                 y: float, 
                 width: Optional[float] = None, 
                 text_style: Optional[TextStyle] = None,
                 # Deprecated direct style attributes (for fallback):
                 font_size: Optional[int] = None, 
                 font_name: Optional[str] = None, 
                 color: Optional[str] = None, 
                 align: Optional[str] = None,
                 line_spacing: Optional[float] = None
                 ) -> None:
        """Add text to the PDF using ReportLab Paragraphs for better styling."""
        if not self.canvas:
            raise ValueError("Canvas not initialized. Call generate first.")

        # Determine actual style to use
        style_to_use = text_style or self.config.stylesheet.body
        if font_size: style_to_use.font_size = font_size
        if font_name: style_to_use.font_family = font_name
        if color: style_to_use.color = color
        if align: 
            try:
                style_to_use.alignment = TextAlignment(align.lower())
            except ValueError:
                style_to_use.alignment = TextAlignment.LEFT # Default
        if line_spacing: style_to_use.line_spacing = line_spacing

        # Create ReportLab ParagraphStyle
        # Map TextAlignment enum to ReportLab TA_xyz constants
        alignment_map = {
            TextAlignment.LEFT: 0,    # TA_LEFT
            TextAlignment.CENTER: 1, # TA_CENTER
            TextAlignment.RIGHT: 2,   # TA_RIGHT
            TextAlignment.JUSTIFY: 4 # TA_JUSTIFY
        }
        rl_alignment = alignment_map.get(style_to_use.alignment, 0)

        r_color, g_color, b_color = self._parse_color(style_to_use.color)
        reportlab_color = colors.Color(r_color, g_color, b_color)

        paragraph_style = ParagraphStyle(
            name='CustomStyle',
            fontName=style_to_use.font_family,
            fontSize=style_to_use.font_size,
            leading=style_to_use.font_size * style_to_use.line_spacing,
            textColor=reportlab_color,
            alignment=rl_alignment,
            spaceBefore=style_to_use.paragraph_spacing / 2, # Approximation
            spaceAfter=style_to_use.paragraph_spacing / 2,  # Approximation
            # TODO: Add bold/italic/underline support if ParagraphStyle allows easily
            # ReportLab handles bold/italic via XML-like tags in the text string itself, e.g. "<b>bold</b>"
        )
        
        # Handle bold/italic/underline by wrapping text with tags if style indicates
        styled_text = text
        if style_to_use.bold: styled_text = f"<b>{styled_text}</b>"
        if style_to_use.italic: styled_text = f"<i>{styled_text}</i>"
        if style_to_use.underline: styled_text = f"<u>{styled_text}</u>"

        para = Paragraph(styled_text, paragraph_style)
        
        # Available width for the paragraph
        # If x is a margin, then page_width - x - right_margin
        # If x is absolute, then use provided width or page_width - x
        available_width = width or (self.page_width - x - self.config.margins.get("right", 72))
        if available_width <=0: available_width = self.page_width # fallback if calc is bad

        w, h = para.wrapOn(self.canvas, available_width, self.page_height) # Height constraint is large
        para.drawOn(self.canvas, x, self.page_height - y - h) # y is from top, ReportLab draws from bottom-left

        # Note: This basic add_text does not easily flow into the SimpleDocTemplate story used in `generate`.
        # For elements to be part of the main document flow, they should be added to the `elements` list
        # in `generate`. This `add_text` is more for direct canvas drawing if an element needs it.
        # The `TextElement.render` will need to be updated to create a Paragraph and add it to flowables
        # if it's to use this richer styling and participate in document flow.
    
    def add_table(self, data: List[List[Any]], x: float, y: float, 
                 col_widths: List[float] = None, header: bool = True) -> None:
        """Add a table to the PDF."""
        if not self.canvas:
            raise ValueError("Canvas not initialized. Call generate first.")
        
        # Convert all data to strings
        data = [[str(cell) for cell in row] for row in data]
        
        # Create a table
        col_widths = col_widths or [100] * len(data[0]) if data and data[0] else []
        table = Table(data, colWidths=col_widths)
        
        # Add table style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue) if header else None,
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold') if header else None,
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        style = [s for s in style if s is not None]
        table.setStyle(TableStyle(style))
        
        # Draw the table
        w, h = table.wrap(self.page_width, self.page_height)
        table.drawOn(self.canvas, x, self.page_height - y - h)
    
    def add_image(self, image_path: Union[str, Path], x: float, y: float, 
                 width: float = None, height: float = None) -> None:
        """Add an image to the PDF."""
        if not self.canvas:
            raise ValueError("Canvas not initialized. Call generate first.")
        
        # Get image size
        img = Image(str(image_path))
        img_width, img_height = img.imageWidth, img.imageHeight
        
        # Calculate actual dimensions
        if width and height:
            # Use specified dimensions
            actual_width = width
            actual_height = height
        elif width:
            # Calculate height to maintain aspect ratio
            aspect = img_height / img_width
            actual_width = width
            actual_height = width * aspect
        elif height:
            # Calculate width to maintain aspect ratio
            aspect = img_width / img_height
            actual_height = height
            actual_width = height * aspect
        else:
            # Use original dimensions
            actual_width = img_width
            actual_height = img_height
        
        # Draw the image
        self.canvas.drawImage(
            str(image_path), 
            x, 
            self.page_height - y - actual_height, 
            width=actual_width, 
            height=actual_height
        )
    
    def add_chart(self, chart_type: str, data: Any, x: float, y: float, 
                 width: float, height: float,
                 title: Optional[str] = None,
                 x_label: Optional[str] = None,
                 y_label: Optional[str] = None,
                 legend: bool = True,
                 style: Optional[ChartStyle] = None
                 ) -> None:
        """Add a chart to the PDF."""
        if not self.canvas:
            raise ValueError("Canvas not initialized. Call generate first.")
        
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
                # PieChart specific constructor if different, for now assuming it also takes title, legend, style
                chart = PieChart(title=title, legend=legend, style=chart_style) 
                chart.create_chart(labels, values, explode)
            elif chart_type == 'scatter':
                x_values = data.get('x_values', [])
                y_values = data.get('y_values', [])
                point_labels = data.get('labels', None) # Renamed to avoid conflict with x_label/y_label
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
    
    def _parse_color(self, color_str: str) -> Tuple[float, float, float]:
        """Parse a color string (hex or named) to RGB components."""
        if color_str.startswith('#'):
            # Hex color
            r = int(color_str[1:3], 16) / 255.0
            g = int(color_str[3:5], 16) / 255.0
            b = int(color_str[5:7], 16) / 255.0
            return (r, g, b)
        else:
            # Named color - this is a simplification; in reality, we would
            # have a mapping of color names to RGB values
            # For now, return black as default
            return (0, 0, 0) 