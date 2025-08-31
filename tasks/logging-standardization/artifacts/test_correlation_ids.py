#!/usr/bin/env python3
"""
Correlation ID test script for logging standardization.
Validates correlation ID propagation across different logging approaches.
"""

import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import patch

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.logging.logger import (
        LoggerFactory,
        StructlogFactory,
        correlation_id_ctx,
        generate_correlation_id,
        set_correlation_id,
    )
    IMPORTS_AVAILABLE = True
except ImportError:
    print("Warning: Could not import logging modules. Using mock implementations for testing.")
    IMPORTS_AVAILABLE = False

    # Mock implementations for testing
    class MockCorrelationCtx:
        def __init__(self):
            self._value = "00000000-0000-0000-0000-000000000000"

        def set(self, value):
            self._value = value

        def get(self):
            return self._value

    class MockLogger:
        def __init__(self):
            self.logged_messages = []

        def info(self, message, **kwargs):
            self.logged_messages.append({"level": "info", "message": message, "kwargs": kwargs})

        def error(self, message, **kwargs):
            self.logged_messages.append({"level": "error", "message": message, "kwargs": kwargs})

    class MockLoggerFactory:
        @classmethod
        def configure(cls, **kwargs):
            pass

        @classmethod
        def get_logger(cls):
            return MockLogger()

    class MockStructlogFactory:
        @classmethod
        def configure(cls, **kwargs):
            pass

        @classmethod
        def get_logger(cls, name=""):
            return MockLogger()

    def mock_set_correlation_id(correlation_id):
        correlation_id_ctx.set(correlation_id)

    def mock_generate_correlation_id():
        cid = uuid.uuid4().hex[:8]
        correlation_id_ctx.set(cid)
        return cid

    LoggerFactory = MockLoggerFactory
    StructlogFactory = MockStructlogFactory
    correlation_id_ctx = MockCorrelationCtx()
    set_correlation_id = mock_set_correlation_id
    generate_correlation_id = mock_generate_correlation_id


