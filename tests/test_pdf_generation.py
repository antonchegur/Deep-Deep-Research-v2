"""
Tests for the PDF Report Generation System.

This module contains tests for the PDF generation components, including
config, report elements, and generation with both ReportLab and FPDF.
"""

import os
import sys
import unittest
from pathlib import Path
import tempfile
import matplotlib.pyplot as plt
import numpy as np
from typing import Any, Optional, Union

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pdf_generation import (
    PDFReport, ReportConfig, ReportLibrary, ReportElement,
    TextElement, TableElement, ChartElement, ImageElement,
    HeaderElement, FooterElement, ListElement, PageBreakElement,
    StyleSheet, ColorScheme, TextFormatter, TableFormatter, ChartFormatter,
    TextStyle, TextAlignment
)
from src.pdf_generation.pdf_base import PDFGenerator
from src.pdf_generation.reportlab_generator import ReportLabPDFGenerator
from src.pdf_generation.fpdf_generator import FPDFGenerator
from src.pdf_generation.charts import LineChart, BarChart, PieChart, ScatterPlot


class MockPDFGenerator(PDFGenerator):
    """Mock implementation of PDFGenerator for testing."""
    
    def __init__(self, config):
        super().__init__(config)
        self.elements_rendered = []
        self.pages_added = 0
        self.config = config
        self.config.stylesheet = config.stylesheet or StyleSheet()
    
    def generate(self, report, output_path):
        """Mock implementation that just records calls."""
        for element in report.elements:
            element.render(self)
        return str(output_path)
    
    def add_page(self):
        """Record page break."""
        self.elements_rendered.append("PageBreak")
    
    def add_text(self, 
                 text: str, 
                 x: float, 
                 y: float, 
                 width: Optional[float] = None, 
                 text_style: Optional[TextStyle] = None,
                 font_size: Optional[int] = None, 
                 font_name: Optional[str] = None, 
                 color: Optional[str] = None, 
                 align: Optional[str] = None,
                 line_spacing: Optional[float] = None
                 ) -> None:
        """Record text addition, prioritizing TextStyle."""
        style_desc = ""
        if text_style:
            style_desc = (f" Style: [Font: {text_style.font_family}, Size: {text_style.font_size}, "
                          f"Color: {text_style.color}, Align: {text_style.alignment.value}, "
                          f"LineSpacing: {text_style.line_spacing}, Bold: {text_style.bold}, "
                          f"Italic: {text_style.italic}, Underline: {text_style.underline}]")
        else:
            fs = font_size or self.config.stylesheet.body.font_size
            fn = font_name or self.config.stylesheet.body.font_family
            cl = color or self.config.stylesheet.body.color
            al = align or self.config.stylesheet.body.alignment.value
            ls = line_spacing or self.config.stylesheet.body.line_spacing
            style_desc = (f" Style: [Font: {fn}, Size: {fs}, Color: {cl}, Align: {al}, LineSpacing: {ls}]")
            
        rendered_text = f"Text: '{text}' at ({x}, {y})"
        if width: rendered_text += f" W:{width}"
        rendered_text += style_desc
        self.elements_rendered.append(rendered_text)
    
    def add_table(self, data, x, y, col_widths=None, header=True):
        """Record table addition."""
        self.elements_rendered.append(f"Table: {len(data)} rows at ({x}, {y})")
    
    def add_image(self, image_path, x, y, width=None, height=None):
        """Record image addition."""
        self.elements_rendered.append(f"Image: {image_path} at ({x}, {y})")
    
    def add_chart(self, 
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
                  style: Optional[ChartStyle] = None
                  ) -> None:
        """Record chart addition."""
        details = f"Chart: {chart_type} at ({x}, {y}) W:{width} H:{height}"
        if title: details += f" Title: {title}"
        if x_label: details += f" XLabel: {x_label}"
        if y_label: details += f" YLabel: {y_label}"
        details += f" Legend: {legend}"
        if style: details += f" Style: {style.__class__.__name__}"
        self.elements_rendered.append(details)


