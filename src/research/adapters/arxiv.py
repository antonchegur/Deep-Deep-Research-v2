"""
arXiv adapter for retrieving and processing academic papers.
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


class ArxivAdapter(SourceAdapter):
    """
    Adapter for retrieving content from arXiv.
    
    This adapter interfaces with arXiv's API to search for academic papers
    and retrieve their content with proper handling of rate limits.
    """
    
    BASE_API_URL = "http://export.arxiv.org/api/query"
    BASE_URL = "https://arxiv.org"
    MAX_RESULTS_PER_REQUEST = 100  # arXiv API limit
    RATE_LIMIT_DELAY = 3  # seconds between requests
    
    # Field mapping for search
    FIELD_MAP = {
        "all": "all",
        "title": "ti",
        "abstract": "abs",
        "author": "au",
        "comment": "co",
        "journal": "jr",
        "category": "cat",
        "report_number": "rn",
        "id": "id",
        "doi": "doi",
    }
    
    @property
    def source_type(self) -> SourceType:
        """Get the type of this source."""
        return SourceType.ACADEMIC
    
    @property
    def source_name(self) -> str:
        """Get the human-readable name of this source."""
        return "arXiv"
    
    async def search(self, parameters: SearchParameters) -> List[SourceResult]:
        """
        Search arXiv for papers matching the query.
        
        Args:
            parameters: Search parameters
            
        Returns:
            List of search results
            
        Raises:
            ConnectionError: If connection to arXiv fails
            TimeoutError: If request times out
        """
        max_results = min(parameters.max_results or self.config.max_results, self.MAX_RESULTS_PER_REQUEST)
        
        # Apply field-specific search if specified in filters
        search_query = parameters.query
        if parameters.filters and "field" in parameters.filters:
            field = parameters.filters["field"]
            if field in self.FIELD_MAP:
                search_query = f"{self.FIELD_MAP[field]}:{search_query}"
        
        # Prepare API request parameters
        params = {
            "search_query": search_query,
            "start": parameters.filters.get("start", 0),
            "max_results": max_results,
            "sortBy": parameters.filters.get("sort_by", "relevance"),
            "sortOrder": parameters.filters.get("sort_order", "descending"),
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(self.BASE_API_URL, params=params)
                response.raise_for_status()
                
                # Parse XML response
                soup = BeautifulSoup(response.text, "lxml-xml")
                entries = soup.find_all("entry")
                
                results = []
                for entry in entries:
                    # Extract required fields
                    title_elem = entry.find("title")
                    title = title_elem.text.strip() if title_elem else "Untitled"
                    
                    # Remove any newlines from title that might be present in the XML
                    title = title.replace("\n", " ").strip()
                    
                    summary_elem = entry.find("summary")
                    summary = summary_elem.text.strip() if summary_elem else ""
                    
                    # Get primary link
                    link_elem = entry.find("link", attrs={"rel": "alternate"})
                    link = link_elem["href"] if link_elem and link_elem.has_attr("href") else ""
                    
                    # Get PDF link if available
                    pdf_link = entry.find("link", attrs={"title": "pdf"})
                    pdf_url = pdf_link["href"] if pdf_link and pdf_link.has_attr("href") else ""
                    
                    # Get ID
                    id_elem = entry.find("id")
                    raw_id = id_elem.text.strip() if id_elem else ""
                    paper_id = raw_id.split("/")[-1] if raw_id else ""
                    
                    # Get authors
                    author_elements = entry.find_all("author")
                    authors = [author.find("name").text.strip() for author in author_elements if author.find("name")]
                    
                    # Get categories
                    primary_category = entry.find("arxiv:primary_category")
                    primary_cat = primary_category["term"] if primary_category and primary_category.has_attr("term") else ""
                    
                    # Get publication date
                    published_elem = entry.find("published")
                    published = published_elem.text.strip() if published_elem else ""
                    
                    # Create a SourceResult
                    results.append(
                        SourceResult(
                            title=title,
                            content=summary,
                            source_name=self.source_name,
                            source_type=self.source_type,
                            url=pdf_url or link,
                            retrieved_at=datetime.now(),
                            metadata={
                                "id": paper_id,
                                "authors": authors,
                                "category": primary_cat,
                                "published": published,
                                "is_full_content": False,
                                "pdf_url": pdf_url,
                            },
                            language=parameters.language,
                        )
                    )
                
                return results
        
        except httpx.TimeoutException as e:
            logger.error(f"Timeout while searching arXiv: {e}")
            raise TimeoutError(f"arXiv search timed out: {e}") from e
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while searching arXiv: {e}")
            raise ConnectionError(f"arXiv API error: {e.response.status_code} - {e.response.text}") from e
        
        except Exception as e:
            logger.error(f"Unexpected error while searching arXiv: {e}")
            raise
    
    async def get_content(self, identifier: str, language: str = "en") -> Optional[SourceResult]:
        """
        Get the detailed information for an arXiv paper.
        
        Args:
            identifier: arXiv paper ID (e.g., "2106.09685") or URL
            language: Language code (not used for arXiv, included for interface compliance)
            
        Returns:
            Paper content or None if not found
            
        Raises:
            ConnectionError: If connection to arXiv fails
            TimeoutError: If request times out
        """
        # Extract paper ID from identifier (URL or ID)
        paper_id = identifier
        
        # Handle URLs to different arXiv paths
        if identifier.startswith('http'):
            # Extract paper ID from different URL formats
            arxiv_patterns = [
                r'arxiv\.org/abs/(\d+\.\d+(?:v\d+)?)',       # https://arxiv.org/abs/2106.09685
                r'arxiv\.org/pdf/(\d+\.\d+(?:v\d+)?)',       # https://arxiv.org/pdf/2106.09685.pdf
                r'arxiv\.org/ps/(\d+\.\d+(?:v\d+)?)',        # https://arxiv.org/ps/2106.09685
                r'arxiv\.org/e-print/(\d+\.\d+(?:v\d+)?)',   # https://arxiv.org/e-print/2106.09685
                r'arxiv\.org/format/(\d+\.\d+(?:v\d+)?)',    # https://arxiv.org/format/2106.09685
                # Legacy archive IDs
                r'arxiv\.org/abs/\w+(-\w+)?/(\d{7}(?:v\d+)?)',    # https://arxiv.org/abs/quant-ph/0702225
                r'arxiv\.org/pdf/\w+(-\w+)?/(\d{7}(?:v\d+)?)'     # https://arxiv.org/pdf/quant-ph/0702225.pdf
            ]
            
            for pattern in arxiv_patterns:
                match = re.search(pattern, identifier)
                if match:
                    paper_id = match.group(1)
                    break
            
            if paper_id == identifier:  # No match found
                logger.warning(f"Could not extract paper ID from arXiv URL: {identifier}")
        
        # Clean the paper ID (remove version number if present)
        if "/" in paper_id:
            paper_id = paper_id.split("/")[-1]
        if "v" in paper_id and paper_id[-2] == "v" and paper_id[-1].isdigit():
            # Remove version if present (e.g., "2106.09685v1" -> "2106.09685")
            paper_id = paper_id[:-2]
        
        # Prepare API request parameters
        params = {
            "id_list": paper_id,
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(self.BASE_API_URL, params=params)
                response.raise_for_status()
                
                # Parse XML response
                soup = BeautifulSoup(response.text, "lxml-xml")
                entry = soup.find("entry")
                
                if not entry:
                    logger.warning(f"arXiv paper with ID {paper_id} not found")
                    return None
                
                # Extract paper details
                title_elem = entry.find("title")
                title = title_elem.text.strip() if title_elem else "Untitled"
                
                summary_elem = entry.find("summary")
                summary = summary_elem.text.strip() if summary_elem else ""
                
                # Get authors
                author_elements = entry.find_all("author")
                authors = [author.find("name").text.strip() for author in author_elements if author.find("name")]
                
                # Get primary category
                category = None
                primary_category = entry.find("arxiv:primary_category")
                if primary_category:
                    category = primary_category.get("term")
                
                # Get all categories
                categories = [cat.get("term") for cat in entry.find_all("category") if cat.get("term")]
                
                # Get links
                links = {}
                for link in entry.find_all("link"):
                    link_type = link.get("title", "")
                    link_href = link.get("href", "")
                    if link_type and link_href:
                        links[link_type] = link_href
                    elif link.get("rel") == "alternate" and link_href:
                        links["alternate"] = link_href
                
                # Get publication date
                published_elem = entry.find("published")
                published = published_elem.text.strip() if published_elem else ""
                
                # Get DOI if available
                doi = None
                journal_ref = None
                comment = None
                for el in entry.find_all("arxiv:doi"):
                    doi = el.text.strip()
                for el in entry.find_all("arxiv:journal_ref"):
                    journal_ref = el.text.strip()
                for el in entry.find_all("arxiv:comment"):
                    comment = el.text.strip()
                
                # If allowed by config, try to get the PDF abstract using the PDF URL
                # This is disabled by default because it requires downloading the PDF
                full_text = ""
                if self.config.additional_params.get("fetch_pdf", False):
                    pdf_url = links.get("pdf")
                    if pdf_url:
                        try:
                            full_text = await self._extract_text_from_pdf(pdf_url)
                        except Exception as e:
                            logger.warning(f"Failed to extract text from PDF: {e}")
                
                # If we couldn't get full text, use summary
                if not full_text:
                    full_text = summary
                
                # Create result
                return SourceResult(
                    title=title,
                    content=full_text,
                    source_name=self.source_name,
                    source_type=self.source_type,
                    url=links.get("pdf", links.get("alternate", f"{self.BASE_URL}/abs/{paper_id}")),
                    retrieved_at=datetime.now(),
                    metadata={
                        "id": paper_id,
                        "authors": authors,
                        "category": category,
                        "categories": categories,
                        "published": published,
                        "links": links,
                        "doi": doi,
                        "journal_ref": journal_ref,
                        "comment": comment,
                        "is_full_content": bool(full_text != summary),
                    },
                    section_headers=self._extract_paper_sections(full_text),
                    language=language,
                )
        
        except httpx.TimeoutException as e:
            logger.error(f"Timeout while retrieving arXiv paper: {e}")
            raise TimeoutError(f"arXiv content retrieval timed out: {e}") from e
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while retrieving arXiv paper: {e}")
            raise ConnectionError(f"arXiv API error: {e.response.status_code} - {e.response.text}") from e
        
        except Exception as e:
            logger.error(f"Unexpected error while retrieving arXiv paper: {e}")
            raise
    
    async def _extract_text_from_pdf(self, pdf_url: str) -> str:
        """
        Extract text from a PDF document.
        
        Args:
            pdf_url: URL of the PDF
            
        Returns:
            Extracted text
            
        Raises:
            ValueError: If PDF extraction fails
            
        Note:
            This is a placeholder implementation. In a real implementation,
            you would use a PDF extraction library like PyPDF2 or pdfplumber.
        """
        # This is a placeholder. In a real implementation, you would:
        # 1. Download the PDF
        # 2. Extract text using a PDF library
        # 3. Return the extracted text
        #
        # For now, we'll just raise an error
        raise NotImplementedError("PDF extraction not implemented")
    
    def _extract_paper_sections(self, text: str) -> List[str]:
        """
        Extract section headers from the paper text.
        
        Args:
            text: Paper text
            
        Returns:
            List of section headers
        """
        if not text:
            return []
        
        # This is a simple heuristic approach to find section headers in academic papers
        # It looks for lines that match common section header patterns
        section_patterns = [
            r"^\s*\d+\.\s+[A-Z][a-zA-Z\s]+$",  # Numbered sections: "1. Introduction"
            r"^\s*[A-Z][A-Z\s]+$",             # All-caps sections: "INTRODUCTION"
            r"^\s*[A-Z][a-z]+(\s+[A-Z][a-z]+)*$"  # Title case sections: "Introduction"
        ]
        
        lines = text.split("\n")
        sections = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            for pattern in section_patterns:
                if re.match(pattern, line) and len(line.split()) <= 5:
                    sections.append(line)
                    break
        
        return sections 