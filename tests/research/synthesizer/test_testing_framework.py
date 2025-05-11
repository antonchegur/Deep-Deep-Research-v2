"""
Tests for the testing and evaluation framework.
"""

import os
import json
import pytest
import asyncio
import tempfile
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

from src.research.synthesizer.testing_framework import (
    EvaluationMetric, PerformanceMetric, TestCase, ABTestConfig,
    QualityEvaluator, PerformanceBenchmark, RegressionTester,
    TestDataGenerator, TestSuite
)
from src.research.synthesizer import GPT4Synthesizer, SynthesisType, SynthesisResult
from src.research.adapters import SourceResult, SourceType


# Sample data for tests
SAMPLE_QUERY = "What is artificial intelligence?"
SAMPLE_SOURCE_RESULTS = [
    SourceResult(
        title="AI Overview",
        content="Artificial intelligence is the simulation of human intelligence by machines...",
        source_name="Example Source",
        source_type=SourceType.WEB_SEARCH,
        url="https://example.com/ai-overview",
        metadata={"relevance": 0.95}
    ),
    SourceResult(
        title="History of AI",
        content="The field of AI research was founded at a workshop held at Dartmouth College in 1956...",
        source_name="Example Source",
        source_type=SourceType.WEB_SEARCH,
        url="https://example.com/ai-history",
        metadata={"relevance": 0.8}
    )
]

# Mock synthesis result for testing evaluation
MOCK_SYNTHESIS_RESULT = SynthesisResult(
    title="Artificial Intelligence Overview",
    content="# Artificial Intelligence Overview\n\nAI refers to the simulation of human intelligence by machines...",
    synthesis_type=SynthesisType.COMPREHENSIVE,
    query=SAMPLE_QUERY,
    sections={"Introduction": "AI refers to...", "History": "The field of AI research..."},
    citations=[{"index": "1", "title": "AI Overview", "source": "example.com"}],
    sources_used=1,
    language="en",
    metadata={"model": "gpt-4o"}
)


def test_evaluation_metric_enum():
    """Test EvaluationMetric enum values."""
    assert EvaluationMetric.RELEVANCE.value == "relevance"
    assert EvaluationMetric.COMPLETENESS.value == "completeness"
    assert EvaluationMetric.COHERENCE.value == "coherence"
    assert EvaluationMetric.ACCURACY.value == "accuracy"
    assert EvaluationMetric.SOURCE_USAGE.value == "source_usage"
    assert EvaluationMetric.CLARITY.value == "clarity"
    assert EvaluationMetric.DEPTH.value == "depth"
    assert EvaluationMetric.CONCISENESS.value == "conciseness"
    assert EvaluationMetric.BIAS.value == "bias"


def test_performance_metric_enum():
    """Test PerformanceMetric enum values."""
    assert PerformanceMetric.LATENCY.value == "latency"
    assert PerformanceMetric.TOKEN_EFFICIENCY.value == "token_efficiency"
    assert PerformanceMetric.ERROR_RATE.value == "error_rate"
    assert PerformanceMetric.THROUGHPUT.value == "throughput"
    assert PerformanceMetric.COST.value == "cost"


