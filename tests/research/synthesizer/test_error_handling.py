"""
Tests for error handling in the research synthesizer.
"""

import pytest
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import httpx

from src.research.synthesizer.error_handling import (
    ResearchError, ErrorCategory, ErrorSeverity,
    AuthenticationError, RateLimitError, ModelError, 
    ContentFilterError, TokenLimitError, TimeoutError,
    ConnectionError, ServerError, InputError, OutputError, ContextError,
    classify_openai_error, classify_network_error,
    error_tracker, fallback_manager
)
from src.research.synthesizer.gpt4_turbo import GPT4Synthesizer
from src.research.adapters import SourceResult
from src.research.synthesizer.base import SynthesisType, SourceType

# Sample data for testing
SAMPLE_QUERY = "What are the effects of climate change on biodiversity?"
SAMPLE_SOURCE_RESULTS = [
    SourceResult(
        title="Climate Change Impact on Ecosystems",
        content="Climate change affects biodiversity in multiple ways.",
        source_name="Example Source",
        source_type=SourceType.WEB_SEARCH,
        url="https://example.com/climate1",
        metadata={"relevance": 0.95}
    ),
    SourceResult(
        title="Biodiversity Loss",
        content="Species are going extinct at an alarming rate due to habitat loss and climate change.",
        source_name="Example Source",
        source_type=SourceType.WEB_SEARCH,
        url="https://example.com/biodiversity",
        metadata={"relevance": 0.85}
    )
]


def test_research_error_initialization():
    """Test basic ResearchError initialization and properties."""
    error = ResearchError(
        message="Test error message",
        error_category=ErrorCategory.RATE_LIMIT,
        error_severity=ErrorSeverity.HIGH,
        status_code=429,
        response_text="Rate limit exceeded",
        is_retryable=True,
        retry_after=30
    )
    
    assert error.message == "Test error message"
    assert error.error_category == ErrorCategory.RATE_LIMIT
    assert error.error_severity == ErrorSeverity.HIGH
    assert error.status_code == 429
    assert error.response_text == "Rate limit exceeded"
    assert error.is_retryable
    assert error.retry_after == 30
    assert str(error) == "Test error message"


def test_research_error_to_dict():
    """Test conversion of ResearchError to dictionary."""
    error = ResearchError(
        message="Test error message",
        error_category=ErrorCategory.CONTENT_FILTER,
        error_severity=ErrorSeverity.HIGH
    )
    
    error_dict = error.to_dict()
    
    assert error_dict["message"] == "Test error message"
    assert error_dict["category"] == "content_filter"
    assert error_dict["severity"] == "high"
    assert "timestamp" in error_dict
    

def test_specialized_error_classes():
    """Test specialized error subclasses."""
    auth_error = AuthenticationError("Invalid API key")
    assert auth_error.error_category == ErrorCategory.AUTHENTICATION
    assert auth_error.error_severity == ErrorSeverity.HIGH
    assert not auth_error.is_retryable
    
    rate_limit_error = RateLimitError("Too many requests", retry_after=60)
    assert rate_limit_error.error_category == ErrorCategory.RATE_LIMIT
    assert rate_limit_error.retry_after == 60
    
    content_filter_error = ContentFilterError("Content policy violation")
    assert content_filter_error.error_category == ErrorCategory.CONTENT_FILTER
    assert not content_filter_error.is_retryable


def test_user_friendly_messages():
    """Test user-friendly error messages."""
    auth_error = AuthenticationError("Invalid API key")
    assert "Authentication error" in auth_error.get_user_message()
    assert "Invalid API key" in auth_error.get_user_message()
    
    timeout_error = TimeoutError("Request timed out after 60s")
    assert "Request timed out" in timeout_error.get_user_message()


