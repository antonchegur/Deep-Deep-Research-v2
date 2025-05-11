"""
Formatting Demo Script

This script demonstrates the language-specific formatting capabilities of the
multilingual support system.
"""

import os
import sys
import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.multilingual.config import Language, get_current_language, set_current_language
from src.multilingual.formatters import format_date, format_number, format_list, format_quotes
from src.multilingual.utils import language_context


def print_separator(title: str = None) -> None:
    """Print a separator line with an optional title."""
    print("\n" + "=" * 60)
    if title:
        print(f" {title} ")
        print("=" * 60)


def test_date_formatting() -> None:
    """Test date formatting in different languages."""
    print_separator("Date Formatting Test")
    
    # Create a sample date
    date = datetime.datetime(2023, 8, 15, 14, 30, 45)
    
    for language in Language:
        with language_context(language):
            formatted_date = format_date(date)
            formatted_time = format_date(date, format_str="%H:%M:%S")
            
            print(f"\n{language.name} ({language.value}):")
            print(f"  Date: {formatted_date}")
            print(f"  Time: {formatted_time}")


def test_number_formatting() -> None:
    """Test number formatting in different languages."""
    print_separator("Number Formatting Test")
    
    # Sample numbers
    integer = 1234567
    decimal = 1234567.89
    
    for language in Language:
        with language_context(language):
            formatted_int = format_number(integer)
            formatted_decimal = format_number(decimal)
            formatted_precise = format_number(decimal, decimal_places=4)
            
            print(f"\n{language.name} ({language.value}):")
            print(f"  Integer: {formatted_int}")
            print(f"  Decimal: {formatted_decimal}")
            print(f"  With 4 decimal places: {formatted_precise}")


def test_list_formatting() -> None:
    """Test list formatting in different languages."""
    print_separator("List Formatting Test")
    
    # Sample lists
    fruits_1 = ["Apple"]
    fruits_2 = ["Apple", "Banana"]
    fruits_many = ["Apple", "Banana", "Orange", "Grape", "Mango"]
    
    for language in Language:
        with language_context(language):
            formatted_1 = format_list(fruits_1)
            formatted_2 = format_list(fruits_2)
            formatted_many = format_list(fruits_many)
            
            print(f"\n{language.name} ({language.value}):")
            print(f"  One item: {formatted_1}")
            print(f"  Two items: {formatted_2}")
            print(f"  Many items: {formatted_many}")


def test_quote_formatting() -> None:
    """Test quotation mark formatting in different languages."""
    print_separator("Quote Formatting Test")
    
    # Sample text
    text = "Hello, world!"
    
    for language in Language:
        with language_context(language):
            formatted = format_quotes(text)
            
            print(f"\n{language.name} ({language.value}):")
            print(f"  Quoted text: {formatted}")


if __name__ == "__main__":
    # Set default language
    set_current_language(Language.ENGLISH)
    
    # Run all tests
    test_date_formatting()
    test_number_formatting()
    test_list_formatting()
    test_quote_formatting()
    
    print("\nDemo completed.") 