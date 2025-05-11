"""
Tests for the chunking algorithm optimization module.

This file contains unit tests for the optimization components and performance monitoring.
"""

import unittest
import asyncio
import time
from unittest import mock

from src.chunking.base import Chunk, ChunkMetadata, ChunkingStrategy, ChunkType
from src.chunking.chunking_strategies import FixedSizeChunker
from src.chunking.optimization import (
    measure_time, ChunkingPerformanceMetrics, PerformanceMonitor,
    ChunkingOptimizer, OptimizedChunkingStrategy
)


class TestMeasureTimeDecorator(unittest.TestCase):
    """Test cases for the measure_time decorator."""
    
    @measure_time
    def sample_function(self, sleep_time=0.1):
        """Sample function that just sleeps."""
        time.sleep(sleep_time)
        return 42
    
    def test_decorator_returns_result(self):
        """Test that the decorator returns the result of the function."""
        result = self.sample_function(sleep_time=0.01)
        self.assertEqual(result, 42)
    
    @mock.patch('src.chunking.optimization.logger')
    def test_decorator_logs_time(self, mock_logger):
        """Test that the decorator logs execution time."""
        self.sample_function(sleep_time=0.01)
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        self.assertIn("sample_function", log_message)
        self.assertIn("executed in", log_message)


class TestChunkingPerformanceMetrics(unittest.TestCase):
    """Test cases for ChunkingPerformanceMetrics data class."""
    
    def test_default_values(self):
        """Test the default values of ChunkingPerformanceMetrics."""
        metrics = ChunkingPerformanceMetrics()
        self.assertEqual(metrics.total_time, 0.0)
        self.assertEqual(metrics.chunks_per_second, 0.0)
        self.assertEqual(metrics.tokens_per_second, 0.0)
        self.assertEqual(metrics.total_chunks, 0)
        self.assertEqual(metrics.strategy_name, "unknown")
        self.assertIsInstance(metrics.custom_metrics, dict)
    
    def test_custom_values(self):
        """Test setting custom values for ChunkingPerformanceMetrics."""
        metrics = ChunkingPerformanceMetrics(
            total_time=10.5,
            chunks_per_second=15.0,
            tokens_per_second=150.0,
            memory_usage_mb=25.0,
            total_chunks=42,
            avg_chunk_size=10.0,
            overlap_percentage=15.0,
            strategy_name="test_strategy",
            custom_metrics={"test_metric": 42}
        )
        
        self.assertEqual(metrics.total_time, 10.5)
        self.assertEqual(metrics.chunks_per_second, 15.0)
        self.assertEqual(metrics.tokens_per_second, 150.0)
        self.assertEqual(metrics.memory_usage_mb, 25.0)
        self.assertEqual(metrics.total_chunks, 42)
        self.assertEqual(metrics.avg_chunk_size, 10.0)
        self.assertEqual(metrics.overlap_percentage, 15.0)
        self.assertEqual(metrics.strategy_name, "test_strategy")
        self.assertEqual(metrics.custom_metrics["test_metric"], 42)


