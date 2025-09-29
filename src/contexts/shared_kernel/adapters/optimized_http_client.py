"""Optimized HTTP client configuration for web applications.

This module provides a standardized HTTP client configuration that
optimizes connection pooling, timeouts, and performance for both
FastAPI and AWS Lambda applications. It complements existing HTTP client implementations.
"""

from typing import Any

import httpx
from src.config.app_config import get_app_settings


class OptimizedHTTPClient:
    """Optimized HTTP client with connection pooling and performance tuning.

    This client is configured for web applications with:
    - Connection pooling for better performance
    - Optimized timeouts for web applications
    - Proper connection limits for concurrent requests
    - Standardized headers and configuration
    """

    def __init__(
        self,
        base_url: httpx.URL | str = "",
        headers: dict[str, str] | None = None,
        timeout: httpx.Timeout | None = None,
        limits: httpx.Limits | None = None,
    ) -> None:
        """Initialize optimized HTTP client.

        Args:
            base_url: Base URL for all requests.
            headers: Default headers for all requests.
            timeout: Request timeout configuration.
            limits: Connection limits configuration.

        Notes:
            Uses optimized defaults for connection pooling and timeouts suitable for web applications.
        """
        # Get settings
        settings = get_app_settings()
        
        # Optimized timeout configuration
        if timeout is None:
            timeout = httpx.Timeout(
                connect=settings.http_timeout_connect,
                read=settings.http_timeout_read,
                write=settings.http_timeout_write,
                pool=settings.http_timeout_pool,
            )

        # Optimized connection limits
        if limits is None:
            limits = httpx.Limits(
                max_connections=settings.http_max_connections,
                max_keepalive_connections=settings.http_max_keepalive,
            )

        # Default headers for web applications
        default_headers = {
            "User-Agent": f"Web-App/{settings.project_name}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        if headers:
            default_headers.update(headers)

        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers=default_headers,
            timeout=timeout,
            limits=limits,
            follow_redirects=True,
            # Web application optimizations
            http2=True,  # Enable HTTP/2 for better performance
        )

    async def __aenter__(self) -> "OptimizedHTTPClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit with cleanup."""
        await self.client.aclose()

    async def close(self) -> None:
        """Close the HTTP client connection."""
        await self.client.aclose()

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a GET request."""
        return await self.client.get(url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a POST request."""
        return await self.client.post(url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a PUT request."""
        return await self.client.put(url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a PATCH request."""
        return await self.client.patch(url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a DELETE request."""
        return await self.client.delete(url, **kwargs)

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Make a request with the specified method."""
        return await self.client.request(method, url, **kwargs)


def create_optimized_http_client(
    base_url: httpx.URL | str = "",
    headers: dict[str, str] | None = None,
    timeout: httpx.Timeout | None = None,
    limits: httpx.Limits | None = None,
) -> OptimizedHTTPClient:
    """Create a new optimized HTTP client instance.

    Args:
        base_url: Base URL for all requests.
        headers: Default headers for all requests.
        timeout: Request timeout configuration.
        limits: Connection limits configuration.

    Returns:
        Configured OptimizedHTTPClient instance.

    Example:
        ```python
        # Create client for external API
        client = create_optimized_http_client(
            base_url="https://api.example.com",
            headers={"Authorization": "Bearer token"}
        )
        
        async with client:
            response = await client.get("/users")
            data = response.json()
        ```
    """
    return OptimizedHTTPClient(
        base_url=base_url,
        headers=headers,
        timeout=timeout,
        limits=limits,
    )


# # Global optimized HTTP client instance for dependency injection
# _optimized_http_client: OptimizedHTTPClient | None = None


# def get_optimized_http_client() -> OptimizedHTTPClient:
#     """Get the global optimized HTTP client instance.

#     Returns:
#         The global OptimizedHTTPClient instance.

#     Notes:
#         Creates a new instance if none exists. This is useful for
#         dependency injection in web applications.
#     """
#     global _optimized_http_client
#     if _optimized_http_client is None:
#         _optimized_http_client = OptimizedHTTPClient()
#     return _optimized_http_client


# async def close_optimized_http_client() -> None:
#     """Close the global optimized HTTP client instance.

#     Notes:
#         This should be called during application shutdown
#         to properly clean up connections.
#     """
#     global _optimized_http_client
#     if _optimized_http_client is not None:
#         await _optimized_http_client.close()
#         _optimized_http_client = None
