"""
Advanced Formatting & Templating Demo Script

This script demonstrates citation formatting and template management
capabilities of the multilingual support system.
"""

import os
import sys
import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.multilingual.config import Language, get_current_language, set_current_language
from src.multilingual.services import TemplateManager
from src.multilingual.formatters import CitationFormatter, CitationStyle, format_date
from src.multilingual.utils import language_context


def print_separator(title: str = None) -> None:
    """Print a separator line with an optional title."""
    print("\n" + "=" * 60)
    if title:
        print(f" {title} ")
        print("=" * 60)


def test_citation_formatting() -> None:
    """Test the CitationFormatter with placeholder logic."""
    print_separator("Citation Formatting Test")
    
    formatter = CitationFormatter()
    source1 = {"author": "Doe, J.", "title": "Sample Paper One", "year": "2023"}
    source2 = {"author": "Smith, A. & Lee, B.", "title": "Another Study", "year": "2022"}
    
    print(f"Source 1: {source1}")
    
    for lang in [Language.ENGLISH, Language.RUSSIAN, Language.SPANISH]:
        with language_context(lang):
            print(f"\n--- Language: {lang.name} ---")
            for style in [CitationStyle.APA, CitationStyle.MLA, "custom_unknown_style"]:
                citation = formatter.format_citation(source1, style=style)
                print(f"  Style '{style}': {citation}")
    
    print_separator("Bibliography Test")
    bibliography_sources = [source1, source2, {"title": "Only Title Item"}]
    with language_context(Language.ENGLISH):
        print("\nEnglish APA Bibliography:")
        for entry in formatter.format_bibliography(bibliography_sources, style=CitationStyle.APA):
            print(f"  - {entry}")
            
    with language_context(Language.RUSSIAN):
        print("\nRussian MLA Bibliography:")
        for entry in formatter.format_bibliography(bibliography_sources, style=CitationStyle.MLA):
            print(f"  - {entry}")


def test_template_management() -> None:
    """Test the TemplateManager with basic templates."""
    print_separator("Template Management Test")
    
    manager = TemplateManager()
    report_data = {
        "report_title": "My Awesome Research Report",
        # Using a fixed date string for simplicity in this demo
        # In a real app, format_date would be used here based on context language
    }
    
    for lang in [Language.ENGLISH, Language.RUSSIAN, Language.SPANISH, Language.KAZAKH]:
        with language_context(lang):
            # Format date according to current context language
            report_data["report_date"] = format_date(datetime.datetime.now())
            
            print(f"\n--- Rendering Header for Language: {lang.name} ---")
            header_content = manager.render_template("report_header.txt", report_data)
            print(header_content)
            
            # Test fallback (assuming a non-existent template for Kazakh for this test)
            if lang == Language.KAZAKH:
                print(f"\n--- Testing Fallback: Requesting 'non_existent_template.txt' for {lang.name} ---")
                # Forcing default language to English for this specific fallback test for clarity
                original_default = manager.config.default_language
                manager.config.default_language = Language.ENGLISH
                
                non_existent_rendered = manager.render_template(
                    "non_existent_template.txt", 
                    {"message": "This should show fallback or error."}
                )
                print(non_existent_rendered) # Expected to be an error message or default template if one existed with that name
                
                # Create a dummy default template for the fallback test to actually succeed
                dummy_default_path = os.path.join(manager.template_base_path, Language.ENGLISH.value, "non_existent_template.txt")
                with open(dummy_default_path, "w", encoding="utf-8") as f:
                    f.write("This is the DEFAULT English template for non_existent_template.txt. Message: {message}")
                
                print(f"\n--- Retrying with dummy default: Requesting 'non_existent_template.txt' for {lang.name} ---")
                non_existent_rendered_fallback = manager.render_template(
                    "non_existent_template.txt", 
                    {"message": "Fallback successful!"}
                )
                print(non_existent_rendered_fallback)
                os.remove(dummy_default_path) # Clean up dummy file
                manager.config.default_language = original_default # Restore original default

if __name__ == "__main__":
    set_current_language(Language.ENGLISH) # Start with English context
    
    test_citation_formatting()
    test_template_management()
    
    print("\nAdvanced Formatting & Templating demo completed.") 