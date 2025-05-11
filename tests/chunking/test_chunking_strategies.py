"""
Tests for chunking strategies.

This file contains unit tests for the various chunking strategies.
"""

import unittest
import re

from src.chunking.base import Chunk, ChunkMetadata, ChunkType
from src.chunking.chunking_strategies import (
    FixedSizeChunker,
    ParagraphChunker,
    HybridChunker
)


class TestFixedSizeChunker(unittest.TestCase):
    """Test cases for the FixedSizeChunker class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.chunker = FixedSizeChunker(
            chunk_size=100,
            overlap=20,
            by_tokens=True
        )
        
        # Simple test text
        self.test_text = "This is a simple test text. " * 50
    
    def test_initial_configuration(self):
        """Test that the chunker is initialized with correct parameters."""
        self.assertEqual(self.chunker.chunk_size, 100)
        self.assertEqual(self.chunker.overlap, 20)
        self.assertTrue(self.chunker.by_tokens)
    
    def test_chunk_text_by_tokens(self):
        """Test chunking text by tokens."""
        chunks = self.chunker.chunk_text(
            text=self.test_text,
            source_id="test-123",
            source_title="Test Document"
        )
        
        # We should get multiple chunks
        self.assertGreater(len(chunks), 1)
        
        # Verify chunk properties
        for i, chunk in enumerate(chunks):
            self.assertIsInstance(chunk, Chunk)
            self.assertEqual(chunk.metadata.source_id, "test-123")
            self.assertEqual(chunk.metadata.chunk_type, ChunkType.FIXED_SIZE)
            
            # Check that chunks have content
            self.assertGreater(len(chunk.content), 0)
            
            # Token count should be around our target (or less for the last chunk)
            if i < len(chunks) - 1:
                self.assertLessEqual(chunk.metadata.tokens, 120)  # Allow some margin
                self.assertGreaterEqual(chunk.metadata.tokens, 80)  # Allow some margin
    
    def test_chunk_text_by_characters(self):
        """Test chunking text by characters."""
        char_chunker = FixedSizeChunker(
            chunk_size=100,
            overlap=20,
            by_tokens=False
        )
        
        chunks = char_chunker.chunk_text(
            text=self.test_text,
            source_id="test-123",
            source_title="Test Document"
        )
        
        # We should get multiple chunks
        self.assertGreater(len(chunks), 1)
        
        # Verify chunk character counts
        for i, chunk in enumerate(chunks):
            # First chunks should be close to our target size
            if i < len(chunks) - 1:
                self.assertLessEqual(len(chunk.content), 100)
                self.assertGreaterEqual(len(chunk.content), 80)
    
    def test_chunk_overlap(self):
        """Test that chunks have proper overlap."""
        chunks = self.chunker.chunk_text(
            text=self.test_text,
            source_id="test-123",
            source_title="Test Document"
        )
        
        # Need at least 2 chunks to test overlap
        if len(chunks) < 2:
            self.skipTest("Not enough chunks to test overlap")
        
        # Check for overlap between first two chunks
        first_chunk_words = chunks[0].content.split()
        second_chunk_words = chunks[1].content.split()
        
        # Get the last 'overlap' words from first chunk
        overlap_from_first = first_chunk_words[-self.chunker.overlap:]
        
        # Get the first 'overlap' words from second chunk
        overlap_from_second = second_chunk_words[:self.chunker.overlap]
        
        # Check if there's overlap
        overlap_found = False
        for word in overlap_from_first:
            if word in overlap_from_second:
                overlap_found = True
                break
        
        self.assertTrue(overlap_found, "No overlap found between chunks")
    
    def test_merge_chunks(self):
        """Test merging chunks."""
        # First create chunks
        chunks = self.chunker.chunk_text(
            text=self.test_text,
            source_id="test-123",
            source_title="Test Document"
        )
        
        # Get initial chunk count
        original_count = len(chunks)
        
        # Merge chunks with larger max size
        merged = self.chunker.merge_chunks(chunks, max_size=200)
        
        # Should have fewer chunks after merging
        self.assertLess(len(merged), original_count)
        
        # Each merged chunk should contain multiple original chunks
        for merged_chunk in merged:
            # Merged chunks should be larger than original chunks
            if original_count > 1:
                self.assertGreater(merged_chunk.metadata.tokens, 100)
            
            # Metadata should be set correctly
            self.assertEqual(merged_chunk.metadata.total_chunks, len(merged))
            self.assertEqual(merged_chunk.metadata.chunk_type, ChunkType.FIXED_SIZE)


class TestParagraphChunker(unittest.TestCase):
    """Test cases for the ParagraphChunker class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.chunker = ParagraphChunker(
            max_chunk_size=200,
            min_chunk_size=50
        )
        
        # Test text with paragraphs
        self.test_text = """
First paragraph with some content.
Some more text for the first paragraph.

Second paragraph that contains different information.
This paragraph continues with additional details.

A third paragraph that will be included.
This is still part of the third paragraph.

Fourth paragraph to round out the text.
A bit more content for the fourth paragraph.
"""
    
    def test_initial_configuration(self):
        """Test that the chunker is initialized with correct parameters."""
        self.assertEqual(self.chunker.max_chunk_size, 200)
        self.assertEqual(self.chunker.min_chunk_size, 50)
    
    def test_chunk_text_preserves_paragraphs(self):
        """Test that paragraphs are preserved in chunks."""
        chunks = self.chunker.chunk_text(
            text=self.test_text,
            source_id="test-123",
            source_title="Test Document"
        )
        
        # We should get some chunks
        self.assertGreater(len(chunks), 0)
        
        # Check for paragraph integrity
        for chunk in chunks:
            # Count paragraphs in chunk
            paragraphs = re.split(r'\n\s*\n', chunk.content)
            paragraphs = [p.strip() for p in paragraphs if p.strip()]
            
            # Each chunk should contain at least one paragraph
            self.assertGreaterEqual(len(paragraphs), 1)
            
            # Paragraphs should be intact (not split mid-paragraph)
            for para in paragraphs:
                # Each paragraph from the original text should be fully contained
                # in at least one chunk (this is a simplification for the test)
                if "First paragraph" in para:
                    self.assertIn("more text for the first", para)
                elif "Second paragraph" in para:
                    self.assertIn("additional details", para)
                elif "A third paragraph" in para:
                    self.assertIn("still part of the third", para)
                elif "Fourth paragraph" in para:
                    self.assertIn("more content for the fourth", para)
    
    def test_large_paragraph_handling(self):
        """Test handling of paragraphs that exceed max chunk size."""
        # Create text with a very large paragraph
        large_para_text = "Start of a very large paragraph. " + "More content. " * 100 + "End of paragraph."
        
        chunks = self.chunker.chunk_text(
            text=large_para_text,
            source_id="test-123",
            source_title="Test Document"
        )
        
        # Should split into multiple chunks
        self.assertGreater(len(chunks), 1)
        
        # Each chunk should be within size limits
        for chunk in chunks:
            self.assertLessEqual(chunk.metadata.tokens, self.chunker.max_chunk_size * 1.1)  # Allow small margin
    
    def test_merge_chunks(self):
        """Test merging paragraph chunks."""
        # Create multiple small paragraphs
        small_paras = "\n\n".join([f"Paragraph {i}. Some text here." for i in range(10)])
        
        # Chunk with small max size to ensure multiple chunks
        small_chunker = ParagraphChunker(max_chunk_size=50)
        chunks = small_chunker.chunk_text(
            text=small_paras,
            source_id="test-123",
            source_title="Test Document"
        )
        
        # Original chunk count
        original_count = len(chunks)
        
        # Merge with larger max size
        merged = small_chunker.merge_chunks(chunks, max_size=200)
        
        # Should have fewer chunks after merging
        self.assertLess(len(merged), original_count)
        
        # Verify merged chunks
        for chunk in merged:
            self.assertEqual(chunk.metadata.chunk_type, ChunkType.PARAGRAPH)
            
            # Count paragraphs in merged chunk
            paragraphs = re.split(r'\n\s*\n', chunk.content)
            paragraphs = [p.strip() for p in paragraphs if p.strip()]
            
            # Merged chunks should contain multiple paragraphs (unless original had very few)
            if original_count > 1:
                self.assertGreater(len(paragraphs), 1)


