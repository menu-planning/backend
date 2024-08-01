from collections.abc import Mapping
from datetime import datetime

from attrs import field, frozen
from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.shared_kernel.domain.value_objects import Amount


@frozen(hash=True)
class AddItem(Command):
    house_ids: list[str] = field(hash=False)
    date: datetime
    amount: Amount = field(
        converter=lambda x: Amount(**x) if x and isinstance(x, Mapping) else x
    )
    product_id: str | None = None
    description: str | None = None
    price_per_unit: float | None = None
    barcode: str | None = None
    cfe_key: str | None = None
    is_food: bool | None = None
