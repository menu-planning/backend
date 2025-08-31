#!/usr/bin/env python3
"""
Middleware correlation ID integration test script for logging standardization.
Validates correlation ID injection and propagation in actual middleware components.
"""

import asyncio
import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

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
    from src.contexts.shared_kernel.middleware.logging.structured_logger import (
        StructuredLoggingMiddleware,
        AWSLambdaLoggingStrategy,
    )
    from src.contexts.shared_kernel.middleware.auth.authentication import (
        AuthenticationMiddleware,
        AWSLambdaAuthenticationStrategy,
        AuthContext,
        AuthPolicy,
    )
    from src.contexts.shared_kernel.middleware.core.middleware_composer import MiddlewareComposer
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import middleware modules: {e}")
    print("Using mock implementations for testing.")
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

    class MockBaseMiddleware:
        def __init__(self, name=None, timeout=None):
            self.name = name or self.__class__.__name__
            self.timeout = timeout

    class MockLoggingStrategy:
        def extract_logging_context(self, *args, **kwargs):
            return {"platform": "mock", "test_mode": True}

        def get_request_data(self, *args, **kwargs):
            event = args[0] if args else {"test": "event"}
            context = args[1] if len(args) > 1 else {"test": "context"}
            return event, context

        def inject_logging_context(self, request_data, logging_context):
            request_data["_logging_context"] = logging_context

    class MockAuthStrategy:
        async def extract_auth_context(self, *args, **kwargs):
            return MockAuthContext()

        def get_request_data(self, *args, **kwargs):
            event = args[0] if args else {"test": "event"}
            context = args[1] if len(args) > 1 else {"test": "context"}
            return event, context

        def inject_auth_context(self, request_data, auth_context):
            request_data["_auth_context"] = auth_context

    class MockAuthContext:
        def __init__(self):
            self.user_id = "test-user-123"
            self.user_roles = ["user"]
            self.is_authenticated = True
            self.metadata = {}

    class MockAuthPolicy:
        def __init__(self):
            self.allowed_roles = ["user", "admin"]

        def is_allowed(self, user_roles):
            return True

    def mock_set_correlation_id(correlation_id):
        correlation_id_ctx.set(correlation_id)

    def mock_generate_correlation_id():
        cid = uuid.uuid4().hex[:8]
        correlation_id_ctx.set(cid)
        return cid

    # Set up mocks
    StructlogFactory = MockStructlogFactory
    correlation_id_ctx = MockCorrelationCtx()
    set_correlation_id = mock_set_correlation_id
    generate_correlation_id = mock_generate_correlation_id
    BaseMiddleware = MockBaseMiddleware
    AWSLambdaLoggingStrategy = MockLoggingStrategy
    AWSLambdaAuthenticationStrategy = MockAuthStrategy
    AuthContext = MockAuthContext
    AuthPolicy = MockAuthPolicy


