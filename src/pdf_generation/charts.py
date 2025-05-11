"""
PDF Charts Module

This module provides classes for generating different types of charts
that can be included in PDF reports.
"""

from abc import ABC, abstractmethod
import io
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any, cast

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.pdf_generation.pdf_base import ReportElement, PDFGenerator
from src.pdf_generation.formatters import ChartStyle


class BaseChart(ABC):
    """Base class for all chart types."""
    
    def __init__(self, 
                 title: Optional[str] = None,
                 x_label: Optional[str] = None,
                 y_label: Optional[str] = None,
                 legend: bool = True,
                 style: Optional[ChartStyle] = None):
        """Initialize with common chart properties.
        
        Args:
            title: Chart title
            x_label: Label for x-axis
            y_label: Label for y-axis
            legend: Whether to display a legend
            style: Chart styling parameters
        """
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.legend = legend
        self.style = style or ChartStyle()
        self.figure: Optional[plt.Figure] = None
        self.axes: Optional[plt.Axes] = None
    
    @abstractmethod
    def create_chart(self, data: Any) -> Tuple[plt.Figure, plt.Axes]:
        """Create the chart figure and axes based on the input data."""
        pass
    
    def save_to_file(self, output_path: Union[str, Path], dpi: int = 300) -> Path:
        """Save the chart to a file."""
        if self.figure is None:
            raise ValueError("Chart has not been created yet. Call create_chart first.")
        
        output_path = Path(output_path)
        self.figure.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close(self.figure)
        return output_path
    
    def get_image_bytes(self, format: str = 'png', dpi: int = 300) -> bytes:
        """Get chart as image bytes."""
        if self.figure is None:
            raise ValueError("Chart has not been created yet. Call create_chart first.")
        
        buffer = io.BytesIO()
        self.figure.savefig(buffer, format=format, dpi=dpi, bbox_inches='tight')
        plt.close(self.figure)
        return buffer.getvalue()
    
    def apply_style(self) -> None:
        """Apply styling to the chart based on the style settings."""
        if self.figure is None or self.axes is None:
            raise ValueError("Figure and axes must be created before applying style.")
        
        # Set figure facecolor
        self.figure.set_facecolor(self.style.background_color)
        
        # Set title
        if self.title:
            self.axes.set_title(self.title, fontsize=self.style.title_font_size)
        
        # Set axis labels
        if self.x_label:
            self.axes.set_xlabel(self.x_label, fontsize=self.style.axis_font_size)
        if self.y_label:
            self.axes.set_ylabel(self.y_label, fontsize=self.style.axis_font_size)
        
        # Set tick label font size
        self.axes.tick_params(axis='both', labelsize=self.style.tick_font_size)
        
        # Set grid
        self.axes.grid(self.style.show_grid, color=self.style.grid_color)
        
        # Adjust layout
        self.figure.tight_layout()


class LineChart(BaseChart):
    """Class for creating line charts."""
    
    def create_chart(self, 
                     x_values: List[Any], 
                     y_series: Dict[str, List[float]]) -> Tuple[plt.Figure, plt.Axes]:
        """Create a line chart.
        
        Args:
            x_values: Values for the x-axis
            y_series: Dictionary mapping series names to y-values
        """
        # Create figure and axes
        self.figure, self.axes = plt.subplots(figsize=(10, 6))
        
        # Plot each series
        for i, (name, values) in enumerate(y_series.items()):
            color_idx = i % len(self.style.colors)
            self.axes.plot(
                x_values, 
                values, 
                label=name, 
                color=self.style.colors[color_idx], 
                linewidth=self.style.line_width
            )
        
        # Add legend if requested
        if self.legend and y_series:
            self.axes.legend()
        
        # Apply styling
        self.apply_style()
        
        return self.figure, self.axes