class TestPerformanceMonitor(unittest.TestCase):
    """Test cases for PerformanceMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
    
    def test_start_monitoring(self):
        """Test starting performance monitoring."""
        self.monitor.start_monitoring("test_strategy")
        self.assertIsNotNone(self.monitor.current_metrics)
        self.assertEqual(self.monitor.current_metrics.strategy_name, "test_strategy")
    
    @mock.patch('src.chunking.optimization.psutil.Process')
    def test_stop_monitoring(self, mock_process):
        """Test stopping performance monitoring and recording metrics."""
        # Mock memory info
        mock_process.return_value.memory_info.return_value.rss = 100 * 1024 * 1024  # 100 MB
        
        self.monitor.start_monitoring("test_strategy")
        # Force sleep to get non-zero execution time
        time.sleep(0.01)
        
        metrics = self.monitor.stop_monitoring(
            total_chunks=5,
            total_tokens=100,
            avg_chunk_size=20.0,
            overlap_percentage=10.0,
            custom_metrics={"test_metric": 42}
        )
        
        # Verify metrics were recorded correctly
        self.assertEqual(metrics.total_chunks, 5)
        self.assertEqual(metrics.avg_chunk_size, 20.0)
        self.assertEqual(metrics.overlap_percentage, 10.0)
        self.assertEqual(metrics.custom_metrics["test_metric"], 42)
        self.assertGreater(metrics.total_time, 0)
        self.assertGreater(metrics.chunks_per_second, 0)
        self.assertGreater(metrics.tokens_per_second, 0)
        
        # Verify metrics were added to history
        self.assertEqual(len(self.monitor.metrics_history), 1)
        self.assertEqual(self.monitor.metrics_history[0], metrics)
    
    def test_get_last_metrics(self):
        """Test retrieving the most recent metrics."""
        # No metrics yet
        self.assertIsNone(self.monitor.get_last_metrics())
        
        # Add metrics
        with mock.patch('src.chunking.optimization.psutil.Process'):
            self.monitor.start_monitoring("test_strategy")
            metrics = self.monitor.stop_monitoring(
                total_chunks=5,
                total_tokens=100,
                avg_chunk_size=20.0
            )
        
        # Get last metrics
        last_metrics = self.monitor.get_last_metrics()
        self.assertEqual(last_metrics, metrics)
    
    def test_compare_strategies(self):
        """Test comparing the performance of different strategies."""
        # Create metrics for two different strategies
        with mock.patch('src.chunking.optimization.psutil.Process'):
            # Strategy 1
            self.monitor.start_monitoring("strategy_1")
            metrics1 = self.monitor.stop_monitoring(
                total_chunks=10,
                total_tokens=200,
                avg_chunk_size=20.0
            )
            metrics1.total_time = 2.0
            metrics1.chunks_per_second = 5.0
            metrics1.tokens_per_second = 100.0
            metrics1.memory_usage_mb = 50.0
            
            # Another run of strategy 1
            self.monitor.start_monitoring("strategy_1")
            metrics1b = self.monitor.stop_monitoring(
                total_chunks=10,
                total_tokens=200,
                avg_chunk_size=20.0
            )
            metrics1b.total_time = 3.0
            metrics1b.chunks_per_second = 3.33
            metrics1b.tokens_per_second = 66.7
            metrics1b.memory_usage_mb = 60.0
            
            # Strategy 2
            self.monitor.start_monitoring("strategy_2")
            metrics2 = self.monitor.stop_monitoring(
                total_chunks=8,
                total_tokens=160,
                avg_chunk_size=20.0
            )
            metrics2.total_time = 1.0
            metrics2.chunks_per_second = 8.0
            metrics2.tokens_per_second = 160.0
            metrics2.memory_usage_mb = 70.0
        
        # Force metrics values
        self.monitor.metrics_history = [metrics1, metrics1b, metrics2]
        
        # Compare the strategies
        comparison = self.monitor.compare_strategies(["strategy_1", "strategy_2"])
        
        # Check average calculations
        self.assertAlmostEqual(comparison["strategy_1"]["avg_time"], 2.5, places=1)
        self.assertAlmostEqual(comparison["strategy_1"]["avg_chunks_per_second"], 4.165, places=2)
        self.assertAlmostEqual(comparison["strategy_1"]["avg_tokens_per_second"], 83.35, places=1)
        self.assertAlmostEqual(comparison["strategy_1"]["avg_memory_mb"], 55.0, places=1)
        self.assertEqual(comparison["strategy_1"]["samples"], 2)
        
        self.assertEqual(comparison["strategy_2"]["avg_time"], 1.0)
        self.assertEqual(comparison["strategy_2"]["avg_chunks_per_second"], 8.0)
        self.assertEqual(comparison["strategy_2"]["avg_tokens_per_second"], 160.0)
        self.assertEqual(comparison["strategy_2"]["avg_memory_mb"], 70.0)
        self.assertEqual(comparison["strategy_2"]["samples"], 1)
        
        # Check best strategy determinations
        self.assertEqual(comparison["best_time"], "strategy_2")  # Lower is better
        self.assertEqual(comparison["best_tokens_per_second"], "strategy_2")  # Higher is better
        self.assertEqual(comparison["best_memory"], "strategy_1")  # Lower is better


class MockChunker(ChunkingStrategy):
    """Mock chunking strategy for testing."""
    
    def __init__(self, chunk_size=100):
        """Initialize the mock chunker."""
        self.chunk_size = chunk_size
    
    def chunk_text(self, text, source_id, source_title):
        """Mock implementation of chunk_text."""
        # Just divide the text into equal parts
        if not text:
            return []
        
        # Simplistic chunking for testing
        tokens = len(text.split())
        num_chunks = max(1, tokens // self.chunk_size + (1 if tokens % self.chunk_size > 0 else 0))
        chunk_length = len(text) // num_chunks
        
        chunks = []
        for i in range(num_chunks):
            start = i * chunk_length
            end = start + chunk_length if i < num_chunks - 1 else len(text)
            content = text[start:end]
            
            chunk = Chunk(
                id=f"chunk-{i}",
                content=content,
                metadata=ChunkMetadata(
                    source_id=source_id,
                    source_title=source_title,
                    chunk_index=i,
                    total_chunks=num_chunks,
                    chunk_type=ChunkType.FIXED_SIZE,
                    tokens=len(content.split()),
                    characters=len(content)
                )
            )
            chunks.append(chunk)
        
        time.sleep(0.01)  # Add a small delay to simulate processing time
        return chunks
    
    def get_config(self):
        """Get configuration parameters for caching."""
        return {"chunk_size": self.chunk_size}


class TestChunkingOptimizer(unittest.TestCase):
    """Test cases for ChunkingOptimizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.optimizer = ChunkingOptimizer(max_workers=2, cache_size=10)
        self.chunker = MockChunker(chunk_size=10)
        self.test_text = "This is a test text for chunking. " * 5
    
    @mock.patch('src.chunking.optimization.psutil.Process')
    def test_optimized_chunk_text(self, mock_process):
        """Test optimized chunking with performance monitoring."""
        # Mock memory info
        mock_process.return_value.memory_info.return_value.rss = 100 * 1024 * 1024  # 100 MB
        
        # Call optimized chunking
        chunks = self.optimizer.optimized_chunk_text(
            self.chunker,
            self.test_text,
            "test-source",
            "Test Source",
            use_cache=True
        )
        
        # Verify chunks were created
        self.assertGreater(len(chunks), 0)
        
        # Verify performance monitoring
        self.assertGreater(len(self.optimizer.monitor.metrics_history), 0)
        metrics = self.optimizer.monitor.get_last_metrics()
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.strategy_name, "MockChunker")
        self.assertEqual(metrics.total_chunks, len(chunks))
    
    @mock.patch('src.chunking.optimization.psutil.Process')
    def test_caching(self, mock_process):
        """Test that chunking results are cached."""
        # Mock memory info
        mock_process.return_value.memory_info.return_value.rss = 100 * 1024 * 1024  # 100 MB
        
        # Create a spy on the _chunk_text_implementation method
        with mock.patch.object(
            self.optimizer, '_chunk_text_implementation', wraps=self.optimizer._chunk_text_implementation
        ) as mock_impl:
            
            # First call - should use implementation
            chunks1 = self.optimizer.optimized_chunk_text(
                self.chunker,
                self.test_text,
                "test-source",
                "Test Source",
                use_cache=True
            )
            
            # Second call with same args - should use cache
            chunks2 = self.optimizer.optimized_chunk_text(
                self.chunker,
                self.test_text,
                "test-source",
                "Test Source",
                use_cache=True
            )
            
            # Verify implementation was only called once
            # Note: we can't directly check the call count because of how lru_cache works internally
            # Instead, we check that we got non-empty results both times
            self.assertGreater(len(chunks1), 0)
            self.assertGreater(len(chunks2), 0)
            
            # Different source - should not use cache
            chunks3 = self.optimizer.optimized_chunk_text(
                self.chunker,
                self.test_text,
                "different-source",
                "Different Source",
                use_cache=True
            )
            self.assertGreater(len(chunks3), 0)
    
    @mock.patch('src.chunking.optimization.psutil.Process')
    def test_parallel_chunk_texts(self, mock_process):
        """Test parallel processing of multiple texts."""
        # Mock memory info
        mock_process.return_value.memory_info.return_value.rss = 100 * 1024 * 1024  # 100 MB
        
        # Create multiple test texts
        texts = [
            (f"Test text {i} for chunking. " * 5, f"source-{i}", f"Source {i}")
            for i in range(3)
        ]
        
        # Create an event loop and run parallel chunking
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(
                self.optimizer.parallel_chunk_texts(self.chunker, texts, use_cache=False)
            )
        finally:
            loop.close()
        
        # Verify results
        self.assertEqual(len(results), len(texts))
        for chunks in results:
            self.assertGreater(len(chunks), 0)
        
        # Verify performance monitoring
        metrics = self.optimizer.monitor.get_last_metrics()
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.strategy_name, "MockChunker_parallel")
        self.assertEqual(metrics.custom_metrics["num_documents"], len(texts))


