from typing import Any

from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class CreateTag(Command):
    name: str
    author_id: str
    description: str | None = None


@frozen(kw_only=True)
class DeleteTag(Command):
    id: str


@frozen(kw_only=True)
class UpdateTag(Command):
    id: str
    updates: dict[str, Any]
