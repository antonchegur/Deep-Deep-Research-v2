#!/usr/bin/env python3
"""
Advanced Synthesis Demo - Demonstrates the enhanced GPT-4 Turbo integration.

This example shows how to use the GPT-4 Turbo synthesizer with error handling,
retry mechanism, and fallback functionality for research synthesis.

Usage:
    python advanced_synthesis_demo.py

Requirements:
    - Set OPENAI_API_KEY in environment variables or .env file
    - Install required packages from requirements.txt
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.research.adapters import SourceType, SourceResult
from src.research.synthesizer import GPT4Synthesizer, SynthesisType


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("advanced_synthesis_demo")


# Sample research data
SAMPLE_SOURCE_RESULTS = [
    SourceResult(
        title="Climate Change: Evidence and Causes",
        content="""Climate change is the long-term alteration of temperature and typical weather patterns.
        Evidence for climate change includes rising global temperatures, warming oceans, shrinking ice sheets,
        glacial retreat, decreased snow cover, sea level rise, declining Arctic sea ice, extreme weather events,
        and ocean acidification. The primary cause is human activities, particularly the burning of fossil fuels,
        which increases heat-trapping greenhouse gas levels in Earth's atmosphere.""",
        source="Scientific Source",
        source_type=SourceType.WEBSITE,
        url="https://example.com/climate-evidence",
        metadata={"year": 2023, "credibility": "high"}
    ),
    SourceResult(
        title="Effects of Climate Change",
        content="""The effects of climate change include rising sea levels, increased frequency and severity of 
        extreme weather events such as hurricanes, floods, and droughts, shifts in plant and animal ranges, 
        and more severe heat waves. These changes affect agriculture, water supplies, human health, infrastructure, 
        and ecosystems. Vulnerable populations, particularly in developing countries, face the most severe impacts 
        despite contributing the least to greenhouse gas emissions.""",
        source="Research Journal",
        source_type=SourceType.ACADEMIC,
        url="https://example.org/climate-effects",
        metadata={"year": 2024, "peer_reviewed": True}
    ),
]


async def run_synthesis_demo():
    """Run the advanced synthesis demo."""
    logger.info("Starting advanced GPT-4 synthesis demo...")
    
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OPENAI_API_KEY found in environment variables or .env file.")
        logger.error("Please set the API key and try again.")
        return
    
    # Initialize the GPT-4 synthesizer with enhanced options
    synthesizer = GPT4Synthesizer(
        api_key=api_key,
        model="gpt-4o",  # Primary model
        temperature=0.3,
        max_tokens=2000,
        timeout=60,
        max_retries=3,
        retry_delay=2,
        fallback_model="gpt-3.5-turbo"  # Fallback model if primary fails
    )
    
    logger.info(f"Initialized synthesizer with model: {synthesizer.model}")
    logger.info(f"Fallback model if needed: {synthesizer.fallback_model}")
    
    # Research query
    query = "Summarize the evidence for climate change and its effects"
    
    # Try different synthesis types
    for synthesis_type in [SynthesisType.SUMMARY, SynthesisType.COMPREHENSIVE]:
        try:
            logger.info(f"Performing {synthesis_type.value} synthesis...")
            
            # Run the synthesis
            start_time = datetime.now()
            
            result = await synthesizer.synthesize(
                query=query,
                source_results=SAMPLE_SOURCE_RESULTS,
                synthesis_type=synthesis_type,
                language="en"
            )
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            if result:
                logger.info(f"Synthesis successful! Completed in {elapsed_time:.2f} seconds")
                logger.info(f"Title: {result.title}")
                logger.info(f"Sources used: {result.sources_used}")
                
                # Save the result to a file
                output_file = f"synthesis_{synthesis_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, "w") as f:
                    json.dump(result.to_dict(), f, indent=2)
                
                logger.info(f"Results saved to {output_file}")
                
                # Display a preview of the content
                content_preview = result.content[:500] + "..." if len(result.content) > 500 else result.content
                logger.info(f"Content preview:\n{content_preview}")
            else:
                logger.error("Synthesis returned no results.")
                
        except Exception as e:
            logger.error(f"Error during {synthesis_type.value} synthesis: {e}")
    
    # Try custom synthesis
    try:
        logger.info("Performing custom synthesis with specialized prompt...")
        
        custom_prompt = """You are a climate science educator preparing material for high school students.
        Create a clear, educational summary that:
        1. Explains climate change in simple terms
        2. Presents the key evidence in an engaging way
        3. Discusses the main effects on our planet
        4. Includes 2-3 simple actions students can take
        
        Use straightforward language appropriate for teenagers and organize the information
        in a way that builds understanding step by step.
        """
        
        # Run the custom synthesis
        result = await synthesizer.custom_synthesis(
            query=query,
            source_results=SAMPLE_SOURCE_RESULTS,
            custom_prompt=custom_prompt,
            language="en"
        )
        
        if result:
            logger.info("Custom synthesis successful!")
            logger.info(f"Title: {result.title}")
            
            # Save the result to a file
            output_file = f"synthesis_custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, "w") as f:
                json.dump(result.to_dict(), f, indent=2)
            
            logger.info(f"Results saved to {output_file}")
            
            # Display a preview of the content
            content_preview = result.content[:500] + "..." if len(result.content) > 500 else result.content
            logger.info(f"Content preview:\n{content_preview}")
        else:
            logger.error("Custom synthesis returned no results.")
            
    except Exception as e:
        logger.error(f"Error during custom synthesis: {e}")
    
    logger.info("Advanced synthesis demo completed!")


if __name__ == "__main__":
    asyncio.run(run_synthesis_demo()) 