def test_test_case_initialization():
    """Test TestCase initialization and methods."""
    # Create a test case
    test_case = TestCase(
        query=SAMPLE_QUERY,
        sources=SAMPLE_SOURCE_RESULTS,
        tags=["ai", "test"],
        metadata={"priority": "high"}
    )
    
    assert test_case.query == SAMPLE_QUERY
    assert len(test_case.sources) == 2
    assert "ai" in test_case.tags
    assert test_case.metadata["priority"] == "high"
    assert len(test_case.results) == 0
    
    # Add a result
    metrics = {
        EvaluationMetric.RELEVANCE: 0.9,
        EvaluationMetric.COMPLETENESS: 0.8
    }
    
    result = test_case.add_result(
        synthesis_result=MOCK_SYNTHESIS_RESULT,
        metrics=metrics,
        version="1.0.0",
        latency=0.8
    )
    
    assert len(test_case.results) == 1
    assert result["version"] == "1.0.0"
    assert result["metrics"]["relevance"] == 0.9
    assert result["latency"] == 0.8
    assert result["model"] == "gpt-4o"
    assert result["score"] == (0.9 + 0.8) / 2  # Average of metric values
    
    # Test to_dict and from_dict
    test_case_dict = test_case.to_dict()
    assert test_case_dict["query"] == SAMPLE_QUERY
    assert test_case_dict["sources_count"] == 2
    assert "ai" in test_case_dict["tags"]
    
    recreated_test_case = TestCase.from_dict(test_case_dict)
    assert recreated_test_case.query == SAMPLE_QUERY
    assert len(recreated_test_case.results) == 1
    assert recreated_test_case.id == test_case.id


def test_ab_test_config():
    """Test ABTestConfig functionality."""
    # Create an A/B test config
    variants = {
        "variant_a": {"system_prompt": "You are a helpful AI...", "temperature": 0.7},
        "variant_b": {"system_prompt": "You are a research assistant...", "temperature": 0.5}
    }
    
    metrics = [
        EvaluationMetric.RELEVANCE,
        EvaluationMetric.CLARITY,
        EvaluationMetric.DEPTH
    ]
    
    ab_test = ABTestConfig(
        name="Prompt Comparison Test",
        description="Comparing different system prompts for research synthesis",
        variants=variants,
        metrics=metrics
    )
    
    assert ab_test.name == "Prompt Comparison Test"
    assert len(ab_test.variants) == 2
    assert len(ab_test.metrics) == 3
    assert len(ab_test.results["variant_a"]) == 0
    assert len(ab_test.results["variant_b"]) == 0
    
    # Create a test case
    test_case = TestCase(
        query=SAMPLE_QUERY,
        sources=SAMPLE_SOURCE_RESULTS
    )
    
    # Add results for each variant
    metrics_a = {
        EvaluationMetric.RELEVANCE: 0.9,
        EvaluationMetric.CLARITY: 0.8,
        EvaluationMetric.DEPTH: 0.7
    }
    
    metrics_b = {
        EvaluationMetric.RELEVANCE: 0.8,
        EvaluationMetric.CLARITY: 0.9,
        EvaluationMetric.DEPTH: 0.8
    }
    
    ab_test.add_result(
        variant_id="variant_a",
        test_case=test_case,
        synthesis_result=MOCK_SYNTHESIS_RESULT,
        metrics=metrics_a,
        latency=0.8
    )
    
    ab_test.add_result(
        variant_id="variant_b",
        test_case=test_case,
        synthesis_result=MOCK_SYNTHESIS_RESULT,
        metrics=metrics_b,
        latency=0.7
    )
    
    assert len(ab_test.results["variant_a"]) == 1
    assert len(ab_test.results["variant_b"]) == 1
    
    # Test summary generation
    summary = ab_test.get_summary()
    assert summary["name"] == "Prompt Comparison Test"
    assert len(summary["variants"]) == 2
    assert len(summary["metrics"]) == 3
    
    assert summary["results"]["variant_a"]["count"] == 1
    assert summary["results"]["variant_b"]["count"] == 1
    
    # Compare scores - variant B should be better
    assert summary["results"]["variant_a"]["score"] < summary["results"]["variant_b"]["score"]
    
    # Test with invalid variant
    with pytest.raises(ValueError):
        ab_test.add_result(
            variant_id="non_existent_variant",
            test_case=test_case,
            synthesis_result=MOCK_SYNTHESIS_RESULT,
            metrics=metrics_a,
            latency=0.8
        )


