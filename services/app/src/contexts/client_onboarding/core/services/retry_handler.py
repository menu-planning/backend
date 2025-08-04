"""
Retry logic service for Client Onboarding Context.

Handles webhook processing failures and TypeForm API errors with intelligent retry strategies,
exponential backoff, and integration with client onboarding error handling using tenacity patterns.

Features:
- Exponential backoff for transient failures
- Specialized retry strategies for TypeForm API rate limits
- Integration with client onboarding error middleware
- Structured logging with correlation IDs
- Configurable retry policies per operation type
- Circuit breaker patterns for persistent failures
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional, TypeVar, Awaitable, List, Type, Tuple
from functools import wraps
from enum import Enum
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import anyio
from tenacity import (
    AsyncRetrying,
    RetryError,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
    wait_combine,
    retry_if_exception_type,
)

from src.contexts.client_onboarding.core.services.exceptions import ClientOnboardingError, DatabaseOperationError, FormResponseProcessingError, TypeFormAPIError, TypeFormAuthenticationError, TypeFormRateLimitError, WebhookPayloadError
from src.logging.logger import correlation_id_ctx, StructlogFactory
from src.contexts.client_onboarding.config import config


# Type variable for return values
T = TypeVar('T')

# Configure structured logging
logger = StructlogFactory.get_logger("client_onboarding_retry_handler")
standard_logger = logging.getLogger(__name__)


class RetryOperation(Enum):
    """Types of operations that can be retried."""
    TYPEFORM_API_REQUEST = "typeform_api_request"
    WEBHOOK_PROCESSING = "webhook_processing"
    DATABASE_OPERATION = "database_operation"
    FORM_RESPONSE_PROCESSING = "form_response_processing"
    CLIENT_IDENTIFIER_EXTRACTION = "client_identifier_extraction"
    EXTERNAL_API_CALL = "external_api_call"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    initial_wait: float = 1.0
    max_wait: float = 60.0
    multiplier: float = 2.0
    jitter: bool = True
    exponential_base: float = 2.0
    
    # Special handling for rate limits
    respect_rate_limit_headers: bool = True
    rate_limit_backoff_multiplier: float = 1.5
    
    # Circuit breaker configuration
    failure_threshold: int = 5
    recovery_timeout: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    
    # Logging configuration
    log_retries: bool = True
    log_failures: bool = True


@dataclass
class RetryAttempt:
    """Information about a retry attempt."""
    attempt_number: int
    operation: RetryOperation
    exception: Optional[Exception] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Circuit breaker for persistent failures."""
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    failure_threshold: int = 5
    recovery_timeout: timedelta = field(default_factory=lambda: timedelta(minutes=5))