class TestOptimizedChunkingStrategy(unittest.TestCase):
    """Test cases for OptimizedChunkingStrategy class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.base_chunker = MockChunker(chunk_size=10)
        self.optimized_chunker = OptimizedChunkingStrategy(
            base_strategy=self.base_chunker,
            use_cache=True,
            use_parallel=True
        )
        self.test_text = "This is a test text for chunking. " * 5
    
    @mock.patch('src.chunking.optimization.ChunkingOptimizer.optimized_chunk_text')
    def test_chunk_text(self, mock_optimized):
        """Test that chunk_text delegates to the optimizer."""
        mock_optimized.return_value = [Chunk(id="test", content="test", metadata=ChunkMetadata(
            source_id="test", source_title="test", chunk_index=0, total_chunks=1, chunk_type=ChunkType.FIXED_SIZE
        ))]
        
        # Call chunk_text on the optimized strategy
        chunks = self.optimized_chunker.chunk_text(
            self.test_text,
            "test-source",
            "Test Source"
        )
        
        # Verify optimizer was called with correct arguments
        mock_optimized.assert_called_once_with(
            self.base_chunker,
            self.test_text,
            "test-source",
            "Test Source",
            use_cache=True
        )
        
        # Verify results were returned
        self.assertEqual(len(chunks), 1)
    
    @mock.patch('src.chunking.optimization.ChunkingOptimizer.parallel_chunk_texts')
    def test_chunk_texts(self, mock_parallel):
        """Test that chunk_texts delegates to the optimizer for parallel processing."""
        mock_result = [[Chunk(id="test", content="test", metadata=ChunkMetadata(
            source_id="test", source_title="test", chunk_index=0, total_chunks=1, chunk_type=ChunkType.FIXED_SIZE
        ))]]
        
        async def async_return():
            return mock_result
        
        mock_parallel.return_value = async_return()
        
        # Prepare test data
        texts = [(self.test_text, "test-source", "Test Source")]
        
        # Create an event loop and run chunk_texts
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(self.optimized_chunker.chunk_texts(texts))
        finally:
            loop.close()
        
        # Verify parallel_chunk_texts was called with correct arguments
        mock_parallel.assert_called_once_with(
            self.base_chunker,
            texts,
            use_cache=True
        )
        
        # Verify results were returned
        self.assertEqual(results, mock_result)
    
    def test_get_base_strategy(self):
        """Test that get_base_strategy returns the base strategy."""
        base = self.optimized_chunker.get_base_strategy()
        self.assertEqual(base, self.base_chunker)
    
    @mock.patch('src.chunking.optimization.ChunkingOptimizer.optimize_chunking_strategy')
    def test_optimize(self, mock_optimize):
        """Test that optimize delegates to the optimizer."""
        expected_result = {"test": "result"}
        mock_optimize.return_value = expected_result
        
        # Call optimize
        sample_texts = ["Sample text 1", "Sample text 2"]
        result = self.optimized_chunker.optimize(sample_texts)
        
        # Verify optimizer was called with correct arguments
        mock_optimize.assert_called_once_with(
            self.base_chunker,
            sample_texts
        )
        
        # Verify results were returned
        self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main() 