"""
Multilingual Support Configuration Module

This module defines the supported languages, their ISO codes, and configuration
settings for the multilingual support system.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


class Language(Enum):
    """Enum representing supported languages in the system."""
    ENGLISH = "en"
    RUSSIAN = "ru"
    SPANISH = "es"
    KAZAKH = "kk"

    @classmethod
    def get_default(cls) -> "Language":
        """Returns the default language (English)."""
        return cls.ENGLISH
    
    @classmethod
    def from_code(cls, code: str) -> "Language":
        """Get a Language enum value from a language code."""
        for lang in cls:
            if lang.value == code:
                return lang
        raise ValueError(f"Unsupported language code: {code}")
    
    @property
    def display_name(self) -> str:
        """Returns the display name of the language."""
        return LANGUAGE_METADATA[self].display_name


@dataclass
class LanguageMetadata:
    """Metadata for a supported language."""
    display_name: str
    native_name: str
    right_to_left: bool = False
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M:%S"
    datetime_format: str = "%Y-%m-%d %H:%M:%S"
    thousand_separator: str = ","
    decimal_separator: str = "."
    quotation_start: str = '"'
    quotation_end: str = '"'


# Metadata for all supported languages
LANGUAGE_METADATA: Dict[Language, LanguageMetadata] = {
    Language.ENGLISH: LanguageMetadata(
        display_name="English",
        native_name="English",
        date_format="%m/%d/%Y",
        datetime_format="%m/%d/%Y %I:%M %p"
    ),
    Language.RUSSIAN: LanguageMetadata(
        display_name="Russian",
        native_name="Русский",
        date_format="%d.%m.%Y",
        datetime_format="%d.%m.%Y %H:%M"
    ),
    Language.SPANISH: LanguageMetadata(
        display_name="Spanish",
        native_name="Español",
        date_format="%d/%m/%Y",
        datetime_format="%d/%m/%Y %H:%M"
    ),
    Language.KAZAKH: LanguageMetadata(
        display_name="Kazakh",
        native_name="Қазақша",
        date_format="%d.%m.%Y",
        datetime_format="%d.%m.%Y %H:%M"
    )
}


@dataclass
class MultilingualConfig:
    """Configuration for the multilingual support system."""
    default_language: Language = Language.ENGLISH
    fallback_language: Language = Language.ENGLISH
    supported_languages: List[Language] = None
    auto_detect: bool = True
    translate_on_demand: bool = True
    cache_translations: bool = True
    
    def __post_init__(self):
        if self.supported_languages is None:
            self.supported_languages = list(Language)
    
    def is_language_supported(self, language: Language) -> bool:
        """Check if a language is in the list of supported languages."""
        return language in self.supported_languages


# Default configuration instance
DEFAULT_CONFIG = MultilingualConfig()

# --- Added for state management ---
_current_language: Language = Language.ENGLISH
_config: MultilingualConfig = DEFAULT_CONFIG

def get_current_language() -> Language:
    """Get the currently active language."""
    return _current_language

def set_current_language(language: Language) -> None:
    """
    Set the current active language.
    
    Args:
        language: The Language enum value to set as current
    
    Raises:
        ValueError: If the language is not in the supported languages list
    """
    global _current_language
    if not _config.is_language_supported(language):
        raise ValueError(f"Language {language.name} is not supported in the current configuration of supported_languages: {[l.name for l in _config.supported_languages]}")
    _current_language = language

def get_config() -> MultilingualConfig:
    """Get the current multilingual configuration."""
    return _config

def configure_base(new_config: MultilingualConfig) -> None:
    """
    Update the base multilingual configuration (_config and _current_language).
    This is intended to be called by the main configure function in __init__.py.
    Args:
        new_config: The new configuration to use
    """
    global _config, _current_language
    _config = new_config
    # Ensure the current language is supported in the new config
    if not _config.is_language_supported(_current_language):
        # Log this change or warning if necessary, then set to default
        # print(f"Warning: Current language {_current_language.name} not in new config. Setting to default.")
        set_current_language(_config.default_language) # Uses the new _config
# --- End of added state management --- 