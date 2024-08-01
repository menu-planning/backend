from src.contexts.products_catalog.shared.domain.commands import (
    AddHouseInputAndCreateProductIfNeeded,
)
from src.contexts.products_catalog.shared.domain.entities.product import Product
from src.contexts.products_catalog.shared.domain.value_objects.is_food_votes import (
    IsFoodVotes,
)
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


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
                    is_food_votes=IsFoodVotes(is_food_houses={cmd.house_id}),
                )
            else:
                product = Product.add_non_food_product(
                    source_id="auto",
                    name="",
                    barcode=cmd.barcode,
                    is_food_votes=IsFoodVotes(is_not_food_houses={cmd.house_id}),
                )
            await uow.products.add(product)
        for product in products:
            product.add_house_input_to_is_food_registry(cmd.house_id, cmd.is_food)
            await uow.products.persist(product)
        await uow.commit()
