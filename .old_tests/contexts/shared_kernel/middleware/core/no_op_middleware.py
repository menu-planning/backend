from typing import Any

from src.contexts.shared_kernel.middleware.core.base_middleware import (
    BaseMiddleware,
    EndpointHandler,
)


class NoOpMiddleware(BaseMiddleware):
    """
    No-operation middleware for testing and development.

    This middleware simply passes through the request without modification,
    useful for testing middleware composition or as a placeholder.
    """

    async def __call__(
        self,
        handler: EndpointHandler,
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Pass through the request without modification.

        Args:
            handler: The next handler in the middleware chain
            event: The AWS Lambda event dictionary

        Returns:
            The response from the handler unchanged
        """
        return await handler(event)
