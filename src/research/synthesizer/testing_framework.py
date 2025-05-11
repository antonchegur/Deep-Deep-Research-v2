"""
Testing and evaluation framework for GPT-4 Turbo integration.

This module provides tools and utilities for:
1. Evaluating response quality through metrics
2. Performance benchmarking
3. A/B testing for prompt optimization
4. Regression testing tools
5. Test data generation
"""

import json
import time
import random
import logging
import asyncio
import statistics
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from pathlib import Path
from datetime import datetime

from .base import SynthesisType, SynthesisResult
from ..adapters import SourceResult

logger = logging.getLogger(__name__)


class EvaluationMetric(Enum):
    """Evaluation metrics for assessing response quality."""
    RELEVANCE = "relevance"                  # Relevance to query
    COMPLETENESS = "completeness"            # Coverage of source material
    COHERENCE = "coherence"                  # Logical flow and structure
    ACCURACY = "accuracy"                    # Factual correctness
    SOURCE_USAGE = "source_usage"            # Effective use of sources
    CLARITY = "clarity"                      # Readability and clarity
    DEPTH = "depth"                          # Analysis depth
    CONCISENESS = "conciseness"              # Appropriate length
    BIAS = "bias"                            # Balanced perspective


class PerformanceMetric(Enum):
    """Performance metrics for benchmarking."""
    LATENCY = "latency"                      # Response time
    TOKEN_EFFICIENCY = "token_efficiency"    # Output quality vs token usage
    ERROR_RATE = "error_rate"                # API errors per request
    THROUGHPUT = "throughput"                # Requests per minute
    COST = "cost"                            # API cost


