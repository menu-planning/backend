from src.contexts.products_catalog.shared.domain.commands.products.update import (
    UpdateProduct,
)
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def udpate_existing_product(cmd: UpdateProduct, uow: UnitOfWork) -> None:
    async with uow:
        product = await uow.products.get(cmd.product_id)
        product.update_properties(**cmd.updates)
        await uow.products.persist(product)
        await uow.commit()
