"""
Base classes for the chunking system.

This module defines foundational classes and interfaces for text chunking,
providing a framework for various chunking strategies.
"""

import abc
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple


class ChunkType(Enum):
    """Types of chunks that can be generated."""
    SEMANTIC = "semantic"       # Based on semantic boundaries (topics, concepts)
    FIXED_SIZE = "fixed_size"   # Fixed token/character size chunks
    PARAGRAPH = "paragraph"     # Based on paragraph boundaries
    SENTENCE = "sentence"       # Based on sentence boundaries
    HYBRID = "hybrid"           # Combination of multiple strategies
    CUSTOM = "custom"           # Custom chunking strategy


@dataclass
class ChunkMetadata:
    """Metadata for a chunk, providing context and relationship information."""
    source_id: str              # ID of the source document
    source_title: str           # Title of the source document
    chunk_index: int            # Index of this chunk within the source
    total_chunks: int           # Total chunks for this source
    chunk_type: ChunkType       # Type of chunking used
    importance_score: float = 0.0  # Score indicating chunk importance (0.0-1.0)
    embedding_vector: Optional[List[float]] = None  # Vector representation if available
    prev_chunk_id: Optional[str] = None  # ID of previous chunk (for context)
    next_chunk_id: Optional[str] = None  # ID of next chunk (for context)
    tokens: int = 0             # Estimated token count
    characters: int = 0         # Character count
    semantic_topics: List[str] = field(default_factory=list)  # Main topics in chunk
    relationships: Dict[str, float] = field(default_factory=dict)  # Related chunks and scores
    custom_data: Dict[str, Any] = field(default_factory=dict)  # Custom metadata


@dataclass
class Chunk:
    """
    Represents a chunk of text with associated metadata.
    
    A chunk is a segment of a larger text document, optimized for 
    processing by large language models while preserving context.
    """
    id: str                     # Unique identifier for the chunk
    content: str                # The actual text content
    metadata: ChunkMetadata     # Associated metadata
    
    def __post_init__(self):
        """Initialize any missing fields after creation."""
        if not self.metadata.characters:
            self.metadata.characters = len(self.content)


class ChunkingStrategy(abc.ABC):
    """
    Abstract base class for chunking strategies.
    
    Chunking strategies determine how text is split into chunks,
    with different approaches optimized for different use cases.
    """
    
    @abc.abstractmethod
    def chunk_text(self, 
                  text: str, 
                  source_id: str,
                  source_title: str,
                  max_chunk_size: int,
                  overlap: int = 0) -> List[Chunk]:
        """
        Split text into chunks according to the strategy.
        
        Args:
            text: The text to chunk
            source_id: ID of the source document
            source_title: Title of the source document
            max_chunk_size: Maximum size of each chunk (tokens or chars)
            overlap: Number of tokens/chars to overlap between chunks
            
        Returns:
            List of Chunk objects
        """
        pass
    
    @abc.abstractmethod
    def merge_chunks(self, chunks: List[Chunk], max_size: int) -> List[Chunk]:
        """
        Merge chunks while respecting maximum size constraints.
        
        Args:
            chunks: List of chunks to merge
            max_size: Maximum size constraint
            
        Returns:
            List of merged chunks
        """
        pass
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate the number of tokens in text.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Simple estimation based on word count
        # This is a rough estimate; production code should use model-specific tokenizers
        words = len(text.split())
        return int(words * 1.3)  # Approximate token count (1.3 tokens per word) 