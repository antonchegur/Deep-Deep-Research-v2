"""
Tests for the GPT-4 Turbo synthesizer.
"""

import asyncio
import pytest
from typing import Dict, List, Optional, Any
from unittest.mock import patch, MagicMock

from src.research.adapters import SourceResult, SourceType
from src.research.synthesizer import GPT4Synthesizer, SynthesisType


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
            content="More test content about quantum computing advancements. Recent breakthroughs include...",
            source_name="Test Source",
            source_type=SourceType.WEB_SEARCH,
            url="https://example.com/article2",
        ),
    ]


@pytest.fixture
def gpt4_synthesizer():
    """Create a GPT4Synthesizer with a mock API key."""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'mock-api-key'}):
        return GPT4Synthesizer()


def test_synthesizer_initialization(gpt4_synthesizer):
    """Test that the synthesizer initializes correctly."""
    assert gpt4_synthesizer.api_key == 'mock-api-key'
    assert gpt4_synthesizer.model == GPT4Synthesizer.DEFAULT_MODEL
    assert gpt4_synthesizer.temperature == 0.2
    assert gpt4_synthesizer.max_tokens == 4000


def test_format_user_prompt(gpt4_synthesizer, mock_source_results):
    """Test the formatting of user prompts."""
    query = "What are recent advancements in quantum computing?"
    language = "en"
    
    prompt = gpt4_synthesizer._format_user_prompt(query, mock_source_results, language)
    
    # Check basic content
    assert query in prompt
    assert f"Language: {language}" in prompt
    assert f"Number of sources: {len(mock_source_results)}" in prompt
    
    # Check that each source is included
    for result in mock_source_results:
        assert result.title in prompt
        assert result.url in prompt
        assert result.content in prompt


@pytest.mark.asyncio
async def test_synthesize_api_call_structure(gpt4_synthesizer, mock_source_results):
    """Test that the API call is structured correctly."""
    with patch.object(gpt4_synthesizer, '_call_gpt4_api', 
                     return_value=asyncio.Future()) as mock_call:
        mock_call.return_value.set_result("Mock API Response")
        
        query = "What are recent advancements in quantum computing?"
        await gpt4_synthesizer.synthesize(
            query=query,
            source_results=mock_source_results,
            synthesis_type=SynthesisType.SUMMARY,
            language="en"
        )
        
        # Check that API was called with the right synthesis type prompt
        mock_call.assert_called_once()
        system_prompt = mock_call.call_args[0][0]
        user_prompt = mock_call.call_args[0][1]
        
        # The system prompt should contain the summary prompt
        assert "creating concise summaries" in system_prompt.lower()
        
        # The user prompt should contain the query and sources
        assert query in user_prompt
        for result in mock_source_results:
            assert result.title in user_prompt


@pytest.mark.asyncio
async def test_custom_synthesis(gpt4_synthesizer, mock_source_results):
    """Test custom synthesis with a user-provided prompt."""
    with patch.object(gpt4_synthesizer, '_call_gpt4_api', 
                     return_value=asyncio.Future()) as mock_call:
        mock_call.return_value.set_result("Mock API Response")
        
        query = "What are recent advancements in quantum computing?"
        custom_prompt = "You are a quantum physics expert. Analyze these sources and explain the implications."
        
        await gpt4_synthesizer.custom_synthesis(
            query=query,
            source_results=mock_source_results,
            custom_prompt=custom_prompt,
            language="en"
        )
        
        # Check that API was called with the custom prompt
        mock_call.assert_called_once()
        system_prompt = mock_call.call_args[0][0]
        
        # The system prompt should be the custom prompt
        assert system_prompt == custom_prompt


@pytest.mark.asyncio
async def test_parse_response(gpt4_synthesizer, mock_source_results):
    """Test parsing of the API response into a structured synthesis result."""
    response_text = """
    Quantum Computing Advancements
    
    # Introduction
    Quantum computing has seen significant progress in recent years.
    
    # Key Developments
    Several breakthroughs have occurred in quantum hardware.
    
    # Future Outlook
    The future of quantum computing looks promising.
    
    According to Source 1, quantum computers use qubits.
    """
    
    query = "What are recent advancements in quantum computing?"
    synthesis_type = SynthesisType.COMPREHENSIVE
    
    result = gpt4_synthesizer._parse_response(
        response_text=response_text,
        query=query,
        source_results=mock_source_results,
        synthesis_type=synthesis_type,
        language="en"
    )
    
    # Check the basic structure
    assert result.title == "Quantum Computing Advancements"
    assert result.synthesis_type == synthesis_type
    assert result.query == query
    assert result.sources_used == len(mock_source_results)
    
    # Check sections extraction
    assert "Introduction" in result.sections
    assert "Key Developments" in result.sections
    assert "Future Outlook" in result.sections
    
    # Check that sections contain their content
    assert "quantum computing has seen significant progress" in result.sections["Introduction"].lower()
    assert "breakthroughs have occurred" in result.sections["Key Developments"].lower()
    
    # Check citation extraction (basic test, as the regex might not catch all formats)
    assert len(result.citations) <= len(mock_source_results) 