"""
Multilingual Services Package

This package provides services for language detection and processing in the
multilingual support system.
"""

from src.multilingual.services.language_detector import LanguageDetector
from src.multilingual.services.base_translation_service import BaseTranslationService
from src.multilingual.services.mock_translation_service import MockTranslationService
from src.multilingual.services.translation_manager import TranslationManager
from src.multilingual.services.template_manager import TemplateManager

__all__ = [
    'LanguageDetector',
    'BaseTranslationService',
    'MockTranslationService',
    'TranslationManager',
    'TemplateManager'
] 