"""
Chunking algorithm optimization module.

This module provides performance optimization for chunking algorithms,
with a focus on efficiently processing large volumes of research content.
"""

import time
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps, lru_cache
from typing import List, Dict, Any, Callable, Optional, Tuple, Union, TypeVar, Generic, Set
import sys
import multiprocessing
from dataclasses import dataclass, field
import os

from .base import Chunk, ChunkMetadata, ChunkingStrategy, ChunkType
from .metadata_handling import ChunkStore, MetadataManager, ChunkCollection

logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')


def measure_time(func):
    """Decorator to measure the execution time of a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Function {func.__name__} executed in {execution_time:.4f} seconds")
        return result
    return wrapper


@dataclass
class ChunkingPerformanceMetrics:
    """Metrics for evaluating chunking performance."""
    total_time: float = 0.0             # Total execution time in seconds
    chunks_per_second: float = 0.0      # Number of chunks processed per second
    tokens_per_second: float = 0.0      # Number of tokens processed per second
    memory_usage_mb: float = 0.0        # Memory usage in MB
    total_chunks: int = 0               # Total number of chunks created
    avg_chunk_size: float = 0.0         # Average chunk size in tokens
    overlap_percentage: float = 0.0     # Percentage of tokens in overlaps
    strategy_name: str = "unknown"      # Name of chunking strategy used
    timestamp: float = field(default_factory=time.time)  # When the metrics were recorded
    custom_metrics: Dict[str, Any] = field(default_factory=dict)  # Additional metrics


class PerformanceMonitor:
    """
    Monitor and analyze the performance of chunking operations.
    
    This class provides methods for tracking execution time, memory usage,
    and other performance metrics during chunking operations.
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.metrics_history: List[ChunkingPerformanceMetrics] = []
        self.current_metrics: Optional[ChunkingPerformanceMetrics] = None
    
    def start_monitoring(self, strategy_name: str) -> None:
        """
        Start monitoring a chunking operation.
        
        Args:
            strategy_name: Name of the chunking strategy being used
        """
        self.current_metrics = ChunkingPerformanceMetrics(
            strategy_name=strategy_name,
            timestamp=time.time()
        )
    
    def stop_monitoring(self, 
                      total_chunks: int, 
                      total_tokens: int,
                      avg_chunk_size: float,
                      overlap_percentage: float = 0.0,
                      custom_metrics: Optional[Dict[str, Any]] = None) -> ChunkingPerformanceMetrics:
        """
        Stop monitoring and record final metrics.
        
        Args:
            total_chunks: Total number of chunks processed
            total_tokens: Total number of tokens processed
            avg_chunk_size: Average chunk size in tokens
            overlap_percentage: Percentage of tokens in overlaps
            custom_metrics: Additional custom metrics to record
            
        Returns:
            The completed performance metrics
        """
        if not self.current_metrics:
            logger.warning("stop_monitoring called without calling start_monitoring first")
            self.start_monitoring("unknown")
        
        end_time = time.time()
        execution_time = end_time - self.current_metrics.timestamp
        
        # Get memory usage (current process only)
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
        
        # Update metrics
        self.current_metrics.total_time = execution_time
        self.current_metrics.total_chunks = total_chunks
        self.current_metrics.avg_chunk_size = avg_chunk_size
        self.current_metrics.overlap_percentage = overlap_percentage
        self.current_metrics.memory_usage_mb = memory_mb
        
        # Compute derived metrics
        if execution_time > 0:
            self.current_metrics.chunks_per_second = total_chunks / execution_time
            self.current_metrics.tokens_per_second = total_tokens / execution_time
        
        # Add custom metrics
        if custom_metrics:
            self.current_metrics.custom_metrics.update(custom_metrics)
        
        # Save metrics to history
        self.metrics_history.append(self.current_metrics)
        
        # Log summary
        logger.info(f"Chunking performance metrics ({self.current_metrics.strategy_name}):")
        logger.info(f"  Time: {self.current_metrics.total_time:.2f}s")
        logger.info(f"  Chunks: {total_chunks} ({self.current_metrics.chunks_per_second:.2f}/s)")
        logger.info(f"  Tokens: {total_tokens} ({self.current_metrics.tokens_per_second:.2f}/s)")
        logger.info(f"  Memory: {self.current_metrics.memory_usage_mb:.2f} MB")
        
        return self.current_metrics
    
    def get_last_metrics(self) -> Optional[ChunkingPerformanceMetrics]:
        """
        Get the most recently recorded metrics.
        
        Returns:
            The most recent performance metrics, or None if none exist
        """
        if not self.metrics_history:
            return None
        return self.metrics_history[-1]
    
    def compare_strategies(self, 
                         strategy_names: List[str]) -> Dict[str, Any]:
        """
        Compare the performance of different chunking strategies.
        
        Args:
            strategy_names: Names of strategies to compare
            
        Returns:
            Dictionary with comparison results
        """
        comparison = {}
        
        # Filter metrics by strategy names
        filtered_metrics = {}
        for name in strategy_names:
            filtered_metrics[name] = [
                m for m in self.metrics_history 
                if m.strategy_name == name
            ]
        
        # Calculate averages for each strategy
        for name, metrics_list in filtered_metrics.items():
            if not metrics_list:
                comparison[name] = {"error": "No metrics available"}
                continue
            
            # Calculate averages
            avg_time = sum(m.total_time for m in metrics_list) / len(metrics_list)
            avg_chunks_per_sec = sum(m.chunks_per_second for m in metrics_list) / len(metrics_list)
            avg_tokens_per_sec = sum(m.tokens_per_second for m in metrics_list) / len(metrics_list)
            avg_memory = sum(m.memory_usage_mb for m in metrics_list) / len(metrics_list)
            
            comparison[name] = {
                "avg_time": avg_time,
                "avg_chunks_per_second": avg_chunks_per_sec,
                "avg_tokens_per_second": avg_tokens_per_sec,
                "avg_memory_mb": avg_memory,
                "samples": len(metrics_list)
            }
        
        # Determine the best strategy for each metric
        if len(filtered_metrics) > 1:
            valid_strategies = [name for name, metrics in filtered_metrics.items() if metrics]
            
            if valid_strategies:
                # Find best for execution time (lowest is best)
                best_time = min(valid_strategies, key=lambda x: comparison[x]["avg_time"])
                comparison["best_time"] = best_time
                
                # Find best for tokens per second (highest is best)
                best_tokens = max(valid_strategies, key=lambda x: comparison[x]["avg_tokens_per_second"])
                comparison["best_tokens_per_second"] = best_tokens
                
                # Find best for memory usage (lowest is best)
                best_memory = min(valid_strategies, key=lambda x: comparison[x]["avg_memory_mb"])
                comparison["best_memory"] = best_memory
        
        return comparison


