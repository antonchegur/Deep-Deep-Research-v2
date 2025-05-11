"""
Abstract Chart Renderer

This module defines the abstract base class for all chart renderers in the
visualization system.
"""

import abc
from typing import Dict, List, Any, Optional, Union

from ..types import ChartType, ChartOptions, ChartData, ChartResult, ChartTheme, ImageData


class AbstractChartRenderer(abc.ABC):
    """Abstract base class for chart renderers."""
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize the chart renderer with options.
        
        Args:
            options: Optional renderer-specific options
        """
        self.options = options or {}
    
    @abc.abstractmethod
    def render_chart(self, data: ChartData, chart_type: ChartType, 
                    options: Optional[ChartOptions] = None) -> ChartResult:
        """
        Render a chart with the given data, type, and options.
        
        Args:
            data: Data to visualize
            chart_type: Type of chart to create
            options: Visualization options
            
        Returns:
            ChartResult: The rendered chart
            
        Raises:
            RenderingError: If chart rendering fails
        """
        pass
    
    @abc.abstractmethod
    def apply_theme(self, chart: ChartResult, theme: ChartTheme) -> ChartResult:
        """
        Apply a theme to a chart.
        
        Args:
            chart: Chart to apply theme to
            theme: Theme to apply
            
        Returns:
            ChartResult: The chart with theme applied
            
        Raises:
            ThemeError: If theme application fails
        """
        pass
    
    @abc.abstractmethod
    def get_supported_chart_types(self) -> List[ChartType]:
        """
        Get a list of chart types supported by this renderer.
        
        Returns:
            List of supported ChartType values
        """
        pass
    
    @abc.abstractmethod
    def get_image_data(self, chart: ChartResult, format: str = 'png', 
                      **kwargs) -> ImageData:
        """
        Convert a chart to image data.
        
        Args:
            chart: Chart to convert
            format: Output format (png, jpg, svg, etc.)
            **kwargs: Additional format-specific options
            
        Returns:
            ImageData: Image data as bytes
            
        Raises:
            ExportError: If image export fails
        """
        pass
    
    @abc.abstractmethod
    def save_chart(self, chart: ChartResult, filename: str, 
                  format: Optional[str] = None, **kwargs) -> str:
        """
        Save a chart to a file.
        
        Args:
            chart: Chart to save
            filename: Output filename
            format: Output format (defaults to extension from filename)
            **kwargs: Additional format-specific options
            
        Returns:
            str: Path to the saved file
            
        Raises:
            ExportError: If saving fails
        """
        pass
    
    def validate_chart_support(self, chart_type: ChartType) -> bool:
        """
        Check if a chart type is supported by this renderer.
        
        Args:
            chart_type: Chart type to check
            
        Returns:
            bool: True if supported, False otherwise
        """
        return chart_type in self.get_supported_chart_types()
    
    def get_renderer_name(self) -> str:
        """
        Get the name of this renderer.
        
        Returns:
            str: Renderer name
        """
        return self.__class__.__name__ 