class TestHybridChunker(unittest.TestCase):
    """Test cases for the HybridChunker class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.chunker = HybridChunker(
            max_chunk_size=200,
            min_chunk_size=50,
            prefer_semantic=True
        )
        
        # Test text with mixed content
        self.test_text = """
# Section 1: Introduction

This is an introduction section with some content.
It includes multiple sentences that discuss the topic.

## Subsection 1.1

This subsection contains more details about the introduction.
It has some specific points to consider.

# Section 2: Methods

The methods section describes the approach used.
There are several important aspects to note:

1. First method implemented
2. Second method considered
3. Third method analyzed

## Subsection 2.1

Additional details about the methods used in the study.
This includes some technical information.

# Section 3: Results

The results section presents the findings of the study.
There were several key outcomes observed.
"""
    
    def test_initial_configuration(self):
        """Test that the chunker is initialized with correct parameters."""
        self.assertEqual(self.chunker.max_chunk_size, 200)
        self.assertEqual(self.chunker.min_chunk_size, 50)
        self.assertTrue(self.chunker.prefer_semantic)
    
    def test_chunk_text_strategy_selection(self):
        """Test that the hybrid chunker selects strategies appropriately."""
        chunks = self.chunker.chunk_text(
            text=self.test_text,
            source_id="test-123",
            source_title="Test Document"
        )
        
        # Should create multiple chunks
        self.assertGreater(len(chunks), 1)
        
        # All chunks should be marked as hybrid type
        for chunk in chunks:
            self.assertEqual(chunk.metadata.chunk_type, ChunkType.HYBRID)
        
        # Check that sections are preserved when possible
        headers_preserved = False
        for chunk in chunks:
            if re.search(r'^# Section \d+:', chunk.content, re.MULTILINE):
                headers_preserved = True
                break
        
        self.assertTrue(headers_preserved, "No section headers preserved in chunks")
    
    def test_fallback_behavior(self):
        """Test that the hybrid chunker falls back to simpler strategies when needed."""
        # Create a large text that will force fallbacks
        large_text = (
            "# Large Document\n\n" + 
            "\n\n".join([f"Paragraph {i}. " + "Content. " * 100 for i in range(10)])
        )
        
        # Set a small max size to force fallbacks
        small_chunker = HybridChunker(max_chunk_size=100)
        
        chunks = small_chunker.chunk_text(
            text=large_text,
            source_id="test-123",
            source_title="Test Document"
        )
        
        # Should create multiple chunks
        self.assertGreater(len(chunks), 5)  # Should be many chunks with this small size
        
        # All chunks should be within the max size limit
        for chunk in chunks:
            self.assertLessEqual(chunk.metadata.tokens, small_chunker.max_chunk_size * 1.1)  # Allow small margin
    
    def test_merge_chunks_across_strategies(self):
        """Test that the hybrid chunker can merge chunks from different strategies."""
        # Create chunks of different types
        from src.chunking import SemanticChunker
        
        semantic_chunker = SemanticChunker()
        fixed_chunker = FixedSizeChunker()
        paragraph_chunker = ParagraphChunker()
        
        # Create chunks of different types
        semantic_chunks = semantic_chunker.chunk_text(
            text="# Semantic Test\n\nThis is semantic content.\n\n## Subsection\n\nMore content.",
            source_id="test-sem",
            source_title="Semantic Doc"
        )
        
        fixed_chunks = fixed_chunker.chunk_text(
            text="Fixed size content. " * 20,
            source_id="test-fix",
            source_title="Fixed Doc"
        )
        
        para_chunks = paragraph_chunker.chunk_text(
            text="Paragraph 1.\n\nParagraph 2.\n\nParagraph 3.",
            source_id="test-par",
            source_title="Para Doc"
        )
        
        # Combine all chunks
        all_chunks = semantic_chunks + fixed_chunks + para_chunks
        
        # Merge with hybrid chunker
        merged = self.chunker.merge_chunks(all_chunks, max_size=300)
        
        # Should have fewer chunks than original
        self.assertLess(len(merged), len(all_chunks))
        
        # All merged chunks should be hybrid type
        for chunk in merged:
            self.assertEqual(chunk.metadata.chunk_type, ChunkType.HYBRID) 