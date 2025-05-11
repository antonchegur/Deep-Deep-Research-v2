"""
Visualization Service

This module provides the main service for creating and managing data visualizations.
"""

import os
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

from .types import ChartType, ChartOptions, ChartData, ChartResult, ImageData
from .renderers.base import AbstractChartRenderer
from .renderers.matplotlib_renderer import MatplotlibRenderer
from .renderers.plotly_renderer import PlotlyRenderer
from .exceptions import (
    VisualizationError, ChartCreationError, RenderingError, 
    ThemeError, ExportError, DataValidationError
)
from .chart_recommender import ChartRecommender
from .config import VisualizationConfig, default_config
from .theme_manager import ThemeManager, default_theme_manager


class VisualizationService:
    """
    Main service for creating and managing data visualizations.
    
    This service provides:
    1. Chart creation with automatic renderer selection
    2. Theme application and management
    3. Chart export in various formats
    4. Chart type recommendation
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None, 
                theme_manager: Optional[ThemeManager] = None):
        """
        Initialize the visualization service.
        
        Args:
            config: Optional configuration to use instead of the default
            theme_manager: Optional theme manager to use instead of the default
        """
        self.config = config or default_config
        self.theme_manager = theme_manager or default_theme_manager
        
        # Initialize renderers
        self.renderers: Dict[str, AbstractChartRenderer] = {
            "matplotlib": MatplotlibRenderer(self.config.get_renderer_options("matplotlib")),
            "plotly": PlotlyRenderer(self.config.get_renderer_options("plotly"))
        }
        
        # Initialize the chart recommender
        self.recommender = ChartRecommender()
        
        # Create output directory if it doesn't exist
        os.makedirs(self.config.output_directory, exist_ok=True)
    
    def create_chart(self, data: ChartData, chart_type: Optional[ChartType] = None, 
                    options: Optional[ChartOptions] = None) -> ChartResult:
        """
        Create a chart with the given data, type, and options.
        
        Args:
            data: Data to visualize
            chart_type: Type of chart to create, or None to auto-recommend
            options: Visualization options
            
        Returns:
            ChartResult: The rendered chart
            
        Raises:
            ChartCreationError: If chart creation fails
        """
        try:
            # Make a copy of the options to avoid modifying the original
            options = options or ChartOptions()
            
            # If no chart type is specified, recommend one
            if chart_type is None:
                chart_type, recommendations = self.recommender.recommend_chart_type(data)
                
                # Apply any recommendations to the options if not already set
                for key, value in recommendations.items():
                    if not getattr(options, key, None):
                        setattr(options, key, value)
            
            # Get the correct renderer
            renderer_name = options.renderer or self.config.default_renderer
            if renderer_name not in self.renderers:
                raise ChartCreationError(
                    f"Unknown renderer '{renderer_name}'",
                    renderer=renderer_name
                )
            
            renderer = self.renderers[renderer_name]
            
            # Validate chart type support
            if not renderer.validate_chart_support(chart_type):
                raise ChartCreationError(
                    f"Chart type '{chart_type.name}' not supported by renderer '{renderer_name}'",
                    chart_type=chart_type.name,
                    renderer=renderer_name
                )
            
            # Create the chart
            chart = renderer.render_chart(data, chart_type, options)
            
            # Apply theme if specified
            if options.theme:
                try:
                    theme = self.theme_manager.get_theme(options.theme)
                    chart = renderer.apply_theme(chart, theme)
                except ThemeError as e:
                    # If the theme doesn't exist, continue with default
                    pass
            
            return chart
            
        except (DataValidationError, RenderingError, ThemeError) as e:
            # Re-raise specific errors
            raise e
        except Exception as e:
            # Wrap other errors
            raise ChartCreationError(str(e))
    
    def save_chart(self, chart: ChartResult, path: str, 
                  format: Optional[str] = None, **kwargs) -> str:
        """
        Save a chart to a file.
        
        Args:
            chart: Chart to save
            path: Output path
            format: Output format (defaults to extension from path)
            **kwargs: Additional format-specific options
            
        Returns:
            str: Path to the saved file
            
        Raises:
            ExportError: If saving fails
        """
        try:
            # Determine the renderer
            renderer_name = chart.get("renderer", self.config.default_renderer)
            if renderer_name not in self.renderers:
                raise ExportError(
                    f"Unknown renderer '{renderer_name}'",
                    renderer=renderer_name
                )
            
            renderer = self.renderers[renderer_name]
            
            # Determine the format
            if format is None:
                # Extract format from file extension
                format = Path(path).suffix.lstrip('.')
                
                if not format:
                    # Default to png if no extension
                    format = 'png'
                    path = f"{path}.{format}"
            
            # Save the chart
            return renderer.save_chart(chart, path, format, **kwargs)
            
        except Exception as e:
            raise ExportError(f"Failed to save chart: {str(e)}", path=path)
    
    def get_image_data(self, chart: ChartResult, format: str = 'png', 
                      **kwargs) -> ImageData:
        """
        Get a chart as image data.
        
        Args:
            chart: Chart to convert
            format: Output format
            **kwargs: Additional format-specific options
            
        Returns:
            ImageData: Image data as bytes
            
        Raises:
            ExportError: If image export fails
        """
        try:
            # Determine the renderer
            renderer_name = chart.get("renderer", self.config.default_renderer)
            if renderer_name not in self.renderers:
                raise ExportError(
                    f"Unknown renderer '{renderer_name}'",
                    renderer=renderer_name
                )
            
            renderer = self.renderers[renderer_name]
            
            # Get image data
            return renderer.get_image_data(chart, format, **kwargs)
            
        except Exception as e:
            raise ExportError(f"Failed to export chart: {str(e)}")
    
    def to_html(self, chart: ChartResult, **kwargs) -> str:
        """
        Convert a chart to HTML.
        
        Args:
            chart: Chart to convert
            **kwargs: Additional conversion options
            
        Returns:
            str: HTML representation of the chart
            
        Raises:
            ExportError: If HTML conversion fails
        """
        try:
            # Determine the renderer
            renderer_name = chart.get("renderer", self.config.default_renderer)
            
            # Special case: if the renderer is matplotlib, we need to use plotly
            # for HTML output since matplotlib doesn't have a native HTML format
            if renderer_name == "matplotlib":
                renderer_name = "plotly"
            
            if renderer_name not in self.renderers:
                raise ExportError(
                    f"Unknown renderer '{renderer_name}'",
                    renderer=renderer_name
                )
            
            renderer = self.renderers[renderer_name]
            
            # Get HTML
            if hasattr(renderer, 'to_html') and callable(getattr(renderer, 'to_html')):
                return renderer.to_html(chart, **kwargs)
            else:
                raise ExportError(
                    f"Renderer '{renderer_name}' does not support HTML export",
                    renderer=renderer_name
                )
            
        except Exception as e:
            raise ExportError(f"Failed to convert chart to HTML: {str(e)}")
    
    def create_theme(self, name: str, colors: List[str], background_color: str,
                    text_color: str, font_family: str, **kwargs) -> None:
        """
        Create a new theme.
        
        Args:
            name: Name for the new theme
            colors: List of colors for the theme's color palette
            background_color: Background color (hex, rgb, or name)
            text_color: Text color (hex, rgb, or name)
            font_family: Font family string
            **kwargs: Additional theme properties
            
        Returns:
            The created ChartTheme instance
            
        Raises:
            ThemeError: If theme creation fails
        """
        return self.theme_manager.create_theme(
            name=name,
            colors=colors,
            background_color=background_color,
            text_color=text_color,
            font_family=font_family,
            **kwargs
        )
    
    def get_theme(self, name: Optional[str] = None):
        """
        Get a theme by name, or the default theme if name is None.
        
        Args:
            name: Name of the theme to get, or None for the default
            
        Returns:
            The ChartTheme instance
        """
        return self.theme_manager.get_theme(name)
    
    def list_themes(self) -> List[str]:
        """
        Get a list of all available theme names.
        
        Returns:
            List of theme names
        """
        return self.theme_manager.list_themes()
    
    def set_default_theme(self, name: str) -> None:
        """
        Set the default theme.
        
        Args:
            name: Name of the theme to set as default
            
        Raises:
            ThemeError: If the theme does not exist
        """
        self.theme_manager.set_default_theme(name)
    
    def get_supported_chart_types(self, renderer_name: Optional[str] = None) -> List[ChartType]:
        """
        Get a list of chart types supported by a specific renderer or all renderers.
        
        Args:
            renderer_name: Name of the renderer to check, or None for all renderers
            
        Returns:
            List of supported ChartType values
        """
        if renderer_name:
            if renderer_name not in self.renderers:
                raise ValueError(f"Unknown renderer '{renderer_name}'")
            return self.renderers[renderer_name].get_supported_chart_types()
        else:
            # Combine supported chart types from all renderers
            all_types = set()
            for renderer in self.renderers.values():
                all_types.update(renderer.get_supported_chart_types())
            return sorted(list(all_types), key=lambda x: x.name)
    
    def generate_filename(self, prefix: str = "chart", 
                        format: str = "png", 
                        directory: Optional[str] = None) -> str:
        """
        Generate a unique filename for a chart.
        
        Args:
            prefix: Prefix for the filename
            format: File extension
            directory: Directory to put the file in (default: config.output_directory)
            
        Returns:
            str: Generated path
        """
        # Use configured output directory if none specified
        if directory is None:
            directory = self.config.output_directory
        
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Generate unique filename using timestamp
        timestamp = int(time.time() * 1000)
        filename = f"{prefix}_{timestamp}.{format}"
        
        return os.path.join(directory, filename) 