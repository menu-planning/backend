from attrs import frozen
from src.contexts.iam.shared.domain.value_objects.role import Role
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen
class CreateUser(Command):
    user_id: str


@frozen
class AssignRoleToUser(Command):
    user_id: str
    role: Role


@frozen
class RemoveRoleFromUser(Command):
    user_id: str
    role: Role
