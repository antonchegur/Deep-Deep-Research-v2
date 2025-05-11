"""
Language Context Management Utilities

This module provides context managers and utility functions for managing language
context within code blocks.
"""

from contextlib import contextmanager
from typing import Generator, Optional

from src.multilingual.config import Language, get_current_language, set_current_language


@contextmanager
def language_context(language: Language) -> Generator[None, None, None]:
    """
    Context manager for temporarily changing the current language.
    
    Args:
        language: The language to set as current within the context
        
    Yields:
        None
        
    Example:
        ```python
        with language_context(Language.RUSSIAN):
            # Code in this block will use Russian as the current language
            text = translate("Hello, world!")  # Will be translated to Russian
        # After the block, the original language is restored
        ```
    """
    previous_language = get_current_language()
    set_current_language(language)
    try:
        yield
    finally:
        set_current_language(previous_language) 