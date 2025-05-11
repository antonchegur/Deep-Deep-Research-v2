"""
Synthesizer module for analyzing and synthesizing research data.
"""

from .base import SynthesisResult, SynthesisType, BaseSynthesizer
from .gpt4_turbo import GPT4Synthesizer
from .testing_framework import (
    EvaluationMetric, PerformanceMetric, TestCase, ABTestConfig,
    QualityEvaluator, PerformanceBenchmark, RegressionTester,
    TestDataGenerator, TestSuite
)

__all__ = [
    "SynthesisResult",
    "SynthesisType",
    "BaseSynthesizer",
    "GPT4Synthesizer",
    # Testing framework components
    "EvaluationMetric",
    "PerformanceMetric",
    "TestCase",
    "ABTestConfig",
    "QualityEvaluator",
    "PerformanceBenchmark",
    "RegressionTester",
    "TestDataGenerator",
    "TestSuite",
] 