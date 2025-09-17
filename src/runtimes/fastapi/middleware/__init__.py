"""FastAPI-specific middleware implementations.

This module provides FastAPI middleware that adapts the existing
Lambda middleware patterns to work with FastAPI's request/response cycle.

Middleware includes:
- Correlation ID tracking
- Structured logging
- Authentication and authorization
- Error handling
- Request/response processing
"""
