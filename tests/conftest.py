"""
pytest configuration file for Deep Deep Research v2
"""

import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from dotenv import load_dotenv

# Add the src directory to the path so that imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load test environment variables
load_dotenv()


@pytest.fixture
def sample_research_topic():
    """Fixture that provides a sample research topic"""
    return "Artificial Intelligence in Healthcare"


@pytest.fixture
def sample_research_output():
    """Fixture that provides a path for sample research output"""
    return os.path.join(os.path.dirname(__file__), 'test_output', 'test_report.pdf')


@pytest.fixture
def mock_api_keys(monkeypatch):
    """Fixture that sets mock API keys for testing"""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_openai_key')
    monkeypatch.setenv('DUCKDUCKGO_API_KEY', 'test_duckduckgo_key')
    monkeypatch.setenv('ARXIV_API_KEY', 'test_arxiv_key')


@pytest.fixture
def test_config():
    """Fixture that provides test configuration"""
    return {
        'research_mode': 'quick',
        'max_sources': 5,
        'language': 'en',
        'pdf_template': 'modern-1'
    }

# --- Enhanced fixtures for comprehensive testing ---

@pytest.fixture
def temp_dir():
    """Fixture that provides a temporary directory for test outputs"""
    with tempfile.TemporaryDirectory(prefix="deep_research_test_") as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_pdf_config():
    """Fixture that provides a sample PDF generation configuration"""
    from src.pdf_generation.pdf_base import ReportConfig, ReportLibrary
    
    return ReportConfig(
        title="Test Report",
        author="Test Author",
        subject="Test Subject",
        keywords=["test", "report", "unit-testing"],
        library=ReportLibrary.REPORTLAB
    )


@pytest.fixture
def sample_json_data():
    """Fixture that provides sample JSON data for testing"""
    return {
        "title": "Test Research Result",
        "query": "Test Query",
        "results": [
            {"title": "Source 1", "content": "Content 1", "url": "http://example.com/1"},
            {"title": "Source 2", "content": "Content 2", "url": "http://example.com/2"}
        ],
        "summary": "This is a test summary of the research results.",
        "metadata": {
            "timestamp": "2025-05-10T10:00:00Z",
            "sources": 2,
            "processing_time": 1.5
        }
    }


@pytest.fixture
def sample_text_content():
    """Fixture that provides sample text content for chunking and processing tests"""
    return """
    Deep Deep Research v2 is an advanced research tool that leverages AI to perform
    comprehensive research on any topic. It integrates with multiple data sources,
    processes and synthesizes information, and generates detailed reports.
    
    The system consists of several core components:
    1. Data Collection Module
    2. Text Processing Pipeline
    3. AI Synthesis Engine
    4. Report Generation System
    
    Each component is designed to be modular and extensible, allowing for easy
    customization and enhancement of the research capabilities.
    """


@pytest.fixture
def mock_source_manager():
    """Fixture that provides a mocked SourceManager for testing"""
    mock = MagicMock()
    mock.search = AsyncMock()
    mock.get_content = AsyncMock()
    return mock


@pytest.fixture
def mock_synthesizer():
    """Fixture that provides a mocked Synthesizer for testing"""
    mock = MagicMock()
    mock.synthesize = AsyncMock()
    mock.custom_synthesis = AsyncMock()
    return mock


@pytest.fixture
def mock_pdf_report():
    """Fixture that provides a mocked PDFReport for testing"""
    mock = MagicMock()
    mock.generate = MagicMock(return_value="test_output.pdf")
    mock.add_element = MagicMock()
    return mock


@pytest.fixture
def sample_research_result_file(temp_dir):
    """Fixture that creates a sample research result JSON file for testing"""
    data = {
        "query": "Artificial Intelligence",
        "timestamp": "2025-05-10T12:00:00Z",
        "search_results": [
            {"title": "AI Overview", "snippet": "AI is a field of computer science...", "url": "https://example.com/ai"},
            {"title": "Machine Learning", "snippet": "Machine learning is a subset of AI...", "url": "https://example.com/ml"}
        ],
        "content_results": [
            {"title": "AI Overview", "content": "Artificial Intelligence (AI) refers to...", "source_type": "web"},
            {"title": "Machine Learning", "content": "Machine Learning enables systems to learn...", "source_type": "web"}
        ],
        "synthesis": {
            "title": "Understanding Artificial Intelligence",
            "content": "Artificial Intelligence is a broad field of computer science...",
            "sections": {
                "Introduction": "AI is transforming industries...",
                "Applications": "AI has numerous applications in healthcare, finance..."
            }
        }
    }
    
    file_path = temp_dir / "research_result.json"
    with open(file_path, "w") as f:
        json.dump(data, f)
    
    return file_path


@pytest.fixture
def reset_singletons():
    """Fixture to reset singleton instances between tests"""
    # This is a placeholder - you would need to implement reset methods in your singletons
    # Example implementation might be:
    # from src.some_module import SomeSingleton
    # SomeSingleton.reset()
    
    # For now, we'll just yield as a placeholder
    yield 