def test_quality_evaluator():
    """Test QualityEvaluator functionality."""
    evaluator = QualityEvaluator()
    
    # Create a test case
    test_case = TestCase(
        query=SAMPLE_QUERY,
        sources=SAMPLE_SOURCE_RESULTS
    )
    
    # Test with our pre-defined source usage evaluator
    metrics = evaluator.evaluate(
        synthesis_result=MOCK_SYNTHESIS_RESULT,
        test_case=test_case,
        metrics=[EvaluationMetric.SOURCE_USAGE]
    )
    
    assert EvaluationMetric.SOURCE_USAGE in metrics
    assert 0 <= metrics[EvaluationMetric.SOURCE_USAGE] <= 1.0
    
    # The mock result uses 1 out of 2 sources
    assert metrics[EvaluationMetric.SOURCE_USAGE] == 0.5
    
    # Test with a non-existent metric
    metrics = evaluator.evaluate(
        synthesis_result=MOCK_SYNTHESIS_RESULT,
        test_case=test_case,
        metrics=[EvaluationMetric.BIAS]  # Not implemented in base evaluator
    )
    
    assert len(metrics) == 0  # No results


@pytest.mark.asyncio
async def test_performance_benchmark():
    """Test PerformanceBenchmark functionality."""
    benchmark = PerformanceBenchmark()
    
    # Create a mock synthesizer
    mock_synthesizer = MagicMock()
    mock_synthesizer.model = "gpt-4o"
    mock_synthesizer.synthesize = AsyncMock(return_value=MOCK_SYNTHESIS_RESULT)
    
    # Create test cases
    test_case = TestCase(
        query=SAMPLE_QUERY,
        sources=SAMPLE_SOURCE_RESULTS
    )
    
    # Mock sleep to avoid delays in tests
    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        # Run benchmark
        summary = await benchmark.run_latency_test(
            synthesizer=mock_synthesizer,
            test_cases=[test_case],
            runs_per_case=2,
            version="test-version"
        )
        
        # Verify benchmark ran correctly
        assert summary["version"] == "test-version"
        assert summary["test_cases"] == 1
        assert summary["total_runs"] == 2
        
        assert "latency" in summary
        assert "avg" in summary["latency"]
        assert "min" in summary["latency"]
        assert "max" in summary["latency"]
        assert "median" in summary["latency"]
        
        assert len(benchmark.results["test-version"]) == 2
        assert benchmark.results["test-version"][0]["test_case_id"] == test_case.id
        assert benchmark.results["test-version"][0]["model"] == "gpt-4o"
        assert benchmark.results["test-version"][0]["success"] == True
        
        # Verify sleep was called between runs
        assert mock_sleep.call_count == 2
        
        # Verify synthesize was called with correct parameters
        assert mock_synthesizer.synthesize.call_count == 2
        mock_synthesizer.synthesize.assert_called_with(
            query=SAMPLE_QUERY,
            source_results=SAMPLE_SOURCE_RESULTS
        )


def test_test_data_generator():
    """Test TestDataGenerator functionality."""
    # Generate a diverse test suite
    test_cases = TestDataGenerator.create_diverse_test_suite(size=5)
    
    assert len(test_cases) == 5
    
    # Verify test cases have required properties
    for test_case in test_cases:
        assert test_case.query is not None and len(test_case.query) > 0
        assert len(test_case.sources) > 0
        assert len(test_case.tags) > 0
        assert "difficulty" in test_case.metadata
        assert test_case.metadata["difficulty"] in ["easy", "medium", "hard"]


