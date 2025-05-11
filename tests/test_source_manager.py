"""
Tests for the source manager.
"""

import asyncio
import pytest
from typing import Dict, List, Optional, Any

from src.research.adapters import SourceConfig, SourceType
from src.research.manager import SourceManager


@pytest.fixture
def source_manager():
    """Create a source manager with default configurations."""
    configs = {
        "wikipedia": SourceConfig(enabled=True, timeout_seconds=5, max_results=3),
        "duckduckgo": SourceConfig(enabled=True, timeout_seconds=5, max_results=3),
        "arxiv": SourceConfig(enabled=True, timeout_seconds=5, max_results=3),
        "openai_search": SourceConfig(enabled=False),  # Disabled by default for tests
    }
    return SourceManager(configs)


def test_source_manager_initialization(source_manager):
    """Test that source manager initializes correctly."""
    # Check that all expected source types are available
    adapter_info = source_manager.get_source_adapter_info()
    
    # Check Wikipedia adapter
    assert "wikipedia" in adapter_info
    assert len(adapter_info["wikipedia"]) == 1
    assert adapter_info["wikipedia"][0]["name"] == "Wikipedia"
    assert adapter_info["wikipedia"][0]["enabled"] is True
    
    # Check Web Search adapters - should have DuckDuckGo but OpenAI disabled
    assert "web_search" in adapter_info
    assert len(adapter_info["web_search"]) > 0
    assert any(a["name"] == "DuckDuckGo" for a in adapter_info["web_search"])
    assert not any(a["name"] == "OpenAI Search" and a["enabled"] for a in adapter_info["web_search"])
    
    # Check Academic adapter
    assert "academic" in adapter_info
    assert len(adapter_info["academic"]) == 1
    assert adapter_info["academic"][0]["name"] == "arXiv"


def test_get_adapters_for_depth(source_manager):
    """Test that the correct adapters are returned for each depth."""
    # Test quick depth
    quick_adapters = source_manager.get_adapters_for_depth("quick")
    assert SourceType.WIKIPEDIA in quick_adapters
    assert SourceType.WEB_SEARCH in quick_adapters
    assert SourceType.ACADEMIC not in quick_adapters
    
    # Test standard depth
    standard_adapters = source_manager.get_adapters_for_depth("standard")
    assert SourceType.WIKIPEDIA in standard_adapters
    assert SourceType.WEB_SEARCH in standard_adapters
    assert SourceType.ACADEMIC in standard_adapters
    
    # Test deep depth
    deep_adapters = source_manager.get_adapters_for_depth("deep")
    assert SourceType.WIKIPEDIA in deep_adapters
    assert SourceType.WEB_SEARCH in deep_adapters
    assert SourceType.ACADEMIC in deep_adapters


def test_get_max_results_for_depth(source_manager):
    """Test that the correct max results are returned for each depth."""
    assert source_manager.get_max_results_for_depth("quick") == 3
    assert source_manager.get_max_results_for_depth("standard") == 5
    assert source_manager.get_max_results_for_depth("deep") == 10


def test_get_max_content_items_for_depth(source_manager):
    """Test that the correct max content items are returned for each depth."""
    assert source_manager.get_max_content_items_for_depth("quick") == 5
    assert source_manager.get_max_content_items_for_depth("standard") == 10
    assert source_manager.get_max_content_items_for_depth("deep") == 20


def test_invalid_depth(source_manager):
    """Test that invalid depths raise ValueError."""
    with pytest.raises(ValueError):
        source_manager.get_adapters_for_depth("invalid")
    
    with pytest.raises(ValueError):
        source_manager.get_max_results_for_depth("invalid")
    
    with pytest.raises(ValueError):
        source_manager.get_max_content_items_for_depth("invalid")


@pytest.mark.asyncio
async def test_search_flow(source_manager, monkeypatch):
    """Test the search flow with mocked adapters."""
    # This is a simplified test that doesn't actually call external APIs
    # We mock the _safe_search method to return predetermined results
    
    async def mock_safe_search(self, adapter, params):
        """Mock implementation that returns dummy results."""
        return [
            {
                "title": f"Test result from {adapter.source_name}",
                "content": f"Test content from {adapter.source_name}",
                "source_name": adapter.source_name,
                "source_type": adapter.source_type,
                "url": "https://example.com",
            }
        ]
    
    # Patch the _safe_search method
    monkeypatch.setattr(SourceManager, "_safe_search", mock_safe_search)
    
    # Call search with standard depth
    results = await source_manager.search("test query", depth="standard")
    
    # We expect at least one result per enabled adapter
    assert len(results) > 0
    
    # We shouldn't have more results than the number of adapters
    adapter_count = sum(len(adapters) for adapters in source_manager.get_adapters_for_depth("standard").values())
    assert len(results) <= adapter_count 