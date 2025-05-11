#!/usr/bin/env python3
"""
Testing Framework Demo for Deep Deep Research v2.

This script demonstrates how to use the testing and evaluation framework
for GPT-4 Turbo integration, including:
1. Creating test cases
2. Running A/B tests on different prompts
3. Benchmarking performance
4. Detecting regressions
5. Using the test data generator
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.research.synthesizer import GPT4Synthesizer, SynthesisType
from src.research.adapters import SourceResult
from src.research.synthesizer.testing_framework import (
    EvaluationMetric, PerformanceMetric, TestCase, ABTestConfig,
    QualityEvaluator, PerformanceBenchmark, RegressionTester,
    TestDataGenerator, TestSuite
)
from src.research.synthesizer.prompt_engineering import PromptLibrary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("testing_framework_demo")

# Create output directory for test artifacts
OUTPUT_DIR = Path("./test_artifacts")
OUTPUT_DIR.mkdir(exist_ok=True)


async def run_ab_test_demo():
    """Demonstrate A/B testing different prompt variants."""
    logger.info("=== A/B Testing Demo ===")
    
    # Create test data
    test_cases = TestDataGenerator.create_diverse_test_suite(size=3)
    logger.info(f"Generated {len(test_cases)} test cases for A/B testing")
    
    # Define prompt variants
    variants = {
        "baseline": {
            "system_prompt": PromptLibrary.get_prompt(SynthesisType.SUMMARY),
            "temperature": 0.7
        },
        "focused": {
            "system_prompt": PromptLibrary.get_prompt(SynthesisType.SUMMARY) + 
                            "\nFocus on providing concise, factual information with minimal speculation.",
            "temperature": 0.5
        },
        "detailed": {
            "system_prompt": PromptLibrary.get_prompt(SynthesisType.COMPREHENSIVE),
            "temperature": 0.7
        }
    }
    
    # Create A/B test configuration
    test_config = ABTestConfig(
        name="Prompt Optimization Test",
        description="Comparing different prompt variants for research synthesis",
        variants=variants,
        metrics=[
            EvaluationMetric.RELEVANCE,
            EvaluationMetric.COMPLETENESS,
            EvaluationMetric.CLARITY
        ]
    )
    
    # Create synthesizer with mock response for demo
    synthesizer = GPT4Synthesizer(
        api_key="demo-key" if not os.getenv("OPENAI_API_KEY") else None,
        max_retries=0  # For demo purposes
    )
    
    # Mock the API call for demo purposes
    async def mock_synthesize(query, source_results, **kwargs):
        # Simulate different responses based on variant
        variant_id = kwargs.get("variant_id", "baseline")
        temperature = variants[variant_id]["temperature"]
        
        # Simulate effect of temperature on response quality
        clarity_score = 0.9 - (temperature * 0.2)  # Lower temp = more clarity
        completeness_score = 0.7 + (temperature * 0.2)  # Higher temp = more complete
        
        # Simulate effect of prompt type on response structure
        is_detailed = "detailed" in variant_id
        
        return {
            "title": f"Research on {query[:20]}...",
            "content": f"{'# Detailed ' if is_detailed else '# '}Response for {query}\n\n" +
                      f"This is a simulated {'comprehensive' if is_detailed else 'summary'} " +
                      f"response with {'high' if clarity_score > 0.8 else 'moderate'} clarity " +
                      f"and {'high' if completeness_score > 0.8 else 'moderate'} completeness.",
            "synthesis_type": SynthesisType.COMPREHENSIVE if is_detailed else SynthesisType.SUMMARY,
            "sources_used": len(source_results) if completeness_score > 0.8 else len(source_results) - 1,
            "metadata": {
                "model": "gpt-4o",
                "temperature": temperature,
                "variant": variant_id
            }
        }
    
    # Replace synthesizer method with mock for demo
    synthesizer.synthesize = mock_synthesize
    
    # Create quality evaluator
    evaluator = QualityEvaluator()
    
    # Run tests for each variant
    for variant_id in variants:
        logger.info(f"Testing variant: {variant_id}")
        
        for test_case in test_cases:
            # Simulate A/B test run
            start_time = datetime.now()
            
            # Call synthesizer with variant
            result = await synthesizer.synthesize(
                query=test_case.query,
                source_results=test_case.sources,
                variant_id=variant_id
            )
            
            # Calculate latency
            latency = (datetime.now() - start_time).total_seconds()
            
            # Create SynthesisResult from mock response
            from src.research.synthesizer.base import SynthesisResult
            synthesis_result = SynthesisResult(
                title=result["title"],
                content=result["content"],
                synthesis_type=result["synthesis_type"],
                query=test_case.query,
                sections={},
                citations=[],
                sources_used=result["sources_used"],
                language="en",
                metadata=result["metadata"]
            )
            
            # Evaluate results
            metrics = {
                EvaluationMetric.RELEVANCE: 0.85,  # Simulated metric
                EvaluationMetric.COMPLETENESS: 0.7 + (0.2 * (result["sources_used"] / len(test_case.sources))),
                EvaluationMetric.CLARITY: 0.9 - (variants[variant_id]["temperature"] * 0.2)
            }
            
            # Add result to test config
            test_config.add_result(
                variant_id=variant_id,
                test_case=test_case,
                synthesis_result=synthesis_result,
                metrics=metrics,
                latency=latency
            )
    
    # Generate summary report
    summary = test_config.get_summary()
    
    # Print results
    logger.info("\nA/B Test Results:")
    logger.info(f"Test: {summary['name']}")
    logger.info(f"Metrics: {', '.join(summary['metrics'])}")
    
    for variant_id, results in summary["results"].items():
        logger.info(f"\nVariant: {variant_id}")
        logger.info(f"  Test runs: {results['count']}")
        logger.info(f"  Overall score: {results['score']:.2f}")
        logger.info(f"  Avg latency: {results['latency']['avg']:.2f}s")
        
        for metric, values in results.get("metrics", {}).items():
            logger.info(f"  {metric}: {values['avg']:.2f} (min: {values['min']:.2f}, max: {values['max']:.2f})")
    
    # Save results
    with open(OUTPUT_DIR / "ab_test_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"\nA/B test results saved to {OUTPUT_DIR / 'ab_test_results.json'}")
    
    # Identify the best variant
    best_variant = max(
        summary["results"].items(),
        key=lambda x: x[1]["score"] if "score" in x[1] else 0
    )[0]
    
    logger.info(f"\n✨ Best variant: {best_variant}")
    return best_variant


async def run_benchmark_demo():
    """Demonstrate performance benchmarking."""
    logger.info("\n=== Performance Benchmark Demo ===")
    
    # Create a small test suite
    test_cases = TestDataGenerator.create_diverse_test_suite(size=2)
    
    # Create synthesizer with mock for demo
    synthesizer = GPT4Synthesizer(
        api_key="demo-key" if not os.getenv("OPENAI_API_KEY") else None
    )
    
    # Mock the synthesize method to return quickly
    async def mock_synthesize(query, source_results, **kwargs):
        # Simulate API latency
        await asyncio.sleep(0.2)
        
        from src.research.synthesizer.base import SynthesisResult
        return SynthesisResult(
            title=f"Results for {query[:20]}...",
            content=f"This is a mock response for benchmark testing.",
            synthesis_type=SynthesisType.SUMMARY,
            query=query,
            sections={},
            citations=[],
            sources_used=len(source_results),
            language="en",
            metadata={"model": "gpt-4o"}
        )
    
    # Replace with mock
    synthesizer.synthesize = mock_synthesize
    
    # Create benchmark
    benchmark = PerformanceBenchmark()
    
    # Run latency test
    results = await benchmark.run_latency_test(
        synthesizer=synthesizer,
        test_cases=test_cases,
        runs_per_case=3,
        version="current"
    )
    
    # Display results
    logger.info("\nBenchmark Results:")
    logger.info(f"Total test cases: {results['test_cases']}")
    logger.info(f"Total runs: {results['total_runs']}")
    logger.info(f"Average latency: {results['latency']['avg']:.3f}s")
    logger.info(f"Min latency: {results['latency']['min']:.3f}s")
    logger.info(f"Max latency: {results['latency']['max']:.3f}s")
    
    # Save results
    with open(OUTPUT_DIR / "benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nBenchmark results saved to {OUTPUT_DIR / 'benchmark_results.json'}")


async def run_regression_test_demo():
    """Demonstrate regression testing."""
    logger.info("\n=== Regression Testing Demo ===")
    
    # Create baseline results
    baseline_results = {
        f"test_{i}": {
            EvaluationMetric.RELEVANCE: 0.8 + (i * 0.02),
            EvaluationMetric.COMPLETENESS: 0.7 + (i * 0.03),
            EvaluationMetric.COHERENCE: 0.9 - (i * 0.01)
        }
        for i in range(5)
    }
    
    # Save baseline
    baseline_path = OUTPUT_DIR / "baseline.json"
    
    # Create regression tester
    tester = RegressionTester(baseline_path=str(baseline_path))
    tester.save_baseline(baseline_results)
    
    logger.info(f"Saved baseline with {len(baseline_results)} test cases")
    
    # Create new results with some regressions
    current_results = {}
    
    # Copy baseline for some tests
    for i in range(2):
        test_id = f"test_{i}"
        current_results[test_id] = baseline_results[test_id].copy()
    
    # Add regression
    current_results["test_2"] = {
        EvaluationMetric.RELEVANCE: baseline_results["test_2"][EvaluationMetric.RELEVANCE] - 0.15,  # significant regression
        EvaluationMetric.COMPLETENESS: baseline_results["test_2"][EvaluationMetric.COMPLETENESS],
        EvaluationMetric.COHERENCE: baseline_results["test_2"][EvaluationMetric.COHERENCE]
    }
    
    # Add improvement
    current_results["test_3"] = {
        EvaluationMetric.RELEVANCE: baseline_results["test_3"][EvaluationMetric.RELEVANCE] + 0.1,
        EvaluationMetric.COMPLETENESS: baseline_results["test_3"][EvaluationMetric.COMPLETENESS] + 0.05,
        EvaluationMetric.COHERENCE: baseline_results["test_3"][EvaluationMetric.COHERENCE]
    }
    
    # Add new test
    current_results["test_new"] = {
        EvaluationMetric.RELEVANCE: 0.85,
        EvaluationMetric.COMPLETENESS: 0.8,
        EvaluationMetric.COHERENCE: 0.9
    }
    
    # Compare results
    comparison = tester.compare_results(current_results)
    
    # Display results
    logger.info("\nRegression Test Results:")
    logger.info(f"Test cases: {comparison['test_cases']}")
    logger.info(f"Baseline cases: {comparison['baseline_cases']}")
    logger.info(f"Overall diff: {comparison['overall_diff']:.3f}")
    
    logger.info(f"\nRegressions: {len(comparison['regressions'])}")
    for reg in comparison["regressions"]:
        logger.info(f"  {reg['test_id']}: {reg['diff']:.3f} change")
        for metric, diff in reg["metrics"].items():
            if diff < 0:
                logger.info(f"    - {metric}: {diff:.3f}")
    
    logger.info(f"\nImprovements: {len(comparison['improvements'])}")
    for imp in comparison["improvements"]:
        logger.info(f"  {imp['test_id']}: +{imp['diff']:.3f} change")
    
    logger.info(f"\nNew tests: {len(comparison['new_tests'])}")
    for test in comparison["new_tests"]:
        logger.info(f"  {test}")
    
    logger.info(f"\nMissing tests: {len(comparison['missing_tests'])}")
    for test in comparison["missing_tests"]:
        logger.info(f"  {test}")
    
    # Save comparison
    with open(OUTPUT_DIR / "regression_comparison.json", "w") as f:
        json.dump(comparison, f, indent=2)
    
    logger.info(f"\nRegression comparison saved to {OUTPUT_DIR / 'regression_comparison.json'}")


async def main():
    """Run the testing framework demo."""
    logger.info("Starting Testing Framework Demo")
    
    try:
        # Run A/B test demo
        best_variant = await run_ab_test_demo()
        
        # Run benchmark demo
        await run_benchmark_demo()
        
        # Run regression test demo
        await run_regression_test_demo()
        
        logger.info("\n=== Testing Framework Demo Complete ===")
        logger.info(f"All demo artifacts saved to {OUTPUT_DIR}")
        logger.info(f"Recommended configuration: Use '{best_variant}' variant for best performance")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    asyncio.run(main()) 