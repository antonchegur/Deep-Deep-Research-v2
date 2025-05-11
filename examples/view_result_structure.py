#!/usr/bin/env python
"""
Display the structure of a research result JSON file.

This script loads a research result JSON file and displays its structure
without showing the full content of large text fields.
"""

import json
import sys
from pathlib import Path


def truncate_text(text, max_length=100):
    """Truncate text to the specified maximum length."""
    if isinstance(text, str) and len(text) > max_length:
        return text[:max_length] + "..."
    return text


def display_structure(data, prefix="", max_depth=3, current_depth=0):
    """
    Display the structure of a dictionary or list.
    
    Args:
        data: The data to display
        prefix: Prefix for indentation
        max_depth: Maximum depth to display
        current_depth: Current depth
    """
    if current_depth >= max_depth:
        print(f"{prefix}...")
        return
    
    if isinstance(data, dict):
        print(f"{prefix}{{")
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{prefix}  {key}:")
                display_structure(value, prefix + "  ", max_depth, current_depth + 1)
            else:
                print(f"{prefix}  {key}: {truncate_text(value)}")
        print(f"{prefix}}}")
    elif isinstance(data, list):
        print(f"{prefix}[")
        if len(data) > 0:
            # Display the first item as an example
            display_structure(data[0], prefix + "  ", max_depth, current_depth + 1)
            if len(data) > 1:
                print(f"{prefix}  ... ({len(data) - 1} more items)")
        print(f"{prefix}]")
    else:
        print(f"{prefix}{truncate_text(data)}")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        # Find the most recent research result file
        result_files = sorted(Path('.').glob('research_result_*.json'))
        if not result_files:
            print("No research result files found.")
            return
        file_path = result_files[-1]  # Get the most recent file
    else:
        file_path = sys.argv[1]
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        print(f"Structure of {file_path}:")
        display_structure(data)
        
        # Print some stats
        sources = data.get('search_results', []) + data.get('content_results', [])
        num_sources = len(sources)
        
        # Get synthesis type from metadata or synthesis
        synthesis_type = "unknown"
        if 'metadata' in data and 'synthesis_type' in data['metadata']:
            synthesis_type = data['metadata']['synthesis_type']
        elif 'synthesis' in data and 'synthesis_type' in data['synthesis']:
            synthesis_type = data['synthesis']['synthesis_type']
            
        query = data.get('query', 'unknown')
        
        print("\nSummary:")
        print(f"Query: {query}")
        print(f"Synthesis type: {synthesis_type}")
        print(f"Number of sources: {num_sources}")
        
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"Invalid JSON file: {file_path}")


if __name__ == "__main__":
    main() 