class TestCase:
    """Represents a test case for evaluating synthesis."""
    
    def __init__(self, 
                query: str,
                sources: List[SourceResult],
                expected_metrics: Optional[Dict[EvaluationMetric, float]] = None,
                tags: Optional[List[str]] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a test case.
        
        Args:
            query: The research query
            sources: List of source results
            expected_metrics: Expected evaluation metric scores
            tags: Tags for categorizing the test case
            metadata: Additional metadata
        """
        self.id = f"test_{int(time.time())}_{random.randint(1000, 9999)}"
        self.query = query
        self.sources = sources
        self.expected_metrics = expected_metrics or {}
        self.tags = tags or []
        self.metadata = metadata or {}
        self.results: List[Dict[str, Any]] = []
    
    def add_result(self, 
                  synthesis_result: SynthesisResult,
                  metrics: Dict[EvaluationMetric, float],
                  version: str,
                  latency: float):
        """
        Add an evaluation result for this test case.
        
        Args:
            synthesis_result: The synthesis result
            metrics: Evaluation metrics
            version: Version identifier of the system under test
            latency: Response latency in seconds
        """
        result = {
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "metrics": {m.value: v for m, v in metrics.items()},
            "latency": latency,
            "synthesis_type": synthesis_result.synthesis_type.value,
            "model": synthesis_result.metadata.get("model", "unknown"),
            "score": sum(metrics.values()) / len(metrics) if metrics else 0,
        }
        self.results.append(result)
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert test case to dictionary for serialization."""
        return {
            "id": self.id,
            "query": self.query,
            "sources_count": len(self.sources),
            "tags": self.tags,
            "metadata": self.metadata,
            "expected_metrics": {m.value: v for m, v in self.expected_metrics.items()},
            "results": self.results
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestCase':
        """Create a test case from dictionary."""
        instance = cls(
            query=data["query"],
            sources=[],  # Sources need to be loaded separately
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )
        
        if "expected_metrics" in data:
            instance.expected_metrics = {
                EvaluationMetric(k): v for k, v in data["expected_metrics"].items()
            }
        
        instance.id = data.get("id", instance.id)
        instance.results = data.get("results", [])
        return instance


class ABTestConfig:
    """Configuration for A/B testing of different prompt versions."""
    
    def __init__(self, 
                name: str,
                description: str,
                variants: Dict[str, Dict[str, Any]],
                metrics: List[EvaluationMetric]):
        """
        Initialize A/B test configuration.
        
        Args:
            name: Test name
            description: Test description
            variants: Dictionary of variant IDs to their configurations
            metrics: Metrics to evaluate for each variant
        """
        self.name = name
        self.description = description
        self.variants = variants
        self.metrics = metrics
        self.results: Dict[str, List[Dict[str, Any]]] = {vid: [] for vid in variants}
    
    def add_result(self, 
                  variant_id: str,
                  test_case: TestCase,
                  synthesis_result: SynthesisResult,
                  metrics: Dict[EvaluationMetric, float],
                  latency: float):
        """
        Add a result for a variant.
        
        Args:
            variant_id: Variant identifier
            test_case: Test case evaluated
            synthesis_result: The synthesis result
            metrics: Evaluation metrics
            latency: Response latency in seconds
        """
        if variant_id not in self.variants:
            raise ValueError(f"Unknown variant ID: {variant_id}")
        
        result = {
            "test_case_id": test_case.id,
            "query": test_case.query,
            "timestamp": datetime.now().isoformat(),
            "metrics": {m.value: v for m, v in metrics.items()},
            "latency": latency,
            "synthesis_type": synthesis_result.synthesis_type.value,
            "model": synthesis_result.metadata.get("model", "unknown"),
            "score": sum(metrics.values()) / len(metrics) if metrics else 0,
        }
        
        self.results[variant_id].append(result)
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of test results."""
        summary = {
            "name": self.name,
            "description": self.description,
            "variants": list(self.variants.keys()),
            "metrics": [m.value for m in self.metrics],
            "results": {}
        }
        
        for variant_id, results in self.results.items():
            if not results:
                summary["results"][variant_id] = {"count": 0}
                continue
            
            variant_summary = {
                "count": len(results),
                "metrics": {},
                "latency": {
                    "avg": statistics.mean(r["latency"] for r in results),
                    "min": min(r["latency"] for r in results),
                    "max": max(r["latency"] for r in results)
                },
                "score": statistics.mean(r["score"] for r in results)
            }
            
            # Summarize metrics
            for metric in self.metrics:
                metric_values = [r["metrics"].get(metric.value, 0) for r in results]
                if metric_values:
                    variant_summary["metrics"][metric.value] = {
                        "avg": statistics.mean(metric_values),
                        "min": min(metric_values),
                        "max": max(metric_values)
                    }
            
            summary["results"][variant_id] = variant_summary
        
        return summary


class QualityEvaluator:
    """Evaluates the quality of synthesis results using various metrics."""
    
    def __init__(self, models_config: Optional[Dict[str, Any]] = None):
        """
        Initialize quality evaluator.
        
        Args:
            models_config: Configuration for evaluation models
        """
        self.models_config = models_config or {}
        self.evaluation_functions: Dict[EvaluationMetric, Callable] = {
            EvaluationMetric.SOURCE_USAGE: self._evaluate_source_usage,
            # Other built-in evaluators would be registered here
        }
    
    def evaluate(self, 
                synthesis_result: SynthesisResult,
                test_case: TestCase,
                metrics: List[EvaluationMetric] = None) -> Dict[EvaluationMetric, float]:
        """
        Evaluate a synthesis result using the specified metrics.
        
        Args:
            synthesis_result: The synthesis result to evaluate
            test_case: The test case used to generate the result
            metrics: List of metrics to evaluate (default: all registered metrics)
            
        Returns:
            Dictionary of metrics and their scores (0.0-1.0)
        """
        if metrics is None:
            metrics = list(self.evaluation_functions.keys())
        
        results = {}
        for metric in metrics:
            if metric in self.evaluation_functions:
                results[metric] = self.evaluation_functions[metric](
                    synthesis_result, test_case)
            else:
                logger.warning(f"No evaluation function for metric: {metric.value}")
        
        return results
    
    def _evaluate_source_usage(self, 
                              synthesis_result: SynthesisResult,
                              test_case: TestCase) -> float:
        """
        Evaluate how effectively the sources were used.
        
        Args:
            synthesis_result: The synthesis result
            test_case: The test case
            
        Returns:
            Score between 0.0 and 1.0
        """
        # Basic source usage metric - ratio of sources mentioned
        if not test_case.sources:
            return 0.0
        
        sources_used = synthesis_result.sources_used
        total_sources = len(test_case.sources)
        
        # Simple ratio of sources used
        return min(1.0, sources_used / total_sources)
    
    # Additional evaluation methods would be implemented here
    # Advanced implementations could use LLM-based evaluation


class PerformanceBenchmark:
    """Benchmark performance metrics of the GPT-4 Turbo integration."""
    
    def __init__(self):
        """Initialize performance benchmark."""
        self.results: Dict[str, List[Dict[str, Any]]] = {}
    
    async def run_latency_test(self, 
                              synthesizer: Any,
                              test_cases: List[TestCase],
                              runs_per_case: int = 3,
                              version: str = "current") -> Dict[str, Any]:
        """
        Benchmark latency performance.
        
        Args:
            synthesizer: The synthesizer to test
            test_cases: List of test cases
            runs_per_case: Number of runs per test case
            version: Version identifier
            
        Returns:
            Benchmark results
        """
        if version not in self.results:
            self.results[version] = []
        
        all_latencies = []
        
        for test_case in test_cases:
            case_latencies = []
            
            for i in range(runs_per_case):
                start_time = time.time()
                
                try:
                    result = await synthesizer.synthesize(
                        query=test_case.query,
                        source_results=test_case.sources
                    )
                    
                    latency = time.time() - start_time
                    case_latencies.append(latency)
                    all_latencies.append(latency)
                    
                    # Record the result
                    benchmark_result = {
                        "test_case_id": test_case.id,
                        "run": i + 1,
                        "latency": latency,
                        "success": result is not None,
                        "model": synthesizer.model,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    self.results[version].append(benchmark_result)
                    
                except Exception as e:
                    logger.error(f"Benchmark error: {e}")
                    
                # Add a small delay between runs to avoid rate limiting
                await asyncio.sleep(1)
        
        # Calculate summary statistics
        summary = {
            "version": version,
            "test_cases": len(test_cases),
            "total_runs": len(self.results[version]),
            "timestamp": datetime.now().isoformat(),
            "latency": {
                "avg": statistics.mean(all_latencies) if all_latencies else 0,
                "min": min(all_latencies) if all_latencies else 0,
                "max": max(all_latencies) if all_latencies else 0,
                "median": statistics.median(all_latencies) if all_latencies else 0
            }
        }
        
        return summary
    
    # Additional benchmark methods would be implemented here


class TestDataGenerator:
    """Generates test data for evaluating synthesis."""
    
    @staticmethod
    def create_diverse_test_suite(size: int = 10) -> List[TestCase]:
        """
        Create a diverse test suite with various queries and sources.
        
        Args:
            size: Number of test cases to generate
            
        Returns:
            List of test cases
        """
        # Research domains for test generation
        domains = [
            "Healthcare", "Climate Change", "Technology", "Economics", 
            "Politics", "Education", "Psychology", "AI Ethics", 
            "Nutrition", "Space Exploration", "History", "Biology"
        ]
        
        # Query templates
        templates = [
            "What are the latest advances in {domain}?",
            "How does {domain} impact society?",
            "What are the ethical considerations in {domain}?",
            "Compare different approaches to {domain}.",
            "What is the future of {domain}?",
            "What are the key challenges in {domain}?",
            "How has {domain} evolved over the past decade?",
            "What are the economic implications of {domain}?"
        ]
        
        test_cases = []
        
        for i in range(size):
            # Select domain and template
            domain = random.choice(domains)
            template = random.choice(templates)
            
            # Generate query
            query = template.format(domain=domain)
            
            # Generate mock sources (in a real implementation, these would be more sophisticated)
            num_sources = random.randint(2, 5)
            sources = []
            
            for j in range(num_sources):
                source = SourceResult(
                    source_id=f"source_{i}_{j}",
                    title=f"{domain} {'Research' if j == 0 else 'Overview' if j == 1 else 'Analysis'} {j+1}",
                    url=f"https://example.com/{domain.lower().replace(' ', '-')}/{j+1}",
                    content=f"Mock content for {domain} source {j+1}. This would be more extensive in a real test.",
                    metadata={
                        "relevance": round(random.uniform(0.7, 1.0), 2),
                        "domain": domain,
                        "type": "academic" if j % 2 == 0 else "web"
                    }
                )
                sources.append(source)
            
            # Create test case
            test_case = TestCase(
                query=query,
                sources=sources,
                tags=[domain.lower(), "auto-generated"],
                metadata={"difficulty": random.choice(["easy", "medium", "hard"])}
            )
            
            test_cases.append(test_case)
        
        return test_cases
    
    # Additional data generation methods would be implemented here


class RegressionTester:
    """Manages regression testing to detect quality degradation."""
    
    def __init__(self, 
                baseline_path: Optional[str] = None,
                threshold: float = 0.1):
        """
        Initialize regression tester.
        
        Args:
            baseline_path: Path to baseline results
            threshold: Threshold for detecting significant changes
        """
        self.baseline_path = baseline_path
        self.threshold = threshold
        self.baseline_results: Dict[str, Dict[str, Any]] = {}
        
        if baseline_path:
            self.load_baseline()
    
    def load_baseline(self, path: Optional[str] = None):
        """
        Load baseline results from file.
        
        Args:
            path: Path to baseline file (if different from initialized path)
        """
        load_path = path or self.baseline_path
        if not load_path:
            logger.warning("No baseline path specified")
            return
        
        try:
            with open(load_path, 'r') as f:
                self.baseline_results = json.load(f)
            logger.info(f"Loaded baseline results with {len(self.baseline_results)} test cases")
        except Exception as e:
            logger.error(f"Error loading baseline: {e}")
    
    def save_baseline(self, 
                     results: Dict[str, Dict[EvaluationMetric, float]],
                     path: Optional[str] = None):
        """
        Save baseline results to file.
        
        Args:
            results: Dictionary of test case IDs to metric results
            path: Path to save baseline (if different from initialized path)
        """
        save_path = path or self.baseline_path
        if not save_path:
            logger.warning("No baseline path specified")
            return
        
        # Convert enum keys to strings for JSON serialization
        serialized_results = {}
        for test_id, metrics in results.items():
            serialized_results[test_id] = {m.value: v for m, v in metrics.items()}
        
        try:
            with open(save_path, 'w') as f:
                json.dump(serialized_results, f, indent=2)
            logger.info(f"Saved baseline with {len(results)} test cases to {save_path}")
            
            # Update in-memory baseline
            self.baseline_results = serialized_results
        except Exception as e:
            logger.error(f"Error saving baseline: {e}")
    
    def compare_results(self, 
                       current_results: Dict[str, Dict[EvaluationMetric, float]]) -> Dict[str, Any]:
        """
        Compare current results against baseline.
        
        Args:
            current_results: Dictionary of test case IDs to metric results
            
        Returns:
            Comparison results with detected regressions
        """
        if not self.baseline_results:
            logger.warning("No baseline results available for comparison")
            return {"error": "No baseline available"}
        
        comparison = {
            "test_cases": len(current_results),
            "baseline_cases": len(self.baseline_results),
            "regressions": [],
            "improvements": [],
            "unchanged": [],
            "new_tests": [],
            "missing_tests": [],
            "overall_diff": 0.0
        }
        
        # Convert current results enum keys to strings
        serialized_current = {}
        for test_id, metrics in current_results.items():
            serialized_current[test_id] = {m.value: v for m, v in metrics.items()}
        
        # Track differences for overall change calculation
        all_diffs = []
        
        # Compare each test case
        for test_id, current_metrics in serialized_current.items():
            if test_id in self.baseline_results:
                baseline_metrics = self.baseline_results[test_id]
                
                # Compare metrics
                diffs = {}
                for metric, value in current_metrics.items():
                    if metric in baseline_metrics:
                        diff = value - baseline_metrics[metric]
                        diffs[metric] = diff
                        all_diffs.append(diff)
                
                # Calculate average change
                avg_diff = sum(diffs.values()) / len(diffs) if diffs else 0
                
                # Classify the change
                if abs(avg_diff) < self.threshold:
                    comparison["unchanged"].append({
                        "test_id": test_id,
                        "diff": avg_diff,
                        "metrics": diffs
                    })
                elif avg_diff < 0:
                    comparison["regressions"].append({
                        "test_id": test_id,
                        "diff": avg_diff,
                        "metrics": diffs
                    })
                else:
                    comparison["improvements"].append({
                        "test_id": test_id,
                        "diff": avg_diff,
                        "metrics": diffs
                    })
            else:
                comparison["new_tests"].append(test_id)
        
        # Find missing tests (in baseline but not in current)
        for test_id in self.baseline_results:
            if test_id not in serialized_current:
                comparison["missing_tests"].append(test_id)
        
        # Calculate overall difference
        comparison["overall_diff"] = statistics.mean(all_diffs) if all_diffs else 0.0
        
        return comparison


class TestSuite:
    """A collection of test cases for evaluating the system."""
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize test suite.
        
        Args:
            name: Name of the test suite
            description: Description of the test suite
        """
        self.name = name
        self.description = description
        self.test_cases: List[TestCase] = []
        self.created_at = datetime.now().isoformat()
    
    def add_test_case(self, test_case: TestCase):
        """
        Add a test case to the suite.
        
        Args:
            test_case: Test case to add
        """
        self.test_cases.append(test_case)
    
    def add_test_cases(self, test_cases: List[TestCase]):
        """
        Add multiple test cases to the suite.
        
        Args:
            test_cases: List of test cases to add
        """
        self.test_cases.extend(test_cases)
    
    def save(self, directory: str):
        """
        Save the test suite to a directory.
        
        Args:
            directory: Directory to save to
        """
        # Create directory if it doesn't exist
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        
        # Save test suite metadata
        metadata = {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": datetime.now().isoformat(),
            "test_count": len(self.test_cases)
        }
        
        with open(path / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save each test case
        test_cases_dir = path / "test_cases"
        test_cases_dir.mkdir(exist_ok=True)
        
        for test_case in self.test_cases:
            test_case_path = test_cases_dir / f"{test_case.id}.json"
            with open(test_case_path, 'w') as f:
                json.dump(test_case.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, directory: str) -> 'TestSuite':
        """
        Load a test suite from a directory.
        
        Args:
            directory: Directory to load from
            
        Returns:
            Loaded test suite
        """
        path = Path(directory)
        
        # Load metadata
        with open(path / "metadata.json", 'r') as f:
            metadata = json.load(f)
        
        # Create test suite
        test_suite = cls(name=metadata["name"], description=metadata["description"])
        test_suite.created_at = metadata["created_at"]
        
        # Load test cases
        test_cases_dir = path / "test_cases"
        for test_case_path in test_cases_dir.glob("*.json"):
            with open(test_case_path, 'r') as f:
                test_case_data = json.load(f)
                test_case = TestCase.from_dict(test_case_data)
                test_suite.add_test_case(test_case)
        
        return test_suite 