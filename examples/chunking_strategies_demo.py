#!/usr/bin/env python3
"""
Chunking Strategies Demo

This script demonstrates the different chunking strategies available
and compares their performance on sample research data.
"""

import sys
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Any

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.chunking import (
    Chunk,
    SemanticChunker, 
    FixedSizeChunker, 
    ParagraphChunker, 
    HybridChunker,
    ChunkType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_chunk_details(chunk: Chunk, show_content: bool = True) -> None:
    """Print detailed information about a chunk."""
    print(f"\n{'=' * 80}")
    print(f"CHUNK ID: {chunk.id}")
    print(f"Source: {chunk.metadata.source_title} (ID: {chunk.metadata.source_id})")
    print(f"Position: {chunk.metadata.chunk_index + 1} of {chunk.metadata.total_chunks}")
    print(f"Type: {chunk.metadata.chunk_type.value}")
    print(f"Size: {chunk.metadata.tokens} tokens, {chunk.metadata.characters} characters")
    print(f"Importance Score: {chunk.metadata.importance_score:.2f}")
    
    if chunk.metadata.semantic_topics:
        print(f"Topics: {', '.join(chunk.metadata.semantic_topics)}")
    
    if show_content:
        print(f"\nCONTENT:\n{'-' * 40}")
        print(chunk.content)
    
    print(f"{'=' * 80}\n")


def get_strategy_name(chunk_type: ChunkType) -> str:
    """Get a human-readable name for a chunk type."""
    names = {
        ChunkType.SEMANTIC: "Semantic",
        ChunkType.FIXED_SIZE: "Fixed Size",
        ChunkType.PARAGRAPH: "Paragraph",
        ChunkType.SENTENCE: "Sentence",
        ChunkType.HYBRID: "Hybrid",
        ChunkType.CUSTOM: "Custom"
    }
    return names.get(chunk_type, "Unknown")


def evaluate_strategy(chunker, text: str, name: str) -> Dict[str, Any]:
    """
    Evaluate a chunking strategy and return metrics.
    
    Args:
        chunker: The chunking strategy to evaluate
        text: Text to chunk
        name: Name of the strategy
        
    Returns:
        Dictionary of metrics
    """
    logger.info(f"Evaluating {name} chunking strategy...")
    
    # Measure processing time
    start_time = time.time()
    
    chunks = chunker.chunk_text(
        text=text,
        source_id=f"example-{name.lower()}",
        source_title=f"{name} Chunking Example"
    )
    
    processing_time = time.time() - start_time
    
    # Calculate metrics
    total_chunks = len(chunks)
    total_tokens = sum(chunk.metadata.tokens for chunk in chunks)
    avg_chunk_size = total_tokens / total_chunks if total_chunks > 0 else 0
    min_chunk_size = min((chunk.metadata.tokens for chunk in chunks), default=0)
    max_chunk_size = max((chunk.metadata.tokens for chunk in chunks), default=0)
    
    # Calculate size variance (uniformity of chunks)
    if total_chunks > 1:
        mean = avg_chunk_size
        variance = sum((chunk.metadata.tokens - mean) ** 2 for chunk in chunks) / total_chunks
        size_stddev = variance ** 0.5
    else:
        size_stddev = 0
    
    return {
        "name": name,
        "total_chunks": total_chunks,
        "total_tokens": total_tokens,
        "avg_chunk_size": round(avg_chunk_size, 1),
        "min_chunk_size": min_chunk_size,
        "max_chunk_size": max_chunk_size,
        "size_stddev": round(size_stddev, 1),
        "processing_time_ms": round(processing_time * 1000, 2),
        "chunks": chunks
    }


def run_demo() -> None:
    """Run the chunking strategies demo."""
    print("\nCHUNKING STRATEGIES COMPARISON DEMO\n")
    print("This demo compares different chunking strategies on sample research text")
    
    # Load sample research text
    # Use the same text as in the semantic chunking demo but truncated for brevity
    SAMPLE_TEXT = """
# Advanced Chunking Algorithms for Research Synthesis

## Abstract

This paper presents novel chunking algorithms designed for large-scale research 
synthesis applications. Our approach efficiently processes hundreds of sources 
while preserving semantic meaning and context. We compare fixed-size, paragraph-based, 
and semantic chunking strategies against a new hybrid approach.

## 1. Introduction

Processing large volumes of research papers poses significant challenges for 
AI-assisted synthesis systems. Traditional chunking methods often fragment 
semantic units, leading to reduced comprehension and synthesis quality. We address 
this challenge by developing strategies that respect natural semantic boundaries.

Our contributions include:
- A comprehensive analysis of existing chunking methods
- A novel hybrid chunking strategy for research documents
- Quantitative and qualitative evaluation of chunking impact on synthesis quality

## 2. Related Work

### 2.1 Fixed-Size Chunking

The most straightforward approach divides text into equal-sized segments. While simple 
to implement, this method often breaks semantic units, cutting off sentences or 
paragraphs mid-stream, leading to context loss.

Zhang et al. (2022) demonstrated that up to 37% of fixed-size chunks contained 
broken sentences, resulting in a 28% reduction in comprehension accuracy.

### 2.2 Paragraph-Based Chunking

Paragraph-based strategies respect paragraph boundaries while managing chunk size.
This preserves local coherence but may still break topical sections that span
multiple paragraphs.

### 2.3 Semantic Chunking

Recent advances in semantic analysis have enabled chunk boundaries based on 
topic shifts and semantic units. Ramakrishnan and Lewis (2020) showed that 
semantic chunking improved downstream tasks by 23% compared to fixed-size methods.

## 3. Methodology

Our hybrid chunking algorithm combines semantic awareness with practical size 
constraints. It incorporates:

1. Boundary detection using:
   - Section and subsection headers
   - Paragraph breaks
   - Topic shifts identified through semantic analysis
   - Discourse markers and transitional phrases

2. Hierarchical chunking that follows document structure
3. Adaptive size management to handle content of varying densities
4. Content prioritization for importance-based chunking

The algorithm dynamically selects the most appropriate strategy based on 
content characteristics.

## 4. Experimental Setup

We evaluated our chunking strategies using:

- 500 research papers from various scientific domains
- 1,000 technical reports and documentation files
- 200 textbooks and educational materials

Each source was processed with four chunking strategies:
1. Fixed-size (800 tokens)
2. Paragraph-based
3. Semantic-aware
4. Our hybrid approach

Metrics included:
- Processing efficiency (time and resources)
- Semantic coherence of chunks
- Information preservation
- Impact on downstream tasks

## 5. Results

Our experiments demonstrate the following key findings:

| Metric | Fixed-Size | Paragraph | Semantic | Hybrid |
|--------|------------|-----------|----------|--------|
| Processing Time (relative) | 1.0× | 1.2× | 2.5× | 1.8× |
| Semantic Coherence (0-10) | 5.2 | 7.8 | 9.1 | 8.9 |
| Information Preservation (%) | 68% | 82% | 93% | 91% |
| Downstream Performance (%) | 72% | 84% | 92% | 90% |

The hybrid approach achieved 98% of the semantic chunker's quality while 
being 28% more efficient to compute.

## 6. Discussion

The results demonstrate clear tradeoffs between chunking strategies. Fixed-size 
chunking excels in simplicity and performance but suffers in semantic coherence.
Semantic chunking produces the highest quality output but at significant 
computational cost. Our hybrid approach balances these concerns effectively.

An unexpected finding was the impact of chunking strategy on very long documents
with complex hierarchical structure. In these cases, the hybrid approach 
actually outperformed pure semantic chunking by better handling nested 
hierarchies.

## 7. Conclusion

Effective chunking is essential for processing large research corpora. We've 
demonstrated that hybrid approaches can achieve near-optimal quality with
reasonable computational requirements. This enables more effective research
synthesis systems that maintain semantic coherence while scaling to hundreds
of sources.

Future work will explore domain-specific adaptations and further optimizations
for specialized content types.

## References

1. Zhang, J., et al. (2022). "Impact of text segmentation on language model comprehension."
   *Natural Language Engineering Journal*, 28(3), 112-128.

2. Ramakrishnan, K., & Lewis, M. (2020). "Semantic-aware text chunking for effective
   document analysis." *Proceedings of the Conference on AI for Document Processing*, 234-246.
"""
    
    # Define chunking parameters for fair comparison
    MAX_CHUNK_SIZE = 600  # Maximum tokens per chunk for all strategies
    
    # Initialize chunkers with comparable configurations
    chunkers = {
        "Semantic": SemanticChunker(
            max_chunk_size=MAX_CHUNK_SIZE,
            min_chunk_size=MAX_CHUNK_SIZE // 3,
            overlap_strategy="semantic"
        ),
        "Fixed-Size": FixedSizeChunker(
            chunk_size=MAX_CHUNK_SIZE,
            overlap=100,
            by_tokens=True
        ),
        "Paragraph": ParagraphChunker(
            max_chunk_size=MAX_CHUNK_SIZE,
            min_chunk_size=MAX_CHUNK_SIZE // 3
        ),
        "Hybrid": HybridChunker(
            max_chunk_size=MAX_CHUNK_SIZE,
            min_chunk_size=MAX_CHUNK_SIZE // 3,
            prefer_semantic=True
        )
    }
    
    # Evaluate each strategy
    results = {}
    for name, chunker in chunkers.items():
        results[name] = evaluate_strategy(chunker, SAMPLE_TEXT, name)
    
    # Display comparison
    print("\n" + "=" * 40)
    print("CHUNKING STRATEGIES COMPARISON")
    print("=" * 40 + "\n")
    
    # Create comparison table
    print(f"{'Strategy':<12} | {'Chunks':<6} | {'Avg Size':<8} | {'Min Size':<8} | {'Max Size':<8} | {'StdDev':<7} | {'Time (ms)':<9}")
    print(f"{'-' * 12} | {'-' * 6} | {'-' * 8} | {'-' * 8} | {'-' * 8} | {'-' * 7} | {'-' * 9}")
    
    for name, result in results.items():
        print(f"{name:<12} | {result['total_chunks']:<6} | {result['avg_chunk_size']:<8} | {result['min_chunk_size']:<8} | {result['max_chunk_size']:<8} | {result['size_stddev']:<7} | {result['processing_time_ms']:<9}")
    
    print("\n")
    
    # Display chunk examples
    for name, result in results.items():
        print(f"\n{name.upper()} CHUNKING EXAMPLE")
        print(f"{'-' * 40}")
        
        if result['chunks']:
            # Find a representative chunk that contains a section header
            header_chunk = None
            for chunk in result['chunks']:
                if "##" in chunk.content:
                    header_chunk = chunk
                    break
            
            # If no chunk with header, just take the first one
            example_chunk = header_chunk or result['chunks'][0]
            print_chunk_details(example_chunk)
    
    # Test hybrid adaptability with a challenging document
    print("\n" + "=" * 40)
    print("HYBRID CHUNKER ADAPTABILITY TEST")
    print("=" * 40 + "\n")
    
    # Create a challenging document with varied structure
    CHALLENGING_TEXT = """
# Document with challenging structure

## Very short section
Just a quick note.

## Extremely long section with minimal paragraph breaks
""" + "This is a very long paragraph with no clear semantic boundaries. " * 100 + """

## Mixed section
This section has multiple paragraphs.

The paragraphs vary in length and content.

Some are short.

Some are longer and contain more detailed information about the topic.

### Subsection with list
- Item 1 with some explanation
- Item 2 with some explanation
- Item 3 with some explanation

## Final section
Concluding thoughts.
"""
    
    # Process with hybrid chunker
    hybrid_result = evaluate_strategy(chunkers["Hybrid"], CHALLENGING_TEXT, "Hybrid (Challenging)")
    
    print(f"\nHybrid chunker created {hybrid_result['total_chunks']} chunks from the challenging document")
    print(f"Average chunk size: {hybrid_result['avg_chunk_size']} tokens")
    print(f"Size standard deviation: {hybrid_result['size_stddev']}")
    
    # Display a couple of examples
    if hybrid_result['chunks']:
        print("\nExample chunks from challenging document:")
        
        # Print first and middle chunks
        if len(hybrid_result['chunks']) > 0:
            print("\nFirst chunk:")
            print_chunk_details(hybrid_result['chunks'][0])
        
        if len(hybrid_result['chunks']) > 2:
            middle_idx = len(hybrid_result['chunks']) // 2
            print("\nMiddle chunk (from long section):")
            print_chunk_details(hybrid_result['chunks'][middle_idx])
    
    print("\nDemonstration complete!")


if __name__ == "__main__":
    run_demo() 