def test_regression_tester():
    """Test RegressionTester functionality."""
    # Create a temporary directory for test files
    with tempfile.TemporaryDirectory() as tmpdir:
        baseline_path = os.path.join(tmpdir, "baseline.json")
        
        # Create a regression tester
        tester = RegressionTester(
            baseline_path=baseline_path,
            threshold=0.1
        )
        
        # Create baseline results
        baseline_results = {
            "test_1": {
                EvaluationMetric.RELEVANCE: 0.8,
                EvaluationMetric.COMPLETENESS: 0.7
            },
            "test_2": {
                EvaluationMetric.RELEVANCE: 0.9,
                EvaluationMetric.COMPLETENESS: 0.8
            }
        }
        
        # Save baseline
        tester.save_baseline(baseline_results)
        
        # Verify baseline file was created
        assert os.path.exists(baseline_path)
        
        # Create new tester that loads baseline
        tester2 = RegressionTester(baseline_path=baseline_path)
        
        # Create current results with some changes
        current_results = {
            "test_1": {
                EvaluationMetric.RELEVANCE: 0.7,  # Regression (0.1 decrease)
                EvaluationMetric.COMPLETENESS: 0.7  # No change
            },
            "test_2": {
                EvaluationMetric.RELEVANCE: 0.95,  # Improvement (0.05 increase)
                EvaluationMetric.COMPLETENESS: 0.85  # Improvement (0.05 increase)
            },
            "test_3": {
                EvaluationMetric.RELEVANCE: 0.8,  # New test
                EvaluationMetric.COMPLETENESS: 0.8
            }
        }
        
        # Compare results
        comparison = tester2.compare_results(current_results)
        
        # Verify comparison results
        assert comparison["test_cases"] == 3
        assert comparison["baseline_cases"] == 2
        assert len(comparison["regressions"]) == 1
        assert len(comparison["improvements"]) == 1
        assert len(comparison["unchanged"]) == 0
        assert len(comparison["new_tests"]) == 1
        assert len(comparison["missing_tests"]) == 0
        
        # Verify regression details
        regression = comparison["regressions"][0]
        assert regression["test_id"] == "test_1"
        assert regression["diff"] < 0
        assert regression["metrics"]["relevance"] == -0.1
        
        # Verify improvement details
        improvement = comparison["improvements"][0]
        assert improvement["test_id"] == "test_2"
        assert improvement["diff"] > 0
        
        # Verify new test
        assert "test_3" in comparison["new_tests"]


def test_test_suite():
    """Test TestSuite functionality."""
    # Create a test suite
    test_suite = TestSuite(
        name="GPT-4 Evaluation Suite",
        description="Test suite for evaluating GPT-4 Turbo performance"
    )
    
    assert test_suite.name == "GPT-4 Evaluation Suite"
    assert test_suite.description == "Test suite for evaluating GPT-4 Turbo performance"
    assert len(test_suite.test_cases) == 0
    
    # Add test cases
    test_case1 = TestCase(
        query="What is machine learning?",
        sources=SAMPLE_SOURCE_RESULTS,
        tags=["ml", "basics"]
    )
    
    test_case2 = TestCase(
        query="How does deep learning work?",
        sources=SAMPLE_SOURCE_RESULTS,
        tags=["dl", "advanced"]
    )
    
    test_suite.add_test_case(test_case1)
    assert len(test_suite.test_cases) == 1
    
    test_suite.add_test_cases([test_case2])
    assert len(test_suite.test_cases) == 2
    
    # Test saving and loading
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save test suite
        test_suite.save(tmpdir)
        
        # Verify files were created
        assert os.path.exists(os.path.join(tmpdir, "metadata.json"))
        assert os.path.exists(os.path.join(tmpdir, "test_cases"))
        assert len(os.listdir(os.path.join(tmpdir, "test_cases"))) == 2
        
        # Load test suite
        loaded_suite = TestSuite.load(tmpdir)
        
        # Verify loaded suite
        assert loaded_suite.name == test_suite.name
        assert loaded_suite.description == test_suite.description
        assert len(loaded_suite.test_cases) == 2
        
        # Verify test case IDs match
        loaded_ids = [tc.id for tc in loaded_suite.test_cases]
        original_ids = [tc.id for tc in test_suite.test_cases]
        assert set(loaded_ids) == set(original_ids) 