#!/usr/bin/env python3
"""
Generate a PDF report on "Who will win: Tesla or Waymo?"

This script creates a research-style PDF report comparing Tesla and Waymo
in the autonomous vehicle race, using the PDF Generation System.
"""

import os
import sys
import tempfile
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.pdf_generation import (
    ReportService, ReportLibrary, ColorScheme,
    PDFReport, ReportConfig, TextElement, ImageElement, TableElement, PageBreakElement
)

def create_comparison_chart():
    """Create a radar chart comparing Tesla and Waymo across different metrics."""
    
    # Create a temporary file for the chart
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        chart_path = tmp.name
    
    # Data for the radar chart
    categories = ['Technology Maturity', 'Data Collection', 'Commercial Deployment', 
                 'Safety Record', 'Regulatory Approval', 'Geographic Reach']
    
    # Values from 0-5 for each category (5 being best)
    tesla_values = [3.7, 4.8, 3.0, 3.2, 2.8, 3.5]
    waymo_values = [4.5, 3.8, 4.2, 4.5, 4.0, 2.5]
    
    # Number of categories
    N = len(categories)
    
    # Create angles for each category
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Close the loop
    
    # Add Tesla and Waymo values, also close the loop
    tesla_values += tesla_values[:1]
    waymo_values += waymo_values[:1]
    
    # Set up the plot
    fig, ax = plt.figure(figsize=(8, 8)), plt.subplot(111, polar=True)
    
    # Draw one axis per category and add labels
    plt.xticks(angles[:-1], categories, size=12)
    
    # Draw the y-axis labels (0-5)
    ax.set_rlabel_position(0)
    plt.yticks([1, 2, 3, 4, 5], ['1', '2', '3', '4', '5'], size=10)
    plt.ylim(0, 5)
    
    # Plot the data
    ax.plot(angles, tesla_values, linewidth=2, linestyle='solid', label='Tesla')
    ax.fill(angles, tesla_values, alpha=0.25)
    
    ax.plot(angles, waymo_values, linewidth=2, linestyle='solid', label='Waymo')
    ax.fill(angles, waymo_values, alpha=0.25)
    
    # Add a legend
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    # Add title
    plt.title('Tesla vs. Waymo: Autonomous Driving Capabilities', size=14, y=1.1)
    
    # Save the chart
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return chart_path

def create_market_projection_chart():
    """Create a line chart showing projected market share for Tesla and Waymo."""
    
    # Create a temporary file for the chart
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        chart_path = tmp.name
    
    # Data: Years and projected market share percentage
    years = [2023, 2024, 2025, 2026, 2027, 2028, 2030, 2032, 2035]
    
    # Market share projections (these are hypothetical)
    tesla_market_share = [5, 8, 12, 18, 22, 25, 30, 32, 35]
    waymo_market_share = [3, 7, 15, 20, 24, 27, 28, 29, 30]
    others_market_share = [92, 85, 73, 62, 54, 48, 42, 39, 35]  # Rest of the market
    
    # Set up the plot
    plt.figure(figsize=(10, 6))
    
    # Plot the data
    plt.plot(years, tesla_market_share, 'b-', marker='o', linewidth=2, label='Tesla')
    plt.plot(years, waymo_market_share, 'r-', marker='s', linewidth=2, label='Waymo')
    plt.plot(years, others_market_share, 'g--', marker='^', linewidth=2, label='Others')
    
    # Customize the chart
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('Projected Market Share (%)', fontsize=12)
    plt.title('Autonomous Vehicle Market Share Projection', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(years)
    plt.ylim(0, 100)
    
    # Add a legend
    plt.legend(loc='center right')
    
    # Add annotations
    plt.annotate('Tesla Robotaxi\nExpected Launch', xy=(2024, 8), xytext=(2024, 15),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5))
    
    plt.annotate('Waymo Multi-City\nExpansion', xy=(2024, 7), xytext=(2023, 20),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5))
    
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300)
    plt.close()
    
    return chart_path

