from typing import Any

from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class CreateClassification(Command):
    name: str
    author_id: str
    description: str | None = None


@frozen(kw_only=True)
class DeleteClassification(Command):
    id: str


@frozen(kw_only=True)
class UpdateClassification(Command):
    id: str
    updates: dict[str, Any]