class ChunkingOptimizer:
    """
    Optimizer for chunking algorithms that enhances performance for large-scale processing.
    
    This class provides methods for parallel chunking, caching, and other optimizations
    to improve the efficiency of processing large volumes of research content.
    """
    
    def __init__(self, 
                max_workers: Optional[int] = None,
                cache_size: int = 1024,
                monitor: Optional[PerformanceMonitor] = None):
        """
        Initialize the chunking optimizer.
        
        Args:
            max_workers: Maximum number of workers for parallel processing
            cache_size: Size of the LRU cache for chunking results
            monitor: Performance monitor instance
        """
        self.max_workers = max_workers or min(32, (multiprocessing.cpu_count() * 2))
        self.monitor = monitor or PerformanceMonitor()
        self.chunk_cache_size = cache_size
        
        # Create an LRU cache for the chunk_text function
        self.cached_chunk_text = lru_cache(maxsize=cache_size)(self._chunk_text_implementation)
    
    def _chunk_text_implementation(self, 
                                chunker: ChunkingStrategy,
                                text: str,
                                source_id: str,
                                source_title: str) -> List[Chunk]:
        """
        Implementation of chunk_text that will be cached.
        
        Note: This function should not be called directly - use optimized_chunk_text instead.
        
        Args:
            chunker: Chunking strategy to use
            text: Text to chunk
            source_id: Source document ID
            source_title: Source document title
            
        Returns:
            List of chunks
        """
        return chunker.chunk_text(text, source_id, source_title)
    
    @measure_time
    def optimized_chunk_text(self,
                           chunker: ChunkingStrategy,
                           text: str,
                           source_id: str,
                           source_title: str,
                           use_cache: bool = True) -> List[Chunk]:
        """
        Optimized version of the chunk_text method with caching.
        
        Args:
            chunker: Chunking strategy to use
            text: Text to chunk
            source_id: Source document ID
            source_title: Source document title
            use_cache: Whether to use caching
            
        Returns:
            List of chunks
        """
        # Start monitoring
        self.monitor.start_monitoring(chunker.__class__.__name__)
        
        # Use cache if enabled, otherwise call directly
        if use_cache:
            # For caching to work correctly, we need a hashable key
            # We can't use the chunker object directly as it may not be hashable
            # Instead, we use its class name, max_chunk_size, and other relevant attributes
            try:
                chunk_config = chunker.get_config()
                chunks = self.cached_chunk_text(
                    chunker.__class__.__name__,
                    frozenset(chunk_config.items()),
                    text,
                    source_id,
                    source_title
                )
            except (AttributeError, TypeError):
                # If get_config() is not available or returns non-hashable values,
                # fall back to direct call
                logger.warning(f"Could not use cache for {chunker.__class__.__name__}, falling back to direct call")
                chunks = chunker.chunk_text(text, source_id, source_title)
        else:
            chunks = chunker.chunk_text(text, source_id, source_title)
        
        # Calculate metrics
        total_tokens = sum(chunk.metadata.tokens or 0 for chunk in chunks)
        avg_chunk_size = total_tokens / len(chunks) if chunks else 0
        
        # Stop monitoring and record metrics
        self.monitor.stop_monitoring(
            total_chunks=len(chunks),
            total_tokens=total_tokens,
            avg_chunk_size=avg_chunk_size
        )
        
        return chunks
    
    async def parallel_chunk_texts(self,
                                chunker: ChunkingStrategy,
                                texts: List[Tuple[str, str, str]],
                                use_cache: bool = True) -> List[List[Chunk]]:
        """
        Process multiple texts in parallel with the same chunker.
        
        Args:
            chunker: Chunking strategy to use
            texts: List of (text, source_id, source_title) tuples
            use_cache: Whether to use caching
            
        Returns:
            List of chunk lists, one per input text
        """
        # Start monitoring
        self.monitor.start_monitoring(f"{chunker.__class__.__name__}_parallel")
        
        async def process_text(text_tuple):
            text, source_id, source_title = text_tuple
            return self.optimized_chunk_text(chunker, text, source_id, source_title, use_cache)
        
        # Create tasks for processing each text
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            tasks = [
                loop.run_in_executor(
                    executor,
                    lambda t=text_tuple: self.optimized_chunk_text(
                        chunker, t[0], t[1], t[2], use_cache
                    )
                )
                for text_tuple in texts
            ]
            
            # Wait for all tasks to complete
            all_chunks = await asyncio.gather(*tasks)
        
        # Calculate metrics
        total_chunks = sum(len(chunks) for chunks in all_chunks)
        total_tokens = sum(
            sum(chunk.metadata.tokens or 0 for chunk in chunks)
            for chunks in all_chunks
        )
        avg_chunk_size = total_tokens / total_chunks if total_chunks else 0
        
        # Stop monitoring and record metrics
        self.monitor.stop_monitoring(
            total_chunks=total_chunks,
            total_tokens=total_tokens,
            avg_chunk_size=avg_chunk_size,
            custom_metrics={"num_documents": len(texts)}
        )
        
        return all_chunks
    
    def optimize_chunking_strategy(self, 
                                chunker: ChunkingStrategy,
                                sample_texts: List[str]) -> Dict[str, Any]:
        """
        Analyze and optimize a chunking strategy based on sample texts.
        
        Args:
            chunker: Chunking strategy to optimize
            sample_texts: Representative sample texts
            
        Returns:
            Dictionary with optimization results and recommended settings
        """
        results = {}
        
        # Test different chunk size settings if applicable
        chunk_sizes = []
        try:
            # Get current chunk size
            current_size = chunker.max_chunk_size
            # Test a range of sizes
            chunk_sizes = [
                max(50, int(current_size * 0.5)),  # 50% of current size
                current_size,  # Current size
                int(current_size * 1.5),  # 150% of current size
                int(current_size * 2.0)   # 200% of current size
            ]
        except AttributeError:
            # Strategy doesn't support max_chunk_size
            try:
                current_size = chunker.chunk_size
                chunk_sizes = [
                    max(50, int(current_size * 0.5)),
                    current_size,
                    int(current_size * 1.5),
                    int(current_size * 2.0)
                ]
            except AttributeError:
                # Strategy doesn't support changing chunk size
                logger.info(f"Strategy {chunker.__class__.__name__} doesn't support chunk size adjustment")
                results["chunk_size_optimization"] = "not supported"
                chunk_sizes = []
        
        if chunk_sizes:
            size_metrics = {}
            
            for size in chunk_sizes:
                try:
                    # Create a copy of the chunker with the new size
                    chunker_copy = chunker.__class__(**{**chunker.__dict__, "max_chunk_size": size})
                except (TypeError, AttributeError):
                    try:
                        chunker_copy = chunker.__class__(**{**chunker.__dict__, "chunk_size": size})
                    except (TypeError, AttributeError):
                        logger.warning(f"Could not create copy of {chunker.__class__.__name__} with size {size}")
                        continue
                
                # Process all sample texts and measure performance
                self.monitor.start_monitoring(f"{chunker.__class__.__name__}_size_{size}")
                
                all_chunks = []
                total_tokens = 0
                start_time = time.time()
                
                for i, text in enumerate(sample_texts):
                    chunks = chunker_copy.chunk_text(
                        text, 
                        f"sample-{i}", 
                        f"Sample Text {i}"
                    )
                    all_chunks.extend(chunks)
                    total_tokens += sum(chunk.metadata.tokens or 0 for chunk in chunks)
                
                end_time = time.time()
                
                # Calculate metrics
                total_chunks = len(all_chunks)
                avg_chunk_size = total_tokens / total_chunks if total_chunks else 0
                
                # Record metrics
                self.monitor.stop_monitoring(
                    total_chunks=total_chunks,
                    total_tokens=total_tokens,
                    avg_chunk_size=avg_chunk_size,
                    custom_metrics={"chunk_size_setting": size}
                )
                
                # Store metrics for this size
                size_metrics[size] = self.monitor.get_last_metrics()
            
            # Determine optimal size based on tokens per second
            if size_metrics:
                optimal_size = max(
                    size_metrics.keys(),
                    key=lambda s: size_metrics[s].tokens_per_second
                )
                
                results["optimal_chunk_size"] = optimal_size
                results["size_performance"] = {
                    size: {
                        "tokens_per_second": metrics.tokens_per_second,
                        "chunks_per_second": metrics.chunks_per_second,
                        "memory_mb": metrics.memory_usage_mb
                    }
                    for size, metrics in size_metrics.items()
                }
        
        # Test parallel vs. sequential processing
        parallel_speedup = self._measure_parallel_speedup(chunker, sample_texts)
        results["parallel_speedup"] = parallel_speedup
        
        # Make recommendations
        recommendations = []
        
        if "optimal_chunk_size" in results:
            current_size = None
            try:
                current_size = chunker.max_chunk_size
            except AttributeError:
                try:
                    current_size = chunker.chunk_size
                except AttributeError:
                    pass
            
            if current_size and results["optimal_chunk_size"] != current_size:
                recommendations.append(
                    f"Use chunk size of {results['optimal_chunk_size']} instead of {current_size} "
                    f"for {int(results['size_performance'][results['optimal_chunk_size']]['tokens_per_second'] / results['size_performance'][current_size]['tokens_per_second'] * 100 - 100)}% speedup"
                )
        
        if parallel_speedup > 1.5:
            recommendations.append(
                f"Use parallel processing for {int((parallel_speedup - 1) * 100)}% speedup"
            )
        
        results["recommendations"] = recommendations
        
        return results
    
    def _measure_parallel_speedup(self,
                              chunker: ChunkingStrategy,
                              sample_texts: List[str]) -> float:
        """
        Measure the speedup from parallel processing.
        
        Args:
            chunker: Chunking strategy to test
            sample_texts: Sample texts to process
            
        Returns:
            Speedup factor (parallel time / sequential time)
        """
        # Skip if only one sample or fewer than 2 CPU cores
        if len(sample_texts) <= 1 or multiprocessing.cpu_count() < 2:
            return 1.0
        
        # Prepare input data
        text_tuples = [
            (text, f"sample-{i}", f"Sample Text {i}")
            for i, text in enumerate(sample_texts)
        ]
        
        # Measure sequential time
        self.monitor.start_monitoring(f"{chunker.__class__.__name__}_sequential")
        
        sequential_start = time.time()
        all_sequential_chunks = []
        
        for text, source_id, source_title in text_tuples:
            chunks = chunker.chunk_text(text, source_id, source_title)
            all_sequential_chunks.extend(chunks)
        
        sequential_time = time.time() - sequential_start
        
        # Stop monitoring
        total_chunks = len(all_sequential_chunks)
        total_tokens = sum(chunk.metadata.tokens or 0 for chunk in all_sequential_chunks)
        avg_chunk_size = total_tokens / total_chunks if total_chunks else 0
        
        sequential_metrics = self.monitor.stop_monitoring(
            total_chunks=total_chunks,
            total_tokens=total_tokens,
            avg_chunk_size=avg_chunk_size
        )
        
        # Measure parallel time
        self.monitor.start_monitoring(f"{chunker.__class__.__name__}_parallel_test")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            all_parallel_chunks = loop.run_until_complete(
                self.parallel_chunk_texts(chunker, text_tuples, use_cache=False)
            )
        finally:
            loop.close()
        
        # Flatten the list of lists
        flat_parallel_chunks = [chunk for chunks in all_parallel_chunks for chunk in chunks]
        
        # Calculate metrics
        total_chunks = len(flat_parallel_chunks)
        total_tokens = sum(chunk.metadata.tokens or 0 for chunk in flat_parallel_chunks)
        avg_chunk_size = total_tokens / total_chunks if total_chunks else 0
        
        parallel_metrics = self.monitor.stop_monitoring(
            total_chunks=total_chunks,
            total_tokens=total_tokens,
            avg_chunk_size=avg_chunk_size
        )
        
        # Calculate speedup
        if parallel_metrics.total_time > 0:
            speedup = sequential_metrics.total_time / parallel_metrics.total_time
        else:
            speedup = 1.0
        
        return speedup


