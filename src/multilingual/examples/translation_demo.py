"""
Translation Demo Script

This script demonstrates the translation capabilities of the multilingual
support system using the TranslationManager and MockTranslationService.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.multilingual.config import Language, MultilingualConfig, DEFAULT_CONFIG, get_current_language, set_current_language
from src.multilingual.services import TranslationManager, MockTranslationService
from src.multilingual.utils import language_context
from src.multilingual import translate, translate_batch, configure_multilingual_system
from src.multilingual.exceptions import TranslationError, UnsupportedLanguageError


def print_separator(title: str = None) -> None:
    """Print a separator line with an optional title."""
    print("\n" + "=" * 60)
    if title:
        print(f" {title} ")
        print("=" * 60)


def test_translation_manager() -> None:
    """Test the TranslationManager with the MockTranslationService."""
    print_separator("Translation Manager Test (Mock Service)")
    
    # Default configuration uses Mock service
    manager = TranslationManager()
    
    english_text = "Hello, this is a test message."
    
    print(f"Original English text: '{english_text}'")
    
    # Translate to Russian
    try:
        with language_context(Language.RUSSIAN):
            russian_translation = manager.translate(english_text, source_language=Language.ENGLISH)
            print(f"  Translated to Russian: '{russian_translation}'")
    except TranslationError as e:
        print(f"  Error translating to Russian: {e}")
        
    # Translate to Spanish using the global translate function
    try:
        spanish_translation = translate(english_text, Language.SPANISH, Language.ENGLISH)
        print(f"  Translated to Spanish (global fn): '{spanish_translation}'")
    except TranslationError as e:
        print(f"  Error translating to Spanish: {e}")

    # Translate to Kazakh, let manager use current language context
    set_current_language(Language.KAZAKH)
    try:
        kazakh_translation = translate(english_text, source_language=Language.ENGLISH)
        print(f"  Translated to Kazakh (context): '{kazakh_translation}'")
    except TranslationError as e:
        print(f"  Error translating to Kazakh: {e}")
    finally:
        set_current_language(Language.ENGLISH) # Reset context
        
    # Test batch translation
    print_separator("Batch Translation Test")
    batch_texts = [
        "First sentence for batch.",
        "Second piece of text.",
        "And a third one here."
    ]
    print(f"Original batch (English):")
    for t in batch_texts: print(f"  - {t}")
        
    try:
        translated_batch_russian = translate_batch(batch_texts, Language.RUSSIAN, Language.ENGLISH)
        print(f"\nBatch translated to Russian:")
        for t in translated_batch_russian: print(f"  - {t}")
            
        translated_batch_kazakh = translate_batch(batch_texts, Language.KAZAKH, Language.ENGLISH)
        print(f"\nBatch translated to Kazakh:")
        for t in translated_batch_kazakh: print(f"  - {t}")
            
    except TranslationError as e:
        print(f"  Error in batch translation: {e}")
        
    # Test changing translation service (hypothetically, if we had another)
    # class AnotherMockService(MockTranslationService):
    #     def translate(self, text: str, target_language: Language, source_language: Optional[Language] = None) -> str:
    #         return f"{text} [translated by AnotherMock to {target_language.value}]"
    # manager.set_translation_service(AnotherMockService)
    # print(f"\nAfter changing service:")
    # print(f"  Translate to Spanish: {manager.translate(english_text, Language.SPANISH, Language.ENGLISH)}")
    # manager.set_translation_service(MockTranslationService) # Change back
    
    # Test caching
    print_separator("Caching Test")
    print(f"Translating '{english_text[:20]}...' to Spanish again.")
    # First call (should use service)
    manager.translate(english_text, Language.SPANISH, Language.ENGLISH)
    # Second call (should use cache if enabled - MockService doesn't show this directly)
    # For a real service, you'd verify by checking API call counts or log messages.
    cached_spanish = manager.translate(english_text, Language.SPANISH, Language.ENGLISH)
    print(f"  Cached Spanish: '{cached_spanish}' (Note: MockService always 're-translates')")
    
    manager.clear_cache()
    print("  Cache cleared.")
    
    # Test unsupported language in config
    print_separator("Unsupported Language Test")
    custom_config = MultilingualConfig(supported_languages=[Language.ENGLISH, Language.RUSSIAN])
    configure_multilingual_system(custom_config)
    
    try:
        print(f"Attempting to translate to Spanish (not in supported_languages):")
        translate(english_text, Language.SPANISH, Language.ENGLISH)
    except UnsupportedLanguageError as e:
        print(f"  Caught expected error: {e}")
    finally:
        configure_multilingual_system(DEFAULT_CONFIG)

if __name__ == "__main__":
    test_translation_manager()
    print("\nTranslation demo completed.") 