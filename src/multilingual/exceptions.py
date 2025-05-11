"""
Multilingual Support Exceptions Module

This module defines exceptions and error handling utilities specific to the
multilingual support system.
"""

from typing import Optional

# from src.error_handling import log_error # Removed
from src.error_handling import error_manager, ResearchError, ErrorCategory, ErrorSeverity


class MultilingualError(ResearchError):
    """Base exception class for all multilingual support errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, \
                 category: ErrorCategory = ErrorCategory.MULTILINGUAL, \
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, \
                 component: str = "MultilingualSystem"):
        
        # Explicitly prepare args for ResearchError to avoid passing 'error_code'
        research_error_args = {
            "message": message,
            "error_category": category,
            "error_severity": severity,
            "component": component
        }
        super().__init__(**research_error_args) # Call ResearchError's __init__
        self.error_code = error_code # Store error_code on this instance
        # Removed direct log_error call, error_manager.handle_error will be called by the raiser
        # or ResearchError's own __init__ if we decide to log all ResearchErrors by default.
        # For now, let's assume the code that *catches* these exceptions will use error_manager.handle_error.
        # However, if the intention was to log every time an exception is CREATED, we could do:
        # error_manager.handle_error(self) # This might lead to double logging if also handled by caller.


class LanguageDetectionError(MultilingualError):
    """Exception raised when language detection fails."""
    
    def __init__(self, message: str, error_code: Optional[str] = "LanguageDetectionError", \
                 component: str = "LanguageDetector"):
        super().__init__(message, error_code=error_code, category=ErrorCategory.MULTILINGUAL, \
                         severity=ErrorSeverity.MEDIUM, component=component)


class UnsupportedLanguageError(MultilingualError):
    """Exception raised when an unsupported language is requested."""
    
    def __init__(self, language_code: str, error_code: Optional[str] = "UnsupportedLanguageError", \
                 component: str = "MultilingualSystem"):
        message = f"Unsupported language code: {language_code}"
        super().__init__(message, error_code=error_code, category=ErrorCategory.VALIDATION, \
                         severity=ErrorSeverity.LOW, component=component)


class TranslationError(MultilingualError):
    """Exception raised when a translation operation fails."""
    
    def __init__(self, message: str, source_lang: str, target_lang: str, \
                 error_code: Optional[str] = "TranslationError", component: str = "TranslationService"):
        full_message = f"Translation error from {source_lang} to {target_lang}: {message}"
        super().__init__(full_message, error_code=error_code, category=ErrorCategory.SERVICE_ERROR, \
                         severity=ErrorSeverity.HIGH, component=component)
        self.source_lang = source_lang
        self.target_lang = target_lang


class FormattingError(MultilingualError):
    """Exception raised when language-specific formatting fails."""
    
    def __init__(self, message: str, language_code: str, \
                 error_code: Optional[str] = "FormattingError", component: str = "Formatter"):
        full_message = f"Formatting error for language {language_code}: {message}"
        super().__init__(full_message, error_code=error_code, category=ErrorCategory.MULTILINGUAL, \
                         severity=ErrorSeverity.MEDIUM, component=component)
        self.language_code = language_code 