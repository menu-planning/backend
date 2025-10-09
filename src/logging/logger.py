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
import logfire
import colorlog

def add_log_level_emoji(logger, method_name, event_dict):
    """Add emoji to log level for better visibility (without colors in JSON)."""
    level = event_dict.get("level", "").lower()
    
    # Define emojis for each level (no colors in JSON)
    level_emojis = {
        "debug": "🔍",
        "info": "ℹ️", 
        "warning": "⚠️",
        "error": "❌",
        "critical": "💥",
    }
    
    emoji = level_emojis.get(level, "📝")  # Default emoji
    
    # Add emoji prefix to the event message (no color codes)
    if "event" in event_dict:
        event_dict["event"] = f"{emoji} {event_dict['event']}"
    
    return event_dict


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
        log_level = os.getenv("LOG_LEVEL","INFO")
    
    # Configure structlog with idiomatic processors
    structlog.configure(
        processors=[
            # Merge context variables (correlation_id, etc.)
            structlog.contextvars.merge_contextvars,
            # Add log level and timestamp
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            # Add emoji and color to log levels
            add_log_level_emoji,
            # Add logger name to the event dict
            structlog.processors.CallsiteParameterAdder(
                parameters=[structlog.processors.CallsiteParameter.FILENAME,
                           structlog.processors.CallsiteParameter.FUNC_NAME,
                           structlog.processors.CallsiteParameter.LINENO]
            ),
            # Send to Logfire (must be before the final renderer according to docs)
            logfire.StructlogProcessor(),
            # Render as JSON for ELK compatibility (final processor) with pretty printing
            structlog.processors.JSONRenderer(indent=2, ensure_ascii=False),
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
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Use colorlog for colored terminal output with JSON content
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(message)s%(reset)s',
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'magenta',
        },
        secondary_log_colors={},
        style='%'
    ))
    
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