#!/usr/bin/env python3
"""
Metadata Handling Demo

This script demonstrates the metadata handling capabilities of the chunking system,
showing how to create, store, and retrieve chunks with rich metadata.
"""

import sys
import os
import logging
import json
from pathlib import Path
import tempfile
from datetime import datetime

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.chunking import (
    Chunk, ChunkMetadata, ChunkType, 
    SemanticChunker, ParagraphChunker
)
from src.chunking.metadata_handling import (
    SourceMetadata, ChunkCollection, MetadataManager, ChunkStore
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_collection_summary(collection):
    """Print a summary of a chunk collection."""
    print(f"\n{'-'*20} COLLECTION: {collection.id} {'-'*20}")
    print(f"Source: {collection.source.title} (ID: {collection.source.id})")
    print(f"Author: {collection.source.author}")
    print(f"Created: {collection.created_at}")
    print(f"Chunks: {len(collection.chunks)}")
    
    if collection.processing_info:
        print("\nProcessing Info:")
        for key, value in collection.processing_info.items():
            print(f"  {key}: {value}")
    
    print(f"{'-'*60}")


def print_chunk_details(chunk):
    """Print details about a chunk."""
    print(f"\n{'-'*20} CHUNK: {chunk.id} {'-'*20}")
    print(f"Source: {chunk.metadata.source_title} (ID: {chunk.metadata.source_id})")
    print(f"Position: {chunk.metadata.chunk_index + 1} of {chunk.metadata.total_chunks}")
    print(f"Type: {chunk.metadata.chunk_type.value}")
    print(f"Importance: {chunk.metadata.importance_score:.2f}")
    
    if chunk.metadata.semantic_topics:
        print(f"Topics: {', '.join(chunk.metadata.semantic_topics)}")
    
    if chunk.metadata.custom_data:
        print("\nCustom Data:")
        for key, value in chunk.metadata.custom_data.items():
            print(f"  {key}: {value}")
    
    print("\nContent Preview:")
    preview = chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content
    print(f"  {preview}")
    print(f"{'-'*60}")


def run_demo():
    """Run the metadata handling demo."""
    print("\nMETADATA HANDLING SYSTEM DEMO\n")
    print("This demo showcases the metadata management capabilities of the chunking system.")
    
    # Create a temporary directory for saving collections
    temp_dir = tempfile.mkdtemp()
    print(f"Using temporary directory: {temp_dir}")
    
    # Initialize metadata manager and chunk store
    manager = MetadataManager()
    store = ChunkStore(metadata_manager=manager, storage_dir=temp_dir)
    
    # ===== Processing multiple source documents =====
    print("\n1. Processing Multiple Source Documents")
    print("="*50)
    
    # Sample documents to process
    documents = [
        {
            "id": "doc-1",
            "title": "Advanced Machine Learning Techniques",
            "author": "Jane Smith",
            "publication_date": "2023-05-15",
            "type": "research",
            "content": """
# Advanced Machine Learning Techniques

## Abstract

This paper introduces novel machine learning techniques for natural language processing.
The proposed methods show significant improvements over baseline approaches.

## Introduction

Machine learning has revolutionized many fields of study, particularly natural language processing.
Recent advancements in deep learning have led to remarkable improvements in model performance.

## Methodology

Our approach combines transformer architectures with reinforcement learning to optimize for
specific downstream tasks. The key innovation is a new attention mechanism that prioritizes
semantic relationships between tokens.

## Results

Experiments on benchmark datasets show a 15% improvement over state-of-the-art methods.
Statistical analysis confirms these results are significant (p < 0.01).

## Conclusion

The proposed techniques advance the field of natural language processing and open
new avenues for future research.
"""
        },
        {
            "id": "doc-2",
            "title": "Survey of Semantic Chunking Algorithms",
            "author": "Michael Johnson",
            "publication_date": "2023-06-10",
            "type": "survey",
            "content": """
# Survey of Semantic Chunking Algorithms

## Introduction

This survey examines various approaches to semantic chunking of documents for
natural language processing tasks.

## Traditional Approaches

Fixed-size chunking has been the standard approach for many years, but suffers from
breaking semantic units across chunk boundaries.

## Semantic-aware Approaches

Recent methods prioritize preserving semantic units, using linguistic features
to determine appropriate chunk boundaries.

## Comparative Analysis

Our analysis shows that semantic-aware chunking improves downstream task performance
by 12-18% compared to traditional methods.

## Conclusion

Semantic chunking approaches provide substantial benefits for document processing
and should be considered standard practice for NLP pipelines.
"""
        }
    ]
    
    # Process each document
    collections = []
    for doc in documents:
        print(f"\nProcessing document: {doc['title']}")
        
        # Create source metadata
        source = manager.create_source_metadata(
            source_id=doc["id"],
            title=doc["title"],
            author=doc["author"],
            publication_date=doc["publication_date"],
            type=doc["type"]
        )
        
        # Create chunker
        chunker = SemanticChunker(max_chunk_size=200)
        
        # Chunk the document
        chunks = chunker.chunk_text(
            text=doc["content"],
            source_id=source.id,
            source_title=source.title
        )
        
        print(f"Created {len(chunks)} chunks")
        
        # Add custom metadata to chunks
        for i, chunk in enumerate(chunks):
            # Extract section title if present
            lines = chunk.content.strip().split("\n")
            section_title = None
            for line in lines:
                if line.startswith("## "):
                    section_title = line[3:].strip()
                    break
                elif line.startswith("# "):
                    section_title = line[2:].strip()
                    break
            
            if section_title:
                chunk.metadata.custom_data["section_title"] = section_title
            
            # Add date processed
            chunk.metadata.custom_data["processed_date"] = datetime.now().isoformat()
            
            # Add arbitrary importance based on position (for demo)
            if "Abstract" in chunk.content or "Conclusion" in chunk.content:
                chunk.metadata.importance_score = 0.9
            else:
                chunk.metadata.importance_score = 0.5 + (i * 0.1) % 0.4
        
        # Create a collection
        collection = manager.create_collection(
            source_metadata=source,
            chunks=chunks
        )
        
        # Add processing info
        collection.processing_info.update({
            "chunking_method": "semantic",
            "max_chunk_size": 200,
            "processing_time_ms": 45 + len(chunks) * 12  # Simulated processing time
        })
        
        # Add to store
        store.add_collection(collection)
        collections.append(collection)
        
        # Print collection summary
        print_collection_summary(collection)
    
    # ===== Querying and retrieving chunks =====
    print("\n2. Querying and Retrieving Chunks")
    print("="*50)
    
    # Get a specific chunk
    collection_id = collections[0].id
    chunk_id = collections[0].chunks[1].id if len(collections[0].chunks) > 1 else collections[0].chunks[0].id
    
    print(f"\nRetrieving chunk {chunk_id} from collection {collection_id}")
    chunk = store.get_chunk(chunk_id)
    if chunk:
        print_chunk_details(chunk)
    
    # Find chunks by topic
    print("\nFinding chunks about 'machine learning'")
    ml_chunks = store.find_chunks_by_topic("machine learning")
    print(f"Found {len(ml_chunks)} chunks about machine learning")
    for chunk in ml_chunks:
        print_chunk_details(chunk)
    
    # Find related chunks
    print(f"\nFinding chunks related to {chunk_id}")
    related_chunks = store.get_related_chunks(chunk_id)
    print(f"Found {len(related_chunks)} related chunks")
    for chunk in related_chunks:
        print_chunk_details(chunk)
    
    # ===== Modifying chunk metadata =====
    print("\n3. Modifying Chunk Metadata")
    print("="*50)
    
    print(f"\nUpdating metadata for chunk {chunk_id}")
    original_score = chunk.metadata.importance_score
    updated_chunk = manager.update_chunk_metadata(
        collection_id=collection_id,
        chunk_id=chunk_id,
        importance_score=0.95,
        review_status="verified",
        review_date=datetime.now().isoformat()
    )
    
    print(f"Importance score updated: {original_score:.2f} -> {updated_chunk.metadata.importance_score:.2f}")
    print(f"Added review metadata: {updated_chunk.metadata.custom_data['review_status']}")
    
    # ===== Storing and loading collections =====
    print("\n4. Storing and Loading Collections")
    print("="*50)
    
    # Save the first collection
    print(f"\nSaving collection {collections[0].id} to disk")
    saved_path = store.save_to_disk(collections[0].id)
    print(f"Saved to: {saved_path}")
    
    # Create a new store and load the collection
    print("\nCreating a new store and loading the saved collection")
    new_store = ChunkStore()
    loaded_id = new_store.load_from_disk(saved_path)
    
    print(f"Loaded collection: {loaded_id}")
    loaded_collection = new_store.metadata_manager.get_collection(loaded_id)
    print_collection_summary(loaded_collection)
    
    # Check that all chunks were loaded
    print(f"Original chunks: {len(collections[0].chunks)}, Loaded chunks: {len(loaded_collection.chunks)}")
    
    # Clean up temporary directory
    print("\nCleaning up temporary files...")
    os.remove(saved_path)
    os.rmdir(temp_dir)
    
    print("\nDemonstration complete!")


if __name__ == "__main__":
    run_demo() 