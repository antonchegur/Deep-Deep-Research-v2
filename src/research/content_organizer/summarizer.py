"""
Executive Summarizer Module

This module provides tools for generating concise executive summaries from research content.
"""

import re
from typing import Dict, List, Optional
import logging
from collections import Counter

from ..synthesizer import SynthesisResult
from .structure import ContentStructure

logger = logging.getLogger(__name__)


class ExecutiveSummarizer:
    """
    Generates executive summaries from research content.
    
    Implements multiple strategies for summary generation, including:
    1. Extraction-based summaries (using key sentences)
    2. Using existing summaries if available
    3. Structure-based summarization using section headers and first sentences
    """
    
    def __init__(self, max_length: int = 500, min_sentences: int = 3, max_sentences: int = 7):
        """
        Initialize the executive summarizer.
        
        Args:
            max_length: Maximum character length for the summary
            min_sentences: Minimum number of sentences to include
            max_sentences: Maximum number of sentences to include
        """
        self.max_length = max_length
        self.min_sentences = min_sentences
        self.max_sentences = max_sentences
    
    def generate_summary(self, content_structure: ContentStructure) -> str:
        """
        Generate an executive summary from a content structure.
        
        Args:
            content_structure: Structured content to summarize
            
        Returns:
            Executive summary text
        """
        # If there's already an executive summary, use it
        if content_structure.executive_summary:
            # Check if it's within our length limits
            if len(content_structure.executive_summary) <= self.max_length:
                return content_structure.executive_summary
            else:
                # Truncate to max_length at sentence boundary
                return self._truncate_at_sentence(content_structure.executive_summary)
        
        # Otherwise, generate a summary based on the content structure
        return self._generate_from_structure(content_structure)
    
    def generate_summary_from_synthesis(self, synthesis_result: SynthesisResult) -> str:
        """
        Generate an executive summary directly from synthesis results.
        
        Args:
            synthesis_result: Synthesis result to summarize
            
        Returns:
            Executive summary text
        """
        # Use the first 500 characters of the content as a summary
        if len(synthesis_result.content) <= self.max_length:
            # Content is already short enough
            return synthesis_result.content
        
        # Check if the first paragraph is a good summary
        paragraphs = synthesis_result.content.split('\n\n')
        first_paragraph = paragraphs[0].strip()
        
        if len(first_paragraph) <= self.max_length and len(first_paragraph) > 100:
            # First paragraph is a good size for a summary
            return first_paragraph
        
        # Extract key sentences from the content
        return self._extract_key_sentences(synthesis_result.content)
    
    def _generate_from_structure(self, content_structure: ContentStructure) -> str:
        """Generate a summary based on the content structure."""
        # Start with the title
        summary_parts = [f"{content_structure.title}"]
        
        # Add key points from each section
        section_points = []
        
        for section in content_structure.sections:
            # Use the first sentence of each section if it's substantive
            section_text = section.content.strip()
            if section_text:
                first_sentence = self._get_first_sentence(section_text)
                if first_sentence and len(first_sentence) > 20:  # Only if it's a real sentence
                    section_points.append(first_sentence)
        
        # If we have enough points, use them
        if len(section_points) >= self.min_sentences:
            summary_parts.append(' '.join(section_points[:self.max_sentences]))
            summary = ' '.join(summary_parts)
            
            # Check if we need to truncate
            if len(summary) > self.max_length:
                summary = self._truncate_at_sentence(summary)
            
            return summary
        
        # If we don't have enough section points, extract key sentences from all content
        all_content = []
        for section in content_structure.sections:
            all_content.append(section.content)
            for subsection in section.subsections:
                all_content.append(subsection.content)
        
        combined_content = '\n\n'.join(all_content)
        return self._extract_key_sentences(combined_content)
    
    def _extract_key_sentences(self, text: str) -> str:
        """Extract key sentences to form a summary."""
        # Split text into sentences
        sentence_pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, text)
        
        # Remove very short sentences
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        if not sentences:
            return text[:self.max_length] + "..."
        
        # If we only have a few sentences, use them all
        if len(sentences) <= self.max_sentences:
            summary = ' '.join(sentences)
            if len(summary) <= self.max_length:
                return summary
            return self._truncate_at_sentence(summary)
        
        # Score sentences based on position and key terms
        scored_sentences = self._score_sentences(sentences)
        
        # Select top sentences
        selected_sentences = [sentences[idx] for idx, _ in scored_sentences[:self.max_sentences]]
        
        # Reorder selected sentences to match original order
        selected_indices = [idx for idx, _ in scored_sentences[:self.max_sentences]]
        selected_indices.sort()
        ordered_sentences = [sentences[idx] for idx in selected_indices]
        
        # Join sentences and check length
        summary = ' '.join(ordered_sentences)
        
        # Truncate if still too long
        if len(summary) > self.max_length:
            summary = self._truncate_at_sentence(summary)
        
        return summary
    
    def _score_sentences(self, sentences: List[str]) -> List[tuple]:
        """Score sentences based on position and content."""
        scores = []
        
        # Extract key terms from all sentences combined
        all_text = ' '.join(sentences)
        key_terms = self._extract_key_terms(all_text)
        
        for idx, sentence in enumerate(sentences):
            score = 0
            
            # Position score: first and last sentences get higher scores
            if idx == 0:
                score += 5  # First sentence
            elif idx == len(sentences) - 1:
                score += 3  # Last sentence
            elif idx <= 2:
                score += 2  # Early sentences
            
            # Content score: sentences with key terms get higher scores
            sentence_lower = sentence.lower()
            for term in key_terms:
                if term in sentence_lower:
                    score += 1
            
            # Length score: prefer medium-length sentences
            length = len(sentence)
            if 50 <= length <= 200:
                score += 2
            elif length < 50:
                score -= 1  # Penalize very short sentences
            elif length > 300:
                score -= 2  # Penalize very long sentences
            
            scores.append((idx, score))
        
        # Sort by score in descending order
        return sorted(scores, key=lambda x: x[1], reverse=True)
    
    def _extract_key_terms(self, text: str, top_n: int = 10) -> List[str]:
        """Extract key terms from text for scoring sentences."""
        # Remove punctuation and convert to lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Common stop words to filter out
        stop_words = {
            'the', 'and', 'a', 'an', 'in', 'on', 'at', 'of', 'to', 'for', 'with',
            'by', 'as', 'this', 'that', 'these', 'those', 'from', 'is', 'are', 'was',
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'but', 'or', 'if', 'because', 'as', 'until', 'while', 'about', 'against',
            'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below'
        }
        
        # Split into words and filter out stop words and short words
        words = [word for word in text.split() if word not in stop_words and len(word) > 3]
        
        # Count word frequencies
        word_counts = Counter(words)
        
        # Get the most common words
        return [word for word, count in word_counts.most_common(top_n)]
    
    def _get_first_sentence(self, text: str) -> Optional[str]:
        """Extract the first sentence from a text."""
        match = re.match(r'([^.!?]+[.!?])', text)
        if match:
            return match.group(1).strip()
        return None
    
    def _truncate_at_sentence(self, text: str) -> str:
        """Truncate text at a sentence boundary to fit within max_length."""
        if len(text) <= self.max_length:
            return text
        
        # Find the last sentence boundary before max_length
        truncated = text[:self.max_length]
        last_boundary = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
        
        if last_boundary > self.max_length // 2:  # Only truncate if we have a good amount of text
            return text[:last_boundary + 1]
        else:
            return truncated + "..." 