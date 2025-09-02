"""Configure structured logging for JSON output compatible with ELK/CloudWatch.

This module provides logging configuration for both stdlib logging and structlog,
standardizing timestamps, levels, logger names, and correlation IDs. It uses
ContextVar for thread-safe correlation ID propagation across async boundaries.

The module exports:
- LoggerFactory: Configure stdlib logging with JSON formatter
- StructlogFactory: Configure structlog for structured JSON output
- correlation_id_ctx: ContextVar for request-scoped correlation IDs
- Helper functions for correlation ID management
"""

import logging
import os
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime
from logging.config import dictConfig
from typing import Any

import structlog
from pythonjsonlogger import json as pythonjsonlogger
from structlog.types import EventDict

# ContextVar for task-safe correlation id
correlation_id_ctx: ContextVar[str] = ContextVar(
    "correlation_id", default=str(uuid.UUID("00000000-0000-0000-0000-000000000000"))
)


class RequestContextFilter(logging.Filter):
    """Inject correlation ID into log records from request context.

    Ensures all log records include a correlation_id attribute populated from
    the request-scoped ContextVar. Falls back to a default UUID if no context
    is available.

    Notes:
        Thread-safe via ContextVar. Used by LoggerFactory to add correlation
        tracking to stdlib logging output.
    """

    def __init__(self, name: str) -> None:
        """Initialize the filter with a logger name.

        Args:
            name: Logger name for the filter.
        """
        super().__init__(name=name)

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation_id to the log record.

        Args:
            record: The log record to process.

        Returns:
            True to keep the record.

        Notes:
            Sets record.correlation_id from ContextVar or default UUID.
        """
        try:
            record.correlation_id = correlation_id_ctx.get()
        except LookupError:
            record.correlation_id = str(
                uuid.UUID("00000000-0000-0000-0000-000000000000")
            )
        return True


class ElkJsonFormatter(pythonjsonlogger.JsonFormatter):
    """Format log records as JSON compatible with ELK stack and CloudWatch.

    Extends python-json-logger to add standardized fields: @timestamp (ISO 8601),
    level, logger name, and correlation_id. Ensures consistent JSON structure
    across all log outputs.

    Notes:
        Uses UTC timestamps. Adds correlation_id from ContextVar if not present.
    """

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Add standard fields to the JSON log record.

        Args:
            log_record: The JSON record being constructed.
            record: The original stdlib log record.
            message_dict: Additional event values from the log call.

        Notes:
            Adds @timestamp, level, logger, and correlation_id fields.
            Timestamp format: ISO 8601 in UTC.
        """
        super().add_fields(log_record, record, message_dict)
        log_record["@timestamp"] = datetime.now(UTC).isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        if not log_record.get("correlation_id"):
            log_record["correlation_id"] = correlation_id_ctx.get()


