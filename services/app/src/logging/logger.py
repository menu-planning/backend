import logging
import os
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.config import dictConfig
from typing import Any

import structlog
from structlog.types import EventDict
from pythonjsonlogger import json as pythonjsonlogger  # type: ignore


# ContextVar for task-safe correlation id
correlation_id_ctx: ContextVar[str] = ContextVar(
    "correlation_id", default=str(uuid.UUID("00000000-0000-0000-0000-000000000000"))
)


class RequestContextFilter(logging.Filter):
    """
    Filter to automatically inject correlation_id into every log record.
    """

    def __init__(self, name: str) -> None:
        super().__init__(name=name)

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.correlation_id = correlation_id_ctx.get()
        except LookupError:
            record.correlation_id = str(uuid.UUID("00000000-0000-0000-0000-000000000000"))
        return True


class ElkJsonFormatter(pythonjsonlogger.JsonFormatter):
    """
    JSON formatter compatible with ELK/CloudWatch.
    Adds timestamp, level, logger name and correlation_id.
    """

    def add_fields(
        self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["@timestamp"] = datetime.now(timezone.utc).isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        if not log_record.get("correlation_id"):
            log_record["correlation_id"] = correlation_id_ctx.get()


def add_correlation_id(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Structlog processor to add correlation_id from context.
    """
    try:
        event_dict["correlation_id"] = correlation_id_ctx.get()
    except LookupError:
        event_dict["correlation_id"] = str(uuid.UUID("00000000-0000-0000-0000-000000000000"))
    return event_dict


def add_timestamp(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Structlog processor to add timestamp in ELK-compatible format.
    """
    event_dict["@timestamp"] = datetime.now(timezone.utc).isoformat()
    return event_dict


def add_level_and_logger(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Structlog processor to add level and logger name for ELK compatibility.
    """
    event_dict["level"] = method_name.upper()
    event_dict["logger"] = logger.name if hasattr(logger, 'name') else "structlog"
    return event_dict


class StructlogFactory:
    """
    Factory for creating and configuring structlog loggers.
    Integrates with existing correlation ID system for consistency.
    """
    
    _configured = False
    
    @classmethod
    def configure(
        cls,
        log_level: str = os.getenv("LOG_LEVEL", "DEBUG"),
    ) -> None:
        """
        Configure structlog to work alongside existing logging system.
        """
        if cls._configured:
            return
            
        # Configure structlog processors for ELK compatibility
        structlog.configure(
            processors=[
                add_correlation_id,           # Add correlation_id from context
                add_timestamp,                # Add @timestamp for ELK
                add_level_and_logger,         # Add level and logger name
                structlog.processors.add_log_level,  # Ensure log level is available
                structlog.processors.JSONRenderer(),  # JSON output for ELK compatibility
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        cls._configured = True
    
    @classmethod
    def get_logger(cls, name: str = "structlog") -> structlog.BoundLogger:
        """
        Get a structlog logger instance.
        """
        if not cls._configured:
            cls.configure()
        return structlog.get_logger(name)


class LoggerFactory:
    """
    Logger factory responsible for configuring logging.
    """

    _configured = False
    _logger: logging.Logger | None = None

    @classmethod
    def configure(
        cls,
        logger_name: str = "app",
        log_level: str = os.getenv("LOG_LEVEL", "DEBUG"),
    ) -> None:
        """
        Configure the logger. Can be called multiple times safely.
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
        if cls._logger is None:
            cls.configure()
        return cls._logger # type: ignore


class LazyLogger:
    """
    Lazy wrapper around LoggerFactory to allow easy `logger.info()` usage.
    """

    def __getattr__(self, name: str) -> Any:
        return getattr(LoggerFactory.get_logger(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(LoggerFactory.get_logger(), name, value)


# Exposed lazy logger for easy imports (maintains backward compatibility)
logger: logging.Logger = LazyLogger() # type: ignore

# Exposed structlog logger for new structured logging usage
structlog_logger = StructlogFactory.get_logger


# Helper methods for correlation id (maintains existing API)
def set_correlation_id(correlation_id: str) -> None:
    correlation_id_ctx.set(correlation_id)


def generate_correlation_id() -> str:
    cid = uuid.uuid4().hex[:8]
    correlation_id_ctx.set(cid)
    return cid
