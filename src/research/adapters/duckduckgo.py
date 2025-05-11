"""
DuckDuckGo adapter for performing web searches.
"""

import asyncio
from datetime import datetime
import logging
import re
from typing import Dict, List, Optional, Any
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from .base import SourceAdapter, SourceResult, SourceConfig, SearchParameters, SourceType


logger = logging.getLogger(__name__)


class DuckDuckGoAdapter(SourceAdapter):
    """
    Adapter for searching the web using DuckDuckGo.
    
    This adapter uses DuckDuckGo's search functionality to retrieve web results
    and extract content from web pages with proper rate limiting and error handling.
    """
    
    BASE_SEARCH_URL = "https://duckduckgo.com/html/"
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    
    def __init__(self, config: Optional[SourceConfig] = None):
        """
        Initialize the DuckDuckGo adapter.
        
        Args:
            config: Configuration for the adapter. If None, default configuration is used.
        """
        super().__init__(config)
        self.user_agent = self.config.additional_params.get("user_agent", self.DEFAULT_USER_AGENT)
    
    @property
    def source_type(self) -> SourceType:
        """Get the type of this source."""
        return SourceType.WEB_SEARCH
    
    @property
    def source_name(self) -> str:
        """Get the human-readable name of this source."""
        return "DuckDuckGo"
    
    async def search(self, parameters: SearchParameters) -> List[SourceResult]:
        """
        Search the web using DuckDuckGo.
        
        Args:
            parameters: Search parameters
            
        Returns:
            List of search results
            
        Raises:
            ConnectionError: If connection to DuckDuckGo fails
            TimeoutError: If request times out
        """
        max_results = parameters.max_results or self.config.max_results
        query = parameters.query
        
        # Add language restriction if specified
        if parameters.language != "en":
            query = f"{query} (site:.{parameters.language})"
        
        # Add time restriction if specified in filters
        time_period = parameters.filters.get("time_period")
        if time_period:
            query = f"{query} (site:{time_period})"
        
        # Prepare search headers
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://duckduckgo.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-GPC": "1",
        }
        
        # Prepare search parameters
        search_params = {
            "q": query,
            "kl": "us-en" if parameters.language == "en" else f"wt-{parameters.language}",
            "kp": "1",  # Safe search on
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(
                    self.BASE_SEARCH_URL,
                    params=search_params,
                    headers=headers,
                )
                response.raise_for_status()
                
                # Parse search results
                soup = BeautifulSoup(response.text, "lxml")
                result_elements = soup.select(".result")
                
                search_results = []
                for i, result in enumerate(result_elements):
                    if i >= max_results:
                        break
                    
                    # Extract result data
                    title_elem = result.select_one(".result__title")
                    title = title_elem.get_text(strip=True) if title_elem else "Untitled"
                    
                    url_elem = result.select_one(".result__url")
                    url = url_elem.get("href") if url_elem else None
                    
                    # Clean the URL (DDG uses redirects)
                    if url and "/uddg=" in url:
                        url = url.split("/uddg=")[1].split("&")[0]
                    
                    snippet_elem = result.select_one(".result__snippet")
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    # Create result
                    search_results.append(
                        SourceResult(
                            title=title,
                            content=snippet,
                            source_name=self.source_name,
                            source_type=self.source_type,
                            url=url,
                            retrieved_at=datetime.now(),
                            metadata={
                                "domain": self._extract_domain(url) if url else None,
                                "is_full_content": False,
                            },
                            language=parameters.language,
                        )
                    )
                
                return search_results
        
        except httpx.TimeoutException as e:
            logger.error(f"Timeout while searching DuckDuckGo: {e}")
            raise TimeoutError(f"DuckDuckGo search timed out: {e}") from e
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while searching DuckDuckGo: {e}")
            raise ConnectionError(f"DuckDuckGo error: {e.response.status_code} - {e.response.text}") from e
        
        except Exception as e:
            logger.error(f"Unexpected error while searching DuckDuckGo: {e}")
            raise
    
    async def get_content(self, identifier: str, language: str = "en") -> Optional[SourceResult]:
        """
        Get content from a web page by URL.
        
        Args:
            identifier: URL of the web page
            language: Language code (not used for web pages, included for interface compliance)
            
        Returns:
            Web page content or None if not found
            
        Raises:
            ConnectionError: If connection to the web page fails
            TimeoutError: If request times out
        """
        url = identifier
        if not (url.startswith("http://") or url.startswith("https://")):
            url = f"https://{url}"
        
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": f"{language},en-US;q=0.9,en;q=0.8",
            "DNT": "1",
            "Connection": "keep-alive",
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                # Parse HTML
                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    logger.warning(f"URL is not HTML: {url} (content-type: {content_type})")
                    return None
                
                # Extract content
                soup = BeautifulSoup(response.text, "lxml")
                
                # Try to determine title
                title = "Untitled"
                if soup.title and soup.title.string:
                    title = soup.title.string.strip()
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.extract()
                
                # Extract main content
                content = self._extract_main_content(soup)
                
                # Extract headers for sections
                headers = [h.get_text(strip=True) for h in soup.find_all(re.compile(r"h[1-3]"))]
                
                # Create result
                return SourceResult(
                    title=title,
                    content=content,
                    source_name=self.source_name,
                    source_type=self.source_type,
                    url=url,
                    retrieved_at=datetime.now(),
                    metadata={
                        "domain": self._extract_domain(url),
                        "status_code": response.status_code,
                        "content_type": content_type,
                        "is_full_content": True,
                    },
                    section_headers=headers,
                    language=language,
                )
        
        except httpx.TimeoutException as e:
            logger.error(f"Timeout while retrieving web page: {e}")
            raise TimeoutError(f"Web page retrieval timed out: {e}") from e
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while retrieving web page: {e}")
            raise ConnectionError(f"Web page error: {e.response.status_code} - {e.response.text}") from e
        
        except Exception as e:
            logger.error(f"Unexpected error while retrieving web page: {e}")
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
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract the main content from a web page.
        
        Args:
            soup: BeautifulSoup object of the HTML
            
        Returns:
            Main content as plain text
        """
        # Try common content containers
        content_selectors = [
            "article", "main", "[role=main]", ".content", "#content",
            ".post-content", ".article-content", ".entry-content"
        ]
        
        main_content = None
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                main_content = content_elem
                break
        
        # Fallback to body if no content container found
        if not main_content:
            main_content = soup.body
            
        # Get text content
        if main_content:
            # Extract paragraph text
            paragraphs = main_content.find_all("p")
            if paragraphs:
                return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            
            # Fallback to all text
            return main_content.get_text(separator="\n\n", strip=True)
        
        # If nothing else worked, just get the text from the whole document
        return soup.get_text(separator="\n\n", strip=True) 