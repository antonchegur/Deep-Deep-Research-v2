"""
Base interfaces for research synthesis.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from ..adapters import SourceResult


class SynthesisType(Enum):
    """Types of research synthesis."""
    SUMMARY = "summary"               # Brief overview
    COMPREHENSIVE = "comprehensive"   # Detailed analysis
    COMPARISON = "comparison"         # Compare different sources/perspectives
    FACT_CHECK = "fact_check"         # Verify information
    CRITIQUE = "critique"             # Critical analysis
    LATEST_RESEARCH = "latest_research"  # Focus on newest findings
    HISTORICAL = "historical"         # Historical development
    CUSTOM = "custom"                 # Custom synthesis with specified template


class SynthesisResult:
    """
    Result of a research synthesis operation.
    
    Contains the synthesized content and metadata about the synthesis process.
    """
    
    def __init__(self, 
                title: str,
                content: str,
                synthesis_type: SynthesisType,
                query: str,
                sources_used: int,
                language: str = "en",
                sections: Optional[Dict[str, str]] = None,
                citations: Optional[List[Dict[str, Any]]] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a synthesis result.
        
        Args:
            title: Title of the synthesis
            content: Full synthesized content
            synthesis_type: Type of synthesis performed
            query: Original research query
            sources_used: Number of sources used in synthesis
            language: Language code of the content
            sections: Dictionary of sections with headings as keys and content as values
            citations: List of citation objects with reference info
            metadata: Additional metadata about the synthesis
        """
        self.title = title
        self.content = content
        self.synthesis_type = synthesis_type
        self.query = query
        self.generated_at = datetime.now()
        self.sources_used = sources_used
        self.language = language
        self.sections = sections or {}
        self.citations = citations or []
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert synthesis result to dictionary representation.
        
        Returns:
            Dictionary representation of synthesis result
        """
        return {
            "title": self.title,
            "content": self.content,
            "synthesis_type": self.synthesis_type.value,
            "query": self.query,
            "generated_at": self.generated_at.isoformat(),
            "sources_used": self.sources_used,
            "language": self.language,
            "sections": self.sections,
            "citations": self.citations,
            "metadata": self.metadata
        }


class BaseSynthesizer(ABC):
    """
    Base interface for research synthesizers.
    
    A synthesizer takes source data and produces a coherent synthesis
    according to the specified synthesis type.
    """
    
    @abstractmethod
    async def synthesize(self, query: str, 
                        source_results: List[SourceResult],
                        synthesis_type: SynthesisType = SynthesisType.COMPREHENSIVE,
                        language: str = "en") -> Optional[SynthesisResult]:
        """
        Synthesize research from source results.
        
        Args:
            query: Research question or topic
            source_results: List of source results to analyze
            synthesis_type: Type of synthesis to perform
            language: Language code for the output
            
        Returns:
            Synthesis result or None if synthesis fails
        """
        pass
    
    @abstractmethod
    async def custom_synthesis(self, query: str,
                              source_results: List[SourceResult],
                              custom_prompt: str,
                              language: str = "en") -> Optional[SynthesisResult]:
        """
        Perform synthesis with a custom prompt template.
        
        Args:
            query: Research question
            source_results: List of source results to analyze
            custom_prompt: Custom prompt template
            language: Language code for the output
            
        Returns:
            Synthesis result or None if synthesis fails
        """
        pass 