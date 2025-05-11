"""
Base Translation Service Module

This module defines the abstract base class for translation services.
All specific translation service implementations (e.g., Google Translate, DeepL)
should inherit from this class and implement its abstract methods.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.multilingual.config import Language, MultilingualConfig, DEFAULT_CONFIG
from src.multilingual.exceptions import TranslationError


class BaseTranslationService(ABC):
    """Abstract base class for all translation services."""
    
    def __init__(self, config: Optional[MultilingualConfig] = None):
        """
        Initialize the translation service.
        
        Args:
            config: Optional multilingual configuration. If not provided,
                   the default configuration will be used.
        """
        self.config = config or DEFAULT_CONFIG
        self.name = "BaseTranslationService"
    
    @abstractmethod
    def translate(self, text: str, target_language: Language, source_language: Optional[Language] = None) -> str:
        """
        Translate a single string of text.
        
        Args:
            text: The text to translate
            target_language: The language to translate the text into
            source_language: Optional. The language of the source text. 
                              If None, the service may attempt to auto-detect.
                              
        Returns:
            The translated text
            
        Raises:
            TranslationError: If translation fails
        """
        pass
    
    @abstractmethod
    def translate_batch(self, texts: List[str], target_language: Language, source_language: Optional[Language] = None) -> List[str]:
        """
        Translate a batch of text strings.
        
        Args:
            texts: A list of text strings to translate
            target_language: The language to translate the texts into
            source_language: Optional. The language of the source texts.
                              If None, the service may attempt to auto-detect.
                              
        Returns:
            A list of translated text strings, corresponding to the input order
            
        Raises:
            TranslationError: If batch translation fails or partially fails
        """
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[Language]:
        """
        Get a list of languages supported by this translation service.
        
        Returns:
            A list of Language enum values that this service can translate to/from.
        """
        pass
    
    def is_language_pair_supported(self, source_lang: Language, target_lang: Language) -> bool:
        """
        Check if a specific source-target language pair is supported.
        
        Args:
            source_lang: The source language
            target_lang: The target language
            
        Returns:
            True if the pair is supported, False otherwise.
        """
        supported = self.get_supported_languages()
        return source_lang in supported and target_lang in supported
    
    def __repr__(self) -> str:
        return f"<{self.name}>" 