"""
Data Visualization Types

This module defines the type system for the visualization module, including enums,
data classes, and interfaces.
"""

from enum import Enum, auto
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field


class ChartType(Enum):
    """Enum representing supported chart types."""
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"
    HISTOGRAM = "histogram"
    BOX = "box"
    VIOLIN = "violin"
    HEATMAP = "heatmap"
    BUBBLE = "bubble"
    RADAR = "radar"
    COMBINED = "combined"  # For combining multiple chart types


class AxisType(Enum):
    """Enum representing axis scale types."""
    LINEAR = "linear"
    LOG = "log"
    DATE = "date"
    CATEGORY = "category"
    

class ChartPurpose(Enum):
    """Enum representing the purpose of a chart."""
    COMPARISON = "comparison"  # Compare values across categories
    TREND = "trend"  # Show change over time
    DISTRIBUTION = "distribution"  # Show distribution of values
    COMPOSITION = "composition"  # Show parts of a whole
    RELATIONSHIP = "relationship"  # Show correlation between variables
    GEOGRAPHIC = "geographic"  # Show data on maps


class ThemeType(Enum):
    """Enum representing theme types."""
    LIGHT = "light"
    DARK = "dark"
    PRINT = "print"
    CUSTOM = "custom"


@dataclass
class ChartOptions:
    """Class for storing chart rendering options."""
    title: Optional[str] = None
    subtitle: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    x_axis_type: AxisType = AxisType.LINEAR
    y_axis_type: AxisType = AxisType.LINEAR
    width: int = 800
    height: int = 600
    legend: bool = True
    legend_position: str = "best"
    grid: bool = True
    theme: str = "light"
    colors: Optional[List[str]] = None
    font_family: Optional[str] = None
    font_size: Optional[int] = None
    animation: bool = False
    interactive: bool = False
    stacked: bool = False
    orientation: str = "vertical"  # or "horizontal"
    opacity: float = 1.0
    custom_options: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert options to a dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class ChartTheme:
    """Class representing a chart theme."""
    name: str
    colors: List[str]
    background_color: str
    text_color: str
    font_family: str
    grid_color: str
    axis_color: str
    line_width: float = 1.5
    marker_size: int = 6
    type: ThemeType = ThemeType.CUSTOM
    custom_properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert theme to a dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class DataPoint:
    """Class representing a single data point."""
    x: Any
    y: Any
    label: Optional[str] = None
    group: Optional[str] = None
    size: Optional[float] = None
    color: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert data point to a dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class ChartData:
    """Class representing structured chart data."""
    data_points: List[DataPoint] = field(default_factory=list)
    series: Dict[str, List[DataPoint]] = field(default_factory=dict)
    x_field: Optional[str] = None
    y_field: Optional[str] = None
    label_field: Optional[str] = None
    group_field: Optional[str] = None
    size_field: Optional[str] = None
    color_field: Optional[str] = None
    
    def add_point(self, x: Any, y: Any, label: Optional[str] = None, group: Optional[str] = None, 
                 size: Optional[float] = None, color: Optional[str] = None):
        """Add a data point to the chart data."""
        point = DataPoint(x=x, y=y, label=label, group=group, size=size, color=color)
        self.data_points.append(point)
        
        # If this point belongs to a series (group), add it there too
        if group:
            if group not in self.series:
                self.series[group] = []
            self.series[group].append(point)
    
    def add_series(self, name: str, points: List[DataPoint]):
        """Add a series of data points."""
        self.series[name] = points
        self.data_points.extend(points)


# Type aliases for better code readability
DataFrameType = Any  # Typically a pandas DataFrame
ChartResult = Any  # Return type from renderers (could be matplotlib Figure, plotly Figure, etc.)
ImageData = bytes  # For PNG, JPEG, etc. binary image data 