class OptimizedChunkingStrategy(ChunkingStrategy):
    """
    A wrapper around any chunking strategy that applies optimizations.
    
    This class enhances any existing chunking strategy with caching,
    parallel processing, and performance monitoring.
    """
    
    def __init__(self, 
                base_strategy: ChunkingStrategy,
                optimizer: Optional[ChunkingOptimizer] = None,
                use_cache: bool = True,
                use_parallel: bool = True):
        """
        Initialize the optimized chunking strategy.
        
        Args:
            base_strategy: The underlying chunking strategy to optimize
            optimizer: Chunking optimizer to use (creates new one if None)
            use_cache: Whether to use caching
            use_parallel: Whether to use parallel processing for multiple texts
        """
        self.base_strategy = base_strategy
        self.optimizer = optimizer or ChunkingOptimizer()
        self.use_cache = use_cache
        self.use_parallel = use_parallel
        
        # Forward attribute access to base strategy
        for attr_name in dir(base_strategy):
            if not attr_name.startswith('_') and not hasattr(self, attr_name):
                setattr(self, attr_name, getattr(base_strategy, attr_name))
    
    def chunk_text(self, 
                 text: str, 
                 source_id: str, 
                 source_title: str) -> List[Chunk]:
        """
        Chunk text using the optimized base strategy.
        
        Args:
            text: Text to chunk
            source_id: Source document ID
            source_title: Source document title
            
        Returns:
            List of chunks
        """
        return self.optimizer.optimized_chunk_text(
            self.base_strategy,
            text,
            source_id,
            source_title,
            use_cache=self.use_cache
        )
    
    async def chunk_texts(self, 
                        texts: List[Tuple[str, str, str]]) -> List[List[Chunk]]:
        """
        Process multiple texts, potentially in parallel.
        
        Args:
            texts: List of (text, source_id, source_title) tuples
            
        Returns:
            List of chunk lists, one per input text
        """
        if not self.use_parallel or len(texts) == 1:
            # Process sequentially
            return [self.chunk_text(text, source_id, source_title) 
                   for text, source_id, source_title in texts]
        
        # Process in parallel
        return await self.optimizer.parallel_chunk_texts(
            self.base_strategy,
            texts,
            use_cache=self.use_cache
        )
    
    def get_base_strategy(self) -> ChunkingStrategy:
        """Get the underlying base strategy."""
        return self.base_strategy
    
    def get_performance_metrics(self) -> List[ChunkingPerformanceMetrics]:
        """Get the performance metrics history."""
        return self.optimizer.monitor.metrics_history
    
    def optimize(self, sample_texts: List[str]) -> Dict[str, Any]:
        """
        Optimize the strategy based on sample texts.
        
        Args:
            sample_texts: Representative sample texts
            
        Returns:
            Optimization results and recommendations
        """
        return self.optimizer.optimize_chunking_strategy(
            self.base_strategy,
            sample_texts
        ) 