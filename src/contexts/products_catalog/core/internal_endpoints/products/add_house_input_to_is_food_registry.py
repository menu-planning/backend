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
    """Execute the add house input to food registry use case.

    Args:
        barcode: Product barcode identifier.
        house_id: UUID v4 of the house.
        is_food: Whether the product is classified as food.

    Returns:
        None: Command executed successfully.

    Events:
        HouseInputAdded: Emitted when house input is successfully added.

    Idempotency:
        No. Duplicate calls create multiple house inputs.

    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.

    Side Effects:
        Publishes domain events, creates product if needed, persists house input.
    """
    api = ApiAddHouseInputAndCreateProductIfNeeded(
        barcode=barcode,
        house_id=house_id,
        is_food=is_food,
    )
    bus: MessageBus = Container().bootstrap()
    await bus.handle(api.to_domain())
