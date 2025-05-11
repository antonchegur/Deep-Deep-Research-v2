"""
Base interfaces for source adapters in the research system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union


class SourceType(Enum):
    """Type of information source."""
    WIKIPEDIA = "wikipedia"
    WEB_SEARCH = "web_search"
    ACADEMIC = "academic"
    CUSTOM = "custom"


@dataclass
class SourceConfig:
    """Configuration for a source adapter."""
    enabled: bool = True
    timeout_seconds: int = 30
    max_results: int = 10
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchParameters:
    """Parameters for a search request."""
    query: str
    language: str = "en"
    max_results: Optional[int] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    include_metadata: bool = True


@dataclass
class SourceResult:
    """Result from a source search."""
    title: str
    content: str
    source_name: str
    source_type: SourceType
    url: Optional[str] = None
    retrieved_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    relevance_score: Optional[float] = None
    section_headers: List[str] = field(default_factory=list)
    language: str = "en"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "title": self.title,
            "content": self.content,
            "source_name": self.source_name,
            "source_type": self.source_type.value,
            "url": self.url,
            "retrieved_at": self.retrieved_at.isoformat(),
            "metadata": self.metadata,
            "relevance_score": self.relevance_score,
            "section_headers": self.section_headers,
            "language": self.language,
        }


class SourceAdapter(ABC):
    """Base interface for all source adapters."""
    
    def __init__(self, config: Optional[SourceConfig] = None):
        """
        Initialize the source adapter.
        
        Args:
            config: Configuration for the adapter. If None, default configuration is used.
        """
        self.config = config or SourceConfig()
    
    @property
    @abstractmethod
    def source_type(self) -> SourceType:
        """Get the type of this source."""
        pass
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Get the human-readable name of this source."""
        pass
    
    @abstractmethod
    async def search(self, parameters: SearchParameters) -> List[SourceResult]:
        """
        Search the source with the given parameters.
        
        Args:
            parameters: Search parameters
            
        Returns:
            List of search results
            
        Raises:
            ConnectionError: If connection to the source fails
            TimeoutError: If request times out
            ValueError: If search parameters are invalid
        """
        pass
    
    @abstractmethod
    async def get_content(self, identifier: str, language: str = "en") -> Optional[SourceResult]:
        """
        Get detailed content for a specific item by its identifier.
        
        Args:
            identifier: Unique identifier for the item (e.g., title, URL, ID)
            language: Language code
            
        Returns:
            Content result or None if not found
            
        Raises:
            ConnectionError: If connection to the source fails
            TimeoutError: If request times out
            ValueError: If identifier is invalid
        """
        pass
    
    @property
    def is_enabled(self) -> bool:
        """Check if this source adapter is enabled."""
        return self.config.enabled
    
    def enable(self) -> None:
        """Enable this source adapter."""
        self.config.enabled = True
    
    def disable(self) -> None:
        """Disable this source adapter."""
        self.config.enabled = False 