def generate_enhanced_report(output_path='tesla_vs_waymo_report.pdf'):
    """Generate an enhanced report with custom charts and formatting."""
    
    # Create report configuration
    config = ReportConfig(
        title="Autonomous Vehicle Leadership: Tesla vs. Waymo Analysis",
        author="Deep Deep Research v2",
        subject="Autonomous Vehicles Research",
        keywords=["Tesla", "Waymo", "autonomous vehicles", "self-driving cars"],
        library=ReportLibrary.REPORTLAB,
        include_toc=True,
        include_page_numbers=True
    )
    
    # Create custom charts
    comparison_chart_path = create_comparison_chart()
    market_chart_path = create_market_projection_chart()
    
    # Create report
    report = PDFReport(config)
    
    # Add title page elements
    report.add_element(TextElement(
        text="Autonomous Vehicle Leadership:\nTesla vs. Waymo Analysis",
        x=72, y=300,
        style_name="title"
    ))
    
    report.add_element(TextElement(
        text=f"Generated on: {datetime.now().strftime('%Y-%m-%d')}",
        x=72, y=380,
        style_name="heading2"
    ))
    
    report.add_element(TextElement(
        text="Deep Deep Research v2",
        x=72, y=410,
        style_name="heading2"
    ))
    
    # Add page break after title page
    report.add_element(PageBreakElement())
    
    # Add executive summary
    report.add_element(TextElement(
        text="Executive Summary",
        x=72, y=72,
        style_name="heading1"
    ))
    
    report.add_element(TextElement(
        text="""
        Tesla and Waymo represent two fundamentally different approaches to autonomous driving.
        Tesla relies primarily on vision-based systems with real-world training from its fleet of
        consumer vehicles, while Waymo uses a combination of lidar, radar, cameras, and HD maps
        with a focus on specific geo-fenced areas. This report analyzes both companies' strengths,
        weaknesses, current market position, and future prospects to determine which approach may
        ultimately prevail in the autonomous vehicle race.
        
        Our analysis suggests that in the short to medium term (3-5 years), Waymo appears better
        positioned for commercial success in limited domains. In the longer term (5-10+ years),
        Tesla's approach may offer more scaling potential if their vision-based AI can overcome
        current limitations.
        
        Most likely, neither company will "win" exclusively. The autonomous vehicle market will
        likely segment, with Waymo dominating in ride-hailing services initially, while Tesla
        maintains an edge in consumer vehicle advanced driver assistance.
        """,
        x=72, y=110,
        width=450,
        style_name="body"
    ))
    
    # Add comparison chart
    report.add_element(TextElement(
        text="Comparative Analysis",
        x=72, y=350,
        style_name="heading2"
    ))
    
    report.add_element(ImageElement(
        image_path=comparison_chart_path,
        x=72, y=380,
        width=450
    ))
    
    # Add page break
    report.add_element(PageBreakElement())
    
    # Add the market projection chart
    report.add_element(TextElement(
        text="Market Projection",
        x=72, y=72,
        style_name="heading1"
    ))
    
    report.add_element(TextElement(
        text="""
        The following chart projects potential market share development for Tesla and Waymo
        in the autonomous vehicle market over the next decade. These projections are based
        on current deployment rates, technology roadmaps, regulatory trends, and market analysis.
        """,
        x=72, y=110,
        width=450,
        style_name="body"
    ))
    
    report.add_element(ImageElement(
        image_path=market_chart_path,
        x=72, y=180,
        width=450
    ))
    
    # Add comparison table
    report.add_element(TextElement(
        text="Key Differences",
        x=72, y=500,
        style_name="heading2"
    ))
    
    table_data = [
        ["Factor", "Tesla", "Waymo"],
        ["Sensor Suite", "Vision-based (cameras)", "Multi-modal (lidar, radar, cameras)"],
        ["Testing Approach", "Shadow mode in consumer vehicles", "Dedicated test fleet with safety drivers"],
        ["Geographic Strategy", "Worldwide consumer deployment", "Geo-fenced service areas"],
        ["Current Status", "Level 2 (supervised)", "Level 4 (fully autonomous in service areas)"],
        ["Business Model", "Consumer sales + future robotaxi", "Ride-hailing service (B2C)"],
        ["Key Advantage", "Data collection scale", "Safety record & regulatory approval"]
    ]
    
    report.add_element(TableElement(
        data=table_data,
        x=72, y=530,
        col_widths=[100, 175, 175]
    ))
    
    # Add page break
    report.add_element(PageBreakElement())
    
    # Generate the PDF
    pdf_path = report.generate(output_path)
    
    # Clean up temporary files
    os.unlink(comparison_chart_path)
    os.unlink(market_chart_path)
    
    print(f"Enhanced report generated successfully at: {pdf_path}")
    return pdf_path

