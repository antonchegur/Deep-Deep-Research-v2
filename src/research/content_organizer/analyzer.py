"""
Content Analyzer Module

This module provides tools for analyzing and extracting structure from research content.
"""

import re
from typing import Dict, List, Set, Tuple, Optional, Any, Union
import logging
from collections import Counter

from ..synthesizer import SynthesisResult 
from .structure import ContentStructure, Section, Subsection, HeadingLevel

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """
    Analyzes content to identify key topics, structure, and organization.
    """
    
    def __init__(self, min_section_length: int = 200, min_topic_frequency: int = 2):
        """
        Initialize a content analyzer.
        
        Args:
            min_section_length: Minimum character length for a valid section
            min_topic_frequency: Minimum frequency for a term to be considered a key topic
        """
        self.min_section_length = min_section_length
        self.min_topic_frequency = min_topic_frequency
        
        # Common stop words to filter out in topic extraction
        self.stop_words = {
            'the', 'and', 'a', 'an', 'in', 'on', 'at', 'of', 'to', 'for', 'with',
            'by', 'as', 'this', 'that', 'these', 'those', 'from', 'is', 'are', 'was',
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'but', 'or', 'if', 'because', 'as', 'until', 'while', 'about', 'against',
            'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below'
        }
    
    def analyze_synthesis_result(self, synthesis_result: SynthesisResult) -> ContentStructure:
        """
        Analyze a synthesis result to create a structured content representation.
        
        Args:
            synthesis_result: The synthesis result to analyze
            
        Returns:
            ContentStructure object representing the organized content
        """
        # Use existing sections if available
        if synthesis_result.sections:
            # The synthesizer already provided structured content
            return self._structure_from_sections(synthesis_result)
        else:
            # Need to extract structure from raw content
            return self._extract_structure_from_text(synthesis_result)
    
    def _structure_from_sections(self, synthesis_result: SynthesisResult) -> ContentStructure:
        """Create a content structure from pre-defined sections."""
        structure = ContentStructure(
            title=synthesis_result.title,
            executive_summary=synthesis_result.content[:500] if len(synthesis_result.content) > 500 else None
        )
        
        for idx, (section_title, section_content) in enumerate(synthesis_result.sections.items()):
            section = Section(
                id=f"section-{idx+1}",
                title=section_title,
                content=section_content,
                level=HeadingLevel.HEADING_1
            )
            
            # Try to identify subsections using formatting patterns
            subsections = self._extract_subsections(section_content)
            
            if subsections:
                # If we found subsections, update the section content to exclude them
                section.content = section_content.split('\n\n')[0] if '\n\n' in section_content else ""
                
                # Add each subsection
                for sub_idx, (sub_title, sub_content) in enumerate(subsections.items()):
                    subsection = Subsection(
                        id=f"section-{idx+1}-{sub_idx+1}",
                        title=sub_title,
                        content=sub_content,
                        level=HeadingLevel.HEADING_2
                    )
                    section.add_subsection(subsection)
            
            structure.add_section(section)
        
        return structure
    
    def _extract_structure_from_text(self, synthesis_result: SynthesisResult) -> ContentStructure:
        """Extract content structure from unstructured text."""
        # Try to identify structure from markdown-style headings first
        content = synthesis_result.content
        
        # Check if content has markdown headings
        has_markdown_headings = bool(re.search(r'^#+\s+.+$', content, re.MULTILINE))
        
        if has_markdown_headings:
            # Use the built-in parser for text with markdown headings
            return ContentStructure.from_plain_text(
                title=synthesis_result.title, 
                content=content
            )
        else:
            # Extract topics and create a structure manually
            structure = ContentStructure(
                title=synthesis_result.title,
                executive_summary=content[:500] if len(content) > 500 else None
            )
            
            # Try to segment the content by paragraphs
            paragraphs = self._split_into_paragraphs(content)
            
            if len(paragraphs) <= 1:
                # If there's only one paragraph, just add it as a single section
                section = Section(
                    id="section-1",
                    title="Overview",
                    content=content,
                    level=HeadingLevel.HEADING_1
                )
                structure.add_section(section)
            else:
                # Try to group paragraphs into logical sections based on content
                topic_clusters = self._cluster_paragraphs_by_topics(paragraphs)
                
                for idx, (topic, para_indices) in enumerate(topic_clusters.items()):
                    # Combine paragraphs for this topic
                    section_content = "\n\n".join([paragraphs[i] for i in para_indices])
                    
                    section = Section(
                        id=f"section-{idx+1}",
                        title=topic,
                        content=section_content,
                        level=HeadingLevel.HEADING_1
                    )
                    structure.add_section(section)
            
            return structure
    
    def _extract_subsections(self, content: str) -> Dict[str, str]:
        """Try to extract subsections based on formatting cues."""
        subsections = {}
        
        # Look for bulleted lists or numbered lists that might indicate subsections
        bullet_pattern = r'(?:^|\n)(?:[-•*]|\d+\.)\s+([A-Z][^.!?]*(?:[.!?]|$))'
        bullet_matches = re.finditer(bullet_pattern, content)
        
        current_subsection = None
        current_content = []
        
        for match in bullet_matches:
            bullet_point = match.group(1).strip()
            
            # If the bullet point is a full sentence and is at least 3 words,
            # consider it as a potential subsection title
            if len(bullet_point.split()) >= 3 and bullet_point[0].isupper():
                if current_subsection:
                    subsections[current_subsection] = '\n'.join(current_content).strip()
                
                current_subsection = bullet_point
                current_content = []
            elif current_subsection:
                current_content.append(bullet_point)
        
        # Add the last subsection if there is one
        if current_subsection and current_content:
            subsections[current_subsection] = '\n'.join(current_content).strip()
        
        return subsections
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs based on blank lines."""
        # Remove trailing/leading whitespace
        text = text.strip()
        
        # Split by double newlines or more
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Filter out very short paragraphs
        return [p.strip() for p in paragraphs if len(p.strip()) > self.min_section_length]
    
    def _extract_key_terms(self, text: str, top_n: int = 10) -> List[str]:
        """Extract the most significant terms from text."""
        # Remove punctuation and convert to lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Split into words and filter out stop words and short words
        words = [word for word in text.split() if word not in self.stop_words and len(word) > 3]
        
        # Count word frequencies
        word_counts = Counter(words)
        
        # Get the most common words
        return [word for word, count in word_counts.most_common(top_n) 
                if count >= self.min_topic_frequency]
    
    def _cluster_paragraphs_by_topics(self, paragraphs: List[str]) -> Dict[str, List[int]]:
        """Group paragraphs into topics based on content similarity."""
        # Extract key terms from each paragraph
        paragraph_terms = [set(self._extract_key_terms(p)) for p in paragraphs]
        
        # Create initial clusters based on term overlap
        clusters = {}
        assigned_paragraphs = set()
        
        # First pass: create clusters for paragraphs with significant term overlap
        for i in range(len(paragraphs)):
            if i in assigned_paragraphs:
                continue
            
            cluster_indices = [i]
            cluster_terms = paragraph_terms[i]
            assigned_paragraphs.add(i)
            
            for j in range(i+1, len(paragraphs)):
                if j in assigned_paragraphs:
                    continue
                
                # Calculate overlap
                overlap = len(cluster_terms.intersection(paragraph_terms[j]))
                
                # If significant overlap, add to cluster
                if overlap >= 2:  # Require at least 2 shared terms
                    cluster_indices.append(j)
                    cluster_terms.update(paragraph_terms[j])
                    assigned_paragraphs.add(j)
            
            # Generate a title for the cluster
            if len(cluster_indices) > 0:
                # Use the first few words of the first paragraph as the title
                first_para = paragraphs[cluster_indices[0]]
                title_match = re.match(r'^((?:[A-Z][a-z]*\s+){2,5})', first_para)
                
                if title_match:
                    cluster_title = title_match.group(1).strip()
                else:
                    # Or use the most common terms
                    all_terms = []
                    for idx in cluster_indices:
                        all_terms.extend(self._extract_key_terms(paragraphs[idx], top_n=5))
                    
                    term_counts = Counter(all_terms)
                    top_terms = [term for term, _ in term_counts.most_common(2)]
                    cluster_title = " ".join(top_terms).title()
                
                clusters[cluster_title] = cluster_indices
        
        # Second pass: assign any remaining paragraphs to the closest cluster
        for i in range(len(paragraphs)):
            if i not in assigned_paragraphs:
                best_overlap = 0
                best_cluster = None
                
                for cluster_title, cluster_indices in clusters.items():
                    cluster_terms = set()
                    for idx in cluster_indices:
                        cluster_terms.update(paragraph_terms[idx])
                    
                    overlap = len(cluster_terms.intersection(paragraph_terms[i]))
                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_cluster = cluster_title
                
                if best_cluster:
                    clusters[best_cluster].append(i)
                else:
                    # Create a new single-paragraph cluster
                    first_words = paragraphs[i].split()[:5]
                    new_title = " ".join(first_words).title()
                    clusters[new_title] = [i]
        
        return clusters 