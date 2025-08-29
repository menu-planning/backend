"""
IAM Core Module

Contains the business logic, repositories, and services for IAM operations.
"""

# Bootstrap
from src.contexts.iam.core.bootstrap.bootstrap import bootstrap
from src.contexts.iam.core.bootstrap.container import Container

# Domain
from src.contexts.iam.core.domain.commands import (
    AssignRoleToUser,
    CreateUser,
    RemoveRoleFromUser,
)
from src.contexts.iam.core.domain.enums import Permission, Role
from src.contexts.iam.core.domain.events import UserCreated
from src.contexts.iam.core.domain.root_aggregate.user import User
from src.contexts.iam.core.domain.value_objects.role import Role as RoleValueObject

# Services
from src.contexts.iam.core.services import command_handlers, event_handlers
from src.contexts.iam.core.services.uow import UnitOfWork

__all__ = [
    "AssignRoleToUser",
    "Container",
    "CreateUser",
    "Permission",
    "RemoveRoleFromUser",
    "Role",
    "RoleValueObject",
    "UnitOfWork",
    "User",
    "UserCreated",
    "bootstrap",
    "command_handlers",
    "event_handlers",
]
