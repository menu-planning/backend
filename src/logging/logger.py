"""Configure structured logging for JSON output compatible with ELK/CloudWatch.

This module provides a simple, idiomatic structlog configuration that follows
structlog's intended patterns. Uses structlog.contextvars for correlation ID
management and provides a clean API for structured logging.

The module exports:
- configure_logging(): One-time configuration function
- get_logger(): Get a configured structlog logger
- Helper functions for correlation ID management
"""

import logging
import os
import uuid

import structlog


def configure_logging(log_level: str | None = None) -> None:
    """Configure structlog for JSON output with correlation ID support.
    
    This is the one-time configuration that sets up structlog with:
    - JSON output for ELK/CloudWatch compatibility
    - Correlation ID support via contextvars
    - Proper log level filtering
    - Standard timestamp and level fields
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  Defaults to LOG_LEVEL env var or INFO.
    """
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Configure structlog with idiomatic processors
    structlog.configure(
        processors=[
            # Merge context variables (correlation_id, etc.)
            structlog.contextvars.merge_contextvars,
            # Add log level and timestamp
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            # Add logger name to the event dict
            structlog.processors.CallsiteParameterAdder(
                parameters=[structlog.processors.CallsiteParameter.FILENAME,
                           structlog.processors.CallsiteParameter.FUNC_NAME,
                           structlog.processors.CallsiteParameter.LINENO]
            ),
            # Render as JSON for ELK compatibility
            structlog.processors.JSONRenderer(),
        ],
        # Use stdlib logging for actual output
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure stdlib logging level and ensure it has a handler
    numeric_level = getattr(logging, log_level.upper(), 10)  # DEBUG = 10
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Ensure there's a handler for output
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        root_logger.addHandler(handler)


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a configured structlog logger.
    
    Args:
        name: Logger name. If None, uses the calling module's name.
        
    Returns:
        A bound structlog logger with correlation ID support.
    """
    return structlog.get_logger(name)


def set_correlation_id(correlation_id: str) -> None:
    """Set the current correlation ID in request context.
    
    Args:
        correlation_id: Correlation ID to associate with subsequent logs.
        
    Note:
        This uses structlog.contextvars for thread-safe context propagation.
    """
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def generate_correlation_id() -> str:
    """Generate and set a short correlation ID for the current context.
    
    Returns:
        The generated 8-character hex correlation ID.
    """
    cid = uuid.uuid4().hex[:8]
    set_correlation_id(cid)
    return cid


def clear_correlation_id() -> None:
    """Clear the current correlation ID from context.
    
    Note:
        This removes the correlation_id from the context variables.
    """
    structlog.contextvars.unbind_contextvars("correlation_id")


# Auto-configure on import for convenience
configure_logging()