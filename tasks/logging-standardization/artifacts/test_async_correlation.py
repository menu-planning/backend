#!/usr/bin/env python3
"""
Async correlation ID test script for logging standardization.
Validates correlation ID preservation across async boundaries and middleware.
"""

import asyncio
import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.logging.logger import (
        StructlogFactory,
        correlation_id_ctx,
        generate_correlation_id,
        set_correlation_id,
    )
    from src.contexts.shared_kernel.middleware.core.base_middleware import BaseMiddleware
    from src.contexts.shared_kernel.middleware.logging.structured_logger import StructuredLoggingMiddleware
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

        def debug(self, message, **kwargs):
            self.logged_messages.append({"level": "debug", "message": message, "kwargs": kwargs})

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

    StructlogFactory = MockStructlogFactory
    correlation_id_ctx = MockCorrelationCtx()
    set_correlation_id = mock_set_correlation_id
    generate_correlation_id = mock_generate_correlation_id


class AsyncCorrelationTester:
    """Test suite for async correlation ID functionality."""

    def __init__(self):
        self.test_results = {}
        self.setup_loggers()

    def setup_loggers(self):
        """Setup loggers for testing."""
        if IMPORTS_AVAILABLE:
            StructlogFactory.configure(log_level="INFO")
        self.logger = StructlogFactory.get_logger("async_correlation_test")

    async def test_simple_async_operation(self) -> dict[str, Any]:
        """Test correlation ID preservation in simple async operation."""
        test_id = "async-simple-12345"
        
        try:
            # Set correlation ID
            set_correlation_id(test_id)
            initial_id = correlation_id_ctx.get()

            async def async_operation():
                """Simple async operation that should preserve correlation ID."""
                await asyncio.sleep(0.01)  # Simulate async work
                return correlation_id_ctx.get()

            # Execute async operation
            result_id = await async_operation()

            success = initial_id == result_id == test_id

            return {
                "test_name": "simple_async_operation",
                "success": success,
                "test_id": test_id,
                "initial_id": initial_id,
                "result_id": result_id,
                "preserved": success,
                "error": None
            }
        except Exception as e:
            return {
                "test_name": "simple_async_operation",
                "success": False,
                "test_id": test_id,
                "initial_id": None,
                "result_id": None,
                "preserved": False,
                "error": str(e)
            }

    async def test_nested_async_operations(self) -> dict[str, Any]:
        """Test correlation ID preservation across nested async operations."""
        test_id = "async-nested-67890"
        
        try:
            # Set correlation ID
            set_correlation_id(test_id)
            
            async def outer_operation():
                """Outer async operation."""
                outer_id = correlation_id_ctx.get()
                
                async def inner_operation():
                    """Inner async operation."""
                    await asyncio.sleep(0.01)
                    return correlation_id_ctx.get()
                
                inner_id = await inner_operation()
                return outer_id, inner_id

            # Execute nested operations
            outer_id, inner_id = await outer_operation()

            success = outer_id == inner_id == test_id

            return {
                "test_name": "nested_async_operations",
                "success": success,
                "test_id": test_id,
                "outer_id": outer_id,
                "inner_id": inner_id,
                "all_preserved": success,
                "error": None
            }
        except Exception as e:
            return {
                "test_name": "nested_async_operations",
                "success": False,
                "test_id": test_id,
                "outer_id": None,
                "inner_id": None,
                "all_preserved": False,
                "error": str(e)
            }

    async def test_concurrent_async_operations(self) -> dict[str, Any]:
        """Test correlation ID preservation in concurrent async operations."""
        base_id = "async-concurrent"
        
        try:
            async def concurrent_operation(operation_id: int):
                """Concurrent operation with its own correlation ID."""
                test_id = f"{base_id}-{operation_id}"
                set_correlation_id(test_id)
                
                # Simulate async work
                await asyncio.sleep(0.01 * operation_id)  # Different delays
                
                return {
                    "operation_id": operation_id,
                    "expected_id": test_id,
                    "actual_id": correlation_id_ctx.get(),
                    "preserved": correlation_id_ctx.get() == test_id
                }

            # Run multiple concurrent operations
            tasks = [concurrent_operation(i) for i in range(1, 6)]
            results = await asyncio.gather(*tasks)

            # Analyze results
            all_preserved = all(result["preserved"] for result in results)

            return {
                "test_name": "concurrent_async_operations",
                "success": all_preserved,
                "base_id": base_id,
                "operation_results": results,
                "all_preserved": all_preserved,
                "operations_count": len(results),
                "error": None
            }
        except Exception as e:
            return {
                "test_name": "concurrent_async_operations",
                "success": False,
                "base_id": base_id,
                "operation_results": [],
                "all_preserved": False,
                "operations_count": 0,
                "error": str(e)
            }

    async def test_async_context_manager(self) -> dict[str, Any]:
        """Test correlation ID preservation with async context managers."""
        test_id = "async-context-abcdef"
        
        try:
            # Set correlation ID
            set_correlation_id(test_id)
            
            class AsyncContextManager:
                async def __aenter__(self):
                    self.entry_id = correlation_id_ctx.get()
                    return self
                
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    self.exit_id = correlation_id_ctx.get()

            # Use async context manager
            async with AsyncContextManager() as cm:
                inside_id = correlation_id_ctx.get()
                await asyncio.sleep(0.01)  # Simulate work
                after_work_id = correlation_id_ctx.get()

            success = all(
                id_val == test_id 
                for id_val in [cm.entry_id, inside_id, after_work_id, cm.exit_id]
            )

            return {
                "test_name": "async_context_manager",
                "success": success,
                "test_id": test_id,
                "entry_id": cm.entry_id,
                "inside_id": inside_id,
                "after_work_id": after_work_id,
                "exit_id": cm.exit_id,
                "all_preserved": success,
                "error": None
            }
        except Exception as e:
            return {
                "test_name": "async_context_manager",
                "success": False,
                "test_id": test_id,
                "entry_id": None,
                "inside_id": None,
                "after_work_id": None,
                "exit_id": None,
                "all_preserved": False,
                "error": str(e)
            }

    async def test_middleware_correlation_preservation(self) -> dict[str, Any]:
        """Test correlation ID preservation through middleware chain."""
        test_id = "middleware-test-123456"
        
        try:
            # Mock middleware for testing
            class TestMiddleware(BaseMiddleware if IMPORTS_AVAILABLE else object):
                def __init__(self, name: str):
                    if IMPORTS_AVAILABLE:
                        super().__init__(name=name)
                    else:
                        self.name = name
                    self.correlation_ids = []

                async def __call__(self, handler, *args, **kwargs):
                    # Capture correlation ID before handler
                    before_id = correlation_id_ctx.get()
                    self.correlation_ids.append(("before", before_id))
                    
                    # Call handler
                    result = await handler(*args, **kwargs)
                    
                    # Capture correlation ID after handler
                    after_id = correlation_id_ctx.get()
                    self.correlation_ids.append(("after", after_id))
                    
                    return result

            # Set correlation ID
            set_correlation_id(test_id)
            
            # Create test middleware
            middleware1 = TestMiddleware("middleware1")
            middleware2 = TestMiddleware("middleware2")
            
            # Mock handler
            async def test_handler(*args, **kwargs):
                handler_id = correlation_id_ctx.get()
                await asyncio.sleep(0.01)  # Simulate work
                return {"handler_id": handler_id, "status": "success"}

            # Execute middleware chain manually
            result = await middleware1(
                lambda *a, **k: middleware2(test_handler, *a, **k),
                {"test": "data"}
            )

            # Collect all correlation IDs
            all_ids = [
                test_id,  # Initial
                *[id_val for _, id_val in middleware1.correlation_ids],
                *[id_val for _, id_val in middleware2.correlation_ids],
                result["handler_id"]  # Handler
            ]

            success = all(id_val == test_id for id_val in all_ids)

            return {
                "test_name": "middleware_correlation_preservation",
                "success": success,
                "test_id": test_id,
                "middleware1_ids": middleware1.correlation_ids,
                "middleware2_ids": middleware2.correlation_ids,
                "handler_id": result["handler_id"],
                "all_ids_preserved": success,
                "total_checks": len(all_ids),
                "error": None
            }
        except Exception as e:
            return {
                "test_name": "middleware_correlation_preservation",
                "success": False,
                "test_id": test_id,
                "middleware1_ids": [],
                "middleware2_ids": [],
                "handler_id": None,
                "all_ids_preserved": False,
                "total_checks": 0,
                "error": str(e)
            }

    async def test_async_generator_correlation(self) -> dict[str, Any]:
        """Test correlation ID preservation with async generators."""
        test_id = "async-gen-789abc"
        
        try:
            # Set correlation ID
            set_correlation_id(test_id)
            
            async def async_generator():
                """Async generator that should preserve correlation ID."""
                for i in range(3):
                    current_id = correlation_id_ctx.get()
                    await asyncio.sleep(0.01)  # Simulate async work
                    yield {"item": i, "correlation_id": current_id}

            # Consume async generator
            items = []
            async for item in async_generator():
                items.append(item)

            # Check all correlation IDs
            all_preserved = all(
                item["correlation_id"] == test_id 
                for item in items
            )

            return {
                "test_name": "async_generator_correlation",
                "success": all_preserved,
                "test_id": test_id,
                "generated_items": items,
                "items_count": len(items),
                "all_preserved": all_preserved,
                "error": None
            }
        except Exception as e:
            return {
                "test_name": "async_generator_correlation",
                "success": False,
                "test_id": test_id,
                "generated_items": [],
                "items_count": 0,
                "all_preserved": False,
                "error": str(e)
            }

    async def run_all_tests(self) -> dict[str, Any]:
        """Run all async correlation ID tests."""
        print("Running async correlation ID tests...")

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
            self.test_simple_async_operation,
            self.test_nested_async_operations,
            self.test_concurrent_async_operations,
            self.test_async_context_manager,
            self.test_middleware_correlation_preservation,
            self.test_async_generator_correlation
        ]

        for test_method in test_methods:
            try:
                result = await test_method()
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

    def save_results(self, results: dict[str, Any], filename: str = "async_correlation_test_results.json"):
        """Save test results to file."""
        output_path = Path("tasks/logging-standardization/artifacts") / filename
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Async correlation ID test results saved to: {output_path}")

    def print_summary(self, results: dict[str, Any]):
        """Print a human-readable summary of test results."""
        print("\n=== Async Correlation ID Test Summary ===")

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


async def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Test async correlation ID functionality")
    parser.add_argument("--output", type=str, help="Output filename for results")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    tester = AsyncCorrelationTester()
    results = await tester.run_all_tests()

    filename = args.output or "async_correlation_test_results.json"
    tester.save_results(results, filename)
    tester.print_summary(results)

    if args.verbose:
        print("\n=== Detailed Results ===")
        print(json.dumps(results, indent=2))

    # Exit with appropriate code
    sys.exit(0 if results["summary"]["overall_success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
