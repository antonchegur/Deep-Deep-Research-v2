"""
Content Organizer Module

This module provides the main content organization functionality, integrating
the analyzer, summarizer, and table of contents generator.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging

from ..synthesizer import SynthesisResult
from .analyzer import ContentAnalyzer
from .structure import ContentStructure, Section, Subsection, HeadingLevel
from .summarizer import ExecutiveSummarizer
from .toc_generator import TableOfContentsGenerator

logger = logging.getLogger(__name__)


@dataclass
class OrganizedContent:
    """Represents fully organized research content."""
    title: str
    executive_summary: str
    table_of_contents: str
    content_structure: ContentStructure
    formatted_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "title": self.title,
            "executive_summary": self.executive_summary,
            "table_of_contents": self.table_of_contents,
            "content_structure": self.content_structure.to_dict(),
            "formatted_content": self.formatted_content,
            "metadata": self.metadata
        }


class ContentOrganizer:
    """
    Main content organization system that implements a complete pipeline
    for structuring research content.
    """
    
    def __init__(self, max_summary_length: int = 500, 
                toc_max_depth: int = 3,
                include_page_numbers: bool = True):
        """
        Initialize the content organizer.
        
        Args:
            max_summary_length: Maximum length for executive summaries
            toc_max_depth: Maximum heading depth for table of contents
            include_page_numbers: Whether to include page numbers in TOC
        """
        self.analyzer = ContentAnalyzer()
        self.summarizer = ExecutiveSummarizer(max_length=max_summary_length)
        self.toc_generator = TableOfContentsGenerator(
            include_page_numbers=include_page_numbers,
            max_depth=toc_max_depth
        )
    
    def organize_content(self, synthesis_result: SynthesisResult,
                       output_format: str = 'markdown') -> OrganizedContent:
        """
        Organize research content from synthesis results.
        
        Args:
            synthesis_result: Research synthesis results to organize
            output_format: Format for the organized content ('markdown', 'html', 'text')
            
        Returns:
            Fully organized content
        """
        # Step 1: Analyze the content to create a structured representation
        content_structure = self.analyzer.analyze_synthesis_result(synthesis_result)
        
        # Step 2: Generate or use executive summary
        if content_structure.executive_summary:
            executive_summary = content_structure.executive_summary
        else:
            executive_summary = self.summarizer.generate_summary(content_structure)
            # Update the structure with the summary
            content_structure.executive_summary = executive_summary
        
        # Step 3: Generate table of contents
        table_of_contents = self.toc_generator.generate_toc(
            content_structure,
            format_type=output_format
        )
        
        # Step 4: Format the content based on the structure
        if output_format == 'markdown':
            formatted_content = content_structure.to_markdown()
        elif output_format == 'html':
            formatted_content = self._format_html(content_structure)
        else:  # text
            formatted_content = self._format_text(content_structure)
        
        # Create organized content result
        return OrganizedContent(
            title=content_structure.title,
            executive_summary=executive_summary,
            table_of_contents=table_of_contents,
            content_structure=content_structure,
            formatted_content=formatted_content,
            metadata={
                "synthesis_type": synthesis_result.synthesis_type.value,
                "source_count": synthesis_result.sources_used,
                "language": synthesis_result.language,
                "generated_at": synthesis_result.generated_at.isoformat()
            }
        )
    
    def organize_from_text(self, title: str, content: str,
                        output_format: str = 'markdown') -> OrganizedContent:
        """
        Organize plain text content without synthesis results.
        
        Args:
            title: Title for the content
            content: Text content to organize
            output_format: Format for the organized content
            
        Returns:
            Fully organized content
        """
        # Parse the structure from plain text
        content_structure = ContentStructure.from_plain_text(title, content)
        
        # Generate executive summary
        executive_summary = self.summarizer._extract_key_sentences(content)
        content_structure.executive_summary = executive_summary
        
        # Generate table of contents
        table_of_contents = self.toc_generator.generate_toc(
            content_structure,
            format_type=output_format
        )
        
        # Format the content
        if output_format == 'markdown':
            formatted_content = content_structure.to_markdown()
        elif output_format == 'html':
            formatted_content = self._format_html(content_structure)
        else:  # text
            formatted_content = self._format_text(content_structure)
        
        # Create organized content result
        return OrganizedContent(
            title=title,
            executive_summary=executive_summary,
            table_of_contents=table_of_contents,
            content_structure=content_structure,
            formatted_content=formatted_content
        )
    
    def refine_structure(self, content_structure: ContentStructure,
                       balance_sections: bool = True,
                       reorder_sections: bool = False) -> ContentStructure:
        """
        Refine an existing content structure to improve organization.
        
        Args:
            content_structure: Structure to refine
            balance_sections: Whether to balance section lengths
            reorder_sections: Whether to reorder sections for better flow
            
        Returns:
            Refined content structure
        """
        # Make a deep copy of the structure to avoid modifying the original
        refined = ContentStructure(
            title=content_structure.title,
            executive_summary=content_structure.executive_summary
        )
        refined.metadata = content_structure.metadata.copy()
        
        # Copy sections and subsections
        for section in content_structure.sections:
            new_section = Section(
                id=section.id,
                title=section.title,
                content=section.content,
                level=section.level,
                metadata=section.metadata.copy()
            )
            
            for subsection in section.subsections:
                new_subsection = Subsection(
                    id=subsection.id,
                    title=subsection.title,
                    content=subsection.content,
                    level=subsection.level,
                    metadata=subsection.metadata.copy()
                )
                new_section.add_subsection(new_subsection)
            
            refined.add_section(new_section)
        
        # Reorder sections if requested
        if reorder_sections:
            self._reorder_sections(refined)
        
        # Balance section lengths if requested
        if balance_sections:
            self._balance_sections(refined)
        
        return refined
    
    def _format_html(self, structure: ContentStructure) -> str:
        """Format content structure as HTML."""
        html_lines = [f"<h1>{structure.title}</h1>"]
        
        if structure.executive_summary:
            html_lines.append("<h2 id='executive-summary'>Executive Summary</h2>")
            html_lines.append(f"<div class='executive-summary'>{structure.executive_summary}</div>")
        
        for section in structure.sections:
            # Create HTML ID from section title
            section_id = self.toc_generator._create_anchor(section.title)
            
            # Add section heading
            heading_level = min(section.level.value, 6)  # HTML only has h1-h6
            html_lines.append(f"<h{heading_level} id='{section_id}'>{section.title}</h{heading_level}>")
            
            # Add section content
            if section.content:
                html_lines.append(f"<div class='section-content'>{section.content}</div>")
            
            # Add subsections
            for subsection in section.subsections:
                # Create HTML ID from subsection title
                subsection_id = self.toc_generator._create_anchor(subsection.title)
                
                # Add subsection heading
                sub_heading_level = min(subsection.level.value, 6)
                html_lines.append(f"<h{sub_heading_level} id='{subsection_id}'>{subsection.title}</h{sub_heading_level}>")
                
                # Add subsection content
                if subsection.content:
                    html_lines.append(f"<div class='subsection-content'>{subsection.content}</div>")
        
        return "\n".join(html_lines)
    
    def _format_text(self, structure: ContentStructure) -> str:
        """Format content structure as plain text."""
        text_lines = [structure.title.upper(), "=" * len(structure.title), ""]
        
        if structure.executive_summary:
            text_lines.append("EXECUTIVE SUMMARY")
            text_lines.append("-" * 16)
            text_lines.append(structure.executive_summary)
            text_lines.append("")
        
        for section in structure.sections:
            # Add section heading
            text_lines.append(section.title.upper())
            text_lines.append("-" * len(section.title))
            
            # Add section content
            if section.content:
                text_lines.append(section.content)
                text_lines.append("")
            
            # Add subsections
            for subsection in section.subsections:
                # Add subsection heading with appropriate indentation
                text_lines.append(f"  {subsection.title}")
                text_lines.append("  " + "-" * len(subsection.title))
                
                # Add subsection content with indentation
                if subsection.content:
                    indented_content = "\n".join(f"  {line}" for line in subsection.content.split("\n"))
                    text_lines.append(indented_content)
                    text_lines.append("")
        
        return "\n".join(text_lines)
    
    def _reorder_sections(self, structure: ContentStructure) -> None:
        """
        Reorder sections for better logical flow.
        This is a placeholder implementation that uses section titles to determine order.
        A more sophisticated approach would analyze content relationships.
        """
        # Common section prefixes that indicate ordering
        ordered_prefixes = ["introduction", "background", "method", "result", "discussion", "conclusion"]
        
        # Assign a position score to each section
        section_scores = []
        for i, section in enumerate(structure.sections):
            title_lower = section.title.lower()
            score = i  # Default position is the current position
            
            # Check if the title starts with one of the ordered prefixes
            for pos, prefix in enumerate(ordered_prefixes):
                if title_lower.startswith(prefix):
                    score = pos
                    break
            
            section_scores.append((section, score))
        
        # Sort sections by position score
        sorted_sections = [s for s, _ in sorted(section_scores, key=lambda x: x[1])]
        
        # Update section order
        structure.sections = sorted_sections
    
    def _balance_sections(self, structure: ContentStructure) -> None:
        """
        Balance section lengths to improve readability.
        This implementation merges very short sections and splits very long ones.
        """
        # Calculate the average section length
        total_length = sum(len(section.content) for section in structure.sections)
        avg_length = total_length / len(structure.sections) if structure.sections else 0
        
        # Identify very short sections (less than 30% of average)
        short_threshold = avg_length * 0.3
        # Identify very long sections (more than 200% of average)
        long_threshold = avg_length * 2
        
        # Process sections to merge short ones and split long ones
        i = 0
        while i < len(structure.sections) - 1:
            section = structure.sections[i]
            next_section = structure.sections[i + 1]
            
            # If both current and next sections are short, consider merging them
            current_length = len(section.content)
            next_length = len(next_section.content)
            
            if current_length < short_threshold and next_length < short_threshold:
                # Merge the sections if they have compatible titles
                if self._are_sections_compatible(section, next_section):
                    # Create a new combined title
                    combined_title = self._create_combined_title(section.title, next_section.title)
                    
                    # Merge content
                    section.title = combined_title
                    section.content = f"{section.content}\n\n{next_section.content}"
                    
                    # Move subsections from the next section to this one
                    for subsection in next_section.subsections:
                        section.add_subsection(subsection)
                    
                    # Remove the next section
                    structure.sections.pop(i + 1)
                    continue  # Don't increment i to check if the merged section should be merged again
            
            # If the current section is very long, consider splitting it
            elif current_length > long_threshold and len(section.content.split('\n\n')) > 2:
                # Only split if the section doesn't already have subsections
                if not section.subsections:
                    # Split into paragraphs
                    paragraphs = section.content.split('\n\n')
                    
                    # Use the first paragraph as the section content
                    section.content = paragraphs[0]
                    
                    # Create subsections from remaining paragraphs
                    for j, para in enumerate(paragraphs[1:]):
                        # Generate a title from the paragraph
                        first_words = para.split()[:5]
                        title = " ".join(first_words) + "..."
                        
                        subsection = Subsection(
                            id=f"{section.id}-{j+1}",
                            title=title[:50],  # Limit title length
                            content=para,
                            level=HeadingLevel.HEADING_2
                        )
                        section.add_subsection(subsection)
            
            i += 1
    
    def _are_sections_compatible(self, section1: Section, section2: Section) -> bool:
        """Check if two sections have related content and can be merged."""
        # Check title similarity
        title1 = section1.title.lower()
        title2 = section2.title.lower()
        
        # Consider sections compatible if they share words in their titles
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        return bool(words1.intersection(words2))
    
    def _create_combined_title(self, title1: str, title2: str) -> str:
        """Create a combined title from two section titles."""
        # If one title is substantively contained in the other, use the longer one
        if title1.lower() in title2.lower():
            return title2
        elif title2.lower() in title1.lower():
            return title1
        
        # Otherwise, combine them
        return f"{title1} & {title2}" 