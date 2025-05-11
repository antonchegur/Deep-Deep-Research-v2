"""
Plotly Chart Renderer

This module provides a renderer implementation that uses Plotly to create
interactive charts and visualizations.
"""

import io
import os
from typing import Dict, List, Any, Optional, Union, Tuple

import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import pandas as pd
import numpy as np

from ..types import ChartType, ChartOptions, ChartData, ChartResult, ImageData
from ..config import VisualizationConfig, default_config
from ..exceptions import RenderingError, ThemeError
from .base import AbstractChartRenderer


class PlotlyRenderer(AbstractChartRenderer):
    """
    Chart renderer that uses Plotly to create interactive visualizations.
    
    This renderer creates interactive charts that can be displayed in web
    environments, exported to various formats, or saved as static images.
    """
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize the Plotly renderer with optional configuration options.
        
        Args:
            options: Plotly-specific configuration options
        """
        super().__init__(options)
        
        # Set default renderer if not specified
        self.options.setdefault('renderer', 'png')
        
        # Set up Plotly configuration
        pio.templates.default = "plotly_white"  # Set default template
    
    def render_chart(self, data: ChartData, chart_type: ChartType, 
                    options: Optional[ChartOptions] = None) -> ChartResult:
        """
        Render a chart of the specified type with the given data using Plotly.
        
        Args:
            data: Data to visualize
            chart_type: Type of chart to create
            options: Optional rendering options
            
        Returns:
            A Plotly Figure object
            
        Raises:
            RenderingError: If the chart cannot be rendered
        """
        try:
            # Default options if not specified
            if options is None:
                options = ChartOptions()
            
            # Convert chart data to format suitable for Plotly
            df = self._chart_data_to_dataframe(data)
            
            # Create the appropriate chart type
            if chart_type == ChartType.BAR:
                fig = self._create_bar_chart(df, data, options)
            elif chart_type == ChartType.LINE:
                fig = self._create_line_chart(df, data, options)
            elif chart_type == ChartType.SCATTER:
                fig = self._create_scatter_chart(df, data, options)
            elif chart_type == ChartType.PIE:
                fig = self._create_pie_chart(df, data, options)
            elif chart_type == ChartType.DONUT:
                fig = self._create_donut_chart(df, data, options)
            elif chart_type == ChartType.AREA:
                fig = self._create_area_chart(df, data, options)
            elif chart_type == ChartType.HISTOGRAM:
                fig = self._create_histogram_chart(df, data, options)
            elif chart_type == ChartType.BOX:
                fig = self._create_box_chart(df, data, options)
            elif chart_type == ChartType.VIOLIN:
                fig = self._create_violin_chart(df, data, options)
            elif chart_type == ChartType.HEATMAP:
                fig = self._create_heatmap_chart(df, data, options)
            elif chart_type == ChartType.BUBBLE:
                fig = self._create_bubble_chart(df, data, options)
            elif chart_type == ChartType.RADAR:
                fig = self._create_radar_chart(df, data, options)
            else:
                raise RenderingError(f"Chart type {chart_type} is not supported by Plotly renderer")
            
            # Apply general options
            self._apply_common_options(fig, options)
            
            return fig
            
        except Exception as e:
            if isinstance(e, RenderingError):
                raise e
            else:
                raise RenderingError(f"Failed to render Plotly chart: {str(e)}", renderer="plotly")
    
    def save_chart(self, chart: ChartResult, filename: str, 
                  format: Optional[str] = None, **kwargs) -> str:
        """
        Save a Plotly chart to a file.
        
        Args:
            chart: The Plotly Figure to save
            filename: Path to save the chart to
            format: Output format (e.g., 'png', 'svg', 'pdf', 'html', 'json')
            **kwargs: Additional format-specific options
            
        Returns:
            The path to the saved file
            
        Raises:
            RenderingError: If the chart cannot be saved
        """
        try:
            # Make sure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            # Get the format from the filename if not specified
            if format is None:
                _, ext = os.path.splitext(filename)
                format = ext[1:] if ext else 'png'
            
            # Adjust height and width if specified
            width = kwargs.get('width', chart.layout.width)
            height = kwargs.get('height', chart.layout.height)
            if width is not None:
                chart.update_layout(width=width)
            if height is not None:
                chart.update_layout(height=height)
            
            # Apply scale for higher resolution
            scale = kwargs.get('scale', 2)
            
            # Determine the appropriate export function
            if format.lower() in ['html', 'htm']:
                include_plotlyjs = kwargs.get('include_plotlyjs', True)
                full_html = kwargs.get('full_html', True)
                pio.write_html(
                    chart, 
                    file=filename, 
                    include_plotlyjs=include_plotlyjs,
                    full_html=full_html
                )
            elif format.lower() in ['json']:
                with open(filename, 'w') as f:
                    f.write(chart.to_json())
            else:
                # For image formats like png, jpg, svg, pdf
                pio.write_image(
                    chart,
                    filename,
                    format=format,
                    scale=scale,
                    width=width,
                    height=height
                )
            
            return filename
            
        except Exception as e:
            raise RenderingError(f"Failed to save Plotly chart: {str(e)}", renderer="plotly")
    
    def get_image_data(self, chart: ChartResult, format: str = 'png', **kwargs) -> ImageData:
        """
        Get the Plotly chart as binary image data.
        
        Args:
            chart: The Plotly Figure
            format: Output format (e.g., 'png', 'jpg', 'svg', 'pdf')
            **kwargs: Additional format-specific options
            
        Returns:
            Binary image data
            
        Raises:
            RenderingError: If the chart cannot be exported to image data
        """
        try:
            # Adjust height and width if specified
            width = kwargs.get('width', chart.layout.width)
            height = kwargs.get('height', chart.layout.height)
            if width is not None:
                chart.update_layout(width=width)
            if height is not None:
                chart.update_layout(height=height)
            
            # Apply scale for higher resolution
            scale = kwargs.get('scale', 2)
            
            # Get image data as bytes
            img_bytes = pio.to_image(
                chart,
                format=format,
                scale=scale,
                width=width,
                height=height
            )
            
            return img_bytes
            
        except Exception as e:
            raise RenderingError(f"Failed to export Plotly chart to image data: {str(e)}", renderer="plotly")
    
    def to_html(self, chart: ChartResult, **kwargs) -> str:
        """
        Convert the Plotly chart to HTML.
        
        Args:
            chart: The Plotly Figure
            **kwargs: Additional conversion options
            
        Returns:
            HTML representation of the chart
            
        Raises:
            RenderingError: If the chart cannot be converted to HTML
        """
        try:
            # Get conversion options
            include_plotlyjs = kwargs.get('include_plotlyjs', True)
            full_html = kwargs.get('full_html', True)
            include_mathjax = kwargs.get('include_mathjax', False)
            
            # Convert to HTML
            html = pio.to_html(
                chart,
                include_plotlyjs=include_plotlyjs,
                full_html=full_html,
                include_mathjax=include_mathjax
            )
            
            return html
            
        except Exception as e:
            raise RenderingError(f"Failed to convert Plotly chart to HTML: {str(e)}", renderer="plotly")
    
    def apply_theme(self, chart: ChartResult, theme_name: str) -> ChartResult:
        """
        Apply a theme to a Plotly chart.
        
        Args:
            chart: The Plotly Figure
            theme_name: Name of the theme to apply
            
        Returns:
            The chart with the theme applied
            
        Raises:
            ThemeError: If the theme cannot be applied
        """
        try:
            # Get the theme from the configuration
            theme = default_config.get_theme(theme_name)
            
            # Create a custom Plotly template from the theme
            layout_template = {
                "paper_bgcolor": theme.background_color,
                "plot_bgcolor": theme.background_color,
                "font": {
                    "family": theme.font_family,
                    "color": theme.text_color
                },
                "colorway": theme.colors,
                "xaxis": {
                    "gridcolor": theme.grid_color,
                    "linecolor": theme.axis_color
                },
                "yaxis": {
                    "gridcolor": theme.grid_color,
                    "linecolor": theme.axis_color
                }
            }
            
            # Apply the template to the chart
            chart.update_layout(**layout_template)
            
            return chart
            
        except Exception as e:
            if isinstance(e, ThemeError):
                raise e
            else:
                raise ThemeError(f"Failed to apply theme to Plotly chart: {str(e)}", theme_name=theme_name)
    
    def _chart_data_to_dataframe(self, data: ChartData) -> pd.DataFrame:
        """Convert ChartData to a pandas DataFrame suitable for Plotly."""
        # Initialize list to store individual data point dictionaries
        data_dicts = []
        
        # Process all data points
        for point in data.data_points:
            # Create dictionary for the current point
            point_dict = {
                'x': point.x,
                'y': point.y
            }
            
            # Add optional attributes if they exist
            if point.label is not None:
                point_dict['label'] = point.label
            if point.group is not None:
                point_dict['group'] = point.group
            if point.size is not None:
                point_dict['size'] = point.size
            if point.color is not None:
                point_dict['color'] = point.color
            
            data_dicts.append(point_dict)
        
        # Convert to DataFrame
        return pd.DataFrame(data_dicts)
    
    def _create_bar_chart(self, df: pd.DataFrame, data: ChartData, options: ChartOptions) -> ChartResult:
        """Create a bar chart using Plotly."""
        # Check for 'group' column to determine if we need a grouped bar chart
        if 'group' in df.columns:
            # Create a grouped bar chart
            if options.stacked:
                # Stacked bar chart
                fig = px.bar(
                    df, 
                    x='x', 
                    y='y', 
                    color='group',
                    barmode='stack',
                    orientation='v' if options.orientation == 'vertical' else 'h'
                )
            else:
                # Grouped bar chart
                fig = px.bar(
                    df, 
                    x='x', 
                    y='y', 
                    color='group',
                    barmode='group',
                    orientation='v' if options.orientation == 'vertical' else 'h'
                )
        else:
            # Simple bar chart
            fig = px.bar(
                df, 
                x='x', 
                y='y',
                orientation='v' if options.orientation == 'vertical' else 'h'
            )
        
        return fig
    
    def _create_line_chart(self, df: pd.DataFrame, data: ChartData, options: ChartOptions) -> ChartResult:
        """Create a line chart using Plotly."""
        if 'group' in df.columns:
            # Create a multi-line chart with groups
            fig = px.line(
                df, 
                x='x', 
                y='y', 
                color='group',
                line_shape='linear',  # or 'spline' for curved lines
                markers=True if df.shape[0] < 50 else False
            )
        else:
            # Simple line chart
            fig = px.line(
                df, 
                x='x', 
                y='y',
                line_shape='linear',
                markers=True if df.shape[0] < 50 else False
            )
        
        return fig
    
    def _create_scatter_chart(self, df: pd.DataFrame, data: ChartData, options: ChartOptions) -> ChartResult:
        """Create a scatter chart using Plotly."""
        # Determine marker size
        size = None
        if 'size' in df.columns:
            size = 'size'
        
        # Create the scatter plot
        if 'group' in df.columns:
            fig = px.scatter(
                df, 
                x='x', 
                y='y', 
                color='group',
                size=size,
                hover_name='label' if 'label' in df.columns else None,
                opacity=options.opacity
            )
        else:
            fig = px.scatter(
                df, 
                x='x', 
                y='y',
                size=size,
                hover_name='label' if 'label' in df.columns else None,
                opacity=options.opacity
            )
        
        return fig
    
    def _create_pie_chart(self, df: pd.DataFrame, data: ChartData, options: ChartOptions) -> ChartResult:
        """Create a pie chart using Plotly."""
        # Pie chart needs a series name for values and a name for each slice
        fig = px.pie(
            df, 
            values='y', 
            names='x',
            hover_name='label' if 'label' in df.columns else None,
            opacity=options.opacity
        )
        
        return fig
    
    def _create_donut_chart(self, df: pd.DataFrame, data: ChartData, options: ChartOptions) -> ChartResult:
        """Create a donut chart using Plotly."""
        # Donut is just a pie with a hole
        fig = px.pie(
            df, 
            values='y', 
            names='x',
            hover_name='label' if 'label' in df.columns else None,
            opacity=options.opacity,
            hole=0.4  # The distinguishing feature of a donut chart
        )
        
        return fig
    
    def _create_area_chart(self, df: pd.DataFrame, data: ChartData, options: ChartOptions) -> ChartResult:
        """Create an area chart using Plotly."""
        if 'group' in df.columns:
            if options.stacked:
                # Stacked area chart
                fig = px.area(
                    df, 
                    x='x', 
                    y='y', 
                    color='group',
                    line_shape='linear',
                )
            else:
                # Grouped area chart (lines with fill)
                fig = px.line(
                    df, 
                    x='x', 
                    y='y', 
                    color='group',
                    line_shape='linear',
                )
                # Add area fill to zero for each trace
                for i in range(len(fig.data)):
                    fig.data[i].fill = 'tozeroy'
        else:
            # Simple area chart
            fig = px.area(
                df, 
                x='x', 
                y='y',
                line_shape='linear',
            )
        
        return fig
    
    def _create_histogram_chart(self, df: pd.DataFrame, data: ChartData, options: ChartOptions) -> ChartResult:
        """Create a histogram using Plotly."""
        # For histograms, we primarily care about the y values
        if 'group' in df.columns:
            fig = px.histogram(
                df, 
                x='y',  # Using y values for the histogram
                color='group',
                barmode='overlay',
                opacity=0.7,
                nbins=options.custom_options.get('nbins', 30),
                histnorm=options.custom_options.get('histnorm', None)  # 'probability', 'percent', etc.
            )
        else:
            fig = px.histogram(
                df, 
                x='y',  # Using y values for the histogram
                nbins=options.custom_options.get('nbins', 30),
                histnorm=options.custom_options.get('histnorm', None)
            )
        
        return fig
    
    def _create_box_chart(self, df: pd.DataFrame, data: ChartData, options: ChartOptions) -> ChartResult:
        """Create a box plot using Plotly."""
        if 'group' in df.columns:
            fig = px.box(
                df, 
                x='group',  # Categories on x-axis
                y='y',      # Values on y-axis
                color='group',
                points='outliers'  # Show only outliers
            )
        else:
            fig = px.box(
                df, 
                y='y',  # Just values, no categories
                points='outliers'
            )
        
        return fig
    
    def _create_violin_chart(self, df: pd.DataFrame, data: ChartData, options: ChartOptions) -> ChartResult:
        """Create a violin plot using Plotly."""
        if 'group' in df.columns:
            fig = px.violin(
                df, 
                x='group',  # Categories on x-axis
                y='y',      # Values on y-axis
                color='group',
                box=True,   # Show box inside the violin
                points='outliers'  # Show only outliers
            )
        else:
            fig = px.violin(
                df, 
                y='y',  # Just values, no categories
                box=True,
                points='outliers'
            )
        
        return fig
    
    def _create_heatmap_chart(self, df: pd.DataFrame, data: ChartData, options: ChartOptions) -> ChartResult:
        """Create a heatmap using Plotly."""
        # Heatmaps typically need to pivot the data to get a 2D grid
        if 'group' in df.columns:
            # Pivot to create a matrix suitable for a heatmap
            pivot_df = df.pivot(index='group', columns='x', values='y')
            # Create heatmap from pivot table
            fig = px.imshow(
                pivot_df,
                color_continuous_scale=options.custom_options.get('colorscale', 'Viridis'),
                zmin=options.custom_options.get('zmin', None),
                zmax=options.custom_options.get('zmax', None)
            )
        else:
            # Without grouping, we need to reshape the data
            # Simple case: treat each row as a separate series
            # This is a simplification and may not work for all data
            matrix = df.pivot_table(index=df.index // 10, columns=df.index % 10, values='y', aggfunc='first')
            fig = px.imshow(
                matrix,
                color_continuous_scale=options.custom_options.get('colorscale', 'Viridis'),
                zmin=options.custom_options.get('zmin', None),
                zmax=options.custom_options.get('zmax', None)
            )
        
        return fig
    
    def _create_bubble_chart(self, df: pd.DataFrame, data: ChartData, options: ChartOptions) -> ChartResult:
        """Create a bubble chart using Plotly."""
        # Bubble charts are scatter plots with size
        # We need x, y, size, and optionally color/group
        size_values = df['size'] if 'size' in df.columns else None
        
        if 'group' in df.columns:
            fig = px.scatter(
                df, 
                x='x', 
                y='y', 
                size=size_values,
                color='group',
                hover_name='label' if 'label' in df.columns else None,
                opacity=options.opacity,
                size_max=options.custom_options.get('size_max', 50)
            )
        else:
            fig = px.scatter(
                df, 
                x='x', 
                y='y',
                size=size_values,
                hover_name='label' if 'label' in df.columns else None,
                opacity=options.opacity,
                size_max=options.custom_options.get('size_max', 50)
            )
        
        return fig
    
    def _create_radar_chart(self, df: pd.DataFrame, data: ChartData, options: ChartOptions) -> ChartResult:
        """Create a radar chart using Plotly."""
        # Radar charts (polar charts) need categories and values
        if 'group' in df.columns:
            # Group the data by the group column
            groups = df['group'].unique()
            fig = go.Figure()
            
            for group in groups:
                group_df = df[df['group'] == group]
                fig.add_trace(go.Scatterpolar(
                    r=group_df['y'].values,
                    theta=group_df['x'].values,
                    fill='toself',
                    name=group
                ))
        else:
            # Single radar trace
            fig = go.Figure(go.Scatterpolar(
                r=df['y'].values,
                theta=df['x'].values,
                fill='toself'
            ))
        
        # Update radar layout
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, df['y'].max() * 1.1]  # Add 10% headroom
                )
            )
        )
        
        return fig
    
    def _apply_common_options(self, fig: ChartResult, options: ChartOptions) -> None:
        """Apply common chart options to a Plotly figure."""
        # Set the title
        if options.title:
            title_settings = {
                'text': options.title,
                'font': {
                    'size': options.font_size or 16
                }
            }
            
            # Add subtitle if available
            if options.subtitle:
                title_settings['text'] += f'<br><sub>{options.subtitle}</sub>'
            
            fig.update_layout(title=title_settings)
        
        # Set axis labels
        if options.x_label:
            fig.update_xaxes(title_text=options.x_label)
        if options.y_label:
            fig.update_yaxes(title_text=options.y_label)
        
        # Set axis types
        if options.x_axis_type:
            axis_type = options.x_axis_type.value.lower()
            if axis_type == 'log':
                fig.update_xaxes(type='log')
            elif axis_type == 'date':
                fig.update_xaxes(type='date')
            elif axis_type == 'category':
                fig.update_xaxes(type='category')
                
        if options.y_axis_type:
            axis_type = options.y_axis_type.value.lower()
            if axis_type == 'log':
                fig.update_yaxes(type='log')
            elif axis_type == 'date':
                fig.update_yaxes(type='date')
            elif axis_type == 'category':
                fig.update_yaxes(type='category')
        
        # Set figure size
        width = options.width or 800
        height = options.height or 600
        fig.update_layout(width=width, height=height)
        
        # Set legend
        if options.legend:
            legend_position = options.legend_position
            # Convert matplotlib-style positions to plotly positions
            position_map = {
                'best': 'auto',
                'upper right': {'x': 1, 'y': 1},
                'upper left': {'x': 0, 'y': 1},
                'lower right': {'x': 1, 'y': 0},
                'lower left': {'x': 0, 'y': 0},
                'right': {'x': 1, 'y': 0.5},
                'left': {'x': 0, 'y': 0.5},
                'center right': {'x': 1, 'y': 0.5},
                'center left': {'x': 0, 'y': 0.5},
                'center': {'x': 0.5, 'y': 0.5}
            }
            
            legend_settings = {'visible': True}
            
            # Apply position if it's recognized
            if legend_position in position_map:
                if position_map[legend_position] == 'auto':
                    pass  # Use Plotly's default
                else:
                    legend_settings.update(position_map[legend_position])
            
            fig.update_layout(legend=legend_settings)
        else:
            fig.update_layout(showlegend=False)
        
        # Set grid
        fig.update_xaxes(showgrid=options.grid)
        fig.update_yaxes(showgrid=options.grid)
        
        # Apply colors if specified
        if options.colors:
            fig.update_layout(colorway=options.colors)
        
        # Apply theme
        if options.theme:
            try:
                self.apply_theme(fig, options.theme)
            except ThemeError:
                # Fall back to default theme if specified theme not found
                pass
        
        # Apply font settings
        font_settings = {}
        if options.font_family:
            font_settings['family'] = options.font_family
        if options.font_size:
            font_settings['size'] = options.font_size
        
        if font_settings:
            fig.update_layout(font=font_settings)
        
        # Make chart interactive
        fig.update_layout(
            hovermode='closest',
            # Add additional interactive features based on options
            dragmode='zoom' if options.interactive else False,
        ) 