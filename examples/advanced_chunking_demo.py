#!/usr/bin/env python3
"""
Advanced Chunking System Demo

This script demonstrates the complete advanced chunking system with all its components:
- Multiple chunking strategies
- Content prioritization
- Metadata handling
- Performance optimization
- Parallel processing
- Visualization of results

This comprehensive demo showcases how the chunking system processes large volumes of
research data while maintaining semantic coherence and optimizing for context.
"""

import sys
import logging
import json
import time
import asyncio
import os
from pathlib import Path
import tempfile
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import asdict

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.chunking import (
    # Base components
    Chunk, ChunkMetadata, ChunkingStrategy, ChunkType,
    # Chunking strategies
    SemanticChunker, FixedSizeChunker, ParagraphChunker, HybridChunker,
    # Content prioritization
    ContentPriority, PriorityScore, ContentPrioritizer, PrioritizedChunker,
    # Metadata handling
    SourceMetadata, ChunkCollection, MetadataManager, ChunkStore,
    # Optimization
    ChunkingPerformanceMetrics, PerformanceMonitor, 
    ChunkingOptimizer, OptimizedChunkingStrategy
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_separator(title: str):
    """Print a section separator with title."""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80 + "\n")


def print_chunk_sample(chunks: List[Chunk], n: int = 3):
    """
    Print a sample of chunks with metadata.
    
    Args:
        chunks: List of chunks to sample from
        n: Number of chunks to show
    """
    if not chunks:
        print("No chunks available to display.")
        return
    
    sample = chunks[:min(n, len(chunks))]
    
    for i, chunk in enumerate(sample):
        print(f"\nCHUNK {i+1}/{len(sample)} (ID: {chunk.id})")
        print(f"  Source: {chunk.metadata.source_title} ({chunk.metadata.source_id})")
        print(f"  Type: {chunk.metadata.chunk_type.name}")
        print(f"  Position: {chunk.metadata.chunk_index+1} of {chunk.metadata.total_chunks}")
        print(f"  Size: {chunk.metadata.tokens} tokens, {chunk.metadata.characters} chars")
        
        # Show priority score if available
        priority_score = chunk.metadata.custom_metadata.get("priority_score")
        if priority_score is not None:
            print(f"  Priority: {priority_score:.2f}")
        
        # Print content preview
        print("\n  Content Preview:")
        content_preview = chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
        for line in content_preview.split("\n"):
            print(f"    {line}")
        print("")
    
    print(f"Showing {len(sample)} of {len(chunks)} chunks")


