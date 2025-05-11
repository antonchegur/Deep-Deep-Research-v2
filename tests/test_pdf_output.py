#!/usr/bin/env python3
"""
Tests for PDF Output Verification and Optimization Aspects.

This module will contain tests that:
1. Generate PDFs using the demo scripts.
2. Attempt to extract text or metadata for basic verification.
3. (Future) Could include performance benchmarks or file size checks.
"""

import os
import sys
import unittest
from pathlib import Path
import tempfile
import subprocess # For running demo scripts

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# PDF parsing library (ensure it's in requirements.txt if not already)
# Try PyPDF2 first, as it's quite common
try:
    import PyPDF2
    PDF_PARSER_AVAILABLE = True
except ImportError:
    PDF_PARSER_AVAILABLE = False
    print("PyPDF2 not found, some PDF content tests will be skipped. pip install PyPDF2")

from src.pdf_generation import ReportLibrary

# Helper function to run an example script
def run_example_script(script_name: str, library: ReportLibrary, output_dir: Path) -> Path:
    script_path = Path(__file__).resolve().parent.parent / "examples" / script_name
    output_file_name = f"{script_name.replace('.py','')}_{library.name.lower()}.pdf"
    output_pdf_path = output_dir / output_file_name
    
    cmd = [
        sys.executable, 
        str(script_path), 
        "--library", library.name.lower(), 
        "--output-dir", str(output_dir)
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    
    if result.returncode != 0:
        print(f"Error running {script_name} with {library.name}:")
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError(f"Failed to run {script_name} with {library.name}")
    
    if not output_pdf_path.exists():
        raise FileNotFoundError(f"Output PDF not found after running script: {output_pdf_path}")
        
    return output_pdf_path

class TestPDFOutputVerification(unittest.TestCase):
    def setUp(self):
        self.temp_output_dir = Path(tempfile.mkdtemp(prefix="test_pdf_outputs_"))
        print(f"Temporary output directory for PDF tests: {self.temp_output_dir}")

    def tearDown(self):
        # Clean up: Remove the temporary directory and its contents
        # for item in self.temp_output_dir.iterdir():
        #     item.unlink()
        # self.temp_output_dir.rmdir()
        # Keeping files for manual inspection for now, comment out to auto-delete
        print(f"PDFs generated in: {self.temp_output_dir}")
        pass 

    @unittest.skipIf(not PDF_PARSER_AVAILABLE, "PyPDF2 not installed, skipping PDF content tests.")
    def test_pdf_generation_demo_output(self):
        """Test pdf_generation_demo.py output for basic content."""
        for lib in [ReportLibrary.REPORTLAB, ReportLibrary.FPDF]:
            with self.subTest(library=lib.name):
                pdf_path = run_example_script("pdf_generation_demo.py", lib, self.temp_output_dir)
                self.assertTrue(pdf_path.exists())
                self.assertGreater(pdf_path.stat().st_size, 1000) # Check file is not tiny

                with open(pdf_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    self.assertGreater(len(reader.pages), 1)
                    metadata = reader.metadata
                    self.assertIn("Global Climate Change Research Report", metadata.title)
                    self.assertIn("Dr. Ai Scientist", metadata.author)
                    
                    first_page_text = reader.pages[0].extract_text()
                    self.assertIn("Introduction", first_page_text)
                    self.assertIn("Global average temperatures", first_page_text)
                    # Add more specific text checks based on demo content
                    if lib == ReportLibrary.REPORTLAB:
                        # ReportLab often renders charts as vector, text might be part of stream
                        self.assertIn("Global Temperature Anomalies", first_page_text)
                    # FPDF charts are images, text won't be directly in page stream for charts

    @unittest.skipIf(not PDF_PARSER_AVAILABLE, "PyPDF2 not installed, skipping PDF content tests.")
    def test_research_report_demo_output(self):
        """Test research_report_demo.py output for basic content."""
        for lib in [ReportLibrary.REPORTLAB, ReportLibrary.FPDF]:
            with self.subTest(library=lib.name):
                pdf_path = run_example_script("research_report_demo.py", lib, self.temp_output_dir)
                self.assertTrue(pdf_path.exists())
                self.assertGreater(pdf_path.stat().st_size, 1000)

                with open(pdf_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    self.assertGreater(len(reader.pages), 0)
                    metadata = reader.metadata
                    self.assertIn("Sample Research Report", metadata.title) # Default title from demo
                    self.assertIn("Research Team Alpha", metadata.author) 
                    
                    first_page_text = reader.pages[0].extract_text()
                    self.assertIn("Executive Summary", first_page_text)
                    self.assertIn("Key Findings", first_page_text)
                    # Add more specific text checks

if __name__ == "__main__":
    unittest.main() 