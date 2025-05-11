"""
Theme Manager

This module provides a dedicated manager for visualization themes, allowing for
easy theme creation, customization, and application.
"""

import os
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import asdict

from .types import ThemeType, ChartTheme
from .config import default_config
from .exceptions import ThemeError


class ThemeManager:
    """
    Manager for visualization themes.
    
    This class provides a unified interface for:
    - Getting and setting themes
    - Creating custom themes
    - Importing and exporting themes
    - Applying themes to charts
    """
    
    def __init__(self, config=None):
        """
        Initialize the theme manager.
        
        Args:
            config: Optional configuration to use instead of the default
        """
        self.config = config or default_config
    
    def get_theme(self, name: Optional[str] = None) -> ChartTheme:
        """
        Get a theme by name, or the default theme if name is None.
        
        Args:
            name: Name of the theme to get, or None for the default
            
        Returns:
            The ChartTheme instance
            
        Raises:
            ThemeError: If the theme does not exist
        """
        try:
            return self.config.get_theme(name)
        except ValueError as e:
            raise ThemeError(str(e), theme_name=name)
    
    def list_themes(self) -> List[str]:
        """
        Get a list of all available theme names.
        
        Returns:
            List of theme names
        """
        return self.config.list_themes()
    
    def get_theme_info(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed information about a theme.
        
        Args:
            name: Name of the theme to get info for, or None for the default
            
        Returns:
            Dictionary with theme properties
            
        Raises:
            ThemeError: If the theme does not exist
        """
        try:
            return self.config.get_theme_info(name)
        except ValueError as e:
            raise ThemeError(str(e), theme_name=name)
    
    def register_theme(self, theme: ChartTheme) -> None:
        """
        Register a new theme or update an existing one.
        
        Args:
            theme: The ChartTheme instance to register
        """
        self.config.register_theme(theme)
    
    def create_theme(self, name: str, colors: List[str], background_color: str,
                    text_color: str, font_family: str, **kwargs) -> ChartTheme:
        """
        Create and register a new theme with specified properties.
        
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
            ThemeError: If a theme with the given name already exists
        """
        try:
            return self.config.create_theme(
                name=name,
                colors=colors,
                background_color=background_color,
                text_color=text_color,
                font_family=font_family,
                **kwargs
            )
        except ValueError as e:
            raise ThemeError(str(e), theme_name=name)
    
    def export_theme(self, name: str, path: str) -> None:
        """
        Export a theme to a JSON file.
        
        Args:
            name: Name of the theme to export
            path: File path to export to
            
        Raises:
            ThemeError: If the theme does not exist or cannot be exported
        """
        try:
            self.config.export_theme(name, path)
        except (ValueError, IOError) as e:
            raise ThemeError(f"Failed to export theme: {str(e)}", theme_name=name)
    
    def import_theme(self, path: str) -> str:
        """
        Import a theme from a JSON file.
        
        Args:
            path: Path to the theme JSON file
            
        Returns:
            Name of the imported theme
            
        Raises:
            ThemeError: If the theme cannot be imported
        """
        try:
            return self.config.import_theme(path)
        except (ValueError, IOError, json.JSONDecodeError) as e:
            raise ThemeError(f"Failed to import theme: {str(e)}")
    
    def set_default_theme(self, name: str) -> None:
        """
        Set the default theme.
        
        Args:
            name: Name of the theme to set as default
            
        Raises:
            ThemeError: If the theme does not exist
        """
        if name not in self.list_themes():
            raise ThemeError(f"Theme '{name}' not found", theme_name=name)
        
        self.config.default_theme = name
    
    def create_color_palette(self, name: str, colors: List[str], 
                           is_sequential: bool = False,
                           is_diverging: bool = False,
                           is_qualitative: bool = True) -> Dict[str, Any]:
        """
        Create a color palette for use in themes.
        
        Args:
            name: Name for the palette
            colors: List of color values
            is_sequential: Whether the palette represents sequential data
            is_diverging: Whether the palette represents diverging data
            is_qualitative: Whether the palette represents qualitative data
            
        Returns:
            Dictionary describing the color palette
        """
        return {
            'name': name,
            'colors': colors,
            'is_sequential': is_sequential,
            'is_diverging': is_diverging,
            'is_qualitative': is_qualitative
        }
    
    def modify_theme(self, name: str, **kwargs) -> ChartTheme:
        """
        Modify an existing theme with new properties.
        
        Args:
            name: Name of the theme to modify
            **kwargs: New property values to set
            
        Returns:
            The modified ChartTheme instance
            
        Raises:
            ThemeError: If the theme does not exist
        """
        try:
            # Get the existing theme
            theme = self.get_theme(name)
            
            # Create a new theme dict
            theme_dict = asdict(theme)
            
            # Update with new values
            for key, value in kwargs.items():
                if hasattr(theme, key):
                    theme_dict[key] = value
                elif key == 'custom_properties' and isinstance(value, dict):
                    # Merge custom properties
                    theme_dict['custom_properties'].update(value)
                else:
                    # Add to custom properties
                    theme_dict['custom_properties'][key] = value
            
            # Convert type string to enum if needed
            if 'type' in kwargs and isinstance(kwargs['type'], str):
                try:
                    theme_dict['type'] = ThemeType(kwargs['type'])
                except ValueError:
                    theme_dict['type'] = ThemeType.CUSTOM
            
            # Create a new theme with updated properties
            new_theme = ChartTheme(**theme_dict)
            
            # Register the updated theme
            self.register_theme(new_theme)
            
            return new_theme
            
        except (ValueError, AttributeError) as e:
            raise ThemeError(f"Failed to modify theme: {str(e)}", theme_name=name)
    
    def derive_theme(self, base_theme_name: str, new_name: str, **kwargs) -> ChartTheme:
        """
        Create a new theme by deriving from an existing one.
        
        Args:
            base_theme_name: Name of the theme to derive from
            new_name: Name for the new theme
            **kwargs: Properties to override in the new theme
            
        Returns:
            The new ChartTheme instance
            
        Raises:
            ThemeError: If the base theme does not exist or the new name is taken
        """
        try:
            # Check if the new name is already taken
            if new_name in self.list_themes():
                raise ValueError(f"Theme '{new_name}' already exists")
            
            # Get the base theme
            base_theme = self.get_theme(base_theme_name)
            
            # Create a new theme dict from the base
            theme_dict = asdict(base_theme)
            
            # Change the name
            theme_dict['name'] = new_name
            
            # Set type to CUSTOM for derived themes
            theme_dict['type'] = ThemeType.CUSTOM
            
            # Update with new values
            for key, value in kwargs.items():
                if key in theme_dict and key != 'name':
                    theme_dict[key] = value
                elif key == 'custom_properties' and isinstance(value, dict):
                    # Merge custom properties
                    theme_dict['custom_properties'].update(value)
                else:
                    # Add to custom properties
                    theme_dict['custom_properties'][key] = value
            
            # Create a new theme with derived properties
            new_theme = ChartTheme(**theme_dict)
            
            # Register the new theme
            self.register_theme(new_theme)
            
            return new_theme
            
        except ValueError as e:
            raise ThemeError(f"Failed to derive theme: {str(e)}", 
                           theme_name=base_theme_name)


# Create a default theme manager instance
default_theme_manager = ThemeManager() 