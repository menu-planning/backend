from src.contexts.products_catalog.core.adapters.api_schemas.commands.products.api_add_house_input_and_create_product_if_needed import (
    ApiAddHouseInputAndCreateProductIfNeeded,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def add_house_input_to_is_food_registry(
    barcode: str,
    house_id: str,
    is_food: bool,
) -> None:
    api = ApiAddHouseInputAndCreateProductIfNeeded(
        barcode=barcode,
        house_id=house_id,
        is_food=is_food,
    )
    bus: MessageBus = Container().bootstrap()
    await bus.handle(api.to_domain())
