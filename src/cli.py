#!/usr/bin/env python3
"""
Command-line interface for Deep Deep Research v2
"""

import argparse
import sys
import os
from dotenv import load_dotenv


def main():
    """Main entry point for the CLI"""
    # Load environment variables from .env file if it exists
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Deep Deep Research v2 - Comprehensive Research System"
    )
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Research command
    research_parser = subparsers.add_parser("research", help="Conduct research on a topic")
    research_parser.add_argument("topic", help="Research topic")
    research_parser.add_argument(
        "--depth", 
        choices=["quick", "standard", "deep"], 
        default=os.getenv("RESEARCH_MODE", "standard"),
        help="Research depth (quick: ~20 sources, standard: ~50 sources, deep: 100+ sources)"
    )
    research_parser.add_argument(
        "--language", 
        choices=["en", "ru", "es", "kk"], 
        default=os.getenv("DEFAULT_LANGUAGE", "en"),
        help="Output language"
    )
    research_parser.add_argument(
        "--output", "-o", 
        help="Output file path (default: ./research_report.pdf)"
    )
    
    # Sources command
    sources_parser = subparsers.add_parser("sources", help="Manage research sources")
    sources_parser.add_argument(
        "--list", action="store_true",
        help="List available sources"
    )
    sources_parser.add_argument(
        "--enable",
        help="Enable a specific source"
    )
    sources_parser.add_argument(
        "--disable",
        help="Disable a specific source"
    )
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Configure the application")
    setup_parser.add_argument(
        "--check", action="store_true",
        help="Check if all dependencies and API keys are configured correctly"
    )
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == "research":
        print(f"Starting research on topic: {args.topic}")
        print(f"Depth: {args.depth}")
        print(f"Language: {args.language}")
        print(f"Output: {args.output or './research_report.pdf'}")
        # TODO: Implement actual research functionality
        print("Research functionality not yet implemented")
        
    elif args.command == "sources":
        if args.list:
            print("Available sources:")
            print("- Wikipedia (enabled)")
            print("- DuckDuckGo (enabled)")
            print("- arXiv (enabled)")
            print("- OpenAI Web Search (disabled)")
            # TODO: Implement actual source listing
        elif args.enable:
            print(f"Enabling source: {args.enable}")
            # TODO: Implement source enabling
        elif args.disable:
            print(f"Disabling source: {args.disable}")
            # TODO: Implement source disabling
        else:
            sources_parser.print_help()
            
    elif args.command == "setup":
        if args.check:
            print("Checking configuration...")
            # TODO: Implement configuration checking
            print("API keys and dependencies check not yet implemented")
        else:
            setup_parser.print_help()
            
    elif args.command == "version":
        from . import __version__
        print(f"Deep Deep Research v2 version {__version__}")
        
    return 0


if __name__ == "__main__":
    sys.exit(main()) 