def test_classify_openai_error():
    """Test OpenAI error classification based on status codes and messages."""
    # Authentication error
    error = classify_openai_error(401, "Invalid Authentication", "Invalid API key")
    assert isinstance(error, AuthenticationError)
    
    # Rate limit error
    rate_limit_response = json.dumps({"error": {"message": "Rate limit exceeded", "retry_after": 30}})
    error = classify_openai_error(429, "Too many requests", rate_limit_response)
    assert isinstance(error, RateLimitError)
    
    # Token limit error
    error = classify_openai_error(400, "This model's maximum context length is 8192 tokens", "")
    assert isinstance(error, TokenLimitError)
    
    # Content filter error
    error = classify_openai_error(400, "Your request was rejected as a result of our safety system", "")
    assert isinstance(error, ContentFilterError)
    
    # Model error
    error = classify_openai_error(400, "The model 'xyz' does not exist", "")
    assert isinstance(error, ModelError)
    
    # Server error
    error = classify_openai_error(500, "Internal server error", "")
    assert isinstance(error, ServerError)


def test_classify_network_error():
    """Test network error classification."""
    timeout_exc = httpx.TimeoutException("Request timed out")
    error = classify_network_error(timeout_exc)
    assert isinstance(error, TimeoutError)
    
    connect_exc = httpx.ConnectError("Connection refused")
    error = classify_network_error(connect_exc)
    assert isinstance(error, ConnectionError)


def test_error_tracker():
    """Test error tracking functionality."""
    # Clear the tracker first
    error_tracker.clear()
    
    # Add some errors
    error1 = AuthenticationError("Invalid API key")
    error2 = RateLimitError("Too many requests")
    error3 = TimeoutError("Request timed out")
    
    error_tracker.record_error(error1)
    error_tracker.record_error(error2)
    error_tracker.record_error(error3)
    
    # Check summary
    summary = error_tracker.get_error_summary()
    assert summary["total_errors"] == 3
    assert summary["categories"]["authentication"] == 1
    assert summary["categories"]["rate_limit"] == 1
    assert summary["categories"]["timeout"] == 1
    assert len(summary["recent_errors"]) == 3


def test_fallback_manager():
    """Test fallback manager registration and prioritization."""
    # Clear existing models
    fallback_manager.fallback_models = []
    
    # Register fallback models
    fallback_manager.register_fallback_model("gpt-3.5-turbo", priority=1)
    fallback_manager.register_fallback_model("gpt-3.5-turbo-16k", priority=2)
    fallback_manager.register_fallback_model("text-davinci-003", priority=0)
    
    # Check priority order
    models = fallback_manager.get_fallback_models()
    assert models[0] == "gpt-3.5-turbo-16k"  # Highest priority
    assert models[1] == "gpt-3.5-turbo"
    assert models[2] == "text-davinci-003"  # Lowest priority


@pytest.mark.asyncio
async def test_gpt4_synthesizer_authentication_error():
    """Test handling of authentication errors in GPT4Synthesizer."""
    # Create a synthesizer with invalid API key
    synthesizer = GPT4Synthesizer(api_key="invalid-key", max_retries=1)
    
    # Mock the API call to raise an authentication error
    with patch.object(synthesizer, '_call_gpt4_api_with_messages', new_callable=AsyncMock) as mock_call:
        auth_error = AuthenticationError("Invalid API key", status_code=401)
        mock_call.side_effect = auth_error
        
        # Call synthesize method
        with pytest.raises(ResearchError) as excinfo:
            await synthesizer.synthesize(
                query=SAMPLE_QUERY,
                source_results=SAMPLE_SOURCE_RESULTS
            )
        
        # Verify the error
        assert excinfo.value.error_category == ErrorCategory.AUTHENTICATION
        assert excinfo.value.status_code == 401
        # Verify it didn't retry (since auth errors are not retryable)
        assert mock_call.call_count == 1


@pytest.mark.asyncio
async def test_gpt4_synthesizer_retry_logic():
    """Test the retry logic in GPT4Synthesizer."""
    synthesizer = GPT4Synthesizer(api_key="test-key", max_retries=3, retry_delay=0.1)
    
    # Mock sleep to avoid actual waiting
    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        # Mock API call to fail twice with retryable errors then succeed
        with patch.object(synthesizer, '_call_gpt4_api_with_messages', new_callable=AsyncMock) as mock_call:
            server_error = ServerError("Server overloaded", status_code=503)
            timeout_error = TimeoutError("Request timed out")
            
            mock_call.side_effect = [
                server_error,    # First call fails with server error
                timeout_error,   # Second call fails with timeout
                "Success response"  # Third call succeeds
            ]
            
            # Call API with retry
            result = await synthesizer._call_gpt4_api_with_retry_and_context([{"role": "user", "content": "test"}])
            
            # Verify result and retry behavior
            assert result == "Success response"
            assert mock_call.call_count == 3
            assert mock_sleep.call_count == 2  # Should sleep between retries