class TestReportConfig(unittest.TestCase):
    """Tests for the ReportConfig class."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = ReportConfig(title="Test Report")
        
        self.assertEqual(config.title, "Test Report")
        self.assertEqual(config.author, "Deep Deep Research v2")
        self.assertEqual(config.page_size, "letter")
        self.assertEqual(config.orientation, "portrait")
        self.assertTrue(config.include_toc)
        self.assertTrue(config.include_page_numbers)
        self.assertEqual(config.library, ReportLibrary.REPORTLAB)
    
    def test_page_size_conversion(self):
        """Test that page size is converted correctly."""
        config = ReportConfig(title="Test", page_size="letter")
        size = config.get_page_size_tuple()
        
        self.assertEqual(size, (612, 792))  # 8.5 x 11 inches in points
        
        # Test landscape orientation
        config.orientation = "landscape"
        size = config.get_page_size_tuple()
        
        self.assertEqual(size, (792, 612))  # Rotated dimensions
    
    def test_reportlab_pagesize(self):
        """Test that ReportLab pagesize is returned correctly."""
        config = ReportConfig(title="Test", page_size="letter")
        size = config.get_reportlab_pagesize()
        
        from reportlab.lib.pagesizes import letter
        self.assertEqual(size, letter)
        
        # Test A4 size
        config.page_size = "a4"
        size = config.get_reportlab_pagesize()
        
        from reportlab.lib.pagesizes import A4
        self.assertEqual(size, A4)

    def test_text_element_creation_and_render(self):
        config = ReportConfig(title="Test")
        mock_gen = MockPDFGenerator(config)
        # Test with style_name
        te_style_name = TextElement("Hello StyleName", 10, 20, style_name="heading1")
        te_style_name.render(mock_gen)
        self.assertIn("Text: 'Hello StyleName' at (10, 20) Style: [Font: Helvetica-Bold, Size: 18", mock_gen.elements_rendered[-1])

        # Test with direct TextStyle object
        direct_style = TextStyle(font_family="Courier", font_size=10, color="#FF0000", alignment=TextAlignment.CENTER, bold=True)
        te_direct_style = TextElement("Hello DirectStyle", 30, 40, style=direct_style)
        te_direct_style.render(mock_gen)
        self.assertIn("Text: 'Hello DirectStyle' at (30, 40) Style: [Font: Courier, Size: 10, Color: #FF0000, Align: center, LineSpacing: 1.2, Bold: True, Italic: False, Underline: False]", mock_gen.elements_rendered[-1])
        
        # Test with legacy parameters (fallback)
        te_legacy = TextElement("Hello Legacy", 50, 60, font_size=14, font_name="Times-Roman", color="#00FF00", align="right")
        te_legacy.render(mock_gen)
        self.assertIn("Text: 'Hello Legacy' at (50, 60) Style: [Font: Times-Roman, Size: 14, Color: #00FF00, Align: right, LineSpacing: 1.2]", mock_gen.elements_rendered[-1])

    def test_table_element_creation_and_render(self):
        data = [["Header 1", "Header 2"], [1, 2], [3, 4]]
        element = TableElement(data=data, x=10, y=20)
        element.render(MockPDFGenerator(ReportConfig(title="Test")))
        
        self.assertEqual(len(MockPDFGenerator(ReportConfig(title="Test")).elements_rendered), 1)
        self.assertIn("Table: 3 rows at (10, 20)", MockPDFGenerator(ReportConfig(title="Test")).elements_rendered[0])
        self.assertIn("(10, 20)", MockPDFGenerator(ReportConfig(title="Test")).elements_rendered[0])

    def test_list_element_creation_and_render(self):
        config = ReportConfig(title="Test")
        mock_gen = MockPDFGenerator(config)
        items = ["Item 1", "Item 2"]
        # Test with style_name
        le_style_name = ListElement(items, 10, 20, style_name="body") # Assuming body style for lists
        le_style_name.render(mock_gen)
        # Check if 'add_text' was called twice for the items with body style
        self.assertIn("Text: '• Item 1' at (10, 20) Style: [Font: Helvetica, Size: 12", mock_gen.elements_rendered[-2])
        self.assertIn("Text: '• Item 2' at (10, " , mock_gen.elements_rendered[-1]) # Check y position changes
        self.assertTrue(float(mock_gen.elements_rendered[-1].split('at (10, ')[1].split(')')[0]) > 20)

        # Test with direct TextStyle object
        direct_list_style = TextStyle(font_family="Arial", font_size=11, color="#0000FF", italic=True)
        le_direct_style = ListElement(items, 10, 100, style=direct_list_style, numbered=True)
        le_direct_style.render(mock_gen)
        self.assertIn("Text: '1. Item 1' at (10, 100) Style: [Font: Arial, Size: 11, Color: #0000FF, Align: left, LineSpacing: 1.2, Bold: False, Italic: True, Underline: False]", mock_gen.elements_rendered[-2])
        self.assertIn("Text: '2. Item 2' at (10, ", mock_gen.elements_rendered[-1])

    def test_pagebreak_element_creation_and_render(self):
        element = PageBreakElement()
        element.render(MockPDFGenerator(ReportConfig(title="Test")))
        
        self.assertEqual(len(MockPDFGenerator(ReportConfig(title="Test")).elements_rendered), 1)
        self.assertEqual("PageBreak", MockPDFGenerator(ReportConfig(title="Test")).elements_rendered[0])


class TestReportElements(unittest.TestCase):
    """Tests for the various report element classes."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = ReportConfig(title="Test Report")
        self.mock_generator = MockPDFGenerator(self.config)
    
    def test_text_element(self):
        """Test that TextElement renders correctly."""
        element = TextElement(text="Hello, World!", x=10, y=20)
        element.render(self.mock_generator)
        
        self.assertEqual(len(self.mock_generator.elements_rendered), 1)
        self.assertIn("Text: Hello, World!", self.mock_generator.elements_rendered[0])
        self.assertIn("(10, 20)", self.mock_generator.elements_rendered[0])
    
    def test_table_element(self):
        """Test that TableElement renders correctly."""
        data = [["Header 1", "Header 2"], [1, 2], [3, 4]]
        element = TableElement(data=data, x=10, y=20)
        element.render(self.mock_generator)
        
        self.assertEqual(len(self.mock_generator.elements_rendered), 1)
        self.assertIn("Table: 3 rows", self.mock_generator.elements_rendered[0])
        self.assertIn("(10, 20)", self.mock_generator.elements_rendered[0])
    
    def test_page_break_element(self):
        """Test that PageBreakElement renders correctly."""
        element = PageBreakElement()
        element.render(self.mock_generator)
        
        self.assertEqual(len(self.mock_generator.elements_rendered), 1)
        self.assertEqual("PageBreak", self.mock_generator.elements_rendered[0])
    
    def test_list_element(self):
        """Test that ListElement renders correctly."""
        items = ["Item 1", "Item 2", "Item 3"]
        element = ListElement(items=items, x=10, y=20)
        element.render(self.mock_generator)
        
        self.assertEqual(len(self.mock_generator.elements_rendered), 3)  # 3 items
        for i, item_text in enumerate(self.mock_generator.elements_rendered):
            self.assertIn(f"• Item {i+1}", item_text)
    
    def test_chart_element_render(self):
        """Test that ChartElement renders correctly using the mock generator."""
        chart_data = {"x_values": [1,2], "y_series": {"A":[1,2]}}
        chart_style = ChartStyle(background_color="#ff0000")
        element = ChartElement(
            chart_type="line",
            data=chart_data,
            x=50, y=100,
            width=200, height=150,
            title="My Line Chart",
            x_label="X Axis",
            y_label="Y Axis",
            legend=False,
            style=chart_style
        )
        element.render(self.mock_generator)
        
        self.assertEqual(len(self.mock_generator.elements_rendered), 1)
        rendered_call = self.mock_generator.elements_rendered[0]
        self.assertIn("Chart: line at (50, 100) W:200 H:150", rendered_call)
        self.assertIn("Title: My Line Chart", rendered_call)
        self.assertIn("XLabel: X Axis", rendered_call)
        self.assertIn("YLabel: Y Axis", rendered_call)
        self.assertIn("Legend: False", rendered_call)
        self.assertIn("Style: ChartStyle", rendered_call)


