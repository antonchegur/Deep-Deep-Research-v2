"""
Large-scale validation tests for the chunking algorithms.

This module contains integration tests that validate the chunking system
with large datasets, ensuring it can handle real-world research volumes.
"""

import unittest
import time
import asyncio
import logging
import os
from pathlib import Path
import tempfile
import json
from typing import List, Dict, Any, Tuple

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.chunking import (
    Chunk, ChunkMetadata, ChunkType,
    SemanticChunker, FixedSizeChunker, ParagraphChunker, HybridChunker,
    ContentPrioritizer, PrioritizedChunker,
    ChunkStore, MetadataManager,
    OptimizedChunkingStrategy, ChunkingOptimizer
)


def generate_large_text(size_kb: int) -> str:
    """
    Generate a large text document of approximately size_kb kilobytes.
    
    Args:
        size_kb: Target size in kilobytes
        
    Returns:
        A large text string
    """
    # Sample paragraphs for realistic-looking content
    paragraphs = [
        "Machine learning is a field of study that gives computers the ability to learn "
        "without being explicitly programmed. It is seen as a subset of artificial intelligence. "
        "Machine learning focuses on the development of computer programs that can access "
        "data and use it to learn for themselves.",
        
        "Natural language processing (NLP) is a field of computer science, artificial intelligence, "
        "and linguistics concerned with the interactions between computers and human languages. "
        "It involves the processing of natural language data to enable computers to understand, "
        "interpret, and generate human language in a way that is valuable.",
        
        "Deep learning is part of a broader family of machine learning methods based on "
        "artificial neural networks with representation learning. Learning can be supervised, "
        "semi-supervised or unsupervised. Deep learning architectures such as deep neural networks, "
        "deep belief networks, recurrent neural networks and convolutional neural networks have been "
        "applied to fields including computer vision, speech recognition, natural language processing, "
        "audio recognition, social network filtering, machine translation, bioinformatics, drug design, "
        "medical image analysis, material inspection and board game programs, where they have produced "
        "results comparable to and in some cases surpassing human expert performance.",
        
        "Reinforcement learning is an area of machine learning concerned with how software agents "
        "ought to take actions in an environment in order to maximize the notion of cumulative reward. "
        "Reinforcement learning is one of three basic machine learning paradigms, alongside supervised "
        "learning and unsupervised learning.",
        
        "Data mining is the process of discovering patterns in large data sets involving methods "
        "at the intersection of machine learning, statistics, and database systems. It is an essential "
        "process where intelligent methods are applied to extract data patterns."
    ]
    
    # Estimate number of repetitions needed to reach target size
    # Average paragraph length in bytes
    avg_para_bytes = sum(len(p.encode('utf-8')) for p in paragraphs) / len(paragraphs)
    
    # Number of paragraphs needed to reach target size
    target_bytes = size_kb * 1024
    num_paragraphs = int(target_bytes / avg_para_bytes) + 1
    
    # Generate text by repeating paragraphs
    text_parts = []
    for i in range(num_paragraphs):
        text_parts.append(paragraphs[i % len(paragraphs)])
        
        # Add some headings for structure
        if i % 20 == 0:
            text_parts.append(f"\n\n## Section {i // 20 + 1}\n\n")
        elif i % 5 == 0:
            text_parts.append("\n\n")
    
    full_text = "\n".join(text_parts)
    actual_kb = len(full_text.encode('utf-8')) / 1024
    logger.info(f"Generated text of {actual_kb:.2f} KB")
    
    return full_text


def generate_dataset(num_docs: int, size_kb_range: Tuple[int, int]) -> List[Tuple[str, str, str]]:
    """
    Generate a test dataset of multiple documents.
    
    Args:
        num_docs: Number of documents to generate
        size_kb_range: Range of sizes (min, max) in KB
        
    Returns:
        List of (text, source_id, source_title) tuples
    """
    import random
    
    dataset = []
    total_size_kb = 0
    
    for i in range(num_docs):
        # Random size within range
        size_kb = random.randint(size_kb_range[0], size_kb_range[1])
        
        # Generate document
        text = generate_large_text(size_kb)
        source_id = f"doc-{i+1}"
        source_title = f"Research Document {i+1}"
        
        dataset.append((text, source_id, source_title))
        
        total_size_kb += len(text.encode('utf-8')) / 1024
    
    logger.info(f"Generated dataset with {num_docs} documents, total size: {total_size_kb:.2f} KB")
    return dataset


