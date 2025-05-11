"""
Test Helper Functions and Utilities

This module provides helper functions, classes and utilities to standardize
testing patterns and reduce code duplication across test modules.
"""

import os
import json
import shutil
import inspect
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic
from unittest.mock import MagicMock, AsyncMock

import pytest


# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')


def compare_json_data(actual: Dict[str, Any], expected: Dict[str, Any], 
                      ignore_keys: List[str] = None) -> List[str]:
    """
    Compare two JSON objects and return a list of differences.
    
    Args:
        actual: The actual JSON data
        expected: The expected JSON data
        ignore_keys: Optional list of keys to ignore during comparison
        
    Returns:
        List of differences found (empty list if no differences)
    """
    ignore_keys = ignore_keys or []
    differences = []
    
    # Check for missing keys in actual
    for key in expected:
        if key in ignore_keys:
            continue
            
        if key not in actual:
            differences.append(f"Missing key '{key}' in actual data")
            continue
            
        # Handle nested dictionaries
        if isinstance(expected[key], dict) and isinstance(actual[key], dict):
            nested_diff = compare_json_data(actual[key], expected[key], ignore_keys)
            differences.extend([f"{key}.{diff}" for diff in nested_diff])
        # Handle lists (simple comparison)
        elif isinstance(expected[key], list) and isinstance(actual[key], list):
            if len(expected[key]) != len(actual[key]):
                differences.append(
                    f"List length mismatch for '{key}': expected {len(expected[key])}, "
                    f"got {len(actual[key])}"
                )
        # Handle scalar values
        elif actual[key] != expected[key]:
            differences.append(
                f"Value mismatch for '{key}': expected '{expected[key]}', "
                f"got '{actual[key]}'"
            )
    
    # Check for extra keys in actual
    for key in actual:
        if key in ignore_keys:
            continue
        if key not in expected:
            differences.append(f"Extra key '{key}' in actual data")
    
    return differences


def save_test_output(output: Any, filename: str, output_dir: str = "test_outputs",
                    overwrite: bool = True) -> Path:
    """
    Save test output to a file for analysis/debugging.
    
    Args:
        output: The data to save (string, dict, or other serializable object)
        filename: The filename to save to
        output_dir: Directory to save outputs in (relative to tests directory)
        overwrite: Whether to overwrite existing files
        
    Returns:
        Path to the saved output file
    """
    # Determine the tests directory
    tests_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    output_path = tests_dir / output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    
    file_path = output_path / filename
    
    # Check if file exists and handle accordingly
    if file_path.exists() and not overwrite:
        base, ext = os.path.splitext(filename)
        file_path = output_path / f"{base}_{os.urandom(4).hex()}{ext}"
    
    # Save the data based on type
    if isinstance(output, (dict, list)):
        with open(file_path, 'w') as f:
            json.dump(output, f, indent=2)
    elif isinstance(output, str):
        with open(file_path, 'w') as f:
            f.write(output)
    else:
        # Try to convert to string
        with open(file_path, 'w') as f:
            f.write(str(output))
    
    return file_path


def async_test(f: Callable) -> Callable:
    """
    Decorator to run async test functions.
    
    Example:
        @async_test
        async def test_async_function():
            result = await some_async_function()
            assert result == expected
    """
    def wrapper(*args, **kwargs):
        coro = asyncio.coroutine(f)
        future = coro(*args, **kwargs)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(future)
    
    return wrapper


