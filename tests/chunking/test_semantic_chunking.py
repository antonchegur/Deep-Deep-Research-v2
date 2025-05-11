"""
Tests for the semantic chunking module.

This file contains unit tests for the SemanticChunker class and related functionality.
"""

import unittest
from unittest import mock
import re

from src.chunking.base import Chunk, ChunkMetadata, ChunkType
from src.chunking.semantic_chunking import SemanticChunker


class TestSemanticChunker(unittest.TestCase):
    """Test cases for the SemanticChunker class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.chunker = SemanticChunker(
            min_chunk_size=50,
            max_chunk_size=300,
            overlap_strategy="semantic"
        )
        
        # Test text with clear semantic boundaries
        self.test_text = """
# Introduction

This is a sample research paper for testing semantic chunking. The paper discusses
important topics related to semantic analysis and chunking algorithms.

## Background

Chunking algorithms are essential for processing large volumes of text data.
They help in breaking down text into manageable units while preserving context.

## Methodology

In this study, we used a combination of statistical and rule-based approaches.
The methodology consisted of three main steps:

1. Data collection from multiple sources
2. Preprocessing of text data
3. Application of semantic boundaries detection

## Results

Our results show significant improvement in chunking quality.
The algorithm achieved 85% accuracy in maintaining semantic coherence.

In conclusion, semantic chunking provides better results than traditional
fixed-size approaches for research text processing.
"""

    def test_initial_configuration(self):
        """Test that the chunker is initialized with correct parameters."""
        self.assertEqual(self.chunker.min_chunk_size, 50)
        self.assertEqual(self.chunker.max_chunk_size, 300)
        self.assertEqual(self.chunker.overlap_strategy, "semantic")
        self.assertEqual(self.chunker.semantic_threshold, 0.7)
    
    def test_identify_semantic_boundaries(self):
        """Test identification of semantic boundaries in text."""
        boundaries = self.chunker._identify_semantic_boundaries(self.test_text)
        
        # There should be multiple boundaries (at least one for each section header)
        self.assertGreater(len(boundaries), 3)
        
        # Check if some of the section headers were detected
        intro_idx = self.test_text.find("# Introduction")
        background_idx = self.test_text.find("## Background")
        
        self.assertIn(intro_idx, boundaries)
        self.assertIn(background_idx, boundaries)
    
    def test_split_into_semantic_units(self):
        """Test splitting text into semantic units."""
        # Simplified test with manually specified boundaries
        test_text = "First unit. Second unit. Third unit."
        boundaries = [0, 12, 25, 37]
        
        units = self.chunker._split_into_semantic_units(test_text, boundaries)
        
        self.assertEqual(len(units), 3)
        self.assertEqual(units[0], "First unit.")
        self.assertEqual(units[1], "Second unit.")
        self.assertEqual(units[2], "Third unit.")
    
    def test_extract_topics(self):
        """Test extraction of topics from text."""
        # Test with a section from our test text
        section = """
## Methodology

In this study, we used a combination of statistical and rule-based approaches.
The methodology consisted of three main steps:

1. Data collection from multiple sources
2. Preprocessing of text data
3. Application of semantic boundaries detection
"""
        
        topics = self.chunker._extract_topics(section)
        
        # Should extract "methodology" from the header
        self.assertIn("methodology", topics)
        
        # Should detect frequent terms
        if "statistical" not in topics and "data" not in topics:
            self.fail("Expected topics like 'statistical' or 'data' were not extracted")
    
    def test_chunk_text_basic_functionality(self):
        """Test basic chunking functionality."""
        chunks = self.chunker.chunk_text(
            text=self.test_text,
            source_id="test-123",
            source_title="Test Document"
        )
        
        # We should get multiple chunks due to semantic boundaries
        self.assertGreater(len(chunks), 1)
        
        # Verify all chunks have been properly initialized
        for i, chunk in enumerate(chunks):
            self.assertIsInstance(chunk, Chunk)
            self.assertTrue(chunk.id.startswith("test-123_"))
            self.assertEqual(chunk.metadata.source_id, "test-123")
            self.assertEqual(chunk.metadata.source_title, "Test Document")
            self.assertEqual(chunk.metadata.chunk_index, i)
            self.assertEqual(chunk.metadata.total_chunks, len(chunks))
            self.assertEqual(chunk.metadata.chunk_type, ChunkType.SEMANTIC)
            
            # Check that we have some content
            self.assertGreater(len(chunk.content), 0)
            
            # Verify that token count was estimated
            self.assertGreater(chunk.metadata.tokens, 0)
            
            # Each chunk should have semantic topics extracted
            self.assertGreater(len(chunk.metadata.semantic_topics), 0)
    
    def test_semantic_chunking_preserves_headers(self):
        """Test that semantic chunking properly handles and preserves headers."""
        chunks = self.chunker.chunk_text(
            text=self.test_text,
            source_id="test-123",
            source_title="Test Document"
        )
        
        # At least one chunk should contain a header
        header_found = False
        for chunk in chunks:
            if re.search(r'^#+ ', chunk.content, re.MULTILINE):
                header_found = True
                break
        
        self.assertTrue(header_found, "No chunk contains a header")
    
    def test_chunk_importance_scoring(self):
        """Test that chunks receive appropriate importance scores."""
        chunks = self.chunker.chunk_text(
            text=self.test_text,
            source_id="test-123",
            source_title="Test Document"
        )
        
        # First and last chunks should have higher importance (intro/conclusion)
        self.assertGreater(chunks[0].metadata.importance_score, 0.5)
        self.assertGreater(chunks[-1].metadata.importance_score, 0.5)
        
        # At least one chunk with a section header should have higher importance
        header_chunk_found = False
        for chunk in chunks:
            if (re.search(r'^#+ ', chunk.content, re.MULTILINE) and
                chunk.metadata.importance_score > 0.6):
                header_chunk_found = True
                break
        
        self.assertTrue(header_chunk_found, "No chunk with header has higher importance")
    
    def test_overlap_between_chunks(self):
        """Test that chunks have appropriate overlap when specified."""
        # Create chunker with fixed overlap strategy for more deterministic testing
        chunker = SemanticChunker(
            min_chunk_size=50,
            max_chunk_size=300,
            overlap_strategy="fixed"
        )
        
        # Use a simpler text that will definitely generate multiple chunks
        simple_text = "Sentence one. " * 100
        
        chunks = chunker.chunk_text(
            text=simple_text,
            source_id="test-123",
            source_title="Test Document",
            overlap=50  # Explicit overlap of 50 tokens
        )
        
        # We need at least 2 chunks to test overlap
        self.assertGreater(len(chunks), 1)
        
        # Check for overlap between consecutive chunks
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            curr_chunk = chunks[i]
            
            # Split into words for easier comparison
            prev_words = prev_chunk.content.split()
            curr_words = curr_chunk.content.split()
            
            # Get the last 10 words of the previous chunk (less than our overlap)
            last_words = prev_words[-10:]
            
            # Check if at least some of these words appear at the start of the current chunk
            overlap_found = False
            for word in last_words:
                if word in " ".join(curr_words[:20]):  # Check first 20 words
                    overlap_found = True
                    break
            
            self.assertTrue(overlap_found, f"No overlap found between chunks {i-1} and {i}")
    
    def test_merge_chunks(self):
        """Test merging chunks functionality."""
        # Create sample chunks to merge
        chunks = []
        for i in range(5):
            content = f"This is chunk {i+1} content."
            metadata = ChunkMetadata(
                source_id="test-123",
                source_title="Test Document",
                chunk_index=i,
                total_chunks=5,
                chunk_type=ChunkType.SEMANTIC,
                tokens=10,  # Small token count for testing
                characters=len(content),
                semantic_topics=[f"topic{i+1}"]
            )
            chunk = Chunk(
                id=f"test-123_{i}",
                content=content,
                metadata=metadata
            )
            chunks.append(chunk)
        
        # Merge chunks with a max size that should result in two merged chunks
        merged = self.chunker.merge_chunks(chunks, max_size=30)
        
        # Should result in 2 merged chunks
        self.assertEqual(len(merged), 2)
        
        # First merged chunk should contain the content of multiple original chunks
        self.assertIn("chunk 1", merged[0].content)
        self.assertIn("chunk 2", merged[0].content)
        
        # Should correctly set metadata
        self.assertEqual(merged[0].metadata.total_chunks, 2)
        self.assertEqual(merged[1].metadata.total_chunks, 2)
        
        # Topics should be combined
        self.assertGreater(len(merged[0].metadata.semantic_topics), 1) 