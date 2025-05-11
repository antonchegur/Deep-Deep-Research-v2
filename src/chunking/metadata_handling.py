"""
Metadata handling system for chunked content.

This module provides advanced metadata management for chunks, including
generation, storage, linking, and retrieval capabilities.
"""

import json
import uuid
import hashlib
import time
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from datetime import datetime
import logging

from .base import Chunk, ChunkMetadata, ChunkType

logger = logging.getLogger(__name__)


@dataclass
class SourceMetadata:
    """Metadata about the source document."""
    id: str                          # Unique identifier for the source
    title: str                       # Title of the source
    author: Optional[str] = None     # Author of the source
    publication_date: Optional[str] = None  # Publication date
    url: Optional[str] = None        # Source URL if applicable
    type: Optional[str] = None       # Document type (e.g., research, book, article)
    publication: Optional[str] = None  # Publication name
    language: str = "en"             # Source language
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    custom_data: Dict[str, Any] = field(default_factory=dict)  # Custom metadata


@dataclass
class ChunkCollection:
    """A collection of chunks with associated metadata."""
    id: str                          # Collection identifier
    source: SourceMetadata           # Metadata about the source
    chunks: List[Chunk]              # List of chunks in the collection
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    processing_info: Dict[str, Any] = field(default_factory=dict)  # Processing information
    custom_data: Dict[str, Any] = field(default_factory=dict)  # Custom metadata