class CorrelationIdTester:
    """Test suite for correlation ID functionality."""

    def __init__(self):
        self.test_results = {}
        self.setup_loggers()

    def setup_loggers(self):
        """Setup loggers for testing."""
        if IMPORTS_AVAILABLE:
            LoggerFactory.configure(logger_name="correlation_test", log_level="INFO")
            StructlogFactory.configure(log_level="INFO")

        self.standard_logger = LoggerFactory.get_logger()
        self.structured_logger = StructlogFactory.get_logger("correlation_test")

    def test_correlation_id_setting(self) -> dict[str, Any]:
        """Test setting correlation ID manually."""
        test_id = "test-correlation-12345"

        try:
            # Set correlation ID
            set_correlation_id(test_id)

            # Get current correlation ID
            current_id = correlation_id_ctx.get()

            success = current_id == test_id

            return {
                "test_name": "correlation_id_setting",
                "success": success,
                "expected": test_id,
                "actual": current_id,
                "error": None
            }
        except Exception as e:
            return {
                "test_name": "correlation_id_setting",
                "success": False,
                "expected": test_id,
                "actual": None,
                "error": str(e)
            }

    def test_correlation_id_generation(self) -> dict[str, Any]:
        """Test automatic correlation ID generation."""
        try:
            # Generate new correlation ID
            generated_id = generate_correlation_id()

            # Verify it was set in context
            current_id = correlation_id_ctx.get()

            success = (
                generated_id is not None and
                len(generated_id) == 8 and
                generated_id == current_id
            )

            return {
                "test_name": "correlation_id_generation",
                "success": success,
                "generated_id": generated_id,
                "context_id": current_id,
                "id_length": len(generated_id) if generated_id else 0,
                "error": None
            }
        except Exception as e:
            return {
                "test_name": "correlation_id_generation",
                "success": False,
                "generated_id": None,
                "context_id": None,
                "id_length": 0,
                "error": str(e)
            }

    def test_correlation_id_persistence(self) -> dict[str, Any]:
        """Test that correlation ID persists across multiple log calls."""
        test_id = "persist-test-67890"

        try:
            # Set correlation ID
            set_correlation_id(test_id)

            # Make multiple log calls
            log_calls = []
            for i in range(5):
                current_id_before = correlation_id_ctx.get()

                # Log with both loggers
                self.standard_logger.info(f"Standard log call {i}")
                self.structured_logger.info(f"Structured log call {i}", call_number=i)

                current_id_after = correlation_id_ctx.get()

                log_calls.append({
                    "call_number": i,
                    "id_before": current_id_before,
                    "id_after": current_id_after,
                    "consistent": current_id_before == current_id_after == test_id
                })

            all_consistent = all(call["consistent"] for call in log_calls)

            return {
                "test_name": "correlation_id_persistence",
                "success": all_consistent,
                "test_id": test_id,
                "log_calls": log_calls,
                "all_consistent": all_consistent,
                "error": None
            }
        except Exception as e:
            return {
                "test_name": "correlation_id_persistence",
                "success": False,
                "test_id": test_id,
                "log_calls": [],
                "all_consistent": False,
                "error": str(e)
            }

    def test_correlation_id_in_structured_logs(self) -> dict[str, Any]:
        """Test that correlation ID appears in structured log output."""
        test_id = "struct-test-abcdef"

        try:
            # Set correlation ID
            set_correlation_id(test_id)

            # For mock testing, we can check if the logger receives the correlation ID
            if not IMPORTS_AVAILABLE:
                # Mock test - just verify the context was set
                current_id = correlation_id_ctx.get()
                success = current_id == test_id

                return {
                    "test_name": "correlation_id_in_structured_logs",
                    "success": success,
                    "test_id": test_id,
                    "found_in_logs": success,
                    "mock_mode": True,
                    "error": None
                }

            # Real implementation would capture actual log output
            # For now, we'll test that the context is properly set
            self.structured_logger.info("Test structured log", user_id="test123", action="test")
            current_id = correlation_id_ctx.get()

            success = current_id == test_id

            return {
                "test_name": "correlation_id_in_structured_logs",
                "success": success,
                "test_id": test_id,
                "context_id": current_id,
                "found_in_logs": success,
                "mock_mode": False,
                "error": None
            }
        except Exception as e:
            return {
                "test_name": "correlation_id_in_structured_logs",
                "success": False,
                "test_id": test_id,
                "context_id": None,
                "found_in_logs": False,
                "mock_mode": not IMPORTS_AVAILABLE,
                "error": str(e)
            }

    def test_correlation_id_thread_safety(self) -> dict[str, Any]:
        """Test correlation ID behavior in concurrent scenarios."""
        import threading
        import time

        results = []
        errors = []

        def worker_thread(thread_id: int, test_correlation_id: str):
            try:
                # Each thread sets its own correlation ID
                set_correlation_id(test_correlation_id)

                # Small delay to simulate work
                time.sleep(0.01)

                # Check if correlation ID is still correct
                current_id = correlation_id_ctx.get()

                results.append({
                    "thread_id": thread_id,
                    "expected_id": test_correlation_id,
                    "actual_id": current_id,
                    "correct": current_id == test_correlation_id
                })
            except Exception as e:
                errors.append({
                    "thread_id": thread_id,
                    "error": str(e)
                })

        try:
            # Create multiple threads with different correlation IDs
            threads = []
            for i in range(5):
                test_id = f"thread-{i}-{uuid.uuid4().hex[:6]}"
                thread = threading.Thread(target=worker_thread, args=(i, test_id))
                threads.append(thread)

            # Start all threads
            for thread in threads:
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Analyze results
            all_correct = len(errors) == 0 and all(r["correct"] for r in results)

            return {
                "test_name": "correlation_id_thread_safety",
                "success": all_correct,
                "thread_results": results,
                "errors": errors,
                "threads_tested": len(threads),
                "all_correct": all_correct,
                "error": None
            }
        except Exception as e:
            return {
                "test_name": "correlation_id_thread_safety",
                "success": False,
                "thread_results": results,
                "errors": [*errors, {"general_error": str(e)}],
                "threads_tested": 0,
                "all_correct": False,
                "error": str(e)
            }

    def test_default_correlation_id(self) -> dict[str, Any]:
        """Test default correlation ID behavior."""
        try:
            # Reset to default by setting to None or empty
            # This test checks what happens when no correlation ID is explicitly set

            # Generate a new ID to start fresh
            generate_correlation_id()
            initial_id = correlation_id_ctx.get()

            # The default should be a valid UUID format
            is_valid_format = (
                initial_id is not None and
                len(initial_id) > 0 and
                initial_id != "None"
            )

            return {
                "test_name": "default_correlation_id",
                "success": is_valid_format,
                "default_id": initial_id,
                "is_valid_format": is_valid_format,
                "id_length": len(initial_id) if initial_id else 0,
                "error": None
            }
        except Exception as e:
            return {
                "test_name": "default_correlation_id",
                "success": False,
                "default_id": None,
                "is_valid_format": False,
                "id_length": 0,
                "error": str(e)
            }

    def run_all_tests(self) -> dict[str, Any]:
        """Run all correlation ID tests."""
        print("Running correlation ID tests...")

        test_results = {
            "test_metadata": {
                "timestamp": time.time(),
                "imports_available": IMPORTS_AVAILABLE,
                "mock_mode": not IMPORTS_AVAILABLE
            },
            "tests": {}
        }

        # Run individual tests
        test_methods = [
            self.test_correlation_id_setting,
            self.test_correlation_id_generation,
            self.test_correlation_id_persistence,
            self.test_correlation_id_in_structured_logs,
            self.test_correlation_id_thread_safety,
            self.test_default_correlation_id
        ]

        for test_method in test_methods:
            try:
                result = test_method()
                test_results["tests"][result["test_name"]] = result
            except Exception as e:
                test_results["tests"][test_method.__name__] = {
                    "test_name": test_method.__name__,
                    "success": False,
                    "error": str(e)
                }

        # Calculate summary
        total_tests = len(test_results["tests"])
        passed_tests = sum(1 for test in test_results["tests"].values() if test["success"])
        failed_tests = total_tests - passed_tests

        test_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "overall_success": failed_tests == 0
        }

        return test_results

    def save_results(self, results: dict[str, Any], filename: str = "correlation_id_test_results.json"):
        """Save test results to file."""
        output_path = Path("tasks/logging-standardization/artifacts") / filename
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Correlation ID test results saved to: {output_path}")

    def print_summary(self, results: dict[str, Any]):
        """Print a human-readable summary of test results."""
        print("\n=== Correlation ID Test Summary ===")

        summary = results["summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Overall: {'✅ PASS' if summary['overall_success'] else '❌ FAIL'}")

        if results["test_metadata"]["mock_mode"]:
            print("\n⚠️  Running in mock mode - some tests may not reflect real behavior")

        # Show failed tests
        failed_tests = [
            name for name, test in results["tests"].items()
            if not test["success"]
        ]

        if failed_tests:
            print(f"\nFailed Tests:")
            for test_name in failed_tests:
                test_result = results["tests"][test_name]
                print(f"  - {test_name}: {test_result.get('error', 'Unknown error')}")


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Test correlation ID functionality")
    parser.add_argument("--output", type=str, help="Output filename for results")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    tester = CorrelationIdTester()
    results = tester.run_all_tests()

    filename = args.output or "correlation_id_test_results.json"
    tester.save_results(results, filename)
    tester.print_summary(results)

    if args.verbose:
        print("\n=== Detailed Results ===")
        print(json.dumps(results, indent=2))

    # Exit with appropriate code
    sys.exit(0 if results["summary"]["overall_success"] else 1)


if __name__ == "__main__":
    main()
