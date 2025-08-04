from src.contexts.products_catalog.core.domain.commands.products.add_house_input_and_create_product_if_needed import (
    AddHouseInputAndCreateProductIfNeeded,
)
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.products_catalog.core.domain.value_objects.is_food_votes import (
    IsFoodVotes,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def add_house_input_and_create_product_if_needed(
    cmd: AddHouseInputAndCreateProductIfNeeded, uow: UnitOfWork
) -> None:
    async with uow:
        products = await uow.products.query(
            filter={"barcode": cmd.barcode}, hide_undefined_auto_products=False
        )
        if not products and Product.is_barcode_unique(cmd.barcode):
            if cmd.is_food:
                product = Product.add_food_product(
                    source_id="auto",
                    name="",
                    category_id="",
                    parent_category_id="",
                    barcode=cmd.barcode,
                    is_food_votes=IsFoodVotes(is_food_houses={cmd.house_id}), # type: ignore
                )
            else:
                product = Product.add_non_food_product(
                    source_id="auto",
                    name="",
                    barcode=cmd.barcode,
                    is_food_votes=IsFoodVotes(is_not_food_houses={cmd.house_id}), # type: ignore
                )
            await uow.products.add(product)
        for product in products:
            product.add_house_input_to_is_food_registry(cmd.house_id, cmd.is_food) # type: ignore
            await uow.products.persist(product) # type: ignore
        await uow.commit()
