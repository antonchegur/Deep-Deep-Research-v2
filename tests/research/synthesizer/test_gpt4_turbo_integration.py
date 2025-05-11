"""
Tests for the GPT-4 Turbo synthesizer integration.
"""

import os
import pytest
import asyncio
import logging
from unittest.mock import patch, AsyncMock, MagicMock

from src.research.synthesizer import GPT4Synthesizer, SynthesisType
from src.research.synthesizer.gpt4_turbo import APIError
from src.research.adapters import SourceResult, SourceType


# Sample data for tests
SAMPLE_QUERY = "What is climate change?"
SAMPLE_SOURCE_RESULTS = [
    SourceResult(
        title="Climate Change Overview",
        content="Climate change is a long-term change in global climate patterns...",
        source="Wikipedia",
        source_type=SourceType.WIKIPEDIA,
        url="https://en.wikipedia.org/wiki/Climate_change",
        metadata={"sections": ["Introduction", "Causes", "Effects"]}
    ),
    SourceResult(
        title="Effects of Climate Change",
        content="The effects of climate change include rising temperatures...",
        source="Website",
        source_type=SourceType.WEBSITE,
        url="https://example.com/climate-effects",
        metadata={}
    )
]

SAMPLE_API_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": "# Climate Change Summary\n\nClimate change refers to long-term shifts in temperatures and weather patterns..."
            }
        }
    ]
}


