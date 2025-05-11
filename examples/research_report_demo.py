#!/usr/bin/env python3
"""
Research Report Demo

This script demonstrates how to create PDF reports from research results
using the report templates.
"""

import os
import sys
import json
import random
from datetime import datetime
from pathlib import Path
import argparse

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pdf_generation import ReportLibrary
from src.pdf_generation.report_templates import (
    ReportTemplate, ResearchReportTemplate, ResearchResultsReport,
    create_report_from_research_results
)


def create_sample_research_results() -> dict:
    """Create a sample research_results.json file with dummy data."""
    timestamp = datetime.now().isoformat()
    
    return {
        "metadata": {
            "query": "Impact of artificial intelligence on climate change research",
            "timestamp": timestamp,
            "search_parameters": {
                "max_results": 10,
                "language": "en",
                "time_range": "last_year"
            }
        },
        "summary": (
            "Research on the impact of artificial intelligence on climate change "
            "reveals several promising applications. AI is being used to improve "
            "climate models, optimize energy systems, and monitor environmental "
            "changes. Machine learning algorithms help analyze large datasets from "
            "satellite imagery and sensors, leading to better predictions and insights. "
            "However, concerns exist about the environmental impact of training large "
            "AI models, which require significant computational resources and energy."
        ),
        "findings": [
            {
                "title": "AI-Enhanced Climate Modeling",
                "content": (
                    "AI techniques, particularly deep learning, are improving the "
                    "accuracy of climate models by better representing complex "
                    "physical processes. Research from Stanford University shows that "
                    "neural networks can reduce computational requirements while "
                    "maintaining or improving prediction accuracy. This enables more "
                    "detailed simulations and longer-term forecasts."
                )
            },
            {
                "title": "Smart Grid Optimization",
                "content": (
                    "Machine learning algorithms are being applied to optimize energy "
                    "grids and integrate renewable energy sources more efficiently. "
                    "Studies from MIT demonstrate that AI can improve grid stability "
                    "and reduce the need for fossil fuel backup generation by "
                    "predicting renewable energy production and demand patterns "
                    "with greater precision."
                )
            },
            {
                "title": "Environmental Monitoring",
                "content": (
                    "Computer vision and satellite imagery analysis powered by AI "
                    "enable near real-time monitoring of deforestation, ice melt, "
                    "and other environmental changes. The Global Forest Watch "
                    "program reports a 60% improvement in deforestation detection "
                    "speed when using AI-based algorithms compared to traditional "
                    "methods."
                )
            },
            {
                "title": "Carbon Footprint of AI",
                "content": (
                    "Training large AI models consumes significant energy. A study "
                    "from the University of Massachusetts found that training a single "
                    "large language model can emit as much carbon as five cars over "
                    "their lifetimes. Researchers are developing more energy-efficient "
                    "algorithms and hardware to address this concern."
                )
            }
        ],
        "sources": [
            {
                "title": "Machine Learning for Climate Science",
                "url": "https://example.com/climate-ai-research",
                "authors": ["Smith, J.", "Johnson, A."],
                "publication_date": "2023-05-15",
                "relevance": "High"
            },
            {
                "title": "Artificial Intelligence Applications in Renewable Energy",
                "url": "https://example.com/renewable-energy-ai",
                "authors": ["Garcia, M.", "Chen, L."],
                "publication_date": "2023-02-22",
                "relevance": "Medium"
            },
            {
                "title": "Environmental Impacts of Training Large AI Models",
                "url": "https://example.com/ai-carbon-footprint",
                "authors": ["Patel, R.", "Lee, S."],
                "publication_date": "2022-11-30",
                "relevance": "High"
            },
            {
                "title": "Satellite Imagery Analysis for Climate Monitoring",
                "url": "https://example.com/satellite-climate-monitoring",
                "authors": ["Brown, T.", "Williams, K."],
                "publication_date": "2023-07-10",
                "relevance": "Medium"
            },
            {
                "title": "Energy Consumption in Modern AI Research",
                "url": "https://example.com/ai-energy-consumption",
                "authors": ["Müller, H.", "Tanaka, Y."],
                "publication_date": "2023-01-05",
                "relevance": "Medium"
            }
        ],
        "conclusion": (
            "AI technologies offer significant potential for addressing climate change "
            "through improved modeling, monitoring, and optimization of resources. "
            "The benefits of these applications likely outweigh the environmental costs "
            "of training and running AI systems, especially as more energy-efficient "
            "methods are developed. Future research should focus on reducing the carbon "
            "footprint of AI while maximizing its positive impact on climate science and "
            "environmental protection. Collaboration between AI researchers and climate "
            "scientists will be crucial for developing effective, targeted solutions."
        ),
        "recommendations": [
            "Prioritize research on energy-efficient AI algorithms and hardware",
            "Establish carbon emission standards for AI research and deployment",
            "Increase funding for interdisciplinary projects combining AI and climate science",
            "Develop open-source AI tools specifically for environmental monitoring and analysis",
            "Create partnerships between tech companies, research institutions, and environmental organizations"
        ]
    }


