# Content Organization System Guide

This guide provides an overview of the Content Organization System in Deep Deep Research v2, explaining how to use it to structure research content, generate executive summaries, and create tables of contents.

## Overview

The Content Organization System is designed to transform unstructured or semi-structured research content into well-organized, easy-to-navigate documents. It provides the following key features:

- **Content Structure Analysis**: Automatically extracts structure from unstructured content
- **Executive Summary Generation**: Creates concise summaries of research content
- **Table of Contents Creation**: Generates structured tables of contents with proper formatting
- **Content Flow Optimization**: Refines content structure for better readability
- **Multi-format Support**: Outputs content in markdown, HTML, or plain text formats

## Basic Usage

### Organizing Research Results

The most common use case is to organize the results from the research synthesis pipeline:

```python
from src.research.content_organizer import ContentOrganizer
from src.research.synthesizer import SynthesisResult

# Initialize the content organizer
organizer = ContentOrganizer(
    max_summary_length=500,  # Maximum length for executive summaries
    toc_max_depth=3,         # Maximum heading depth for table of contents
    include_page_numbers=True  # Whether to include page numbers in TOC (for HTML/PDF)
)

# Organize a synthesis result
organized_content = organizer.organize_content(
    synthesis_result=synthesis_result,  # A SynthesisResult instance
    output_format='markdown'  # 'markdown', 'html', or 'text'
)

# Access the organized content
print(organized_content.title)
print(organized_content.executive_summary)
print(organized_content.table_of_contents)
print(organized_content.formatted_content)

# Save the formatted content to a file
with open('organized_research.md', 'w') as f:
    f.write(organized_content.formatted_content)
```

### Organizing Plain Text Content

You can also organize plain text content without going through the synthesis pipeline:

```python
# Organize plain text content
organized_content = organizer.organize_from_text(
    title="Research on Artificial Intelligence",
    content=my_text_content,  # A string containing the text content
    output_format='markdown'  # 'markdown', 'html', or 'text'
)

# The result is the same OrganizedContent object as before
```

## Components

The system consists of several components that can be used individually if needed:

### Content Structure

The `ContentStructure` class represents the structure of research content:

```python
from src.research.content_organizer import ContentStructure, Section, Subsection, HeadingLevel

# Create a content structure manually
structure = ContentStructure(
    title="Research Topic",
    executive_summary="Brief summary of the research."
)

# Add sections
section = Section(
    id="section-1",
    title="Introduction",
    content="Section content goes here.",
    level=HeadingLevel.HEADING_1
)
structure.add_section(section)

# Add subsections to a section
subsection = Subsection(
    id="section-1-1",
    title="Background",
    content="Subsection content goes here.",
    level=HeadingLevel.HEADING_2
)
section.add_subsection(subsection)

# Create a structure from plain text with markdown headings
structure = ContentStructure.from_plain_text(
    title="Research Topic",
    content="# Section 1\nContent\n## Subsection 1.1\nMore content"
)

# Convert to markdown
markdown_text = structure.to_markdown()
```

### Content Analyzer

The `ContentAnalyzer` class extracts structure from unstructured content:

```python
from src.research.content_organizer import ContentAnalyzer
from src.research.synthesizer import SynthesisResult

analyzer = ContentAnalyzer(
    min_section_length=200,    # Minimum length for a valid section
    min_topic_frequency=2      # Minimum frequency for a term to be a key topic
)

# Analyze a synthesis result
content_structure = analyzer.analyze_synthesis_result(synthesis_result)
```

### Executive Summarizer

The `ExecutiveSummarizer` class generates concise summaries:

```python
from src.research.content_organizer import ExecutiveSummarizer, ContentStructure

summarizer = ExecutiveSummarizer(
    max_length=500,       # Maximum summary length
    min_sentences=3,      # Minimum sentences to include
    max_sentences=7       # Maximum sentences to include
)

# Generate a summary from a content structure
summary = summarizer.generate_summary(content_structure)

# Generate a summary directly from a synthesis result
summary = summarizer.generate_summary_from_synthesis(synthesis_result)
```

### Table of Contents Generator

The `TableOfContentsGenerator` class creates tables of contents:

```python
from src.research.content_organizer import TableOfContentsGenerator, ContentStructure

toc_generator = TableOfContentsGenerator(
    include_page_numbers=True,  # Include page numbers (for PDF/HTML)
    max_depth=3                 # Maximum heading depth to include
)

# Generate a table of contents in different formats
markdown_toc = toc_generator.generate_toc(content_structure, format_type='markdown')
html_toc = toc_generator.generate_toc(content_structure, format_type='html')
text_toc = toc_generator.generate_toc(content_structure, format_type='text')

# Get structured TOC data for custom rendering
toc_data = toc_generator.generate_toc_data(content_structure)
```

## Advanced Features

### Content Structure Refinement

You can refine a content structure to improve its organization:

```python
# Refine a content structure
refined_structure = organizer.refine_structure(
    content_structure=structure,
    balance_sections=True,     # Balance section lengths
    reorder_sections=True      # Reorder sections for better flow
)
```

### Custom Formatting

For more control over formatting, you can use the internal formatting methods:

```python
# Format as HTML
html_content = organizer._format_html(content_structure)

# Format as plain text
text_content = organizer._format_text(content_structure)
```

## Integration with Other Systems

### Integration with PDF Generation

The Content Organization System integrates seamlessly with the PDF Generation System:

```python
from src.research.content_organizer import ContentOrganizer
from src.pdf_generation import ReportService

# Organize content
organizer = ContentOrganizer()
organized_content = organizer.organize_content(synthesis_result)

# Generate PDF report from organized content
report_service = ReportService()
pdf_path = report_service.generate_report(
    title=organized_content.title,
    content=organized_content.formatted_content,
    toc=organized_content.table_of_contents,
    executive_summary=organized_content.executive_summary
)
```

### Integration with Research Pipeline

To integrate with the complete research pipeline:

```python
from src.research.manager import ResearchManager
from src.research.content_organizer import ContentOrganizer

# Set up research manager
research_manager = ResearchManager()

# Run research query
synthesis_result = await research_manager.research("Research topic")

# Organize the research results
organizer = ContentOrganizer()
organized_content = organizer.organize_content(synthesis_result)

# The organized content is ready for presentation or export
```

## Examples

For complete working examples, see the `examples/content_organization_demo.py` script, which demonstrates:

1. Organizing mock synthesis results
2. Organizing real GPT-4 synthesis results
3. Organizing plain text content

## Best Practices

1. **Use appropriate output formats** for your target medium (markdown for most documentation, HTML for web, text for simpler displays)
2. **Customize summary length** based on the content size (longer for comprehensive research, shorter for brief reports)
3. **Set appropriate TOC depth** (2-3 levels is usually sufficient for readability)
4. **Review and refine** auto-generated summaries and structure for important documents
5. **Preserve original content** when needed, as the organization process does interpretation and restructuring

## Troubleshooting

**Issue**: Executive summary is too short or doesn't capture key points
- **Solution**: Increase the `max_summary_length` parameter when initializing the ContentOrganizer

**Issue**: Table of contents is too detailed or too shallow
- **Solution**: Adjust the `toc_max_depth` parameter to control detail level

**Issue**: Content structure doesn't correctly identify sections
- **Solution**: Format original content with clear markdown headings or use sections in the synthesis result 