"""
Language Detection Utility Module

This module provides utilities for detecting the language of text input.
It uses a combination of techniques including character frequency analysis,
common word detection, and optional integration with external detection services.
"""

import re
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple

from src.error_handling import error_manager
from src.multilingual.config import Language, LANGUAGE_METADATA
from src.multilingual.exceptions import LanguageDetectionError


# Common word collections for each supported language to help with detection
COMMON_WORDS = {
    Language.ENGLISH: {
        'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it',
        'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but'
    },
    Language.RUSSIAN: {
        'и', 'в', 'не', 'на', 'я', 'что', 'с', 'по', 'к', 'а', 'от', 'это',
        'как', 'то', 'так', 'его', 'но', 'у', 'за', 'мы', 'вы', 'для', 'все'
    },
    Language.SPANISH: {
        'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no', 'haber',
        'por', 'con', 'su', 'para', 'como', 'estar', 'tener', 'le', 'lo', 'todo'
    },
    Language.KAZAKH: {
        'және', 'бар', 'жоқ', 'бұл', 'мен', 'сен', 'ол', 'біз', 'сіз', 'олар', 
        'бол', 'кел', 'кет', 'істе', 'үшін', 'себебі', 'бірақ', 'да', 'не', 'қалай'
    }
}

# Character frequency patterns for languages
CHAR_PATTERNS = {
    Language.ENGLISH: re.compile(r'[a-zA-Z]'),
    Language.RUSSIAN: re.compile(r'[а-яА-ЯёЁ]'),
    Language.SPANISH: re.compile(r'[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ¿¡]'),
    Language.KAZAKH: re.compile(r'[а-яА-ЯәіңғүұқөӘІҢҒҮҰҚӨ]')
}

# Language-specific character sets that are distinctive
DISTINCTIVE_CHARS = {
    Language.RUSSIAN: set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя'),
    Language.SPANISH: set('áéíóúüñ¿¡'),
    Language.KAZAKH: set('әіңғүұқөӘІҢҒҮҰҚӨ'),
}


def detect_language(text: str) -> Language:
    """
    Detect the language of the provided text.
    
    Args:
        text: The text to analyze
        
    Returns:
        The detected Language enum value
    """
    if not text or len(text.strip()) == 0:
        return Language.get_default()
    
    try:
        # First check for distinctive characters
        distinctive_lang = _check_distinctive_chars(text.lower())
        if distinctive_lang:
            return distinctive_lang
        
        # Then analyze word frequency
        word_scores = _calculate_word_similarity(text)
        
        # Then character patterns
        char_scores = _calculate_char_pattern_match(text)
        
        # Combine scores
        final_scores = {}
        for lang in Language:
            final_scores[lang] = word_scores.get(lang, 0) * 0.7 + char_scores.get(lang, 0) * 0.3
        
        # Return the language with the highest score
        if not final_scores:
            return Language.get_default()
        
        return max(final_scores.items(), key=lambda x: x[1])[0]
    
    except Exception as e:
        detection_error = LanguageDetectionError(f"Language detection failed: {str(e)}")
        error_manager.handle_error(detection_error, component="detect_language_utility")
        return Language.get_default()


def _check_distinctive_chars(text: str) -> Optional[Language]:
    """Check for distinctive characters that strongly indicate a specific language."""
    # Count characters by language
    char_counts = {lang: 0 for lang in DISTINCTIVE_CHARS}
    
    for char_val in text:
        for lang, char_set in DISTINCTIVE_CHARS.items():
            if char_val in char_set:
                char_counts[lang] += 1
    
    # If we have a substantial number of distinctive chars for a language
    for lang, count in char_counts.items():
        if count > 5 or (len(text) > 0 and count / len(text) > 0.05):
            return lang
    
    return None


def _calculate_word_similarity(text: str) -> Dict[Language, float]:
    """Calculate similarity scores based on common words."""
    scores = {}
    
    # Normalize and split into words
    words = set(re.findall(r'\b\w+\b', text.lower()))
    if not words:
        return scores
    
    for lang, common_words in COMMON_WORDS.items():
        # Count matching words
        matches = words.intersection(common_words)
        if matches:
            # Calculate a score based on the proportion of matches
            scores[lang] = len(matches) / len(words)
    
    return scores


def _calculate_char_pattern_match(text: str) -> Dict[Language, float]:
    """Calculate scores based on character pattern matches."""
    scores = {}
    text_length = len(text)
    
    if text_length == 0:
        return scores
    
    for lang, pattern in CHAR_PATTERNS.items():
        matches = len(re.findall(pattern, text))
        if matches:
            scores[lang] = matches / text_length
    
    return scores 