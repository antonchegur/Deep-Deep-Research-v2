"""
Tests for the context management system.
"""

import unittest
from unittest.mock import patch, MagicMock

from src.research.adapters import SourceType, SourceResult
from src.research.synthesizer.context_management import ContextManager, ContextWindow


class TestContextWindow(unittest.TestCase):
    """Tests for the ContextWindow class."""
    
    def test_init(self):
        """Test initialization of ContextWindow."""
        window = ContextWindow(content="Test content", token_count=10)
        self.assertEqual(window.content, "Test content")
        self.assertEqual(window.token_count, 10)
        self.assertEqual(window.priority, 0)
        self.assertEqual(window.metadata, {})
        
    def test_init_with_metadata(self):
        """Test initialization with metadata."""
        metadata = {"type": "test", "source": "example"}
        window = ContextWindow(
            content="Test content", 
            token_count=10, 
            priority=5, 
            metadata=metadata
        )
        self.assertEqual(window.priority, 5)
        self.assertEqual(window.metadata, metadata)


class TestContextManager(unittest.TestCase):
    """Tests for the ContextManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.context_manager = ContextManager(
            model="gpt-4o",
            response_tokens=1000,
            compression_level=1
        )
        
        # Create sample source
        self.sample_source = SourceResult(
            title="Test Source",
            content="This is a test source with some content that will be processed by the context manager.",
            source="Test",
            source_type=SourceType.WEBSITE,
            url="https://example.com",
            metadata={"year": 2023}
        )
        
    def test_init(self):
        """Test initialization of ContextManager."""
        self.assertEqual(self.context_manager.model, "gpt-4o")
        self.assertEqual(self.context_manager.response_tokens, 1000)
        self.assertEqual(self.context_manager.compression_level, 1)
        self.assertEqual(self.context_manager.token_limit, 128000)  # gpt-4o limit
        self.assertEqual(self.context_manager.available_tokens, 127000)  # token_limit - response_tokens
        
    def test_estimate_tokens(self):
        """Test token estimation."""
        text = "This is a sample text with 10 words."
        estimated = self.context_manager.estimate_tokens(text)
        # Should be approximately: 10 words * 1.3 tokens/word
        self.assertAlmostEqual(estimated, 13, delta=3)
        
    def test_add_system_prompt(self):
        """Test adding system prompt."""
        prompt = "You are a helpful assistant."
        initial_tokens = self.context_manager.available_tokens
        
        result = self.context_manager.add_system_prompt(prompt)
        
        self.assertTrue(result)
        self.assertLess(self.context_manager.available_tokens, initial_tokens)
        self.assertEqual(len(self.context_manager.context_windows), 1)
        self.assertEqual(self.context_manager.context_windows[0].content, prompt)
        self.assertEqual(self.context_manager.context_windows[0].metadata.get("type"), "system_prompt")
        self.assertEqual(self.context_manager.context_windows[0].priority, 100)
        
    def test_add_user_input(self):
        """Test adding user input."""
        user_input = "What can you tell me about climate change?"
        initial_tokens = self.context_manager.available_tokens
        
        result = self.context_manager.add_user_input(user_input, priority=80)
        
        self.assertTrue(result)
        self.assertLess(self.context_manager.available_tokens, initial_tokens)
        self.assertEqual(len(self.context_manager.context_windows), 1)
        self.assertEqual(self.context_manager.context_windows[0].content, user_input)
        self.assertEqual(self.context_manager.context_windows[0].metadata.get("type"), "user_input")
        self.assertEqual(self.context_manager.context_windows[0].priority, 80)
        
    def test_add_sources(self):
        """Test adding sources."""
        # Create multiple test sources
        sources = [self.sample_source]
        sources.append(SourceResult(
            title="Another Test Source",
            content="This is another test source with different content to test multiple source handling.",
            source="Test 2",
            source_type=SourceType.DOCUMENT,
            url="https://example.org",
            metadata={"year": 2022}
        ))
        
        initial_tokens = self.context_manager.available_tokens
        sources_added = self.context_manager.add_sources(sources)
        
        self.assertEqual(sources_added, 2)
        self.assertLess(self.context_manager.available_tokens, initial_tokens)
        self.assertGreater(len(self.context_manager.context_windows), 0)
        
    def test_build_messages(self):
        """Test building messages for API request."""
        self.context_manager.add_system_prompt("You are a helpful assistant.")
        self.context_manager.add_user_input("What is climate change?")
        
        messages = self.context_manager.build_messages()
        
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], "You are a helpful assistant.")
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], "What is climate change?")
        
    def test_compress_context_level_0(self):
        """Test context compression at level 0 (no compression)."""
        # Set compression level to 0
        self.context_manager.compression_level = 0
        
        # Add some context
        self.context_manager.add_system_prompt("You are a helpful assistant.")
        self.context_manager.add_user_input("First question")
        self.context_manager.add_user_input("Second question")
        
        initial_windows = len(self.context_manager.context_windows)
        tokens_freed = self.context_manager.compress_context()
        
        # No compression should occur
        self.assertEqual(tokens_freed, 0)
        self.assertEqual(len(self.context_manager.context_windows), initial_windows)
        
    def test_compress_context_level_1(self):
        """Test context compression at level 1 (light compression)."""
        # Ensure compression level is 1
        self.context_manager.compression_level = 1
        
        # Setup a scenario where compression is needed
        self.context_manager.add_system_prompt("You are a helpful assistant.")
        
        # Add several user inputs with different priorities
        for i in range(10):
            self.context_manager.add_user_input(f"Question {i}", priority=10+i)
        
        # Set available tokens to force compression
        self.context_manager.available_tokens = 100
        
        initial_windows = len(self.context_manager.context_windows)
        tokens_freed = self.context_manager.compress_context()
        
        # Some windows should be removed
        self.assertGreater(tokens_freed, 0)
        self.assertLess(len(self.context_manager.context_windows), initial_windows)
        
    def test_compress_context_level_2(self):
        """Test context compression at level 2 (medium compression)."""
        # Set compression level to 2
        self.context_manager.compression_level = 2
        
        # Add content with formatting that can be compressed
        self.context_manager.add_user_input("This is a **formatted** text with some `code` and *emphasis*.")
        
        # Set available tokens to force compression
        self.context_manager.available_tokens = 100
        
        initial_content = self.context_manager.context_windows[0].content
        tokens_freed = self.context_manager.compress_context()
        
        # Content should be modified but window count remains the same
        compressed_content = self.context_manager.context_windows[0].content
        self.assertNotEqual(compressed_content, initial_content)
        self.assertGreater(tokens_freed, 0)
        
    def test_compress_context_level_3(self):
        """Test context compression at level 3 (heavy compression)."""
        # Set compression level to 3
        self.context_manager.compression_level = 3
        
        # Add multiple paragraphs of content
        long_text = """
        First paragraph with multiple sentences. This should be kept. The rest might be removed.
        
        Second paragraph that might be compressed. It has several sentences too. These might be removed.
        
        Third paragraph with more content. This is just for testing.
        """
        self.context_manager.add_user_input(long_text)
        
        # Set available tokens to force compression
        self.context_manager.available_tokens = 100
        
        initial_content = self.context_manager.context_windows[0].content
        tokens_freed = self.context_manager.compress_context()
        
        # Content should be heavily compressed
        compressed_content = self.context_manager.context_windows[0].content
        self.assertNotEqual(compressed_content, initial_content)
        self.assertLess(len(compressed_content), len(initial_content))
        self.assertGreater(tokens_freed, 0)
        
    def test_clear_context(self):
        """Test clearing context."""
        # Add system prompt and user input
        self.context_manager.add_system_prompt("You are a helpful assistant.")
        self.context_manager.add_user_input("What is climate change?")
        
        # Clear context preserving system prompt
        self.context_manager.clear_context(preserve_system=True)
        
        # Should have only the system prompt
        self.assertEqual(len(self.context_manager.context_windows), 1)
        self.assertEqual(self.context_manager.context_windows[0].metadata.get("type"), "system_prompt")
        
        # Clear context without preserving system prompt
        self.context_manager.clear_context(preserve_system=False)
        
        # Should have no windows
        self.assertEqual(len(self.context_manager.context_windows), 0)
        
    def test_chunk_text(self):
        """Test text chunking functionality."""
        # Create a long text with multiple paragraphs
        long_text = "\n\n".join([f"Paragraph {i} with some content." for i in range(10)])
        
        # Mock estimate_tokens to return predictable values
        with patch.object(self.context_manager, 'estimate_tokens', side_effect=lambda text: len(text) // 5):
            chunks = self.context_manager._chunk_text(
                text=long_text,
                title="Test Document",
                source_idx=1,
                max_chunk_tokens=50
            )
            
            # Should have created multiple chunks
            self.assertGreater(len(chunks), 1)
            
            # Each chunk should have appropriate metadata
            for i, chunk in enumerate(chunks):
                self.assertEqual(chunk.metadata.get("type"), "source_content")
                self.assertEqual(chunk.metadata.get("source_idx"), 1)
                self.assertEqual(chunk.metadata.get("title"), "Test Document")
                self.assertEqual(chunk.metadata.get("chunk_idx"), i+1)
                self.assertLessEqual(chunk.token_count, 50)
                
    def test_prioritize_sources(self):
        """Test source prioritization."""
        sources = [
            SourceResult(
                title="Academic Source",
                content="Academic content",
                source="Academic",
                source_type=SourceType.ACADEMIC,
                url="https://example.edu",
                metadata={"year": 2023}
            ),
            SourceResult(
                title="News Source",
                content="News content",
                source="News",
                source_type=SourceType.NEWS,
                url="https://example.news",
                metadata={"year": 2021}
            ),
            SourceResult(
                title="Wikipedia Source",
                content="Wikipedia content",
                source="Wikipedia",
                source_type=SourceType.WIKIPEDIA,
                url="https://wikipedia.org",
                metadata={"year": 2022}
            )
        ]
        
        prioritized = self.context_manager._prioritize_sources(sources)
        
        # Academic should be first due to source type score
        self.assertEqual(prioritized[0].source_type, SourceType.ACADEMIC)
        
    def test_archive_window(self):
        """Test archiving window to history."""
        window = ContextWindow(
            content="Content to archive",
            token_count=10,
            priority=50,
            metadata={"type": "test"}
        )
        
        self.context_manager._archive_window(window)
        
        # History should contain the archived window
        self.assertEqual(len(self.context_manager.context_history), 1)
        self.assertEqual(self.context_manager.context_history[0]["token_count"], 10)
        self.assertEqual(self.context_manager.context_history[0]["priority"], 50)
        self.assertEqual(self.context_manager.context_history[0]["metadata"], {"type": "test"})


if __name__ == "__main__":
    unittest.main() 