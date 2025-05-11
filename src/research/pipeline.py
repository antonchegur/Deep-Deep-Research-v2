"""
Unified research pipeline combining multi-source research with AI synthesis.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Union, Any

from .adapters import SourceResult, SourceType
from .manager import SourceManager
from .synthesizer import SynthesisResult, SynthesisType, GPT4Synthesizer


logger = logging.getLogger(__name__)


class ResearchPipeline:
    """
    Unified pipeline for conducting research across multiple sources and synthesizing results.
    
    This class provides a high-level API that coordinates:
    1. Data collection from multiple sources via SourceManager
    2. Analysis and synthesis of research data via GPT-4 Turbo
    """
    
    def __init__(self, source_manager: Optional[SourceManager] = None, 
                synthesizer: Optional[GPT4Synthesizer] = None):
        """
        Initialize the research pipeline.
        
        Args:
            source_manager: Source manager for data collection. If None, a default one is created.
            synthesizer: GPT-4 synthesizer for analysis. If None, a default one is created.
        """
        self.source_manager = source_manager or SourceManager()
        self.synthesizer = synthesizer or GPT4Synthesizer()
    
    async def research(self, query: str, depth: str = "standard", language: str = "en",
                      synthesis_type: SynthesisType = SynthesisType.COMPREHENSIVE,
                      filters: Optional[Dict[str, Any]] = None,
                      max_sources_to_analyze: int = 10) -> Dict[str, Any]:
        """
        Conduct full research on a topic with both data collection and synthesis.
        
        Args:
            query: Research query or topic
            depth: Research depth ('quick', 'standard', or 'deep')
            language: Language code (e.g., 'en', 'es', 'ru')
            synthesis_type: Type of synthesis to perform
            filters: Additional filters for the search
            max_sources_to_analyze: Maximum number of sources to include in synthesis
            
        Returns:
            Dictionary containing search results, content details, and synthesis
            
        Raises:
            ValueError: If depth is invalid
        """
        # Step 1: Collect initial search results
        search_results = await self.source_manager.search(
            query=query,
            depth=depth,
            language=language,
            filters=filters
        )
        
        if not search_results:
            logger.warning(f"No search results found for query: {query}")
            return {
                "query": query,
                "search_results": [],
                "content_results": [],
                "synthesis": None,
                "metadata": {
                    "depth": depth,
                    "language": language,
                    "synthesis_type": synthesis_type.value,
                }
            }
            
        # Step 2: Get detailed content for top results
        # Prepare identifiers for content retrieval
        identifiers = []
        for result in search_results:
            # For Wikipedia and arXiv, use URL as identifier
            if result.source_type in [SourceType.WIKIPEDIA, SourceType.ACADEMIC] and result.url:
                identifiers.append((result.url, result.source_type))
            # For other sources or if URL is missing, use title
            elif result.title:
                identifiers.append((result.title, result.source_type))
        
        # Limit the number of sources based on max_sources_to_analyze
        identifiers = identifiers[:max_sources_to_analyze]
        
        # Get detailed content
        content_results = await self.source_manager.get_content(
            identifiers=identifiers,
            depth=depth,
            language=language
        )
        
        # Step 3: Synthesize research with GPT-4
        synthesis = await self.synthesizer.synthesize(
            query=query,
            source_results=content_results,
            synthesis_type=synthesis_type,
            language=language
        )
        
        # Step 4: Return combined results
        return {
            "query": query,
            "search_results": [result.to_dict() for result in search_results],
            "content_results": [result.to_dict() for result in content_results],
            "synthesis": synthesis.to_dict() if synthesis else None,
            "metadata": {
                "depth": depth,
                "language": language,
                "synthesis_type": synthesis_type.value,
                "sources_analyzed": len(content_results),
                "total_sources_found": len(search_results),
            }
        }
    
    async def search_only(self, query: str, depth: str = "standard", language: str = "en",
                         filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Perform search across sources without content retrieval or synthesis.
        
        Args:
            query: Search query
            depth: Research depth ('quick', 'standard', or 'deep')
            language: Language code
            filters: Additional filters for the search
            
        Returns:
            List of search results as dictionaries
            
        Raises:
            ValueError: If depth is invalid
        """
        results = await self.source_manager.search(
            query=query,
            depth=depth,
            language=language,
            filters=filters
        )
        
        return [result.to_dict() for result in results]
    
    async def analyze_texts(self, query: str, texts: List[str], 
                           synthesis_type: SynthesisType = SynthesisType.COMPREHENSIVE,
                           language: str = "en") -> Dict[str, Any]:
        """
        Analyze provided texts without performing source search.
        
        This is useful when you already have text content and just need GPT-4 analysis.
        
        Args:
            query: Research question or context for analysis
            texts: List of text contents to analyze
            synthesis_type: Type of synthesis to perform
            language: Language code for the synthesis output
            
        Returns:
            Dictionary containing synthesis results
        """
        # Create simple source results from provided texts
        source_results = [
            SourceResult(
                title=f"Text {i+1}",
                content=text,
                source_name="User Provided",
                source_type=SourceType.CUSTOM,
                language=language
            )
            for i, text in enumerate(texts)
        ]
        
        # Perform synthesis
        synthesis = await self.synthesizer.synthesize(
            query=query,
            source_results=source_results,
            synthesis_type=synthesis_type,
            language=language
        )
        
        return {
            "query": query,
            "synthesis": synthesis.to_dict() if synthesis else None,
            "metadata": {
                "language": language,
                "synthesis_type": synthesis_type.value,
                "sources_analyzed": len(texts),
            }
        }
    
    async def customize_synthesis(self, query: str, source_results: List[SourceResult],
                                 custom_prompt: str, language: str = "en") -> Dict[str, Any]:
        """
        Perform synthesis with a custom prompt template.
        
        Args:
            query: Research question 
            source_results: List of source results to analyze
            custom_prompt: Custom prompt template for the synthesis
            language: Language code
            
        Returns:
            Dictionary containing synthesis results
        """
        synthesis = await self.synthesizer.custom_synthesis(
            query=query,
            source_results=source_results,
            custom_prompt=custom_prompt,
            language=language
        )
        
        return {
            "query": query,
            "synthesis": synthesis.to_dict() if synthesis else None,
            "metadata": {
                "language": language,
                "synthesis_type": "custom",
                "sources_analyzed": len(source_results),
            }
        } 