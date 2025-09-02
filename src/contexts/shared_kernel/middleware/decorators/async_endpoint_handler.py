"""Main decorator for Lambda handlers with middleware composition.

This module provides the `async_endpoint_handler` decorator that simplifies the use
of middleware composition in AWS Lambda functions. It follows the KISS
principle by providing a simple, declarative way to apply middleware
to Lambda handlers.
"""

import functools
from collections.abc import Callable
from typing import Any

from src.contexts.shared_kernel.middleware.core.base_middleware import (
    BaseMiddleware,
    EndpointHandler,
)
from src.contexts.shared_kernel.middleware.core.middleware_composer import (
    MiddlewareComposer,
)


def async_endpoint_handler(
    *middleware: BaseMiddleware,
    timeout: float | None = None,
    name: str | None = None,
) -> Callable[[EndpointHandler], EndpointHandler]:
    """Decorator for Lambda handlers with middleware composition.

    Provides a simple, declarative way to apply middleware to Lambda handlers.
    It follows the KISS principle by hiding the complexity of middleware
    composition behind a simple decorator interface.

    Args:
        *middleware: Variable number of middleware components to apply
                    (order will be automatically enforced).
        timeout: Optional timeout in seconds for the entire middleware chain.
        name: Optional name for the decorated handler (useful for debugging).

    Returns:
        A decorator function that wraps the handler with the specified middleware.

    Notes:
        Middleware order is automatically enforced for security and consistency:
        1. Logging middleware runs first (captures everything)
        2. Authentication middleware runs early (before business logic)
        3. Custom middleware runs in the middle (business-specific logic)
        4. Error handling middleware runs last (catches all errors)

    Examples:
        @async_endpoint_handler(
            StructuredLoggingMiddleware(),
            AuthenticationMiddleware(),
            ErrorHandlingMiddleware(),
            timeout=30.0
        )
        async def my_lambda_handler(event: dict[str, Any]) -> dict[str, Any]:
            # Your handler logic here
            return {"statusCode": 200, "body": "Hello World"}

        # Note: Order doesn't matter - it's automatically enforced!
        @async_endpoint_handler(
            ErrorHandlingMiddleware(),  # Will run last
            StructuredLoggingMiddleware(),  # Will run first
            AuthenticationMiddleware(),  # Will run early
        )
        async def another_handler(event: dict[str, Any]) -> dict[str, Any]:
            return {"statusCode": 200, "body": "Hello World"}
    """

    def decorator(
        handler: EndpointHandler,
    ) -> EndpointHandler:
        """Apply middleware to the handler function.

        Args:
            handler: The Lambda handler function to wrap.

        Returns:
            The handler wrapped with the specified middleware.

        Notes:
            Creates middleware composer and composes middleware with handler.
            Preserves original function metadata using functools.wraps.
        """
        # Create middleware composer with the provided middleware
        composer = MiddlewareComposer(list(middleware), default_timeout=timeout)

        # Compose the middleware with the handler
        composed_handler = composer.compose(handler, timeout=timeout)

        # Preserve the original function metadata
        @functools.wraps(handler)
        async def wrapped_handler(
            *args,
            **kwargs,
        ) -> dict[str, Any]:
            """Execute the handler with middleware composition."""
            return await composed_handler(*args, **kwargs)

        # Add metadata for debugging and introspection
        meta = {
            "middleware_count": len(middleware),
            "middleware_names": [m.name for m in middleware],
            "timeout": timeout,
            "decorator_name": name or handler.__name__,
        }
        wrapped_handler._middleware_info = meta  # type: ignore[attr-defined]

        return wrapped_handler

    return decorator


def async_endpoint_handler_simple(
    *middleware: BaseMiddleware,
    timeout: float | None = None,
) -> Callable[[EndpointHandler], EndpointHandler]:
    """Simplified version of async_endpoint_handler without additional metadata.

    Provides a simpler alternative that focuses on the core functionality
    without the additional debugging features. Use this when you want
    minimal overhead and don't need introspection capabilities.

    Args:
        *middleware: Variable number of middleware components to apply.
        timeout: Optional timeout in seconds for the entire middleware chain.

    Returns:
        A decorator function that wraps the handler with the specified middleware.

    Notes:
        Middleware order is automatically enforced for security and consistency.
        No additional metadata is attached to the wrapped handler.

    Examples:
        @async_endpoint_handler_simple(
            StructuredLoggingMiddleware(),
            AuthenticationMiddleware()
        )
        async def my_lambda_handler(event: dict[str, Any]) -> dict[str, Any]:
            return {"statusCode": 200, "body": "Hello World"}
    """

    def decorator(
        handler: EndpointHandler,
    ) -> EndpointHandler:
        """Apply middleware to the handler function.

        Args:
            handler: The Lambda handler function to wrap.

        Returns:
            The handler wrapped with the specified middleware.

        Notes:
            Creates middleware composer and composes middleware with handler.
            No additional metadata is attached.
        """
        composer = MiddlewareComposer(list(middleware), default_timeout=timeout)
        composed_handler = composer.compose(handler, timeout=timeout)

        @functools.wraps(handler)
        async def wrapped_handler(
            event: dict[str, Any], context: Any
        ) -> dict[str, Any]:
            """Execute the handler with middleware composition."""
            return await composed_handler(event, context)

        return wrapped_handler

    return decorator