class ClientOnboardingRetryHandler:
    """
    Retry handler with intelligent backoff strategies for client onboarding operations.
    
    Provides specialized retry logic for TypeForm API calls, webhook processing,
    and database operations with circuit breaker patterns and structured logging.
    """
    
    def __init__(self, default_config: Optional[RetryConfig] = None):
        """
        Initialize retry handler with default configuration.
        
        Args:
            default_config: Default retry configuration for all operations
        """
        self.default_config = default_config or RetryConfig()
        self.operation_configs: Dict[RetryOperation, RetryConfig] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_attempts: List[RetryAttempt] = []
        
        # Setup default configurations for different operations
        self._setup_operation_configs()
    
    def _setup_operation_configs(self) -> None:
        """Setup specialized retry configurations for different operation types."""
        
        # TypeForm API requests - more aggressive retry for rate limits
        self.operation_configs[RetryOperation.TYPEFORM_API_REQUEST] = RetryConfig(
            max_attempts=5,
            initial_wait=2.0,
            max_wait=120.0,
            multiplier=1.5,
            respect_rate_limit_headers=True,
            rate_limit_backoff_multiplier=2.0
        )
        
        # Webhook processing - fast retry for transient issues
        self.operation_configs[RetryOperation.WEBHOOK_PROCESSING] = RetryConfig(
            max_attempts=3,
            initial_wait=0.5,
            max_wait=10.0,
            multiplier=2.0,
            jitter=True
        )
        
        # Database operations - moderate retry with longer waits
        self.operation_configs[RetryOperation.DATABASE_OPERATION] = RetryConfig(
            max_attempts=4,
            initial_wait=1.0,
            max_wait=30.0,
            multiplier=2.5,
            failure_threshold=3
        )
        
        # Form response processing - conservative retry
        self.operation_configs[RetryOperation.FORM_RESPONSE_PROCESSING] = RetryConfig(
            max_attempts=2,
            initial_wait=1.5,
            max_wait=15.0,
            multiplier=2.0
        )
    
    def get_config(self, operation: RetryOperation) -> RetryConfig:
        """Get retry configuration for specific operation type."""
        return self.operation_configs.get(operation, self.default_config)
    
    def configure_operation(self, operation: RetryOperation, config: RetryConfig) -> None:
        """Configure retry behavior for specific operation type."""
        self.operation_configs[operation] = config
    
    async def retry_async(
        self,
        func: Callable[..., Awaitable[T]],
        operation: RetryOperation,
        *args,
        operation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        custom_config: Optional[RetryConfig] = None,
        **kwargs
    ) -> T:
        """
        Execute async function with retry logic and exponential backoff.
        
        Args:
            func: Async function to execute with retry
            operation: Type of operation for specialized retry logic
            *args: Positional arguments for the function
            operation_id: Unique identifier for circuit breaker tracking
            context: Additional context for logging
            custom_config: Override default retry configuration
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function execution
            
        Raises:
            RetryError: When all retry attempts are exhausted
            Exception: The last exception raised by the function
        """
        config = custom_config or self.get_config(operation)
        correlation_id = correlation_id_ctx.get() or "unknown"
        op_id = operation_id or f"{operation.value}_{correlation_id}"
        ctx = context or {}
        
        # Check circuit breaker
        if not self._check_circuit_breaker(op_id, config):
            raise CircuitBreakerOpenError(f"Circuit breaker open for operation: {op_id}")
        
        # Setup retry strategy based on operation type
        retry_strategy = self._create_retry_strategy(operation, config)
        
        try:
            async for attempt in retry_strategy:
                with attempt:
                    try:
                        # Record attempt
                        retry_attempt = RetryAttempt(
                            attempt_number=attempt.retry_state.attempt_number,
                            operation=operation,
                            correlation_id=correlation_id,
                            context=ctx
                        )
                        
                        if config.log_retries and attempt.retry_state.attempt_number > 1:
                            logger.info(
                                f"Retrying {operation.value}",
                                attempt_number=attempt.retry_state.attempt_number,
                                operation_id=op_id,
                                correlation_id=correlation_id,
                                **ctx
                            )
                        
                        # Execute function with timeout if configured
                        result = await self._execute_with_timeout(func, *args, **kwargs)
                        
                        # Reset circuit breaker on success
                        self._reset_circuit_breaker(op_id)
                        
                        return result
                        
                    except Exception as e:
                        retry_attempt.exception = e
                        self.retry_attempts.append(retry_attempt)
                        
                        # Handle rate limiting with special backoff
                        if isinstance(e, TypeFormRateLimitError):
                            await self._handle_rate_limit(e, config)
                        
                        # Record failure for circuit breaker
                        self._record_failure(op_id, config)
                        
                        # Log retry attempt
                        if config.log_retries:
                            logger.warning(
                                f"Retry attempt failed for {operation.value}",
                                attempt_number=attempt.retry_state.attempt_number,
                                operation_id=op_id,
                                correlation_id=correlation_id,
                                exception_type=type(e).__name__,
                                exception_message=str(e),
                                **ctx
                            )
                        
                        raise  # Re-raise to trigger retry logic
                        
        except RetryError as retry_error:
            # All retries exhausted
            last_exception = retry_error.last_attempt.exception()
            if last_exception is None:
                # Fallback if exception is None
                last_exception = ClientOnboardingError("Retry attempts exhausted with unknown error")
            
            if config.log_failures:
                logger.error(
                    f"All retry attempts exhausted for {operation.value}",
                    operation_id=op_id,
                    correlation_id=correlation_id,
                    max_attempts=config.max_attempts,
                    final_exception_type=type(last_exception).__name__,
                    final_exception_message=str(last_exception),
                    **ctx
                )
            
            # Open circuit breaker if threshold reached
            self._evaluate_circuit_breaker(op_id, config)
            
            raise last_exception
        
        # This should never be reached due to the async for loop behavior,
        # but we need it to satisfy the type checker
        raise ClientOnboardingError("Retry function completed without returning a value")
    
    def _create_retry_strategy(self, operation: RetryOperation, config: RetryConfig) -> AsyncRetrying:
        """Create tenacity retry strategy based on operation type and configuration."""
        
        # Define retryable exception types
        retryable_exceptions: Tuple[Type[Exception], ...] = (
            TypeFormAPIError,
            DatabaseOperationError,
            WebhookPayloadError,
            FormResponseProcessingError,
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        )
        
        # Don't retry authentication errors for most operations
        if operation != RetryOperation.TYPEFORM_API_REQUEST:
            retryable_exceptions = retryable_exceptions + (TypeFormAuthenticationError,)
        
        # Wait strategy with exponential backoff
        wait_strategy = wait_exponential(
            multiplier=config.initial_wait,
            max=config.max_wait,
            exp_base=config.exponential_base
        )
        
        # Add jitter if configured (combine with fixed wait for jitter effect)
        if config.jitter:
            wait_strategy = wait_combine(
                wait_strategy,
                wait_fixed(0.1)  # Small fixed component for jitter effect
            )
        
        return AsyncRetrying(
            stop=stop_after_attempt(config.max_attempts),
            wait=wait_strategy,
            retry=retry_if_exception_type(retryable_exceptions),
            reraise=True
        )
    
    async def _execute_with_timeout(
        self, 
        func: Callable[..., Awaitable[T]], 
        *args, 
        **kwargs
    ) -> T:
        """Execute function with configured timeout."""
        timeout = getattr(config, 'webhook_timeout_seconds', 30)
        
        try:
            with anyio.move_on_after(timeout) as cancel_scope:
                result = await func(*args, **kwargs)
                if cancel_scope.cancelled_caught:
                    raise asyncio.TimeoutError(f"Operation timed out after {timeout} seconds")
                return result
        except anyio.get_cancelled_exc_class():
            raise asyncio.TimeoutError(f"Operation cancelled due to timeout")
        except Exception:
            # Re-raise any other exceptions
            raise
        
        # This should never be reached, but satisfy type checker
        raise asyncio.TimeoutError("Function execution completed without returning a value")
    
    async def _handle_rate_limit(self, error: TypeFormRateLimitError, config: RetryConfig) -> None:
        """Handle TypeForm rate limiting with respect for retry-after headers."""
        if config.respect_rate_limit_headers and error.retry_after:
            # Respect the API's retry-after suggestion with multiplier
            wait_time = error.retry_after * config.rate_limit_backoff_multiplier
            
            logger.info(
                "Rate limit detected, waiting for suggested duration",
                retry_after_seconds=error.retry_after,
                actual_wait_seconds=wait_time,
                correlation_id=correlation_id_ctx.get()
            )
            
            await asyncio.sleep(wait_time)
    
    def _check_circuit_breaker(self, operation_id: str, config: RetryConfig) -> bool:
        """Check if circuit breaker allows operation to proceed."""
        breaker = self.circuit_breakers.get(operation_id)
        if not breaker:
            return True
        
        if breaker.state == CircuitBreakerState.CLOSED:
            return True
        elif breaker.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if (breaker.last_failure_time and 
                datetime.now(UTC) - breaker.last_failure_time > config.recovery_timeout):
                breaker.state = CircuitBreakerState.HALF_OPEN
                breaker.failure_count = 0
                return True
            return False
        elif breaker.state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False
    
    def _record_failure(self, operation_id: str, config: RetryConfig) -> None:
        """Record failure for circuit breaker tracking."""
        if operation_id not in self.circuit_breakers:
            self.circuit_breakers[operation_id] = CircuitBreaker(
                failure_threshold=config.failure_threshold,
                recovery_timeout=config.recovery_timeout
            )
        
        breaker = self.circuit_breakers[operation_id]
        breaker.failure_count += 1
        breaker.last_failure_time = datetime.now(UTC)
    
    def _reset_circuit_breaker(self, operation_id: str) -> None:
        """Reset circuit breaker on successful operation."""
        if operation_id in self.circuit_breakers:
            breaker = self.circuit_breakers[operation_id]
            breaker.state = CircuitBreakerState.CLOSED
            breaker.failure_count = 0
    
    def _evaluate_circuit_breaker(self, operation_id: str, config: RetryConfig) -> None:
        """Evaluate whether to open circuit breaker."""
        breaker = self.circuit_breakers.get(operation_id)
        if breaker and breaker.failure_count >= config.failure_threshold:
            breaker.state = CircuitBreakerState.OPEN
            
            logger.warning(
                f"Circuit breaker opened for operation: {operation_id}",
                failure_count=breaker.failure_count,
                threshold=config.failure_threshold,
                recovery_timeout_minutes=config.recovery_timeout.total_seconds() / 60
            )
    
    def get_retry_statistics(self, operation: Optional[RetryOperation] = None) -> Dict[str, Any]:
        """Get retry statistics for monitoring and debugging."""
        if operation:
            attempts = [a for a in self.retry_attempts if a.operation == operation]
        else:
            attempts = self.retry_attempts
        
        if not attempts:
            return {"total_attempts": 0, "operations": {}}
        
        stats = {
            "total_attempts": len(attempts),
            "operations": {},
            "recent_failures": len([a for a in attempts[-20:] if a.exception]),
            "circuit_breakers": {
                op_id: {
                    "state": breaker.state.value,
                    "failure_count": breaker.failure_count,
                    "last_failure": breaker.last_failure_time.isoformat() if breaker.last_failure_time else None
                }
                for op_id, breaker in self.circuit_breakers.items()
            }
        }
        
        # Group by operation type
        for op_type in RetryOperation:
            op_attempts = [a for a in attempts if a.operation == op_type]
            if op_attempts:
                stats["operations"][op_type.value] = {
                    "total_attempts": len(op_attempts),
                    "failed_attempts": len([a for a in op_attempts if a.exception]),
                    "success_rate": (len(op_attempts) - len([a for a in op_attempts if a.exception])) / len(op_attempts)
                }
        
        return stats