class MetadataManager:
    """
    Manages metadata for chunks and chunk collections.
    
    This class provides functionality for generating, updating, and retrieving
    metadata for chunks and their source documents.
    """
    
    def __init__(self):
        """Initialize the metadata manager."""
        self.collections: Dict[str, ChunkCollection] = {}
    
    def create_source_metadata(self, 
                              source_id: str,
                              title: str,
                              **kwargs) -> SourceMetadata:
        """
        Create metadata for a source document.
        
        Args:
            source_id: Unique identifier for the source
            title: Title of the source document
            **kwargs: Additional metadata fields
            
        Returns:
            SourceMetadata object
        """
        return SourceMetadata(
            id=source_id,
            title=title,
            **kwargs
        )
    
    def create_collection(self,
                        source_metadata: SourceMetadata,
                        chunks: Optional[List[Chunk]] = None) -> ChunkCollection:
        """
        Create a new chunk collection.
        
        Args:
            source_metadata: Metadata about the source document
            chunks: Initial list of chunks (optional)
            
        Returns:
            ChunkCollection object
        """
        collection_id = f"col_{source_metadata.id}_{uuid.uuid4().hex[:8]}"
        collection = ChunkCollection(
            id=collection_id,
            source=source_metadata,
            chunks=chunks or [],
            processing_info={
                "chunking_timestamp": datetime.now().isoformat(),
                "chunk_count": len(chunks) if chunks else 0
            }
        )
        
        # Store the collection
        self.collections[collection_id] = collection
        
        return collection
    
    def add_chunks_to_collection(self,
                               collection_id: str,
                               chunks: List[Chunk]) -> ChunkCollection:
        """
        Add chunks to an existing collection.
        
        Args:
            collection_id: ID of the collection to update
            chunks: Chunks to add
            
        Returns:
            Updated ChunkCollection
            
        Raises:
            KeyError: If the collection is not found
        """
        if collection_id not in self.collections:
            raise KeyError(f"Collection {collection_id} not found")
        
        collection = self.collections[collection_id]
        
        # Check for duplicate chunk IDs
        existing_ids = {chunk.id for chunk in collection.chunks}
        
        # Add only non-duplicate chunks
        for chunk in chunks:
            if chunk.id not in existing_ids:
                collection.chunks.append(chunk)
                existing_ids.add(chunk.id)
        
        # Update processing info
        collection.processing_info.update({
            "last_updated": datetime.now().isoformat(),
            "chunk_count": len(collection.chunks)
        })
        
        return collection
    
    def get_collection(self, collection_id: str) -> ChunkCollection:
        """
        Retrieve a chunk collection by ID.
        
        Args:
            collection_id: ID of the collection to retrieve
            
        Returns:
            ChunkCollection object
            
        Raises:
            KeyError: If the collection is not found
        """
        if collection_id not in self.collections:
            raise KeyError(f"Collection {collection_id} not found")
        
        return self.collections[collection_id]
    
    def get_chunk_by_id(self, collection_id: str, chunk_id: str) -> Optional[Chunk]:
        """
        Retrieve a specific chunk from a collection.
        
        Args:
            collection_id: ID of the collection
            chunk_id: ID of the chunk to retrieve
            
        Returns:
            Chunk object if found, None otherwise
        """
        try:
            collection = self.get_collection(collection_id)
            for chunk in collection.chunks:
                if chunk.id == chunk_id:
                    return chunk
        except KeyError:
            pass
        
        return None
    
    def update_chunk_metadata(self, 
                             collection_id: str, 
                             chunk_id: str,
                             **metadata_updates) -> Optional[Chunk]:
        """
        Update metadata for a specific chunk.
        
        Args:
            collection_id: ID of the collection
            chunk_id: ID of the chunk to update
            **metadata_updates: Metadata fields to update
            
        Returns:
            Updated Chunk object if found, None otherwise
        """
        chunk = self.get_chunk_by_id(collection_id, chunk_id)
        if not chunk:
            return None
        
        # Update chunk metadata
        for key, value in metadata_updates.items():
            if hasattr(chunk.metadata, key):
                setattr(chunk.metadata, key, value)
            else:
                # If not a direct attribute, add to custom_data
                chunk.metadata.custom_data[key] = value
        
        return chunk
    
    def export_collection(self, collection_id: str) -> Dict[str, Any]:
        """
        Export a collection as a dictionary for serialization.
        
        Args:
            collection_id: ID of the collection to export
            
        Returns:
            Dictionary representation of the collection
            
        Raises:
            KeyError: If the collection is not found
        """
        collection = self.get_collection(collection_id)
        
        # Convert dataclasses to dictionaries
        result = {
            "id": collection.id,
            "source": asdict(collection.source),
            "chunks": [
                {
                    "id": chunk.id,
                    "content": chunk.content,
                    "metadata": asdict(chunk.metadata)
                }
                for chunk in collection.chunks
            ],
            "created_at": collection.created_at,
            "processing_info": collection.processing_info,
            "custom_data": collection.custom_data
        }
        
        return result
    
    def import_collection(self, data: Dict[str, Any]) -> ChunkCollection:
        """
        Import a collection from a dictionary.
        
        Args:
            data: Dictionary representation of a collection
            
        Returns:
            ChunkCollection object
        """
        # Create source metadata
        source_data = data.get("source", {})
        source_metadata = SourceMetadata(
            id=source_data.get("id", str(uuid.uuid4())),
            title=source_data.get("title", "Untitled Source"),
            author=source_data.get("author"),
            publication_date=source_data.get("publication_date"),
            url=source_data.get("url"),
            type=source_data.get("type"),
            publication=source_data.get("publication"),
            language=source_data.get("language", "en"),
            created_at=source_data.get("created_at", datetime.now().isoformat()),
            custom_data=source_data.get("custom_data", {})
        )
        
        # Create chunks
        chunks = []
        for chunk_data in data.get("chunks", []):
            metadata_data = chunk_data.get("metadata", {})
            
            # Handle chunk_type conversion from string to enum
            chunk_type_str = metadata_data.get("chunk_type")
            if isinstance(chunk_type_str, str):
                try:
                    chunk_type = ChunkType[chunk_type_str.upper()]
                except KeyError:
                    chunk_type = ChunkType.CUSTOM
            else:
                chunk_type = ChunkType.CUSTOM
            
            # Create chunk metadata
            metadata = ChunkMetadata(
                source_id=metadata_data.get("source_id", source_metadata.id),
                source_title=metadata_data.get("source_title", source_metadata.title),
                chunk_index=metadata_data.get("chunk_index", 0),
                total_chunks=metadata_data.get("total_chunks", 0),
                chunk_type=chunk_type,
                importance_score=metadata_data.get("importance_score", 0.5),
                tokens=metadata_data.get("tokens", 0),
                characters=metadata_data.get("characters", 0),
                semantic_topics=metadata_data.get("semantic_topics", []),
                custom_data=metadata_data.get("custom_data", {})
            )
            
            # Create chunk
            chunk = Chunk(
                id=chunk_data.get("id", f"chunk_{uuid.uuid4().hex[:8]}"),
                content=chunk_data.get("content", ""),
                metadata=metadata
            )
            
            chunks.append(chunk)
        
        # Create collection
        collection = ChunkCollection(
            id=data.get("id", f"col_{uuid.uuid4().hex[:8]}"),
            source=source_metadata,
            chunks=chunks,
            created_at=data.get("created_at", datetime.now().isoformat()),
            processing_info=data.get("processing_info", {}),
            custom_data=data.get("custom_data", {})
        )
        
        # Add to manager
        self.collections[collection.id] = collection
        
        return collection