@pytest.mark.asyncio
async def test_gpt4_synthesizer_fallback_models():
    """Test fallback model mechanism in GPT4Synthesizer."""
    # First, register fallback models
    fallback_manager.fallback_models = []
    fallback_manager.register_fallback_model("gpt-3.5-turbo", priority=1)
    
    synthesizer = GPT4Synthesizer(api_key="test-key", model="gpt-4", max_retries=1)
    
    # Mock the primary model to fail but fallback to succeed
    with patch.object(synthesizer, '_call_gpt4_api_with_messages', new_callable=AsyncMock) as mock_call:
        # First call with primary model fails
        model_error = ModelError("Model overloaded", status_code=503)
        
        # Set up the mock to fail for gpt-4 but succeed for gpt-3.5-turbo
        def side_effect(*args, **kwargs):
            if synthesizer.model == "gpt-4":
                raise model_error
            else:
                return "Fallback model response"
        
        mock_call.side_effect = side_effect
        
        # Call synthesize
        result = await synthesizer.synthesize(
            query=SAMPLE_QUERY,
            source_results=SAMPLE_SOURCE_RESULTS
        )
        
        # Verify fallback worked
        assert result is not None
        assert "Fallback model response" in result.content
        assert mock_call.call_count >= 2  # Called at least twice (once for primary, once for fallback)


@pytest.mark.asyncio
async def test_error_with_retry_after():
    """Test handling of errors with retry-after directive."""
    synthesizer = GPT4Synthesizer(api_key="test-key", max_retries=2, retry_delay=1)
    
    # Mock sleep to avoid actual waiting
    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        # Mock API call to fail with rate limit error that includes retry_after
        with patch.object(synthesizer, '_call_gpt4_api_with_messages', new_callable=AsyncMock) as mock_call:
            rate_limit_error = RateLimitError(
                "Rate limit exceeded",
                status_code=429,
                retry_after=5  # Explicit retry-after time
            )
            
            mock_call.side_effect = [
                rate_limit_error,  # First call fails with rate limit
                "Success after waiting"  # Second call succeeds
            ]
            
            # Call API with retry
            result = await synthesizer._call_gpt4_api_with_retry_and_context([{"role": "user", "content": "test"}])
            
            # Verify result and sleep behavior
            assert result == "Success after waiting"
            assert mock_call.call_count == 2
            
            # Should use the retry_after value (5) instead of calculated backoff
            mock_sleep.assert_called_once_with(5)


def test_error_handlers():
    """Test custom error handlers in fallback manager."""
    # Clear existing handlers
    fallback_manager.fallback_handlers = {cat: [] for cat in ErrorCategory}
    
    # Create a test handler that counts calls
    handler_called = {"count": 0, "category": None}
    
    def test_handler(error):
        handler_called["count"] += 1
        handler_called["category"] = error.error_category
        return True  # Successfully handled
    
    # Register handler for rate limit errors
    fallback_manager.register_fallback_handler(ErrorCategory.RATE_LIMIT, test_handler)
    
    # Test handler with matching error
    rate_limit_error = RateLimitError("Too many requests")
    result = fallback_manager.handle_error(rate_limit_error)
    
    assert result is True  # Handler returned True
    assert handler_called["count"] == 1
    assert handler_called["category"] == ErrorCategory.RATE_LIMIT
    
    # Test with non-matching error
    auth_error = AuthenticationError("Invalid API key")
    result = fallback_manager.handle_error(auth_error)
    
    assert result is False  # No handler for this category
    assert handler_called["count"] == 1  # Didn't increase 