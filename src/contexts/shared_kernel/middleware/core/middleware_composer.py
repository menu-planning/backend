"""
Middleware composer for handling middleware execution order and composition.

This module provides the MiddlewareComposer class that manages the composition
and execution order of multiple middleware components with proper timeout handling
and exception management using anyio cancel scopes.

The composer enforces a fixed, secure middleware order to ensure consistent
behavior and prevent security vulnerabilities.
"""

from typing import Any

import anyio

from src.contexts.shared_kernel.middleware.auth.authentication import (
    AuthenticationMiddleware,
)
from src.contexts.shared_kernel.middleware.core.base_middleware import (
    BaseMiddleware,
    EndpointHandler,
)
from src.contexts.shared_kernel.middleware.error_handling.exception_handler import (
    ExceptionHandlerMiddleware,
)
from src.contexts.shared_kernel.middleware.logging.structured_logger import (
    StructuredLoggingMiddleware,
)

MIDDLEWARE_ORDER = {
    "logging": 0,  # First: capture all requests
    "auth": 1,  # Early: authenticate before business logic
    "custom": 2,  # Middle: business-specific middleware
    "error": 3,  # Last: catch and handle all errors
}


class MiddlewareComposer:
    """
    Composes multiple middleware components into a single executable chain.

    This class enforces a fixed, secure middleware order to ensure consistent
    behavior and prevent security vulnerabilities. The execution order is:
    1. Logging middleware (first - captures everything)
    2. Authentication middleware (early - before business logic)
    3. Custom middleware (middle - business-specific logic)
    4. Error handling middleware (last - catches all errors)

    The composer also handles timeout management using anyio cancel scopes
    and provides exception grouping for better error handling.

    Example:
        composer = MiddlewareComposer([
            LoggingMiddleware(),
            AuthMiddleware(),
            CustomBusinessMiddleware(),
            ErrorMiddleware()
        ], default_timeout=30.0)
        final_handler = composer.compose(original_handler)
    """

    def __init__(
        self, middleware: list[BaseMiddleware], default_timeout: float | None = None
    ):
        """
        Initialize the middleware composer.

        Args:
            middleware: List of middleware components (order will be enforced)
            default_timeout: Default timeout in seconds for the entire middleware chain
        """
        self.middleware = self._enforce_middleware_order(middleware)
        self.default_timeout = default_timeout

    def _enforce_middleware_order(
        self, middleware: list[BaseMiddleware]
    ) -> list[BaseMiddleware]:
        """
        Enforce fixed middleware order for security and consistency.

        Args:
            middleware: List of middleware components

        Returns:
            List of middleware components in the correct order

        Raises:
            ValueError: If middleware order cannot be determined
        """
        if not middleware:
            return []

        # Categorize middleware by type
        categorized = {"logging": [], "auth": [], "custom": [], "error": []}

        for m in middleware:
            category = self._categorize_middleware(m)
            categorized[category].append(m)

        # Build ordered list
        ordered = []

        # Add logging middleware first
        ordered.extend(categorized["logging"])

        # Add auth middleware early
        ordered.extend(categorized["auth"])

        # Add custom middleware in the middle
        ordered.extend(categorized["custom"])

        # Add error handling middleware last
        ordered.extend(categorized["error"])

        return ordered

    def _categorize_middleware(self, middleware: BaseMiddleware) -> str:
        """
        Categorize middleware by type using proper instance checks.

        Args:
            middleware: The middleware to categorize

        Returns:
            Category string: "logging", "auth", "error", or "custom"
        """

        # Check for specific middleware types using isinstance
        if isinstance(middleware, StructuredLoggingMiddleware):
            return "logging"

        if isinstance(middleware, AuthenticationMiddleware):
            return "auth"

        if isinstance(middleware, ExceptionHandlerMiddleware):
            return "error"

        # Default to custom middleware for any other types
        return "custom"

    def compose(
        self,
        handler: EndpointHandler,
        timeout: float | None = None,
    ) -> EndpointHandler:
        """
        Compose the middleware with the handler.

        Args:
            handler: The original handler function to wrap
            timeout: Override timeout for this specific composition

        Returns:
            A new handler function that executes all middleware in the correct order
            with timeout handling
        """
        # Start with the innermost handler
        composed_handler = handler

        # Wrap each middleware around the current handler
        # Note: We reverse the list so the first middleware becomes outermost
        for middleware in reversed(self.middleware):
            composed_handler = self._wrap_middleware(middleware, composed_handler)

        # Wrap with timeout handling at the outermost level
        return self._wrap_with_timeout(
            composed_handler, timeout or self.default_timeout
        )

    def _wrap_middleware(
        self,
        middleware: BaseMiddleware,
        handler: EndpointHandler,
    ) -> EndpointHandler:
        """
        Wrap a single middleware around a handler.

        Args:
            middleware: The middleware to wrap
            handler: The handler to wrap

        Returns:
            A new handler that executes the middleware around the original handler
        """

        async def wrapped_handler(
            *args,
            **kwargs,
        ) -> dict[str, Any]:
            """Execute the middleware around the handler."""
            return await middleware(handler, *args, **kwargs)

        return wrapped_handler

    def _wrap_with_timeout(
        self, handler: EndpointHandler, timeout: float | None
    ) -> EndpointHandler:
        """
        Wrap handler with timeout handling using anyio cancel scopes.

        Args:
            handler: The handler to wrap with timeout
            timeout: Timeout in seconds (None = no timeout)

        Returns:
            A new handler with timeout handling
        """
        if timeout is None:
            return handler

        async def timeout_wrapped_handler(
            event: dict[str, Any], context: Any
        ) -> dict[str, Any]:
            """
            Execute handler with timeout using anyio move_on_after.

            This approach ensures that:
            1. Timeouts are handled gracefully
            2. Cancellation exceptions are properly propagated
            3. The client always receives a response
            """
            with anyio.move_on_after(timeout):
                return await handler(event, context)

            # If we reach here, timeout occurred without exceptions
            return {"error": "Request timeout", "statusCode": 408}

        return timeout_wrapped_handler

    def add_middleware(
        self, middleware: BaseMiddleware, position: int | None = None
    ) -> None:
        """
        Add middleware to the composition.

        Args:
            middleware: The middleware to add
            position: Position to insert (None = append to end)
        """
        if position is None:
            self.middleware.append(middleware)
        else:
            self.middleware.insert(position, middleware)

    def remove_middleware(self, middleware: BaseMiddleware) -> None:
        """
        Remove middleware from the composition.

        Args:
            middleware: The middleware to remove
        """
        if middleware in self.middleware:
            self.middleware.remove(middleware)

    def clear(self) -> None:
        """Remove all middleware from the composition."""
        self.middleware.clear()

    def __len__(self) -> int:
        """Return the number of middleware components."""
        return len(self.middleware)

    def __repr__(self) -> str:
        """Return string representation of the composer."""
        middleware_names = [m.name for m in self.middleware]
        timeout_str = (
            f", timeout={self.default_timeout}s" if self.default_timeout else ""
        )
        return f"MiddlewareComposer(middleware={middleware_names}{timeout_str})"
