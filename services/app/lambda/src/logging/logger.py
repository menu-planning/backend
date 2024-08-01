import logging
import os
import uuid
from contextvars import ContextVar
from datetime import datetime
from logging.config import dictConfig
from typing import Any

import colorlog
from pythonjsonlogger import jsonlogger


class RequestContextFilter(logging.Filter):
    """ "Provides correlation id parameter for the logger"""

    def __init__(self, name: str, correlation_id: str) -> None:
        super().__init__(name=name)
        self.correlation_id = correlation_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = self.correlation_id.get()
        return True


class ElkJsonFormatter(jsonlogger.JsonFormatter):
    """
    ELK stack-compatibile formatter
    """

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ):
        super().add_fields(log_record, record, message_dict)
        log_record["@timestamp"] = datetime.now().isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name


class LoggerFactory:
    _configured = False
    _logger = None

    @classmethod
    def configure(
        cls,
        logger_name="app",
        correlation_id=ContextVar(
            "correlation_id", default=uuid.UUID("00000000-0000-0000-0000-000000000000")
        ),
        environment=os.getenv("APP_ENVIRONMENT", "development"),
        log_level=os.getenv(
            "LOG_LEVEL",
            (
                "DEBUG"
                if os.getenv("APP_ENVIRONMENT", "development") == "development"
                else "INFO"
            ),
        ),
    ):
        if environment == "development":
            logging_config = {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "colored": {
                        "()": "colorlog.ColoredFormatter",
                        "format": "%(log_color)s%(levelname)-8s | %(asctime)s | %(name)-12s | %(correlation_id)s | %(message)s",
                        "log_colors": {
                            "DEBUG": "white",
                            "INFO": "green",
                            "WARNING": "yellow",
                            "ERROR": "red",
                            "CRITICAL": "red,bold",
                        },
                    },
                },
                "handlers": {
                    "stdout": {
                        "class": "colorlog.StreamHandler",
                        "level": log_level,
                        "formatter": "colored",
                        "stream": "ext://sys.stdout",
                    },
                },
                "loggers": {
                    logger_name: {
                        "level": log_level,
                        "handlers": ["stdout"],
                        "propagate": False,
                    },
                },
            }
        else:
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
        cls._logger.correlation_id = correlation_id
        cls._logger.addFilter(
            RequestContextFilter(name=logger_name, correlation_id=correlation_id)
        )
        cls._configured = True

    @classmethod
    def get_logger(cls):
        if cls._logger is None:
            cls.configure()
        return cls._logger


class LazyLogger:
    def __getattr__(self, name):
        return getattr(LoggerFactory.get_logger(), name)

    def __setattr__(self, name, value):
        setattr(LoggerFactory.get_logger(), name, value)


# Creating the lazy logger instance
logger: logging.Logger = LazyLogger()
