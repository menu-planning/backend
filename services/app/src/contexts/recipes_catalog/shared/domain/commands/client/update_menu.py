from typing import Any

from attrs import frozen

from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class UpdateMenu(Command):
    # client_id: str
    menu_id: str
    updates: dict[str, Any]
