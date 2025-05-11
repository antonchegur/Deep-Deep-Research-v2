"""
Content prioritization for chunking algorithms.

This module provides algorithms and utilities for identifying and prioritizing
important content when processing research documents.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Tuple, Union
import re
import math
import logging

from .base import Chunk, ChunkMetadata, ChunkType

logger = logging.getLogger(__name__)


class ContentPriority(Enum):
    """Priority levels for content segments."""
    CRITICAL = 4    # Must be preserved (key findings, conclusions)
    HIGH = 3        # Very important (methods, results)
    MEDIUM = 2      # Important (background, explanations)
    LOW = 1         # Less important (general descriptions)
    MINIMAL = 0     # Least important (redundant info, filler)


@dataclass
class PriorityScore:
    """Detailed scoring for a content segment."""
    raw_score: float                   # Base score from 0.0 to 1.0
    priority_level: ContentPriority    # Categorical priority level
    factors: Dict[str, float] = field(default_factory=dict)  # Contributing factors to score


class ContentPrioritizer:
    """
    Evaluates and prioritizes content based on importance for research synthesis.
    
    This class analyzes text to identify high-value content that should be
    preserved during chunking, ensuring that critical information is maintained.
    """
    
    # Patterns indicating important content
    CITATION_PATTERN = r'\((?:[A-Za-z]+(?:,?\s*(?:&|and)\s*[A-Za-z]+)?,\s*\d{4}(?:;\s*)?)+\)'
    STATISTIC_PATTERN = r'(?:(?:p|r|t|F|χ²|d|η²|β)\s*(?:<|>|=|≈)\s*(?:\.?\d+))'
    KEY_FINDING_PHRASES = [
        r'demonstrate(?:s|d) that', r'show(?:s|ed) that', r'reveal(?:s|ed) that',
        r'confirm(?:s|ed) that', r'prove(?:s|d) that', r'establish(?:es|ed) that',
        r'significant(?:ly)?', r'substantial(?:ly)?', r'remarkable', r'notable',
        r'important(?:ly)?', r'crucial(?:ly)?', r'essential(?:ly)?',
        r'key finding', r'main result', r'critical insight'
    ]
    SECTION_HEADER_IMPORTANCE = {
        'abstract': 0.9, 'summary': 0.9, 'conclusion': 0.9, 'result': 0.85, 
        'discussion': 0.8, 'method': 0.75, 'background': 0.6, 
        'introduction': 0.7, 'related work': 0.5
    }
    
    def __init__(self, 
                 citation_weight: float = 0.6,
                 statistic_weight: float = 0.7,
                 key_finding_weight: float = 0.8,
                 section_weight: float = 0.65,
                 numerical_weight: float = 0.5):
        """
        Initialize the content prioritizer.
        
        Args:
            citation_weight: Weight given to citation presence
            statistic_weight: Weight given to statistical findings
            key_finding_weight: Weight given to key finding phrases
            section_weight: Weight given to important sections
            numerical_weight: Weight given to numerical data presence
        """
        self.citation_weight = citation_weight
        self.statistic_weight = statistic_weight
        self.key_finding_weight = key_finding_weight
        self.section_weight = section_weight
        self.numerical_weight = numerical_weight
        
        # Compile regex patterns
        self.citation_regex = re.compile(self.CITATION_PATTERN)
        self.statistic_regex = re.compile(self.STATISTIC_PATTERN)
        self.key_finding_regex = re.compile(
            r'|'.join(self.KEY_FINDING_PHRASES), 
            re.IGNORECASE
        )
        self.numerical_regex = re.compile(r'\b\d+(?:\.\d+)?%?\b')
        
    def prioritize_text(self, text: str, section_name: Optional[str] = None) -> PriorityScore:
        """
        Calculate priority score for a text segment.
        
        Args:
            text: Text content to evaluate
            section_name: Name of the section this text belongs to, if known
            
        Returns:
            PriorityScore with calculated priority information
        """
        factors = {}
        
        # 1. Check for citations
        citation_count = len(self.citation_regex.findall(text))
        citation_factor = min(1.0, citation_count * 0.2) * self.citation_weight
        factors['citations'] = citation_factor
        
        # 2. Check for statistics
        statistic_count = len(self.statistic_regex.findall(text))
        statistic_factor = min(1.0, statistic_count * 0.25) * self.statistic_weight
        factors['statistics'] = statistic_factor
        
        # 3. Check for key finding phrases
        key_finding_count = len(self.key_finding_regex.findall(text))
        key_finding_factor = min(1.0, key_finding_count * 0.3) * self.key_finding_weight
        factors['key_findings'] = key_finding_factor
        
        # 4. Apply section importance if known
        section_factor = 0.0
        if section_name:
            # Normalize section name for lookup
            norm_section = section_name.lower().strip()
            # Look for partial matches with section names
            for key, value in self.SECTION_HEADER_IMPORTANCE.items():
                if key in norm_section:
                    section_factor = value * self.section_weight
                    break
        factors['section'] = section_factor
        
        # 5. Check for numerical data
        numerical_count = len(self.numerical_regex.findall(text))
        numerical_factor = min(1.0, numerical_count * 0.1) * self.numerical_weight
        factors['numerical_data'] = numerical_factor
        
        # Calculate raw score (weighted average of factors)
        raw_score = sum(factors.values()) / len(factors)
        
        # Determine priority level based on raw score
        priority_level = ContentPriority.MINIMAL
        if raw_score >= 0.8:
            priority_level = ContentPriority.CRITICAL
        elif raw_score >= 0.6:
            priority_level = ContentPriority.HIGH
        elif raw_score >= 0.4:
            priority_level = ContentPriority.MEDIUM
        elif raw_score >= 0.2:
            priority_level = ContentPriority.LOW
            
        return PriorityScore(
            raw_score=round(raw_score, 2),
            priority_level=priority_level,
            factors=factors
        )
    
    def prioritize_chunk(self, chunk: Chunk) -> Chunk:
        """
        Evaluate a chunk and update its metadata with priority information.
        
        Args:
            chunk: Chunk to evaluate
            
        Returns:
            Updated chunk with priority information
        """
        # Extract section from chunk content if possible
        section_match = re.search(r'^#+\s*(.+?)$', chunk.content, re.MULTILINE)
        section_name = section_match.group(1) if section_match else None
        
        # Get priority score
        priority = self.prioritize_text(chunk.content, section_name)
        
        # Update chunk metadata
        chunk.metadata.importance_score = priority.raw_score
        chunk.metadata.custom_data['priority_level'] = priority.priority_level.name
        chunk.metadata.custom_data['priority_factors'] = priority.factors
        
        # Add topic information if not already present
        if not chunk.metadata.semantic_topics and section_name:
            chunk.metadata.semantic_topics = [section_name.lower()]
            
        return chunk
    
    def prioritize_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Evaluate and prioritize a list of chunks.
        
        Args:
            chunks: List of chunks to evaluate
            
        Returns:
            List of updated chunks with priority information
        """
        return [self.prioritize_chunk(chunk) for chunk in chunks]


