"""
Tests for the CLI module
"""

import sys
import pytest
from unittest.mock import patch

from src.cli import main


def test_cli_help():
    """Test that the CLI help command works"""
    with patch('sys.argv', ['ddr']), patch('argparse.ArgumentParser.print_help') as mock_help:
        with pytest.raises(SystemExit):
            main()
        mock_help.assert_called_once()


def test_cli_version():
    """Test that the CLI version command works"""
    with patch('sys.argv', ['ddr', 'version']), patch('builtins.print') as mock_print:
        with patch('src.__version__', '0.1.0'):
            assert main() == 0
            mock_print.assert_called_with('Deep Deep Research v2 version 0.1.0')


def test_cli_research_command(sample_research_topic):
    """Test that the research command works correctly"""
    with patch('sys.argv', ['ddr', 'research', sample_research_topic]), patch('builtins.print') as mock_print:
        assert main() == 0
        mock_print.assert_any_call(f"Starting research on topic: {sample_research_topic}")


def test_cli_sources_list():
    """Test that the sources list command works"""
    with patch('sys.argv', ['ddr', 'sources', '--list']), patch('builtins.print') as mock_print:
        assert main() == 0
        mock_print.assert_any_call("Available sources:")


def test_cli_setup_check():
    """Test that the setup check command works"""
    with patch('sys.argv', ['ddr', 'setup', '--check']), patch('builtins.print') as mock_print:
        assert main() == 0
        mock_print.assert_any_call("Checking configuration...") 