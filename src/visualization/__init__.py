"""
Data Visualization System

This module provides a comprehensive system for generating charts, graphs, and visual 
representations of data for inclusion in research reports.
"""

from .service import VisualizationService
from .types import ChartType, ChartTheme, ChartOptions, ChartPurpose, ThemeType
from .config import VisualizationConfig, default_config
from .exceptions import (
    VisualizationError, ChartCreationError, RenderingError, 
    ExportError, ThemeError, DataValidationError, ChartRecommendationError,
    ReportIntegrationError
)
from .chart_recommender import ChartRecommender
from .theme_manager import ThemeManager, default_theme_manager
from .report_integration import ReportVisualizer

__all__ = [
    'VisualizationService',
    'ChartType',
    'ChartTheme',
    'ChartOptions',
    'ChartPurpose',
    'ThemeType',
    'VisualizationConfig',
    'default_config',
    'VisualizationError',
    'ChartCreationError',
    'RenderingError',
    'ExportError',
    'ThemeError',
    'DataValidationError',
    'ChartRecommendationError',
    'ReportIntegrationError',
    'ChartRecommender',
    'ThemeManager',
    'default_theme_manager',
    'ReportVisualizer',
] 