class MockResponse:
    """
    Mock HTTP response for testing API clients.
    
    Attributes:
        status_code: HTTP status code
        json_data: Data to return from json() method
        text: Text to return from text property
        content: Bytes to return from content property
        headers: HTTP headers dict
        ok: Whether the request was successful
        raise_for_status: Function to raise an exception for error status
    """
    
    def __init__(self, 
                 status_code: int = 200, 
                 json_data: Optional[Dict[str, Any]] = None,
                 text: str = "",
                 content: bytes = b"",
                 headers: Optional[Dict[str, str]] = None):
        """Initialize the mock response with the given attributes."""
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text
        self.content = content
        self.headers = headers or {}
        self.ok = 200 <= status_code < 300
        self.raise_for_status = MagicMock()
        
        if not self.ok:
            self.raise_for_status.side_effect = Exception(f"HTTP Error: {status_code}")
    
    async def json(self) -> Dict[str, Any]:
        """Return the JSON data."""
        return self._json_data
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class ParameterizedTestCase(Generic[T, R]):
    """
    Helper class for creating parameterized test cases.
    
    Simplifies creating tests with multiple input/output combinations.
    
    Example:
        test_cases = ParameterizedTestCase[str, int]([
            ("test", 4, "length of 'test'"),
            ("hello", 5, "length of 'hello'")
        ])
        
        @pytest.mark.parametrize("input_val,expected,description", test_cases.cases())
        def test_string_length(input_val, expected, description):
            assert len(input_val) == expected
    """
    
    def __init__(self, test_tuples: List[tuple]):
        """
        Initialize with a list of test case tuples.
        
        Each tuple should contain: (input, expected_output, description)
        """
        self.test_tuples = test_tuples
    
    def cases(self) -> List[tuple]:
        """Return the test cases in a format suitable for pytest.mark.parametrize."""
        return self.test_tuples
    
    def inputs(self) -> List[T]:
        """Return just the input values from all test cases."""
        return [t[0] for t in self.test_tuples]
    
    def expected_outputs(self) -> List[R]:
        """Return just the expected output values from all test cases."""
        return [t[1] for t in self.test_tuples]
    
    def descriptions(self) -> List[str]:
        """Return just the descriptions from all test cases."""
        return [t[2] if len(t) > 2 else "" for t in self.test_tuples]


def assert_files_equal(file1: Union[str, Path], file2: Union[str, Path], 
                      ignore_bytes_at_offset: Optional[Dict[int, int]] = None) -> bool:
    """
    Assert that two files are identical, with optional byte comparison exceptions.
    
    Args:
        file1: Path to first file
        file2: Path to second file
        ignore_bytes_at_offset: Dict of {offset: num_bytes} to ignore during comparison
        
    Returns:
        True if files are equal (within specified parameters)
        
    Raises:
        AssertionError: If files differ
    """
    file1 = Path(file1)
    file2 = Path(file2)
    
    # Check if files exist
    assert file1.exists(), f"File {file1} does not exist"
    assert file2.exists(), f"File {file2} does not exist"
    
    # Check file sizes
    size1 = file1.stat().st_size
    size2 = file2.stat().st_size
    assert size1 == size2, f"File sizes differ: {size1} vs {size2} bytes"
    
    # Compare file contents
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        offset = 0
        while True:
            byte1 = f1.read(1)
            byte2 = f2.read(1)
            
            if not byte1 or not byte2:
                break
                
            # Skip comparison for specified byte ranges
            skip = False
            if ignore_bytes_at_offset:
                for start_offset, length in ignore_bytes_at_offset.items():
                    if start_offset <= offset < start_offset + length:
                        skip = True
                        break
            
            if not skip and byte1 != byte2:
                raise AssertionError(
                    f"Files differ at byte offset {offset}: "
                    f"{byte1.hex()} vs {byte2.hex()}"
                )
            
            offset += 1
    
    return True


def get_caller_module_path() -> Path:
    """
    Get the file path of the module that called the current function.
    
    Useful for locating test data files relative to the test module.
    
    Returns:
        Path object for the caller's module file
    """
    frame = inspect.currentframe()
    try:
        # Get the frame of the caller of the caller of this function
        # (skipping the immediate caller)
        caller_frame = frame.f_back.f_back
        if caller_frame:
            return Path(inspect.getmodule(caller_frame).__file__)
        else:
            # Fallback to the immediate caller if there's no grandparent frame
            return Path(inspect.getmodule(frame.f_back).__file__)
    finally:
        # Always delete the frame to avoid reference cycles
        del frame


def get_test_data_path(relative_path: str = "", create: bool = False) -> Path:
    """
    Get a path to test data files that's relative to the caller's module.
    
    Args:
        relative_path: Relative path from the test_data directory
        create: Whether to create the directory if it doesn't exist
        
    Returns:
        Path object for the specified test data directory/file
    """
    caller_module = get_caller_module_path()
    test_data_dir = caller_module.parent / "test_data"
    
    if relative_path:
        test_data_path = test_data_dir / relative_path
    else:
        test_data_path = test_data_dir
    
    if create and not test_data_path.exists():
        if relative_path and '.' in relative_path.split('/')[-1]:
            # It's a file path, so create the parent directory
            test_data_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # It's a directory path
            test_data_path.mkdir(parents=True, exist_ok=True)
    
    return test_data_path 