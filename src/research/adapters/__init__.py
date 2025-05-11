"""
Source adapters for retrieving data from various research sources.
"""

from .base import SourceAdapter, SourceResult, SourceConfig, SearchParameters, SourceType
from .wikipedia import WikipediaAdapter
from .duckduckgo import DuckDuckGoAdapter
from .arxiv import ArxivAdapter
from .openai_search import OpenAISearchAdapter

__all__ = [
    "SourceAdapter",
    "SourceResult",
    "SourceConfig",
    "SearchParameters",
    "SourceType",
    "WikipediaAdapter",
    "DuckDuckGoAdapter",
    "ArxivAdapter",
    "OpenAISearchAdapter",
] 