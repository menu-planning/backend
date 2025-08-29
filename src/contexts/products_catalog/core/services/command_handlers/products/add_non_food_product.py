from attrs import asdict

from src.contexts.products_catalog.core.domain.commands import AddNonFoodProduct
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestError


async def add_new_non_food_product(cmd: AddNonFoodProduct, uow: UnitOfWork) -> None:
    async with uow:
        products = await uow.products.query(filters={"barcode": cmd.barcode})
        try:
            next(
                p
                for p in products
                if p.source_id == cmd.source_id and p.barcode == cmd.barcode
            )
            raise BadRequestError(
                f'Product with barcode "{cmd.barcode}" and source "{cmd.source_id}" already exists.'
            )
        except StopIteration:
            pass
        product = Product.add_non_food_product(**asdict(cmd))
        await uow.products.add(product)
        await uow.commit()
