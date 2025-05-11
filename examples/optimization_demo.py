#!/usr/bin/env python3
"""
Chunking Optimization Demo

This script demonstrates the performance optimization capabilities of the
chunking system, showing how it improves processing efficiency for large datasets.
"""

import sys
import logging
import json
import time
import asyncio
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import tempfile
import os

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.chunking import (
    Chunk, ChunkMetadata, ChunkType,
    SemanticChunker, FixedSizeChunker, ParagraphChunker, HybridChunker
)
from src.chunking.optimization import (
    ChunkingOptimizer, OptimizedChunkingStrategy,
    PerformanceMonitor, ChunkingPerformanceMetrics
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def plot_performance_comparison(comparison_data, title="Chunking Strategy Performance Comparison"):
    """
    Plot performance comparison data.
    
    Args:
        comparison_data: Dictionary with strategy comparison data
        title: Plot title
    """
    # Extract strategy names and metrics
    strategies = [name for name in comparison_data.keys() 
                 if not name.startswith("best_")]
    
    if not strategies:
        logger.warning("No strategy data available for plotting")
        return
    
    # Create figure with 2x2 subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(title, fontsize=16)
    
    # Plot execution time (lower is better)
    avg_times = [comparison_data[s]["avg_time"] for s in strategies]
    axes[0, 0].bar(strategies, avg_times, color='skyblue')
    axes[0, 0].set_title('Average Execution Time (s)')
    axes[0, 0].set_ylabel('Seconds')
    axes[0, 0].grid(axis='y', linestyle='--', alpha=0.7)
    
    # Plot chunks per second (higher is better)
    chunks_per_sec = [comparison_data[s]["avg_chunks_per_second"] for s in strategies]
    axes[0, 1].bar(strategies, chunks_per_sec, color='lightgreen')
    axes[0, 1].set_title('Chunks Processed per Second')
    axes[0, 1].set_ylabel('Chunks/s')
    axes[0, 1].grid(axis='y', linestyle='--', alpha=0.7)
    
    # Plot tokens per second (higher is better)
    tokens_per_sec = [comparison_data[s]["avg_tokens_per_second"] for s in strategies]
    axes[1, 0].bar(strategies, tokens_per_sec, color='salmon')
    axes[1, 0].set_title('Tokens Processed per Second')
    axes[1, 0].set_ylabel('Tokens/s')
    axes[1, 0].grid(axis='y', linestyle='--', alpha=0.7)
    
    # Plot memory usage (lower is better)
    memory_usage = [comparison_data[s]["avg_memory_mb"] for s in strategies]
    axes[1, 1].bar(strategies, memory_usage, color='plum')
    axes[1, 1].set_title('Memory Usage')
    axes[1, 1].set_ylabel('MB')
    axes[1, 1].grid(axis='y', linestyle='--', alpha=0.7)
    
    # Highlight the best strategy for each metric
    if "best_time" in comparison_data:
        best_time_idx = strategies.index(comparison_data["best_time"])
        axes[0, 0].get_children()[best_time_idx].set_color('darkblue')
    
    if "best_tokens_per_second" in comparison_data:
        best_tokens_idx = strategies.index(comparison_data["best_tokens_per_second"])
        axes[1, 0].get_children()[best_tokens_idx].set_color('darkred')
    
    if "best_memory" in comparison_data:
        best_memory_idx = strategies.index(comparison_data["best_memory"])
        axes[1, 1].get_children()[best_memory_idx].set_color('darkmagenta')
    
    plt.tight_layout()
    
    # Save plot to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        plt.savefig(tmp_file.name)
        logger.info(f"Performance comparison plot saved to {tmp_file.name}")
    
    plt.close()


def plot_optimization_results(size_performance, title="Chunk Size Optimization Results"):
    """
    Plot chunk size optimization results.
    
    Args:
        size_performance: Dictionary with performance data for different chunk sizes
        title: Plot title
    """
    if not size_performance:
        logger.warning("No size performance data available for plotting")
        return
    
    # Extract chunk sizes and metrics
    sizes = sorted(size_performance.keys())
    tokens_per_sec = [size_performance[s]["tokens_per_second"] for s in sizes]
    chunks_per_sec = [size_performance[s]["chunks_per_second"] for s in sizes]
    memory_mb = [size_performance[s]["memory_mb"] for s in sizes]
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle(title, fontsize=16)
    
    # Plot tokens per second
    ax1.plot(sizes, tokens_per_sec, 'o-', color='blue', label='Tokens/s')
    ax1.set_xlabel('Chunk Size')
    ax1.set_ylabel('Tokens per Second', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Plot chunks per second on same axis
    ax3 = ax1.twinx()
    ax3.plot(sizes, chunks_per_sec, 'o-', color='green', label='Chunks/s')
    ax3.set_ylabel('Chunks per Second', color='green')
    ax3.tick_params(axis='y', labelcolor='green')
    
    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines3, labels3 = ax3.get_legend_handles_labels()
    ax1.legend(lines1 + lines3, labels1 + labels3, loc='upper left')
    
    # Plot memory usage
    ax2.plot(sizes, memory_mb, 'o-', color='red')
    ax2.set_xlabel('Chunk Size')
    ax2.set_ylabel('Memory Usage (MB)')
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    # Save plot to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        plt.savefig(tmp_file.name)
        logger.info(f"Optimization results plot saved to {tmp_file.name}")
    
    plt.close()


async def run_demo():
    """Run the optimization demo."""
    print("\nCHUNKING OPTIMIZATION DEMO\n")
    print("This demo showcases the performance optimization capabilities of the chunking system.")
    print("It demonstrates how different chunking strategies perform and how they can be optimized.")
    
    # Load sample texts
    print("\n1. Loading sample research texts...")
    
    sample_texts = [
        """
        # Advanced Machine Learning Research
        
        ## Abstract
        
        This paper presents a comprehensive study of advanced machine learning techniques,
        focusing on their applications in natural language processing. We introduce novel
        approaches to semantic analysis and demonstrate their effectiveness through
        extensive experimentation and empirical evaluation.
        
        ## Introduction
        
        Machine learning has revolutionized the field of computer science, enabling systems
        to learn from data and improve their performance over time. Natural language processing,
        in particular, has benefited immensely from these advances, with applications ranging
        from machine translation to sentiment analysis.
        
        ## Methodology
        
        Our approach combines transformer architectures with reinforcement learning to optimize
        for specific downstream tasks. The key innovation is a new attention mechanism that
        prioritizes semantic relationships between tokens.
        
        We trained our models on a diverse dataset comprising over 10 million documents from
        various sources, including academic papers, news articles, and web content. The training
        procedure involved three phases: pretraining, fine-tuning, and evaluation.
        
        ## Results
        
        Experiments on benchmark datasets show a 15% improvement over state-of-the-art methods.
        Statistical analysis confirms these results are significant (p < 0.01). The improvements
        are particularly pronounced for tasks involving semantic understanding and contextual
        analysis.
        
        ## Conclusion
        
        Our research demonstrates the effectiveness of the proposed techniques for advancing
        the field of natural language processing. The novel attention mechanism provides a
        promising direction for future research in semantic analysis and understanding.
        """ * 5,
        
        """
        # Survey of Semantic Chunking Algorithms
        
        ## Introduction
        
        This survey examines various approaches to semantic chunking of documents for
        natural language processing tasks. Chunking, the process of dividing text into
        semantically coherent segments, plays a crucial role in document understanding
        and information retrieval.
        
        ## Traditional Approaches
        
        Fixed-size chunking has been the standard approach for many years but suffers from
        breaking semantic units across chunk boundaries. This limitation has prompted
        researchers to explore more sophisticated methods that respect the semantic
        structure of the text.
        
        Early approaches to semantic chunking relied on syntactic parsing and rule-based
        systems. These methods identify sentence and paragraph boundaries and use them
        as natural delimitation points for chunks. While intuitive, these approaches
        often fail to capture the underlying semantic relationships that span across
        these syntactic boundaries.
        
        ## Semantic-aware Approaches
        
        Recent methods prioritize preserving semantic units, using linguistic features
        to determine appropriate chunk boundaries. These approaches leverage advancements
        in natural language understanding and embedding techniques to identify semantic
        shifts in the text.
        
        Transformer-based models have shown particular promise in this area, as they
        can capture long-range dependencies and contextual relationships that are
        essential for identifying meaningful semantic units.
        
        ## Comparative Analysis
        
        Our analysis shows that semantic-aware chunking improves downstream task performance
        by 12-18% compared to traditional methods. This improvement is consistent across
        various applications, including information retrieval, question answering, and
        document summarization.
        
        The following table summarizes the performance metrics for different chunking
        approaches on standard benchmarks:
        
        | Method | Precision | Recall | F1 Score |
        |--------|-----------|--------|----------|
        | Fixed-size | 0.72 | 0.68 | 0.70 |
        | Paragraph-based | 0.78 | 0.75 | 0.76 |
        | Semantic-aware | 0.85 | 0.87 | 0.86 |
        | Hybrid | 0.87 | 0.84 | 0.85 |
        
        ## Conclusion
        
        Semantic chunking approaches provide substantial benefits for document processing
        and should be considered standard practice for NLP pipelines. The choice of chunking
        strategy should be informed by the specific requirements of the downstream task,
        with hybrid approaches offering a good balance between performance and efficiency.
        """ * 5,
        
        """
        # Optimization Techniques for Natural Language Processing
        
        ## Abstract
        
        This research paper explores various optimization techniques to improve the efficiency
        of natural language processing systems. We present a comprehensive analysis of methods
        for reducing computational complexity while maintaining high accuracy in language
        understanding tasks.
        
        ## Background
        
        As language models continue to grow in size and complexity, optimization becomes
        increasingly important. Modern transformer-based models often contain billions of
        parameters, making them computationally expensive to train and deploy. This has
        led to a growing interest in techniques that can reduce these costs without
        compromising performance.
        
        ## Memory Optimization
        
        Memory usage is a critical concern in large language models. We investigate several
        approaches to reduce memory footprint:
        
        1. **Quantization**: Reducing the precision of model weights from 32-bit floating-point
           to 16-bit or 8-bit representations.
           
        2. **Pruning**: Removing unnecessary connections in the neural network.
        
        3. **Knowledge Distillation**: Training smaller "student" models to mimic the behavior
           of larger "teacher" models.
           
        4. **Gradient Checkpointing**: Trading computation for memory by recomputing activations
           during the backward pass instead of storing them.
        
        ## Computational Efficiency
        
        We also explore techniques to reduce the computational complexity of language models:
        
        1. **Sparse Attention**: Replacing the quadratic-complexity attention mechanism with
           sparse variants that scale linearly with sequence length.
           
        2. **Early Exit**: Allowing the model to produce outputs from intermediate layers when
           confidence is high enough.
           
        3. **Caching**: Storing and reusing computation results for common inputs.
        
        4. **Parallel Processing**: Distributing computation across multiple processors or
           accelerators.
        
        ## Results
        
        Our experiments show that combining multiple optimization techniques can yield
        substantial efficiency gains. For instance, using 8-bit quantization with sparse
        attention reduces memory usage by 75% and increases inference speed by 300%,
        with only a 2% reduction in accuracy on benchmark tasks.
        
        ## Conclusion
        
        This research demonstrates that significant optimization is possible in natural
        language processing systems through careful application of memory and computational
        efficiency techniques. These optimizations are essential for deploying advanced
        language models in resource-constrained environments and enabling their use in
        real-time applications.
        """ * 5
    ]
    
    print(f"Loaded {len(sample_texts)} sample texts")
    
    # Initialize chunking strategies
    print("\n2. Initializing chunking strategies...")
    
    strategies = {
        "semantic": SemanticChunker(max_chunk_size=150),
        "fixed_size": FixedSizeChunker(chunk_size=150),
        "paragraph": ParagraphChunker(max_chunk_size=150),
        "hybrid": HybridChunker(max_chunk_size=150)
    }
    
    # Test each strategy without optimization
    print("\n3. Testing strategies without optimization...")
    
    monitor = PerformanceMonitor()
    
    for name, strategy in strategies.items():
        print(f"\nTesting {name} strategy...")
        
        # Process each sample text
        monitor.start_monitoring(name)
        
        start_time = time.time()
        all_chunks = []
        total_tokens = 0
        
        for i, text in enumerate(sample_texts):
            print(f"  Processing sample {i+1}...")
            chunks = strategy.chunk_text(
                text, 
                f"sample-{i}", 
                f"Sample Text {i}"
            )
            all_chunks.extend(chunks)
            total_tokens += sum(chunk.metadata.tokens or 0 for chunk in chunks)
        
        end_time = time.time()
        
        # Calculate metrics
        total_time = end_time - start_time
        total_chunks = len(all_chunks)
        avg_chunk_size = total_tokens / total_chunks if total_chunks else 0
        
        # Stop monitoring
        metrics = monitor.stop_monitoring(
            total_chunks=total_chunks,
            total_tokens=total_tokens,
            avg_chunk_size=avg_chunk_size
        )
        
        print(f"  Created {total_chunks} chunks in {total_time:.2f} seconds")
        print(f"  Tokens per second: {metrics.tokens_per_second:.2f}")
        print(f"  Chunks per second: {metrics.chunks_per_second:.2f}")
        print(f"  Memory usage: {metrics.memory_usage_mb:.2f} MB")
    
    # Compare strategies
    print("\n4. Comparing strategy performance...")
    comparison = monitor.compare_strategies(list(strategies.keys()))
    
    # Print comparison results
    for name in strategies.keys():
        if name in comparison:
            print(f"\n{name.capitalize()} Strategy:")
            print(f"  Avg. time: {comparison[name]['avg_time']:.2f} seconds")
            print(f"  Avg. tokens/second: {comparison[name]['avg_tokens_per_second']:.2f}")
            print(f"  Avg. chunks/second: {comparison[name]['avg_chunks_per_second']:.2f}")
            print(f"  Avg. memory usage: {comparison[name]['avg_memory_mb']:.2f} MB")
    
    print("\nBest strategies:")
    if "best_time" in comparison:
        print(f"  Fastest execution: {comparison['best_time']}")
    if "best_tokens_per_second" in comparison:
        print(f"  Highest throughput: {comparison['best_tokens_per_second']}")
    if "best_memory" in comparison:
        print(f"  Lowest memory usage: {comparison['best_memory']}")
    
    # Plot the comparison results
    plot_performance_comparison(comparison)
    
    # Create an optimized chunking strategy
    print("\n5. Testing chunking with optimization...")
    
    # Pick the best strategy from the comparison
    best_strategy_name = comparison.get("best_tokens_per_second", list(strategies.keys())[0])
    best_strategy = strategies[best_strategy_name]
    
    print(f"Selected {best_strategy_name} as the base strategy for optimization")
    
    # Create optimizer
    optimizer = ChunkingOptimizer(max_workers=4)
    
    # Create optimized strategy
    optimized_strategy = OptimizedChunkingStrategy(
        base_strategy=best_strategy,
        optimizer=optimizer,
        use_cache=True,
        use_parallel=True
    )
    
    # Optimize the strategy
    print("\n6. Optimizing chunking parameters...")
    optimization_results = optimized_strategy.optimize(sample_texts)
    
    # Print optimization results
    print("\nOptimization results:")
    if "optimal_chunk_size" in optimization_results:
        print(f"  Optimal chunk size: {optimization_results['optimal_chunk_size']}")
    
    print(f"  Parallel speedup: {optimization_results['parallel_speedup']:.2f}x")
    
    print("\nRecommendations:")
    for recommendation in optimization_results.get("recommendations", []):
        print(f"  - {recommendation}")
    
    # Plot optimization results if available
    if "size_performance" in optimization_results:
        plot_optimization_results(
            optimization_results["size_performance"],
            f"Chunk Size Optimization for {best_strategy_name} Strategy"
        )
    
    # Test sequential vs. parallel processing
    print("\n7. Testing sequential vs. parallel processing...")
    
    # Prepare for parallel processing
    texts = [(text, f"sample-{i}", f"Sample Text {i}")
             for i, text in enumerate(sample_texts)]
    
    # Sequential processing
    print("\nSequential processing:")
    
    start_time = time.time()
    sequential_chunks = []
    
    for text, source_id, source_title in texts:
        chunks = best_strategy.chunk_text(text, source_id, source_title)
        sequential_chunks.extend(chunks)
    
    sequential_time = time.time() - start_time
    
    print(f"  Created {len(sequential_chunks)} chunks in {sequential_time:.2f} seconds")
    
    # Parallel processing
    print("\nParallel processing:")
    
    start_time = time.time()
    
    # Process texts in parallel
    parallel_results = await asyncio.gather(*[
        asyncio.to_thread(best_strategy.chunk_text, text, source_id, source_title)
        for text, source_id, source_title in texts
    ])
    
    # Flatten results
    parallel_chunks = [chunk for chunks in parallel_results for chunk in chunks]
    
    parallel_time = time.time() - start_time
    
    print(f"  Created {len(parallel_chunks)} chunks in {parallel_time:.2f} seconds")
    print(f"  Speedup: {sequential_time / parallel_time:.2f}x")
    
    # Final demonstration with optimized strategy
    print("\n8. Processing with fully optimized strategy...")
    
    # Process a large batch of texts with the optimized strategy
    start_time = time.time()
    
    # Create a larger batch by duplicating the texts
    large_batch = texts * 2  # Double the size
    
    # Process with optimized strategy
    optimized_results = await optimized_strategy.chunk_texts(large_batch)
    
    # Flatten results
    optimized_chunks = [chunk for chunks in optimized_results for chunk in chunks]
    
    optimized_time = time.time() - start_time
    
    print(f"  Processed {len(large_batch)} documents")
    print(f"  Created {len(optimized_chunks)} chunks in {optimized_time:.2f} seconds")
    
    # Compare with estimated sequential time
    estimated_sequential = sequential_time * 2  # Double batch size, double time
    print(f"  Estimated sequential time: {estimated_sequential:.2f} seconds")
    print(f"  Overall speedup: {estimated_sequential / optimized_time:.2f}x")
    
    print("\nOptimization demo complete!")


if __name__ == "__main__":
    try:
        import psutil
    except ImportError:
        print("This demo requires the psutil package. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil
    
    try:
        import matplotlib
    except ImportError:
        print("This demo requires matplotlib. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
        import matplotlib
        import matplotlib.pyplot as plt
    
    asyncio.run(run_demo()) 