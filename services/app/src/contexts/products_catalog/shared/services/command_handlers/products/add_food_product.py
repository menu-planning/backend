from src.contexts.products_catalog.shared.domain.commands.products.add_food_product_bulk import (
    AddFoodProductBulk,
)
from src.contexts.products_catalog.shared.domain.entities.product import Product
from src.contexts.products_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from src.logging.logger import logger


async def add_new_food_product(cmd: AddFoodProductBulk, uow: UnitOfWork) -> list[str]:
    async with uow:
        products_ids = []
        for c in cmd.add_product_cmds:
            if c.barcode:
                products = await uow.products.query(filter={"barcode": c.barcode})
                try:
                    next(
                        p
                        for p in products
                        if p.source_id == c.source_id and p.barcode == c.barcode
                    )
                    raise BadRequestException(
                        f'Product with barcode "{c.barcode}" and source "{c.source_id}" already exists.'
                    )
                except StopIteration:
                    pass
            c = Product.add_food_product(
                source_id=c.source_id,
                name=c.name,
                category_id=c.category_id,
                parent_category_id=c.parent_category_id,
                nutri_facts=c.nutri_facts,
                ingredients=c.ingredients,
                package_size=c.package_size,
                package_size_unit=c.package_size_unit,
                json_data=c.json_data,
                food_group_id=c.food_group_id,
                process_type_id=c.process_type_id,
                score=c.score,
                brand_id=c.brand_id,
                barcode=c.barcode,
                image_url=c.image_url,
            )
            await uow.products.add(c)
            products_ids.append(c.id)
        await uow.commit()
    return products_ids