class TestLargeDatasetChunking(unittest.TestCase):
    """Test suite for validating chunking with large datasets."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are used for all tests."""
        # Generate moderate-sized dataset (approx. 10 MB total)
        cls.medium_dataset = generate_dataset(20, (500, 750))
        
        # Performance metrics will be stored here
        cls.metrics = {}
    
    def setUp(self):
        """Set up before each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up after each test."""
        self.temp_dir.cleanup()
    
    def test_chunking_strategies_with_medium_dataset(self):
        """Test all chunking strategies with medium-sized dataset."""
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=150),
            "paragraph": ParagraphChunker(max_chunk_size=150),
            "semantic": SemanticChunker(max_chunk_size=150),
            "hybrid": HybridChunker(max_chunk_size=150)
        }
        
        results = {}
        
        for name, strategy in strategies.items():
            logger.info(f"\nTesting {name} strategy with medium dataset...")
            
            # Process documents and measure time
            start_time = time.time()
            all_chunks = []
            
            for text, source_id, source_title in self.medium_dataset:
                chunks = strategy.chunk_text(text, source_id, source_title)
                all_chunks.extend(chunks)
            
            elapsed_time = time.time() - start_time
            
            # Calculate metrics
            total_chunks = len(all_chunks)
            total_docs = len(self.medium_dataset)
            total_tokens = sum(chunk.metadata.tokens or 0 for chunk in chunks)
            avg_chunk_size = total_tokens / total_chunks if total_chunks else 0
            chunks_per_second = total_chunks / elapsed_time if elapsed_time > 0 else 0
            
            # Record results
            results[name] = {
                "time": elapsed_time,
                "total_chunks": total_chunks,
                "chunks_per_doc": total_chunks / total_docs,
                "chunks_per_second": chunks_per_second,
                "avg_chunk_size": avg_chunk_size
            }
            
            logger.info(f"  Processed {total_docs} docs into {total_chunks} chunks in {elapsed_time:.2f}s")
            logger.info(f"  Chunks per second: {chunks_per_second:.2f}")
            logger.info(f"  Average chunk size: {avg_chunk_size:.2f} tokens")
        
        # Save metrics for class-level access
        TestLargeDatasetChunking.metrics["medium"] = results
        
        # Write detailed results to JSON file
        with open(self.output_dir / "medium_dataset_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Detailed results saved to {self.output_dir}/medium_dataset_results.json")
        
        # Basic correctness checks
        for name, metrics in results.items():
            self.assertGreater(metrics["total_chunks"], 0, f"{name} strategy produced no chunks")
            self.assertGreater(metrics["chunks_per_second"], 0, f"{name} strategy had invalid processing rate")
    
    @unittest.skipIf(os.environ.get("SKIP_LARGE_TESTS"), "Skipping large dataset test")
    def test_chunking_with_large_dataset(self):
        """Test optimized chunking with a large dataset (100+ MB)."""
        # Only run if not skipped
        if os.environ.get("SKIP_LARGE_TESTS"):
            return
        
        # Generate a large dataset (approx. 100 MB total)
        logger.info("Generating large dataset (100+ MB)...")
        large_dataset = generate_dataset(50, (2000, 2500))
        
        # Use the hybrid strategy with optimization
        base_strategy = HybridChunker(max_chunk_size=150)
        optimizer = ChunkingOptimizer(max_workers=8)
        optimized_strategy = OptimizedChunkingStrategy(
            base_strategy=base_strategy,
            optimizer=optimizer,
            use_cache=True,
            use_parallel=True
        )
        
        # Process with optimized strategy
        logger.info("Processing large dataset with optimized strategy...")
        start_time = time.time()
        
        # Create event loop and run parallel processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            all_chunks_lists = loop.run_until_complete(
                optimized_strategy.chunk_texts(large_dataset)
            )
            # Flatten the lists
            all_chunks = [chunk for chunks in all_chunks_lists for chunk in chunks]
        finally:
            loop.close()
        
        elapsed_time = time.time() - start_time
        
        # Calculate metrics
        total_chunks = len(all_chunks)
        chunks_per_second = total_chunks / elapsed_time if elapsed_time > 0 else 0
        docs_per_second = len(large_dataset) / elapsed_time if elapsed_time > 0 else 0
        
        logger.info(f"Processed {len(large_dataset)} documents into {total_chunks} chunks")
        logger.info(f"Total processing time: {elapsed_time:.2f} seconds")
        logger.info(f"Chunks per second: {chunks_per_second:.2f}")
        logger.info(f"Documents per second: {docs_per_second:.2f}")
        
        # Test the chunking results
        self.assertGreater(total_chunks, 0, "No chunks produced")
        self.assertGreater(chunks_per_second, 0, "Invalid processing rate")
        
        # Check optimized processing is reasonably fast (threshold can be adjusted)
        self.assertGreater(docs_per_second, 0.1, "Processing too slow")
        
        # Save to metrics
        TestLargeDatasetChunking.metrics["large"] = {
            "optimized": {
                "time": elapsed_time,
                "total_chunks": total_chunks,
                "chunks_per_second": chunks_per_second,
                "docs_per_second": docs_per_second
            }
        }
        
        # Save metrics to file
        with open(self.output_dir / "large_dataset_results.json", "w") as f:
            json.dump(TestLargeDatasetChunking.metrics["large"], f, indent=2)
    
    def test_chunking_with_content_prioritization(self):
        """Test content prioritization with a varied dataset."""
        # Use a smaller subset for faster testing
        dataset = self.medium_dataset[:5]
        
        # Create prioritized chunker
        prioritizer = ContentPrioritizer()
        base_chunker = HybridChunker(max_chunk_size=150)
        prioritized_chunker = PrioritizedChunker(
            base_strategy=base_chunker,
            prioritizer=prioritizer
        )
        
        # Process with the prioritized chunker
        start_time = time.time()
        prioritized_chunks = []
        
        for text, source_id, source_title in dataset:
            chunks = prioritized_chunker.chunk_text(text, source_id, source_title)
            prioritized_chunks.extend(chunks)
        
        prioritized_time = time.time() - start_time
        
        # Now process with the base chunker for comparison
        start_time = time.time()
        base_chunks = []
        
        for text, source_id, source_title in dataset:
            chunks = base_chunker.chunk_text(text, source_id, source_title)
            base_chunks.extend(chunks)
        
        base_time = time.time() - start_time
        
        # Log metrics
        logger.info(f"Base chunking: {len(base_chunks)} chunks in {base_time:.2f}s")
        logger.info(f"Prioritized chunking: {len(prioritized_chunks)} chunks in {prioritized_time:.2f}s")
        
        # Verify that high-priority content is preserved
        high_priority_chunks = [
            chunk for chunk in prioritized_chunks
            if chunk.metadata.custom_metadata.get("priority_score", 0) >= 3
        ]
        
        logger.info(f"High-priority chunks: {len(high_priority_chunks)}")
        
        # Basic assertions
        self.assertGreater(len(prioritized_chunks), 0, "No chunks produced with prioritization")
        self.assertGreater(len(high_priority_chunks), 0, "No high-priority chunks identified")
    
    def test_chunking_with_metadata_storage(self):
        """Test storing and retrieving chunks with metadata in a ChunkStore."""
        # Use a smaller dataset for this test
        dataset = self.medium_dataset[:3]
        
        # Create a chunk store
        store_path = self.output_dir / "chunk_store"
        metadata_mgr = MetadataManager(store_path)
        chunk_store = ChunkStore(store_path, metadata_mgr)
        
        # Use hybrid chunker
        chunker = HybridChunker(max_chunk_size=150)
        
        # Process and store chunks
        for text, source_id, source_title in dataset:
            chunks = chunker.chunk_text(text, source_id, source_title)
            # Add to store
            chunk_collection = ChunkCollection(
                source_id=source_id,
                chunks=chunks
            )
            chunk_store.store_chunk_collection(chunk_collection)
        
        # Test retrieval
        all_collections = chunk_store.list_collections()
        self.assertEqual(len(all_collections), len(dataset), 
                         "Number of stored collections doesn't match input dataset")
        
        # Get a specific collection
        test_source_id = dataset[0][1]
        collection = chunk_store.get_chunk_collection(test_source_id)
        
        self.assertIsNotNone(collection, f"Failed to retrieve collection for {test_source_id}")
        self.assertGreater(len(collection.chunks), 0, "Retrieved collection has no chunks")
        
        # Search by content
        search_results = chunk_store.search_chunks("machine learning")
        self.assertGreater(len(search_results), 0, "Search returned no results")


if __name__ == '__main__':
    unittest.main() 