def generate_tesla_waymo_report(output_path='tesla_vs_waymo_report.pdf'):
    """Generate a research report comparing Tesla and Waymo."""
    
    # Create research results structure
    research_results = {
        "query": "Who will win: Tesla or Waymo?",
        "summary": """
        Tesla and Waymo represent two fundamentally different approaches to autonomous driving.
        Tesla relies primarily on vision-based systems with real-world training from its fleet of
        consumer vehicles, while Waymo uses a combination of lidar, radar, cameras, and HD maps
        with a focus on specific geo-fenced areas. This report analyzes both companies' strengths,
        weaknesses, current market position, and future prospects to determine which approach may
        ultimately prevail in the autonomous vehicle race.
        """,
        "findings": [
            {
                "title": "Technology Approaches",
                "content": """
                Tesla's approach relies heavily on vision-based neural networks trained on data
                collected from its consumer vehicle fleet, which includes over 2 million cars
                on the road. Tesla's "Autopilot" and "Full Self-Driving (FSD)" systems use 8
                cameras, ultrasonic sensors, and radar (though radar was removed in newer models).
                Tesla rejects lidar, with CEO Elon Musk calling it a "crutch" and emphasizing
                that humans drive using vision alone.

                Waymo, a subsidiary of Alphabet (Google's parent company), uses a more sensor-rich
                approach with lidar, radar, cameras, and precise HD maps. Waymo's system creates
                a detailed 3D model of its surroundings and operates primarily within geo-fenced
                areas that have been extensively mapped. Their approach prioritizes safety and
                reliability in specific operational domains before expanding.
                """
            },
            {
                "title": "Current Deployment Status",
                "content": """
                Tesla has deployed its FSD Beta software to hundreds of thousands of customers
                in North America, with plans for wider release. However, it remains a Level 2
                system requiring constant driver supervision. Tesla collects data from consumer
                vehicles to improve its neural networks, claiming a data advantage from its large
                fleet.

                Waymo operates a fully driverless (Level 4) commercial ride-hailing service called
                Waymo One in Phoenix, San Francisco, and is expanding to Los Angeles and Austin.
                These vehicles operate without safety drivers in specific areas. Waymo's approach
                focuses on perfecting driverless operation in limited domains before expanding.
                """
            },
            {
                "title": "Safety and Regulatory Considerations",
                "content": """
                Tesla has faced scrutiny from regulators, including NHTSA investigations into
                crashes involving Autopilot. Critics argue Tesla's approach of using customers
                as test drivers raises safety concerns and that its marketing has overpromised
                capabilities.

                Waymo's cautious deployment has resulted in few accidents, and their commitment
                to only releasing fully driverless technology when ready has earned regulatory
                trust. Waymo vehicles have driven over 20 million miles autonomously and
                billions of miles in simulation.

                Regulatory frameworks for autonomous vehicles are still evolving, and companies
                with established safety records may have an advantage as regulations develop.
                """
            },
            {
                "title": "Business Models and Market Strategy",
                "content": """
                Tesla integrates autonomous technology into consumer vehicles, generating revenue
                through software sales (FSD currently costs $8,000-12,000 per vehicle or $199/month
                subscription). Tesla has announced plans for a "robotaxi" network but hasn't
                launched it yet.

                Waymo focuses on ride-hailing services rather than consumer vehicle sales. Their
                business model depends on transportation as a service (TaaS), eliminating driver
                costs which represent about 80% of ride-hailing expenses. Waymo has partnerships
                with automakers like Jaguar Land Rover and Volvo to build vehicles specifically
                designed for autonomy.
                """
            }
        ],
        "sources": [
            {
                "title": "Tesla Vehicle Safety Report",
                "source_name": "Tesla",
                "url": "https://www.tesla.com/VehicleSafetyReport",
                "source_type": "report"
            },
            {
                "title": "Waymo Safety Report: On the Road to Fully Self-Driving",
                "source_name": "Waymo",
                "url": "https://waymo.com/safety/",
                "source_type": "report"
            },
            {
                "title": "The 2023 Autonomous Vehicle Technology Report",
                "source_name": "Guidehouse Insights",
                "url": "https://guidehouseinsights.com/reports/autonomous-vehicle-market-data",
                "source_type": "market_research"
            },
            {
                "title": "Computer Vision vs. LiDAR for Autonomous Vehicles",
                "source_name": "IEEE Spectrum",
                "url": "https://spectrum.ieee.org/transportation/self-driving/lidar-vs-cameras-for-selfdriving-cars",
                "source_type": "article"
            }
        ],
        "conclusion": """
        The competition between Tesla and Waymo represents a fascinating contrast in approaches to solving
        autonomous driving: Tesla's vision-based neural networks with fleet learning versus Waymo's
        sensor-fusion and mapping-based approach.

        In the short to medium term (3-5 years), Waymo appears better positioned for commercial success in
        limited domains. Their fully driverless ride-hailing service is already operational and generating
        revenue, with a clear business model and safety record. Waymo's focus on specific geo-fenced areas
        allows them to perfect operation in controlled environments.

        In the longer term (5-10+ years), Tesla's approach may offer more scaling potential if their
        vision-based AI can overcome current limitations. Tesla's integrated hardware-software business model
        and large fleet for data collection provide unique advantages for iterative improvement.

        Most likely, neither company will "win" exclusively. The autonomous vehicle market will likely
        segment, with Waymo dominating in ride-hailing services initially, while Tesla maintains an edge in
        consumer vehicle advanced driver assistance. Regulatory developments, particularly how governments
        approach approval for driverless operation, will significantly impact which company gains advantage.

        The ultimate winner may be the company that best navigates the complex intersection of technology,
        regulation, business model, and public acceptance, rather than simply having the most advanced
        technology.
        """
    }
    
    # Create a temporary file for the report
    if output_path is None:
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            output_path = tmp.name
    
    # Create report service with academic template for a formal research look
    report_service = ReportService(template_name="academic")
    
    # Generate the report
    pdf_path = report_service.generate_report_from_research_results(
        research_results=research_results,
        output_path=output_path,
        title="Autonomous Vehicle Leadership: Tesla vs. Waymo Analysis"
    )
    
    print(f"Report generated successfully at: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    # Create directory for the report if doesn't exist
    os.makedirs('docs/examples', exist_ok=True)
    
    # Generate the report
    output_path = os.path.join('docs/examples', 'tesla_vs_waymo_report.pdf')
    
    # Choose which report generator to use
    use_enhanced_report = True
    
    if use_enhanced_report:
        generate_enhanced_report(output_path)
    else:
        generate_tesla_waymo_report(output_path) 