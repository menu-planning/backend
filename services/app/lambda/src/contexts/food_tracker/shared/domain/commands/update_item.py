from typing import Any

from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class UpdateItem(Command):
    item_id: str
    updates: dict[str, Any]
