"""
GPT-4 Turbo implementation for research synthesis.
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union

import httpx

from ..adapters import SourceResult
from .base import BaseSynthesizer, SynthesisResult, SynthesisType
from .prompt_engineering import PromptLibrary, PromptEvaluator
from .context_management import ContextManager
from .error_handling import (
    ResearchError, ErrorCategory, ErrorSeverity,
    classify_openai_error, classify_network_error,
    error_tracker, fallback_manager
)


logger = logging.getLogger(__name__)


class GPT4Synthesizer(BaseSynthesizer):
    """
    Research synthesizer using OpenAI's GPT-4 Turbo.
    
    This synthesizer uses GPT-4 Turbo to analyze and synthesize research data from
    multiple sources. It supports different types of synthesis and customizable prompts.
    """
    
    # OpenAI API constants
    API_URL = "https://api.openai.com/v1/chat/completions"
    DEFAULT_MODEL = "gpt-4o"
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None,
                temperature: float = 0.2, max_tokens: int = 4000,
                timeout: int = 60, max_retries: int = 3, retry_delay: int = 2,
                fallback_model: Optional[str] = "gpt-3.5-turbo",
                prompt_templates_dir: Optional[str] = None,
                context_compression_level: int = 1):
        """
        Initialize the GPT-4 Turbo synthesizer.
        
        Args:
            api_key: OpenAI API key. If None, read from environment variable
            model: GPT model to use. If None, use default model
            temperature: Temperature for generation (0.0 to 1.0)
            max_tokens: Maximum tokens for generation
            timeout: Timeout for API requests in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Base delay between retries in seconds (exponential backoff will be applied)
            fallback_model: Model to use if primary model fails or is unavailable
            prompt_templates_dir: Directory containing custom prompt templates
            context_compression_level: Level of context compression (0-3)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not provided. Set it in the constructor or OPENAI_API_KEY environment variable.")
        
        self.model = model or self.DEFAULT_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize error handling
        if fallback_model and fallback_model != self.model:
            fallback_manager.register_fallback_model(fallback_model, priority=1)
        
        # Initialize prompt library and evaluator
        self.prompt_library = PromptLibrary(templates_dir=prompt_templates_dir)
        self.prompt_evaluator = PromptEvaluator()
        
        # Initialize context manager
        self.context_manager = ContextManager(
            model=self.model,
            response_tokens=self.max_tokens,
            compression_level=context_compression_level
        )
    
    async def synthesize(self, query: str, 
                        source_results: List[SourceResult],
                        synthesis_type: SynthesisType = SynthesisType.COMPREHENSIVE,
                        language: str = "en") -> Optional[SynthesisResult]:
        """
        Synthesize research from source results using GPT-4 Turbo.
        
        Args:
            query: Research question or topic
            source_results: List of source results to analyze
            synthesis_type: Type of synthesis to perform
            language: Language code for the output
            
        Returns:
            Synthesis result or None if synthesis fails
            
        Raises:
            ResearchError: If an error occurs during synthesis
        """
        # Validate inputs
        if not self.api_key:
            error = ResearchError(
                "API key is required for GPT-4 synthesis",
                error_category=ErrorCategory.AUTHENTICATION,
                error_severity=ErrorSeverity.HIGH,
                is_retryable=False
            )
            error_tracker.record_error(error)
            raise error
        
        if not source_results:
            logger.warning("No source results provided for synthesis")
            return None
        
        # Generate prompts using the prompt library
        try:
            prompts = self.prompt_library.create_prompt(
                query=query,
                source_results=source_results,
                synthesis_type=synthesis_type,
                language=language
            )
            system_prompt = prompts["system_prompt"]
            user_prompt = prompts["user_prompt"]
        except ValueError as e:
            error = ResearchError(
                f"Error creating prompts: {e}",
                error_category=ErrorCategory.INPUT,
                error_severity=ErrorSeverity.MEDIUM,
                is_retryable=False,
                original_exception=e
            )
            error_tracker.record_error(error)
            logger.error(f"Error creating prompts: {e}")
            return None
        
        # Clear previous context and set up new context
        self.context_manager.clear_context()
        
        # Add system prompt to context
        if not self.context_manager.add_system_prompt(system_prompt):
            error = ResearchError(
                "System prompt too large for context window",
                error_category=ErrorCategory.CONTEXT,
                error_severity=ErrorSeverity.MEDIUM,
                is_retryable=False
            )
            error_tracker.record_error(error)
            logger.error("System prompt too large for context window")
            return None
        
        # Instead of including all sources in one go, process them through context manager
        sources_added = self.context_manager.add_sources(
            sources=source_results,
            max_tokens=int(self.context_manager.token_limit * 0.7)  # Use up to 70% for sources
        )
        
        if sources_added == 0:
            logger.warning("No sources could be added to context")
            
        # Add user query
        query_text = f"Research Query: {query}\nPlease synthesize the information from the provided sources to address this query, using {language} language."
        if not self.context_manager.add_user_input(query_text, priority=90):
            logger.warning("Could not add user query to context")
        
        # Build messages for API request
        messages = self.context_manager.build_messages()
        
        if not messages:
            error = ResearchError(
                "No messages to send to API",
                error_category=ErrorCategory.CONTEXT,
                error_severity=ErrorSeverity.MEDIUM,
                is_retryable=False
            )
            error_tracker.record_error(error)
            logger.error("No messages to send to API")
            return None
        
        # Call GPT-4 Turbo API with retry and fallback
        try:
            response_text = await self._call_gpt4_api_with_retry_and_context(messages)
            if not response_text:
                return None
        except ResearchError as e:
            logger.error(f"Failed to call GPT-4 API: {e.get_user_message()}")
            
            # Try fallback models if available
            fallback_models = fallback_manager.get_fallback_models()
            if fallback_models:
                for fallback_model in fallback_models:
                    logger.info(f"Attempting to use fallback model: {fallback_model}")
                    try:
                        original_model = self.model
                        self.model = fallback_model
                        
                        # Update context manager's model
                        self.context_manager = ContextManager(
                            model=self.model,
                            response_tokens=self.max_tokens,
                            compression_level=self.context_manager.compression_level
                        )
                        
                        # Set up context again with fallback model
                        self.context_manager.clear_context()
                        self.context_manager.add_system_prompt(system_prompt)
                        self.context_manager.add_sources(source_results, max_tokens=int(self.context_manager.token_limit * 0.7))
                        self.context_manager.add_user_input(query_text, priority=90)
                        
                        # Call API with fallback model
                        messages = self.context_manager.build_messages()
                        response_text = await self._call_gpt4_api_with_retry_and_context(messages)
                        
                        if response_text:
                            # Restore original model and log success
                            logger.info(f"Successfully used fallback model: {fallback_model}")
                            self.model = original_model
                            break
                        
                    except ResearchError as fallback_error:
                        logger.error(f"Fallback model {fallback_model} also failed: {fallback_error.get_user_message()}")
                        self.model = original_model  # Restore original model
                
                # If we still don't have a response after trying all fallbacks
                if not response_text:
                    return None
            else:
                # Try to handle the error with registered handlers
                if not fallback_manager.handle_error(e):
                    return None
        
        # Parse the response
        synthesis_result = self._parse_response(
            response_text=response_text,
            query=query,
            source_results=source_results,
            synthesis_type=synthesis_type,
            language=language
        )
        
        # Log prompt evaluation metrics if we have a result
        if synthesis_result:
            template = self.prompt_library.get_template_for_synthesis(synthesis_type)
            if template:
                # Basic metrics for now - can be expanded
                metrics = {
                    "token_count": len(response_text.split()) * 1.3,  # Rough estimate
                    "sources_cited": synthesis_result.sources_used,
                    "has_sections": len(synthesis_result.sections) > 0
                }
                
                self.prompt_evaluator.log_result(
                    template_id=template.template_id,
                    version=template.version,
                    synthesis_type=synthesis_type,
                    metrics=metrics,
                    query=query
                )
        
        return synthesis_result
    
    async def custom_synthesis(self, query: str,
                              source_results: List[SourceResult],
                              custom_prompt: str,
                              language: str = "en") -> Optional[SynthesisResult]:
        """
        Perform synthesis with a custom prompt template.
        
        Args:
            query: Research question
            source_results: List of source results to analyze
            custom_prompt: Custom prompt template
            language: Language code for the output
            
        Returns:
            Synthesis result or None if synthesis fails
            
        Raises:
            ResearchError: If an error occurs during synthesis
        """
        # Validate inputs
        if not self.api_key:
            error = ResearchError(
                "API key is required for GPT-4 synthesis",
                error_category=ErrorCategory.AUTHENTICATION,
                error_severity=ErrorSeverity.HIGH,
                is_retryable=False
            )
            error_tracker.record_error(error)
            raise error
        
        if not source_results:
            logger.warning("No source results provided for synthesis")
            return None
        
        # Generate prompts using the prompt library
        try:
            prompts = self.prompt_library.create_prompt(
                query=query,
                source_results=source_results,
                synthesis_type=SynthesisType.CUSTOM,
                language=language,
                custom_system_prompt=custom_prompt
            )
            system_prompt = prompts["system_prompt"]
            user_prompt = prompts["user_prompt"]
        except ValueError as e:
            error = ResearchError(
                f"Error creating prompts: {e}",
                error_category=ErrorCategory.INPUT,
                error_severity=ErrorSeverity.MEDIUM,
                is_retryable=False,
                original_exception=e
            )
            error_tracker.record_error(error)
            logger.error(f"Error creating prompts: {e}")
            return None
        
        # Clear previous context and set up new context
        self.context_manager.clear_context()
        
        # Add system prompt to context
        if not self.context_manager.add_system_prompt(system_prompt):
            error = ResearchError(
                "System prompt too large for context window",
                error_category=ErrorCategory.CONTEXT,
                error_severity=ErrorSeverity.MEDIUM,
                is_retryable=False
            )
            error_tracker.record_error(error)
            logger.error("System prompt too large for context window")
            return None
        
        # Process sources through context manager
        sources_added = self.context_manager.add_sources(
            sources=source_results,
            max_tokens=int(self.context_manager.token_limit * 0.7)
        )
        
        if sources_added == 0:
            logger.warning("No sources could be added to context")
            
        # Add user query
        query_text = f"Research Query: {query}\nPlease synthesize the information from the provided sources using {language} language."
        if not self.context_manager.add_user_input(query_text, priority=90):
            logger.warning("Could not add user query to context")
        
        # Build messages for API request
        messages = self.context_manager.build_messages()
        
        if not messages:
            error = ResearchError(
                "No messages to send to API",
                error_category=ErrorCategory.CONTEXT,
                error_severity=ErrorSeverity.MEDIUM,
                is_retryable=False
            )
            error_tracker.record_error(error)
            logger.error("No messages to send to API")
            return None
        
        # Call GPT-4 Turbo API with retry and fallback
        try:
            response_text = await self._call_gpt4_api_with_retry_and_context(messages)
            if not response_text:
                return None
        except ResearchError as e:
            logger.error(f"Failed to call GPT-4 API: {e.get_user_message()}")
            
            # Try fallback models if available
            fallback_models = fallback_manager.get_fallback_models()
            if fallback_models:
                for fallback_model in fallback_models:
                    logger.info(f"Attempting to use fallback model: {fallback_model}")
                    try:
                        original_model = self.model
                        self.model = fallback_model
                        
                        # Update context manager's model
                        self.context_manager = ContextManager(
                            model=self.model,
                            response_tokens=self.max_tokens,
                            compression_level=self.context_manager.compression_level
                        )
                        
                        # Set up context again with fallback model
                        self.context_manager.clear_context()
                        self.context_manager.add_system_prompt(system_prompt)
                        self.context_manager.add_sources(source_results, max_tokens=int(self.context_manager.token_limit * 0.7))
                        self.context_manager.add_user_input(query_text, priority=90)
                        
                        # Call API with fallback model
                        messages = self.context_manager.build_messages()
                        response_text = await self._call_gpt4_api_with_retry_and_context(messages)
                        
                        if response_text:
                            # Restore original model and log success
                            logger.info(f"Successfully used fallback model: {fallback_model}")
                            self.model = original_model
                            break
                        
                    except ResearchError as fallback_error:
                        logger.error(f"Fallback model {fallback_model} also failed: {fallback_error.get_user_message()}")
                        self.model = original_model  # Restore original model
                
                # If we still don't have a response after trying all fallbacks
                if not response_text:
                    return None
            else:
                # Try to handle the error with registered handlers
                if not fallback_manager.handle_error(e):
                    return None
        
        # Parse the response
        synthesis_result = self._parse_response(
            response_text=response_text,
            query=query,
            source_results=source_results,
            synthesis_type=SynthesisType.CUSTOM,
            language=language,
            custom_prompt=custom_prompt
        )
        
        return synthesis_result
    
    def save_prompt_templates(self, directory: str):
        """
        Save prompt templates to the specified directory.
        
        Args:
            directory: Directory to save templates
        """
        self.prompt_library.save_templates(directory)
    
    def save_prompt_evaluations(self, file_path: str):
        """
        Save prompt evaluation results to a file.
        
        Args:
            file_path: Path to save evaluation results
        """
        self.prompt_evaluator.save_results(file_path)
    
    def get_prompt_comparison(self, template_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get comparison metrics for prompt templates.
        
        Args:
            template_ids: List of template IDs to compare (if None, compare all)
            
        Returns:
            Comparison metrics
        """
        if template_ids is None:
            template_ids = list(self.prompt_library.templates.keys())
            
        return self.prompt_evaluator.compare_prompts(template_ids)
    
    async def _call_gpt4_api_with_retry_and_context(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        Call OpenAI API with context management, retry logic and exponential backoff.
        
        Args:
            messages: List of message dictionaries (role and content)

        Returns:
            Response text from the API or None if all retries fail
            
        Raises:
            ResearchError: If API calls fail after all retries
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return await self._call_gpt4_api_with_messages(messages)
            except ResearchError as e:
                last_error = e
                
                # Don't retry certain error categories
                if not e.is_retryable:
                    error_tracker.record_error(e)
                    raise
                
                # Use specific retry_after if provided, otherwise calculate with exponential backoff
                if e.retry_after:
                    delay = e.retry_after
                else:
                    # Calculate delay with exponential backoff (2^attempt * base_delay)
                    delay = self.retry_delay * (2 ** attempt)
                
                # Log the error and retry
                if attempt < self.max_retries - 1:
                    logger.warning(f"API call failed, retrying in {delay}s: {e.get_user_message()}")
                    await asyncio.sleep(delay)
                else:
                    error_tracker.record_error(e)
                    logger.error(f"API call failed after {self.max_retries} attempts: {e.get_user_message()}")
            except Exception as e:
                # Unexpected error - convert to ResearchError
                last_error = classify_network_error(e)
                
                # Calculate delay with exponential backoff
                delay = self.retry_delay * (2 ** attempt)
                
                # Log and retry
                if attempt < self.max_retries - 1:
                    logger.warning(f"Unexpected error, retrying in {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    error_tracker.record_error(last_error)
                    logger.error(f"API call failed after {self.max_retries} attempts due to unexpected error: {str(e)}")
                    
        # If we get here, all retries failed - raise the last error
        if last_error:
            raise last_error
        
        return None
    
    async def _call_gpt4_api_with_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Call OpenAI's API for GPT-4 completion with prepared messages.
        
        Args:
            messages: List of message dictionaries (role and content)
            
        Returns:
            The text response from the model
            
        Raises:
            ResearchError: If the API request fails
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.API_URL, headers=headers, json=data)
                
                if response.status_code != 200:
                    error_detail = ""
                    try:
                        error_data = response.json()
                        error_detail = json.dumps(error_data, indent=4)
                    except Exception:
                        error_detail = response.text
                    
                    logger.error(f"HTTP error from GPT-4 API: {response.status_code} - {response.reason_phrase}")
                    logger.error(f"Error details: {error_detail}")
                    
                    # Classify and raise the appropriate error
                    error_message = f"OpenAI API error: {response.status_code}"
                    if error_detail:
                        try:
                            data = json.loads(error_detail)
                            if "error" in data and "message" in data["error"]:
                                error_message = data["error"]["message"]
                        except:
                            pass
                    
                    error = classify_openai_error(
                        status_code=response.status_code,
                        error_message=error_message,
                        response_text=error_detail
                    )
                    raise error
                
                response_data = response.json()
                content = response_data["choices"][0]["message"]["content"]
                return content
                
        except httpx.TimeoutException as e:
            logger.error(f"API request timed out: {e}")
            error = classify_network_error(e)
            raise error
        except httpx.RequestError as e:
            logger.error(f"HTTP request error: {e}")
            error = classify_network_error(e)
            raise error
        except Exception as e:
            logger.error(f"Unexpected error calling GPT-4 API: {e}")
            if not isinstance(e, ResearchError):
                error = ResearchError(
                    f"Unexpected error: {e}",
                    error_category=ErrorCategory.UNKNOWN,
                    error_severity=ErrorSeverity.HIGH,
                    original_exception=e
                )
                raise error
            raise
    
    # Keep this method for backward compatibility
    async def _call_gpt4_api_with_retry(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Legacy method for API calls with retry logic.
        
        Args:
            system_prompt: The system prompt that guides the model behavior
            user_prompt: The user prompt containing the research query and source data

        Returns:
            Response text from the API or None if all retries fail
            
        Raises:
            ResearchError: If API calls fail after all retries
        """
        # Set up context with system and user prompts
        self.context_manager.clear_context()
        self.context_manager.add_system_prompt(system_prompt)
        self.context_manager.add_user_input(user_prompt)
        
        # Build messages and call API
        messages = self.context_manager.build_messages()
        return await self._call_gpt4_api_with_retry_and_context(messages)
    
    # Keep this method for backward compatibility
    async def _call_gpt4_api(self, system_prompt: str, user_prompt: str) -> str:
        """
        Legacy method for direct API calls.
        
        Args:
            system_prompt: The system prompt that guides the model behavior
            user_prompt: The user prompt containing the research query and source data
            
        Returns:
            The text response from the model
            
        Raises:
            ResearchError: If the API request fails
        """
        # Convert prompts to messages format
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self._call_gpt4_api_with_messages(messages)
    
    def _format_user_prompt(self, query: str, source_results: List[SourceResult], 
                           language: str) -> str:
        """
        Format the user prompt with source data.
        
        Note: This method is kept for backward compatibility but delegates
        to the prompt library for actual formatting.
        
        Args:
            query: Research query
            source_results: List of source results
            language: Target language code
            
        Returns:
            Formatted user prompt
        """
        # Use the prompt library to format sources
        formatted_sources = self.prompt_library.format_sources(source_results)
        
        # Create a basic user prompt
        prompt = f"Research Query: {query}\n\nSources:\n{formatted_sources}\n\n"
        prompt += f"Please synthesize the information from these sources to address the research query.\n"
        prompt += f"Use {language} language for your response."
        
        return prompt
    
    def _parse_response(self, response_text: str, query: str, 
                       source_results: List[SourceResult],
                       synthesis_type: SynthesisType,
                       language: str,
                       custom_prompt: str = "") -> SynthesisResult:
        """
        Parse the GPT-4 response into a structured synthesis result.
        
        Args:
            response_text: GPT-4 response text
            query: Original research query
            source_results: Source results used
            synthesis_type: Type of synthesis performed
            language: Language code
            custom_prompt: Custom prompt if used
            
        Returns:
            Structured synthesis result
        """
        # Extract title (first line if it looks like a title)
        lines = response_text.strip().split("\n")
        title = lines[0].strip()
        
        # If title is too long or has special characters, generate a simpler one
        if len(title) > 100 or any(c in title for c in ["#", "=", "-", "*", "+"]):
            title = f"Research Synthesis: {query[:50]}"
        
        # Extract sections from markdown headers
        sections = {}
        current_section = None
        current_content = []
        
        for line in lines[1:]:  # Skip the title line
            if re.match(r"^#{1,3} ", line):  # Match headings (# to ###)
                # If we were building a section, save it
                if current_section is not None:
                    sections[current_section] = "\n".join(current_content).strip()
                
                # Start a new section
                current_section = line.lstrip("#").strip()
                current_content = []
            else:
                # Add line to current section
                current_content.append(line)
        
        # Add the last section if we were building one
        if current_section is not None:
            sections[current_section] = "\n".join(current_content).strip()
        
        # Extract citations if any are present (this is a simple extraction and could be improved)
        citations = []
        citation_pattern = r"\[(\d+)\]"
        citation_matches = re.findall(citation_pattern, response_text)
        
        if citation_matches:
            # Create simple citation objects for matched references
            for idx in set(citation_matches):
                if int(idx) <= len(source_results):
                    source = source_results[int(idx) - 1]
                    citations.append({
                        "index": idx,
                        "title": source.title,
                        "source": source.source,
                        "url": source.url
                    })
        
        # Build metadata
        metadata = {
            "model": self.model,
            "synthesis_type": synthesis_type.value
        }
        
        if custom_prompt:
            metadata["custom_prompt"] = True
        
        # Create and return the synthesis result
        return SynthesisResult(
            title=title,
            content=response_text,
            synthesis_type=synthesis_type,
            query=query,
            sections=sections,
            citations=citations,
            sources_used=len(source_results),
            language=language,
            metadata=metadata
        ) 