def generate_sample_research_results_file(output_dir: Path) -> Path:
    """Generate a sample research_results.json file.
    
    Args:
        output_dir: Directory to save the file
        
    Returns:
        Path to the generated file
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Generate sample data
    research_results = create_sample_research_results()
    
    # Save to file
    json_path = output_dir / "sample_research_results.json"
    with open(json_path, 'w') as f:
        json.dump(research_results, f, indent=2)
    
    print(f"Generated sample research results: {json_path}")
    return json_path


def demo_research_report_template(output_dir: Path) -> None:
    """Demonstrate using the ResearchReportTemplate.
    
    Args:
        output_dir: Directory to save the output report
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Create a report template
    report_template = ResearchReportTemplate(
        title="AI and Climate Change Research",
        author="Deep Deep Research v2"
    )
    
    # Add a title page
    report_template.add_title_page(
        subtitle="An Analysis of Current Research and Applications"
    )
    
    # Add executive summary
    report_template.add_executive_summary(
        "This report examines the intersection of artificial intelligence and "
        "climate change research, highlighting key applications, benefits, and "
        "concerns. AI technologies are increasingly being applied to improve "
        "climate models, optimize energy systems, and monitor environmental changes, "
        "offering new tools in the fight against climate change."
    )
    
    # Add table of contents (placeholder)
    report_template.add_table_of_contents()
    
    # Add introduction section
    report_template.add_section(
        title="Introduction",
        content=(
            "Climate change represents one of the most significant challenges facing "
            "humanity today. As we seek innovative solutions to understand, mitigate, "
            "and adapt to climate change, artificial intelligence offers powerful "
            "tools that can accelerate research and implementation of climate strategies. "
            "This report explores how AI is being applied in climate science and what "
            "potential benefits and limitations exist."
        )
    )
    
    # Add a table
    applications_data = [
        ["Application Area", "AI Technology", "Benefits"],
        ["Climate Modeling", "Deep Learning", "Improved accuracy, reduced computation"],
        ["Energy Grid", "Reinforcement Learning", "Optimization, renewable integration"],
        ["Deforestation", "Computer Vision", "Real-time monitoring, early detection"],
        ["Emissions Tracking", "Predictive Analytics", "Better forecasting, policy planning"]
    ]
    
    report_template.add_table_from_data(
        title="Table 1: AI Applications in Climate Science",
        data=applications_data,
        y=250
    )
    
    # Add chart data (line chart)
    years = list(range(2018, 2024))
    ai_papers = [120, 180, 250, 320, 450, 580]
    
    line_chart_data = {
        "type": "line",
        "x_values": years,
        "y_series": {
            "Number of AI-Climate Papers": ai_papers
        }
    }
    
    # Add chart
    report_template.add_chart_from_data(
        title="Figure 1: Growth in AI-Climate Research Publications",
        chart_type="line",
        data=line_chart_data,
        y=400
    )
    
    # Add challenges section
    report_template.add_section(
        title="Challenges and Limitations",
        content=(
            "Despite its promise, applying AI to climate change faces several challenges. "
            "Data quality and availability remain inconsistent across regions, limiting "
            "the effectiveness of models in vulnerable areas. Additionally, the carbon "
            "footprint of training large AI models is significant, raising questions "
            "about the net environmental benefit of certain applications. Technical "
            "challenges also exist in representing complex Earth systems accurately "
            "within AI frameworks."
        ),
        level=2
    )
    
    # Add a conclusion with recommendations
    report_template.add_conclusion(
        conclusion_text=(
            "Artificial intelligence presents significant opportunities for advancing "
            "climate change research and implementing effective solutions. The technologies "
            "reviewed in this report demonstrate that AI can enhance our understanding of "
            "climate systems, optimize resource usage, and improve monitoring capabilities. "
            "However, responsible development is essential to ensure that the environmental "
            "costs of AI itself do not outweigh its benefits."
        ),
        recommendations=[
            "Increase funding for interdisciplinary AI-climate research",
            "Develop standards for measuring and reporting the carbon footprint of AI systems",
            "Create open datasets specifically for climate AI applications",
            "Prioritize AI applications with the highest potential climate impact",
            "Ensure AI climate solutions address equity and accessibility concerns"
        ]
    )
    
    # Generate the report
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = output_dir / f"custom_report_{today}.pdf"
    report_template.generate(output_path)
    
    print(f"Generated custom report: {output_path}")


