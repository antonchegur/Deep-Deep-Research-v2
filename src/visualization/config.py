"""
Visualization Configuration

This module provides configuration options for the visualization system.
"""

import os
import json
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field, asdict

from .types import ThemeType, ChartTheme


@dataclass
class VisualizationConfig:
    """Configuration for the visualization system."""
    
    # Default renderer (matplotlib, plotly)
    default_renderer: str = "matplotlib"
    
    # Default theme name
    default_theme: str = "light"
    
    # Default output format
    default_format: str = "png"
    
    # Default DPI for rasterized formats
    default_dpi: int = 300
    
    # Default dimensions for charts
    default_width: int = 800
    default_height: int = 600
    
    # Default font settings
    default_font_family: str = "Arial, Helvetica, sans-serif"
    default_font_size: int = 12
    
    # Default color schemes
    default_color_scheme: str = "default"
    
    # Flag for enabling interactive features (when supported)
    enable_interactive: bool = True
    
    # Output directory for saved charts
    output_directory: str = "./output/charts"
    
    # Custom renderer options
    renderer_options: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "matplotlib": {
            "backend": "Agg",  # Default to non-interactive backend
            "style": "default",
            "figure.figsize": (10, 6),
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        },
        "plotly": {
            "renderer": "png",
            "include_plotlyjs": True,
            "include_mathjax": False,
            "full_html": True,
        }
    })
    
    # Predefined themes
    themes: Dict[str, ChartTheme] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default themes if not provided."""
        if not self.themes:
            self._initialize_default_themes()
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_directory, exist_ok=True)
    
    def _initialize_default_themes(self):
        """Initialize default themes."""
        # Light theme
        self.themes["light"] = ChartTheme(
            name="light",
            type=ThemeType.LIGHT,
            colors=["#4C78A8", "#F58518", "#E45756", "#72B7B2", "#54A24B", 
                   "#EECA3B", "#B279A2", "#FF9DA6", "#9D755D", "#BAB0AC"],
            background_color="#FFFFFF",
            text_color="#333333",
            font_family=self.default_font_family,
            grid_color="#E0E0E0",
            axis_color="#000000",
            line_width=1.5,
            marker_size=6
        )
        
        # Dark theme
        self.themes["dark"] = ChartTheme(
            name="dark",
            type=ThemeType.DARK,
            colors=["#4C78A8", "#F58518", "#E45756", "#72B7B2", "#54A24B", 
                   "#EECA3B", "#B279A2", "#FF9DA6", "#9D755D", "#BAB0AC"],
            background_color="#333333",
            text_color="#FFFFFF",
            font_family=self.default_font_family,
            grid_color="#555555",
            axis_color="#FFFFFF",
            line_width=1.5,
            marker_size=6
        )
        
        # Print-friendly theme (good for reports, uses colorblind-friendly palette)
        self.themes["print"] = ChartTheme(
            name="print",
            type=ThemeType.PRINT,
            colors=["#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", 
                   "#0072B2", "#D55E00", "#CC79A7"],
            background_color="#FFFFFF",
            text_color="#000000",
            font_family="Times New Roman, serif",
            grid_color="#CCCCCC",
            axis_color="#000000",
            line_width=1.0,
            marker_size=5
        )
        
        # Corporate theme
        self.themes["corporate"] = ChartTheme(
            name="corporate",
            type=ThemeType.CUSTOM,
            colors=["#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD", 
                   "#8C564B", "#E377C2", "#7F7F7F", "#BCBD22", "#17BECF"],
            background_color="#FFFFFF",
            text_color="#333333",
            font_family="Georgia, serif",
            grid_color="#E5E5E5",
            axis_color="#666666",
            line_width=2.0,
            marker_size=7
        )
        
        # Minimalist theme (clean, simple look)
        self.themes["minimalist"] = ChartTheme(
            name="minimalist",
            type=ThemeType.CUSTOM,
            colors=["#2E5098", "#FF8C00", "#1D6F42", "#C41E3A", "#6B5B95", 
                   "#FF9F80", "#88B04B", "#394359", "#DCDCDC", "#0085CA"],
            background_color="#FFFFFF",
            text_color="#333333",
            font_family="Helvetica, Arial, sans-serif",
            grid_color="#F0F0F0",
            axis_color="#999999",
            line_width=1.5,
            marker_size=6,
            custom_properties={"axis_line_width": 0.5, "use_spines": False}
        )
        
        # Scientific publication theme
        self.themes["scientific"] = ChartTheme(
            name="scientific",
            type=ThemeType.CUSTOM,
            colors=["#3182bd", "#6baed6", "#9ecae1", "#c6dbef", "#e6550d", 
                   "#fd8d3c", "#fdae6b", "#fdd0a2", "#31a354", "#74c476"],
            background_color="#FFFFFF",
            text_color="#000000",
            font_family="Arial, Helvetica, sans-serif",
            grid_color="#E0E0E0",
            axis_color="#000000",
            line_width=1.25,
            marker_size=5,
            custom_properties={"figure_ratio": "golden", "label_fontsize": 10}
        )
    
    def get_theme(self, name: Optional[str] = None) -> ChartTheme:
        """Get a theme by name, or the default theme if name is None."""
        theme_name = name or self.default_theme
        
        if theme_name not in self.themes:
            raise ValueError(f"Theme '{theme_name}' not found")
        
        return self.themes[theme_name]
    
    def register_theme(self, theme: ChartTheme) -> None:
        """Register a new theme or update an existing one."""
        self.themes[theme.name] = theme
    
    def list_themes(self) -> List[str]:
        """Get a list of all available theme names."""
        return list(self.themes.keys())
    
    def get_theme_info(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed information about a theme."""
        theme = self.get_theme(name)
        theme_dict = asdict(theme)
        # Convert enum to string for easier serialization
        if 'type' in theme_dict and hasattr(theme_dict['type'], 'value'):
            theme_dict['type'] = theme_dict['type'].value
        return theme_dict
    
    def export_theme(self, name: str, path: str) -> None:
        """Export a theme to a JSON file."""
        theme = self.get_theme(name)
        theme_dict = asdict(theme)
        # Convert enum to string for easier serialization
        if 'type' in theme_dict and hasattr(theme_dict['type'], 'value'):
            theme_dict['type'] = theme_dict['type'].value
            
        with open(path, 'w') as f:
            json.dump(theme_dict, f, indent=2)
    
    def import_theme(self, path: str) -> str:
        """Import a theme from a JSON file."""
        with open(path, 'r') as f:
            theme_dict = json.load(f)
        
        # Ensure required fields are present
        required_fields = ['name', 'colors', 'background_color', 'text_color', 'font_family']
        for field in required_fields:
            if field not in theme_dict:
                raise ValueError(f"Missing required field '{field}' in theme file")
        
        # Convert type string to enum if present
        if 'type' in theme_dict and isinstance(theme_dict['type'], str):
            try:
                theme_dict['type'] = ThemeType(theme_dict['type'])
            except ValueError:
                # Default to custom if not a valid enum value
                theme_dict['type'] = ThemeType.CUSTOM
        
        # Create the theme object
        theme = ChartTheme(**theme_dict)
        
        # Register the theme
        self.register_theme(theme)
        
        return theme.name
    
    def create_theme(self, name: str, colors: List[str], background_color: str, 
                    text_color: str, font_family: str, **kwargs) -> ChartTheme:
        """Create and register a new theme with specified properties."""
        # Check if the theme already exists
        if name in self.themes:
            raise ValueError(f"Theme '{name}' already exists. Use register_theme to update it.")
        
        # Create the theme
        theme = ChartTheme(
            name=name,
            type=ThemeType.CUSTOM,
            colors=colors,
            background_color=background_color,
            text_color=text_color,
            font_family=font_family,
            grid_color=kwargs.get('grid_color', '#E0E0E0'),
            axis_color=kwargs.get('axis_color', text_color),
            line_width=kwargs.get('line_width', 1.5),
            marker_size=kwargs.get('marker_size', 6),
            custom_properties={k: v for k, v in kwargs.items() 
                             if k not in ['grid_color', 'axis_color', 'line_width', 'marker_size']}
        )
        
        # Register the theme
        self.register_theme(theme)
        
        return theme
    
    def get_renderer_options(self, renderer: Optional[str] = None) -> Dict[str, Any]:
        """Get options for a specific renderer."""
        renderer_name = renderer or self.default_renderer
        
        if renderer_name not in self.renderer_options:
            return {}
        
        return self.renderer_options[renderer_name]
    
    def update_renderer_options(self, renderer: str, options: Dict[str, Any]) -> None:
        """Update options for a specific renderer."""
        if renderer not in self.renderer_options:
            self.renderer_options[renderer] = {}
        
        self.renderer_options[renderer].update(options)


# Create a default configuration instance
default_config = VisualizationConfig() 