class ChunkStore:
    """
    Storage and retrieval system for chunks and metadata.
    
    This class provides persistent storage for chunk collections,
    with support for serialization, retrieval, and querying.
    """
    
    def __init__(self, 
                metadata_manager: Optional[MetadataManager] = None,
                storage_dir: Optional[str] = None):
        """
        Initialize the chunk store.
        
        Args:
            metadata_manager: Metadata manager to use (creates new one if None)
            storage_dir: Directory for storing serialized data (memory-only if None)
        """
        self.metadata_manager = metadata_manager or MetadataManager()
        self.storage_dir = storage_dir
        
        # Index tracking
        self.chunk_index: Dict[str, Tuple[str, int]] = {}  # chunk_id -> (collection_id, chunk_index)
        self.content_hash_index: Dict[str, List[str]] = {}  # content_hash -> [chunk_ids]
        self.topic_index: Dict[str, List[str]] = {}  # topic -> [chunk_ids]
    
    def add_collection(self, collection: ChunkCollection) -> str:
        """
        Add a collection to the store and build indices.
        
        Args:
            collection: Collection to add
            
        Returns:
            Collection ID
        """
        # Store the collection
        self.metadata_manager.collections[collection.id] = collection
        
        # Index all chunks
        for i, chunk in enumerate(collection.chunks):
            # Add to chunk index
            self.chunk_index[chunk.id] = (collection.id, i)
            
            # Add to content hash index
            content_hash = hashlib.md5(chunk.content.encode()).hexdigest()
            if content_hash not in self.content_hash_index:
                self.content_hash_index[content_hash] = []
            self.content_hash_index[content_hash].append(chunk.id)
            
            # Add to topic index
            for topic in chunk.metadata.semantic_topics:
                if topic not in self.topic_index:
                    self.topic_index[topic] = []
                self.topic_index[topic].append(chunk.id)
        
        return collection.id
    
    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """
        Retrieve a chunk by ID.
        
        Args:
            chunk_id: ID of the chunk to retrieve
            
        Returns:
            Chunk object if found, None otherwise
        """
        if chunk_id not in self.chunk_index:
            return None
        
        collection_id, chunk_idx = self.chunk_index[chunk_id]
        try:
            collection = self.metadata_manager.get_collection(collection_id)
            return collection.chunks[chunk_idx]
        except (KeyError, IndexError):
            return None
    
    def find_similar_chunks(self, 
                          content: str, 
                          max_results: int = 5) -> List[Chunk]:
        """
        Find chunks with similar content.
        
        Args:
            content: Content to compare against
            max_results: Maximum number of results to return
            
        Returns:
            List of similar chunks
        """
        # For now, use content hash as a simple similarity check
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # If exact match exists, return those chunks
        if content_hash in self.content_hash_index:
            chunk_ids = self.content_hash_index[content_hash]
            return [self.get_chunk(chunk_id) for chunk_id in chunk_ids 
                   if self.get_chunk(chunk_id) is not None][:max_results]
        
        # Otherwise, just return empty list
        # A more advanced implementation would use embedding similarity
        return []
    
    def find_chunks_by_topic(self, 
                           topic: str, 
                           max_results: int = 10) -> List[Chunk]:
        """
        Find chunks related to a specific topic.
        
        Args:
            topic: Topic to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of chunks related to the topic
        """
        # Normalize topic
        norm_topic = topic.lower().strip()
        
        # Check direct match
        if norm_topic in self.topic_index:
            chunk_ids = self.topic_index[norm_topic]
            return [self.get_chunk(chunk_id) for chunk_id in chunk_ids 
                   if self.get_chunk(chunk_id) is not None][:max_results]
        
        # Check partial matches
        results = []
        for indexed_topic, chunk_ids in self.topic_index.items():
            if norm_topic in indexed_topic or indexed_topic in norm_topic:
                for chunk_id in chunk_ids:
                    chunk = self.get_chunk(chunk_id)
                    if chunk:
                        results.append(chunk)
                        if len(results) >= max_results:
                            return results
        
        return results
    
    def get_related_chunks(self, 
                         chunk_id: str, 
                         max_results: int = 5) -> List[Chunk]:
        """
        Find chunks related to a specific chunk.
        
        Args:
            chunk_id: ID of the chunk to find related chunks for
            max_results: Maximum number of results to return
            
        Returns:
            List of related chunks
        """
        chunk = self.get_chunk(chunk_id)
        if not chunk:
            return []
        
        # Get source and neighboring chunks
        collection_id, chunk_idx = self.chunk_index[chunk_id]
        try:
            collection = self.metadata_manager.get_collection(collection_id)
            
            # Start with neighboring chunks
            related = []
            
            # Add previous chunk if exists
            if chunk_idx > 0:
                related.append(collection.chunks[chunk_idx - 1])
            
            # Add next chunk if exists
            if chunk_idx < len(collection.chunks) - 1:
                related.append(collection.chunks[chunk_idx + 1])
            
            # If we need more, add topic-related chunks
            if len(related) < max_results and chunk.metadata.semantic_topics:
                for topic in chunk.metadata.semantic_topics:
                    topic_chunks = self.find_chunks_by_topic(topic, max_results=5)
                    for topic_chunk in topic_chunks:
                        if topic_chunk.id != chunk_id and topic_chunk not in related:
                            related.append(topic_chunk)
                            if len(related) >= max_results:
                                break
                    if len(related) >= max_results:
                        break
            
            return related[:max_results]
        
        except (KeyError, IndexError):
            return []
    
    def save_to_disk(self, collection_id: str, filepath: Optional[str] = None) -> Optional[str]:
        """
        Serialize and save a collection to disk.
        
        Args:
            collection_id: ID of the collection to save
            filepath: Path to save to (generated if None)
            
        Returns:
            Path where the collection was saved, or None if storage_dir is not set
        """
        if not self.storage_dir and not filepath:
            logger.warning("Cannot save to disk: no storage directory or filepath specified")
            return None
        
        try:
            # Export collection to dict
            collection_data = self.metadata_manager.export_collection(collection_id)
            
            # Generate filepath if not provided
            if not filepath:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = f"{self.storage_dir}/collection_{collection_id}_{timestamp}.json"
            
            # Save to disk
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(collection_data, f, indent=2)
                
            logger.info(f"Saved collection {collection_id} to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving collection {collection_id}: {str(e)}")
            return None
    
    def load_from_disk(self, filepath: str) -> Optional[str]:
        """
        Load a collection from disk.
        
        Args:
            filepath: Path to load from
            
        Returns:
            ID of the loaded collection, or None if loading failed
        """
        try:
            # Load from disk
            with open(filepath, 'r', encoding='utf-8') as f:
                collection_data = json.load(f)
            
            # Import collection
            collection = self.metadata_manager.import_collection(collection_data)
            
            # Add to store and index
            self.add_collection(collection)
            
            logger.info(f"Loaded collection {collection.id} from {filepath}")
            return collection.id
            
        except Exception as e:
            logger.error(f"Error loading collection from {filepath}: {str(e)}")
            return None 