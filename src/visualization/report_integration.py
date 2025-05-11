"""
Report Integration

This module provides functionality to seamlessly integrate data visualizations
into research reports, with support for various output formats and automatic
caption generation.
"""

import os
import base64
import json
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime
import uuid

from .service import VisualizationService
from .types import ChartType, ChartOptions, ChartData, ChartResult, ChartPurpose
from .exceptions import (
    VisualizationError, ExportError, ReportIntegrationError
)
from .chart_recommender import ChartRecommender
from .config import default_config


class ReportVisualizer:
    """
    Class for integrating visualizations into research reports.
    
    This class provides functionality to:
    1. Generate visualizations in formats suitable for different report types
    2. Create descriptive captions for charts
    3. Manage visualization metadata
    4. Optimize visualizations for different report contexts
    """
    
    def __init__(self, visualization_service: Optional[VisualizationService] = None):
        """
        Initialize the report visualizer.
        
        Args:
            visualization_service: Optional visualization service to use
        """
        self.viz_service = visualization_service or VisualizationService()
        self.chart_recommender = ChartRecommender()
        
    def create_chart_for_report(self, 
                              data: Union[ChartData, Dict, List, Any],
                              report_format: str = "pdf",
                              chart_type: Optional[ChartType] = None,
                              options: Optional[Union[ChartOptions, Dict[str, Any]]] = None,
                              caption: Optional[str] = None,
                              auto_caption: bool = True,
                              include_metadata: bool = True) -> Dict[str, Any]:
        """
        Generate a chart suitable for inclusion in a research report.
        
        Args:
            data: Data to visualize
            report_format: Format of the report ('pdf', 'html', 'markdown')
            chart_type: Type of chart to create, or None to auto-recommend
            options: Visualization options
            caption: Custom caption for the chart
            auto_caption: Whether to generate an automatic caption
            include_metadata: Whether to include metadata about the chart
            
        Returns:
            Dict with chart data appropriate for the report format
            
        Raises:
            ReportIntegrationError: If chart generation fails
        """
        try:
            # Convert options to ChartOptions if provided as dict
            if options is not None and isinstance(options, dict):
                chart_options = ChartOptions()
                for key, value in options.items():
                    if hasattr(chart_options, key):
                        setattr(chart_options, key, value)
                    else:
                        chart_options.custom_options[key] = value
            else:
                chart_options = options or ChartOptions()
            
            # If no chart type is specified, recommend one
            if chart_type is None:
                chart_type, recommendations = self.chart_recommender.recommend_chart_type(data)
                
                # Apply any recommendations to the options if not already set
                for key, value in recommendations.items():
                    if not hasattr(chart_options, key) or getattr(chart_options, key) is None:
                        setattr(chart_options, key, value)
            
            # Apply appropriate theme for report context
            if not chart_options.theme:
                if report_format == "pdf":
                    chart_options.theme = "print"
                elif report_format == "html":
                    chart_options.theme = "light"
            
            # Generate the chart
            chart = self.viz_service.create_chart(data, chart_type, chart_options)
            
            # Generate caption if needed
            final_caption = caption
            if auto_caption and not caption:
                final_caption = self._generate_caption(data, chart_type, chart_options)
            
            # Generate metadata if needed
            metadata = None
            if include_metadata:
                metadata = self._generate_metadata(data, chart_type, chart_options)
            
            # Generate appropriate output format
            if report_format.lower() == "pdf":
                return self._prepare_for_pdf(chart, final_caption, metadata, chart_options)
            elif report_format.lower() == "html":
                return self._prepare_for_html(chart, final_caption, metadata, chart_options)
            elif report_format.lower() == "markdown":
                return self._prepare_for_markdown(chart, final_caption, metadata, chart_options)
            else:
                raise ReportIntegrationError(
                    f"Unsupported report format: {report_format}",
                    report_format=report_format
                )
                
        except Exception as e:
            if isinstance(e, VisualizationError):
                raise ReportIntegrationError(str(e))
            else:
                raise ReportIntegrationError(f"Failed to create chart for report: {str(e)}")
    
    def _prepare_for_pdf(self, chart: ChartResult, caption: Optional[str], 
                        metadata: Optional[Dict[str, Any]], 
                        options: ChartOptions) -> Dict[str, Any]:
        """
        Prepare a chart for inclusion in a PDF report.
        
        Args:
            chart: The chart to prepare
            caption: Caption for the chart
            metadata: Metadata about the chart
            options: Chart options
            
        Returns:
            Dict with image data and metadata suitable for PDF inclusion
        """
        # Get image format based on renderer
        format = "png"
        dpi = options.custom_options.get("dpi", 300)
        
        # Get image data
        image_data = self.viz_service.get_image_data(chart, format=format, dpi=dpi)
        
        # Generate a unique ID for the chart
        chart_id = f"chart_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
        
        # Assemble result
        result = {
            "id": chart_id,
            "format": format,
            "image_data": image_data,
            "caption": caption,
            "width": options.width or default_config.default_width,
            "height": options.height or default_config.default_height,
        }
        
        if metadata:
            result["metadata"] = metadata
        
        return result
    
    def _prepare_for_html(self, chart: ChartResult, caption: Optional[str], 
                         metadata: Optional[Dict[str, Any]], 
                         options: ChartOptions) -> Dict[str, Any]:
        """
        Prepare a chart for inclusion in an HTML report.
        
        Args:
            chart: The chart to prepare
            caption: Caption for the chart
            metadata: Metadata about the chart
            options: Chart options
            
        Returns:
            Dict with HTML or image data suitable for HTML inclusion
        """
        # Generate a unique ID for the chart
        chart_id = f"chart_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
        
        # Check if we should use interactive or static chart
        interactive = options.custom_options.get("interactive", 
                                                options.renderer == "plotly")
        
        if interactive:
            # Get HTML content
            try:
                html_content = self.viz_service.to_html(chart)
                
                # Assemble result
                result = {
                    "id": chart_id,
                    "type": "interactive",
                    "html_content": html_content,
                    "caption": caption,
                    "width": options.width or default_config.default_width,
                    "height": options.height or default_config.default_height,
                }
            except ExportError:
                # Fallback to static image if HTML export fails
                interactive = False
        
        if not interactive:
            # Get image as data URL
            format = "png"
            image_data = self.viz_service.get_image_data(chart, format=format)
            data_url = f"data:image/{format};base64,{base64.b64encode(image_data).decode('utf-8')}"
            
            # Assemble result
            result = {
                "id": chart_id,
                "type": "static",
                "data_url": data_url,
                "caption": caption,
                "width": options.width or default_config.default_width,
                "height": options.height or default_config.default_height,
            }
        
        if metadata:
            result["metadata"] = metadata
        
        return result
    
    def _prepare_for_markdown(self, chart: ChartResult, caption: Optional[str], 
                            metadata: Optional[Dict[str, Any]], 
                            options: ChartOptions) -> Dict[str, Any]:
        """
        Prepare a chart for inclusion in a Markdown report.
        
        Args:
            chart: The chart to prepare
            caption: Caption for the chart
            metadata: Metadata about the chart
            options: Chart options
            
        Returns:
            Dict with image path or data URL suitable for Markdown inclusion
        """
        # Generate a unique filename
        timestamp = int(time.time() * 1000)
        filename = f"chart_{timestamp}.png"
        
        # Determine if we should embed or save to file
        embed = options.custom_options.get("embed_images", False)
        
        if embed:
            # Get image as data URL for embedding
            format = "png"
            image_data = self.viz_service.get_image_data(chart, format=format)
            data_url = f"data:image/{format};base64,{base64.b64encode(image_data).decode('utf-8')}"
            
            # Assemble result
            result = {
                "type": "embedded",
                "data_url": data_url,
                "caption": caption,
                "markdown": f"![{caption or 'Chart'}]({data_url})",
            }
        else:
            # Save to file in the output directory
            output_dir = options.custom_options.get("output_dir", "output/charts")
            os.makedirs(output_dir, exist_ok=True)
            
            # Save the chart to file
            file_path = os.path.join(output_dir, filename)
            saved_path = self.viz_service.save_chart(chart, file_path)
            
            # Create a relative path for markdown linking
            rel_path = os.path.relpath(saved_path, os.getcwd())
            
            # Assemble result
            result = {
                "type": "file",
                "path": saved_path,
                "relative_path": rel_path,
                "caption": caption,
                "markdown": f"![{caption or 'Chart'}]({rel_path})",
            }
        
        if metadata:
            result["metadata"] = metadata
        
        return result
    
    def _generate_caption(self, data: Any, chart_type: ChartType, 
                         options: ChartOptions) -> str:
        """
        Generate a descriptive caption for a chart.
        
        Args:
            data: Data being visualized
            chart_type: Type of chart
            options: Visualization options
            
        Returns:
            A descriptive caption
        """
        # Start with title if available
        parts = []
        if options.title:
            parts.append(options.title)
        
        # Add description based on chart type and purpose
        chart_desc = self._get_chart_type_description(chart_type)
        if chart_desc:
            parts.append(chart_desc)
        
        # Add purpose if specified
        if options.purpose:
            purpose_desc = self._get_purpose_description(options.purpose)
            if purpose_desc:
                parts.append(purpose_desc)
        
        # Add data summary if available
        data_desc = self._get_data_description(data, chart_type)
        if data_desc:
            parts.append(data_desc)
        
        # Combine parts into caption
        if parts:
            caption = ". ".join(parts)
            # Ensure it ends with a period
            if not caption.endswith('.'):
                caption += '.'
            return caption
        else:
            # Default caption
            return f"Visualization of data using a {chart_type.name.lower().replace('_', ' ')} chart."
    
    def _get_chart_type_description(self, chart_type: ChartType) -> Optional[str]:
        """Get a description for a chart type."""
        descriptions = {
            ChartType.BAR: "Bar chart showing categorical comparison",
            ChartType.LINE: "Line chart showing trends over time or sequences",
            ChartType.SCATTER: "Scatter plot showing relationship between variables",
            ChartType.PIE: "Pie chart showing composition or proportion of categories",
            ChartType.AREA: "Area chart showing cumulative values over time",
            ChartType.HISTOGRAM: "Histogram showing distribution of values",
            ChartType.BOX: "Box plot showing statistical distribution of values",
            ChartType.HEATMAP: "Heatmap showing intensity of values across two dimensions",
            ChartType.BUBBLE: "Bubble chart showing relationship between three variables",
            ChartType.RADAR: "Radar chart showing multivariate data as a 2D shape",
            ChartType.VIOLIN: "Violin plot showing distribution density",
            ChartType.DONUT: "Donut chart showing composition with emphasis on total",
            ChartType.TREEMAP: "Treemap showing hierarchical data as nested rectangles",
            ChartType.SANKEY: "Sankey diagram showing flow between nodes",
            ChartType.CHORD: "Chord diagram showing inter-relationships between entities",
            ChartType.GAUGE: "Gauge chart showing value within a range",
            ChartType.CANDLESTICK: "Candlestick chart showing stock price movements",
            ChartType.FUNNEL: "Funnel chart showing sequential stages of a process",
            ChartType.WATERFALL: "Waterfall chart showing cumulative effect of changes",
        }
        return descriptions.get(chart_type)
    
    def _get_purpose_description(self, purpose: ChartPurpose) -> Optional[str]:
        """Get a description for a chart purpose."""
        descriptions = {
            ChartPurpose.COMPARISON: "This visualization enables comparison between different categories",
            ChartPurpose.TREND: "This visualization shows trends or changes over time",
            ChartPurpose.DISTRIBUTION: "This visualization shows how values are distributed",
            ChartPurpose.COMPOSITION: "This visualization shows how parts contribute to a whole",
            ChartPurpose.RELATIONSHIP: "This visualization shows correlations or relationships between variables",
            ChartPurpose.HIERARCHY: "This visualization shows hierarchical structure in the data",
            ChartPurpose.GEOSPATIAL: "This visualization shows geographic or spatial patterns",
            ChartPurpose.PART_TO_WHOLE: "This visualization shows how individual parts relate to the total",
            ChartPurpose.FLOW: "This visualization shows movement or transitions between states",
            ChartPurpose.RANKING: "This visualization highlights the relative position of items",
        }
        return descriptions.get(purpose)
    
    def _get_data_description(self, data: Any, chart_type: ChartType) -> Optional[str]:
        """Get a description of the data being visualized."""
        # This is a simplistic implementation; a real implementation would analyze the data more thoroughly
        try:
            if isinstance(data, dict):
                if 'x' in data and 'y' in data:
                    x_len = len(data['x'])
                    if x_len > 0:
                        return f"Based on {x_len} data points"
                elif 'series' in data:
                    series_count = len(data['series'])
                    if series_count > 0:
                        return f"Comparing {series_count} data series"
            return None
        except:
            return None
    
    def _generate_metadata(self, data: Any, chart_type: ChartType, 
                          options: ChartOptions) -> Dict[str, Any]:
        """
        Generate metadata for a chart.
        
        Args:
            data: Data being visualized
            chart_type: Type of chart
            options: Visualization options
            
        Returns:
            A dictionary of metadata
        """
        # Basic metadata
        metadata = {
            "chart_type": chart_type.name,
            "created_at": datetime.now().isoformat(),
            "renderer": options.renderer or default_config.default_renderer,
            "theme": options.theme or default_config.default_theme,
        }
        
        # Add title and other options if available
        if options.title:
            metadata["title"] = options.title
        if options.subtitle:
            metadata["subtitle"] = options.subtitle
        if options.purpose:
            metadata["purpose"] = options.purpose.name
        
        # Add data statistics if possible
        try:
            data_stats = self._get_data_statistics(data, chart_type)
            if data_stats:
                metadata["data_statistics"] = data_stats
        except:
            pass
        
        return metadata
    
    def _get_data_statistics(self, data: Any, chart_type: ChartType) -> Optional[Dict[str, Any]]:
        """Get statistical information about the data."""
        # This is a simplistic implementation; a real implementation would calculate more statistics
        try:
            stats = {}
            if isinstance(data, dict):
                if 'x' in data and 'y' in data:
                    stats["data_points"] = len(data['x'])
                    if all(isinstance(y, (int, float)) for y in data['y']):
                        y_values = data['y']
                        stats["min"] = min(y_values)
                        stats["max"] = max(y_values)
                        stats["mean"] = sum(y_values) / len(y_values)
                elif 'series' in data:
                    stats["series_count"] = len(data['series'])
            return stats
        except:
            return None
    
    def generate_report_section(self, chart_data: Dict[str, Any],
                              section_title: Optional[str] = None,
                              include_caption: bool = True,
                              include_title: bool = True,
                              section_text: Optional[str] = None,
                              section_level: int = 2) -> str:
        """
        Generate a complete report section with a chart.
        
        Args:
            chart_data: Chart data from create_chart_for_report
            section_title: Title for the section (defaults to chart title or 'Chart Section')
            include_caption: Whether to include the caption below the chart
            include_title: Whether to include the chart title in the image
            section_text: Optional text to include in the section before the chart
            section_level: Heading level for the section title (2 = h2, 3 = h3, etc.)
            
        Returns:
            str: Markdown text for a complete report section
        """
        # Start with section title
        title = section_title
        if not title and chart_data.get("metadata", {}).get("title"):
            title = chart_data["metadata"]["title"]
        if not title:
            title = "Chart Section"
        
        # Create markdown
        md_parts = []
        
        # Add section heading
        md_parts.append(f"{'#' * section_level} {title}\n")
        
        # Add section text if provided
        if section_text:
            md_parts.append(f"{section_text}\n")
        
        # Add chart
        if chart_data.get("type") == "embedded" or chart_data.get("type") == "file":
            # Already have markdown for this
            md_parts.append(chart_data["markdown"])
        else:
            # Need to create markdown for this (likely from PDF or HTML output)
            if "data_url" in chart_data:
                md_parts.append(f"![{chart_data.get('caption', 'Chart')}]({chart_data['data_url']})")
            elif "path" in chart_data:
                md_parts.append(f"![{chart_data.get('caption', 'Chart')}]({chart_data['path']})")
        
        # Add caption if requested
        if include_caption and chart_data.get("caption") and "markdown" not in chart_data:
            md_parts.append(f"*{chart_data['caption']}*\n")
        
        return "\n\n".join(md_parts)
    
    def save_chart_to_file(self, chart_data: Dict[str, Any], 
                          output_dir: str = "output/charts") -> str:
        """
        Save a chart to a file from chart data returned by create_chart_for_report.
        
        Args:
            chart_data: Chart data from create_chart_for_report
            output_dir: Directory to save the chart in
            
        Returns:
            str: Path to the saved file
            
        Raises:
            ReportIntegrationError: If the chart cannot be saved
        """
        try:
            # Make sure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename
            chart_id = chart_data.get("id", f"chart_{int(time.time() * 1000)}")
            format = chart_data.get("format", "png")
            filename = f"{chart_id}.{format}"
            full_path = os.path.join(output_dir, filename)
            
            # Save the chart
            if "image_data" in chart_data:
                # We have raw image data
                with open(full_path, 'wb') as f:
                    f.write(chart_data["image_data"])
                return full_path
            elif "data_url" in chart_data:
                # We have a data URL
                data_url = chart_data["data_url"]
                if data_url.startswith("data:"):
                    # Extract the data from the URL
                    header, encoded = data_url.split(",", 1)
                    image_data = base64.b64decode(encoded)
                    with open(full_path, 'wb') as f:
                        f.write(image_data)
                    return full_path
            elif "path" in chart_data:
                # Chart is already saved to a file
                return chart_data["path"]
            
            raise ReportIntegrationError(
                "Chart data doesn't contain image data, data URL, or path",
                chart_id=chart_id
            )
                
        except Exception as e:
            raise ReportIntegrationError(
                f"Failed to save chart to file: {str(e)}",
                chart_id=chart_data.get("id")
            ) 