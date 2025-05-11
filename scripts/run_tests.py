#!/usr/bin/env python3
"""
Test Runner Script for Deep Deep Research v2

This script provides a convenient way to run tests with different options
and generate coverage reports.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import shutil


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Run tests for Deep Deep Research v2')
    
    parser.add_argument(
        '--module', '-m',
        help='Run tests for a specific module (e.g., "chunking" or "research.synthesizer")'
    )
    
    parser.add_argument(
        '--test', '-t',
        help='Run a specific test (e.g., "test_content_prioritization.py" or "test_content_prioritization.py::TestContentPrioritizer")'
    )
    
    parser.add_argument(
        '--coverage', '-c',
        action='store_true',
        help='Generate coverage report'
    )
    
    parser.add_argument(
        '--html',
        action='store_true',
        help='Generate HTML coverage report'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Run tests in verbose mode'
    )
    
    parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help='Run tests in parallel mode using pytest-xdist'
    )
    
    parser.add_argument(
        '--slow',
        action='store_true',
        help='Include tests marked as slow'
    )
    
    parser.add_argument(
        '--durations', '-d',
        type=int,
        default=0,
        help='Show N slowest tests (default: 0, no timing)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output directory for reports (default: reports)'
    )
    
    return parser.parse_args()


def run_tests(args):
    """Run the tests with the given options."""
    # Ensure the project root directory is in the Python path
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))
    
    # Build command
    cmd = ['pytest']
    
    # Add module/test specifier if provided
    if args.module:
        cmd.append(f'tests/{args.module}')
    elif args.test:
        cmd.append(f'tests/{args.test}')
    
    # Add options
    if args.verbose:
        cmd.append('-v')
    
    if args.parallel:
        if shutil.which('pytest-xdist'):
            cmd.append('-xvs')
        else:
            print("WARNING: pytest-xdist not found. Install with: pip install pytest-xdist")
    
    if args.durations > 0:
        cmd.append(f'--durations={args.durations}')
    
    # Skip slow tests by default unless explicitly included
    if not args.slow:
        cmd.append('-m')
        cmd.append('not slow')
    
    # Configure coverage
    output_dir = args.output or 'reports'
    output_path = project_root / output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Add coverage options if requested
    if args.coverage or args.html:
        coverage_cmd = [
            '--cov=src',
            '--cov-report=term'
        ]
        
        if args.html:
            html_path = output_path / 'coverage_html'
            coverage_cmd.append(f'--cov-report=html:{html_path}')
        
        # Add coverage XML for integration with tools like SonarQube
        xml_path = output_path / 'coverage.xml'
        coverage_cmd.append(f'--cov-report=xml:{xml_path}')
        
        cmd.extend(coverage_cmd)
    
    # Print command being run
    print(f"Running: {' '.join(cmd)}")
    
    # Run the tests
    result = subprocess.run(cmd)
    
    # Return the pytest exit code
    return result.returncode


def main():
    """Main entry point for the script."""
    args = parse_args()
    exit_code = run_tests(args)
    
    # Output paths to reports if generated
    if args.html:
        output_dir = args.output or 'reports'
        project_root = Path(__file__).resolve().parent.parent
        html_path = project_root / output_dir / 'coverage_html' / 'index.html'
        print(f"\nHTML coverage report generated at: {html_path}")
    
    # Exit with the pytest return code
    sys.exit(exit_code)


if __name__ == '__main__':
    main() 