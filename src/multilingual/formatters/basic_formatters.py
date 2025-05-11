"""
Basic Language-Specific Formatters

This module provides formatters for basic data types like dates, numbers, and strings
according to the language-specific conventions.
"""

import datetime
import locale
import re
from typing import Any, Dict, Optional, Union

from src.multilingual.config import Language, LANGUAGE_METADATA
from src.multilingual.exceptions import FormattingError
from src.multilingual import get_current_language


# Mapping between Language enum and locale strings
LOCALE_MAPPING = {
    Language.ENGLISH: "en_US.UTF-8",
    Language.RUSSIAN: "ru_RU.UTF-8",
    Language.SPANISH: "es_ES.UTF-8",
    Language.KAZAKH: "kk_KZ.UTF-8"
}

# Store original locale to restore later
# _original_locale = locale.getlocale(locale.LC_ALL) # Can be problematic
_original_time_locale_tuple = locale.getlocale(locale.LC_TIME)
_original_numeric_locale_tuple = locale.getlocale(locale.LC_NUMERIC)


def format_date(date_obj: Union[datetime.date, datetime.datetime], 
                language: Optional[Language] = None,
                format_str: Optional[str] = None) -> str:
    """
    Format a date according to the specified language's conventions.
    
    Args:
        date_obj: Date or datetime object to format
        language: Language to use for formatting. If None, uses the current language.
        format_str: Optional custom format string. If None, uses the language's default.
    
    Returns:
        Formatted date string
    
    Raises:
        FormattingError: If formatting fails
    """
    language = language or get_current_language()
    metadata = LANGUAGE_METADATA[language]
    
    if format_str is None:
        if isinstance(date_obj, datetime.datetime):
            format_str = metadata.datetime_format
        else:
            format_str = metadata.date_format
    
    current_time_locale_set = False
    try:
        locale_str = LOCALE_MAPPING.get(language)
        if locale_str:
            try:
                locale.setlocale(locale.LC_TIME, locale_str)
                current_time_locale_set = True
            except locale.Error:
                # Log this warning with error_manager if desired
                # print(f"Warning: Locale {locale_str} for LC_TIME not available. Using default strftime behavior.")
                pass # Proceed with default Python strftime behavior
        
        formatted = date_obj.strftime(format_str)
        return formatted
    
    except Exception as e:
        raise FormattingError(f"Date formatting failed: {str(e)}", language.value, component="format_date")
    finally:
        if current_time_locale_set:
            try:
                locale.setlocale(locale.LC_TIME, _original_time_locale_tuple) # Restore original
            except locale.Error:
                # This might happen if _original_time_locale_tuple was (None, None)
                # print(f"Warning: Could not restore original LC_TIME locale: {_original_time_locale_tuple}")
                pass # Best effort


def format_number(number: Union[int, float], 
                  language: Optional[Language] = None,
                  decimal_places: Optional[int] = None) -> str:
    """
    Format a number according to the specified language's conventions.
    
    Args:
        number: Number to format
        language: Language to use for formatting. If None, uses the current language.
        decimal_places: Number of decimal places to include. If None, uses default behavior.
    
    Returns:
        Formatted number string
    
    Raises:
        FormattingError: If formatting fails
    """
    language = language or get_current_language()
    metadata = LANGUAGE_METADATA[language]
    current_numeric_locale_set = False
    
    try:
        formatted_num_str = ""
        locale_str = LOCALE_MAPPING.get(language)
        use_locale_formatting = False
        if locale_str:
            try:
                locale.setlocale(locale.LC_NUMERIC, locale_str)
                current_numeric_locale_set = True
                use_locale_formatting = True
            except locale.Error:
                # print(f"Warning: Locale {locale_str} for LC_NUMERIC not available. Using manual formatting.")
                pass
        
        if use_locale_formatting:
            if isinstance(number, int):
                formatted_num_str = locale.format_string("%d", number, grouping=True)
            else:
                if decimal_places is not None:
                    formatted_num_str = locale.format_string(f"%.{decimal_places}f", number, grouping=True)
                else:
                    # Default to 2 decimal places for floats if not specified
                    formatted_num_str = locale.format_string("%.2f", number, grouping=True) 
        else:
            # Manual formatting if locale is not available/set
            if isinstance(number, int):
                num_format_str = "{:,}" # Basic thousands separator for int
                formatted_num_str = num_format_str.format(number)
            else:
                if decimal_places is not None:
                    num_format_str = "{:,.{dp}f}".format(dp=decimal_places)
                else:
                    num_format_str = "{:,.2f}" # Default to 2 decimal places
                formatted_num_str = num_format_str.format(number)
            
            # Apply language-specific separators manually if they differ from Python's default (usually English-like)
            # Python's default: thousands=,, decimal=.
            if metadata.decimal_separator != '.':
                formatted_num_str = formatted_num_str.replace('.', metadata.decimal_separator, 1) # Replace only the decimal
            if metadata.thousand_separator != ',':
                # This is tricky as the above format might have already put ','
                # If default was ',' and target is something else, replace. 
                # If target is '', remove. If default wasn't ',' this becomes more complex.
                # Assuming base format uses ',' for thousands for simplicity here.
                formatted_num_str = formatted_num_str.replace(',', metadata.thousand_separator)

        return formatted_num_str
    
    except Exception as e:
        raise FormattingError(f"Number formatting failed: {str(e)}", language.value, component="format_number")
    finally:
        if current_numeric_locale_set:
            try:
                locale.setlocale(locale.LC_NUMERIC, _original_numeric_locale_tuple)
            except locale.Error:
                # print(f"Warning: Could not restore original LC_NUMERIC locale: {_original_numeric_locale_tuple}")
                pass # Best effort


def format_list(items: list, 
                language: Optional[Language] = None,
                conjunction: Optional[str] = None) -> str:
    """
    Format a list into a string according to the language conventions.
    
    Args:
        items: List of items to format
        language: Language to use for formatting. If None, uses current language.
        conjunction: Optional custom conjunction. If None, uses language default.
    
    Returns:
        Formatted list string
    
    Raises:
        FormattingError: If formatting fails
    """
    language = language or get_current_language()
    
    if not items:
        return ""
    
    if len(items) == 1:
        return str(items[0])
    
    try:
        # Default conjunctions by language
        default_conjunctions = {
            Language.ENGLISH: "and",
            Language.RUSSIAN: "и",
            Language.SPANISH: "y",
            Language.KAZAKH: "және"
        }
        
        conj = conjunction or default_conjunctions.get(language, "and")
        
        if len(items) == 2:
            return f"{items[0]} {conj} {items[1]}"
        
        # For English-like languages
        if language in [Language.ENGLISH, Language.SPANISH]:
            return ", ".join(str(item) for item in items[:-1]) + f", {conj} {items[-1]}"
        
        # For other languages (simplified)
        return ", ".join(str(item) for item in items[:-1]) + f" {conj} {items[-1]}"
    
    except Exception as e:
        raise FormattingError(f"List formatting failed: {str(e)}", language.value)


def format_quotes(text: str, language: Optional[Language] = None) -> str:
    """
    Format a text with language-specific quotation marks.
    
    Args:
        text: Text to format with quotes
        language: Language to use for formatting. If None, uses current language.
    
    Returns:
        Text with appropriate quotation marks
    """
    language = language or get_current_language()
    metadata = LANGUAGE_METADATA[language]
    
    return f"{metadata.quotation_start}{text}{metadata.quotation_end}" 