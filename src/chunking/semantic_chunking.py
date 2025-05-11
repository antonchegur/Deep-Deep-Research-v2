"""
Semantic chunking implementation for research text.

This module provides advanced semantic chunking techniques that divide
text based on semantic boundaries rather than arbitrary character limits.
"""

import re
import uuid
import logging
from typing import Dict, List, Tuple, Optional, Any, Set
import hashlib

from .base import Chunk, ChunkMetadata, ChunkingStrategy, ChunkType

logger = logging.getLogger(__name__)


class SemanticChunker(ChunkingStrategy):
    """
    Implements semantic-aware text chunking.
    
    This strategy analyzes text for semantic boundaries such as topic shifts,
    section headers, and natural paragraph breaks to create more meaningful chunks.
    It prioritizes keeping related content together and maintaining context.
    """
    
    # Regex patterns for detecting structural elements
    SECTION_HEADER_PATTERN = r"(?:^|\n)(?:#{1,6}|\d+\.\s+|\*\*|__)[^#\n\*_]{3,50}(?:\*\*|__)?\s*(?:\n|$)"
    KEY_SENTENCE_PATTERNS = [
        r"(?:^|\s)(?:in (?:summary|conclusion)|to summarize|importantly|significantly|notably|therefore|thus|hence|in (?:particular|essence))",
        r"(?:^|\s)(?:this (?:paper|study|research|work|analysis) (?:shows|demonstrates|reveals|suggests|indicates|concludes))",
        r"(?:^|\s)(?:results (?:show|demonstrate|reveal|suggest|indicate)|findings (?:show|demonstrate|reveal|suggest|indicate))"
    ]
    
    def __init__(self, 
                 min_chunk_size: int = 100,
                 max_chunk_size: int = 1000,
                 overlap_strategy: str = "semantic",
                 semantic_threshold: float = 0.7):
        """
        Initialize semantic chunker.
        
        Args:
            min_chunk_size: Minimum chunk size in tokens
            max_chunk_size: Maximum chunk size in tokens
            overlap_strategy: Strategy for chunk overlap ('semantic', 'fixed', 'none')
            semantic_threshold: Threshold for semantic similarity (0.0-1.0)
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_strategy = overlap_strategy
        self.semantic_threshold = semantic_threshold
    
    def chunk_text(self, 
                  text: str, 
                  source_id: str,
                  source_title: str,
                  max_chunk_size: Optional[int] = None,
                  overlap: int = 100) -> List[Chunk]:
        """
        Split text into chunks based on semantic boundaries.
        
        Args:
            text: The text to chunk
            source_id: ID of the source document
            source_title: Title of the source document
            max_chunk_size: Maximum size of each chunk (tokens)
            overlap: Number of tokens to overlap between chunks
            
        Returns:
            List of Chunk objects
        """
        if max_chunk_size is None:
            max_chunk_size = self.max_chunk_size
        
        # 1. Identify semantic boundaries
        boundaries = self._identify_semantic_boundaries(text)
        
        # 2. Split text into semantic units
        semantic_units = self._split_into_semantic_units(text, boundaries)
        
        # 3. Combine units into appropriate sized chunks
        raw_chunks = self._combine_semantic_units(
            semantic_units, 
            max_size=max_chunk_size,
            min_size=self.min_chunk_size
        )
        
        # 4. Process chunks (add overlaps, metadata, etc.)
        processed_chunks = self._process_chunks(
            raw_chunks,
            source_id=source_id,
            source_title=source_title,
            overlap=overlap
        )
        
        # 5. Perform post-processing (add relationships, importance scores)
        final_chunks = self._post_process_chunks(processed_chunks)
        
        logger.info(f"Split text into {len(final_chunks)} semantic chunks")
        return final_chunks
    
    def merge_chunks(self, chunks: List[Chunk], max_size: int) -> List[Chunk]:
        """
        Merge semantically related chunks while respecting size constraints.
        
        Args:
            chunks: List of chunks to merge
            max_size: Maximum token size for merged chunks
            
        Returns:
            List of merged chunks
        """
        if not chunks:
            return []
        
        # Group chunks by source
        chunks_by_source = {}
        for chunk in chunks:
            source_id = chunk.metadata.source_id
            if source_id not in chunks_by_source:
                chunks_by_source[source_id] = []
            chunks_by_source[source_id].append(chunk)
        
        # Merge chunks within each source
        merged_chunks = []
        for source_id, source_chunks in chunks_by_source.items():
            # Sort chunks by index
            sorted_chunks = sorted(source_chunks, key=lambda c: c.metadata.chunk_index)
            
            current_merged = None
            current_tokens = 0
            
            for chunk in sorted_chunks:
                # If we don't have a current merged chunk or adding this would exceed max size
                if (current_merged is None or 
                    current_tokens + chunk.metadata.tokens > max_size):
                    # Start a new merged chunk
                    if current_merged:
                        merged_chunks.append(current_merged)
                    
                    # Create new merged chunk
                    chunk_id = f"merged_{uuid.uuid4().hex[:8]}"
                    metadata = ChunkMetadata(
                        source_id=chunk.metadata.source_id,
                        source_title=chunk.metadata.source_title,
                        chunk_index=len(merged_chunks),
                        total_chunks=-1,  # Will update later
                        chunk_type=ChunkType.HYBRID,
                        importance_score=chunk.metadata.importance_score,
                        tokens=chunk.metadata.tokens,
                        characters=len(chunk.content),
                        semantic_topics=chunk.metadata.semantic_topics.copy()
                    )
                    
                    current_merged = Chunk(
                        id=chunk_id,
                        content=chunk.content,
                        metadata=metadata
                    )
                    current_tokens = chunk.metadata.tokens
                else:
                    # Append to current merged chunk
                    current_merged.content += f"\n\n{chunk.content}"
                    current_merged.metadata.tokens += chunk.metadata.tokens
                    current_merged.metadata.characters += len(chunk.content) + 2  # +2 for newlines
                    
                    # Update semantic topics
                    topics = set(current_merged.metadata.semantic_topics)
                    topics.update(chunk.metadata.semantic_topics)
                    current_merged.metadata.semantic_topics = list(topics)
                    
                    # Update importance score to the max of the chunks
                    current_merged.metadata.importance_score = max(
                        current_merged.metadata.importance_score,
                        chunk.metadata.importance_score
                    )
                    
                    current_tokens += chunk.metadata.tokens
            
            # Add the last merged chunk if it exists
            if current_merged:
                merged_chunks.append(current_merged)
        
        # Update total_chunks for all merged chunks
        total_merged = len(merged_chunks)
        for chunk in merged_chunks:
            chunk.metadata.total_chunks = total_merged
        
        return merged_chunks
    
    def _identify_semantic_boundaries(self, text: str) -> List[int]:
        """
        Identify indices where semantic boundaries occur.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of index positions for semantic boundaries
        """
        boundaries = set()
        
        # 1. Section headers
        for match in re.finditer(self.SECTION_HEADER_PATTERN, text, re.MULTILINE):
            boundaries.add(match.start())
            boundaries.add(match.end())
        
        # 2. Paragraph breaks (double newlines)
        for match in re.finditer(r"\n\s*\n", text):
            boundaries.add(match.start())
            boundaries.add(match.end())
        
        # 3. Key sentences that indicate topic shifts
        for pattern in self.KEY_SENTENCE_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Find the sentence start
                sent_start = text.rfind(".", 0, match.start())
                if sent_start == -1:
                    sent_start = 0
                else:
                    sent_start += 1  # Skip the period
                
                # Find the sentence end
                sent_end = text.find(".", match.end())
                if sent_end == -1:
                    sent_end = len(text)
                else:
                    sent_end += 1  # Include the period
                
                boundaries.add(sent_start)
                boundaries.add(sent_end)
        
        # Convert to sorted list
        return sorted(list(boundaries))
    
    def _split_into_semantic_units(self, text: str, boundaries: List[int]) -> List[str]:
        """
        Split text into semantic units based on identified boundaries.
        
        Args:
            text: Text to split
            boundaries: List of boundary indices
            
        Returns:
            List of semantic text units
        """
        if not boundaries:
            return [text]
        
        units = []
        start_idx = 0
        
        for boundary in boundaries:
            # Skip boundaries at the start
            if boundary <= start_idx:
                continue
            
            unit = text[start_idx:boundary].strip()
            if unit:  # Only add non-empty units
                units.append(unit)
            
            start_idx = boundary
        
        # Add final unit if necessary
        final_unit = text[start_idx:].strip()
        if final_unit:
            units.append(final_unit)
        
        return units
    
    def _combine_semantic_units(self, 
                               units: List[str], 
                               max_size: int,
                               min_size: int) -> List[str]:
        """
        Combine semantic units into appropriate sized chunks.
        
        Args:
            units: List of semantic text units
            max_size: Maximum token size for each chunk
            min_size: Minimum token size for each chunk
            
        Returns:
            List of raw text chunks
        """
        chunks = []
        current_chunk = []
        current_size = 0
        
        for unit in units:
            unit_size = self.estimate_tokens(unit)
            
            # If this unit alone exceeds max_size, split it further
            if unit_size > max_size:
                # First, add the current chunk if it's not empty
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split large unit by sentences
                sentences = re.split(r'(?<=[.!?])\s+', unit)
                sentence_chunk = []
                sentence_size = 0
                
                for sentence in sentences:
                    sentence_tokens = self.estimate_tokens(sentence)
                    
                    # If adding this sentence wouldn't exceed the limit
                    if sentence_size + sentence_tokens <= max_size:
                        sentence_chunk.append(sentence)
                        sentence_size += sentence_tokens
                    else:
                        # Add current sentence chunk if it's not empty
                        if sentence_chunk:
                            chunks.append(" ".join(sentence_chunk))
                            sentence_chunk = []
                            sentence_size = 0
                        
                        # If a single sentence exceeds max_size, we need to truncate
                        if sentence_tokens > max_size:
                            # Split into roughly equal parts
                            words = sentence.split()
                            word_count = len(words)
                            chunk_count = (sentence_tokens // max_size) + 1
                            words_per_chunk = word_count // chunk_count
                            
                            for i in range(0, word_count, words_per_chunk):
                                word_chunk = words[i:i+words_per_chunk]
                                if word_chunk:
                                    chunks.append(" ".join(word_chunk))
                        else:
                            sentence_chunk.append(sentence)
                            sentence_size = sentence_tokens
                
                # Add any remaining sentences
                if sentence_chunk:
                    chunks.append(" ".join(sentence_chunk))
            
            # If adding this unit would exceed max_size
            elif current_size + unit_size > max_size:
                # Check if current chunk is too small
                if current_size < min_size and unit_size < max_size * 0.8:
                    # Try to split the unit to add some content to current chunk
                    sentences = re.split(r'(?<=[.!?])\s+', unit)
                    
                    for i, sentence in enumerate(sentences):
                        sentence_tokens = self.estimate_tokens(sentence)
                        
                        if current_size + sentence_tokens <= max_size:
                            current_chunk.append(sentence)
                            current_size += sentence_tokens
                            sentences[i] = ""  # Mark as used
                        else:
                            break
                    
                    # Add current chunk
                    if current_chunk:
                        chunks.append("\n".join(current_chunk))
                    
                    # Start new chunk with remaining sentences
                    remaining = " ".join([s for s in sentences if s])
                    if remaining:
                        current_chunk = [remaining]
                        current_size = self.estimate_tokens(remaining)
                    else:
                        current_chunk = []
                        current_size = 0
                else:
                    # Add current chunk and start a new one
                    chunks.append("\n".join(current_chunk))
                    current_chunk = [unit]
                    current_size = unit_size
            else:
                # Add unit to current chunk
                current_chunk.append(unit)
                current_size += unit_size
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append("\n".join(current_chunk))
        
        return chunks
    
    def _process_chunks(self, 
                       raw_chunks: List[str],
                       source_id: str,
                       source_title: str,
                       overlap: int = 100) -> List[Chunk]:
        """
        Process raw text chunks into Chunk objects with metadata.
        
        Args:
            raw_chunks: List of raw text chunks
            source_id: Source document ID
            source_title: Source document title
            overlap: Number of tokens to overlap
            
        Returns:
            List of processed Chunk objects
        """
        chunks = []
        total_chunks = len(raw_chunks)
        
        for i, content in enumerate(raw_chunks):
            # Generate a unique ID based on content and position
            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            chunk_id = f"{source_id}_{i}_{content_hash}"
            
            # Create basic metadata
            metadata = ChunkMetadata(
                source_id=source_id,
                source_title=source_title,
                chunk_index=i,
                total_chunks=total_chunks,
                chunk_type=ChunkType.SEMANTIC,
                tokens=self.estimate_tokens(content),
                characters=len(content)
            )
            
            # Add semantic topics
            metadata.semantic_topics = self._extract_topics(content)
            
            # Create the chunk
            chunk = Chunk(id=chunk_id, content=content, metadata=metadata)
            chunks.append(chunk)
        
        # Add overlaps if specified
        if overlap > 0 and self.overlap_strategy != "none" and len(chunks) > 1:
            self._add_overlaps(chunks, overlap)
        
        # Link chunks
        for i in range(len(chunks) - 1):
            chunks[i].metadata.next_chunk_id = chunks[i+1].id
            chunks[i+1].metadata.prev_chunk_id = chunks[i].id
        
        return chunks
    
    def _add_overlaps(self, chunks: List[Chunk], overlap_tokens: int):
        """
        Add overlapping content between chunks.
        
        Args:
            chunks: List of chunks to process
            overlap_tokens: Target number of tokens to overlap
        """
        if not chunks or len(chunks) < 2:
            return
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            curr_chunk = chunks[i]
            
            # Semantic overlap strategy attempts to include complete sentences/paragraphs
            if self.overlap_strategy == "semantic":
                # Extract the end of previous chunk
                prev_content = prev_chunk.content
                sentences = re.split(r'(?<=[.!?])\s+', prev_content)
                
                # Take sentences from the end until we reach target overlap
                overlap_content = ""
                overlap_size = 0
                
                for sentence in reversed(sentences):
                    sentence_size = self.estimate_tokens(sentence)
                    if overlap_size + sentence_size <= overlap_tokens:
                        overlap_content = sentence + " " + overlap_content
                        overlap_size += sentence_size
                    else:
                        break
                
                # Add overlap to beginning of current chunk if we found meaningful content
                if overlap_content and overlap_size > 0:
                    curr_chunk.content = overlap_content + "\n\n" + curr_chunk.content
                    curr_chunk.metadata.tokens += overlap_size
                    curr_chunk.metadata.characters += len(overlap_content) + 2  # +2 for newlines
            
            # Fixed overlap takes exact number of tokens
            elif self.overlap_strategy == "fixed":
                # Tokenize the previous chunk content (simplified)
                words = prev_chunk.content.split()
                
                # Calculate approximate number of words for target overlap
                target_words = int(overlap_tokens / 1.3)  # Using same token estimation
                
                if len(words) > target_words:
                    # Take the last N words
                    overlap_content = " ".join(words[-target_words:])
                    overlap_size = self.estimate_tokens(overlap_content)
                    
                    # Add to current chunk
                    curr_chunk.content = overlap_content + "\n\n" + curr_chunk.content
                    curr_chunk.metadata.tokens += overlap_size
                    curr_chunk.metadata.characters += len(overlap_content) + 2
    
    def _post_process_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Perform post-processing on chunks.
        
        Args:
            chunks: List of chunks to process
            
        Returns:
            Post-processed chunks
        """
        # Calculate chunk importance scores
        for chunk in chunks:
            # Basic importance scoring - higher score for:
            # - Chunks with section headers
            # - Chunks with keywords or key phrases
            # - Chunks with numerical data
            # - First and last chunks (intro/conclusion)
            
            score = 0.5  # Base score
            
            # Check for section headers
            if re.search(self.SECTION_HEADER_PATTERN, chunk.content):
                score += 0.2
            
            # Check for key phrases
            for pattern in self.KEY_SENTENCE_PATTERNS:
                if re.search(pattern, chunk.content, re.IGNORECASE):
                    score += 0.15
                    break
            
            # Check for numerical data (could be important statistics)
            if re.search(r'\d+(?:\.\d+)?(?:\s*%)?', chunk.content):
                score += 0.1
            
            # Boost score for first and last chunks
            if chunk.metadata.chunk_index == 0:
                score += 0.2  # Introduction
            elif chunk.metadata.chunk_index == chunk.metadata.total_chunks - 1:
                score += 0.2  # Conclusion
            
            # Cap the score at 1.0
            chunk.metadata.importance_score = min(1.0, score)
        
        return chunks
    
    def _extract_topics(self, text: str) -> List[str]:
        """
        Extract key topics from text content.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of extracted topics
        """
        # Simple keyword extraction - in a real system, use more sophisticated NLP
        # like topic modeling, named entity recognition, or keyword extraction
        topics = set()
        
        # Extract potential topics from headers
        for match in re.finditer(self.SECTION_HEADER_PATTERN, text, re.MULTILINE):
            header = match.group(0).strip()
            # Clean header of markers
            header = re.sub(r'^#+\s*|\s*#+$', '', header)
            header = re.sub(r'^\d+\.\s+', '', header)
            header = re.sub(r'\*\*|\*|__|_', '', header)
            
            if header and len(header) > 3:
                topics.add(header.lower())
        
        # Look for repeatedly mentioned terms
        words = re.findall(r'\b[A-Za-z][A-Za-z-]{3,15}\b', text.lower())
        word_counts = {}
        for word in words:
            if word not in word_counts:
                word_counts[word] = 0
            word_counts[word] += 1
        
        # Add frequently occurring non-stopwords as topics
        stopwords = {'the', 'and', 'that', 'this', 'with', 'for', 'from', 'was', 'were'}
        for word, count in word_counts.items():
            if count > 3 and word not in stopwords and len(word) > 3:
                topics.add(word)
        
        return sorted(list(topics))[:5]  # Limit to top 5 topics 