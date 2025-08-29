"""
Base middleware class for the unified middleware system.

This module provides the foundational BaseMiddleware class that all middleware
components should inherit from, ensuring consistent behavior and composition.
"""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

EndpointHandler = Callable[..., Awaitable[dict[str, Any]]]


class BaseMiddleware(ABC):
    """
    Base class for all middleware components.

    This class provides a simple, consistent interface for middleware components
    that can be composed together. Each middleware handles one specific concern
    and can be chained with other middleware.

    Following the KISS principle, this base class is intentionally simple and
    focuses on the core middleware pattern without unnecessary complexity.
    """

    def __init__(self, name: str | None = None, timeout: float | None = None):
        """
        Initialize the base middleware.

        Args:
            name: Optional name for the middleware (useful for debugging)
            timeout: Optional timeout in seconds for this middleware's operations
        """
        self.name = name or self.__class__.__name__
        self.timeout = timeout

    @abstractmethod
    async def __call__(
        self,
        handler: EndpointHandler,
        *args,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute the middleware around the handler.

        This is the core method that all middleware must implement. It should:
        1. Perform any pre-processing before calling the handler
        2. Call the handler with the event and context
        3. Perform any post-processing on the response
        4. Return the final response

        Args:
            handler: The next handler in the middleware chain
            event: The AWS Lambda event dictionary
            context: The AWS Lambda context object

        Returns:
            The response from the handler (potentially modified)
        """

    def __repr__(self) -> str:
        """Return string representation of the middleware."""
        timeout_str = f", timeout={self.timeout}s" if self.timeout else ""
        return f"{self.__class__.__name__}(name='{self.name}'{timeout_str})"
