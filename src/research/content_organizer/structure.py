"""
Content Structure Module

This module provides classes for representing structured research content.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import re


class HeadingLevel(Enum):
    """Enumeration of heading levels."""
    TITLE = 0
    HEADING_1 = 1
    HEADING_2 = 2
    HEADING_3 = 3
    HEADING_4 = 4
    HEADING_5 = 5


@dataclass
class Subsection:
    """Represents a subsection in the content structure."""
    id: str
    title: str 
    content: str
    level: HeadingLevel = HeadingLevel.HEADING_3
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "level": self.level.value,
            "metadata": self.metadata
        }


@dataclass
class Section:
    """Represents a section in the content structure."""
    id: str
    title: str
    content: str
    level: HeadingLevel = HeadingLevel.HEADING_2
    subsections: List[Subsection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_subsection(self, subsection: Subsection) -> None:
        """Add a subsection to the section."""
        self.subsections.append(subsection)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "level": self.level.value,
            "subsections": [s.to_dict() for s in self.subsections],
            "metadata": self.metadata
        }


class ContentStructure:
    """
    Represents the structure of research content.
    
    Includes a title, executive summary, sections, and subsections.
    """
    
    def __init__(self, title: str, executive_summary: Optional[str] = None):
        """
        Initialize a content structure.
        
        Args:
            title: Title of the content
            executive_summary: Executive summary (optional)
        """
        self.title = title
        self.executive_summary = executive_summary
        self.sections: List[Section] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_section(self, section: Section) -> None:
        """Add a section to the structure."""
        self.sections.append(section)
    
    def get_section_by_id(self, section_id: str) -> Optional[Section]:
        """Get a section by its ID."""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None
    
    def get_section_by_title(self, title: str) -> Optional[Section]:
        """Get a section by its title."""
        for section in self.sections:
            if section.title.lower() == title.lower():
                return section
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "title": self.title,
            "executive_summary": self.executive_summary,
            "sections": [s.to_dict() for s in self.sections],
            "metadata": self.metadata
        }
    
    def generate_table_of_contents(self) -> List[Dict[str, Any]]:
        """Generate a table of contents from the structure."""
        toc = []
        
        for i, section in enumerate(self.sections):
            section_entry = {
                "id": section.id,
                "title": section.title,
                "level": section.level.value,
                "subsections": []
            }
            
            for j, subsection in enumerate(section.subsections):
                subsection_entry = {
                    "id": subsection.id,
                    "title": subsection.title,
                    "level": subsection.level.value
                }
                section_entry["subsections"].append(subsection_entry)
            
            toc.append(section_entry)
        
        return toc
    
    @staticmethod
    def from_plain_text(title: str, content: str) -> 'ContentStructure':
        """
        Create a content structure from plain text by identifying headings.
        
        Args:
            title: Title of the content
            content: Plain text content with markdown-style headings
            
        Returns:
            ContentStructure object
        """
        # Create new content structure
        structure = ContentStructure(title)
        
        # Split content by heading markers
        lines = content.split('\n')
        current_section = None
        current_subsection = None
        section_content = []
        section_id_counter = 1
        subsection_id_counter = 1
        
        for line in lines:
            # Check for heading patterns
            h1_match = re.match(r'^# (.+)$', line)
            h2_match = re.match(r'^## (.+)$', line)
            h3_match = re.match(r'^### (.+)$', line)
            
            if h1_match:  # This could be a title or executive summary
                if current_section:
                    current_section.content = '\n'.join(section_content).strip()
                    structure.add_section(current_section)
                    section_content = []
                
                section_title = h1_match.group(1).strip()
                current_section = Section(
                    id=f"section-{section_id_counter}",
                    title=section_title,
                    content="",
                    level=HeadingLevel.HEADING_1
                )
                section_id_counter += 1
                current_subsection = None
            
            elif h2_match and current_section:  # This is a subsection
                if current_subsection:
                    current_subsection.content = '\n'.join(section_content).strip()
                    current_section.add_subsection(current_subsection)
                    section_content = []
                
                subsection_title = h2_match.group(1).strip()
                current_subsection = Subsection(
                    id=f"{current_section.id}-{subsection_id_counter}",
                    title=subsection_title,
                    content="",
                    level=HeadingLevel.HEADING_2
                )
                subsection_id_counter += 1
            
            elif h3_match and current_section:  # This is a sub-subsection (we'll treat as content)
                if current_subsection:
                    section_content.append(line)
                else:
                    section_content.append(line)
            
            else:  # Regular content
                section_content.append(line)
        
        # Add the last section/subsection if there is one
        if current_subsection:
            current_subsection.content = '\n'.join(section_content).strip()
            current_section.add_subsection(current_subsection)
        
        if current_section:
            if not current_subsection:
                current_section.content = '\n'.join(section_content).strip()
            structure.add_section(current_section)
        
        return structure
    
    def to_markdown(self) -> str:
        """
        Convert the content structure to markdown text.
        
        Returns:
            Markdown representation of the content
        """
        markdown = [f"# {self.title}\n"]
        
        if self.executive_summary:
            markdown.append("## Executive Summary\n")
            markdown.append(f"{self.executive_summary}\n\n")
        
        for section in self.sections:
            # Add section heading
            level_prefix = '#' * section.level.value
            markdown.append(f"{level_prefix} {section.title}\n")
            
            # Add section content
            if section.content:
                markdown.append(f"{section.content}\n\n")
            
            # Add subsections
            for subsection in section.subsections:
                sub_level_prefix = '#' * subsection.level.value
                markdown.append(f"{sub_level_prefix} {subsection.title}\n")
                
                if subsection.content:
                    markdown.append(f"{subsection.content}\n\n")
        
        return ''.join(markdown) 