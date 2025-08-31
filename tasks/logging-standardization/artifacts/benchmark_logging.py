#!/usr/bin/env python3
"""
Performance benchmark script for logging standardization.
Measures logging performance before/after migration to identify overhead.
"""

import json
import logging
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.logging.logger import LoggerFactory, StructlogFactory, correlation_id_ctx
except ImportError:
    # Fallback for testing - create mock implementations
    print("Warning: Could not import logging modules. Using mock implementations for testing.")

    class MockLogger:
        def info(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass

    class MockLoggerFactory:
        @classmethod
        def configure(cls, **kwargs): pass
        @classmethod
        def get_logger(cls): return MockLogger()

    class MockStructlogFactory:
        @classmethod
        def configure(cls, **kwargs): pass
        @classmethod
        def get_logger(cls, name=""): return MockLogger()

    class MockCorrelationCtx:
        @classmethod
        def set(cls, value): pass

    LoggerFactory = MockLoggerFactory
    StructlogFactory = MockStructlogFactory
    correlation_id_ctx = MockCorrelationCtx()


class LoggingBenchmark:
    """Benchmark suite for comparing logging performance."""

    def __init__(self):
        self.results = {}
        self.iterations = 10000
        self.setup_loggers()

    def setup_loggers(self):
        """Setup both standard and structured loggers for comparison."""
        # Standard logger setup
        LoggerFactory.configure(logger_name="benchmark_standard", log_level="INFO")
        self.standard_logger = LoggerFactory.get_logger()

        # Structured logger setup
        StructlogFactory.configure(log_level="INFO")
        self.structured_logger = StructlogFactory.get_logger("benchmark_structured")

        # Set correlation ID for consistent testing
        correlation_id_ctx.set("bench-12345678")

    def benchmark_function(self, func: Callable, name: str, *args, **kwargs) -> dict[str, Any]:
        """Benchmark a function and return timing results."""
        times = []

        # Warmup
        for _ in range(100):
            func(*args, **kwargs)

        # Actual benchmark
        for _ in range(self.iterations):
            start_time = time.perf_counter()
            func(*args, **kwargs)
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        # Calculate statistics
        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)

        # Calculate percentiles
        sorted_times = sorted(times)
        p50 = sorted_times[len(sorted_times) // 2]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]

        return {
            "name": name,
            "iterations": self.iterations,
            "total_time_seconds": total_time,
            "average_time_microseconds": avg_time * 1_000_000,
            "min_time_microseconds": min_time * 1_000_000,
            "max_time_microseconds": max_time * 1_000_000,
            "p50_microseconds": p50 * 1_000_000,
            "p95_microseconds": p95 * 1_000_000,
            "p99_microseconds": p99 * 1_000_000,
            "operations_per_second": self.iterations / total_time
        }

    def benchmark_standard_logging_info(self):
        """Benchmark standard logging info calls."""
        return self.benchmark_function(
            self.standard_logger.info,
            "standard_logging_info",
            "Test message with user_id=%s and action=%s",
            "user123",
            "login"
        )

    def benchmark_standard_logging_error(self):
        """Benchmark standard logging error calls."""
        return self.benchmark_function(
            self.standard_logger.error,
            "standard_logging_error",
            "Error processing user_id=%s: %s",
            "user123",
            "Database connection failed"
        )

    def benchmark_structured_logging_info(self):
        """Benchmark structured logging info calls."""
        return self.benchmark_function(
            self.structured_logger.info,
            "structured_logging_info",
            "Test message",
            user_id="user123",
            action="login"
        )

    def benchmark_structured_logging_error(self):
        """Benchmark structured logging error calls."""
        return self.benchmark_function(
            self.structured_logger.error,
            "structured_logging_error",
            "Error processing user",
            user_id="user123",
            error="Database connection failed"
        )

    def benchmark_correlation_id_overhead(self):
        """Benchmark correlation ID context overhead."""
        def with_correlation_id():
            correlation_id_ctx.set("test-correlation-id")
            self.structured_logger.info("Test message", user_id="user123")

        def without_correlation_id():
            # This will use the default correlation ID
            self.structured_logger.info("Test message", user_id="user123")

        with_corr_results = self.benchmark_function(
            with_correlation_id,
            "structured_logging_with_correlation_id"
        )

        without_corr_results = self.benchmark_function(
            without_correlation_id,
            "structured_logging_without_correlation_id"
        )

        return {
            "with_correlation_id": with_corr_results,
            "without_correlation_id": without_corr_results,
            "overhead_microseconds": (
                with_corr_results["average_time_microseconds"] -
                without_corr_results["average_time_microseconds"]
            )
        }

    def benchmark_message_formatting(self):
        """Benchmark different message formatting approaches."""
        # Old style string formatting
        def old_string_format():
            self.standard_logger.info("User %s performed %s", "user123", "login")

        # f-string formatting
        def f_string_format():
            user_id = "user123"
            action = "login"
            self.standard_logger.info(f"User {user_id} performed {action}")

        # Structured logging
        def structured_format():
            self.structured_logger.info("User performed action", user_id="user123", action="login")

        return {
            "old_string_format": self.benchmark_function(old_string_format, "old_string_format"),
            "f_string_format": self.benchmark_function(f_string_format, "f_string_format"),
            "structured_format": self.benchmark_function(structured_format, "structured_format")
        }

    def run_all_benchmarks(self) -> dict[str, Any]:
        """Run all benchmarks and return comprehensive results."""
        print("Running logging performance benchmarks...")

        results = {
            "benchmark_metadata": {
                "iterations_per_test": self.iterations,
                "timestamp": time.time(),
                "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
            },
            "standard_logging": {
                "info": self.benchmark_standard_logging_info(),
                "error": self.benchmark_standard_logging_error()
            },
            "structured_logging": {
                "info": self.benchmark_structured_logging_info(),
                "error": self.benchmark_structured_logging_error()
            },
            "correlation_id_overhead": self.benchmark_correlation_id_overhead(),
            "message_formatting": self.benchmark_message_formatting()
        }

        # Calculate performance comparisons
        results["performance_comparison"] = self.calculate_performance_comparison(results)

        return results

    def calculate_performance_comparison(self, results: dict[str, Any]) -> dict[str, Any]:
        """Calculate performance comparisons between logging approaches."""
        standard_info_ops = results["standard_logging"]["info"]["operations_per_second"]
        structured_info_ops = results["structured_logging"]["info"]["operations_per_second"]

        standard_error_ops = results["standard_logging"]["error"]["operations_per_second"]
        structured_error_ops = results["structured_logging"]["error"]["operations_per_second"]

        return {
            "info_logging": {
                "standard_ops_per_sec": standard_info_ops,
                "structured_ops_per_sec": structured_info_ops,
                "performance_ratio": structured_info_ops / standard_info_ops,
                "performance_impact_percent": ((standard_info_ops - structured_info_ops) / standard_info_ops) * 100
            },
            "error_logging": {
                "standard_ops_per_sec": standard_error_ops,
                "structured_ops_per_sec": structured_error_ops,
                "performance_ratio": structured_error_ops / standard_error_ops,
                "performance_impact_percent": ((standard_error_ops - structured_error_ops) / standard_error_ops) * 100
            },
            "overall_assessment": {
                "acceptable_impact": abs(((standard_info_ops - structured_info_ops) / standard_info_ops) * 100) < 5.0,
                "recommendation": "PROCEED" if abs(((standard_info_ops - structured_info_ops) / standard_info_ops) * 100) < 5.0 else "INVESTIGATE"
            }
        }

    def save_results(self, results: dict[str, Any], filename: str = "benchmark_results.json"):
        """Save benchmark results to file."""
        output_path = Path("tasks/logging-standardization/artifacts") / filename
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Benchmark results saved to: {output_path}")

    def print_summary(self, results: dict[str, Any]):
        """Print a human-readable summary of benchmark results."""
        print("\n=== Logging Performance Benchmark Summary ===")

        comparison = results["performance_comparison"]

        print(f"\nInfo Logging Performance:")
        print(f"  Standard:   {comparison['info_logging']['standard_ops_per_sec']:,.0f} ops/sec")
        print(f"  Structured: {comparison['info_logging']['structured_ops_per_sec']:,.0f} ops/sec")
        print(f"  Impact:     {comparison['info_logging']['performance_impact_percent']:+.2f}%")

        print(f"\nError Logging Performance:")
        print(f"  Standard:   {comparison['error_logging']['standard_ops_per_sec']:,.0f} ops/sec")
        print(f"  Structured: {comparison['error_logging']['structured_ops_per_sec']:,.0f} ops/sec")
        print(f"  Impact:     {comparison['error_logging']['performance_impact_percent']:+.2f}%")

        correlation_overhead = results["correlation_id_overhead"]["overhead_microseconds"]
        print(f"\nCorrelation ID Overhead: {correlation_overhead:.2f} microseconds")

        assessment = comparison["overall_assessment"]
        print(f"\nOverall Assessment: {assessment['recommendation']}")
        print(f"Acceptable Impact: {'✅ YES' if assessment['acceptable_impact'] else '❌ NO'}")

        if not assessment['acceptable_impact']:
            print("\n⚠️  Performance impact exceeds 5% threshold. Consider optimization.")


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark logging performance")
    parser.add_argument("--baseline", action="store_true", help="Run baseline measurements")
    parser.add_argument("--compare", action="store_true", help="Compare with baseline")
    parser.add_argument("--iterations", type=int, default=10000, help="Number of iterations per test")
    parser.add_argument("--output", type=str, help="Output filename for results")

    args = parser.parse_args()

    benchmark = LoggingBenchmark()
    benchmark.iterations = args.iterations

    if args.baseline:
        print("Running baseline performance measurements...")
        results = benchmark.run_all_benchmarks()
        filename = args.output or "baseline_performance.json"
        benchmark.save_results(results, filename)
        benchmark.print_summary(results)

    elif args.compare:
        print("Running comparison measurements...")
        results = benchmark.run_all_benchmarks()
        filename = args.output or "comparison_performance.json"
        benchmark.save_results(results, filename)
        benchmark.print_summary(results)

        # Load baseline for comparison if it exists
        baseline_path = Path("tasks/logging-standardization/artifacts/baseline_performance.json")
        if baseline_path.exists():
            with open(baseline_path) as f:
                baseline = json.load(f)
            print("\n=== Comparison with Baseline ===")
            baseline_ops = baseline["performance_comparison"]["info_logging"]["standard_ops_per_sec"]
            current_ops = results["performance_comparison"]["info_logging"]["structured_ops_per_sec"]
            change_percent = ((current_ops - baseline_ops) / baseline_ops) * 100
            print(f"Performance change: {change_percent:+.2f}%")

    else:
        # Default: run all benchmarks
        results = benchmark.run_all_benchmarks()
        filename = args.output or "benchmark_results.json"
        benchmark.save_results(results, filename)
        benchmark.print_summary(results)


if __name__ == "__main__":
    main()
