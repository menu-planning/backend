"""Commands encapsulating IAM intents (user creation, role changes)."""
from attrs import frozen
from src.contexts.iam.core.domain.value_objects.role import Role
from src.contexts.seedwork.domain.commands.command import Command


@frozen
class CreateUser(Command):
    """Command to create a new user in the IAM system.
    
    Args:
        user_id: Unique identifier for the user (UUID v4).
    """
    user_id: str


@frozen
class AssignRoleToUser(Command):
    """Command to assign a role to an existing user.
    
    Args:
        user_id: Unique identifier of the target user (UUID v4).
        role: Role value object to assign to the user.
    """
    user_id: str
    role: Role


@frozen
class RemoveRoleFromUser(Command):
    """Command to remove a role from an existing user.
    
    Args:
        user_id: Unique identifier of the target user (UUID v4).
        role: Role value object to remove from the user.
    """
    user_id: str
    role: Role
