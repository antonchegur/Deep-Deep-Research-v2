"""
Multilingual Support System Package

This package provides support for generating research reports in multiple languages
including English, Russian, Spanish, and Kazakh. It includes language detection,
translation services, and formatting utilities.
"""

from src.multilingual.config import (
    Language, 
    LanguageMetadata, 
    LANGUAGE_METADATA, 
    MultilingualConfig,
    DEFAULT_CONFIG,
    get_current_language,
    set_current_language,
    get_config,
    configure_base
)
from src.multilingual.services import TranslationManager
from typing import List, Optional

# Make key components available at package level for easy imports
__all__ = [
    'Language',
    'LanguageMetadata',
    'LANGUAGE_METADATA',
    'MultilingualConfig',
    'DEFAULT_CONFIG',
    'get_current_language',
    'set_current_language',
    'get_config',
    'configure_multilingual_system',
    'translate',
    'translate_batch'
]

# Module-level default translation manager instance
_translation_manager = TranslationManager(config=get_config())


def configure_multilingual_system(new_config: MultilingualConfig) -> None:
    """
    Update the global multilingual configuration and reinitialize services.
    
    Args:
        new_config: The new configuration to use
    """
    global _translation_manager
    configure_base(new_config)
    _translation_manager = TranslationManager(config=get_config())


def translate(text: str, target_language: Optional[Language] = None, source_language: Optional[Language] = None) -> str:
    """
    Global helper function to translate text.
    Uses the default TranslationManager instance.

    Args:
        text: The text to translate.
        target_language: The language to translate to. If None, uses current active language.
        source_language: The source language. If None, allows the manager to auto-detect or use default.

    Returns:
        The translated text.
    """
    return _translation_manager.translate(text, target_language or get_current_language(), source_language)


def translate_batch(texts: List[str], target_language: Optional[Language] = None, source_language: Optional[Language] = None) -> List[str]:
    """
    Global helper function to translate a batch of texts.
    Uses the default TranslationManager instance.

    Args:
        texts: A list of text strings to translate.
        target_language: The language to translate to. If None, uses current active language.
        source_language: The source language of the texts. If None, allows the manager to auto-detect or use default.

    Returns:
        A list of translated text strings.
    """
    return _translation_manager.translate_batch(texts, target_language or get_current_language(), source_language) 