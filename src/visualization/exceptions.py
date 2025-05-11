"""
Visualization Exceptions

This module defines exception classes specific to the visualization system.
"""

from typing import Optional, Any
from src.error_handling import ResearchError, ErrorCategory, ErrorSeverity


class VisualizationError(ResearchError):
    """Base exception class for visualization errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.OUTPUT,
            error_severity=ErrorSeverity.MEDIUM,
            component="visualization",
            **kwargs
        )


class ChartCreationError(VisualizationError):
    """Exception raised when a chart cannot be created."""
    
    def __init__(self, message: str, chart_type: Optional[str] = None, **kwargs):
        self.chart_type = chart_type
        super_message = f"Failed to create chart"
        if chart_type:
            super_message += f" of type '{chart_type}'"
        super_message += f": {message}"
        super().__init__(super_message, **kwargs)


class DataValidationError(VisualizationError):
    """Exception raised when data validation fails for visualization."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(f"Data validation error: {message}", **kwargs)


class RenderingError(VisualizationError):
    """Exception raised when a chart cannot be rendered."""
    
    def __init__(self, message: str, renderer: Optional[str] = None, **kwargs):
        self.renderer = renderer
        super_message = f"Failed to render chart"
        if renderer:
            super_message += f" with renderer '{renderer}'"
        super_message += f": {message}"
        super().__init__(super_message, **kwargs)


class ExportError(VisualizationError):
    """Exception raised when a chart cannot be exported to the desired format."""
    
    def __init__(self, message: str, format: Optional[str] = None, **kwargs):
        self.format = format
        super_message = f"Failed to export chart"
        if format:
            super_message += f" to format '{format}'"
        super_message += f": {message}"
        super().__init__(super_message, **kwargs)


class ThemeError(VisualizationError):
    """Exception raised when there's an issue with chart theming."""
    
    def __init__(self, message: str, theme_name: Optional[str] = None, **kwargs):
        self.theme_name = theme_name
        super_message = f"Theme error"
        if theme_name:
            super_message += f" for theme '{theme_name}'"
        super_message += f": {message}"
        super().__init__(super_message, **kwargs)


class ChartRecommendationError(VisualizationError):
    """Exception raised when a chart type cannot be recommended."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(f"Chart recommendation error: {message}", **kwargs)


class ReportIntegrationError(VisualizationError):
    """Exception raised when integration with research reports fails."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(f"Report integration error: {message}", **kwargs) 