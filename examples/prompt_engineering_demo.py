#!/usr/bin/env python3
"""
Prompt Engineering Demo - Demonstrates how to use the prompt engineering framework.

This example shows how to:
1. Create and manage prompt templates
2. Use the PromptLibrary and PromptEvaluator
3. Customize prompts for specific research tasks
4. Compare effectiveness of different prompt templates

Usage:
    python prompt_engineering_demo.py

Requirements:
    - Set OPENAI_API_KEY in environment variables or .env file
    - Install required packages from requirements.txt
"""

import os
import sys
import json
import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.research.adapters import SourceType, SourceResult
from src.research.synthesizer import GPT4Synthesizer, SynthesisType
from src.research.synthesizer.prompt_engineering import (
    PromptTemplate, 
    PromptLibrary, 
    PromptEvaluator
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("prompt_engineering_demo")


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


def create_custom_template() -> PromptTemplate:
    """Create a custom prompt template for educational content."""
    
    system_template = """
    You are an expert educator creating clear, engaging content for {{audience}} students.
    
    Your task is to create educational material that:
    1. Explains complex topics in accessible language
    2. Provides clear examples and illustrations
    3. Connects the topic to real-world implications
    4. Includes reflection questions or discussion points
    
    Topic: {{query}}
    Target audience: {{audience}}
    Target language: {{language}}
    """
    
    user_template = """
    Research Query: {{query}}
    
    Sources:
    {{sources}}
    
    Based on these sources, please create educational content for {{audience}} students.
    Focus particularly on making the content engaging and relevant to their interests and needs.
    Use {{language}} language for your response.
    """
    
    template = PromptTemplate(
        template_id="educational_content",
        system_template=system_template,
        user_template=user_template,
        version="1.0.0",
        description="Template for creating educational content for students",
        parameters={
            "query": "Research query or topic",
            "sources": "Formatted source data",
            "language": "Target language for the response",
            "audience": "Target student audience (e.g., high school, college)"
        },
        metadata={
            "creator": "Research Team",
            "purpose": "Educational content creation",
            "recommended_models": ["gpt-4o", "gpt-4-turbo"]
        }
    )
    
    return template


async def setup_prompt_library():
    """Set up prompt library with custom templates."""
    
    # Create the templates directory if it doesn't exist
    templates_dir = Path("data/prompt_templates")
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize the prompt library
    prompt_library = PromptLibrary(templates_dir=str(templates_dir))
    
    # Create and add custom template
    educational_template = create_custom_template()
    prompt_library.add_template(educational_template)
    
    # Create and add a specialized fact-check template
    fact_check_template = PromptTemplate(
        template_id="research_fact_check",
        system_template="""
        You are an expert fact-checker analyzing evidence from multiple sources.
        Your primary goal is to present a balanced, accurate assessment of claims.
        
        For each major claim, provide:
        1. Clear statement of the claim
        2. Evidence assessment (supporting and contradicting)
        3. Confidence rating (High, Medium, Low)
        4. Context and nuance
        
        Topic: {{query}}
        Target language: {{language}}
        """,
        user_template=prompt_library._get_default_user_template(),
        version="1.1.0",  # This will override the default fact-check template
        description="Enhanced fact-check template with confidence ratings",
        parameters={
            "query": "Research query or topic",
            "sources": "Formatted source data",
            "language": "Target language for the response"
        }
    )
    prompt_library.add_template(fact_check_template)
    
    # Save templates to disk
    prompt_library.save_templates()
    
    logger.info(f"Created and saved prompt templates to {templates_dir}")
    return templates_dir


async def demonstrate_template_comparison(templates_dir: Path):
    """Demonstrate comparison of different prompt templates."""
    
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OPENAI_API_KEY found in environment variables or .env file.")
        logger.error("Please set the API key and try again.")
        return
    
    # Initialize the GPT-4 synthesizer with our prompt templates
    synthesizer = GPT4Synthesizer(
        api_key=api_key,
        model="gpt-4o",
        temperature=0.3,
        max_tokens=2000,
        prompt_templates_dir=str(templates_dir)
    )
    
    # Research query
    query = "Explain the evidence and effects of climate change"
    
    # Test different synthesis types with both default and custom templates
    synthesis_types = [
        SynthesisType.SUMMARY,
        SynthesisType.FACT_CHECK,  # Will use our custom version
        SynthesisType.COMPREHENSIVE
    ]
    
    for synthesis_type in synthesis_types:
        try:
            logger.info(f"Testing {synthesis_type.value} synthesis...")
            
            # Run the synthesis
            result = await synthesizer.synthesize(
                query=query,
                source_results=SAMPLE_SOURCE_RESULTS,
                synthesis_type=synthesis_type,
                language="en"
            )
            
            if result:
                logger.info(f"Synthesis successful!")
                logger.info(f"Title: {result.title}")
                logger.info(f"Sections: {list(result.sections.keys())}")
                
                # Save the result to a file
                output_file = f"synthesis_{synthesis_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, "w") as f:
                    json.dump(result.to_dict(), f, indent=2)
                
                logger.info(f"Results saved to {output_file}")
            else:
                logger.error(f"Synthesis failed for {synthesis_type.value}")
                
        except Exception as e:
            logger.error(f"Error during {synthesis_type.value} synthesis: {e}")
    
    # Test custom educational template with custom parameters
    try:
        logger.info("Testing custom educational template...")
        
        # Get the prompt for custom template
        prompt_library = synthesizer.prompt_library
        educational_template = prompt_library.get_template("educational_content")
        
        if not educational_template:
            logger.error("Educational template not found in library")
            return
        
        # Format the prompt with custom parameters
        formatted_sources = prompt_library.format_sources(SAMPLE_SOURCE_RESULTS)
        
        prompts = educational_template.format(
            query=query,
            sources=formatted_sources,
            language="en",
            audience="high school"
        )
        
        # Call the API directly
        response_text = await synthesizer._call_gpt4_api_with_retry(
            prompts["system_prompt"],
            prompts["user_prompt"]
        )
        
        if response_text:
            logger.info("Custom educational content generated successfully!")
            
            # Save the result to a file
            output_file = f"educational_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(output_file, "w") as f:
                f.write(response_text)
            
            logger.info(f"Content saved to {output_file}")
            
            # Log evaluation metrics
            synthesizer.prompt_evaluator.log_result(
                template_id="educational_content",
                version=educational_template.version,
                synthesis_type=SynthesisType.CUSTOM,
                metrics={
                    "token_count": len(response_text.split()) * 1.3,
                    "has_sections": bool(re.search(r"^#+\s+", response_text, re.MULTILINE)),
                    "has_questions": "?" in response_text
                },
                query=query,
                metadata={"audience": "high school"}
            )
        else:
            logger.error("Failed to generate educational content")
            
    except Exception as e:
        logger.error(f"Error during custom template test: {e}")
    
    # Analyze template effectiveness
    logger.info("Template effectiveness comparison:")
    comparison = synthesizer.get_prompt_comparison()
    
    # Save evaluation results and comparison
    evaluation_file = "prompt_evaluation_results.json"
    synthesizer.save_prompt_evaluations(evaluation_file)
    logger.info(f"Evaluation results saved to {evaluation_file}")
    
    comparison_file = "prompt_template_comparison.json"
    with open(comparison_file, "w") as f:
        json.dump(comparison, f, indent=2)
    logger.info(f"Template comparison saved to {comparison_file}")
    
    
async def main():
    """Run the prompt engineering demonstration."""
    logger.info("Starting prompt engineering framework demo...")
    
    # Set up the prompt library with custom templates
    templates_dir = await setup_prompt_library()
    
    # Demonstrate template comparison
    await demonstrate_template_comparison(templates_dir)
    
    logger.info("Prompt engineering demo completed!")


if __name__ == "__main__":
    asyncio.run(main()) 