def add_correlation_id(
    logger: Any, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add correlation ID to structlog event data.

    Args:
        logger: The structlog logger instance.
        method_name: The log method name (e.g., "info", "error").
        event_dict: The event data dictionary.

    Returns:
        Event data with correlation_id field added.

    Notes:
        Falls back to default UUID if no correlation context available.
        Used as structlog processor for consistent correlation tracking.
    """
    try:
        event_dict["correlation_id"] = correlation_id_ctx.get()
    except LookupError:
        event_dict["correlation_id"] = str(
            uuid.UUID("00000000-0000-0000-0000-000000000000")
        )
    return event_dict


def add_timestamp(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add ISO-8601 timestamp to structlog event data.

    Args:
        logger: The structlog logger instance.
        method_name: The log method name.
        event_dict: The event data dictionary.

    Returns:
        Event data with @timestamp field added.

    Notes:
        Uses UTC timezone. Format: ISO 8601 string.
        Used as structlog processor for ELK compatibility.
    """
    event_dict["@timestamp"] = datetime.now(UTC).isoformat()
    return event_dict


def add_level_and_logger(
    logger: Any, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add log level and logger name to structlog event data.

    Args:
        logger: The structlog logger instance.
        method_name: The log method name (e.g., "info", "error").
        event_dict: The event data dictionary.

    Returns:
        Event data with level and logger fields added.

    Notes:
        Level is converted to uppercase. Logger name defaults to "structlog"
        if not available on logger instance.
        Used as structlog processor for consistent metadata.
    """
    event_dict["level"] = method_name.upper()
    event_dict["logger"] = logger.name if hasattr(logger, "name") else "structlog"
    return event_dict


class StructlogFactory:
    """Configure and provide structlog loggers with correlation ID support.

    Factory class that configures structlog for JSON output compatible with
    ELK stack. Integrates correlation ID system and standardizes log format.

    Notes:
        Idempotent configuration. Thread-safe via ContextVar usage.
        Configures processors for correlation_id, timestamp, level, and logger.
    """

    _configured = False

    @classmethod
    def configure(
        cls,
        log_level: str = os.getenv("LOG_LEVEL", "DEBUG"),
    ) -> None:
        """Configure structlog for JSON output and correlation ID support.

        Args:
            log_level: Log level for the root logger.

        Notes:
            Idempotent: subsequent calls are no-ops.
            Configures processors for ELK compatibility and correlation tracking.
        """
        if cls._configured:
            return

        # Configure structlog processors for ELK compatibility
        structlog.configure(
            processors=[
                add_correlation_id,  # Add correlation_id from context
                add_timestamp,  # Add @timestamp for ELK
                add_level_and_logger,  # Add level and logger name
                structlog.processors.add_log_level,  # Ensure log level is available
                structlog.processors.JSONRenderer(),  # For ELK compatibility
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        cls._configured = True

    @classmethod
    def get_logger(cls, name: str = "structlog") -> structlog.BoundLogger:
        """Return a configured structlog logger instance.

        Args:
            name: Logger name to retrieve.

        Returns:
            A bound structlog logger with correlation ID support.

        Notes:
            Auto-configures structlog if not already configured.
        """
        if not cls._configured:
            cls.configure()
        return structlog.get_logger(name)


class LoggerFactory:
    """Configure stdlib logging for JSON output with correlation ID support.

    Factory class that sets up stdlib logging with JSON formatter compatible
    with ELK stack. Integrates with correlation ID system and provides
    consistent log format across the application.

    Notes:
        Idempotent configuration. Thread-safe via ContextVar usage.
        Configures both stdlib logging and structlog when called.
    """

    _configured = False
    _logger: logging.Logger | None = None

    @classmethod
    def configure(
        cls,
        logger_name: str = "app",
        log_level: str = os.getenv("LOG_LEVEL", "DEBUG"),
    ) -> None:
        """Configure stdlib logging for JSON output with correlation ID support.

        Args:
            logger_name: Application logger name to register.
            log_level: Log level for handlers and root logger.

        Notes:
            Idempotent: subsequent calls are no-ops.
            Configures JSON formatter, stdout handler, and correlation filter.
            Also configures structlog for consistency.
        """
        if cls._configured:
            return

        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": ElkJsonFormatter,
                },
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "level": log_level,
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                logger_name: {
                    "handlers": ["stdout"],
                    "level": log_level,
                    "propagate": False,
                },
            },
            # Ensure all other stdlib loggers (including structlog stdlib-backed ones)
            # emit to stdout as well. This captures modules that use
            # `logging.getLogger(__name__)` without explicitly using our factory.
            "root": {
                "level": log_level,
                "handlers": ["stdout"],
            },
        }

        dictConfig(logging_config)
        cls._logger = logging.getLogger(logger_name)
        cls._logger.addFilter(RequestContextFilter(name=logger_name))
        cls._configured = True

        # Also configure structlog when standard logging is configured
        StructlogFactory.configure(log_level=log_level)

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """Return the configured application logger.

        Returns:
            The named application logger with correlation ID support.

        Notes:
            Auto-configures logging if not already configured.
        """
        if cls._logger is None:
            cls.configure()
        assert cls._logger is not None
        return cls._logger

# Exposed structlog logger for new structured logging usage
structlog_logger = StructlogFactory.get_logger

# Helper methods for correlation id (maintains existing API)
def set_correlation_id(correlation_id: str) -> None:
    """Set the current correlation ID in request context.

    Args:
        correlation_id: Correlation ID to associate with subsequent logs.

    Notes:
        Thread-safe via ContextVar. Affects all loggers in current context.
    """
    correlation_id_ctx.set(correlation_id)


def generate_correlation_id() -> str:
    """Generate and set a short correlation ID for the current context.

    Returns:
        The generated 8-character hex correlation ID.

    Notes:
        Auto-sets the correlation ID in context. Format: 8-char hex string.
        Thread-safe via ContextVar.
    """
    cid = uuid.uuid4().hex[:8]
    correlation_id_ctx.set(cid)
    return cid
