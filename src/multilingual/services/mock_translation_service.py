"""
Mock Translation Service Module

This module provides a mock implementation of the BaseTranslationService.
It is used for testing and development purposes when actual translation APIs
are not available or not needed.
"""

from typing import List, Optional
import time

from src.multilingual.config import Language, MultilingualConfig
from src.multilingual.exceptions import TranslationError
from src.multilingual.services.base_translation_service import BaseTranslationService


class MockTranslationService(BaseTranslationService):
    """
    Mock implementation of a translation service.
    
    Simulates translation by appending the target language code to the text.
    It also simulates a short delay to mimic network latency.
    """
    
    def __init__(self, config: Optional[MultilingualConfig] = None, delay: float = 0.1):
        super().__init__(config)
        self.name = "MockTranslationService"
        self.delay = delay  # Simulate network delay
        # This mock service supports all languages defined in the Language enum
        self._supported_languages = list(Language)

    def translate(self, text: str, target_language: Language, source_language: Optional[Language] = None) -> str:
        """Simulates translating a single string of text."""
        if not self.is_language_pair_supported(source_language or Language.ENGLISH, target_language):
            raise TranslationError(
                f"Language pair {source_language.value if source_language else 'auto'} -> {target_language.value} not supported.",
                source_lang=source_language.value if source_language else "auto",
                target_lang=target_language.value
            )
        
        time.sleep(self.delay)  # Simulate API call delay
        
        source_lang_code = source_language.value if source_language else "auto"
        return f"{text} [translated from {source_lang_code} to {target_language.value} by MockService]"

    def translate_batch(self, texts: List[str], target_language: Language, source_language: Optional[Language] = None) -> List[str]:
        """Simulates translating a batch of text strings."""
        if not self.is_language_pair_supported(source_language or Language.ENGLISH, target_language):
            raise TranslationError(
                f"Batch translation for language pair {source_language.value if source_language else 'auto'} -> {target_language.value} not supported.",
                source_lang=source_language.value if source_language else "auto",
                target_lang=target_language.value
            )
            
        translated_texts = []
        for text in texts:
            time.sleep(self.delay)  # Simulate API call delay for each item
            source_lang_code = source_language.value if source_language else "auto"
            translated_texts.append(f"{text} [translated from {source_lang_code} to {target_language.value} by MockService]")
        return translated_texts

    def get_supported_languages(self) -> List[Language]:
        """Returns all languages defined in the Language enum as supported."""
        return self._supported_languages 