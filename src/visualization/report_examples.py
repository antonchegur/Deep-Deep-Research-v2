"""
Report Integration Examples

This module provides example functions that demonstrate how to integrate
visualizations into research reports using the visualization system.
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

from .service import VisualizationService
from .types import ChartType, ChartOptions, ChartPurpose
from .report_integration import ReportVisualizer


def generate_sample_data() -> Dict[str, Any]:
    """
    Generate sample data for visualization examples.
    
    Returns:
        Dictionary containing various sample datasets
    """
    np.random.seed(42)
    
    # Monthly sales data
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    sales_values = [10500, 12800, 14300, 16200, 15600, 17800, 
                    19200, 21500, 20100, 19800, 22300, 25100]
    
    # Product categories data
    categories = ['Electronics', 'Clothing', 'Home', 'Books', 'Food', 'Other']
    category_values = [32, 25, 15, 8, 12, 8]
    
    # Time series data
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    time_series = np.sin(np.arange(len(dates)) * 0.1) * 10 + np.random.normal(0, 2, len(dates)) + 50
    
    # Multi-series data
    series_data = {
        'Product A': {
            'x': months,
            'y': sales_values
        },
        'Product B': {
            'x': months,
            'y': [val * 0.7 + np.random.normal(0, 500) for val in sales_values]
        },
        'Product C': {
            'x': months,
            'y': [val * 0.5 + np.random.normal(0, 300) for val in sales_values]
        }
    }
    
    # Scatter plot data
    x_scatter = np.random.normal(50, 15, 100)
    y_scatter = x_scatter * 0.8 + np.random.normal(0, 10, 100)
    
    return {
        'monthly_sales': {
            'x': months,
            'y': sales_values
        },
        'categories': {
            'x': categories,
            'y': category_values
        },
        'time_series': {
            'x': dates.tolist(),
            'y': time_series.tolist()
        },
        'multi_series': {
            'series': series_data
        },
        'scatter_data': {
            'x': x_scatter.tolist(),
            'y': y_scatter.tolist()
        }
    }


def basic_pdf_chart_example(output_dir: str = "output/reports") -> str:
    """
    Create a basic chart for inclusion in a PDF report.
    
    Args:
        output_dir: Directory to save the output
        
    Returns:
        Path to the saved chart file
    """
    # Create a report visualizer
    report_vis = ReportVisualizer()
    
    # Generate sample data
    data = generate_sample_data()
    
    # Create a chart for a PDF report
    chart_options = ChartOptions(
        title="Monthly Sales Performance",
        subtitle="Sales figures for the past 12 months",
        theme="print",
        x_label="Month",
        y_label="Sales ($)",
        grid=True,
        width=800,
        height=500
    )
    
    chart_data = report_vis.create_chart_for_report(
        data=data['monthly_sales'],
        report_format="pdf",
        chart_type=ChartType.BAR,
        options=chart_options,
        auto_caption=True
    )
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the chart to a file
    output_path = os.path.join(output_dir, "monthly_sales_chart.png")
    with open(output_path, 'wb') as f:
        f.write(chart_data['image_data'])
    
    print(f"PDF chart saved to: {output_path}")
    print(f"Caption: {chart_data['caption']}")
    
    return output_path


def interactive_html_chart_example(output_dir: str = "output/reports") -> str:
    """
    Create an interactive chart for inclusion in an HTML report.
    
    Args:
        output_dir: Directory to save the output
        
    Returns:
        Path to the saved HTML file
    """
    # Create a report visualizer
    report_vis = ReportVisualizer()
    
    # Generate sample data
    data = generate_sample_data()
    
    # Create a chart for an HTML report
    chart_options = ChartOptions(
        title="Sales by Product Category",
        subtitle="Current year breakdown",
        theme="light",
        renderer="plotly",
        custom_options={
            "interactive": True,
            "showLegend": True
        }
    )
    
    chart_data = report_vis.create_chart_for_report(
        data=data['categories'],
        report_format="html",
        chart_type=ChartType.PIE,
        options=chart_options,
        auto_caption=True
    )
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the HTML to a file
    output_path = os.path.join(output_dir, "category_sales_chart.html")
    with open(output_path, 'w') as f:
        f.write(chart_data['html_content'])
    
    print(f"HTML chart saved to: {output_path}")
    print(f"Chart type: {chart_data['type']}")
    
    return output_path


def markdown_report_section_example(output_dir: str = "output/reports") -> str:
    """
    Create a complete markdown report section with a chart.
    
    Args:
        output_dir: Directory to save the output
        
    Returns:
        Path to the saved markdown file
    """
    # Create a report visualizer
    report_vis = ReportVisualizer()
    
    # Generate sample data
    data = generate_sample_data()
    
    # Create a chart for a markdown report
    chart_options = ChartOptions(
        title="Product Performance Comparison",
        subtitle="Monthly sales comparison across product lines",
        theme="corporate",
        x_label="Month",
        y_label="Sales ($)",
        grid=True,
        purpose=ChartPurpose.COMPARISON,
        legend=True,
        custom_options={
            "output_dir": os.path.join(output_dir, "images")
        }
    )
    
    chart_data = report_vis.create_chart_for_report(
        data=data['multi_series'],
        report_format="markdown",
        chart_type=ChartType.LINE,
        options=chart_options,
        auto_caption=True
    )
    
    # Generate a complete markdown section
    section_text = """
    This section compares the performance of our three main product lines over the past year.
    As shown in the chart below, Product A has consistently outperformed Products B and C,
    with the gap widening in the second half of the year. All products show a general upward
    trend, with seasonal fluctuations visible in the summer months.
    
    Key observations:
    - Product A shows the strongest growth trajectory
    - Product B performance peaked in August before declining slightly
    - Product C maintains the most consistent sales pattern
    """
    
    markdown_content = report_vis.generate_report_section(
        chart_data=chart_data,
        section_title="Product Performance Analysis",
        section_text=section_text,
        include_caption=True,
        section_level=2
    )
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the markdown to a file
    output_path = os.path.join(output_dir, "product_comparison_section.md")
    with open(output_path, 'w') as f:
        f.write(markdown_content)
    
    print(f"Markdown report section saved to: {output_path}")
    
    return output_path


def multi_chart_report_example(output_dir: str = "output/reports") -> str:
    """
    Create a complete report with multiple charts in markdown format.
    
    Args:
        output_dir: Directory to save the output
        
    Returns:
        Path to the saved markdown file
    """
    # Create a report visualizer
    report_vis = ReportVisualizer()
    
    # Generate sample data
    data = generate_sample_data()
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    image_dir = os.path.join(output_dir, "images")
    os.makedirs(image_dir, exist_ok=True)
    
    # Create markdown sections list
    md_sections = []
    
    # Add report title
    md_sections.append("# Quarterly Sales Analysis Report\n")
    
    # Add introduction
    md_sections.append("""
    ## Introduction
    
    This report presents a comprehensive analysis of sales performance for the past year.
    It includes breakdowns by product category, monthly trends, and product line comparisons.
    The visualizations in this report are generated automatically based on sales data from our CRM system.
    """)
    
    # 1. Monthly Sales Bar Chart
    bar_options = ChartOptions(
        title="Monthly Sales Performance",
        subtitle="Sales figures for the past 12 months",
        theme="print",
        x_label="Month",
        y_label="Sales ($)",
        grid=True,
        purpose=ChartPurpose.TREND,
        custom_options={"output_dir": image_dir}
    )
    
    bar_chart = report_vis.create_chart_for_report(
        data=data['monthly_sales'],
        report_format="markdown",
        chart_type=ChartType.BAR,
        options=bar_options
    )
    
    bar_section = report_vis.generate_report_section(
        chart_data=bar_chart,
        section_title="Monthly Sales Trends",
        section_text="The chart below shows the monthly sales figures for the past year. " +
                   "There is a clear upward trend, with particularly strong performance " +
                   "in the latter part of the year.",
        section_level=2
    )
    md_sections.append(bar_section)
    
    # 2. Category Pie Chart
    pie_options = ChartOptions(
        title="Sales by Product Category",
        subtitle="Current year breakdown",
        theme="corporate",
        purpose=ChartPurpose.COMPOSITION,
        legend=True,
        custom_options={"output_dir": image_dir}
    )
    
    pie_chart = report_vis.create_chart_for_report(
        data=data['categories'],
        report_format="markdown",
        chart_type=ChartType.PIE,
        options=pie_options
    )
    
    pie_section = report_vis.generate_report_section(
        chart_data=pie_chart,
        section_title="Product Category Analysis",
        section_text="The pie chart below shows the breakdown of sales by product category. " +
                   "Electronics continues to be our strongest category, followed by Clothing and Home goods.",
        section_level=2
    )
    md_sections.append(pie_section)
    
    # 3. Product Comparison Line Chart
    line_options = ChartOptions(
        title="Product Line Comparison",
        subtitle="Monthly sales across product lines",
        theme="corporate",
        x_label="Month",
        y_label="Sales ($)",
        grid=True,
        purpose=ChartPurpose.COMPARISON,
        legend=True,
        custom_options={"output_dir": image_dir}
    )
    
    line_chart = report_vis.create_chart_for_report(
        data=data['multi_series'],
        report_format="markdown",
        chart_type=ChartType.LINE,
        options=line_options
    )
    
    line_section = report_vis.generate_report_section(
        chart_data=line_chart,
        section_title="Product Line Performance",
        section_text="This chart compares the performance of our three main product lines over time. " +
                   "Product A consistently outperforms the other lines, though all products show growth.",
        section_level=2
    )
    md_sections.append(line_section)
    
    # 4. Scatter Plot for Correlation Analysis
    scatter_options = ChartOptions(
        title="Marketing vs. Sales Correlation",
        subtitle="Impact of marketing spend on sales",
        theme="scientific",
        x_label="Marketing Investment ($)",
        y_label="Sales Return ($)",
        grid=True,
        purpose=ChartPurpose.RELATIONSHIP,
        custom_options={"output_dir": image_dir}
    )
    
    scatter_chart = report_vis.create_chart_for_report(
        data=data['scatter_data'],
        report_format="markdown",
        chart_type=ChartType.SCATTER,
        options=scatter_options
    )
    
    scatter_section = report_vis.generate_report_section(
        chart_data=scatter_chart,
        section_title="Marketing ROI Analysis",
        section_text="The scatter plot below shows the relationship between marketing investment " +
                   "and sales returns. There is a clear positive correlation, suggesting that " +
                   "our marketing efforts are generally effective.",
        section_level=2
    )
    md_sections.append(scatter_section)
    
    # Add conclusions
    md_sections.append("""
    ## Conclusions and Recommendations
    
    Based on the analysis presented in this report, we can draw the following conclusions:
    
    1. Overall sales are trending upward, with strong performance in Q4
    2. Electronics remains our strongest product category
    3. Product A outperforms other product lines and should be the focus of future investment
    4. Marketing expenditure shows a positive correlation with sales
    
    We recommend:
    
    - Increasing inventory for Product A in anticipation of continued growth
    - Reviewing the marketing strategy for Product C to improve performance
    - Investigating seasonal variations to better prepare for demand fluctuations
    - Exploring expansion opportunities in the Electronics category
    """)
    
    # Combine all sections and save the report
    full_report = "\n\n".join(md_sections)
    output_path = os.path.join(output_dir, "quarterly_sales_report.md")
    with open(output_path, 'w') as f:
        f.write(full_report)
    
    print(f"Complete report saved to: {output_path}")
    
    return output_path


def run_all_examples(output_dir: str = "output/reports") -> Dict[str, str]:
    """
    Run all report integration examples.
    
    Args:
        output_dir: Directory to save the outputs
        
    Returns:
        Dictionary with paths to all generated files
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    # Run the PDF chart example
    pdf_dir = os.path.join(output_dir, "pdf")
    results["pdf_chart"] = basic_pdf_chart_example(pdf_dir)
    
    # Run the HTML chart example
    html_dir = os.path.join(output_dir, "html")
    results["html_chart"] = interactive_html_chart_example(html_dir)
    
    # Run the markdown section example
    md_dir = os.path.join(output_dir, "markdown")
    results["markdown_section"] = markdown_report_section_example(md_dir)
    
    # Run the multi-chart report example
    report_dir = os.path.join(output_dir, "full_report")
    results["full_report"] = multi_chart_report_example(report_dir)
    
    return results


if __name__ == "__main__":
    # Run all examples if file is executed directly
    run_all_examples() 