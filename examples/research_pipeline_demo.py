#!/usr/bin/env python
"""
Demo script for the Deep Deep Research v2 pipeline.

This example shows how to use the unified research pipeline API
to conduct research across multiple sources and synthesize results.

Prerequisites:
- API keys for OpenAI should be set in environment variables
- Dependencies installed: httpx, beautifulsoup4, lxml
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from pprint import pprint
import logging
from dotenv import load_dotenv

# Add the parent directory to the Python path so we can import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
load_dotenv()

from src.research.adapters import SourceConfig, SourceType
from src.research.manager import SourceManager
from src.research.synthesizer import GPT4Synthesizer, SynthesisType
from src.research.pipeline import ResearchPipeline


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("research_demo")


async def run_demo():
    """Run the research pipeline demo."""
    
    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OpenAI API key not found in environment variables.")
        logger.error("Please set the OPENAI_API_KEY environment variable.")
        return
    
    logger.info("Initializing research pipeline...")
    
    # Configure source adapters
    source_configs = {
        "wikipedia": SourceConfig(
            enabled=True,
            timeout_seconds=10,
            max_results=3,
        ),
        "duckduckgo": SourceConfig(
            enabled=True,
            timeout_seconds=15,
            max_results=5,
        ),
        "arxiv": SourceConfig(
            enabled=True,
            timeout_seconds=10,
            max_results=3,
        ),
        "openai_search": SourceConfig(
            enabled=True,
            timeout_seconds=20,
            max_results=3,
            api_key=os.environ.get("OPENAI_API_KEY"),
        ),
    }
    
    # Create source manager with configs
    source_manager = SourceManager(source_configs)
    
    # Create GPT-4 synthesizer
    synthesizer = GPT4Synthesizer(
        api_key=os.environ.get("OPENAI_API_KEY"),
        temperature=0.3,
        max_tokens=4000,
    )
    
    # Create unified research pipeline
    pipeline = ResearchPipeline(
        source_manager=source_manager,
        synthesizer=synthesizer,
    )
    
    # Example research queries
    queries = [
        {
            "query": "What are the latest developments in quantum computing?",
            "depth": "standard",
            "synthesis_type": SynthesisType.LATEST_RESEARCH,
        },
        {
            "query": "Compare the effectiveness of mRNA vaccines versus traditional vaccines",
            "depth": "deep",
            "synthesis_type": SynthesisType.COMPARISON,
        },
        {
            "query": "Summarize the evidence for climate change",
            "depth": "quick",
            "synthesis_type": SynthesisType.SUMMARY,
        },
    ]
    
    # Select one query to run
    selected_query = queries[2]  # Change index to run different queries
    
    logger.info(f"Research query: {selected_query['query']}")
    logger.info(f"Research depth: {selected_query['depth']}")
    logger.info(f"Synthesis type: {selected_query['synthesis_type'].value}")
    
    try:
        # Run search step only first to debug
        logger.info("Step 1: Performing search...")
        search_results = await source_manager.search(
            query=selected_query['query'],
            depth=selected_query['depth'],
            language="en"
        )
        
        logger.info(f"Found {len(search_results)} search results")
        
        # Print the first few search results
        for i, result in enumerate(search_results[:3]):
            logger.info(f"Search result {i+1}:")
            logger.info(f"  Title: {result.title}")
            logger.info(f"  Source: {result.source_name}")
            logger.info(f"  Type: {result.source_type}")
            logger.info(f"  URL: {result.url}")
            
        # Step 2: Get content for the top search results
        logger.info("\nStep 2: Retrieving content...")
        identifiers = []
        for result in search_results[:5]:
            # For Wikipedia and arXiv, use URL as identifier
            if result.source_type in [SourceType.WIKIPEDIA, SourceType.ACADEMIC] and result.url:
                identifiers.append((result.url, result.source_type))
                logger.info(f"Using URL as identifier for {result.source_type}: {result.url}")
            # For other sources or if URL is missing, use title
            elif result.title:
                identifiers.append((result.title, result.source_type))
                logger.info(f"Using title as identifier for {result.source_type}: {result.title}")
        
        content_results = await source_manager.get_content(
            identifiers=identifiers,
            depth=selected_query['depth'],
            language="en"
        )
        
        logger.info(f"Retrieved {len(content_results)} content items")
        
        # Print the first few content results
        for i, result in enumerate(content_results[:2]):
            logger.info(f"Content result {i+1}:")
            logger.info(f"  Title: {result.title}")
            logger.info(f"  Source: {result.source_name}")
            logger.info(f"  Type: {result.source_type}")
            logger.info(f"  Content length: {len(result.content)} characters")
        
        # Step 3: Run the full pipeline
        logger.info("\nStep 3: Running full research pipeline...")
        
        result = await pipeline.research(
            query=selected_query['query'],
            depth=selected_query['depth'],
            synthesis_type=selected_query['synthesis_type'],
            language="en",
            max_sources_to_analyze=6,
        )
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"research_result_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Research complete! Results saved to {filename}")
        
        # Print synthesis information
        if result["synthesis"]:
            print("\n" + "=" * 80)
            print(f"TITLE: {result['synthesis']['title']}")
            print("=" * 80)
            
            if result["synthesis"]["sections"]:
                # Print each section
                for section_title, section_content in result["synthesis"]["sections"].items():
                    print(f"\n## {section_title}")
                    print(f"{section_content[:500]}...")
            else:
                # Print beginning of content if no sections
                print(f"\n{result['synthesis']['content'][:1000]}...\n")
            
            print(f"\nSources used: {result['metadata']['sources_analyzed']}")
            print(f"Total sources found: {result['metadata']['total_sources_found']}")
        else:
            logger.warning("No synthesis was produced.")
            
    except Exception as e:
        logger.error(f"Error during research: {e}", exc_info=True)


def main():
    """Main entry point."""
    asyncio.run(run_demo())


if __name__ == "__main__":
    main() 