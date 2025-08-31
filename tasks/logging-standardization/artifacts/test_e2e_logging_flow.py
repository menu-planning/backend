#!/usr/bin/env python3
"""
End-to-End Logging Flow Verification

This script performs comprehensive manual verification of the complete request flow
with correlation ID tracking across all bounded contexts and middleware layers.

Purpose: Manually verify complete request flow with correlation ID tracking
Task: 4.4.1 End-to-end logging flow verification
"""

import asyncio
import json
import logging
import sys
import time
import uuid
from contextlib import contextmanager
from io import StringIO
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, '/Users/joaquim/projects/menu-planning/backend/src')

from logging.logger import correlation_id_ctx, set_correlation_id, logger
from contexts.shared_kernel.middleware.core.middleware_composer import MiddlewareComposer
from contexts.shared_kernel.middleware.auth.authentication import AuthenticationMiddleware
from contexts.shared_kernel.middleware.logging.structured_logger import StructuredLoggingMiddleware
from contexts.shared_kernel.middleware.error_handling.exception_handler import ExceptionHandlerMiddleware


class LogCapture:
    """Captures log output for analysis"""
    
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
        self.handler = None
        self.stream = StringIO()
    
    def __enter__(self):
        # Create custom handler to capture structured logs
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setLevel(logging.DEBUG)
        
        # Get the root logger and add our handler
        root_logger = logging.getLogger()
        root_logger.addHandler(self.handler)
        root_logger.setLevel(logging.DEBUG)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handler:
            logging.getLogger().removeHandler(self.handler)
        
        # Parse captured logs
        self.stream.seek(0)
        log_content = self.stream.read()
        
        # Split by lines and parse JSON logs
        for line in log_content.strip().split('\n'):
            if line.strip():
                try:
                    # Try to parse as JSON (structured log)
                    log_entry = json.loads(line)
                    self.logs.append(log_entry)
                except json.JSONDecodeError:
                    # Handle non-JSON logs (fallback)
                    self.logs.append({
                        'message': line,
                        'level': 'INFO',
                        'raw': True
                    })
    
    def get_logs_with_correlation_id(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Get all logs that contain the specified correlation ID"""
        return [
            log for log in self.logs 
            if log.get('correlation_id') == correlation_id
        ]
    
    def get_logs_by_logger(self, logger_name: str) -> List[Dict[str, Any]]:
        """Get all logs from a specific logger"""
        return [
            log for log in self.logs 
            if log.get('logger', '').startswith(logger_name)
        ]


class E2ELoggingFlowVerifier:
    """End-to-end logging flow verification"""
    
    def __init__(self):
        self.results = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
    
    def log_test_result(self, test_name: str, passed: bool, details: str):
        """Log test result"""
        self.results['tests_run'] += 1
        if passed:
            self.results['tests_passed'] += 1
            status = "PASS"
        else:
            self.results['tests_failed'] += 1
            status = "FAIL"
        
        result = {
            'test': test_name,
            'status': status,
            'details': details
        }
        self.results['details'].append(result)
        print(f"[{status}] {test_name}: {details}")
    
    async def test_correlation_id_propagation(self):
        """Test 1: Correlation ID propagation through request lifecycle"""
        test_name = "Correlation ID Propagation"
        
        try:
            correlation_id = str(uuid.uuid4())
            
            with LogCapture() as log_capture:
                # Simulate request start with correlation ID
                set_correlation_id(correlation_id)
                
                # Log from different components
                logger.info("Request started", extra={'component': 'api'})
                logger.info("Processing business logic", extra={'component': 'service'})
                logger.info("Database operation", extra={'component': 'repository'})
                logger.info("Request completed", extra={'component': 'api'})
                
                # Clear correlation ID
                correlation_id_ctx.set("")
            
            # Verify all logs have the correlation ID
            correlated_logs = log_capture.get_logs_with_correlation_id(correlation_id)
            
            if len(correlated_logs) >= 4:
                # Check that all expected components logged with correlation ID
                components = {log.get('component') for log in correlated_logs}
                expected_components = {'api', 'service', 'repository'}
                
                if expected_components.issubset(components):
                    self.log_test_result(
                        test_name, 
                        True, 
                        f"All {len(correlated_logs)} logs contain correlation ID {correlation_id[:8]}..."
                    )
                else:
                    missing = expected_components - components
                    self.log_test_result(
                        test_name, 
                        False, 
                        f"Missing components in logs: {missing}"
                    )
            else:
                self.log_test_result(
                    test_name, 
                    False, 
                    f"Expected 4+ logs with correlation ID, got {len(correlated_logs)}"
                )
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_middleware_integration(self):
        """Test 2: Middleware integration with logging"""
        test_name = "Middleware Integration"
        
        try:
            correlation_id = str(uuid.uuid4())
            
            with LogCapture() as log_capture:
                # Create middleware chain
                structured_logging_middleware = StructuredLoggingMiddleware()
                auth_middleware = AuthenticationMiddleware()
                error_middleware = ExceptionHandlerMiddleware()
                
                composer = MiddlewareComposer([
                    structured_logging_middleware,
                    auth_middleware,
                    error_middleware
                ])
                
                # Mock request/response
                mock_request = Mock()
                mock_request.headers = {'X-Correlation-ID': correlation_id}
                mock_response = Mock()
                
                # Simulate middleware chain execution
                async def mock_handler(request, response):
                    logger.info("Handler executed", extra={'handler': 'test'})
                    return response
                
                # Execute middleware chain
                composed_handler = composer.compose(mock_handler)
                await composed_handler(mock_request)
            
            # Verify middleware logs contain correlation ID
            correlated_logs = log_capture.get_logs_with_correlation_id(correlation_id)
            middleware_logs = [
                log for log in correlated_logs 
                if any(keyword in log.get('message', '') for keyword in ['middleware', 'request', 'response'])
            ]
            
            if len(middleware_logs) > 0:
                self.log_test_result(
                    test_name, 
                    True, 
                    f"Middleware chain logged {len(middleware_logs)} entries with correlation ID"
                )
            else:
                self.log_test_result(
                    test_name, 
                    False, 
                    f"No middleware logs found with correlation ID {correlation_id[:8]}..."
                )
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_cross_context_logging(self):
        """Test 3: Cross-context logging with correlation ID preservation"""
        test_name = "Cross-Context Logging"
        
        try:
            correlation_id = str(uuid.uuid4())
            
            with LogCapture() as log_capture:
                set_correlation_id(correlation_id)
                
                # Simulate logging from different bounded contexts
                contexts = [
                    'client_onboarding',
                    'products_catalog', 
                    'recipes_catalog',
                    'iam',
                    'shared_kernel'
                ]
                
                for context in contexts:
                    logger.info(
                        f"Operation in {context}", 
                        extra={
                            'context': context,
                            'operation': 'test_operation'
                        }
                    )
                
                correlation_id_ctx.set("")
            
            # Verify all contexts logged with correlation ID
            correlated_logs = log_capture.get_logs_with_correlation_id(correlation_id)
            logged_contexts = {log.get('context') for log in correlated_logs if log.get('context')}
            
            if len(logged_contexts) >= len(contexts):
                self.log_test_result(
                    test_name, 
                    True, 
                    f"All {len(contexts)} contexts logged with correlation ID"
                )
            else:
                missing_contexts = set(contexts) - logged_contexts
                self.log_test_result(
                    test_name, 
                    False, 
                    f"Missing contexts: {missing_contexts}"
                )
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_async_operation_correlation(self):
        """Test 4: Async operation correlation ID preservation"""
        test_name = "Async Operation Correlation"
        
        try:
            correlation_id = str(uuid.uuid4())
            
            with LogCapture() as log_capture:
                set_correlation_id(correlation_id)
                
                async def async_operation_1():
                    await asyncio.sleep(0.01)
                    logger.info("Async operation 1 completed", extra={'operation': 'async_1'})
                
                async def async_operation_2():
                    await asyncio.sleep(0.02)
                    logger.info("Async operation 2 completed", extra={'operation': 'async_2'})
                
                async def async_operation_3():
                    await asyncio.sleep(0.01)
                    logger.info("Async operation 3 completed", extra={'operation': 'async_3'})
                
                # Run async operations concurrently
                await asyncio.gather(
                    async_operation_1(),
                    async_operation_2(), 
                    async_operation_3()
                )
                
                correlation_id_ctx.set("")
            
            # Verify all async operations logged with correlation ID
            correlated_logs = log_capture.get_logs_with_correlation_id(correlation_id)
            async_logs = [
                log for log in correlated_logs 
                if log.get('operation', '').startswith('async_')
            ]
            
            if len(async_logs) >= 3:
                self.log_test_result(
                    test_name, 
                    True, 
                    f"All {len(async_logs)} async operations preserved correlation ID"
                )
            else:
                self.log_test_result(
                    test_name, 
                    False, 
                    f"Expected 3 async logs with correlation ID, got {len(async_logs)}"
                )
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_error_logging_with_correlation(self):
        """Test 5: Error logging with correlation ID and context"""
        test_name = "Error Logging with Correlation"
        
        try:
            correlation_id = str(uuid.uuid4())
            
            with LogCapture() as log_capture:
                set_correlation_id(correlation_id)
                
                try:
                    # Simulate an error scenario
                    raise ValueError("Test error for logging verification")
                except ValueError as e:
                    logger.error(
                        "Error occurred during processing",
                        extra={
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'component': 'test_component'
                        },
                        exc_info=True
                    )
                
                # Log recovery action
                logger.info(
                    "Error handled, continuing processing",
                    extra={'recovery_action': 'continue'}
                )
                
                correlation_id_ctx.set("")
            
            # Verify error logs contain correlation ID and proper context
            correlated_logs = log_capture.get_logs_with_correlation_id(correlation_id)
            error_logs = [
                log for log in correlated_logs 
                if log.get('level') == 'ERROR' or 'error' in log.get('message', '').lower()
            ]
            
            if len(error_logs) > 0:
                error_log = error_logs[0]
                has_context = (
                    error_log.get('error_type') and 
                    error_log.get('error_message') and
                    error_log.get('component')
                )
                
                if has_context:
                    self.log_test_result(
                        test_name, 
                        True, 
                        f"Error logs contain correlation ID and proper context"
                    )
                else:
                    self.log_test_result(
                        test_name, 
                        False, 
                        f"Error logs missing context fields"
                    )
            else:
                self.log_test_result(
                    test_name, 
                    False, 
                    f"No error logs found with correlation ID"
                )
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_structured_data_logging(self):
        """Test 6: Structured data logging with correlation ID"""
        test_name = "Structured Data Logging"
        
        try:
            correlation_id = str(uuid.uuid4())
            
            with LogCapture() as log_capture:
                set_correlation_id(correlation_id)
                
                # Log structured data
                user_data = {
                    'user_id': 'user_123',
                    'action': 'create_recipe',
                    'recipe_id': 'recipe_456'
                }
                
                logger.info(
                    "User action performed",
                    extra={
                        'user_data': user_data,
                        'timestamp': time.time(),
                        'request_size': 1024
                    }
                )
                
                # Log with nested structures
                complex_data = {
                    'request': {
                        'method': 'POST',
                        'path': '/api/recipes',
                        'headers': {'content-type': 'application/json'}
                    },
                    'response': {
                        'status': 201,
                        'size': 512
                    }
                }
                
                logger.info(
                    "Request processed",
                    extra={'request_response': complex_data}
                )
                
                correlation_id_ctx.set("")
            
            # Verify structured data is properly logged with correlation ID
            correlated_logs = log_capture.get_logs_with_correlation_id(correlation_id)
            structured_logs = [
                log for log in correlated_logs 
                if log.get('user_data') or log.get('request_response')
            ]
            
            if len(structured_logs) >= 2:
                # Check data integrity
                user_log = next((log for log in structured_logs if log.get('user_data')), None)
                request_log = next((log for log in structured_logs if log.get('request_response')), None)
                
                if user_log and request_log:
                    self.log_test_result(
                        test_name, 
                        True, 
                        f"Structured data logged correctly with correlation ID"
                    )
                else:
                    self.log_test_result(
                        test_name, 
                        False, 
                        f"Structured data incomplete in logs"
                    )
            else:
                self.log_test_result(
                    test_name, 
                    False, 
                    f"Expected 2 structured logs with correlation ID, got {len(structured_logs)}"
                )
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all end-to-end logging flow tests"""
        print("=" * 80)
        print("END-TO-END LOGGING FLOW VERIFICATION")
        print("=" * 80)
        print()
        
        tests = [
            self.test_correlation_id_propagation,
            self.test_middleware_integration,
            self.test_cross_context_logging,
            self.test_async_operation_correlation,
            self.test_error_logging_with_correlation,
            self.test_structured_data_logging
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                self.log_test_result(test.__name__, False, f"Test execution failed: {str(e)}")
            print()
        
        # Print summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.results['tests_run']}")
        print(f"Tests Passed: {self.results['tests_passed']}")
        print(f"Tests Failed: {self.results['tests_failed']}")
        
        if self.results['tests_failed'] > 0:
            print(f"Success Rate: {(self.results['tests_passed'] / self.results['tests_run']) * 100:.1f}%")
            print("\nFAILED TESTS:")
            for result in self.results['details']:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['details']}")
        else:
            print("Success Rate: 100.0%")
            print("\n✅ ALL TESTS PASSED - End-to-end logging flow verification successful!")
        
        return self.results


async def main():
    """Main execution function"""
    verifier = E2ELoggingFlowVerifier()
    results = await verifier.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results['tests_failed'] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
