#!/usr/bin/env python3
"""
Font Rendering and Embedding Test Script

This script tests font rendering and embedding across different PDF libraries.
It generates PDFs with various font settings and checks for proper embedding.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import platform

# Add the src directory to the path
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir.parent))

from src.pdf_generation.pdf_base import PDFReport, ReportConfig, ReportLibrary
from src.pdf_generation.elements import TextElement, PageBreakElement
from src.pdf_generation.formatters import TextStyle, TextAlignment

# Define a list of fonts to test - grouped by common availability
FONT_GROUPS = {
    "standard": [
        "Helvetica", "Times-Roman", "Courier",
        "Symbol", "ZapfDingbats"
    ],
    "windows": [
        "Arial", "Times New Roman", "Courier New", 
        "Verdana", "Georgia", "Tahoma", "Calibri"
    ],
    "macos": [
        "Helvetica Neue", "SF Pro", "Menlo", "Avenir",
        "Copperplate", "Didot", "Geneva"
    ],
    "universal": [
        "Open Sans", "Roboto", "Lato", "Montserrat",
        "Ubuntu", "Source Sans Pro", "Noto Sans"
    ],
    "decorative": [
        "Comic Sans MS", "Impact", "Brush Script MT",
        "Papyrus", "Chalkduster", "Broadway", "Copperplate"
    ]
}

# Sample text for testing
SAMPLE_TEXT = {
    "english": "The quick brown fox jumps over the lazy dog. 0123456789",
    "pangrams": {
        "english": "The quick brown fox jumps over the lazy dog.",
        "french": "Portez ce vieux whisky au juge blond qui fume.",
        "german": "Victor jagt zwölf Boxkämpfer quer über den großen Sylter Deich.",
        "spanish": "El veloz murciélago hindú comía feliz cardillo y kiwi.",
        "russian": "В чащах юга жил бы цитрус? Да, но фальшивый экземпляр!",
        "japanese": "いろはにほへと ちりぬるを わかよたれそ つねならむ うゐのおくやま けふこえて あさきゆめみし ゑひもせす",
        "arabic": "صِف خَلقَ خَودِ كَمِثلِ الشَمسِ إِذ بَزَغَت — يَحظى الضَجيعُ بِها نَجلاءَ مِعطارِ",
    },
    "special_chars": "©®™§¶†‡•—–«»""''€£¥$¢!@#$%^&*()_+[]{};:'\"\\|,.<>/?`~",
    "emoji": "😀 😎 👍 🚀 🌟 🌈 🔥 💯 🎉 🎊 🎁 🎯 🎲 🎬 🎼 🎵 🎶"
}


def create_font_test_report(
    library: ReportLibrary,
    output_dir: Path,
    font_groups=None,
    embed_fonts=True,
    platform_specific=False
) -> Path:
    """
    Create a PDF report that tests various fonts and character sets.
    
    Args:
        library: The PDF library to use
        output_dir: Directory to save the PDF
        font_groups: List of font group names to test, or None for all
        embed_fonts: Whether to embed fonts in the PDF
        platform_specific: Whether to include platform-specific fonts
        
    Returns:
        Path to the generated PDF
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"font_test_{library.name.lower()}_{'embed' if embed_fonts else 'noembed'}_{timestamp}.pdf"
    output_path = output_dir / filename
    
    # Set up report configuration
    config = ReportConfig(
        title="Font Rendering Test",
        author="Font Test Suite",
        subject=f"Testing font rendering with {library.name}",
        keywords=["test", "pdf", "fonts", library.name.lower()],
        library=library,
        page_size="letter",
        orientation="portrait"
    )
    
    # Set font embedding option
    if hasattr(config, "embed_fonts"):
        config.embed_fonts = embed_fonts
    
    # Create the report
    report = PDFReport(config)
    
    # Add title and introduction using built-in styles
    report.add_element(TextElement(
        text="Font Rendering and Embedding Test",
        x=72, y=72,
        width=450,
        style=TextStyle(
            font_family="Helvetica-Bold",
            font_size=18,
            alignment=TextAlignment.CENTER
        )
    ))
    
    report.add_element(TextElement(
        text=f"Generated with {library.name} | " + 
             f"Fonts {'Embedded' if embed_fonts else 'Not Embedded'} | " +
             f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        x=72, y=100,
        width=450,
        style=TextStyle(
            font_family="Helvetica",
            font_size=10,
            alignment=TextAlignment.LEFT
        )
    ))
    
    report.add_element(TextElement(
        text=f"Platform: {platform.system()} {platform.release()} | " +
             f"Python: {platform.python_version()}",
        x=72, y=120,
        width=450,
        style=TextStyle(
            font_family="Helvetica",
            font_size=10,
            alignment=TextAlignment.LEFT
        )
    ))
    
    # Select font groups to test
    if font_groups is None:
        if platform_specific:
            test_groups = list(FONT_GROUPS.keys())
        else:
            # If not testing platform-specific fonts, only use standard and universal
            test_groups = ["standard", "universal", "decorative"]
    else:
        test_groups = [g for g in font_groups if g in FONT_GROUPS]
    
    # Add note about platform-specific fonts
    report.add_element(TextElement(
        text="Note: Some fonts may not be available on all systems. The actual font used may be a fallback font.",
        x=72, y=140,
        width=450,
        style=TextStyle(
            font_family="Helvetica",
            font_size=10,
            alignment=TextAlignment.LEFT
        )
    ))
    
    # Current y position for adding elements
    y_pos = 180
    
    # Test each font group
    for group_idx, group_name in enumerate(test_groups):
        # Add page break if needed
        if group_idx > 0:
            report.add_element(PageBreakElement())
            y_pos = 72
        
        # Add group heading
        report.add_element(TextElement(
            text=f"Font Group: {group_name.capitalize()}",
            x=72, y=y_pos,
            width=450,
            style=TextStyle(
                font_family="Helvetica-Bold",
                font_size=14,
                alignment=TextAlignment.LEFT
            )
        ))
        y_pos += 30
        
        # Test each font in the group
        for font_name in FONT_GROUPS[group_name]:
            # Add font heading
            report.add_element(TextElement(
                text=f"Font: {font_name}",
                x=72, y=y_pos,
                width=450,
                style=TextStyle(
                    font_family="Helvetica-Bold",
                    font_size=12,
                    alignment=TextAlignment.LEFT
                )
            ))
            y_pos += 20
            
            # Create custom style for this font
            font_style = TextStyle(
                font_family=font_name,
                font_size=12,
                alignment=TextAlignment.LEFT
            )
            
            # Add basic Latin text
            report.add_element(TextElement(
                text=f"Latin: {SAMPLE_TEXT['english']}",
                x=72, y=y_pos,
                width=450,
                style=font_style
            ))
            y_pos += 20
            
            # Add special characters
            report.add_element(TextElement(
                text=f"Special: {SAMPLE_TEXT['special_chars']}",
                x=72, y=y_pos,
                width=450,
                style=font_style
            ))
            y_pos += 20
            
            # Add emoji (may not render in most fonts)
            report.add_element(TextElement(
                text=f"Emoji: {SAMPLE_TEXT['emoji']}",
                x=72, y=y_pos,
                width=450,
                style=font_style
            ))
            y_pos += 30
            
            # Check if we need a new page
            if y_pos > 700:
                report.add_element(PageBreakElement())
                y_pos = 72
    
    # Add page for multilingual text
    report.add_element(PageBreakElement())
    y_pos = 72
    
    report.add_element(TextElement(
        text="Multilingual Text Rendering",
        x=72, y=y_pos,
        width=450,
        style=TextStyle(
            font_family="Helvetica-Bold",
            font_size=14,
            alignment=TextAlignment.LEFT
        )
    ))
    y_pos += 30
    
    # Test each language with a standard font
    for lang, text in SAMPLE_TEXT['pangrams'].items():
        report.add_element(TextElement(
            text=f"{lang.capitalize()}: {text}",
            x=72, y=y_pos,
            width=450,
            style=TextStyle(
                font_family="Helvetica",
                font_size=10,
                alignment=TextAlignment.LEFT
            )
        ))
        y_pos += 25
        
        # Test with a few different fonts
        for font in ["Helvetica", "Times-Roman", "Arial"]:
            report.add_element(TextElement(
                text=f"  {font}: {text}",
                x=90, y=y_pos,
                width=432,
                style=TextStyle(
                    font_family=font,
                    font_size=10,
                    alignment=TextAlignment.LEFT
                )
            ))
            y_pos += 20
        
        y_pos += 10
        
        # Check if we need a new page
        if y_pos > 700:
            report.add_element(PageBreakElement())
            y_pos = 72
    
    # Generate the PDF
    report.generate(output_path)
    print(f"Font test PDF generated: {output_path}")
    
    return output_path