class TestPDFReport(unittest.TestCase):
    """Tests for the PDFReport class."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = ReportConfig(title="Test Report")
        self.report = PDFReport(self.config)
    
    def test_add_element(self):
        """Test adding elements to the report."""
        element = TextElement(text="Test", x=10, y=10)
        self.report.add_element(element)
        
        self.assertEqual(len(self.report.elements), 1)
        self.assertIs(self.report.elements[0], element)
    
    def test_add_elements(self):
        """Test adding multiple elements to the report."""
        elements = [
            TextElement(text="Test 1", x=10, y=10),
            TextElement(text="Test 2", x=20, y=20)
        ]
        self.report.add_elements(elements)
        
        self.assertEqual(len(self.report.elements), 2)
        self.assertIs(self.report.elements[0], elements[0])
        self.assertIs(self.report.elements[1], elements[1])
    
    def test_generate_with_mock(self):
        """Test generating a report with a mock generator."""
        # Add some elements to the report
        self.report.add_element(TextElement(text="Test", x=10, y=10))
        self.report.add_element(PageBreakElement())
        self.report.add_element(TextElement(text="Page 2", x=10, y=10))
        
        # Create a temporary output file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            output_path = Path(tmp.name)
        
        try:
            # Override the generator creation in the generate method
            original_generate = self.report.generate
            
            def mock_generate(output_path):
                generator = MockPDFGenerator(self.config)
                return generator.generate(self.report, output_path)
            
            self.report.generate = mock_generate
            
            # Generate the report
            result_path = self.report.generate(output_path)
            
            # Check that the result path is correct
            self.assertEqual(str(result_path), str(output_path))
            
        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)
            
            # Restore original method
            self.report.generate = original_generate


class TestColorSchemeAndStyles(unittest.TestCase):
    """Tests for color schemes and style classes."""
    
    def test_color_scheme(self):
        """Test that ColorScheme provides correct colors."""
        scheme = ColorScheme()
        
        # Test default colors
        self.assertEqual(scheme.primary, "#1a73e8")  # Google Blue
        self.assertEqual(scheme.text, "#202124")     # Dark gray
        
        # Test get_color method
        self.assertEqual(scheme.get_color("primary"), "#1a73e8")
        self.assertEqual(scheme.get_color("nonexistent"), "#202124")  # Default to text
    
    def test_stylesheet(self):
        """Test that StyleSheet integrates styles correctly."""
        stylesheet = StyleSheet()
        
        # Test default styles
        self.assertEqual(stylesheet.heading1.font_size, 24)
        self.assertTrue(stylesheet.heading1.bold)
        self.assertEqual(stylesheet.body.font_size, 12)
        
        # Test applying a custom color scheme
        custom_scheme = ColorScheme(
            primary="#ff0000",  # Red
            heading="#000000",  # Black
            text="#333333"      # Dark gray
        )
        
        stylesheet.apply_color_scheme(custom_scheme)
        
        # Check that colors were applied to styles
        self.assertEqual(stylesheet.heading1.color, "#000000")
        self.assertEqual(stylesheet.body.color, "#333333")
        
        # Test to_dict method
        style_dict = stylesheet.to_dict()
        self.assertIn("heading1", style_dict)
        self.assertIn("color_scheme", style_dict)


class TestCharts(unittest.TestCase):
    """Tests for chart generation classes."""
    
    def test_line_chart(self):
        """Test creating a line chart."""
        chart = LineChart(title="Test Line Chart")
        x_values = [1, 2, 3, 4, 5]
        y_series = {"Series 1": [10, 15, 13, 17, 20]}
        
        fig, ax = chart.create_chart(x_values, y_series)
        
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)
        
        # Test saving to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            output_path = Path(tmp.name)
        
        try:
            saved_path = chart.save_to_file(output_path)
            self.assertTrue(os.path.exists(saved_path))
            self.assertGreater(os.path.getsize(saved_path), 0)
        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_pie_chart(self):
        """Test creating a pie chart."""
        chart = PieChart(title="Test Pie Chart")
        labels = ["A", "B", "C", "D"]
        values = [15, 30, 25, 30]
        
        fig, ax = chart.create_chart(labels, values)
        
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax)


class TestReportLabGenerator(unittest.TestCase):
    """Tests for the ReportLab PDF generator implementation."""
    
    def test_initialization(self):
        """Test that the ReportLab generator initializes correctly."""
        config = ReportConfig(title="Test Report", page_size="letter")
        generator = ReportLabPDFGenerator(config)
        
        self.assertEqual(generator.config, config)
        self.assertIsNone(generator.canvas)
        self.assertIsNone(generator.doc)
        self.assertEqual(generator.current_y, 0)
    
    def test_parse_color(self):
        """Test parsing color strings."""
        config = ReportConfig(title="Test Report")
        generator = ReportLabPDFGenerator(config)
        
        # Test hex color
        r, g, b = generator._parse_color("#ff0000")
        self.assertAlmostEqual(r, 1.0)  # Red
        self.assertAlmostEqual(g, 0.0)  # No green
        self.assertAlmostEqual(b, 0.0)  # No blue
        
        # Test named color (defaults to black in the implementation)
        r, g, b = generator._parse_color("red")
        self.assertAlmostEqual(r, 0.0)
        self.assertAlmostEqual(g, 0.0)
        self.assertAlmostEqual(b, 0.0)


class TestFPDFGenerator(unittest.TestCase):
    """Tests for the FPDF PDF generator implementation."""
    
    def test_initialization(self):
        """Test that the FPDF generator initializes correctly."""
        config = ReportConfig(title="Test Report", page_size="letter")
        generator = FPDFGenerator(config)
        
        self.assertEqual(generator.config, config)
        self.assertIsNotNone(generator.pdf)
        self.assertGreater(generator.page_width, 0)
        self.assertGreater(generator.page_height, 0)
    
    def test_parse_color(self):
        """Test parsing color strings."""
        config = ReportConfig(title="Test Report")
        generator = FPDFGenerator(config)
        
        # Test hex color
        r, g, b = generator._parse_color("#ff0000")
        self.assertEqual(r, 255)  # Red
        self.assertEqual(g, 0)    # No green
        self.assertEqual(b, 0)    # No blue


if __name__ == '__main__':
    unittest.main() 