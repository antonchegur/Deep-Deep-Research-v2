#!/usr/bin/env python3
"""
Error Handling Demo for Deep Deep Research.

This script demonstrates the comprehensive error handling capabilities 
of the GPT-4 Turbo integration, including error classification, fallback mechanisms,
and error tracking.
"""

import os
import sys
import asyncio
import logging
from typing import List, Dict, Any, Optional

# Add project root to path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.research.synthesizer.gpt4_turbo import GPT4Synthesizer
from src.research.synthesizer.base import SynthesisType
from src.research.adapters import SourceResult
from src.research.synthesizer.error_handling import (
    ResearchError, ErrorCategory, ErrorSeverity,
    error_tracker, fallback_manager
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Mock data for demonstration
SAMPLE_QUERY = "What are the economic impacts of climate change?"
SAMPLE_SOURCES = [
    SourceResult(
        source_id="1",
        title="Economic Consequences of Climate Change",
        url="https://example.com/climate-economics",
        content="Climate change is expected to reduce global GDP by up to 18% by 2050 if global temperatures rise by 3.2°C.",
        metadata={"relevance": 0.95}
    ),
    SourceResult(
        source_id="2",
        title="Agriculture and Climate Change",
        url="https://example.com/agriculture-climate",
        content="Changing weather patterns are projected to reduce crop yields by 30% in certain regions, impacting food security and prices worldwide.",
        metadata={"relevance": 0.87}
    ),
    SourceResult(
        source_id="3",
        title="Rising Sea Levels and Coastal Infrastructure",
        url="https://example.com/sea-levels",
        content="Sea level rise threatens infrastructure worth over $100 billion in coastal cities, requiring massive investment in adaptation measures.",
        metadata={"relevance": 0.82}
    )
]


async def demo_error_types():
    """Demonstrate different types of errors and their handling."""
    logger.info("=== DEMONSTRATING ERROR TYPES AND HANDLING ===")
    
    # 1. Authentication error (using an invalid API key)
    logger.info("\n1. Authentication Error Example:")
    try:
        synth = GPT4Synthesizer(api_key="invalid_key_12345", max_retries=1)
        await synth.synthesize(SAMPLE_QUERY, SAMPLE_SOURCES)
    except ResearchError as e:
        logger.info(f"✓ Caught error: {e.get_user_message()}")
        logger.info(f"  Category: {e.error_category.value}, Severity: {e.error_severity.value}")
        logger.info(f"  Retryable: {e.is_retryable}")
    
    # 2. Demonstrate token limit error
    logger.info("\n2. Token Limit Error Example (simulated):")
    # Create a huge input that would exceed token limits
    large_content = "This is a very long text. " * 10000
    large_sources = [
        SourceResult(
            source_id="large",
            title="Very Large Document",
            url="https://example.com/large",
            content=large_content,
            metadata={"relevance": 0.9}
        )
    ]
    
    synth = GPT4Synthesizer(
        api_key=os.environ.get("OPENAI_API_KEY", "sk-demo-key"),
        max_tokens=100  # Set unrealistically low to trigger error
    )
    
    # This won't actually make an API call because of our context manager logic
    result = await synth.synthesize(SAMPLE_QUERY, large_sources)
    logger.info(f"✓ Result: {result is None}")  # Should be None due to context size issues
    
    # Access recent errors from the error tracker
    errors = error_tracker.get_error_summary()
    logger.info(f"  Logged errors: {errors['total_errors']}")
    if errors['total_errors'] > 0:
        most_recent = errors['recent_errors'][-1]
        logger.info(f"  Most recent error: {most_recent['message']} ({most_recent['category']})")


async def demo_retry_mechanism():
    """Demonstrate the retry mechanism with exponential backoff."""
    logger.info("\n=== DEMONSTRATING RETRY MECHANISM ===")
    
    # Use monkey patching to simulate API errors
    original_call = GPT4Synthesizer._call_gpt4_api_with_messages
    
    # Counter for tracking call attempts
    call_counter = {"count": 0}
    
    # Mock API call that fails twice then succeeds
    async def mock_api_call(self, messages):
        call_counter["count"] += 1
        
        if call_counter["count"] <= 2:
            # Simulate a server error for the first two calls
            logger.info(f"  Attempt {call_counter['count']}: Simulating a server error")
            from src.research.synthesizer.error_handling import ServerError
            raise ServerError(f"Simulated server error (attempt {call_counter['count']})", status_code=503)
        
        # Succeed on the third attempt
        logger.info(f"  Attempt {call_counter['count']}: Simulating successful response")
        return "This is a mock success response after retries."
    
    try:
        # Replace the API call method with our mock
        GPT4Synthesizer._call_gpt4_api_with_messages = mock_api_call
        
        # Create synthesizer with retry settings
        synth = GPT4Synthesizer(
            api_key="dummy-key-for-demo",
            max_retries=3,
            retry_delay=1  # Short delay for demo purposes
        )
        
        logger.info("Calling API with retry mechanism (should retry twice then succeed):")
        result = await synth._call_gpt4_api_with_retry_and_context([{"role": "user", "content": "test"}])
        
        logger.info(f"Final result after {call_counter['count']} attempts: {result}")
    finally:
        # Restore the original method
        GPT4Synthesizer._call_gpt4_api_with_messages = original_call


async def demo_fallback_models():
    """Demonstrate fallback model mechanism."""
    logger.info("\n=== DEMONSTRATING FALLBACK MODELS ===")
    
    # Register fallback models
    fallback_manager.fallback_models = []
    fallback_manager.register_fallback_model("gpt-3.5-turbo", priority=1)
    fallback_manager.register_fallback_model("gpt-3.5-turbo-16k", priority=2)
    
    logger.info(f"Registered fallback models (in priority order): {fallback_manager.get_fallback_models()}")
    
    # Use monkey patching to simulate primary model failure
    original_call = GPT4Synthesizer._call_gpt4_api_with_messages
    
    # Mock API call that fails for primary model but succeeds for fallback
    async def mock_api_call(self, messages):
        if self.model == "gpt-4":
            logger.info(f"  API call with model '{self.model}': Simulating failure")
            from src.research.synthesizer.error_handling import ModelError
            raise ModelError(f"Simulated error with {self.model}", status_code=503)
        else:
            logger.info(f"  API call with model '{self.model}': Simulating success")
            return f"This is a mock response from the fallback model '{self.model}'."
    
    try:
        # Replace the API call method with our mock
        GPT4Synthesizer._call_gpt4_api_with_messages = mock_api_call
        
        # Create synthesizer with a primary model that will fail
        synth = GPT4Synthesizer(
            api_key="dummy-key-for-demo",
            model="gpt-4",
            max_retries=1
        )
        
        logger.info("Synthesizing with primary model (should fail and use fallback):")
        result = await synth.synthesize(SAMPLE_QUERY, SAMPLE_SOURCES[:1])
        
        if result:
            logger.info(f"✓ Successfully used fallback model: {result.content}")
        else:
            logger.info("✗ All models failed")
    finally:
        # Restore the original method
        GPT4Synthesizer._call_gpt4_api_with_messages = original_call


async def demo_custom_error_handlers():
    """Demonstrate custom error handlers."""
    logger.info("\n=== DEMONSTRATING CUSTOM ERROR HANDLERS ===")
    
    # Clear existing handlers
    fallback_manager.fallback_handlers = {cat: [] for cat in ErrorCategory}
    
    # Handler statistics
    handler_stats = {"calls": 0, "handled_categories": set()}
    
    # Create a custom handler for rate limit errors
    def rate_limit_handler(error):
        handler_stats["calls"] += 1
        handler_stats["handled_categories"].add(error.error_category.value)
        
        logger.info(f"  Custom handler processing {error.error_category.value} error")
        logger.info(f"  Error message: {error.message}")
        
        # In a real handler, we might implement special handling like:
        # - Scheduling a retry after the specified time
        # - Switching to a different API endpoint or key
        # - Notifying administrators of rate limit issues
        
        # Return True to indicate we handled the error
        return True
    
    # Register handlers for different error categories
    fallback_manager.register_fallback_handler(ErrorCategory.RATE_LIMIT, rate_limit_handler)
    fallback_manager.register_fallback_handler(ErrorCategory.SERVER, rate_limit_handler)
    
    logger.info("Registered custom handlers for rate limit and server errors")
    
    # Test with a rate limit error
    from src.research.synthesizer.error_handling import RateLimitError
    rate_error = RateLimitError("Too many requests", retry_after=30, status_code=429)
    
    logger.info("Handling a simulated rate limit error:")
    handled = fallback_manager.handle_error(rate_error)
    
    logger.info(f"✓ Error handled: {handled}")
    logger.info(f"  Handler called {handler_stats['calls']} times")
    logger.info(f"  Categories handled: {handler_stats['handled_categories']}")


async def demo_error_tracking():
    """Demonstrate error tracking and statistics."""
    logger.info("\n=== DEMONSTRATING ERROR TRACKING ===")
    
    # Clear the error tracker
    error_tracker.clear()
    
    # Create various error types
    from src.research.synthesizer.error_handling import (
        AuthenticationError, RateLimitError, TokenLimitError, 
        TimeoutError, ServerError
    )
    
    # Record several errors of different types
    errors = [
        AuthenticationError("Invalid API key", status_code=401),
        RateLimitError("Rate limit exceeded", status_code=429, retry_after=60),
        TokenLimitError("Context length exceeded", status_code=400),
        TimeoutError("Request timed out after 30 seconds"),
        ServerError("Internal server error", status_code=500),
        ServerError("Service unavailable", status_code=503)
    ]
    
    for error in errors:
        logger.info(f"Recording error: {error.error_category.value} - {error.message}")
        error_tracker.record_error(error)
    
    # Get error statistics
    stats = error_tracker.get_error_summary()
    
    logger.info(f"Error tracking statistics:")
    logger.info(f"  Total errors: {stats['total_errors']}")
    logger.info(f"  By category: {stats['categories']}")
    logger.info(f"  By severity: {stats['severities']}")
    
    # Show most recent errors
    logger.info("Most recent errors:")
    for i, error in enumerate(stats['recent_errors'][-3:], 1):
        logger.info(f"  {i}. [{error['category']}] {error['message']}")


async def main():
    """Run all demo functions."""
    logger.info("STARTING ERROR HANDLING DEMO")
    
    try:
        await demo_error_types()
        await demo_retry_mechanism()
        await demo_fallback_models()
        await demo_custom_error_handlers()
        await demo_error_tracking()
    except Exception as e:
        logger.error(f"Demo encountered an error: {e}")
    
    logger.info("\nDEMO COMPLETED")


if __name__ == "__main__":
    asyncio.run(main()) 