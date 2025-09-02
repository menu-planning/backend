from src.contexts.products_catalog.core.domain.commands.products.add_food_product_bulk import (
    AddFoodProductBulk,
)
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.contexts.shared_kernel.domain.exceptions import BusinessRuleValidationError


async def add_new_food_product(cmd: AddFoodProductBulk, uow: UnitOfWork) -> list[str]:
    """Execute the add food product bulk use case.
    
    Args:
        cmd: Command containing list of food products to create.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        list[str]: List of created product IDs.
    
    Raises:
        BusinessRuleValidationError: If product with same barcode and source exists.
    
    Events:
        FoodProductCreated: Emitted for each successfully created product.
    
    Idempotency:
        No. Duplicate calls with same barcode/source will raise validation error.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Creates new Product aggregates, publishes FoodProductCreated events.
    """
    async with uow:
        products_ids = []
        for c in cmd.add_product_cmds:
            if c.barcode:
                products = await uow.products.query(filters={"barcode": c.barcode})
                try:
                    next(
                        p
                        for p in products
                        if p.source_id == c.source_id and p.barcode == c.barcode
                    )
                    raise BusinessRuleValidationError(
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