class PrioritizedChunker:
    """
    Wrapper around any chunking strategy that applies content prioritization.
    
    This class enhances an existing chunking strategy by ensuring high-priority
    content is preserved and properly handled during the chunking process.
    """
    
    def __init__(self, 
                 base_chunker: Any,
                 prioritizer: Optional[ContentPrioritizer] = None,
                 preserve_critical: bool = True,
                 max_critical_chunk_factor: float = 1.5):
        """
        Initialize a prioritized chunker.
        
        Args:
            base_chunker: Base chunking strategy to enhance
            prioritizer: Content prioritizer instance (created if None)
            preserve_critical: Whether critical chunks can exceed max size limits
            max_critical_chunk_factor: Max factor by which critical chunks can exceed limits
        """
        self.base_chunker = base_chunker
        self.prioritizer = prioritizer or ContentPrioritizer()
        self.preserve_critical = preserve_critical
        self.max_critical_chunk_factor = max_critical_chunk_factor
    
    def chunk_text(self, 
                  text: str, 
                  source_id: str,
                  source_title: str,
                  max_chunk_size: Optional[int] = None,
                  overlap: int = 0) -> List[Chunk]:
        """
        Chunk text with priority-aware processing.
        
        Args:
            text: The text to chunk
            source_id: ID of the source document
            source_title: Title of the source document
            max_chunk_size: Maximum chunk size in tokens
            overlap: Number of tokens to overlap between chunks
            
        Returns:
            List of prioritized Chunk objects
        """
        # First, get chunks from base chunker
        base_chunks = self.base_chunker.chunk_text(
            text=text,
            source_id=source_id,
            source_title=source_title,
            max_chunk_size=max_chunk_size,
            overlap=overlap
        )
        
        # Apply prioritization to each chunk
        prioritized_chunks = self.prioritizer.prioritize_chunks(base_chunks)
        
        # Adjust chunks based on priority if preserve_critical is enabled
        if self.preserve_critical:
            max_size = max_chunk_size or getattr(self.base_chunker, 'max_chunk_size', 1000)
            prioritized_chunks = self._adjust_chunks_by_priority(prioritized_chunks, max_size)
        
        return prioritized_chunks
    
    def _adjust_chunks_by_priority(self, chunks: List[Chunk], max_size: int) -> List[Chunk]:
        """
        Adjust chunk boundaries based on priority to preserve critical content.
        
        Args:
            chunks: List of prioritized chunks
            max_size: Maximum regular chunk size
            
        Returns:
            List of adjusted chunks
        """
        # Special handling isn't needed if we have 0-1 chunks
        if len(chunks) <= 1:
            return chunks
            
        adjusted_chunks = []
        i = 0
        
        while i < len(chunks):
            current = chunks[i]
            
            # If this is a critical chunk, consider extending it
            if (current.metadata.custom_data.get('priority_level') == ContentPriority.CRITICAL.name and
                i < len(chunks) - 1):
                
                next_chunk = chunks[i + 1]
                combined_tokens = current.metadata.tokens + next_chunk.metadata.tokens
                
                # If combining with next chunk is within our extended limit
                if combined_tokens <= max_size * self.max_critical_chunk_factor:
                    # Combine chunks
                    combined_content = current.content + "\n\n" + next_chunk.content
                    combined_chunk = Chunk(
                        id=f"{current.id}_extended",
                        content=combined_content,
                        metadata=ChunkMetadata(
                            source_id=current.metadata.source_id,
                            source_title=current.metadata.source_title,
                            chunk_index=len(adjusted_chunks),
                            total_chunks=-1,  # Will update later
                            chunk_type=current.metadata.chunk_type,
                            tokens=combined_tokens,
                            characters=len(combined_content),
                            importance_score=max(current.metadata.importance_score, next_chunk.metadata.importance_score),
                            semantic_topics=list(set(current.metadata.semantic_topics + next_chunk.metadata.semantic_topics))
                        )
                    )
                    
                    # Re-analyze priority of combined chunk
                    combined_chunk = self.prioritizer.prioritize_chunk(combined_chunk)
                    adjusted_chunks.append(combined_chunk)
                    i += 2  # Skip next chunk since we combined it
                    continue
            
            # Otherwise, keep the chunk as is
            adjusted_chunks.append(current)
            i += 1
        
        # Update chunk indices and total count
        total = len(adjusted_chunks)
        for idx, chunk in enumerate(adjusted_chunks):
            chunk.metadata.chunk_index = idx
            chunk.metadata.total_chunks = total
            
            # Update next/prev links
            if idx > 0:
                chunk.metadata.prev_chunk_id = adjusted_chunks[idx-1].id
            if idx < total - 1:
                chunk.metadata.next_chunk_id = adjusted_chunks[idx+1].id
                
        return adjusted_chunks
    
    def merge_chunks(self, chunks: List[Chunk], max_size: int) -> List[Chunk]:
        """
        Merge chunks with priority awareness.
        
        Args:
            chunks: List of chunks to merge
            max_size: Maximum size for merged chunks
            
        Returns:
            List of merged chunks
        """
        # Delegate to base chunker for merging
        merged = self.base_chunker.merge_chunks(chunks, max_size)
        
        # Apply prioritization to merged chunks
        return self.prioritizer.prioritize_chunks(merged) 