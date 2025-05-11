"""
Language Detection Demo Script

This script demonstrates the language detection capabilities of the
multilingual support system.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.multilingual.config import Language, LANGUAGE_METADATA, get_current_language, set_current_language
from src.multilingual.services import LanguageDetector
from src.multilingual.utils import language_context


def print_separator(title: str = None) -> None:
    """Print a separator line with an optional title."""
    print("\n" + "=" * 60)
    if title:
        print(f" {title} ")
        print("=" * 60)


def test_language_detection() -> None:
    """Test the language detection functionality."""
    print_separator("Language Detection Test")
    
    detector = LanguageDetector()
    
    test_texts = {
        "English": "The quick brown fox jumps over the lazy dog.",
        "Russian": "Съешь ещё этих мягких французских булок, да выпей чаю.",
        "Spanish": "El veloz murciélago hindú comía feliz cardillo y kiwi. La cigüeña tocaba el saxofón.",
        "Kazakh": "Әбіш Кекілбайұлы атындағы халықаралық қоры авторлық құқық қорғауға үлес қосты.",
        "Mixed": "Hello and Привет with some Español y Қазақша text mixed together."
    }
    
    for label, text in test_texts.items():
        detected = detector.detect(text)
        confidence = detector.detect_with_confidence(text)[1]
        print(f"\n{label} text:")
        print(f"  Sample: \"{text[:60]}{'...' if len(text) > 60 else ''}\"")
        print(f"  Detected: {detected.name} ({detected.value})")
        print(f"  Display name: {LANGUAGE_METADATA[detected].display_name}")
        print(f"  Native name: {LANGUAGE_METADATA[detected].native_name}")
        print(f"  Confidence: {confidence:.2f}")


def test_language_context() -> None:
    """Test the language context manager."""
    print_separator("Language Context Test")
    
    # Set the default language
    set_current_language(Language.ENGLISH)
    print(f"Current language: {get_current_language().name}")
    
    # Use the context manager to temporarily change the language
    with language_context(Language.RUSSIAN):
        print(f"Inside Russian context: {get_current_language().name}")
        
        # Nested context
        with language_context(Language.SPANISH):
            print(f"Inside nested Spanish context: {get_current_language().name}")
        
        print(f"Back to Russian context: {get_current_language().name}")
    
    print(f"Restored to original language: {get_current_language().name}")


if __name__ == "__main__":
    test_language_detection()
    test_language_context()
    print("\nDemo completed.") 