from typing import Any

from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen
class UpdateProduct(Command):
    product_id: str
    updates: dict[str, Any]
