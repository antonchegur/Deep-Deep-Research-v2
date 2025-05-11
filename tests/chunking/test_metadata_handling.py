"""
Tests for the metadata handling system.

This file contains unit tests for the metadata management and storage functionality.
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime

from src.chunking.base import Chunk, ChunkMetadata, ChunkType
from src.chunking.metadata_handling import (
    SourceMetadata, ChunkCollection, MetadataManager, ChunkStore
)


class TestSourceMetadata(unittest.TestCase):
    """Test cases for SourceMetadata class."""
    
    def test_creation(self):
        """Test creating a SourceMetadata object."""
        metadata = SourceMetadata(
            id="doc-123",
            title="Test Document",
            author="Test Author",
            publication_date="2023-01-01",
            url="https://example.com/doc",
            type="research",
            publication="Test Journal",
            language="en"
        )
        
        self.assertEqual(metadata.id, "doc-123")
        self.assertEqual(metadata.title, "Test Document")
        self.assertEqual(metadata.author, "Test Author")
        self.assertEqual(metadata.type, "research")
        self.assertEqual(metadata.language, "en")


class TestChunkCollection(unittest.TestCase):
    """Test cases for ChunkCollection class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.source = SourceMetadata(
            id="doc-123",
            title="Test Document"
        )
        
        self.chunk = Chunk(
            id="chunk-1",
            content="Test content",
            metadata=ChunkMetadata(
                source_id="doc-123",
                source_title="Test Document",
                chunk_index=0,
                total_chunks=1,
                chunk_type=ChunkType.SEMANTIC
            )
        )
    
    def test_creation(self):
        """Test creating a ChunkCollection."""
        collection = ChunkCollection(
            id="col-123",
            source=self.source,
            chunks=[self.chunk]
        )
        
        self.assertEqual(collection.id, "col-123")
        self.assertEqual(collection.source.id, "doc-123")
        self.assertEqual(len(collection.chunks), 1)
        self.assertEqual(collection.chunks[0].id, "chunk-1")