class CircuitBreakerOpenError(ClientOnboardingError):
    """Raised when circuit breaker prevents operation execution."""
    pass


# Decorator for easy retry application
def retry_on_failure(
    operation: RetryOperation,
    operation_id: Optional[str] = None,
    custom_config: Optional[RetryConfig] = None,
    context: Optional[Dict[str, Any]] = None
):
    """
    Decorator to apply retry logic to async functions.
    
    Usage:
        @retry_on_failure(RetryOperation.TYPEFORM_API_REQUEST)
        async def call_typeform_api():
            # Implementation that might fail
            pass
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            handler = ClientOnboardingRetryHandler()
            return await handler.retry_async(
                func,
                operation,
                *args,
                operation_id=operation_id,
                context=context,
                custom_config=custom_config,
                **kwargs
            )
        return wrapper
    return decorator


# Global retry handler instance
_global_retry_handler: Optional[ClientOnboardingRetryHandler] = None


def get_retry_handler() -> ClientOnboardingRetryHandler:
    """Get or create global retry handler instance."""
    global _global_retry_handler
    if _global_retry_handler is None:
        _global_retry_handler = ClientOnboardingRetryHandler()
    return _global_retry_handler


def configure_global_retry_handler(config: RetryConfig) -> None:
    """Configure the global retry handler with custom settings."""
    global _global_retry_handler
    _global_retry_handler = ClientOnboardingRetryHandler(default_config=config) 