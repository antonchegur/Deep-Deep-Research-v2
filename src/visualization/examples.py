"""
Visualization Examples

This module provides example functions that demonstrate how to use the visualization
system's theming and styling capabilities.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional, Tuple

from .service import VisualizationService
from .types import ChartType, ChartOptions, ChartTheme, ThemeType
from .theme_manager import ThemeManager, default_theme_manager


def create_basic_themed_chart(save_path: Optional[str] = None) -> str:
    """
    Create a basic chart with a theme applied.
    
    Args:
        save_path: Optional path to save the chart image
        
    Returns:
        Path to the saved image or HTML
    """
    # Create a service
    service = VisualizationService()
    
    # Sample data
    data = {
        'x': ['A', 'B', 'C', 'D', 'E'],
        'y': [5, 7, 3, 9, 4]
    }
    
    # Create chart with light theme
    options = ChartOptions(
        title="Basic Themed Chart",
        subtitle="Using the 'light' theme",
        theme="light"
    )
    
    chart = service.create_chart(
        data=data,
        chart_type=ChartType.BAR,
        options=options
    )
    
    # Save chart to file
    if save_path:
        return service.save_chart(chart, save_path)
    else:
        return service.save_chart(chart, "output/basic_themed_chart.png")


def compare_themes(save_dir: str = "output/theme_examples") -> Dict[str, str]:
    """
    Create the same chart with different themes for comparison.
    
    Args:
        save_dir: Directory to save the chart images
        
    Returns:
        Dictionary mapping theme names to saved file paths
    """
    # Create service and ensure output directory exists
    service = VisualizationService()
    os.makedirs(save_dir, exist_ok=True)
    
    # Sample data
    data = {
        'x': list(range(10)),
        'y': np.random.normal(5, 2, 10).tolist(),
        'series': {
            'Series A': {
                'x': list(range(10)),
                'y': np.random.normal(5, 2, 10).tolist()
            },
            'Series B': {
                'x': list(range(10)),
                'y': np.random.normal(7, 1.5, 10).tolist()
            },
            'Series C': {
                'x': list(range(10)),
                'y': np.random.normal(3, 1.8, 10).tolist()
            }
        }
    }
    
    # Get list of available themes
    theme_names = default_theme_manager.list_themes()
    
    # Create charts with each theme
    saved_paths = {}
    for theme_name in theme_names:
        options = ChartOptions(
            title=f"Theme Comparison",
            subtitle=f"Using the '{theme_name}' theme",
            theme=theme_name,
            legend=True
        )
        
        chart = service.create_chart(
            data=data,
            chart_type=ChartType.LINE,
            options=options
        )
        
        # Save chart to file
        file_path = os.path.join(save_dir, f"theme_{theme_name}.png")
        service.save_chart(chart, file_path)
        saved_paths[theme_name] = file_path
    
    return saved_paths


def create_custom_theme_example(save_path: Optional[str] = None) -> Tuple[ChartTheme, str]:
    """
    Create a custom theme and apply it to a chart.
    
    Args:
        save_path: Optional path to save the chart image
        
    Returns:
        Tuple containing the created theme and path to the saved chart
    """
    # Create a theme manager
    theme_manager = ThemeManager()
    service = VisualizationService()
    
    # Create a custom theme
    custom_theme = theme_manager.create_theme(
        name="ocean",
        colors=["#003f5c", "#2f4b7c", "#665191", "#a05195", "#d45087", 
               "#f95d6a", "#ff7c43", "#ffa600"],
        background_color="#f0f8ff",  # Alice blue
        text_color="#00008b",  # Dark blue
        font_family="Georgia, serif",
        grid_color="#add8e6",  # Light blue
        axis_color="#4682b4",  # Steel blue
        line_width=2.5,
        marker_size=8
    )
    
    # Sample data
    x = np.linspace(0, 10, 100)
    y1 = np.sin(x)
    y2 = np.cos(x)
    
    data = {
        'series': {
            'Sine': {
                'x': x.tolist(),
                'y': y1.tolist()
            },
            'Cosine': {
                'x': x.tolist(),
                'y': y2.tolist()
            }
        }
    }
    
    # Create chart with custom theme
    options = ChartOptions(
        title="Sine and Cosine Waves",
        subtitle="With custom 'ocean' theme",
        theme="ocean",
        x_label="X Axis",
        y_label="Y Axis",
        grid=True,
        legend=True
    )
    
    chart = service.create_chart(
        data=data,
        chart_type=ChartType.LINE,
        options=options
    )
    
    # Save chart to file
    if save_path:
        path = service.save_chart(chart, save_path)
    else:
        path = service.save_chart(chart, "output/custom_theme_example.png")
    
    return custom_theme, path


def modify_existing_theme_example(save_path: Optional[str] = None) -> Tuple[ChartTheme, str]:
    """
    Modify an existing theme and apply it to a chart.
    
    Args:
        save_path: Optional path to save the chart image
        
    Returns:
        Tuple containing the modified theme and path to the saved chart
    """
    # Create a theme manager
    theme_manager = ThemeManager()
    service = VisualizationService()
    
    # Modify the existing dark theme
    modified_theme = theme_manager.modify_theme(
        name="dark",
        colors=["#fd7f6f", "#7eb0d5", "#b2e061", "#bd7ebe", "#ffb55a", 
               "#ffee65", "#beb9db", "#fdcce5", "#8bd3c7"],
        text_color="#ffffff",
        background_color="#111111",
        grid_color="#333333",
        line_width=2.0,
        custom_properties={"legend_fontsize": 12}
    )
    
    # Sample data
    categories = ['Category A', 'Category B', 'Category C', 'Category D', 'Category E']
    values = [15, 30, 25, 10, 20]
    
    data = {
        'x': categories,
        'y': values
    }
    
    # Create chart with modified theme
    options = ChartOptions(
        title="Category Distribution",
        subtitle="With modified 'dark' theme",
        theme="dark",
        legend=False
    )
    
    chart = service.create_chart(
        data=data,
        chart_type=ChartType.PIE,
        options=options
    )
    
    # Save chart to file
    if save_path:
        path = service.save_chart(chart, save_path)
    else:
        path = service.save_chart(chart, "output/modified_theme_example.png")
    
    return modified_theme, path


def derive_theme_example(save_path: Optional[str] = None) -> Tuple[ChartTheme, str]:
    """
    Derive a new theme from an existing one and apply it to a chart.
    
    Args:
        save_path: Optional path to save the chart image
        
    Returns:
        Tuple containing the derived theme and path to the saved chart
    """
    # Create a theme manager
    theme_manager = ThemeManager()
    service = VisualizationService()
    
    # Derive a new theme from an existing one
    derived_theme = theme_manager.derive_theme(
        base_theme_name="print",
        new_name="publication",
        text_color="#000033",  # Dark navy
        font_family="Times New Roman, serif",
        grid_color="#eeeeee",
        line_width=1.0,
        custom_properties={
            "figure_ratio": 0.618,  # Golden ratio
            "label_fontsize": 10,
            "title_fontsize": 14,
            "title_bold": True,
            "axis_linewidth": 0.5
        }
    )
    
    # Sample data - random data points
    np.random.seed(42)
    x = np.random.normal(0, 1, 100)
    y = np.random.normal(0, 1, 100)
    
    data = {
        'x': x.tolist(),
        'y': y.tolist()
    }
    
    # Create chart with derived theme
    options = ChartOptions(
        title="Scatter Plot Example",
        subtitle="With 'publication' theme derived from 'print'",
        theme="publication",
        x_label="Variable X",
        y_label="Variable Y",
        grid=True
    )
    
    chart = service.create_chart(
        data=data,
        chart_type=ChartType.SCATTER,
        options=options
    )
    
    # Save chart to file
    if save_path:
        path = service.save_chart(chart, save_path)
    else:
        path = service.save_chart(chart, "output/derived_theme_example.png")
    
    return derived_theme, path


def export_import_theme_example(save_dir: str = "output/theme_examples") -> Tuple[str, str]:
    """
    Export a theme to a file and import it back.
    
    Args:
        save_dir: Directory to save theme file and chart image
        
    Returns:
        Tuple containing path to saved theme file and chart image
    """
    # Create a theme manager and ensure output directory exists
    theme_manager = ThemeManager()
    service = VisualizationService()
    os.makedirs(save_dir, exist_ok=True)
    
    # Create a custom theme
    custom_theme = theme_manager.create_theme(
        name="vibrant",
        colors=["#ff595e", "#ffca3a", "#8ac926", "#1982c4", "#6a4c93"],
        background_color="#ffffff",
        text_color="#333333",
        font_family="Verdana, Geneva, sans-serif",
        grid_color="#f0f0f0",
        line_width=2.0,
        marker_size=8,
        custom_properties={"title_bold": True}
    )
    
    # Export the theme to JSON
    theme_path = os.path.join(save_dir, "vibrant_theme.json")
    theme_manager.export_theme("vibrant", theme_path)
    
    # Delete the theme to verify import works
    # First, register a new theme with the same name to replace it
    temp_theme = ChartTheme(
        name="vibrant",
        type=ThemeType.CUSTOM,
        colors=["#000000"],  # Different from original
        background_color="#ffffff",
        text_color="#000000",
        font_family="Arial",
        grid_color="#cccccc",
        axis_color="#000000"
    )
    theme_manager.register_theme(temp_theme)
    
    # Now import the original theme back
    theme_manager.import_theme(theme_path)
    
    # Verify the theme was imported correctly by creating a chart
    data = {
        'x': ['A', 'B', 'C', 'D', 'E'],
        'y': [12, 7, 15, 10, 9]
    }
    
    options = ChartOptions(
        title="Imported Theme Example",
        subtitle="Theme loaded from JSON file",
        theme="vibrant",
        legend=False
    )
    
    chart = service.create_chart(
        data=data,
        chart_type=ChartType.BAR,
        options=options
    )
    
    # Save chart to file
    chart_path = os.path.join(save_dir, "imported_theme_example.png")
    service.save_chart(chart, chart_path)
    
    return theme_path, chart_path


def run_all_examples(output_dir: str = "output/theme_examples") -> Dict[str, Any]:
    """
    Run all theming examples and return the results.
    
    Args:
        output_dir: Directory to save examples
        
    Returns:
        Dictionary with results from all examples
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    # Run basic themed chart example
    basic_chart_path = os.path.join(output_dir, "basic_themed_chart.png")
    results["basic_themed_chart"] = create_basic_themed_chart(basic_chart_path)
    
    # Run theme comparison example
    theme_comparison_dir = os.path.join(output_dir, "theme_comparison")
    results["theme_comparison"] = compare_themes(theme_comparison_dir)
    
    # Run custom theme example
    custom_theme_path = os.path.join(output_dir, "custom_theme_example.png")
    results["custom_theme"] = create_custom_theme_example(custom_theme_path)
    
    # Run modify theme example
    modified_theme_path = os.path.join(output_dir, "modified_theme_example.png")
    results["modified_theme"] = modify_existing_theme_example(modified_theme_path)
    
    # Run derive theme example
    derived_theme_path = os.path.join(output_dir, "derived_theme_example.png")
    results["derived_theme"] = derive_theme_example(derived_theme_path)
    
    # Run export/import theme example
    results["export_import_theme"] = export_import_theme_example(output_dir)
    
    return results


if __name__ == "__main__":
    # Run all examples if file is executed directly
    run_all_examples() 