class TestMetadataManager(unittest.TestCase):
    """Test cases for MetadataManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = MetadataManager()
        self.source = self.manager.create_source_metadata(
            source_id="doc-123",
            title="Test Document",
            author="Test Author"
        )
        
        self.chunk = Chunk(
            id="chunk-1",
            content="Test content",
            metadata=ChunkMetadata(
                source_id="doc-123",
                source_title="Test Document",
                chunk_index=0,
                total_chunks=1,
                chunk_type=ChunkType.SEMANTIC
            )
        )
    
    def test_create_source_metadata(self):
        """Test creating source metadata."""
        source = self.manager.create_source_metadata(
            source_id="doc-456",
            title="Another Document",
            author="Another Author",
            type="book"
        )
        
        self.assertEqual(source.id, "doc-456")
        self.assertEqual(source.title, "Another Document")
        self.assertEqual(source.type, "book")
    
    def test_create_collection(self):
        """Test creating a collection."""
        collection = self.manager.create_collection(
            source_metadata=self.source,
            chunks=[self.chunk]
        )
        
        self.assertIn(collection.id, self.manager.collections)
        self.assertEqual(collection.source.id, "doc-123")
        self.assertEqual(len(collection.chunks), 1)
        self.assertIn("chunking_timestamp", collection.processing_info)
    
    def test_add_chunks_to_collection(self):
        """Test adding chunks to a collection."""
        # Create empty collection
        collection = self.manager.create_collection(
            source_metadata=self.source
        )
        
        # Add chunks
        new_chunk = Chunk(
            id="chunk-2",
            content="More content",
            metadata=ChunkMetadata(
                source_id="doc-123",
                source_title="Test Document",
                chunk_index=1,
                total_chunks=2,
                chunk_type=ChunkType.SEMANTIC
            )
        )
        
        updated = self.manager.add_chunks_to_collection(
            collection_id=collection.id,
            chunks=[self.chunk, new_chunk]
        )
        
        self.assertEqual(len(updated.chunks), 2)
        self.assertEqual(updated.processing_info["chunk_count"], 2)
    
    def test_get_collection(self):
        """Test retrieving a collection."""
        collection = self.manager.create_collection(
            source_metadata=self.source,
            chunks=[self.chunk]
        )
        
        retrieved = self.manager.get_collection(collection.id)
        self.assertEqual(retrieved.id, collection.id)
        self.assertEqual(retrieved.source.id, "doc-123")
    
    def test_get_chunk_by_id(self):
        """Test retrieving a chunk by ID."""
        collection = self.manager.create_collection(
            source_metadata=self.source,
            chunks=[self.chunk]
        )
        
        chunk = self.manager.get_chunk_by_id(collection.id, "chunk-1")
        self.assertIsNotNone(chunk)
        self.assertEqual(chunk.id, "chunk-1")
        
        # Test non-existent chunk
        none_chunk = self.manager.get_chunk_by_id(collection.id, "non-existent")
        self.assertIsNone(none_chunk)
    
    def test_update_chunk_metadata(self):
        """Test updating chunk metadata."""
        collection = self.manager.create_collection(
            source_metadata=self.source,
            chunks=[self.chunk]
        )
        
        # Update metadata
        updated = self.manager.update_chunk_metadata(
            collection_id=collection.id,
            chunk_id="chunk-1",
            importance_score=0.9,
            custom_field="custom value"
        )
        
        self.assertEqual(updated.metadata.importance_score, 0.9)
        self.assertEqual(updated.metadata.custom_data["custom_field"], "custom value")
    
    def test_export_collection(self):
        """Test exporting a collection to a dictionary."""
        collection = self.manager.create_collection(
            source_metadata=self.source,
            chunks=[self.chunk]
        )
        
        exported = self.manager.export_collection(collection.id)
        
        self.assertEqual(exported["id"], collection.id)
        self.assertEqual(exported["source"]["id"], "doc-123")
        self.assertEqual(len(exported["chunks"]), 1)
        self.assertEqual(exported["chunks"][0]["id"], "chunk-1")
    
    def test_import_collection(self):
        """Test importing a collection from a dictionary."""
        # First export a collection
        collection = self.manager.create_collection(
            source_metadata=self.source,
            chunks=[self.chunk]
        )
        exported = self.manager.export_collection(collection.id)
        
        # Create a new manager and import
        new_manager = MetadataManager()
        imported = new_manager.import_collection(exported)
        
        self.assertEqual(imported.id, collection.id)
        self.assertEqual(imported.source.id, "doc-123")
        self.assertEqual(len(imported.chunks), 1)
        self.assertEqual(imported.chunks[0].id, "chunk-1")


class TestChunkStore(unittest.TestCase):
    """Test cases for ChunkStore class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = MetadataManager()
        # Create a temporary directory for storage
        self.temp_dir = tempfile.mkdtemp()
        self.store = ChunkStore(
            metadata_manager=self.manager,
            storage_dir=self.temp_dir
        )
        
        # Create source metadata
        self.source = self.manager.create_source_metadata(
            source_id="doc-123",
            title="Test Document"
        )
        
        # Create chunks with different topics
        self.chunks = [
            Chunk(
                id=f"chunk-{i}",
                content=f"Content about {topic}" if i > 0 else "General content.",
                metadata=ChunkMetadata(
                    source_id="doc-123",
                    source_title="Test Document",
                    chunk_index=i,
                    total_chunks=3,
                    chunk_type=ChunkType.SEMANTIC,
                    semantic_topics=[topic] if i > 0 else []
                )
            ) for i, topic in enumerate(["", "machine learning", "natural language processing"])
        ]
        
        # Create a collection
        self.collection = self.manager.create_collection(
            source_metadata=self.source,
            chunks=self.chunks
        )
        
        # Add to store
        self.store.add_collection(self.collection)
    
    def tearDown(self):
        """Clean up temporary files."""
        for file in os.listdir(self.temp_dir):
            if file.endswith('.json'):
                os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def test_add_collection(self):
        """Test adding a collection to the store."""
        self.assertIn("chunk-0", self.store.chunk_index)
        self.assertIn("chunk-1", self.store.chunk_index)
        self.assertIn("chunk-2", self.store.chunk_index)
        
        # Check topic index
        self.assertIn("machine learning", self.store.topic_index)
        self.assertIn("natural language processing", self.store.topic_index)
    
    def test_get_chunk(self):
        """Test retrieving a chunk by ID."""
        chunk = self.store.get_chunk("chunk-1")
        self.assertIsNotNone(chunk)
        self.assertEqual(chunk.id, "chunk-1")
        
        # Test non-existent chunk
        none_chunk = self.store.get_chunk("non-existent")
        self.assertIsNone(none_chunk)
    
    def test_find_similar_chunks(self):
        """Test finding similar chunks by content."""
        # Add a duplicate content chunk
        duplicate_chunk = Chunk(
            id="chunk-dup",
            content="Content about machine learning",
            metadata=ChunkMetadata(
                source_id="doc-123",
                source_title="Test Document",
                chunk_index=3,
                total_chunks=4,
                chunk_type=ChunkType.SEMANTIC,
                semantic_topics=["machine learning"]
            )
        )
        self.manager.add_chunks_to_collection(self.collection.id, [duplicate_chunk])
        
        # Rebuild indices
        self.store.add_collection(self.collection)
        
        # Find similar chunks
        similar = self.store.find_similar_chunks("Content about machine learning")
        self.assertEqual(len(similar), 2)
    
    def test_find_chunks_by_topic(self):
        """Test finding chunks by topic."""
        # Find by exact topic
        ml_chunks = self.store.find_chunks_by_topic("machine learning")
        self.assertEqual(len(ml_chunks), 1)
        self.assertEqual(ml_chunks[0].id, "chunk-1")
        
        # Find by partial topic match
        nlp_chunks = self.store.find_chunks_by_topic("language")
        self.assertEqual(len(nlp_chunks), 1)
        self.assertEqual(nlp_chunks[0].id, "chunk-2")
    
    def test_get_related_chunks(self):
        """Test finding related chunks."""
        related = self.store.get_related_chunks("chunk-1")
        
        # Should find at least one neighbor (chunk-0 or chunk-2)
        self.assertGreater(len(related), 0)
        neighbor_ids = {chunk.id for chunk in related}
        self.assertTrue("chunk-0" in neighbor_ids or "chunk-2" in neighbor_ids)
    
    def test_save_and_load(self):
        """Test saving and loading collections."""
        # Save the collection
        filepath = self.store.save_to_disk(self.collection.id)
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))
        
        # Create a new store
        new_store = ChunkStore()
        
        # Load the collection
        loaded_id = new_store.load_from_disk(filepath)
        self.assertIsNotNone(loaded_id)
        
        # Check the loaded collection
        loaded_collection = new_store.metadata_manager.get_collection(loaded_id)
        self.assertEqual(loaded_collection.source.id, "doc-123")
        self.assertEqual(len(loaded_collection.chunks), 3)  # Original chunks


if __name__ == '__main__':
    unittest.main() 