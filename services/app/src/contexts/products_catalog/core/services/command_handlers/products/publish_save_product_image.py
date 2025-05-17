from src.contexts.products_catalog.core.domain.commands.products.add_image import (
    AddProductImage,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def publish_save_product_image(
    cmd: AddProductImage,
    uow: UnitOfWork,
) -> None:
    # TODO: implement this function
    raise NotImplementedError("Not implemented yet")
