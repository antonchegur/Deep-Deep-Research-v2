"""
Context management system for GPT-4 synthesis.

This module provides tools for efficiently managing conversation context
and handling large volumes of data within token limits for LLM interactions.
"""

import logging
import re
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass

from ..adapters import SourceResult


logger = logging.getLogger(__name__)


@dataclass
class ContextWindow:
    """Represents a context window with content and metadata."""
    content: str
    token_count: int
    priority: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}


class ContextManager:
    """
    Manages context windowing and token usage for LLM interactions.
    
    Features:
    - Smart chunking of large text
    - Context prioritization
    - Token counting and management
    - Context compression algorithms
    - Storage and retrieval of context histories
    """
    
    # Average tokens per word for English text (rough estimate)
    AVG_TOKENS_PER_WORD = 1.3
    
    # Token limits for different models
    MODEL_TOKEN_LIMITS = {
        "gpt-4o": 128000,
        "gpt-4-turbo": 128000,
        "gpt-4": 8192,
        "gpt-3.5-turbo": 16384,
        "gpt-3.5-turbo-16k": 16384,
    }
    
    # Reserved tokens for response generation (default)
    DEFAULT_RESPONSE_TOKENS = 4000
    
    def __init__(self, 
                model: str = "gpt-4o",
                response_tokens: int = DEFAULT_RESPONSE_TOKENS,
                compression_level: int = 0,
                storage_path: Optional[str] = None):
        """
        Initialize context manager.
        
        Args:
            model: LLM model identifier to determine token limits
            response_tokens: Tokens to reserve for response
            compression_level: Level of compression to apply (0-3)
                0: No compression
                1: Light compression (remove redundancies)
                2: Medium compression (summarize less important content)
                3: Heavy compression (aggressively reduce context size)
            storage_path: Path to store persistent context history
        """
        self.model = model
        self.response_tokens = response_tokens
        self.compression_level = compression_level
        self.storage_path = storage_path
        
        # Determine token limit
        self.token_limit = self.MODEL_TOKEN_LIMITS.get(model, 8192)
        self.available_tokens = self.token_limit - self.response_tokens
        
        # Store current context windows
        self.context_windows: List[ContextWindow] = []
        
        # Initialize context history
        self.context_history: List[Dict[str, Any]] = []
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text.
        
        Args:
            text: Input text to estimate
            
        Returns:
            Estimated token count
        """
        # Simple estimation based on words
        words = len(re.findall(r'\b\w+\b', text))
        return int(words * self.AVG_TOKENS_PER_WORD)
    
    def add_system_prompt(self, prompt: str) -> bool:
        """
        Add system prompt to context, prioritizing it highest.
        
        Args:
            prompt: System prompt text
            
        Returns:
            Success status
        """
        tokens = self.estimate_tokens(prompt)
        
        if tokens > self.available_tokens:
            logger.warning(f"System prompt exceeds available tokens: {tokens} > {self.available_tokens}")
            return False
        
        window = ContextWindow(
            content=prompt,
            token_count=tokens,
            priority=100,  # Highest priority
            metadata={"type": "system_prompt"}
        )
        
        self.context_windows.append(window)
        self.available_tokens -= tokens
        return True
    
    def add_user_input(self, text: str, priority: int = 50) -> bool:
        """
        Add user input to context.
        
        Args:
            text: User input text
            priority: Priority level (higher gets preserved longer)
            
        Returns:
            Success status
        """
        tokens = self.estimate_tokens(text)
        
        # If not enough space, try compression
        if tokens > self.available_tokens:
            self.compress_context()
            
            # If still not enough space after compression
            if tokens > self.available_tokens:
                logger.warning(f"User input exceeds available tokens even after compression")
                return False
        
        window = ContextWindow(
            content=text,
            token_count=tokens,
            priority=priority,
            metadata={"type": "user_input"}
        )
        
        self.context_windows.append(window)
        self.available_tokens -= tokens
        return True
    
    def add_sources(self, sources: List[SourceResult], max_tokens: Optional[int] = None) -> int:
        """
        Add research sources to context, using smart chunking.
        
        Args:
            sources: List of source results
            max_tokens: Maximum tokens to use for sources (if None, use all available)
            
        Returns:
            Number of sources successfully added
        """
        sources_added = 0
        total_tokens_used = 0
        
        # Determine max tokens to use
        max_tokens = max_tokens or self.available_tokens
        
        # Prioritize sources by size and metadata
        prioritized_sources = self._prioritize_sources(sources)
        
        for source in prioritized_sources:
            # Create chunks for source content
            chunks = self._chunk_text(
                text=source.content,
                title=source.title,
                source_idx=sources_added + 1,
                max_chunk_tokens=int(max_tokens * 0.2)  # Limit each source to 20% of available
            )
            
            # Add chunks as context windows
            chunks_added = 0
            for chunk in chunks:
                # If we can add this chunk
                if chunk.token_count <= self.available_tokens and total_tokens_used + chunk.token_count <= max_tokens:
                    self.context_windows.append(chunk)
                    self.available_tokens -= chunk.token_count
                    total_tokens_used += chunk.token_count
                    chunks_added += 1
                else:
                    break  # Stop adding chunks for this source
            
            # Only count this source if at least one chunk was added
            if chunks_added > 0:
                sources_added += 1
            
            # If we can't add more sources
            if total_tokens_used >= max_tokens * 0.9:  # Leave some buffer
                break
        
        return sources_added
    
    def build_messages(self) -> List[Dict[str, str]]:
        """
        Build message list for API request.
        
        Returns:
            List of message dictionaries
        """
        messages = []
        
        # Sort windows by type and priority
        sorted_windows = sorted(
            self.context_windows,
            key=lambda w: (-100 if w.metadata.get("type") == "system_prompt" else -w.priority)
        )
        
        for window in sorted_windows:
            role = "system" if window.metadata.get("type") == "system_prompt" else "user"
            messages.append({
                "role": role,
                "content": window.content
            })
        
        return messages
    
    def compress_context(self) -> int:
        """
        Compress context to free up tokens.
        
        Returns:
            Number of tokens freed
        """
        if not self.context_windows or self.compression_level == 0:
            return 0
        
        tokens_before = sum(w.token_count for w in self.context_windows)
        
        # Sort windows by priority (lowest first)
        self.context_windows.sort(key=lambda w: w.priority)
        
        # Apply compression based on level
        if self.compression_level == 1:
            # Light compression: remove lowest priority windows
            while self.context_windows and self.available_tokens < self.token_limit * 0.2:
                window = self.context_windows.pop(0)  # Remove lowest priority
                self.available_tokens += window.token_count
                
                # Archive removed context
                self._archive_window(window)
                
                # Don't remove system prompt
                if len(self.context_windows) == 1 and self.context_windows[0].metadata.get("type") == "system_prompt":
                    break
        
        elif self.compression_level == 2:
            # Medium compression: Reduce detail in lower priority windows
            for i, window in enumerate(self.context_windows):
                # Skip system prompt and high priority windows
                if window.metadata.get("type") == "system_prompt" or window.priority > 70:
                    continue
                
                # Apply text compression
                compressed_text = self._compress_text(window.content)
                new_token_count = self.estimate_tokens(compressed_text)
                
                # Update if compression was effective
                if new_token_count < window.token_count:
                    tokens_saved = window.token_count - new_token_count
                    window.content = compressed_text
                    window.token_count = new_token_count
                    self.available_tokens += tokens_saved
        
        elif self.compression_level == 3:
            # Heavy compression: Aggressive window removal and summarization
            # First remove low priority windows
            while self.context_windows and self.available_tokens < self.token_limit * 0.4:
                if len(self.context_windows) == 1 and self.context_windows[0].metadata.get("type") == "system_prompt":
                    break
                
                window = self.context_windows.pop(0)  # Remove lowest priority
                self.available_tokens += window.token_count
                
                # Archive removed context
                self._archive_window(window)
            
            # Then compress remaining windows except system prompt
            for i, window in enumerate(self.context_windows):
                if window.metadata.get("type") == "system_prompt":
                    continue
                
                # Apply aggressive compression
                compressed_text = self._compress_text(window.content, aggressive=True)
                new_token_count = self.estimate_tokens(compressed_text)
                
                # Update if compression was effective
                if new_token_count < window.token_count:
                    tokens_saved = window.token_count - new_token_count
                    window.content = compressed_text
                    window.token_count = new_token_count
                    self.available_tokens += tokens_saved
        
        # Calculate tokens freed
        tokens_after = sum(w.token_count for w in self.context_windows)
        return tokens_before - tokens_after
    
    def clear_context(self, preserve_system: bool = True):
        """
        Clear all context windows.
        
        Args:
            preserve_system: Whether to preserve system prompt
        """
        if preserve_system:
            # Keep only system prompts
            system_windows = [w for w in self.context_windows if w.metadata.get("type") == "system_prompt"]
            system_tokens = sum(w.token_count for w in system_windows)
            
            # Archive non-system context
            for window in self.context_windows:
                if window.metadata.get("type") != "system_prompt":
                    self._archive_window(window)
            
            self.context_windows = system_windows
            self.available_tokens = self.token_limit - self.response_tokens - system_tokens
        else:
            # Archive all context
            for window in self.context_windows:
                self._archive_window(window)
                
            self.context_windows = []
            self.available_tokens = self.token_limit - self.response_tokens
    
    def _compress_text(self, text: str, aggressive: bool = False) -> str:
        """
        Compress text content to reduce tokens.
        
        Args:
            text: Text to compress
            aggressive: Whether to use aggressive compression
            
        Returns:
            Compressed text
        """
        # Remove redundant whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        if not aggressive:
            # Light compression
            # Remove some markdown formatting
            text = re.sub(r'(\*\*|\*|__|\\_|`)', '', text)
            # Simplify lists
            text = re.sub(r'\n\s*[-•*]\s*', '\n• ', text)
            
            return text
        else:
            # Aggressive compression
            # Keep only first sentence of paragraphs
            paragraphs = text.split('\n\n')
            compressed_paragraphs = []
            
            for para in paragraphs:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                if sentences:
                    compressed_paragraphs.append(sentences[0])
            
            return '\n'.join(compressed_paragraphs)
    
    def _chunk_text(self, text: str, title: str, source_idx: int, max_chunk_tokens: int) -> List[ContextWindow]:
        """
        Split text into chunks that fit within token limits.
        
        Args:
            text: Text to chunk
            title: Source title
            source_idx: Source index for reference
            max_chunk_tokens: Maximum tokens per chunk
            
        Returns:
            List of context windows
        """
        chunks = []
        
        # Try to split by paragraphs first
        paragraphs = text.split('\n\n')
        
        current_chunk = []
        current_tokens = 0
        chunk_idx = 1
        
        # Header for each chunk
        header = f"SOURCE {source_idx}: {title} (part {chunk_idx})\n"
        header_tokens = self.estimate_tokens(header)
        
        for para in paragraphs:
            para_tokens = self.estimate_tokens(para)
            
            # If this paragraph alone exceeds max chunk size, we need to split further
            if para_tokens > max_chunk_tokens - header_tokens:
                # If we have content already, finish current chunk
                if current_chunk:
                    chunk_content = header + "\n".join(current_chunk)
                    chunks.append(ContextWindow(
                        content=chunk_content,
                        token_count=current_tokens + header_tokens,
                        priority=50 - len(chunks),  # Declining priority for later chunks
                        metadata={
                            "type": "source_content",
                            "source_idx": source_idx,
                            "chunk_idx": chunk_idx,
                            "title": title
                        }
                    ))
                    
                    current_chunk = []
                    current_tokens = 0
                    chunk_idx += 1
                    header = f"SOURCE {source_idx}: {title} (part {chunk_idx})\n"
                
                # Split large paragraph into sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                
                sentence_chunk = []
                sentence_tokens = 0
                
                for sentence in sentences:
                    s_tokens = self.estimate_tokens(sentence)
                    
                    if sentence_tokens + s_tokens <= max_chunk_tokens - header_tokens:
                        sentence_chunk.append(sentence)
                        sentence_tokens += s_tokens
                    else:
                        # Finish current sentence chunk
                        if sentence_chunk:
                            chunk_content = header + " ".join(sentence_chunk)
                            chunks.append(ContextWindow(
                                content=chunk_content,
                                token_count=sentence_tokens + header_tokens,
                                priority=50 - len(chunks),
                                metadata={
                                    "type": "source_content",
                                    "source_idx": source_idx,
                                    "chunk_idx": chunk_idx,
                                    "title": title
                                }
                            ))
                            
                            sentence_chunk = [sentence]
                            sentence_tokens = s_tokens
                            chunk_idx += 1
                            header = f"SOURCE {source_idx}: {title} (part {chunk_idx})\n"
                        else:
                            # If a single sentence is too long, truncate it
                            logger.warning(f"Truncating extremely long sentence in source {source_idx}")
                            truncated = sentence[:int(len(sentence) * 0.8)]  # Take 80%
                            chunk_content = header + truncated + "..."
                            
                            chunks.append(ContextWindow(
                                content=chunk_content,
                                token_count=self.estimate_tokens(chunk_content),
                                priority=50 - len(chunks),
                                metadata={
                                    "type": "source_content",
                                    "source_idx": source_idx,
                                    "chunk_idx": chunk_idx,
                                    "title": title
                                }
                            ))
                            
                            chunk_idx += 1
                            header = f"SOURCE {source_idx}: {title} (part {chunk_idx})\n"
                
                # Add any remaining sentences
                if sentence_chunk:
                    chunk_content = header + " ".join(sentence_chunk)
                    chunks.append(ContextWindow(
                        content=chunk_content,
                        token_count=sentence_tokens + header_tokens,
                        priority=50 - len(chunks),
                        metadata={
                            "type": "source_content",
                            "source_idx": source_idx,
                            "chunk_idx": chunk_idx,
                            "title": title
                        }
                    ))
                    
                    chunk_idx += 1
                    header = f"SOURCE {source_idx}: {title} (part {chunk_idx})\n"
            
            # Normal case: add paragraph to current chunk if it fits
            elif current_tokens + para_tokens + header_tokens <= max_chunk_tokens:
                current_chunk.append(para)
                current_tokens += para_tokens
            else:
                # Finish current chunk and start a new one
                chunk_content = header + "\n".join(current_chunk)
                chunks.append(ContextWindow(
                    content=chunk_content,
                    token_count=current_tokens + header_tokens,
                    priority=50 - len(chunks),
                    metadata={
                        "type": "source_content",
                        "source_idx": source_idx,
                        "chunk_idx": chunk_idx,
                        "title": title
                    }
                ))
                
                current_chunk = [para]
                current_tokens = para_tokens
                chunk_idx += 1
                header = f"SOURCE {source_idx}: {title} (part {chunk_idx})\n"
        
        # Add final chunk if there's anything left
        if current_chunk:
            chunk_content = header + "\n".join(current_chunk)
            chunks.append(ContextWindow(
                content=chunk_content,
                token_count=current_tokens + header_tokens,
                priority=50 - len(chunks),
                metadata={
                    "type": "source_content",
                    "source_idx": source_idx,
                    "chunk_idx": chunk_idx,
                    "title": title
                }
            ))
        
        return chunks
    
    def _prioritize_sources(self, sources: List[SourceResult]) -> List[SourceResult]:
        """
        Prioritize sources based on relevance and size.
        
        Args:
            sources: List of source results
            
        Returns:
            Prioritized list of sources
        """
        # This is a simple implementation; it could be extended with more sophisticated metrics
        def score_source(source: SourceResult) -> float:
            # Basic scoring: favor academic sources and recent content
            source_type_score = {
                "ACADEMIC": 2.0,
                "WEBSITE": 1.0,
                "NEWS": 1.5,
                "WIKIPEDIA": 1.2,
                "DOCUMENT": 1.0,
                "API": 1.0
            }.get(source.source_type.value.upper(), 1.0)
            
            # Score recency if available
            recency_score = 1.0
            if source.metadata and "year" in source.metadata:
                year = source.metadata["year"]
                if isinstance(year, int) and year >= 2020:
                    recency_score = 1.5
            
            # Penalize extremely long sources slightly
            length_penalty = 1.0
            estimated_tokens = self.estimate_tokens(source.content)
            if estimated_tokens > 10000:
                length_penalty = 0.8
            
            return source_type_score * recency_score * length_penalty
        
        # Sort sources by score
        scored_sources = [(score_source(s), s) for s in sources]
        scored_sources.sort(key=lambda x: x[0], reverse=True)
        
        return [s[1] for s in scored_sources]
    
    def _archive_window(self, window: ContextWindow):
        """
        Archive a context window to history.
        
        Args:
            window: Context window to archive
        """
        self.context_history.append({
            "content": window.content[:100] + "..." if len(window.content) > 100 else window.content,
            "token_count": window.token_count,
            "priority": window.priority,
            "metadata": window.metadata
        })
        
        # Trim history if it gets too large
        if len(self.context_history) > 100:
            self.context_history = self.context_history[-100:] 