class BarChart(BaseChart):
    """Class for creating bar charts."""
    
    def create_chart(self, 
                     categories: List[str], 
                     series: Dict[str, List[float]],
                     stacked: bool = False,
                     horizontal: bool = False) -> Tuple[plt.Figure, plt.Axes]:
        """Create a bar chart.
        
        Args:
            categories: Category labels for x-axis
            series: Dictionary mapping series names to values for each category
            stacked: Whether to stack the bars
            horizontal: Whether to create a horizontal bar chart
        """
        # Create figure and axes
        self.figure, self.axes = plt.subplots(figsize=(10, 6))
        
        # Set up positions for bars
        x = np.arange(len(categories))
        width = 0.8 / len(series) if not stacked else 0.8
        
        # Plot each series
        bottom = np.zeros(len(categories)) if stacked else None
        
        for i, (name, values) in enumerate(series.items()):
            color_idx = i % len(self.style.colors)
            
            if horizontal:
                if stacked:
                    self.axes.barh(
                        x, values, height=width, label=name,
                        color=self.style.colors[color_idx], left=bottom
                    )
                    bottom = bottom + np.array(values)
                else:
                    self.axes.barh(
                        x - width/2 + i*width/len(series), values, height=width/len(series),
                        label=name, color=self.style.colors[color_idx]
                    )
            else:
                if stacked:
                    self.axes.bar(
                        x, values, width=width, label=name,
                        color=self.style.colors[color_idx], bottom=bottom
                    )
                    bottom = bottom + np.array(values)
                else:
                    self.axes.bar(
                        x - width/2 + i*width/len(series), values, width=width/len(series),
                        label=name, color=self.style.colors[color_idx]
                    )
        
        # Set category labels
        if horizontal:
            self.axes.set_yticks(x)
            self.axes.set_yticklabels(categories)
        else:
            self.axes.set_xticks(x)
            self.axes.set_xticklabels(categories)
        
        # Add legend if requested
        if self.legend and series:
            self.axes.legend()
        
        # Apply styling
        self.apply_style()
        
        return self.figure, self.axes


class PieChart(BaseChart):
    """Class for creating pie charts."""
    
    def create_chart(self, 
                     labels: List[str], 
                     values: List[float],
                     explode: Optional[List[float]] = None) -> Tuple[plt.Figure, plt.Axes]:
        """Create a pie chart.
        
        Args:
            labels: Labels for pie slices
            values: Values for pie slices
            explode: Optional list of values to "explode" (offset) slices
        """
        # Create figure and axes
        self.figure, self.axes = plt.subplots(figsize=(8, 8))
        
        # Create pie chart
        self.axes.pie(
            values, 
            labels=labels,
            explode=explode,
            colors=self.style.colors[:len(values)],
            autopct='%1.1f%%',
            shadow=False,
            startangle=90
        )
        
        # Equal aspect ratio ensures that pie is drawn as a circle
        self.axes.axis('equal')
        
        # Apply styling (modified for pie charts)
        if self.title:
            self.axes.set_title(self.title, fontsize=self.style.title_font_size)
        
        self.figure.set_facecolor(self.style.background_color)
        self.figure.tight_layout()
        
        return self.figure, self.axes


class ScatterPlot(BaseChart):
    """Class for creating scatter plots."""
    
    def create_chart(self, 
                     x_values: List[float], 
                     y_values: List[float],
                     labels: Optional[List[str]] = None,
                     sizes: Optional[List[float]] = None) -> Tuple[plt.Figure, plt.Axes]:
        """Create a scatter plot.
        
        Args:
            x_values: Values for the x-axis
            y_values: Values for the y-axis
            labels: Optional labels for points
            sizes: Optional sizes for points
        """
        # Create figure and axes
        self.figure, self.axes = plt.subplots(figsize=(10, 6))
        
        # Default size if none provided
        if sizes is None:
            sizes = [self.style.point_size * 10] * len(x_values)
        
        # Create scatter plot
        scatter = self.axes.scatter(
            x_values, 
            y_values, 
            s=sizes,
            c=self.style.colors[0],
            alpha=0.7
        )
        
        # Add labels if provided
        if labels is not None:
            for i, label in enumerate(labels):
                self.axes.annotate(label, (x_values[i], y_values[i]))
        
        # Apply styling
        self.apply_style()
        
        return self.figure, self.axes 