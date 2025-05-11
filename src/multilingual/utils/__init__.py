"""
Multilingual Utilities Package

This package provides utility functions for language detection and other
multilingual support operations.
"""

from src.multilingual.utils.language_detection import detect_language
from src.multilingual.utils.context import language_context

__all__ = ['detect_language', 'language_context'] 