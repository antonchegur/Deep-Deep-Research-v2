"""
Implementations of different chunking strategies.

This module provides various chunking strategies that can be used
depending on the specific requirements of the task and content type.
"""

import re
import uuid
import hashlib
from typing import List, Dict, Set, Optional, Any, Tuple
import math

from .base import Chunk, ChunkMetadata, ChunkingStrategy, ChunkType


class FixedSizeChunker(ChunkingStrategy):
    """
    Chunks text into fixed-size segments based on token or character count.
    
    While simple, this approach ensures consistent chunk sizes but may break
    semantic units like sentences or paragraphs.
    """
    
    def __init__(self, 
                chunk_size: int = 500,
                overlap: int = 50,
                by_tokens: bool = True):
        """
        Initialize fixed size chunker.
        
        Args:
            chunk_size: Size of each chunk in tokens or characters
            overlap: Amount of overlap between chunks in tokens or characters
            by_tokens: If True, size is measured in tokens; if False, in characters
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.by_tokens = by_tokens
    
    def chunk_text(self, 
                  text: str, 
                  source_id: str,
                  source_title: str,
                  max_chunk_size: Optional[int] = None,
                  overlap: Optional[int] = None) -> List[Chunk]:
        """
        Split text into chunks of fixed size.
        
        Args:
            text: The text to chunk
            source_id: ID of the source document
            source_title: Title of the source document
            max_chunk_size: Override default chunk size if provided
            overlap: Override default overlap if provided
            
        Returns:
            List of Chunk objects
        """
        # Use provided values or defaults
        chunk_size = max_chunk_size or self.chunk_size
        overlap_size = overlap or self.overlap
        
        chunks = []
        
        if self.by_tokens:
            # Split by tokens (approximated as words)
            words = text.split()
            total_words = len(words)
            
            # Calculate chunks
            offset = chunk_size - overlap_size
            start_indices = list(range(0, total_words, offset))
            
            # Ensure we don't create empty chunks at the end
            if start_indices and start_indices[-1] >= total_words:
                start_indices.pop()
            
            # Create chunks
            for i, start_idx in enumerate(start_indices):
                end_idx = min(start_idx + chunk_size, total_words)
                chunk_text = " ".join(words[start_idx:end_idx])
                
                # Create chunk with metadata
                chunk_id = f"{source_id}_{i}_{hashlib.md5(chunk_text.encode()).hexdigest()[:8]}"
                metadata = ChunkMetadata(
                    source_id=source_id,
                    source_title=source_title,
                    chunk_index=i,
                    total_chunks=len(start_indices),
                    chunk_type=ChunkType.FIXED_SIZE,
                    tokens=self.estimate_tokens(chunk_text),
                    characters=len(chunk_text),
                    importance_score=0.5  # Default score
                )
                
                chunks.append(Chunk(id=chunk_id, content=chunk_text, metadata=metadata))
        else:
            # Split by characters
            total_chars = len(text)
            
            # Calculate chunks
            offset = chunk_size - overlap_size
            start_indices = list(range(0, total_chars, offset))
            
            # Ensure we don't create empty chunks at the end
            if start_indices and start_indices[-1] >= total_chars:
                start_indices.pop()
            
            # Create chunks
            for i, start_idx in enumerate(start_indices):
                end_idx = min(start_idx + chunk_size, total_chars)
                chunk_text = text[start_idx:end_idx]
                
                # Create chunk with metadata
                chunk_id = f"{source_id}_{i}_{hashlib.md5(chunk_text.encode()).hexdigest()[:8]}"
                metadata = ChunkMetadata(
                    source_id=source_id,
                    source_title=source_title,
                    chunk_index=i,
                    total_chunks=len(start_indices),
                    chunk_type=ChunkType.FIXED_SIZE,
                    tokens=self.estimate_tokens(chunk_text),
                    characters=len(chunk_text),
                    importance_score=0.5  # Default score
                )
                
                chunks.append(Chunk(id=chunk_id, content=chunk_text, metadata=metadata))
        
        # Link chunks
        for i in range(len(chunks) - 1):
            chunks[i].metadata.next_chunk_id = chunks[i+1].id
            chunks[i+1].metadata.prev_chunk_id = chunks[i].id
        
        return chunks
    
    def merge_chunks(self, chunks: List[Chunk], max_size: int) -> List[Chunk]:
        """
        Merge chunks while respecting maximum size.
        
        Args:
            chunks: List of chunks to merge
            max_size: Maximum size for merged chunks
            
        Returns:
            List of merged chunks
        """
        # Simple implementation that just combines consecutive chunks up to max_size
        if not chunks:
            return []
        
        merged_chunks = []
        current_content = []
        current_size = 0
        chunk_count = 0
        
        for chunk in sorted(chunks, key=lambda c: (c.metadata.source_id, c.metadata.chunk_index)):
            # If adding this chunk would exceed max size, start a new merged chunk
            if current_size + chunk.metadata.tokens > max_size and current_content:
                # Create merged chunk
                merged_content = "\n\n".join(current_content)
                merged_id = f"merged_{uuid.uuid4().hex[:8]}"
                
                metadata = ChunkMetadata(
                    source_id=chunks[0].metadata.source_id,
                    source_title=chunks[0].metadata.source_title,
                    chunk_index=len(merged_chunks),
                    total_chunks=-1,  # Updated later
                    chunk_type=ChunkType.FIXED_SIZE,
                    tokens=current_size,
                    characters=sum(len(c) for c in current_content) + (len(current_content) - 1) * 2,
                    importance_score=0.5
                )
                
                merged_chunks.append(Chunk(id=merged_id, content=merged_content, metadata=metadata))
                
                # Reset for next merged chunk
                current_content = [chunk.content]
                current_size = chunk.metadata.tokens
                chunk_count = 1
            else:
                # Add to current merged chunk
                current_content.append(chunk.content)
                current_size += chunk.metadata.tokens
                chunk_count += 1
        
        # Add the last merged chunk if there's anything left
        if current_content:
            merged_content = "\n\n".join(current_content)
            merged_id = f"merged_{uuid.uuid4().hex[:8]}"
            
            metadata = ChunkMetadata(
                source_id=chunks[0].metadata.source_id,
                source_title=chunks[0].metadata.source_title,
                chunk_index=len(merged_chunks),
                total_chunks=-1,
                chunk_type=ChunkType.FIXED_SIZE,
                tokens=current_size,
                characters=sum(len(c) for c in current_content) + (len(current_content) - 1) * 2,
                importance_score=0.5
            )
            
            merged_chunks.append(Chunk(id=merged_id, content=merged_content, metadata=metadata))
        
        # Update total_chunks
        total = len(merged_chunks)
        for chunk in merged_chunks:
            chunk.metadata.total_chunks = total
        
        return merged_chunks


class ParagraphChunker(ChunkingStrategy):
    """
    Chunks text based on paragraph boundaries.
    
    This approach preserves paragraph structure but may result
    in chunks of varying sizes.
    """
    
    def __init__(self, 
                max_chunk_size: int = 800,
                min_chunk_size: int = 100):
        """
        Initialize paragraph chunker.
        
        Args:
            max_chunk_size: Maximum chunk size in tokens
            min_chunk_size: Minimum chunk size in tokens for combining small paragraphs
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
    
    def chunk_text(self, 
                  text: str, 
                  source_id: str,
                  source_title: str,
                  max_chunk_size: Optional[int] = None,
                  overlap: int = 0) -> List[Chunk]:
        """
        Split text by paragraphs and combine as needed.
        
        Args:
            text: The text to chunk
            source_id: ID of the source document
            source_title: Title of the source document
            max_chunk_size: Override default max chunk size if provided
            overlap: Number of tokens to overlap (not used in this implementation)
            
        Returns:
            List of Chunk objects
        """
        max_size = max_chunk_size or self.max_chunk_size
        
        # Split text into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # Calculate token counts for each paragraph
        para_tokens = [self.estimate_tokens(p) for p in paragraphs]
        
        # Group paragraphs into chunks
        chunks_text = []
        current_chunk = []
        current_tokens = 0
        
        for i, (para, tokens) in enumerate(zip(paragraphs, para_tokens)):
            # If this paragraph alone exceeds max size, split it further
            if tokens > max_size:
                # Add current chunk if not empty
                if current_chunk:
                    chunks_text.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0
                
                # Split large paragraph into sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                sentence_chunk = []
                sentence_tokens = 0
                
                for sentence in sentences:
                    sent_tokens = self.estimate_tokens(sentence)
                    
                    if sentence_tokens + sent_tokens <= max_size:
                        sentence_chunk.append(sentence)
                        sentence_tokens += sent_tokens
                    else:
                        # Add current sentence chunk
                        if sentence_chunk:
                            chunks_text.append(" ".join(sentence_chunk))
                            sentence_chunk = []
                            sentence_tokens = 0
                        
                        # If single sentence is too large, split by words
                        if sent_tokens > max_size:
                            words = sentence.split()
                            word_chunks = []
                            word_chunk = []
                            word_tokens = 0
                            
                            for word in words:
                                word_token_est = max(1, len(word) // 4)  # Rough estimate
                                
                                if word_tokens + word_token_est <= max_size:
                                    word_chunk.append(word)
                                    word_tokens += word_token_est
                                else:
                                    if word_chunk:
                                        word_chunks.append(" ".join(word_chunk))
                                        word_chunk = []
                                        word_tokens = 0
                                    
                                    word_chunk.append(word)
                                    word_tokens = word_token_est
                            
                            if word_chunk:
                                word_chunks.append(" ".join(word_chunk))
                            
                            # Add word chunks to main chunks
                            chunks_text.extend(word_chunks)
                        else:
                            sentence_chunk.append(sentence)
                            sentence_tokens = sent_tokens
                
                # Add final sentence chunk
                if sentence_chunk:
                    chunks_text.append(" ".join(sentence_chunk))
            
            # If adding this paragraph would exceed max size
            elif current_tokens + tokens > max_size:
                # Add current chunk
                chunks_text.append("\n\n".join(current_chunk))
                
                # Start new chunk with this paragraph
                current_chunk = [para]
                current_tokens = tokens
            else:
                # Add paragraph to current chunk
                current_chunk.append(para)
                current_tokens += tokens
        
        # Add the last chunk if there's anything left
        if current_chunk:
            chunks_text.append("\n\n".join(current_chunk))
        
        # Create Chunk objects with metadata
        chunks = []
        for i, content in enumerate(chunks_text):
            chunk_id = f"{source_id}_p{i}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
            
            metadata = ChunkMetadata(
                source_id=source_id,
                source_title=source_title,
                chunk_index=i,
                total_chunks=len(chunks_text),
                chunk_type=ChunkType.PARAGRAPH,
                tokens=self.estimate_tokens(content),
                characters=len(content),
                importance_score=0.5  # Default score
            )
            
            chunks.append(Chunk(id=chunk_id, content=content, metadata=metadata))
        
        # Link chunks
        for i in range(len(chunks) - 1):
            chunks[i].metadata.next_chunk_id = chunks[i+1].id
            chunks[i+1].metadata.prev_chunk_id = chunks[i].id
        
        return chunks
    
    def merge_chunks(self, chunks: List[Chunk], max_size: int) -> List[Chunk]:
        """
        Merge chunks while respecting paragraph boundaries and maximum size.
        
        Args:
            chunks: List of chunks to merge
            max_size: Maximum size for merged chunks
            
        Returns:
            List of merged chunks
        """
        # Delegate to generic implementation
        merged = []
        current_content = []
        current_size = 0
        
        for chunk in sorted(chunks, key=lambda c: (c.metadata.source_id, c.metadata.chunk_index)):
            # If adding this chunk would exceed max size, start a new merged chunk
            if current_size + chunk.metadata.tokens > max_size and current_content:
                # Create merged chunk
                merged_content = "\n\n".join(current_content)
                merged_id = f"merged_p{uuid.uuid4().hex[:8]}"
                
                metadata = ChunkMetadata(
                    source_id=chunks[0].metadata.source_id,
                    source_title=chunks[0].metadata.source_title,
                    chunk_index=len(merged),
                    total_chunks=-1,  # Updated later
                    chunk_type=ChunkType.PARAGRAPH,
                    tokens=current_size,
                    characters=sum(len(c) for c in current_content) + (len(current_content) - 1) * 2,
                    importance_score=0.5
                )
                
                merged.append(Chunk(id=merged_id, content=merged_content, metadata=metadata))
                
                # Reset for next merged chunk
                current_content = [chunk.content]
                current_size = chunk.metadata.tokens
            else:
                # Add to current merged chunk
                current_content.append(chunk.content)
                current_size += chunk.metadata.tokens
        
        # Add the last merged chunk if there's anything left
        if current_content:
            merged_content = "\n\n".join(current_content)
            merged_id = f"merged_p{uuid.uuid4().hex[:8]}"
            
            metadata = ChunkMetadata(
                source_id=chunks[0].metadata.source_id,
                source_title=chunks[0].metadata.source_title,
                chunk_index=len(merged),
                total_chunks=-1,
                chunk_type=ChunkType.PARAGRAPH,
                tokens=current_size,
                characters=sum(len(c) for c in current_content) + (len(current_content) - 1) * 2,
                importance_score=0.5
            )
            
            merged.append(Chunk(id=merged_id, content=merged_content, metadata=metadata))
        
        # Update total_chunks
        total = len(merged)
        for chunk in merged:
            chunk.metadata.total_chunks = total
        
        return merged


class HybridChunker(ChunkingStrategy):
    """
    Combines multiple chunking strategies for optimal results.
    
    This approach uses semantic boundaries when possible but falls back to
    other strategies to ensure chunk size constraints are met.
    """
    
    def __init__(self, 
                max_chunk_size: int = 800,
                min_chunk_size: int = 100,
                prefer_semantic: bool = True):
        """
        Initialize hybrid chunker.
        
        Args:
            max_chunk_size: Maximum chunk size in tokens
            min_chunk_size: Minimum chunk size in tokens
            prefer_semantic: Whether to prioritize semantic boundaries
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.prefer_semantic = prefer_semantic
        
        # Initialize sub-chunkers
        from .semantic_chunking import SemanticChunker
        self.semantic_chunker = SemanticChunker(
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size
        )
        self.paragraph_chunker = ParagraphChunker(
            max_chunk_size=max_chunk_size,
            min_chunk_size=min_chunk_size
        )
        self.fixed_chunker = FixedSizeChunker(
            chunk_size=max_chunk_size,
            overlap=min(100, max_chunk_size // 8)
        )
    
    def chunk_text(self, 
                  text: str, 
                  source_id: str,
                  source_title: str,
                  max_chunk_size: Optional[int] = None,
                  overlap: int = 0) -> List[Chunk]:
        """
        Apply multiple chunking strategies and select the best result.
        
        Args:
            text: The text to chunk
            source_id: ID of the source document
            source_title: Title of the source document
            max_chunk_size: Override default max chunk size if provided
            overlap: Number of tokens to overlap
            
        Returns:
            List of Chunk objects
        """
        max_size = max_chunk_size or self.max_chunk_size
        
        # Try semantic chunking first
        semantic_chunks = self.semantic_chunker.chunk_text(
            text=text,
            source_id=source_id,
            source_title=source_title,
            max_chunk_size=max_size,
            overlap=overlap
        )
        
        # Check if semantic chunking produced valid chunks
        semantic_valid = all(c.metadata.tokens <= max_size for c in semantic_chunks)
        
        # If semantic chunking was valid and we prefer it, use those chunks
        if semantic_valid and self.prefer_semantic:
            for chunk in semantic_chunks:
                chunk.metadata.chunk_type = ChunkType.HYBRID
            return semantic_chunks
        
        # Try paragraph chunking
        paragraph_chunks = self.paragraph_chunker.chunk_text(
            text=text,
            source_id=source_id,
            source_title=source_title,
            max_chunk_size=max_size,
            overlap=overlap
        )
        
        # Check if paragraph chunking produced valid chunks
        paragraph_valid = all(c.metadata.tokens <= max_size for c in paragraph_chunks)
        
        # If paragraph chunking was valid, use those chunks
        if paragraph_valid:
            for chunk in paragraph_chunks:
                chunk.metadata.chunk_type = ChunkType.HYBRID
            return paragraph_chunks
        
        # Fall back to fixed-size chunking
        fixed_chunks = self.fixed_chunker.chunk_text(
            text=text,
            source_id=source_id,
            source_title=source_title,
            max_chunk_size=max_size,
            overlap=overlap
        )
        
        for chunk in fixed_chunks:
            chunk.metadata.chunk_type = ChunkType.HYBRID
        
        return fixed_chunks
    
    def merge_chunks(self, chunks: List[Chunk], max_size: int) -> List[Chunk]:
        """
        Merge chunks using the appropriate strategy based on chunk type.
        
        Args:
            chunks: List of chunks to merge
            max_size: Maximum size for merged chunks
            
        Returns:
            List of merged chunks
        """
        # Group chunks by type
        chunks_by_type = {}
        for chunk in chunks:
            chunk_type = chunk.metadata.chunk_type
            if chunk_type not in chunks_by_type:
                chunks_by_type[chunk_type] = []
            chunks_by_type[chunk_type].append(chunk)
        
        # Merge each group with appropriate strategy
        merged_chunks = []
        
        for chunk_type, type_chunks in chunks_by_type.items():
            if chunk_type == ChunkType.SEMANTIC:
                merged = self.semantic_chunker.merge_chunks(type_chunks, max_size)
            elif chunk_type == ChunkType.PARAGRAPH:
                merged = self.paragraph_chunker.merge_chunks(type_chunks, max_size)
            else:
                merged = self.fixed_chunker.merge_chunks(type_chunks, max_size)
            
            merged_chunks.extend(merged)
        
        # Sort by source and index
        merged_chunks.sort(key=lambda c: (c.metadata.source_id, c.metadata.chunk_index))
        
        # Update chunk indices and total count
        for i, chunk in enumerate(merged_chunks):
            chunk.metadata.chunk_index = i
            chunk.metadata.chunk_type = ChunkType.HYBRID
        
        total = len(merged_chunks)
        for chunk in merged_chunks:
            chunk.metadata.total_chunks = total
        
        # Link chunks
        for i in range(len(merged_chunks) - 1):
            merged_chunks[i].metadata.next_chunk_id = merged_chunks[i+1].id
            merged_chunks[i+1].metadata.prev_chunk_id = merged_chunks[i].id
        
        return merged_chunks 