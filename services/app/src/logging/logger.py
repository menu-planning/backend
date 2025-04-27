import logging
import os
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.config import dictConfig
from typing import Any

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
        }

        dictConfig(logging_config)
        cls._logger = logging.getLogger(logger_name)
        cls._logger.addFilter(RequestContextFilter(name=logger_name))
        cls._configured = True

    @classmethod
    def get_logger(cls) -> logging.Logger:
        if cls._logger is None:
            cls.configure()
        return cls._logger


class LazyLogger:
    """
    Lazy wrapper around LoggerFactory to allow easy `logger.info()` usage.
    """

    def __getattr__(self, name: str) -> Any:
        return getattr(LoggerFactory.get_logger(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(LoggerFactory.get_logger(), name, value)


# Exposed lazy logger for easy imports
logger: logging.Logger = LazyLogger()


# Helper methods for correlation id
def set_correlation_id(correlation_id: str) -> None:
    correlation_id_ctx.set(correlation_id)


def generate_correlation_id() -> str:
    cid = uuid.uuid4().hex[:8]
    correlation_id_ctx.set(cid)
    return cid