def plot_chunking_comparison(results: Dict[str, Dict[str, float]], 
                            metric: str,
                            title: str,
                            ylabel: str,
                            higher_is_better: bool = True):
    """
    Plot a comparison of chunking strategies.
    
    Args:
        results: Dictionary with strategy results
        metric: Metric to compare
        title: Plot title
        ylabel: Y-axis label
        higher_is_better: Whether higher values are better
    """
    strategies = list(results.keys())
    values = [results[s][metric] for s in strategies]
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(strategies, values, color='skyblue')
    
    # Highlight the best bar
    if higher_is_better:
        best_idx = values.index(max(values))
    else:
        best_idx = values.index(min(values))
    
    bars[best_idx].set_color('navy')
    
    plt.title(title)
    plt.ylabel(ylabel)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add value labels on top of bars
    for i, v in enumerate(values):
        plt.text(i, v + (max(values) * 0.02), f"{v:.2f}", 
                ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    
    # Save plot to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        plt.savefig(tmp_file.name)
        logger.info(f"Plot saved to {tmp_file.name}")
    
    plt.close()


def generate_sample_text(size_kb: int = 30) -> str:
    """
    Generate a sample text for demonstration purposes.
    
    Args:
        size_kb: Target size in kilobytes
        
    Returns:
        A sample text
    """
    # Sample document with varied content and structure
    base_text = """
# Advanced Research on Neural Networks and Deep Learning

## Abstract

This comprehensive study explores recent advances in neural network architectures and deep learning techniques, with a particular focus on applications in natural language processing and computer vision. We analyze the performance of various models across different tasks and provide recommendations for practitioners.

## 1. Introduction

Neural networks have revolutionized the field of artificial intelligence, enabling systems to learn from data and improve their performance over time. The field has seen rapid advances in recent years, with new architectures and training methodologies continuously pushing the boundaries of what's possible.

Deep learning, in particular, has demonstrated remarkable success in a wide range of applications, from image recognition and natural language understanding to game playing and scientific discovery. This success is largely attributed to the availability of large datasets, increased computational power, and algorithmic innovations.

## 2. Background

### 2.1 Historical Development

The history of neural networks dates back to the 1940s, with the introduction of the McCulloch-Pitts neuron. However, it wasn't until the 1980s that backpropagation enabled practical training of multi-layer networks. The field experienced a renaissance in the 2010s with the advent of deep learning, driven by breakthroughs such as:

- Convolutional Neural Networks (CNNs) for computer vision
- Recurrent Neural Networks (RNNs) and Long Short-Term Memory (LSTM) for sequential data
- Transformers and attention mechanisms for natural language processing

### 2.2 Key Concepts

Neural networks are composed of interconnected layers of artificial neurons that transform input data through a series of non-linear operations. The learning process involves adjusting the connection weights to minimize a loss function that measures the difference between predicted and actual outputs.

## 3. Methodology

Our research methodology involves systematic evaluation of various neural network architectures on standardized benchmarks. We employed rigorous statistical analysis to ensure the validity of our findings, using multiple random initializations and cross-validation where appropriate.

The experiments were conducted on a cluster of NVIDIA A100 GPUs, with each model trained for a minimum of 100 epochs or until convergence. We used standard optimization techniques such as Adam with learning rate scheduling to ensure optimal training dynamics.

## 4. Results

### 4.1 Performance Evaluation

Our experiments revealed several interesting patterns:

| Model             | Accuracy (%) | Training Time (h) | Memory (GB) |
|-------------------|--------------|-------------------|-------------|
| CNN (ResNet-50)   | 94.2         | 3.5               | 4.2         |
| LSTM              | 89.7         | 5.2               | 3.8         |
| Transformer (base)| 96.3         | 8.1               | 7.5         |
| Transformer (large)| 97.8        | 22.4              | 12.6        |

The Transformer models consistently outperformed other architectures, particularly on complex tasks requiring long-range dependencies. However, this came at the cost of increased computational requirements and training time.

### 4.2 Ablation Studies

To understand the contribution of different components, we conducted extensive ablation studies by systematically removing or modifying parts of each architecture. The results highlighted the critical role of attention mechanisms in the Transformer models and the importance of residual connections in enabling training of very deep networks.

## 5. Discussion

Our findings have several important implications for the field:

1. **Scaling Laws**: We observed that performance continues to improve with model size and dataset size, following predictable scaling laws.

2. **Efficiency Tradeoffs**: While larger models generally perform better, there are diminishing returns when considering computational costs. Careful consideration of these tradeoffs is essential for practical applications.

3. **Transfer Learning**: Pre-training on large datasets followed by fine-tuning on specific tasks consistently outperformed training from scratch, suggesting that transfer learning should be the default approach for most applications.

## 6. Conclusion

This research advances our understanding of neural network architectures and their performance characteristics. The dominance of Transformer-based models across diverse tasks suggests a convergence in architecture design, though domain-specific optimizations remain important for certain applications.

Future work should focus on improving the efficiency of these models and developing methods to reduce their computational and environmental footprint while maintaining high performance.

## References

1. LeCun, Y., Bengio, Y., & Hinton, G. (2015). Deep learning. Nature, 521(7553), 436-444.
2. Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... & Polosukhin, I. (2017). Attention is all you need. In Advances in neural information processing systems (pp. 5998-6008).
3. Brown, T. B., Mann, B., Ryder, N., Subbiah, M., Kaplan, J., Dhariwal, P., ... & Amodei, D. (2020). Language models are few-shot learners. arXiv preprint arXiv:2005.14165.
"""
    
    # Determine how many repeats we need to reach the target size
    base_size_kb = len(base_text.encode('utf-8')) / 1024
    repeats = max(1, int(size_kb / base_size_kb) + 1)
    
    # Create the full text with some variations
    full_text = base_text
    
    for i in range(1, repeats):
        # Add some variations to make it look like different content
        variation = f"\n\n# Additional Research Section {i}\n\n"
        variation += f"This section explores additional aspects of neural networks and their applications "
        variation += f"in various domains including healthcare, finance, and autonomous systems.\n\n"
        variation += base_text.replace("Neural Networks", f"Neural Networks (Variation {i})")
        
        full_text += variation
    
    return full_text


async def run_demo():
    """Run the comprehensive chunking demo."""
    print_separator("ADVANCED CHUNKING SYSTEM DEMONSTRATION")
    print("This demonstration showcases the complete advanced chunking system with:")
    print("- Multiple chunking strategies")
    print("- Content prioritization")
    print("- Metadata handling")
    print("- Performance optimization")
    print("- Parallel processing\n")
    
    # Create a temporary directory for output files
    temp_dir = tempfile.TemporaryDirectory()
    output_dir = Path(temp_dir.name)
    
    try:
        # Step 1: Generate sample documents
        print_separator("1. GENERATING SAMPLE DOCUMENTS")
        
        print("Generating sample research documents...")
        docs = [
            {
                "id": "doc1",
                "title": "Neural Network Architectures",
                "content": generate_sample_text(30)
            },
            {
                "id": "doc2",
                "title": "Transformer Models for NLP",
                "content": generate_sample_text(40)
            },
            {
                "id": "doc3",
                "title": "Computational Efficiency in Deep Learning",
                "content": generate_sample_text(35)
            }
        ]
        
        print(f"Generated {len(docs)} documents")
        for doc in docs:
            size_kb = len(doc["content"].encode('utf-8')) / 1024
            print(f"  - {doc['title']} ({doc['id']}): {size_kb:.1f} KB")
        
        # Step 2: Initialize all chunking strategies
        print_separator("2. INITIALIZING CHUNKING STRATEGIES")
        
        # Standard chunk size for all strategies
        chunk_size = 150
        
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size),
            "paragraph": ParagraphChunker(max_chunk_size=chunk_size),
            "semantic": SemanticChunker(max_chunk_size=chunk_size),
            "hybrid": HybridChunker(max_chunk_size=chunk_size)
        }
        
        print(f"Initialized {len(strategies)} chunking strategies with chunk size {chunk_size}")
        for name, strategy in strategies.items():
            print(f"  - {name.capitalize()} Strategy: {strategy.__class__.__name__}")
        
        # Step 3: Compare chunking strategies
        print_separator("3. COMPARING CHUNKING STRATEGIES")
        
        # Performance monitor for comparison
        monitor = PerformanceMonitor()
        
        # Store results
        strategy_results = {}
        all_strategy_chunks = {}
        
        # Process each strategy
        for name, strategy in strategies.items():
            print(f"\nTesting {name.capitalize()} Strategy...")
            
            # Start monitoring
            monitor.start_monitoring(name)
            
            # Process each document
            start_time = time.time()
            all_chunks = []
            
            for doc in docs:
                print(f"  Processing {doc['title']}...")
                chunks = strategy.chunk_text(
                    doc["content"], 
                    doc["id"], 
                    doc["title"]
                )
                all_chunks.extend(chunks)
            
            # End timing
            elapsed_time = time.time() - start_time
            
            # Store chunk results
            all_strategy_chunks[name] = all_chunks
            
            # Calculate metrics
            total_chunks = len(all_chunks)
            total_tokens = sum(chunk.metadata.tokens or 0 for chunk in all_chunks)
            avg_chunk_size = total_tokens / total_chunks if total_chunks else 0
            
            # Stop monitoring
            metrics = monitor.stop_monitoring(
                total_chunks=total_chunks,
                total_tokens=total_tokens,
                avg_chunk_size=avg_chunk_size
            )
            
            # Store results
            strategy_results[name] = {
                "time": elapsed_time,
                "total_chunks": total_chunks,
                "chunks_per_doc": total_chunks / len(docs),
                "tokens_per_second": metrics.tokens_per_second,
                "memory_mb": metrics.memory_usage_mb,
                "avg_chunk_size": avg_chunk_size
            }
            
            # Print summary
            print(f"  Created {total_chunks} chunks in {elapsed_time:.2f} seconds")
            print(f"  Average chunk size: {avg_chunk_size:.1f} tokens")
            print(f"  Processing speed: {metrics.tokens_per_second:.1f} tokens/second")
            
            # Show a sample chunk
            print("\n  Sample chunk:")
            print_chunk_sample(all_chunks, n=1)
        
        # Compare strategies
        print("\nStrategy Comparison:")
        comparison = monitor.compare_strategies(list(strategies.keys()))
        
        # Display results in a table
        print("\n" + "-"*80)
        print(f"{'Strategy':<15} {'Time (s)':<10} {'Chunks':<10} {'Tokens/s':<10} {'Mem (MB)':<10}")
        print("-"*80)
        
        for name in strategies.keys():
            results = strategy_results[name]
            print(f"{name.capitalize():<15} "
                  f"{results['time']:<10.2f} "
                  f"{results['total_chunks']:<10} "
                  f"{results['tokens_per_second']:<10.1f} "
                  f"{results['memory_mb']:<10.1f}")
        
        print("-"*80)
        
        # Highlight best strategy
        if "best_tokens_per_second" in comparison:
            best_strategy = comparison["best_tokens_per_second"]
            print(f"\nBest overall strategy: {best_strategy.capitalize()} "
                  f"({strategy_results[best_strategy]['tokens_per_second']:.1f} tokens/s)")
        
        # Create comparison plots
        print("\nGenerating performance comparison plots...")
        
        # Plot processing speed
        plot_chunking_comparison(
            strategy_results, 
            "tokens_per_second", 
            "Chunking Strategies: Processing Speed", 
            "Tokens per Second",
            higher_is_better=True
        )
        
        # Plot memory usage
        plot_chunking_comparison(
            strategy_results, 
            "memory_mb", 
            "Chunking Strategies: Memory Usage", 
            "Memory (MB)",
            higher_is_better=False
        )
        
        # Step 4: Content Prioritization
        print_separator("4. CONTENT PRIORITIZATION")
        
        # Use the hybrid strategy as the base
        base_strategy = strategies["hybrid"]
        
        # Create a content prioritizer
        prioritizer = ContentPrioritizer()
        prioritized_chunker = PrioritizedChunker(
            base_strategy=base_strategy,
            prioritizer=prioritizer
        )
        
        print("Processing with content prioritization...")
        prioritized_chunks = []
        
        start_time = time.time()
        for doc in docs:
            chunks = prioritized_chunker.chunk_text(
                doc["content"], 
                doc["id"], 
                doc["title"]
            )
            prioritized_chunks.extend(chunks)
        
        elapsed_time = time.time() - start_time
        
        print(f"Created {len(prioritized_chunks)} prioritized chunks in {elapsed_time:.2f} seconds")
        
        # Analyze priority distribution
        priority_scores = [
            chunk.metadata.custom_metadata.get("priority_score", 0) 
            for chunk in prioritized_chunks
        ]
        
        high_priority = sum(1 for score in priority_scores if score >= 3)
        medium_priority = sum(1 for score in priority_scores if 2 <= score < 3)
        low_priority = sum(1 for score in priority_scores if score < 2)
        
        print(f"\nPriority distribution:")
        print(f"  High priority: {high_priority} chunks")
        print(f"  Medium priority: {medium_priority} chunks")
        print(f"  Low priority: {low_priority} chunks")
        
        # Show sample high-priority chunks
        high_priority_chunks = [
            chunk for chunk in prioritized_chunks
            if chunk.metadata.custom_metadata.get("priority_score", 0) >= 3
        ]
        
        print("\nSample high-priority chunks:")
        print_chunk_sample(high_priority_chunks, n=2)
        
        # Step 5: Metadata Handling
        print_separator("5. METADATA HANDLING")
        
        # Set up metadata store
        store_path = output_dir / "chunk_store"
        metadata_mgr = MetadataManager(store_path)
        chunk_store = ChunkStore(store_path, metadata_mgr)
        
        print(f"Created chunk store at {store_path}")
        
        # Create source metadata
        source_metadata = {
            doc["id"]: SourceMetadata(
                id=doc["id"],
                title=doc["title"],
                author="Research Team",
                publication_date="2023-01-01",
                url=f"https://example.com/research/{doc['id']}",
                source_type="research",
                language="en",
                keywords=["neural networks", "deep learning", "research"],
                custom_metadata={"importance": 5}
            )
            for doc in docs
        }
        
        # Store chunks with metadata
        print("\nStoring chunks with metadata...")
        for doc in docs:
            # Get chunks from hybrid strategy
            chunks = all_strategy_chunks["hybrid"]
            doc_chunks = [c for c in chunks if c.metadata.source_id == doc["id"]]
            
            # Create a collection
            collection = ChunkCollection(
                source_id=doc["id"],
                source_metadata=source_metadata[doc["id"]],
                chunks=doc_chunks
            )
            
            # Store in the chunk store
            chunk_store.store_chunk_collection(collection)
            
            print(f"  Stored {len(doc_chunks)} chunks for {doc['title']}")
        
        # Test metadata retrieval
        print("\nRetrieving collections from store...")
        collections = chunk_store.list_collections()
        print(f"Found {len(collections)} collections")
        
        # Test searching
        print("\nSearching for chunks containing 'transformer'...")
        search_results = chunk_store.search_chunks("transformer")
        print(f"Found {len(search_results)} matching chunks")
        
        # Show a sample result
        if search_results:
            print("\nSample search result:")
            print_chunk_sample(search_results, n=1)
        
        # Metadata export
        print("\nExporting metadata to JSON...")
        metadata_file = output_dir / "chunk_metadata.json"
        collections = chunk_store.list_collections()
        
        with open(metadata_file, "w") as f:
            collection_data = []
            for collection_id in collections:
                collection = chunk_store.get_chunk_collection(collection_id)
                if collection:
                    collection_data.append({
                        "source_id": collection.source_id,
                        "source_metadata": asdict(collection.source_metadata) if collection.source_metadata else None,
                        "num_chunks": len(collection.chunks),
                        "total_tokens": sum(c.metadata.tokens or 0 for c in collection.chunks)
                    })
            
            json.dump(collection_data, f, indent=2)
        
        print(f"Metadata exported to {metadata_file}")
        
        # Step 6: Optimization and Parallel Processing
        print_separator("6. OPTIMIZATION AND PARALLEL PROCESSING")
        
        # Create an optimizer
        optimizer = ChunkingOptimizer(max_workers=4)
        
        # Create optimized strategy based on hybrid chunker
        optimized_strategy = OptimizedChunkingStrategy(
            base_strategy=strategies["hybrid"],
            optimizer=optimizer,
            use_cache=True,
            use_parallel=True
        )
        
        print("Created optimized chunking strategy")
        
        # Optimize the strategy parameters
        print("\nOptimizing chunking parameters...")
        optimization_results = optimized_strategy.optimize(
            [doc["content"] for doc in docs]
        )
        
        # Print optimization results
        if "optimal_chunk_size" in optimization_results:
            print(f"Optimal chunk size: {optimization_results['optimal_chunk_size']}")
        
        print(f"Parallel speedup: {optimization_results['parallel_speedup']:.2f}x")
        
        print("\nOptimization recommendations:")
        for recommendation in optimization_results.get("recommendations", []):
            print(f"  - {recommendation}")
        
        # Compare sequential vs. parallel processing
        print("\nComparing sequential vs. parallel processing...")
        
        # Prepare data tuples for processing
        data_tuples = [
            (doc["content"], doc["id"], doc["title"])
            for doc in docs
        ]
        
        # Sequential processing
        print("\nSequential processing:")
        start_time = time.time()
        sequential_chunks = []
        
        for text, source_id, source_title in data_tuples:
            chunks = strategies["hybrid"].chunk_text(text, source_id, source_title)
            sequential_chunks.extend(chunks)
        
        sequential_time = time.time() - start_time
        
        print(f"  Created {len(sequential_chunks)} chunks in {sequential_time:.2f} seconds")
        
        # Parallel processing
        print("\nParallel processing:")
        start_time = time.time()
        
        parallel_chunks_lists = await optimized_strategy.chunk_texts(data_tuples)
        parallel_chunks = [chunk for chunks in parallel_chunks_lists for chunk in chunks]
        
        parallel_time = time.time() - start_time
        
        print(f"  Created {len(parallel_chunks)} chunks in {parallel_time:.2f} seconds")
        print(f"  Speedup: {sequential_time / parallel_time:.2f}x")
        
        # Verify results match
        print("\nVerifying results consistency...")
        print(f"  Sequential chunks: {len(sequential_chunks)}")
        print(f"  Parallel chunks: {len(parallel_chunks)}")
        
        # Step 7: Final comparison and recommendations
        print_separator("7. SUMMARY AND RECOMMENDATIONS")
        
        print("Based on the comprehensive evaluation, here's a summary of findings:")
        
        # Determine best strategy
        best_speed_strategy = max(strategy_results.keys(), 
                                key=lambda s: strategy_results[s]["tokens_per_second"])
        
        best_memory_strategy = min(strategy_results.keys(),
                                key=lambda s: strategy_results[s]["memory_mb"])
        
        print("\n1. Chunking Strategy Selection:")
        print(f"  - Best for speed: {best_speed_strategy.capitalize()} " 
              f"({strategy_results[best_speed_strategy]['tokens_per_second']:.1f} tokens/s)")
        print(f"  - Best for memory efficiency: {best_memory_strategy.capitalize()} "
              f"({strategy_results[best_memory_strategy]['memory_mb']:.1f} MB)")
        print(f"  - Best overall balance: Hybrid (combines semantic understanding with efficiency)")
        
        print("\n2. Content Prioritization:")
        print(f"  - Identified {high_priority} high-priority chunks that should be preserved")
        print(f"  - Content prioritization ensures important information is maintained when context limits apply")
        
        print("\n3. Optimization:")
        print(f"  - Parallel processing provided a {sequential_time / parallel_time:.2f}x speedup")
        
        if "optimal_chunk_size" in optimization_results:
            print(f"  - Optimal chunk size determined to be {optimization_results['optimal_chunk_size']} tokens")
        
        print("\n4. Recommendations for large-scale processing:")
        print("  - Use the HybridChunker with OptimizedChunkingStrategy for best results")
        print("  - Enable parallel processing for datasets with multiple documents")
        print("  - Use ContentPrioritizer when processing long documents with token limits")
        print("  - Store chunks with rich metadata to enable advanced search and retrieval")
        
        # Print conclusion
        print("\nThis concludes the demonstration of the Advanced Chunking System.")
        print("The system is now ready for integration with the full Deep Deep Research pipeline.")
    
    finally:
        # Clean up
        print("\nCleaning up temporary files...")
        temp_dir.cleanup()


if __name__ == "__main__":
    # Check for required libraries and install if needed
    required_libs = {
        "matplotlib": "matplotlib",
        "numpy": "numpy",
        "psutil": "psutil"
    }
    
    for module, package in required_libs.items():
        try:
            __import__(module)
        except ImportError:
            print(f"Installing required package: {package}")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    asyncio.run(run_demo()) 