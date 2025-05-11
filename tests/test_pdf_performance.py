#!/usr/bin/env python3
"""
Performance and Cross-Platform Compatibility Tests for PDF Generation

This module tests:
1. Performance metrics for PDF generation
2. File size optimization
3. Cross-platform rendering verification (where possible)
"""

import os
import sys
import time
import unittest
from pathlib import Path
import tempfile
import subprocess
import platform
import shutil
from typing import Dict, List, Tuple

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pdf_generation.pdf_base import PDFReport, ReportConfig, ReportLibrary
from src.pdf_generation.elements import (
    TextElement, TableElement, ChartElement, PageBreakElement
)

# Try to import PDF parsing libraries for testing content
try:
    import PyPDF2
    PDF_PARSER_AVAILABLE = True
except ImportError:
    PDF_PARSER_AVAILABLE = False
    print("PyPDF2 not found, some PDF content tests will be skipped. Install with: pip install PyPDF2")


def create_test_report(library: ReportLibrary, complexity: str = "medium") -> Tuple[PDFReport, Path]:
    """
    Create a test report with configurable complexity for performance testing.
    
    Args:
        library: Which PDF library to use
        complexity: 'low', 'medium', or 'high' to control report size
    
    Returns:
        Tuple of (PDFReport object, Path to output file)
    """
    # Create temp dir for output
    output_dir = Path(tempfile.mkdtemp(prefix="pdf_perf_test_"))
    output_path = output_dir / f"performance_test_{library.name.lower()}_{complexity}.pdf"
    
    # Configure report based on complexity
    pages = 1 if complexity == "low" else 5 if complexity == "medium" else 20
    elements_per_page = 3 if complexity == "low" else 8 if complexity == "medium" else 15
    
    config = ReportConfig(
        title=f"Performance Test Report ({complexity} complexity)",
        author="Test Suite",
        library=library
    )
    
    report = PDFReport(config)
    
    # Add elements based on complexity
    for page in range(pages):
        # Add page break after first page
        if page > 0:
            report.add_element(PageBreakElement())
        
        # Add header for each page
        report.add_element(TextElement(
            text=f"Page {page+1} - {complexity.capitalize()} Complexity Test",
            x=72, y=72,
            style_name="heading1"
        ))
        
        # Add text elements
        for i in range(elements_per_page // 3):
            report.add_element(TextElement(
                text=f"This is a test paragraph {i+1} on page {page+1}. " * 5,
                x=72, y=120 + i*50,
                width=450,
                style_name="body"
            ))
        
        # Add table on some pages
        if page % 2 == 0:
            table_data = [
                ["Header 1", "Header 2", "Header 3"],
                ["Value 1", "Value 2", "Value 3"],
                ["Value 4", "Value 5", "Value 6"]
            ]
            
            if complexity == "high":
                # Add more rows for high complexity
                for i in range(10):
                    table_data.append([f"Row {i+3}, Col 1", f"Row {i+3}, Col 2", f"Row {i+3}, Col 3"])
            
            report.add_element(TableElement(
                data=table_data,
                x=72, y=300,
                header=True
            ))
        
        # Add chart on some pages
        if page % 3 == 1:
            chart_data = {
                "x_values": [1, 2, 3, 4, 5],
                "y_series": {
                    "Series A": [10, 15, 13, 17, 20],
                    "Series B": [5, 10, 8, 12, 15]
                }
            }
            
            report.add_element(ChartElement(
                chart_type="line",
                data=chart_data,
                x=72, y=400,
                width=400,
                height=300,
                title="Sample Line Chart",
                x_label="X Axis",
                y_label="Y Axis"
            ))
    
    return report, output_path


class TestPDFPerformance(unittest.TestCase):
    """Test performance and optimization aspects of PDF generation."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="pdf_performance_tests_"))
        print(f"PDF performance test files will be saved to: {self.test_dir}")
    
    def tearDown(self):
        """Clean up test environment."""
        # Comment out to keep test files for manual inspection
        # shutil.rmtree(self.test_dir)
        pass
    
    def test_generation_performance(self):
        """Test and compare PDF generation performance between libraries."""
        results = {}
        
        # Test both libraries
        for lib in [ReportLibrary.REPORTLAB, ReportLibrary.FPDF]:
            lib_results = {}
            
            # Test different complexity levels
            for complexity in ["low", "medium", "high"]:
                # Create the report
                report, output_path = create_test_report(lib, complexity)
                
                # Measure generation time
                start_time = time.time()
                report.generate(output_path)
                end_time = time.time()
                
                generation_time = end_time - start_time
                file_size = output_path.stat().st_size / 1024  # Size in KB
                
                lib_results[complexity] = {
                    "time": generation_time,
                    "size": file_size,
                    "path": str(output_path)
                }
                
                print(f"{lib.name} - {complexity} complexity: {generation_time:.2f}s, {file_size:.2f}KB")
                
                # Basic verification that file exists and is not empty
                self.assertTrue(output_path.exists())
                self.assertGreater(output_path.stat().st_size, 1000)
            
            results[lib.name] = lib_results
        
        # Compare ReportLab vs FPDF performance
        print("\nPerformance Comparison:")
        for complexity in ["low", "medium", "high"]:
            rl_time = results["REPORTLAB"][complexity]["time"]
            fpdf_time = results["FPDF"][complexity]["time"]
            rl_size = results["REPORTLAB"][complexity]["size"]
            fpdf_size = results["FPDF"][complexity]["size"]
            
            print(f"{complexity.capitalize()} Complexity:")
            print(f"  Time - ReportLab: {rl_time:.2f}s, FPDF: {fpdf_time:.2f}s, Ratio: {rl_time/fpdf_time:.2f}x")
            print(f"  Size - ReportLab: {rl_size:.2f}KB, FPDF: {fpdf_size:.2f}KB, Ratio: {rl_size/fpdf_size:.2f}x")
    
    @unittest.skipIf(not PDF_PARSER_AVAILABLE, "PyPDF2 not installed")
    def test_content_verification(self):
        """Test PDF content verification across libraries."""
        for lib in [ReportLibrary.REPORTLAB, ReportLibrary.FPDF]:
            # Create a medium complexity report
            report, output_path = create_test_report(lib, "medium")
            report.generate(output_path)
            
            # Verify content with PyPDF2
            with open(output_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                
                # Different libraries might produce different page counts
                # We'll just log it rather than checking exact count
                print(f"{lib.name} page count: {len(reader.pages)}")
                
                # Check first page content (should be consistent)
                first_page_text = reader.pages[0].extract_text()
                self.assertIn("Page 1 - Medium Complexity Test", first_page_text)
                self.assertIn("This is a test paragraph", first_page_text)
                
                # Check metadata (should be consistent)
                self.assertEqual(reader.metadata.title, "Performance Test Report (medium complexity)")
                self.assertEqual(reader.metadata.author, "Test Suite")
    
    def test_cross_platform_viewer_launch(self):
        """Test launching generated PDFs in platform-specific viewers."""
        # This test doesn't verify rendering, just tests launch capability
        current_platform = platform.system()
        
        # Create a simple test PDF
        report, output_path = create_test_report(ReportLibrary.REPORTLAB, "low")
        report.generate(output_path)
        
        # Get platform-specific commands to open the PDF
        open_commands = {
            "Darwin": ["/usr/bin/open", str(output_path)],  # macOS
            "Linux": ["xdg-open", str(output_path)],        # Linux
            "Windows": ["cmd", "/c", "start", str(output_path)]  # Windows
        }
        
        if current_platform in open_commands:
            cmd = open_commands[current_platform]
            print(f"Testing PDF viewing on {current_platform} with command: {' '.join(cmd)}")
            
            try:
                # Just test if the command runs without error (don't wait for it)
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # Wait a short time then terminate to avoid leaving processes open
                time.sleep(1)
                proc.terminate()
                print(f"Successfully launched PDF viewer for {output_path}")
            except Exception as e:
                print(f"Error launching PDF viewer: {e}")
                # Don't fail the test, as this is environment-dependent
                pass


if __name__ == "__main__":
    unittest.main() 