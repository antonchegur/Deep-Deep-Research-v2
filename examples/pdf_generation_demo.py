#!/usr/bin/env python3
"""
PDF Generation Demo

This script demonstrates the PDF Report Generation System capabilities
by creating a sample research report with various elements.
"""

import os
import sys
import random
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse # Import argparse

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pdf_generation import (
    PDFReport, ReportConfig, ReportLibrary, 
    TextElement, TableElement, ChartElement, ImageElement,
    HeaderElement, FooterElement, ListElement, PageBreakElement,
    StyleSheet, ColorScheme, TextStyle, TextAlignment
)

# Import ReportLab ParagraphStyle for specific demo adjustments if needed
from reportlab.lib.styles import ParagraphStyle as RLParagraphStyle
from reportlab.lib import colors as rl_colors


def create_sample_report(library=ReportLibrary.REPORTLAB, output_dir="outputs"):
    """Create a sample PDF report using the PDF Generation system."""
    # Create output directory if it doesn't exist
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Get current date for the report
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Create report configuration
    config = ReportConfig(
        title="Global Climate Change Research Report",
        author="Dr. Ai Scientist & The Research Team",
        subject="Comprehensive Analysis of Climate Trends",
        keywords=["climate change", "global warming", "research", "environment"],
        library=library,
        header_text="Climate Change Report - Confidential",
        footer_text="© Deep Deep Research Inc."
    )
    
    # Optionally, customize the stylesheet after config creation
    # Example: Change body text color or heading font
    config.stylesheet.body.color = "#333333"
    config.stylesheet.heading2.font_family = "Times-Roman"
    config.stylesheet.heading2.bold = True
    config.stylesheet.caption.italic = True

    # Create a PDF report
    report = PDFReport(config)
    
    # Add header and footer
    report.add_element(HeaderElement(
        text="Deep Deep Research v2",
        height=50,
        include_date=True,
        include_page_number=True
    ))
    
    report.add_element(FooterElement(
        text=f"Generated on {today}",
        height=30,
        include_page_number=True
    ))
    
    # Add title and introduction
    report.add_element(TextElement(
        text="Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        x=72, y=100, # Placeholder x,y if ReportLab makes it flow
        style_name="caption" # Use caption style
    ))
    
    report.add_element(TextElement(
        text="Introduction",
        x=72, y=130,
        style_name="heading1"
    ))
    
    intro_text = ("This report presents a comprehensive analysis of global climate trends, "
                  "focusing on temperature anomalies, CO2 concentrations, and sea level rise. "
                  "The findings are based on extensive data collected from various international "
                  "sources over the past several decades. Our goal is to provide a clear overview "
                  "of the current state of our planet's climate and highlight key areas of concern. "
                  "We will explore patterns, correlations, and potential future scenarios based on "
                  "current scientific understanding.")
    report.add_element(TextElement(
        text=intro_text,
        x=72, y=160, width=450, # width for wrapping
        style_name="body"
    ))
    
    # Add executive summary section
    report.add_element(TextElement(
        text="Executive Summary",
        x=72, y=200,
        font_size=18,
        font_name="Helvetica-Bold"
    ))
    
    report.add_element(TextElement(
        text=(
            "This report presents an analysis of climate change data "
            "collected from various sources over the past decade. "
            "The research focuses on temperature variations, CO2 emissions, "
            "and their correlation with environmental impacts. "
            "Key findings indicate a significant upward trend in global "
            "temperatures and a strong correlation with increased carbon emissions."
        ),
        x=72, y=230,
        width=450,
        font_size=12
    ))
    
    # Add page break
    report.add_element(PageBreakElement())
    
    # Add methodology section
    report.add_element(TextElement(
        text="Methodology",
        x=72, y=72,
        font_size=18,
        font_name="Helvetica-Bold"
    ))
    
    report.add_element(TextElement(
        text=(
            "Our research methodology combined data from multiple authoritative "
            "sources and applied rigorous statistical analysis techniques. "
            "The following approaches were utilized:"
        ),
        x=72, y=100,
        width=450,
        font_size=12
    ))
    
    # Add list of methodology steps
    report.add_element(ListElement(
        items=[
            "Collection of temperature data from global monitoring stations",
            "Analysis of atmospheric CO2 measurements",
            "Correlation analysis between temperature and emissions",
            "Statistical modeling of future climate scenarios",
            "Validation against peer-reviewed research findings"
        ],
        x=92, y=150,
        width=430,
        numbered=True,
        font_size=12
    ))
    
    # Add data section
    report.add_element(TextElement(
        text="Data Analysis",
        x=72, y=270,
        font_size=18,
        font_name="Helvetica-Bold"
    ))
    
    report.add_element(TextElement(
        text=(
            "The following table presents a summary of annual temperature "
            "anomalies and CO2 concentrations over the past decade:"
        ),
        x=72, y=300,
        width=450,
        font_size=12
    ))
    
    # Create sample data for table
    years = list(range(2013, 2023))
    temp_anomalies = [round(0.8 + random.uniform(-0.1, 0.2), 2) for _ in range(10)]
    co2_levels = [390 + i * 2 + random.uniform(-1, 1) for i in range(10)]
    co2_levels = [round(level, 1) for level in co2_levels]
    
    # Add table with data
    report.add_element(TableElement(
        data=[
            ["Year", "Temperature Anomaly (°C)", "CO2 Concentration (ppm)"],
            *[[years[i], temp_anomalies[i], co2_levels[i]] for i in range(10)]
        ],
        x=72, y=330,
        col_widths=[100, 150, 200],
        header=True
    ))
    
    # Add page break
    report.add_element(PageBreakElement())
    
    # Add visualization section
    report.add_element(TextElement(
        text="Visualizations",
        x=72, y=72,
        font_size=18,
        font_name="Helvetica-Bold"
    ))
    
    report.add_element(TextElement(
        text="The following charts illustrate key findings from our research:",
        x=72, y=100,
        width=450,
        font_size=12
    ))
    
    # Add line chart
    report.add_element(TextElement(
        text="Figure 1: Temperature Anomalies (2013-2022)",
        x=72, y=130,
        font_size=14
    ))
    
    # Prepare line chart data
    line_plot_data = {
        "x_values": years,
        "y_series": {
            "Temperature Anomaly (°C)": temp_anomalies
        }
    }
    
    report.add_element(ChartElement(
        chart_type="line",
        data=line_plot_data,
        x=72, y=150,
        width=450,
        height=300,
        title="Global Temperature Anomalies",
        x_label="Year",
        y_label="Temperature Anomaly (°C)"
    ))
    
    # Add bar chart
    report.add_element(TextElement(
        text="Figure 2: CO2 Concentrations by Year",
        x=72, y=480,
        font_size=14
    ))
    
    # Prepare bar chart data
    bar_plot_data = {
        "categories": [str(year) for year in years],
        "series": {
            "CO2 Concentration (ppm)": co2_levels
        }
    }
    
    report.add_element(ChartElement(
        chart_type="bar",
        data=bar_plot_data,
        x=72, y=500,
        width=450,
        height=300,
        title="Atmospheric CO2 Concentrations",
        x_label="Year",
        y_label="CO2 (ppm)"
    ))
    
    # Add page break
    report.add_element(PageBreakElement())
    
    # Add pie chart 
    report.add_element(TextElement(
        text="Figure 3: Distribution of CO2 Sources",
        x=72, y=72,
        font_size=14
    ))
    
    # Prepare pie chart data
    pie_labels = ["Transportation", "Industry", "Electricity", "Agriculture", "Buildings"]
    pie_values = [29, 23, 25, 10, 13]
    
    pie_plot_data = {
        "labels": pie_labels,
        "values": pie_values
    }
    
    report.add_element(ChartElement(
        chart_type="pie",
        data=pie_plot_data,
        x=72, y=100,
        width=400,
        height=300,
        title="CO2 Emissions by Sector"
    ))
    
    # Add scatter plot
    report.add_element(TextElement(
        text="Figure 4: Correlation between Temperature and CO2",
        x=72, y=430,
        font_size=14
    ))
    
    # Prepare scatter plot data with slight correlation
    scatter_plot_data = {
        "x_values": co2_levels,
        "y_values": temp_anomalies
    }
    
    report.add_element(ChartElement(
        chart_type="scatter",
        data=scatter_plot_data,
        x=72, y=450,
        width=450,
        height=300,
        title="Temperature vs. CO2 Concentration",
        x_label="CO2 Concentration (ppm)",
        y_label="Temperature Anomaly (°C)"
    ))
    
    # Add page break
    report.add_element(PageBreakElement())
    
    # Add conclusion section
    report.add_element(TextElement(
        text="Conclusion",
        x=72, y=72,
        font_size=18,
        font_name="Helvetica-Bold"
    ))
    
    report.add_element(TextElement(
        text=(
            "Our analysis confirms the strong correlation between rising CO2 levels "
            "and global temperature anomalies. The data supports the scientific "
            "consensus on anthropogenic climate change and underscores the urgency "
            "of reducing carbon emissions.\n\n"
            "Key takeaways from this research include:"
        ),
        x=72, y=100,
        width=450,
        font_size=12
    ))
    
    # Add list of conclusions
    report.add_element(ListElement(
        items=[
            "Average global temperatures have increased consistently over the past decade",
            "CO2 concentrations continue to rise at approximately 2-3 ppm per year",
            "There is a statistically significant correlation between CO2 levels and temperature anomalies",
            "The transportation and electricity sectors represent the largest sources of carbon emissions",
            "Current trends suggest continued warming without significant intervention"
        ],
        x=92, y=160,
        width=430,
        numbered=False,
        font_size=12
    ))
    
    # Add recommendations
    report.add_element(TextElement(
        text="Recommendations",
        x=72, y=300,
        font_size=18,
        font_name="Helvetica-Bold"
    ))
    
    report.add_element(TextElement(
        text=(
            "Based on our findings, we recommend the following actions to address "
            "the challenges of climate change:"
        ),
        x=72, y=330,
        width=450,
        font_size=12
    ))
    
    # Add list of recommendations
    report.add_element(ListElement(
        items=[
            "Accelerate the transition to renewable energy sources",
            "Implement carbon pricing mechanisms to incentivize emissions reductions",
            "Increase investment in public transportation and electric vehicle infrastructure",
            "Develop more efficient industrial processes to reduce emissions",
            "Expand carbon capture and sequestration research and implementation"
        ],
        x=92, y=370,
        width=430,
        numbered=False,
        font_size=12
    ))
    
    # Example of using a direct TextStyle object for an element
    custom_style = TextStyle(
        font_family="Courier", 
        font_size=10, 
        color="#555555", 
        italic=True, 
        alignment=TextAlignment.RIGHT
    )
    report.add_element(TextElement(
        text="Report End - Internal Use Only",
        x=72, y=600, width=450,
        style=custom_style
    ))
    
    # Generate the report
    library_name = "reportlab" if library == ReportLibrary.REPORTLAB else "fpdf"
    output_path = output_dir / f"research_report_{library_name}_{today}.pdf"
    report.generate(output_path)
    
    print(f"Report generated: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a sample PDF report.")
    parser.add_argument(
        "--library", 
        type=str, 
        default="reportlab", 
        choices=["reportlab", "fpdf"],
        help="PDF library to use (reportlab or fpdf)."
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="outputs", 
        help="Directory to save the generated PDF."
    )
    args = parser.parse_args()

    selected_library = ReportLibrary.REPORTLAB if args.library.lower() == "reportlab" else ReportLibrary.FPDF
    
    # Ensure output directory exists
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    create_sample_report(library=selected_library, output_dir=args.output_dir)
    
    print("\nPDF Report Generation Demo Complete!")
    print("PDF files have been generated in the 'outputs' directory.") 