def demo_research_results_report(output_dir: Path) -> None:
    """Demonstrate using the ResearchResultsReport with sample data.
    
    Args:
        output_dir: Directory to save the output report
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Generate sample research results file
    json_path = generate_sample_research_results_file(output_dir)
    
    # Create a report using the helper function
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = output_dir / f"auto_report_{today}.pdf"
    
    create_report_from_research_results(
        json_path=json_path,
        output_path=output_path,
        title="AI and Climate Change: Research Insights",
        library=ReportLibrary.REPORTLAB
    )
    
    print(f"Generated automatic report from JSON: {output_path}")
    
    # Create another report using the FPDF library
    output_path_fpdf = output_dir / f"auto_report_fpdf_{today}.pdf"
    
    create_report_from_research_results(
        json_path=json_path,
        output_path=output_path_fpdf,
        title="AI and Climate Change: Research Insights (FPDF Version)",
        library=ReportLibrary.FPDF
    )
    
    print(f"Generated automatic report from JSON using FPDF: {output_path_fpdf}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a research PDF report from sample data.")
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
    output_dir_path = Path(args.output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # 1. Create sample research data
    sample_results = create_sample_research_results()
    
    # Save the sample data for inspection if needed
    sample_data_path = output_dir_path / "sample_research_data.json"
    with open(sample_data_path, 'w') as f:
        json.dump(sample_results, f, indent=4)
    print(f"Sample research data saved to: {sample_data_path}")

    # 2. Create report elements from this data (simulating ResearchResultsReport logic)
    # For this demo, we'll create a simpler set of elements directly
    report_elements = generate_report_elements(sample_results)

    # 3. Define report config
    report_title = sample_results.get("metadata", {}).get("report_title", "Sample Research Report")
    report_config = ReportConfig(
        title=report_title,
        author=sample_results.get("metadata", {}).get("author", "Research Team Alpha"),
        subject=f"Research Findings for Query: {sample_results.get('metadata',{}).get('query', 'N/A')}",
        library=selected_library,
        header_text=report_title,
        footer_text="Confidential - Internal Use Only"
    )

    # 4. Generate the report using the generic `create_report_from_research_results` function
    # This function encapsulates PDFReport creation and element addition.
    create_report_from_research_results(
        research_results=sample_results, # Pass the full results dict
        config_overrides={
            'library': selected_library, 
            'title': report_title, 
            'author': sample_results.get("metadata", {}).get("author", "Research Team Alpha")
            # Any other ReportConfig fields can be overridden here
        },
        output_dir=str(output_dir_path),
        output_filename=f"research_report_demo_{selected_library.name.lower()}.pdf"
    )

    print(f"\nResearch Report Demo for {selected_library.name} complete!")
    
    print("\nReport Generation Demo Complete!")
    print("PDF files have been generated in the 'outputs' directory.") 