"""
Tests for the unified research pipeline.
"""

import asyncio
import pytest
from typing import Dict, List, Optional, Any
from unittest.mock import patch, MagicMock, AsyncMock

from src.research.adapters import SourceResult, SourceType
from src.research.synthesizer import SynthesisResult, SynthesisType
from src.research.manager import SourceManager
from src.research.synthesizer import GPT4Synthesizer
from src.research.pipeline import ResearchPipeline


@pytest.fixture
def mock_source_results():
    """Create mock source results for testing."""
    return [
        SourceResult(
            title="Test Article 1",
            content="This is test content about quantum computing. Quantum computers use qubits.",
            source_name="Test Source",
            source_type=SourceType.WIKIPEDIA,
            url="https://example.com/article1",
        ),
        SourceResult(
            title="Test Article 2",
            content="More test content about quantum computing advancements.",
            source_name="Test Source",
            source_type=SourceType.WEB_SEARCH,
            url="https://example.com/article2",
        ),
    ]


@pytest.fixture
def mock_synthesis_result():
    """Create a mock synthesis result for testing."""
    return SynthesisResult(
        title="Quantum Computing Analysis",
        content="Synthesized content about quantum computing.",
        synthesis_type=SynthesisType.COMPREHENSIVE,
        query="What is quantum computing?",
        sources_used=2,
        sections={
            "Introduction": "Quantum computing is...",
            "Key Concepts": "Qubits are...",
        },
        citations=[
            {"source_idx": 1, "title": "Test Article 1"},
            {"source_idx": 2, "title": "Test Article 2"},
        ],
    )


@pytest.fixture
def mock_pipeline():
    """Create a research pipeline with mocked components."""
    # Create mock source manager
    source_manager = MagicMock(spec=SourceManager)
    source_manager.search = AsyncMock()
    source_manager.get_content = AsyncMock()
    
    # Create mock synthesizer
    synthesizer = MagicMock(spec=GPT4Synthesizer)
    synthesizer.synthesize = AsyncMock()
    synthesizer.custom_synthesis = AsyncMock()
    
    # Create pipeline with mocks
    pipeline = ResearchPipeline(
        source_manager=source_manager,
        synthesizer=synthesizer,
    )
    
    return pipeline


@pytest.mark.asyncio
async def test_research_flow(mock_pipeline, mock_source_results, mock_synthesis_result):
    """Test the complete research flow."""
    # Configure mocks
    mock_pipeline.source_manager.search.return_value = mock_source_results
    mock_pipeline.source_manager.get_content.return_value = mock_source_results
    mock_pipeline.synthesizer.synthesize.return_value = mock_synthesis_result
    
    # Run research
    query = "What is quantum computing?"
    result = await mock_pipeline.research(
        query=query,
        depth="standard",
        synthesis_type=SynthesisType.COMPREHENSIVE,
    )
    
    # Check that source manager methods were called
    mock_pipeline.source_manager.search.assert_called_once()
    assert mock_pipeline.source_manager.search.call_args[1]["query"] == query
    assert mock_pipeline.source_manager.search.call_args[1]["depth"] == "standard"
    
    mock_pipeline.source_manager.get_content.assert_called_once()
    
    # Check that synthesizer was called
    mock_pipeline.synthesizer.synthesize.assert_called_once()
    assert mock_pipeline.synthesizer.synthesize.call_args[1]["query"] == query
    assert mock_pipeline.synthesizer.synthesize.call_args[1]["source_results"] == mock_source_results
    
    # Check result structure
    assert result["query"] == query
    assert "search_results" in result
    assert "content_results" in result
    assert "synthesis" in result
    assert "metadata" in result
    
    # Check that synthesis was included
    assert result["synthesis"] == mock_synthesis_result.to_dict()
    
    # Check metadata
    assert result["metadata"]["depth"] == "standard"
    assert result["metadata"]["synthesis_type"] == SynthesisType.COMPREHENSIVE.value
    assert result["metadata"]["sources_analyzed"] == len(mock_source_results)


@pytest.mark.asyncio
async def test_search_only_flow(mock_pipeline, mock_source_results):
    """Test the search-only flow."""
    # Configure mocks
    mock_pipeline.source_manager.search.return_value = mock_source_results
    
    # Run search only
    query = "What is quantum computing?"
    results = await mock_pipeline.search_only(
        query=query,
        depth="quick",
    )
    
    # Check that only search was called
    mock_pipeline.source_manager.search.assert_called_once()
    assert mock_pipeline.source_manager.search.call_args[1]["query"] == query
    assert mock_pipeline.source_manager.search.call_args[1]["depth"] == "quick"
    
    # Verify get_content and synthesize were not called
    mock_pipeline.source_manager.get_content.assert_not_called()
    mock_pipeline.synthesizer.synthesize.assert_not_called()
    
    # Check results structure
    assert isinstance(results, list)
    assert len(results) == len(mock_source_results)
    for i, result in enumerate(results):
        assert result["title"] == mock_source_results[i].title
        assert result["content"] == mock_source_results[i].content


@pytest.mark.asyncio
async def test_analyze_texts_flow(mock_pipeline, mock_synthesis_result):
    """Test the analyze texts flow."""
    # Configure mocks
    mock_pipeline.synthesizer.synthesize.return_value = mock_synthesis_result
    
    # Run analyze texts
    query = "What are the key points in these documents?"
    texts = ["Document 1 text", "Document 2 text"]
    result = await mock_pipeline.analyze_texts(
        query=query,
        texts=texts,
        synthesis_type=SynthesisType.SUMMARY,
    )
    
    # Check that synthesizer was called correctly
    mock_pipeline.synthesizer.synthesize.assert_called_once()
    call_args = mock_pipeline.synthesizer.synthesize.call_args[1]
    assert call_args["query"] == query
    assert call_args["synthesis_type"] == SynthesisType.SUMMARY
    assert len(call_args["source_results"]) == len(texts)
    
    # Source manager methods should not be called
    mock_pipeline.source_manager.search.assert_not_called()
    mock_pipeline.source_manager.get_content.assert_not_called()
    
    # Check result structure
    assert result["query"] == query
    assert result["synthesis"] == mock_synthesis_result.to_dict()
    assert result["metadata"]["synthesis_type"] == SynthesisType.SUMMARY.value
    assert result["metadata"]["sources_analyzed"] == len(texts)


@pytest.mark.asyncio
async def test_empty_search_results(mock_pipeline):
    """Test handling of empty search results."""
    # Configure mock to return empty results
    mock_pipeline.source_manager.search.return_value = []
    
    # Run research
    query = "Nonexistent topic"
    result = await mock_pipeline.research(
        query=query,
        depth="standard",
    )
    
    # Source manager search should be called
    mock_pipeline.source_manager.search.assert_called_once()
    
    # But get_content and synthesize should not be called
    mock_pipeline.source_manager.get_content.assert_not_called()
    mock_pipeline.synthesizer.synthesize.assert_not_called()
    
    # Check result structure for empty case
    assert result["query"] == query
    assert result["search_results"] == []
    assert result["content_results"] == []
    assert result["synthesis"] is None 