@pytest.fixture
def mock_env_api_key(monkeypatch):
    """Set a test API key in the environment."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key-12345")


@pytest.mark.asyncio
async def test_gpt4_synthesizer_initialization():
    """Test synthesizer initialization with different parameters."""
    # Test with explicit API key
    synthesizer = GPT4Synthesizer(
        api_key="explicit-key-12345",
        model="gpt-4-turbo-preview",
        temperature=0.5,
        max_tokens=2000,
        timeout=30,
        max_retries=2,
        retry_delay=1,
        fallback_model="gpt-3.5-turbo"
    )
    
    assert synthesizer.api_key == "explicit-key-12345"
    assert synthesizer.model == "gpt-4-turbo-preview"
    assert synthesizer.temperature == 0.5
    assert synthesizer.max_tokens == 2000
    assert synthesizer.timeout == 30
    assert synthesizer.max_retries == 2
    assert synthesizer.retry_delay == 1
    assert synthesizer.fallback_model == "gpt-3.5-turbo"


@pytest.mark.asyncio
async def test_gpt4_synthesizer_env_key(mock_env_api_key):
    """Test synthesizer initialization with environment API key."""
    synthesizer = GPT4Synthesizer()
    assert synthesizer.api_key == "test-api-key-12345"
    assert synthesizer.model == "gpt-4o"  # Default model


@pytest.mark.asyncio
async def test_synthesize_success():
    """Test successful synthesis."""
    synthesizer = GPT4Synthesizer(api_key="test-key")
    
    # Mock the API call
    with patch.object(synthesizer, '_call_gpt4_api_with_retry', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "# Test Results\n\nThis is a synthesized response."
        
        result = await synthesizer.synthesize(
            query=SAMPLE_QUERY,
            source_results=SAMPLE_SOURCE_RESULTS,
            synthesis_type=SynthesisType.SUMMARY
        )
        
        # Verify the result
        assert result is not None
        assert result.title == "Test Results"
        assert result.content == "# Test Results\n\nThis is a synthesized response."
        assert result.synthesis_type == SynthesisType.SUMMARY
        assert result.query == SAMPLE_QUERY
        assert result.sources_used == 2
        
        # Verify that API was called with the right parameters
        mock_call.assert_called_once()
        system_prompt, user_prompt = mock_call.call_args[0]
        assert "research assistant" in system_prompt.lower()  # From the SUMMARY prompt
        assert SAMPLE_QUERY in user_prompt


@pytest.mark.asyncio
async def test_synthesize_api_error():
    """Test handling of API errors."""
    synthesizer = GPT4Synthesizer(api_key="test-key", max_retries=2)
    
    # Mock the API call to raise an error
    with patch.object(synthesizer, '_call_gpt4_api_with_retry', new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = APIError("API error", status_code=500)
        
        # No fallback model is set explicitly (using the default)
        result = await synthesizer.synthesize(
            query=SAMPLE_QUERY,
            source_results=SAMPLE_SOURCE_RESULTS
        )
        
        # Should return None after failure
        assert result is None
        mock_call.assert_called_once()


@pytest.mark.asyncio
async def test_synthesize_fallback():
    """Test fallback to alternative model."""
    synthesizer = GPT4Synthesizer(
        api_key="test-key",
        model="gpt-4-turbo",
        fallback_model="gpt-3.5-turbo",
        max_retries=1
    )
    
    # First call fails, second call succeeds
    with patch.object(synthesizer, '_call_gpt4_api', new_callable=AsyncMock) as mock_api:
        # First call with primary model fails
        mock_api.side_effect = [
            APIError("Primary model failed", status_code=500),
            "# Fallback Results\n\nThis is from the fallback model."
        ]
        
        result = await synthesizer.synthesize(
            query=SAMPLE_QUERY,
            source_results=SAMPLE_SOURCE_RESULTS
        )
        
        # Should get results from fallback model
        assert result is not None
        assert result.title == "Fallback Results"
        assert "fallback model" in result.content
        
        # Should be called twice (once with primary, once with fallback)
        assert mock_api.call_count == 2
        
        # Verify the model was temporarily changed to fallback
        assert synthesizer.model == "gpt-4-turbo"  # Should be restored


@pytest.mark.asyncio
async def test_retry_mechanism():
    """Test the retry mechanism with exponential backoff."""
    synthesizer = GPT4Synthesizer(
        api_key="test-key",
        max_retries=3,
        retry_delay=1
    )
    
    # Mock sleep to avoid actual waiting
    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        # Mock API call to fail twice then succeed
        with patch.object(synthesizer, '_call_gpt4_api', new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = [
                Exception("First failure"),
                Exception("Second failure"),
                "# Success After Retries\n\nThis worked on the third try."
            ]
            
            result = await synthesizer._call_gpt4_api_with_retry("system", "user")
            
            # Should get the successful result
            assert result == "# Success After Retries\n\nThis worked on the third try."
            
            # Should have been called 3 times
            assert mock_api.call_count == 3
            
            # Should have slept with exponential backoff
            assert mock_sleep.call_count == 2
            assert mock_sleep.call_args_list[0][0][0] == 1  # First delay: 1
            assert mock_sleep.call_args_list[1][0][0] == 2  # Second delay: 2 (2^1 * base_delay)


@pytest.mark.asyncio
async def test_custom_synthesis():
    """Test custom synthesis with custom prompts."""
    synthesizer = GPT4Synthesizer(api_key="test-key")
    custom_prompt = "You are a climate science specialist. Analyze the following information:"
    
    # Mock the API call
    with patch.object(synthesizer, '_call_gpt4_api_with_retry', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "# Custom Analysis\n\nSpecialized climate analysis..."
        
        result = await synthesizer.custom_synthesis(
            query=SAMPLE_QUERY,
            source_results=SAMPLE_SOURCE_RESULTS,
            custom_prompt=custom_prompt
        )
        
        # Verify the result
        assert result is not None
        assert result.title == "Custom Analysis"
        assert "climate analysis" in result.content
        assert result.synthesis_type == SynthesisType.CUSTOM
        
        # Verify API was called with custom prompt
        mock_call.assert_called_once()
        system_prompt_arg, _ = mock_call.call_args[0]
        assert system_prompt_arg == custom_prompt


@pytest.mark.asyncio
async def test_api_call_with_success():
    """Test the direct API call with successful response."""
    synthesizer = GPT4Synthesizer(api_key="test-key")
    
    # Mock the httpx client response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_API_RESPONSE
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post.return_value = mock_response
    
    with patch('httpx.AsyncClient', return_value=mock_client):
        result = await synthesizer._call_gpt4_api("system prompt", "user prompt")
        
        # Should return the content from the first choice
        assert result == SAMPLE_API_RESPONSE["choices"][0]["message"]["content"]
        
        # Verify the request was made correctly
        post_call = mock_client.__aenter__.return_value.post
        post_call.assert_called_once()
        
        # Check auth header
        _, kwargs = post_call.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer test-key"
        
        # Check request body
        assert kwargs["json"]["messages"][0]["content"] == "system prompt"
        assert kwargs["json"]["messages"][1]["content"] == "user prompt"


@pytest.mark.asyncio
async def test_api_call_with_error():
    """Test the direct API call with error response."""
    synthesizer = GPT4Synthesizer(api_key="test-key")
    
    # Mock an error response
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.reason_phrase = "Bad Request"
    mock_response.json.return_value = {"error": {"message": "Invalid request"}}
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post.return_value = mock_response
    
    with patch('httpx.AsyncClient', return_value=mock_client):
        with pytest.raises(APIError) as excinfo:
            await synthesizer._call_gpt4_api("system prompt", "user prompt")
        
        # Check error details
        assert excinfo.value.status_code == 400
        assert "OpenAI API error: 400" in str(excinfo.value)
        assert "Invalid request" in excinfo.value.response_text


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 