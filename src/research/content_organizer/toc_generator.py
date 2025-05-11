"""
Table of Contents Generator Module

This module provides tools for generating structured tables of contents from research content.
"""

from typing import Dict, List, Optional, Any, Union
import logging

from .structure import ContentStructure, HeadingLevel

logger = logging.getLogger(__name__)


class TableOfContentsGenerator:
    """
    Generates structured tables of contents from research content.
    
    Supports different formats including markdown, HTML, and structured data.
    """
    
    def __init__(self, include_page_numbers: bool = True, max_depth: int = 3):
        """
        Initialize a table of contents generator.
        
        Args:
            include_page_numbers: Whether to include page numbers in the TOC
            max_depth: Maximum depth of headings to include in the TOC
        """
        self.include_page_numbers = include_page_numbers
        self.max_depth = max_depth
    
    def generate_toc(self, content_structure: ContentStructure,
                   format_type: str = 'markdown') -> str:
        """
        Generate a table of contents from a content structure.
        
        Args:
            content_structure: Structure to generate TOC from
            format_type: Output format ('markdown', 'html', or 'text')
            
        Returns:
            Formatted table of contents
        """
        if format_type == 'markdown':
            return self._generate_markdown_toc(content_structure)
        elif format_type == 'html':
            return self._generate_html_toc(content_structure)
        elif format_type == 'text':
            return self._generate_text_toc(content_structure)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def generate_toc_data(self, content_structure: ContentStructure) -> List[Dict[str, Any]]:
        """
        Generate a structured data representation of the table of contents.
        
        Args:
            content_structure: Structure to generate TOC from
            
        Returns:
            List of TOC entries as dictionaries
        """
        return content_structure.generate_table_of_contents()
    
    def _generate_markdown_toc(self, structure: ContentStructure) -> str:
        """Generate a markdown-formatted table of contents."""
        toc_lines = ["# Table of Contents\n"]
        
        # Add executive summary if it exists
        if structure.executive_summary:
            toc_lines.append("- [Executive Summary](#executive-summary)")
        
        # Add sections
        for i, section in enumerate(structure.sections):
            # Skip sections with level higher than max_depth
            if section.level.value > self.max_depth:
                continue
                
            # Create an anchor from the section title
            anchor = self._create_anchor(section.title)
            
            # Add section entry
            indent = "  " * (section.level.value - 1)
            toc_lines.append(f"{indent}- [{section.title}](#{anchor})")
            
            # Add subsections
            for subsection in section.subsections:
                # Skip subsections with level higher than max_depth
                if subsection.level.value > self.max_depth:
                    continue
                    
                sub_anchor = self._create_anchor(subsection.title)
                sub_indent = "  " * (subsection.level.value - 1)
                toc_lines.append(f"{sub_indent}- [{subsection.title}](#{sub_anchor})")
        
        return "\n".join(toc_lines)
    
    def _generate_html_toc(self, structure: ContentStructure) -> str:
        """Generate an HTML-formatted table of contents."""
        toc_lines = ["<div class='table-of-contents'>", "<h2>Table of Contents</h2>", "<ul>"]
        
        # Add executive summary if it exists
        if structure.executive_summary:
            toc_lines.append("  <li><a href='#executive-summary'>Executive Summary</a></li>")
        
        # Track the current nesting level
        current_level = 1
        
        for i, section in enumerate(structure.sections):
            # Skip sections with level higher than max_depth
            if section.level.value > self.max_depth:
                continue
                
            # Create an anchor from the section title
            anchor = self._create_anchor(section.title)
            
            # Handle nesting
            if section.level.value > current_level:
                # Open a new nested list for each level increase
                for _ in range(section.level.value - current_level):
                    toc_lines.append("<ul>")
            elif section.level.value < current_level:
                # Close the nested lists when level decreases
                for _ in range(current_level - section.level.value):
                    toc_lines.append("</ul>")
            
            # Update the current level
            current_level = section.level.value
            
            # Add section entry
            toc_lines.append(f"  <li><a href='#{anchor}'>{section.title}</a>")
            
            # Handle subsections
            if section.subsections:
                toc_lines.append("  <ul>")
                
                for subsection in section.subsections:
                    # Skip subsections with level higher than max_depth
                    if subsection.level.value > self.max_depth:
                        continue
                        
                    sub_anchor = self._create_anchor(subsection.title)
                    toc_lines.append(f"    <li><a href='#{sub_anchor}'>{subsection.title}</a></li>")
                
                toc_lines.append("  </ul>")
            
            # Close the list item
            toc_lines.append("  </li>")
        
        # Close any remaining nested lists
        for _ in range(current_level):
            toc_lines.append("</ul>")
        
        toc_lines.append("</div>")
        
        return "\n".join(toc_lines)
    
    def _generate_text_toc(self, structure: ContentStructure) -> str:
        """Generate a plain text table of contents."""
        toc_lines = ["TABLE OF CONTENTS\n"]
        
        # Add executive summary if it exists
        if structure.executive_summary:
            toc_lines.append("Executive Summary")
        
        # Add sections
        for i, section in enumerate(structure.sections):
            # Skip sections with level higher than max_depth
            if section.level.value > self.max_depth:
                continue
                
            # Add section entry
            indent = "  " * (section.level.value - 1)
            toc_lines.append(f"{indent}{section.title}")
            
            # Add subsections
            for subsection in section.subsections:
                # Skip subsections with level higher than max_depth
                if subsection.level.value > self.max_depth:
                    continue
                    
                sub_indent = "  " * (subsection.level.value - 1)
                toc_lines.append(f"{sub_indent}{subsection.title}")
        
        return "\n".join(toc_lines)
    
    def _create_anchor(self, title: str) -> str:
        """
        Create an HTML anchor from a title.
        
        Args:
            title: Section title
            
        Returns:
            Anchor string for the title
        """
        # Convert to lowercase
        anchor = title.lower()
        
        # Replace non-alphanumeric characters with hyphens
        anchor = ''.join(c if c.isalnum() else '-' for c in anchor)
        
        # Remove consecutive hyphens
        while '--' in anchor:
            anchor = anchor.replace('--', '-')
        
        # Remove leading and trailing hyphens
        return anchor.strip('-') 