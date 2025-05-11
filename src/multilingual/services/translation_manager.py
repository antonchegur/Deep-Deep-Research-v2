"""
Translation Manager Service Module

This module provides a TranslationManager service that orchestrates translation
requests, selects appropriate translation providers, and manages caching.
"""

from typing import Dict, List, Optional, Type

from src.error_handling import error_manager, ResearchError, ErrorSeverity
from src.multilingual.config import Language, MultilingualConfig, DEFAULT_CONFIG
from src.multilingual.exceptions import TranslationError, UnsupportedLanguageError
from src.multilingual.services.base_translation_service import BaseTranslationService
from src.multilingual.services.mock_translation_service import MockTranslationService
from src.multilingual import get_current_language, set_current_language


class TranslationManager:
    """
    Manages translation operations, selects providers, and handles caching.
    """
    
    def __init__(self, config: Optional[MultilingualConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.translation_cache: Dict[Tuple[str, Language, Language], str] = {}
        self.current_service: Optional[BaseTranslationService] = None
        self._initialize_service()
        
    def _initialize_service(self):
        """Initialize the translation service based on configuration."""
        self.current_service = MockTranslationService(config=self.config)
        
        if not self.current_service:
            init_err = ResearchError("No translation service could be initialized. Using Mock.", \
                                     error_severity=ErrorSeverity.MEDIUM, component=self.__class__.__name__)
            error_manager.handle_error(init_err)
            self.current_service = MockTranslationService(config=self.config)

    def set_translation_service(self, service_class: Type[BaseTranslationService], **kwargs):
        """
        Manually set or change the translation service.
        
        Args:
            service_class: The class of the translation service to use.
            **kwargs: Arguments to pass to the service constructor (e.g., api_key).
        """
        try:
            self.current_service = service_class(config=self.config, **kwargs)
            change_info = ResearchError(f"Translation service changed to: {self.current_service.name}", \
                                        error_severity=ErrorSeverity.LOW, component=self.__class__.__name__)
            error_manager.handle_error(change_info)
            self.translation_cache.clear() # Clear cache when service changes
        except Exception as e:
            set_err = ResearchError(f"Failed to set translation service {service_class.__name__}: {e}", \
                                    error_severity=ErrorSeverity.HIGH, component=self.__class__.__name__)
            error_manager.handle_error(set_err)
            if not isinstance(self.current_service, MockTranslationService):
                self.current_service = MockTranslationService(config=self.config)
                fallback_warn = ResearchError("Fell back to MockTranslationService after failing to set new one.", \
                                              error_severity=ErrorSeverity.MEDIUM, component=self.__class__.__name__)
                error_manager.handle_error(fallback_warn)

    def translate(self, text: str, target_language: Optional[Language] = None, source_language: Optional[Language] = None) -> str:
        """
        Translate text using the configured service and cache.
        
        Args:
            text: The text to translate.
            target_language: The language to translate to. If None, uses current language.
            source_language: The source language. If None, attempts auto-detection.
            
        Returns:
            Translated text.
            
        Raises:
            TranslationError: If translation fails.
            UnsupportedLanguageError: If the language pair is not supported.
        """
        target_language = target_language or get_current_language()
        
        if not self.config.is_language_supported(target_language):
            raise UnsupportedLanguageError(target_language.value, component=self.__class__.__name__)
            
        # If source language is not provided, use default or auto-detect
        # For simplicity in this example, default to English if not specified
        # A real system might use language detection here.
        effective_source_language = source_language or self.config.default_language
        
        # Create cache key
        cache_key = (text, effective_source_language, target_language)
        
        if self.config.cache_translations and cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
            
        if not self.current_service:
            no_service_err = TranslationError("No translation service is configured.", 
                                              effective_source_language.value, target_language.value, 
                                              component=self.__class__.__name__)
            raise no_service_err

        if not self.current_service.is_language_pair_supported(effective_source_language, target_language):
            pair_err = TranslationError(
                f"Service {self.current_service.name} does not support {effective_source_language.name} to {target_language.name}",
                effective_source_language.value, target_language.value, component=self.__class__.__name__
            )
            raise pair_err
        
        try:
            translated_text = self.current_service.translate(text, target_language, effective_source_language)
            if self.config.cache_translations:
                self.translation_cache[cache_key] = translated_text
            return translated_text
        except TranslationError as e:
            raise
        except Exception as e:
            unexpected_err = TranslationError(f"Unexpected: {str(e)}", effective_source_language.value, target_language.value, \
                                              error_code="TranslationManagerUnexpectedError", component=self.__class__.__name__)
            error_manager.handle_error(unexpected_err)
            raise unexpected_err
            
    def translate_batch(self, texts: List[str], target_language: Optional[Language] = None, source_language: Optional[Language] = None) -> List[str]:
        """
        Translate a batch of texts.
        
        Args:
            texts: List of texts to translate.
            target_language: Target language. If None, uses current language.
            source_language: Source language. If None, attempts auto-detection.
            
        Returns:
            List of translated texts.
        """
        target_language = target_language or get_current_language()
        effective_source_language = source_language or self.config.default_language
        
        # Basic implementation: translate one by one. 
        # A more optimized version would use the service's batch method if available 
        # and handle caching for batches.
        # For now, leverage single translate for caching and individual error handling.
        results = []
        for text in texts:
            try:
                results.append(self.translate(text, target_language, effective_source_language))
            except TranslationError as e:
                batch_item_err = ResearchError(f"Batch translation item '{text[:30]}...' failed: {e.message}", \
                                               error_severity=ErrorSeverity.MEDIUM, component=self.__class__.__name__)
                error_manager.handle_error(batch_item_err)
                results.append(f"[Translation Failed for: {text[:30]}...] {e.source_lang}->{e.target_lang}")
        return results

    def clear_cache(self) -> None:
        """Clear the translation cache."""
        self.translation_cache.clear()
        cache_clear_info = ResearchError("Translation cache cleared.", \
                                         error_severity=ErrorSeverity.LOW, component=self.__class__.__name__)
        error_manager.handle_error(cache_clear_info) 