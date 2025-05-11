"""
OpenAI Search adapter for retrieving web content through OpenAI's API.
"""

import asyncio
from datetime import datetime
import json
import logging
import os
from typing import Dict, List, Optional, Any

import httpx

from .base import SourceAdapter, SourceResult, SourceConfig, SearchParameters, SourceType


logger = logging.getLogger(__name__)


class OpenAISearchAdapter(SourceAdapter):
    """
    Adapter for searching the web using OpenAI's API.
    
    This adapter uses OpenAI's web search capability to retrieve web content.
    It requires a valid OpenAI API key with web search enabled.
    """
    
    BASE_API_URL = "https://api.openai.com/v1/chat/completions"
    DEFAULT_MODEL = "gpt-4o"  # Model that supports web search function
    
    def __init__(self, config: Optional[SourceConfig] = None):
        """
        Initialize the OpenAI Search adapter.
        
        Args:
            config: Configuration for the adapter. If None, default configuration is used.
        """
        super().__init__(config)
        # Get API key from config or environment
        self.api_key = self.config.api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not provided. Set it in the config or OPENAI_API_KEY environment variable.")
        
        # Get model from config or use default
        self.model = self.config.additional_params.get("model", self.DEFAULT_MODEL)
    
    @property
    def source_type(self) -> SourceType:
        """Get the type of this source."""
        return SourceType.WEB_SEARCH
    
    @property
    def source_name(self) -> str:
        """Get the human-readable name of this source."""
        return "OpenAI Search"
    
    @property
    def is_enabled(self) -> bool:
        """Check if this source adapter is enabled and configured."""
        return super().is_enabled and bool(self.api_key)
    
    async def search(self, parameters: SearchParameters) -> List[SourceResult]:
        """
        Search the web using OpenAI's search functionality.
        
        Args:
            parameters: Search parameters
            
        Returns:
            List of search results
            
        Raises:
            ConnectionError: If connection to OpenAI fails
            TimeoutError: If request times out
            ValueError: If API key is not provided or search is not enabled
        """
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        max_results = parameters.max_results or self.config.max_results
        
        # Construct the OpenAI API request with search function
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        # Prepare search request with the web_search tool
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful research assistant."},
                {"role": "user", "content": (
                    f"Search for information about: {parameters.query}. "
                    f"Look for the most relevant and recent information. "
                    f"Language preference: {parameters.language}."
                )}
            ],
            "tools": [{
                "type": "web_search",
            }],
            "tool_choice": {"type": "auto"},
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(
                    self.BASE_API_URL,
                    headers=headers,
                    json=data,
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract search results
                search_results = []
                
                if "choices" in result and result["choices"]:
                    choice = result["choices"][0]
                    if "message" in choice and "tool_calls" in choice["message"]:
                        tool_calls = choice["message"]["tool_calls"]
                        
                        for tool_call in tool_calls:
                            if tool_call["type"] == "web_search":
                                try:
                                    function_args = json.loads(tool_call["function"]["arguments"])
                                    search_results_data = function_args.get("search_results", [])
                                    
                                    for i, search_result in enumerate(search_results_data):
                                        if i >= max_results:
                                            break
                                            
                                        # Extract data
                                        title = search_result.get("title", "Untitled")
                                        content = search_result.get("snippet", "")
                                        url = search_result.get("url", "")
                                        
                                        # Create result
                                        search_results.append(
                                            SourceResult(
                                                title=title,
                                                content=content,
                                                source_name=self.source_name,
                                                source_type=self.source_type,
                                                url=url,
                                                retrieved_at=datetime.now(),
                                                metadata={
                                                    "domain": self._extract_domain(url),
                                                    "search_position": i + 1,
                                                    "is_full_content": False,
                                                },
                                                language=parameters.language,
                                            )
                                        )
                                except (json.JSONDecodeError, KeyError) as e:
                                    logger.error(f"Error parsing OpenAI search results: {e}")
                
                return search_results
        
        except httpx.TimeoutException as e:
            logger.error(f"Timeout while searching with OpenAI: {e}")
            raise TimeoutError(f"OpenAI search timed out: {e}") from e
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from OpenAI: {e}")
            error_content = e.response.text
            raise ConnectionError(f"OpenAI API error: {e.response.status_code} - {error_content}") from e
        
        except Exception as e:
            logger.error(f"Unexpected error while searching with OpenAI: {e}")
            raise
    
    async def get_content(self, identifier: str, language: str = "en") -> Optional[SourceResult]:
        """
        Get detailed content from a URL using OpenAI's browsing capability.
        
        Args:
            identifier: URL to retrieve content from
            language: Language code
            
        Returns:
            Content result or None if not found
            
        Raises:
            ConnectionError: If connection to OpenAI fails
            TimeoutError: If request times out
            ValueError: If API key is not provided
        """
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        url = identifier
        if not (url.startswith("http://") or url.startswith("https://")):
            url = f"https://{url}"
        
        # Construct the OpenAI API request with web browsing
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        # Prepare request with web_browse functionality
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": (
                    "You are a helpful research assistant. Your task is to browse a webpage and extract its content. "
                    "Provide a detailed summary including key points, facts, and data."
                )},
                {"role": "user", "content": f"Browse this URL and extract its content: {url}"}
            ],
            "tools": [{
                "type": "web_browser",
                "web_browser": {
                    "type": "browse",
                }
            }],
            "tool_choice": {"type": "auto"},
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds * 2) as client:  # Double timeout for browsing
                response = await client.post(
                    self.BASE_API_URL,
                    headers=headers,
                    json=data,
                )
                response.raise_for_status()
                result = response.json()
                
                # Process the browsing result
                content = ""
                title = f"Content from {url}"
                metadata = {
                    "domain": self._extract_domain(url),
                    "is_full_content": True,
                }
                section_headers = []
                
                if "choices" in result and result["choices"]:
                    choice = result["choices"][0]
                    if "message" in choice:
                        # Extract text content from OpenAI's response
                        if "content" in choice["message"] and choice["message"]["content"]:
                            content = choice["message"]["content"]
                            
                            # Try to extract a title from the content
                            lines = content.split("\n")
                            if lines and lines[0].strip():
                                potential_title = lines[0].strip()
                                if len(potential_title) < 100 and not potential_title.startswith("#"):
                                    title = potential_title
                            
                            # Extract section headers based on markdown formatting
                            for line in lines:
                                line = line.strip()
                                if line.startswith("##"):  # Markdown header format
                                    header = line.lstrip("#").strip()
                                    if header:
                                        section_headers.append(header)
                        
                        # Extract tool call results if any
                        if "tool_calls" in choice["message"]:
                            tool_calls = choice["message"]["tool_calls"]
                            for tool_call in tool_calls:
                                if tool_call["type"] == "web_browser":
                                    try:
                                        function_args = json.loads(tool_call["function"]["arguments"])
                                        browser_info = function_args.get("browser_info", {})
                                        
                                        # Update metadata with additional browser info
                                        if browser_info:
                                            metadata.update(browser_info)
                                            
                                            # Get page title if available
                                            if "page_title" in browser_info:
                                                title = browser_info["page_title"]
                                    except (json.JSONDecodeError, KeyError) as e:
                                        logger.error(f"Error parsing OpenAI browsing results: {e}")
                
                # Return the result if we have content
                if content:
                    return SourceResult(
                        title=title,
                        content=content,
                        source_name=self.source_name,
                        source_type=self.source_type,
                        url=url,
                        retrieved_at=datetime.now(),
                        metadata=metadata,
                        section_headers=section_headers,
                        language=language,
                    )
                
                return None
        
        except httpx.TimeoutException as e:
            logger.error(f"Timeout while browsing with OpenAI: {e}")
            raise TimeoutError(f"OpenAI browsing timed out: {e}") from e
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from OpenAI: {e}")
            error_content = e.response.text
            raise ConnectionError(f"OpenAI API error: {e.response.status_code} - {error_content}") from e
        
        except Exception as e:
            logger.error(f"Unexpected error while browsing with OpenAI: {e}")
            raise
    
    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from a URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name
        """
        if not url:
            return ""
        
        # Remove protocol
        domain = url.replace("https://", "").replace("http://", "")
        # Remove path
        domain = domain.split("/")[0]
        # Remove subdomains if common ones
        common_subdomains = ["www", "m", "mobile", "blog", "news"]
        parts = domain.split(".")
        if len(parts) > 2 and parts[0] in common_subdomains:
            domain = ".".join(parts[1:])
        
        return domain 