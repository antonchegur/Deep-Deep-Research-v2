"""
Advanced chunking module for handling large volumes of research sources.

This module provides efficient chunking algorithms for processing 100+ sources
while maintaining semantic coherence and optimizing for context preservation.
"""

from .semantic_chunking import SemanticChunker
from .base import Chunk, ChunkMetadata, ChunkingStrategy, ChunkType
from .chunking_strategies import FixedSizeChunker, ParagraphChunker, HybridChunker
from .content_prioritization import (
    ContentPriority, PriorityScore, ContentPrioritizer, PrioritizedChunker
)
from .metadata_handling import (
    SourceMetadata, ChunkCollection, MetadataManager, ChunkStore
)
from .optimization import (
    ChunkingPerformanceMetrics, PerformanceMonitor, 
    ChunkingOptimizer, OptimizedChunkingStrategy
)

__all__ = [
    "Chunk",
    "ChunkMetadata",
    "ChunkingStrategy",
    "ChunkType",
    "SemanticChunker",
    "FixedSizeChunker",
    "ParagraphChunker",
    "HybridChunker",
    "ContentPriority",
    "PriorityScore",
    "ContentPrioritizer",
    "PrioritizedChunker",
    "SourceMetadata",
    "ChunkCollection",
    "MetadataManager",
    "ChunkStore",
    "ChunkingPerformanceMetrics",
    "PerformanceMonitor",
    "ChunkingOptimizer",
    "OptimizedChunkingStrategy"
] 