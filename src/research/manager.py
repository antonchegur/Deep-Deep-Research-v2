"""
Source manager for coordinating multiple research sources.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type, Tuple, Set

from .adapters import (
    SourceAdapter, 
    SourceResult, 
    SourceConfig, 
    SearchParameters,
    SourceType,
    WikipediaAdapter,
    DuckDuckGoAdapter,
    ArxivAdapter,
    OpenAISearchAdapter,
)


logger = logging.getLogger(__name__)


class SourceManager:
    """
    Manager for coordinating multiple research sources.
    
    This class manages multiple source adapters, handles source selection based on
    research depth, coordinates concurrent requests, and aggregates results.
    """
    
    # Default source configuration for different research depths
    DEFAULT_DEPTH_CONFIG = {
        "quick": {
            "sources": [SourceType.WIKIPEDIA, SourceType.WEB_SEARCH],
            "max_results_per_source": 3,
            "max_content_items": 5,
        },
        "standard": {
            "sources": [SourceType.WIKIPEDIA, SourceType.WEB_SEARCH, SourceType.ACADEMIC],
            "max_results_per_source": 5,
            "max_content_items": 10,
        },
        "deep": {
            "sources": [SourceType.WIKIPEDIA, SourceType.WEB_SEARCH, SourceType.ACADEMIC],
            "max_results_per_source": 10,
            "max_content_items": 20,
        },
    }
    
    def __init__(self, source_configs: Optional[Dict[str, SourceConfig]] = None):
        """
        Initialize the source manager.
        
        Args:
            source_configs: Configuration for each source adapter. Keys are source names.
        """
        self.source_configs = source_configs or {}
        self.adapters: Dict[SourceType, List[SourceAdapter]] = self._initialize_adapters()
    
    def _initialize_adapters(self) -> Dict[SourceType, List[SourceAdapter]]:
        """
        Initialize all source adapters.
        
        Returns:
            Dictionary of source adapters by type
        """
        adapters: Dict[SourceType, List[SourceAdapter]] = {
            source_type: [] for source_type in SourceType
        }
        
        # Initialize Wikipedia adapter
        wiki_config = self.source_configs.get("wikipedia")
        adapters[SourceType.WIKIPEDIA].append(WikipediaAdapter(wiki_config))
        
        # Initialize DuckDuckGo adapter for web search
        ddg_config = self.source_configs.get("duckduckgo")
        adapters[SourceType.WEB_SEARCH].append(DuckDuckGoAdapter(ddg_config))
        
        # Initialize OpenAI Search adapter for web search
        openai_config = self.source_configs.get("openai_search")
        if openai_config and openai_config.api_key:
            openai_adapter = OpenAISearchAdapter(openai_config)
            # Only add if API key is set and adapter is enabled
            if openai_adapter.is_enabled:
                adapters[SourceType.WEB_SEARCH].append(openai_adapter)
        
        # Initialize arXiv adapter for academic content
        arxiv_config = self.source_configs.get("arxiv")
        adapters[SourceType.ACADEMIC].append(ArxivAdapter(arxiv_config))
        
        return adapters
    
    def get_adapters_for_depth(self, depth: str) -> Dict[SourceType, List[SourceAdapter]]:
        """
        Get active adapters based on research depth.
        
        Args:
            depth: Research depth ("quick", "standard", or "deep")
            
        Returns:
            Dictionary of source adapters by type for the specified depth
            
        Raises:
            ValueError: If depth is not valid
        """
        if depth not in self.DEFAULT_DEPTH_CONFIG:
            valid_depths = ", ".join(self.DEFAULT_DEPTH_CONFIG.keys())
            raise ValueError(f"Invalid research depth: {depth}. Valid values are: {valid_depths}")
        
        # Get source types for the specified depth
        source_types = self.DEFAULT_DEPTH_CONFIG[depth]["sources"]
        
        # Filter adapters by type and enabled status
        active_adapters: Dict[SourceType, List[SourceAdapter]] = {
            source_type: [adapter for adapter in self.adapters[source_type] if adapter.is_enabled]
            for source_type in source_types
        }
        
        return active_adapters
    
    def get_max_results_for_depth(self, depth: str) -> int:
        """
        Get the maximum results per source for the specified depth.
        
        Args:
            depth: Research depth ("quick", "standard", or "deep")
            
        Returns:
            Maximum number of results per source
            
        Raises:
            ValueError: If depth is not valid
        """
        if depth not in self.DEFAULT_DEPTH_CONFIG:
            valid_depths = ", ".join(self.DEFAULT_DEPTH_CONFIG.keys())
            raise ValueError(f"Invalid research depth: {depth}. Valid values are: {valid_depths}")
        
        return self.DEFAULT_DEPTH_CONFIG[depth]["max_results_per_source"]
    
    def get_max_content_items_for_depth(self, depth: str) -> int:
        """
        Get the maximum content items to retrieve for the specified depth.
        
        Args:
            depth: Research depth ("quick", "standard", or "deep")
            
        Returns:
            Maximum number of content items to retrieve
            
        Raises:
            ValueError: If depth is not valid
        """
        if depth not in self.DEFAULT_DEPTH_CONFIG:
            valid_depths = ", ".join(self.DEFAULT_DEPTH_CONFIG.keys())
            raise ValueError(f"Invalid research depth: {depth}. Valid values are: {valid_depths}")
        
        return self.DEFAULT_DEPTH_CONFIG[depth]["max_content_items"]
    
    async def search(self, query: str, depth: str = "standard", language: str = "en", 
                    filters: Optional[Dict[str, Any]] = None) -> List[SourceResult]:
        """
        Search across multiple sources based on depth.
        
        Args:
            query: Search query
            depth: Research depth ("quick", "standard", or "deep")
            language: Language code
            filters: Additional filters for the search
            
        Returns:
            Combined list of search results from all sources
            
        Raises:
            ValueError: If depth is not valid
        """
        active_adapters = self.get_adapters_for_depth(depth)
        max_results = self.get_max_results_for_depth(depth)
        filters = filters or {}
        
        # Create search parameters
        params = SearchParameters(
            query=query,
            language=language,
            max_results=max_results,
            filters=filters,
        )
        
        # Create tasks for each adapter
        tasks = []
        for source_type, adapters in active_adapters.items():
            for adapter in adapters:
                tasks.append(self._safe_search(adapter, params))
        
        # Run all search tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # Flatten results
        flat_results = []
        for result_list in results:
            flat_results.extend(result_list)
        
        return flat_results
    
    async def get_content(self, identifiers: List[Tuple[str, SourceType]], depth: str = "standard", 
                         language: str = "en") -> List[SourceResult]:
        """
        Retrieve detailed content for search results.
        
        Args:
            identifiers: List of (identifier, source_type) tuples
            depth: Research depth ("quick", "standard", or "deep")
            language: Language code
            
        Returns:
            List of content results
            
        Raises:
            ValueError: If depth is not valid
        """
        active_adapters = self.get_adapters_for_depth(depth)
        max_content_items = self.get_max_content_items_for_depth(depth)
        
        # Limit the number of items based on depth
        identifiers = identifiers[:max_content_items]
        
        # Create tasks for each identifier
        tasks = []
        for identifier, source_type in identifiers:
            # Find an appropriate adapter for this source type
            if source_type in active_adapters and active_adapters[source_type]:
                # Use the first enabled adapter of the appropriate type
                adapter = active_adapters[source_type][0]
                tasks.append(self._safe_get_content(adapter, identifier, language))
        
        # Run all content retrieval tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # Filter out None results
        valid_results = [result for result in results if result is not None]
        
        return valid_results
    
    async def _safe_search(self, adapter: SourceAdapter, params: SearchParameters) -> List[SourceResult]:
        """
        Safely execute a search request, handling errors.
        
        Args:
            adapter: Source adapter to use
            params: Search parameters
            
        Returns:
            List of search results or empty list on error
        """
        try:
            return await adapter.search(params)
        except Exception as e:
            logger.error(f"Error searching with {adapter.source_name}: {e}")
            return []
    
    async def _safe_get_content(self, adapter: SourceAdapter, identifier: str, 
                               language: str) -> Optional[SourceResult]:
        """
        Safely execute a content retrieval request, handling errors.
        
        Args:
            adapter: Source adapter to use
            identifier: Content identifier
            language: Language code
            
        Returns:
            Content result or None on error
        """
        try:
            return await adapter.get_content(identifier, language)
        except Exception as e:
            logger.error(f"Error getting content from {adapter.source_name}: {e}")
            return None
    
    def get_available_source_types(self) -> Set[SourceType]:
        """
        Get the set of available source types with at least one enabled adapter.
        
        Returns:
            Set of available source types
        """
        return {
            source_type
            for source_type, adapters in self.adapters.items()
            if any(adapter.is_enabled for adapter in adapters)
        }
    
    def get_source_adapter_info(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get information about all source adapters.
        
        Returns:
            Dictionary with source types as keys and lists of adapter info as values
        """
        result = {}
        for source_type, adapters in self.adapters.items():
            adapter_info = []
            for adapter in adapters:
                adapter_info.append({
                    "name": adapter.source_name,
                    "enabled": adapter.is_enabled,
                    "type": source_type.value,
                })
            result[source_type.value] = adapter_info
        return result 