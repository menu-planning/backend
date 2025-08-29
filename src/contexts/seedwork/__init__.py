"""
Seedwork Context

Foundation classes and utilities used across all contexts.
"""

# Shared Domain
from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.seedwork.shared.domain.entity import Entity
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject

# Shared Endpoints
from .shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)

# Shared Services
from .shared.services.uow import UnitOfWork

__all__ = [
    "Command",
    "Entity",
    "Event",
    "SeedUser",
    "UnitOfWork",
    "ValueObject",
    "lambda_exception_handler",
]