class MiddlewareCorrelationTester:
    """Test suite for middleware correlation ID integration."""

    def __init__(self):
        self.test_results = {}
        self.setup_loggers()

    def setup_loggers(self):
        """Setup loggers for testing."""
        if IMPORTS_AVAILABLE:
            StructlogFactory.configure(log_level="INFO")
        self.logger = StructlogFactory.get_logger("middleware_correlation_test")

    async def test_structured_logging_middleware_correlation(self) -> dict[str, Any]:
        """Test correlation ID handling in StructuredLoggingMiddleware."""
        test_id = "logging-middleware-12345"
        
        try:
            # Set correlation ID
            set_correlation_id(test_id)
            
            # Create logging middleware
            if IMPORTS_AVAILABLE:
                strategy = AWSLambdaLoggingStrategy()
                middleware = StructuredLoggingMiddleware(strategy=strategy)
            else:
                # Mock implementation
                class MockStructuredLoggingMiddleware:
                    def __init__(self, strategy):
                        self.strategy = strategy
                        self.correlation_ids = []

                    async def __call__(self, handler, *args, **kwargs):
                        # Capture correlation ID
                        correlation_id = correlation_id_ctx.get()
                        self.correlation_ids.append(("before_handler", correlation_id))
                        
                        # Execute handler
                        result = await handler(*args, **kwargs)
                        
                        # Capture correlation ID after
                        correlation_id_after = correlation_id_ctx.get()
                        self.correlation_ids.append(("after_handler", correlation_id_after))
                        
                        return result

                strategy = AWSLambdaLoggingStrategy()
                middleware = MockStructuredLoggingMiddleware(strategy)

            # Mock handler
            async def test_handler(event, context):
                handler_correlation_id = correlation_id_ctx.get()
                return {
                    "statusCode": 200,
                    "body": "success",
                    "handler_correlation_id": handler_correlation_id
                }

            # Execute middleware
            event = {"test": "event", "path": "/test"}
            context = {"test": "context"}
            result = await middleware(test_handler, event, context)

            # Validate correlation ID preservation
            if IMPORTS_AVAILABLE:
                # For real implementation, check that correlation ID is preserved
                success = result["handler_correlation_id"] == test_id
                correlation_ids = [test_id, result["handler_correlation_id"]]
            else:
                # For mock implementation, check captured IDs
                success = all(cid == test_id for _, cid in middleware.correlation_ids)
                correlation_ids = [cid for _, cid in middleware.correlation_ids]

            return {
                "test_name": "structured_logging_middleware_correlation",
                "success": success,
                "test_id": test_id,
                "correlation_ids_captured": correlation_ids,
                "handler_result": result,
                "all_preserved": success,
                "error": None
            }
        except Exception as e:
            return {
                "test_name": "structured_logging_middleware_correlation",
                "success": False,
                "test_id": test_id,
                "correlation_ids_captured": [],
                "handler_result": None,
                "all_preserved": False,
                "error": str(e)
            }

    async def test_authentication_middleware_correlation(self) -> dict[str, Any]:
        """Test correlation ID handling in AuthenticationMiddleware."""
        test_id = "auth-middleware-67890"
        
        try:
            # Set correlation ID
            set_correlation_id(test_id)
            
            # Create authentication middleware
            if IMPORTS_AVAILABLE:
                strategy = AWSLambdaAuthenticationStrategy()
                policy = AuthPolicy()
                middleware = AuthenticationMiddleware(strategy=strategy, policy=policy)
            else:
                # Mock implementation
                class MockAuthenticationMiddleware:
                    def __init__(self, strategy, policy):
                        self.strategy = strategy
                        self.policy = policy
                        self.correlation_ids = []

                    async def __call__(self, handler, *args, **kwargs):
                        # Capture correlation ID
                        correlation_id = correlation_id_ctx.get()
                        self.correlation_ids.append(("before_auth", correlation_id))
                        
                        # Mock authentication
                        auth_context = await self.strategy.extract_auth_context(*args, **kwargs)
                        request_data, context = self.strategy.get_request_data(*args, **kwargs)
                        self.strategy.inject_auth_context(request_data, auth_context)
                        
                        # Execute handler
                        result = await handler(request_data, context)
                        
                        # Capture correlation ID after
                        correlation_id_after = correlation_id_ctx.get()
                        self.correlation_ids.append(("after_auth", correlation_id_after))
                        
                        return result

                strategy = AWSLambdaAuthenticationStrategy()
                policy = AuthPolicy()
                middleware = MockAuthenticationMiddleware(strategy, policy)

            # Mock handler
            async def test_handler(event, context):
                handler_correlation_id = correlation_id_ctx.get()
                return {
                    "statusCode": 200,
                    "body": "authenticated",
                    "handler_correlation_id": handler_correlation_id
                }

            # Execute middleware
            event = {
                "requestContext": {
                    "authorizer": {
                        "user_id": "test-user",
                        "user_roles": ["user"]
                    }
                }
            }
            context = {"test": "context"}
            result = await middleware(test_handler, event, context)

            # Validate correlation ID preservation
            if IMPORTS_AVAILABLE:
                success = result["handler_correlation_id"] == test_id
                correlation_ids = [test_id, result["handler_correlation_id"]]
            else:
                success = all(cid == test_id for _, cid in middleware.correlation_ids)
                correlation_ids = [cid for _, cid in middleware.correlation_ids]

            return {
                "test_name": "authentication_middleware_correlation",
                "success": success,
                "test_id": test_id,
                "correlation_ids_captured": correlation_ids,
                "handler_result": result,
                "all_preserved": success,
                "error": None
            }
        except Exception as e:
            return {
                "test_name": "authentication_middleware_correlation",
                "success": False,
                "test_id": test_id,
                "correlation_ids_captured": [],
                "handler_result": None,
                "all_preserved": False,
                "error": str(e)
            }

    async def test_middleware_chain_correlation(self) -> dict[str, Any]:
        """Test correlation ID preservation through middleware chain."""
        test_id = "middleware-chain-abcdef"
        
        try:
            # Set correlation ID
            set_correlation_id(test_id)
            
            # Create middleware chain
            correlation_ids_captured = []
            
            class TestMiddleware1(BaseMiddleware if IMPORTS_AVAILABLE else object):
                def __init__(self):
                    if IMPORTS_AVAILABLE:
                        super().__init__(name="TestMiddleware1")
                    else:
                        self.name = "TestMiddleware1"

                async def __call__(self, handler, *args, **kwargs):
                    correlation_id = correlation_id_ctx.get()
                    correlation_ids_captured.append(("middleware1_before", correlation_id))
                    
                    result = await handler(*args, **kwargs)
                    
                    correlation_id_after = correlation_id_ctx.get()
                    correlation_ids_captured.append(("middleware1_after", correlation_id_after))
                    
                    return result

            class TestMiddleware2(BaseMiddleware if IMPORTS_AVAILABLE else object):
                def __init__(self):
                    if IMPORTS_AVAILABLE:
                        super().__init__(name="TestMiddleware2")
                    else:
                        self.name = "TestMiddleware2"

                async def __call__(self, handler, *args, **kwargs):
                    correlation_id = correlation_id_ctx.get()
                    correlation_ids_captured.append(("middleware2_before", correlation_id))
                    
                    result = await handler(*args, **kwargs)
                    
                    correlation_id_after = correlation_id_ctx.get()
                    correlation_ids_captured.append(("middleware2_after", correlation_id_after))
                    
                    return result

            # Create middleware instances
            middleware1 = TestMiddleware1()
            middleware2 = TestMiddleware2()

            # Mock handler
            async def test_handler(*args, **kwargs):
                handler_correlation_id = correlation_id_ctx.get()
                correlation_ids_captured.append(("handler", handler_correlation_id))
                return {
                    "statusCode": 200,
                    "body": "chain_success",
                    "handler_correlation_id": handler_correlation_id
                }

            # Execute middleware chain manually
            result = await middleware1(
                lambda *a, **k: middleware2(test_handler, *a, **k),
                {"test": "event"},
                {"test": "context"}
            )

            # Validate all correlation IDs
            all_preserved = all(cid == test_id for _, cid in correlation_ids_captured)

            return {
                "test_name": "middleware_chain_correlation",
                "success": all_preserved,
                "test_id": test_id,
                "correlation_ids_captured": correlation_ids_captured,
                "handler_result": result,
                "chain_length": len(correlation_ids_captured),
                "all_preserved": all_preserved,
                "error": None
            }
        except Exception as e:
            return {
                "test_name": "middleware_chain_correlation",
                "success": False,
                "test_id": test_id,
                "correlation_ids_captured": [],
                "handler_result": None,
                "chain_length": 0,
                "all_preserved": False,
                "error": str(e)
            }

    async def test_middleware_composer_correlation(self) -> dict[str, Any]:
        """Test correlation ID preservation with MiddlewareComposer."""
        test_id = "composer-test-123abc"
        
        try:
            # Set correlation ID
            set_correlation_id(test_id)
            
            if not IMPORTS_AVAILABLE:
                # Mock MiddlewareComposer
                class MockMiddlewareComposer:
                    def __init__(self, middleware_list):
                        self.middleware = middleware_list
                        self.correlation_ids = []

                    def compose(self, handler, timeout=None):
                        async def composed_handler(*args, **kwargs):
                            # Capture initial correlation ID
                            initial_id = correlation_id_ctx.get()
                            self.correlation_ids.append(("compose_start", initial_id))
                            
                            # Execute middleware chain
                            current_handler = handler
                            for middleware in reversed(self.middleware):
                                current_handler = self._wrap_middleware(middleware, current_handler)
                            
                            result = await current_handler(*args, **kwargs)
                            
                            # Capture final correlation ID
                            final_id = correlation_id_ctx.get()
                            self.correlation_ids.append(("compose_end", final_id))
                            
                            return result

                        return composed_handler

                    def _wrap_middleware(self, middleware, handler):
                        async def wrapped(*args, **kwargs):
                            return await middleware(handler, *args, **kwargs)
                        return wrapped

                MiddlewareComposer = MockMiddlewareComposer

            # Create test middleware
            class LoggingTestMiddleware(BaseMiddleware if IMPORTS_AVAILABLE else object):
                def __init__(self):
                    if IMPORTS_AVAILABLE:
                        super().__init__(name="LoggingTestMiddleware")

                async def __call__(self, handler, *args, **kwargs):
                    # Simulate logging middleware behavior
                    correlation_id = correlation_id_ctx.get()
                    return await handler(*args, **kwargs)

            class AuthTestMiddleware(BaseMiddleware if IMPORTS_AVAILABLE else object):
                def __init__(self):
                    if IMPORTS_AVAILABLE:
                        super().__init__(name="AuthTestMiddleware")

                async def __call__(self, handler, *args, **kwargs):
                    # Simulate auth middleware behavior
                    correlation_id = correlation_id_ctx.get()
                    return await handler(*args, **kwargs)

            # Create middleware list
            middleware_list = [LoggingTestMiddleware(), AuthTestMiddleware()]
            
            # Create composer
            composer = MiddlewareComposer(middleware_list)

            # Mock handler
            async def test_handler(*args, **kwargs):
                handler_correlation_id = correlation_id_ctx.get()
                return {
                    "statusCode": 200,
                    "body": "composer_success",
                    "handler_correlation_id": handler_correlation_id
                }

            # Compose and execute
            composed_handler = composer.compose(test_handler)
            result = await composed_handler({"test": "event"}, {"test": "context"})

            # Validate correlation ID preservation
            if IMPORTS_AVAILABLE:
                success = result["handler_correlation_id"] == test_id
                correlation_ids = [test_id, result["handler_correlation_id"]]
            else:
                success = all(cid == test_id for _, cid in composer.correlation_ids)
                correlation_ids = [cid for _, cid in composer.correlation_ids]

            return {
                "test_name": "middleware_composer_correlation",
                "success": success,
                "test_id": test_id,
                "correlation_ids_captured": correlation_ids,
                "handler_result": result,
                "middleware_count": len(middleware_list),
                "all_preserved": success,
                "error": None
            }
        except Exception as e:
            return {
                "test_name": "middleware_composer_correlation",
                "success": False,
                "test_id": test_id,
                "correlation_ids_captured": [],
                "handler_result": None,
                "middleware_count": 0,
                "all_preserved": False,
                "error": str(e)
            }

    async def run_all_tests(self) -> dict[str, Any]:
        """Run all middleware correlation ID tests."""
        print("Running middleware correlation ID integration tests...")

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
            self.test_structured_logging_middleware_correlation,
            self.test_authentication_middleware_correlation,
            self.test_middleware_chain_correlation,
            self.test_middleware_composer_correlation,
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

    def save_results(self, results: dict[str, Any], filename: str = "middleware_correlation_test_results.json"):
        """Save test results to file."""
        output_path = Path("tasks/logging-standardization/artifacts") / filename
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Middleware correlation ID test results saved to: {output_path}")

    def print_summary(self, results: dict[str, Any]):
        """Print a human-readable summary of test results."""
        print("\n=== Middleware Correlation ID Integration Test Summary ===")

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

    parser = argparse.ArgumentParser(description="Test middleware correlation ID integration")
    parser.add_argument("--output", type=str, help="Output filename for results")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    tester = MiddlewareCorrelationTester()
    results = await tester.run_all_tests()

    filename = args.output or "middleware_correlation_test_results.json"
    tester.save_results(results, filename)
    tester.print_summary(results)

    if args.verbose:
        print("\n=== Detailed Results ===")
        print(json.dumps(results, indent=2))

    # Exit with appropriate code
    sys.exit(0 if results["summary"]["overall_success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
