#!/usr/bin/env python3
"""
Semantic Chunking Demo

This script demonstrates the capabilities of the advanced semantic chunking
module with a real-world research text example.
"""

import sys
import logging
import json
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.chunking import SemanticChunker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_chunk_details(chunk, show_content=True):
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


def run_demo():
    """Run the semantic chunking demo."""
    # Sample research text (excerpt from a paper)
    SAMPLE_TEXT = """
# Advances in Semantic Chunking for Large Language Models

## Abstract

This paper explores advanced techniques for semantic chunking in the context of large language models. 
We present novel algorithms that effectively divide text based on semantic boundaries rather than 
arbitrary character limits. Our approach significantly improves context preservation and reduces 
information loss when processing large volumes of research data.

## 1. Introduction

Large language models (LLMs) have revolutionized natural language processing, but they still face
context window limitations. When processing extensive research documents, traditional chunking
methods often break coherent sections of text, leading to context fragmentation and reduced comprehension.

This research addresses this challenge by developing semantic-aware chunking algorithms that respect
the natural boundaries in text. By preserving semantic units, we enable more effective processing
of large research corpora with LLMs.

## 2. Background and Related Work

### 2.1 Traditional Chunking Approaches

Conventional text chunking typically relies on fixed-size divisions, often measured in tokens or characters.
While simple to implement, these approaches frequently break sentences, paragraphs, and logical sections,
creating problematic context boundaries.

Previous work by Smith et al. (2022) demonstrated that approximately 35% of information is lost when
using fixed-size chunking on scientific papers. Johnson (2023) further showed that chunking at arbitrary
points reduces model comprehension by up to 42% compared to human-segmented text.

### 2.2 Semantic Analysis in NLP

Recent advances in natural language understanding have enabled more sophisticated text analysis.
Transformer models can identify semantic relationships and topic boundaries with increasing accuracy.
These capabilities form the foundation of our semantic chunking approach.

## 3. Methodology

Our semantic chunking algorithm incorporates several key components:

1. **Boundary Detection**: We identify natural semantic boundaries in text using a combination of:
   - Section and subsection headers
   - Paragraph breaks
   - Topic shift detection
   - Discourse markers and transitional phrases

2. **Importance Scoring**: Each text segment receives an importance score based on:
   - Presence of key findings
   - Statistical data
   - Citations
   - Topic relevance to research questions

3. **Optimal Chunking**: A dynamic programming algorithm identifies the optimal chunk
   boundaries that maximize semantic coherence while respecting token limits.

## 4. Results

Our evaluations demonstrate significant improvements over baseline chunking methods:

| Metric               | Traditional Chunking | Semantic Chunking | Improvement |
|----------------------|----------------------|-------------------|-------------|
| Context Preservation | 65.3%                | 92.7%             | +27.4%      |
| Information Retrieval| 71.2%                | 88.5%             | +17.3%      |
| Model Comprehension  | 68.9%                | 89.3%             | +20.4%      |

These results were consistent across different document types and lengths, indicating
the robustness of our approach.

## 5. Discussion

The significant improvements in context preservation directly translate to better downstream
performance in research synthesis tasks. When LLMs process semantically coherent chunks,
they can more accurately capture the meaning and relationships expressed in the original text.

An interesting finding was that even with smaller context windows, models using our semantic
chunks outperformed those using larger but semantically incoherent chunks. This suggests that
semantic coherence may be more important than raw context size for certain comprehension tasks.

## 6. Conclusion

In conclusion, semantic chunking represents a substantial advancement for processing large research
documents with LLMs. By respecting the natural semantic boundaries in text, we enable more effective
information extraction and synthesis from extensive textual sources.

Future work will explore incorporating domain-specific knowledge to further improve chunking for
specialized research areas such as biomedical literature and legal documents.

## References

1. Smith, J., et al. (2022). "Information loss in fixed-size chunking of scientific literature."
   *Journal of Natural Language Processing*, 45(3), 112-128.

2. Johnson, A. (2023). "Impact of text segmentation on large language model comprehension."
   *Proceedings of the International Conference on Language Models*, 234-246.

3. Zhang, C., & Brown, D. (2022). "Semantic boundary detection in multi-topic documents."
   *Computational Linguistics Review*, 18(2), 89-103.
"""

    print("\nDEMONSTRATING SEMANTIC CHUNKING CAPABILITIES\n")
    print("This demo shows how the semantic chunker breaks down research text\n"
          "into meaningful chunks based on semantic boundaries.")
    
    # Create chunker with different configurations
    chunkers = {
        "standard": SemanticChunker(
            min_chunk_size=100,
            max_chunk_size=1000,
            overlap_strategy="semantic"
        ),
        "small_chunks": SemanticChunker(
            min_chunk_size=100,
            max_chunk_size=500,
            overlap_strategy="semantic"
        ),
        "fixed_overlap": SemanticChunker(
            min_chunk_size=100,
            max_chunk_size=1000,
            overlap_strategy="fixed"
        )
    }
    
    # Process with standard configuration
    print("\n\n" + "=" * 40)
    print("STANDARD SEMANTIC CHUNKING")
    print("=" * 40)
    
    standard_chunks = chunkers["standard"].chunk_text(
        text=SAMPLE_TEXT,
        source_id="research-paper-123",
        source_title="Advances in Semantic Chunking for LLMs"
    )
    
    print(f"\nIdentified {len(standard_chunks)} semantic chunks")
    
    # Show the first and last chunks in detail
    print("\nFirst chunk (likely contains introduction):")
    print_chunk_details(standard_chunks[0])
    
    print("\nLast chunk (likely contains conclusion):")
    print_chunk_details(standard_chunks[-1])
    
    # Show the highest importance chunk
    highest_importance = max(standard_chunks, key=lambda c: c.metadata.importance_score)
    print("\nHighest importance chunk:")
    print_chunk_details(highest_importance)
    
    # Demonstrate chunk merging
    print("\n\n" + "=" * 40)
    print("CHUNK MERGING DEMONSTRATION")
    print("=" * 40)
    
    # Create smaller chunks first
    small_chunks = chunkers["small_chunks"].chunk_text(
        text=SAMPLE_TEXT,
        source_id="research-paper-123",
        source_title="Advances in Semantic Chunking for LLMs"
    )
    
    print(f"\nCreated {len(small_chunks)} smaller chunks")
    
    # Merge chunks
    merged_chunks = chunkers["standard"].merge_chunks(small_chunks, max_size=1500)
    
    print(f"\nMerged into {len(merged_chunks)} larger chunks")
    print("\nExample of a merged chunk:")
    print_chunk_details(merged_chunks[0])
    
    # Compare chunking strategies
    print("\n\n" + "=" * 40)
    print("COMPARING CHUNKING STRATEGIES")
    print("=" * 40)
    
    results = {}
    
    for name, chunker in chunkers.items():
        chunks = chunker.chunk_text(
            text=SAMPLE_TEXT,
            source_id="research-paper-123",
            source_title="Advances in Semantic Chunking for LLMs"
        )
        
        # Collect statistics
        total_tokens = sum(c.metadata.tokens for c in chunks)
        avg_tokens = total_tokens / len(chunks)
        avg_importance = sum(c.metadata.importance_score for c in chunks) / len(chunks)
        
        results[name] = {
            "chunk_count": len(chunks),
            "avg_tokens_per_chunk": round(avg_tokens, 1),
            "avg_importance_score": round(avg_importance, 2),
            "total_tokens": total_tokens
        }
    
    # Display comparison
    print("\nComparison of chunking strategies:")
    print(json.dumps(results, indent=2))
    
    print("\nDemonstration complete!")


if __name__ == "__main__":
    run_demo() 