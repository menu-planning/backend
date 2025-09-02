"""Base middleware infrastructure for unified middleware system.

This module provides the foundational BaseMiddleware class that all middleware
components inherit from, ensuring consistent behavior and composition patterns.
"""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

EndpointHandler = Callable[..., Awaitable[dict[str, Any]]]


class BaseMiddleware(ABC):
    """Base class for all middleware components in the unified system.

    Provides a consistent interface for middleware components that can be composed
    together. Each middleware handles one specific concern and can be chained
    with other middleware following the KISS principle.

    Attributes:
        name: Optional name for the middleware (useful for debugging).
        timeout: Optional timeout in seconds for this middleware's operations.

    Notes:
        All middleware must implement the __call__ method to execute around handlers.
        Concurrency: async; not thread-safe unless stated.
    """

    def __init__(self, name: str | None = None, timeout: float | None = None):
        """Initialize the base middleware.

        Args:
            name: Optional name for the middleware (useful for debugging).
            timeout: Optional timeout in seconds for this middleware's operations.
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
        """Execute the middleware around the handler.

        Args:
            handler: The next handler in the middleware chain.
            *args: Positional arguments passed to the middleware.
            **kwargs: Keyword arguments passed to the middleware.

        Returns:
            The response from the handler (potentially modified).

        Notes:
            Must perform pre-processing, call handler, and post-processing.
            All middleware must implement this method.
        """

    def __repr__(self) -> str:
        """Return string representation of the middleware."""
        timeout_str = f", timeout={self.timeout}s" if self.timeout else ""
        return f"{self.__class__.__name__}(name='{self.name}'{timeout_str})"