def main():
    """Run the font rendering test script."""
    parser = argparse.ArgumentParser(
        description="Test font rendering and embedding across PDF libraries."
    )
    
    parser.add_argument(
        "--library",
        type=str,
        choices=["reportlab", "fpdf", "both"],
        default="both",
        help="PDF library to use (default: both)"
    )
    
    parser.add_argument(
        "--embed",
        action="store_true",
        default=True,
        help="Embed fonts in the PDF (default: True)"
    )
    
    parser.add_argument(
        "--no-embed",
        action="store_true",
        help="Do not embed fonts in the PDF"
    )
    
    parser.add_argument(
        "--platform-specific",
        action="store_true",
        help="Include platform-specific fonts in the test"
    )
    
    parser.add_argument(
        "--font-groups",
        type=str,
        nargs="+",
        choices=list(FONT_GROUPS.keys()),
        help="Specific font groups to test"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/font_tests",
        help="Directory to save generated PDFs (default: outputs/font_tests)"
    )
    
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open generated PDFs with default viewer after creation"
    )
    
    args = parser.parse_args()
    
    # Handle --no-embed flag
    if args.no_embed:
        args.embed = False
    
    # Determine which libraries to use
    libraries = []
    if args.library == "reportlab" or args.library == "both":
        libraries.append(ReportLibrary.REPORTLAB)
    if args.library == "fpdf" or args.library == "both":
        libraries.append(ReportLibrary.FPDF)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_pdfs = []
    
    # Generate PDFs for each library
    for library in libraries:
        print(f"\nGenerating font test with {library.name}...")
        
        output_path = create_font_test_report(
            library=library,
            output_dir=output_dir,
            font_groups=args.font_groups,
            embed_fonts=args.embed,
            platform_specific=args.platform_specific
        )
        
        generated_pdfs.append(output_path)
    
    # Print summary
    print(f"\nGenerated {len(generated_pdfs)} PDF files in {output_dir}")
    
    # Open PDFs if requested
    if args.open and generated_pdfs:
        print("\nOpening PDFs with default viewer...")
        for pdf_path in generated_pdfs:
            try:
                if platform.system() == "Darwin":  # macOS
                    os.system(f"open '{pdf_path}'")
                elif platform.system() == "Windows":
                    os.system(f'start "" "{pdf_path}"')
                elif platform.system() == "Linux":
                    os.system(f"xdg-open '{pdf_path}'")
                print(f"Opened {pdf_path}")
            except Exception as e:
                print(f"Error opening {pdf_path}: {e}")
    

if __name__ == "__main__":
    main() 