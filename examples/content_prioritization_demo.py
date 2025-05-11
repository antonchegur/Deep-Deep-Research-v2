#!/usr/bin/env python3
"""
Content Prioritization Demo

This script demonstrates the content prioritization capabilities of the
chunking system, showing how it identifies and preserves high-value content.
"""

import sys
import logging
import json
from pathlib import Path
import time

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.chunking import (
    Chunk, ChunkMetadata, ChunkType, 
    SemanticChunker, HybridChunker, 
    ParagraphChunker, FixedSizeChunker
)
from src.chunking.content_prioritization import (
    ContentPriority, ContentPrioritizer, PrioritizedChunker
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_chunk_details(chunk, show_content=True, show_priority=True):
    """Print detailed information about a chunk."""
    print(f"\n{'=' * 80}")
    print(f"CHUNK ID: {chunk.id}")
    print(f"Source: {chunk.metadata.source_title} (ID: {chunk.metadata.source_id})")
    print(f"Position: {chunk.metadata.chunk_index + 1} of {chunk.metadata.total_chunks}")
    print(f"Type: {chunk.metadata.chunk_type.value}")
    print(f"Size: {chunk.metadata.tokens} tokens, {chunk.metadata.characters} characters")
    print(f"Importance Score: {chunk.metadata.importance_score:.2f}")
    
    if show_priority and 'priority_level' in chunk.metadata.custom_data:
        print(f"Priority Level: {chunk.metadata.custom_data['priority_level']}")
        print("Priority Factors:")
        for factor, score in chunk.metadata.custom_data.get('priority_factors', {}).items():
            print(f"  - {factor}: {score:.2f}")
    
    if chunk.metadata.semantic_topics:
        print(f"Topics: {', '.join(chunk.metadata.semantic_topics)}")
    
    if show_content:
        print(f"\nCONTENT:\n{'-' * 40}")
        print(chunk.content)
    
    print(f"{'=' * 80}\n")


def run_demo():
    """Run the content prioritization demo."""
    print("\nCONTENT PRIORITIZATION DEMO\n")
    print("This demo demonstrates how the system identifies and prioritizes important content")
    print("in research papers, ensuring that critical information is preserved during chunking.")
    
    # Sample research text
    SAMPLE_TEXT = """
# Impact of Advanced Chunking Techniques on Information Retrieval

## Abstract

This study evaluates the effect of various chunking strategies on information retrieval 
accuracy and completeness. We compare fixed-size, paragraph-based, semantic, and priority-aware 
chunking approaches across a dataset of 500 research papers. Our findings demonstrate that 
priority-aware chunking improves retrieval accuracy by 37% (p < 0.01) compared to baseline methods.

## 1. Introduction

Large language models have revolutionized research synthesis, but their effectiveness 
depends heavily on how source documents are processed and chunked. Traditional fixed-size 
chunking often fragments key information, leading to information loss and reduced comprehension.

The research questions this study addresses include:
1. How do different chunking strategies affect information retrieval accuracy?
2. What impact does preserving semantic coherence have on synthesis quality?
3. Can automated content prioritization improve research synthesis outcomes?

## 2. Methodology

### 2.1 Experimental Design

We conducted a comparative analysis using a dataset of 500 research papers from diverse 
academic fields. Each paper was processed using four chunking strategies:

1. Fixed-size (500 tokens)
2. Paragraph-based
3. Semantic-aware 
4. Priority-aware (our proposed approach)

The priority-aware approach identifies high-value content using:
- Statistical significance markers (p-values, effect sizes)
- Citation density
- Key finding phrases
- Location heuristics (e.g., abstract, conclusion sections)

### 2.2 Evaluation Metrics

Performance was evaluated using:
- Information retrieval accuracy (percentage of key facts preserved)
- Context coherence (rated by human evaluators)
- Synthesis quality (comparison with human-generated summaries)
- Processing efficiency (time and computational resources)

## 3. Results

### 3.1 Information Retrieval

Priority-aware chunking demonstrated superior performance in preserving key information.
Table 1 shows the percentage of critical facts retrieved by each method:

| Chunking Method  | Critical Facts Retrieved | Relative Improvement |
|------------------|--------------------------|----------------------|
| Fixed-size       | 68%                      | Baseline             |
| Paragraph-based  | 79%                      | +16%                 |
| Semantic-aware   | 85%                      | +25%                 |
| Priority-aware   | 93%                      | +37%                 |

Statistical analysis confirms these differences are significant (χ² = 28.4, p < 0.01).

### 3.2 Impact on Synthesis Quality

Synthesis quality scores (evaluated by domain experts on a scale of 1-10):

- Fixed-size: 6.2 ± 0.8
- Paragraph-based: 7.1 ± 0.7
- Semantic-aware: 7.8 ± 0.6
- Priority-aware: 8.5 ± 0.5

The priority-aware approach resulted in synthesized documents that most closely 
resembled expert-created summaries (similarity score = 0.87).

## 4. Discussion

The significant improvement in information retrieval accuracy (37%) when using 
priority-aware chunking demonstrates the importance of content prioritization
in research synthesis tasks. Particularly notable was the system's ability to
maintain context around statistical findings and key conclusions, which are
often fragmented by other approaches.

One limitation is the increased computational overhead (approximately 15% more
processing time compared to fixed-size chunking). However, this tradeoff is
justified by the substantial quality improvements for applications where
accuracy is critical.

## 5. Conclusion

This study demonstrates that content prioritization is a crucial factor in effective
research synthesis. The priority-aware chunking approach significantly outperforms
traditional methods in preserving critical information while maintaining context.

Future work should focus on domain-specific prioritization strategies and further
optimization of the computational efficiency.

## References

1. Smith, J., et al. (2022). "Advanced text processing for research synthesis."
   *Journal of Information Retrieval*, 45(3), 112-128.

2. Johnson, A. (2023). "Semantic preservation in document processing."
   *Computational Linguistics Review*, 18(2), 89-103.
"""
    
    print("\nInitializing content prioritizer...")
    prioritizer = ContentPrioritizer()
    
    # Analyze the document by sections to demonstrate prioritization
    print("\n" + "=" * 40)
    print("SECTION-BY-SECTION ANALYSIS")
    print("=" * 40)
    
    # Extract sections
    sections = {}
    current_section = "Header"
    current_content = []
    
    for line in SAMPLE_TEXT.split("\n"):
        if line.strip().startswith("# "):
            # Save previous section
            if current_content:
                sections[current_section] = "\n".join(current_content)
            # Start new section
            current_section = line.strip()[2:]
            current_content = [line]
        elif line.strip().startswith("## "):
            # Save previous section
            if current_content:
                sections[current_section] = "\n".join(current_content)
            # Start new subsection
            current_section = line.strip()[3:]
            current_content = [line]
        else:
            current_content.append(line)
    
    # Add the last section
    if current_content:
        sections[current_section] = "\n".join(current_content)
    
    # Analyze each section
    section_scores = {}
    for section_name, content in sections.items():
        if len(content.strip()) > 0:
            print(f"\nAnalyzing section: {section_name}")
            score = prioritizer.prioritize_text(content, section_name)
            section_scores[section_name] = score
            
            print(f"Priority Level: {score.priority_level.name}")
            print(f"Raw Score: {score.raw_score:.2f}")
            print("Contributing Factors:")
            for factor, value in score.factors.items():
                print(f"  - {factor}: {value:.2f}")
    
    # Sort sections by priority
    sorted_sections = sorted(
        section_scores.items(), 
        key=lambda x: x[1].raw_score, 
        reverse=True
    )
    
    print("\n" + "=" * 40)
    print("HIGHEST PRIORITY SECTIONS")
    print("=" * 40)
    
    for i, (section, score) in enumerate(sorted_sections[:3]):
        print(f"\n{i+1}. {section} (Score: {score.raw_score:.2f}, Level: {score.priority_level.name})")
    
    # Demonstrate chunking with and without prioritization
    print("\n" + "=" * 40)
    print("COMPARING STANDARD VS. PRIORITY-AWARE CHUNKING")
    print("=" * 40)
    
    # Create standard chunkers
    chunkers = {
        "semantic": SemanticChunker(max_chunk_size=300),
        "paragraph": ParagraphChunker(max_chunk_size=300),
        "fixed": FixedSizeChunker(chunk_size=300)
    }
    
    # Create prioritized versions
    prioritized_chunkers = {
        f"prioritized_{name}": PrioritizedChunker(chunker, prioritizer)
        for name, chunker in chunkers.items()
    }
    
    # Process with each chunker
    results = {}
    
    for name, chunker in {**chunkers, **prioritized_chunkers}.items():
        print(f"\nProcessing with {name} chunker...")
        start_time = time.time()
        
        chunks = chunker.chunk_text(
            text=SAMPLE_TEXT,
            source_id=f"demo-{name}",
            source_title="Chunking Techniques Study"
        )
        
        processing_time = time.time() - start_time
        
        # Calculate metrics
        high_priority_chunks = sum(
            1 for c in chunks 
            if c.metadata.custom_data.get('priority_level') in 
            [ContentPriority.CRITICAL.name, ContentPriority.HIGH.name]
        ) if 'prioritized' in name else 0
        
        avg_importance = sum(c.metadata.importance_score for c in chunks) / len(chunks)
        
        results[name] = {
            "chunks": chunks,
            "chunk_count": len(chunks),
            "high_priority_count": high_priority_chunks,
            "avg_importance": round(avg_importance, 2),
            "processing_time_ms": round(processing_time * 1000, 2)
        }
    
    # Compare results
    print("\n" + "=" * 40)
    print("CHUNKING STRATEGY COMPARISON")
    print("=" * 40 + "\n")
    
    # Print comparison table
    print(f"{'Strategy':<20} | {'Chunks':<6} | {'High Priority':<12} | {'Avg Importance':<14} | {'Time (ms)':<9}")
    print(f"{'-' * 20} | {'-' * 6} | {'-' * 12} | {'-' * 14} | {'-' * 9}")
    
    for name, result in results.items():
        print(f"{name:<20} | {result['chunk_count']:<6} | {result['high_priority_count']:<12} | {result['avg_importance']:<14} | {result['processing_time_ms']:<9}")
    
    # Show highest importance chunk from prioritized semantic chunker
    print("\n" + "=" * 40)
    print("HIGHEST PRIORITY CHUNK EXAMPLE")
    print("=" * 40)
    
    prioritized_chunks = results.get("prioritized_semantic", {}).get("chunks", [])
    if prioritized_chunks:
        highest_importance = max(prioritized_chunks, key=lambda c: c.metadata.importance_score)
        print_chunk_details(highest_importance)
    
    # Show a regular vs. prioritized chunk containing the same content
    print("\n" + "=" * 40)
    print("REGULAR VS. PRIORITIZED CHUNKING COMPARISON")
    print("=" * 40)
    
    # Try to find a results section in both versions
    reg_results_chunk = None
    pri_results_chunk = None
    
    for chunk in results.get("semantic", {}).get("chunks", []):
        if "Results" in chunk.content or "results" in chunk.content:
            reg_results_chunk = chunk
            break
    
    for chunk in results.get("prioritized_semantic", {}).get("chunks", []):
        if "Results" in chunk.content or "results" in chunk.content:
            pri_results_chunk = chunk
            break
    
    if reg_results_chunk and pri_results_chunk:
        print("\nREGULAR SEMANTIC CHUNKING:")
        print_chunk_details(reg_results_chunk)
        
        print("\nPRIORITIZED SEMANTIC CHUNKING:")
        print_chunk_details(pri_results_chunk)
    
    print("\nDemonstration complete!")


if __name__ == "__main__":
    run_demo() 