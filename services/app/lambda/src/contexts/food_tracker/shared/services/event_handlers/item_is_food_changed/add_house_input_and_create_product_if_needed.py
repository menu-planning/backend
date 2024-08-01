from src.contexts.food_tracker.shared.adapters.internal_providers.products_catalog.api import (
    ProductsCatalogProvider,
)
from src.contexts.food_tracker.shared.domain.events.events import ItemIsFoodChanged
from src.contexts.food_tracker.shared.services.uow import UnitOfWork


async def add_house_input_and_create_product_if_needed(
    event: ItemIsFoodChanged,
    uow: UnitOfWork,
) -> None:
    async with uow:
        item = await uow.items.get(event.item_id)
    if item.is_barcode_unique:
        await ProductsCatalogProvider.add_house_input_and_create_product_if_needed(
            barcode=event.barcode,
            house_id=event.house_id,
            is_food=event.is_food,
        )
