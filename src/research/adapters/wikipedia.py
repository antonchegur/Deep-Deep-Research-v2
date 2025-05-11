"""
Wikipedia adapter for retrieving and processing Wikipedia articles.
"""

import asyncio
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any
import re

import httpx

from .base import SourceAdapter, SourceResult, SourceConfig, SearchParameters, SourceType


logger = logging.getLogger(__name__)


class WikipediaAdapter(SourceAdapter):
    """
    Adapter for retrieving content from Wikipedia.
    
    This adapter interfaces with the Wikipedia API to search for articles
    and retrieve their full content with proper handling of rate limits.
    """
    
    BASE_API_URL = "https://{{language}}.wikipedia.org/w/api.php"
    
    @property
    def source_type(self) -> SourceType:
        """Get the type of this source."""
        return SourceType.WIKIPEDIA
    
    @property
    def source_name(self) -> str:
        """Get the human-readable name of this source."""
        return "Wikipedia"
    
    def _get_api_url(self, language: str) -> str:
        """
        Get the API URL for the given language.
        
        Args:
            language: Language code (e.g., "en", "es")
            
        Returns:
            API URL
        """
        return self.BASE_API_URL.replace("{{language}}", language)
    
    async def search(self, parameters: SearchParameters) -> List[SourceResult]:
        """
        Search Wikipedia for articles matching the query.
        
        Args:
            parameters: Search parameters
            
        Returns:
            List of search results
            
        Raises:
            ConnectionError: If connection to Wikipedia fails
            TimeoutError: If request times out
        """
        max_results = parameters.max_results or self.config.max_results
        language = parameters.language
        
        api_url = self._get_api_url(language)
        
        # Prepare search request parameters
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": parameters.query,
            "srlimit": str(max_results),
            "srprop": "snippet|titlesnippet",
        }
        
        # Add parameters for retrieving redirects if requested
        if parameters.filters.get("include_redirects", False):
            params["srredirect"] = "1"
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(api_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Extract search results
                search_results = []
                if "query" in data and "search" in data["query"]:
                    for result in data["query"]["search"]:
                        # Create a minimal result with search snippet
                        search_results.append(
                            SourceResult(
                                title=result["title"],
                                content=result.get("snippet", ""),
                                source_name=self.source_name,
                                source_type=self.source_type,
                                url=f"https://{language}.wikipedia.org/wiki/{result['title'].replace(' ', '_')}",
                                retrieved_at=datetime.now(),
                                metadata={
                                    "pageid": result.get("pageid"),
                                    "wordcount": result.get("wordcount", 0),
                                    "size": result.get("size", 0),
                                    "is_full_content": False,
                                },
                                language=language,
                            )
                        )
                
                return search_results
        
        except httpx.TimeoutException as e:
            logger.error(f"Timeout while searching Wikipedia: {e}")
            raise TimeoutError(f"Wikipedia search timed out: {e}") from e
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while searching Wikipedia: {e}")
            raise ConnectionError(f"Wikipedia API error: {e.response.status_code} - {e.response.text}") from e
        
        except Exception as e:
            logger.error(f"Unexpected error while searching Wikipedia: {e}")
            raise
    
    async def get_content(self, identifier: str, language: str = "en") -> Optional[SourceResult]:
        """
        Get the full content of a Wikipedia article.
        
        Args:
            identifier: The title of the Wikipedia article or its URL
            language: Language code (default: "en" for English)
            
        Returns:
            Article content or None if not found
            
        Raises:
            ConnectionError: If connection to Wikipedia fails
            TimeoutError: If request times out
        """
        api_url = self._get_api_url(language)
        
        # Extract title from URL if needed
        if identifier.startswith('http'):
            # Extract the page title from the URL
            match = re.search(r'/wiki/([^?#]+)$', identifier)
            if match:
                title = match.group(1).replace('_', ' ')
            else:
                logger.warning(f"Could not extract title from Wikipedia URL: {identifier}")
                title = identifier
        else:
            title = identifier
        
        # Prepare request parameters for full article content
        params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "extracts|info|categories|links|langlinks",
            "exintro": "0",  # Include full content, not just intro
            "explaintext": "1",  # Get plain text content
            "inprop": "url|displaytitle",
            "clshow": "!hidden",  # Show non-hidden categories
            "cllimit": "20",  # Limit to 20 categories
            "pllimit": "20",  # Limit to 20 links
            "lllimit": "10",  # Limit to 10 language links
            "redirects": "1",  # Follow redirects
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(api_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Extract page content
                if "query" in data and "pages" in data["query"]:
                    pages = data["query"]["pages"]
                    
                    # Wikipedia returns a dict with page IDs as keys
                    # Since we requested one page, we take the first item
                    page_id, page_data = next(iter(pages.items()))
                    
                    # Missing page has page_id == -1
                    if page_id == "-1":
                        logger.warning(f"Wikipedia article '{identifier}' not found")
                        return None
                    
                    # Extract sections using a separate API call
                    sections = await self._get_article_sections(page_data["title"], language)
                    
                    # Create the result with full content
                    return SourceResult(
                        title=page_data.get("title", title),
                        content=page_data.get("extract", ""),
                        source_name=self.source_name,
                        source_type=self.source_type,
                        url=page_data.get("fullurl", f"https://{language}.wikipedia.org/wiki/{title.replace(' ', '_')}"),
                        retrieved_at=datetime.now(),
                        metadata={
                            "pageid": page_id,
                            "lastrevid": page_data.get("lastrevid"),
                            "categories": [c["title"] for c in page_data.get("categories", [])],
                            "links": [l["title"] for l in page_data.get("links", [])],
                            "langlinks": {ll["lang"]: ll["*"] for ll in page_data.get("langlinks", [])},
                            "is_full_content": True,
                        },
                        section_headers=sections,
                        language=language,
                    )
                
                return None
        
        except httpx.TimeoutException as e:
            logger.error(f"Timeout while retrieving Wikipedia article: {e}")
            raise TimeoutError(f"Wikipedia content retrieval timed out: {e}") from e
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while retrieving Wikipedia article: {e}")
            raise ConnectionError(f"Wikipedia API error: {e.response.status_code} - {e.response.text}") from e
        
        except Exception as e:
            logger.error(f"Unexpected error while retrieving Wikipedia article: {e}")
            raise
    
    async def _get_article_sections(self, title: str, language: str) -> List[str]:
        """
        Get the section headers for a Wikipedia article.
        
        Args:
            title: Article title
            language: Language code
            
        Returns:
            List of section headers
        """
        api_url = self._get_api_url(language)
        
        # Prepare request parameters for sections
        params = {
            "action": "parse",
            "format": "json",
            "page": title,
            "prop": "sections",
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(api_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                sections = []
                if "parse" in data and "sections" in data["parse"]:
                    for section in data["parse"]["sections"]:
                        sections.append(section["line"])
                
                return sections
        
        except Exception as e:
            logger.warning(f"Could not retrieve sections for article '{title}': {e}")
            return [] 