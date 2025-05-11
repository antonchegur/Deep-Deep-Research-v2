"""
Language Detector Service

This service provides a high-level interface for language detection in the
multilingual support system.
"""

from typing import Dict, Optional, Tuple

from src.error_handling import error_manager
from src.multilingual.config import Language, MultilingualConfig, DEFAULT_CONFIG
from src.multilingual.utils.language_detection import detect_language
from src.multilingual.exceptions import LanguageDetectionError


class LanguageDetector:
    """
    Service for detecting the language of text input.
    
    This class provides a simple interface for language detection with additional
    features like confidence scoring and automatic fallback to the default language
    when detection fails or has low confidence.
    """
    
    def __init__(self, config: Optional[MultilingualConfig] = None):
        """
        Initialize the language detector.
        
        Args:
            config: Optional multilingual configuration. If not provided,
                   the default configuration will be used.
        """
        self.config = config or DEFAULT_CONFIG
        self._detection_cache = {}  # Cache detection results for performance
    
    def detect(self, text: str) -> Language:
        """
        Detect the language of the provided text.
        
        Args:
            text: The text to analyze
            
        Returns:
            The detected Language enum value
        """
        if not text or len(text.strip()) == 0:
            return self.config.default_language
            
        # Check cache first for exact matches
        if text in self._detection_cache:
            return self._detection_cache[text]
        
        try:
            # Use the detection utility
            detected_language = detect_language(text)
            
            # Only store in cache if text is not too long
            if len(text) < 1000:
                self._detection_cache[text] = detected_language
                
            return detected_language
        
        except Exception as e:
            detection_error = LanguageDetectionError(f"LanguageDetector.detect failed: {str(e)}")
            error_manager.handle_error(detection_error, component=self.__class__.__name__)
            return self.config.default_language
    
    def detect_with_confidence(self, text: str) -> Tuple[Language, float]:
        """
        Detect the language of the text with a confidence score.
        
        Args:
            text: The text to analyze
            
        Returns:
            A tuple containing the detected language and a confidence score (0-1)
        """
        if not text or len(text.strip()) == 0:
            return self.config.default_language, 0.0
        
        try:
            # This is a simplified implementation; in a real system,
            # we would calculate actual confidence scores
            language = self.detect(text)
            
            # Confidence is higher with more text to analyze
            confidence = min(0.5 + (len(text) / 500) * 0.5, 1.0)
            
            return language, confidence
        
        except Exception as e:
            detection_error = LanguageDetectionError(f"LanguageDetector.detect_with_confidence failed: {str(e)}")
            error_manager.handle_error(detection_error, component=self.__class__.__name__)
            return self.config.default_language, 0.0
    
    def clear_cache(self) -> None:
        """Clear the detection cache."""
        self._detection_cache.clear() 