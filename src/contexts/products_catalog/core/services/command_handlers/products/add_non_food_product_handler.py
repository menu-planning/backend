from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.products.add_non_food_product import (
    AddNonFoodProduct,
)
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.contexts.shared_kernel.domain.exceptions import BusinessRuleValidationError


async def add_new_non_food_product(cmd: AddNonFoodProduct, uow: UnitOfWork) -> None:
    """Execute the add non-food product use case.
    
    Args:
        cmd: Command containing non-food product data to create.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Raises:
        BusinessRuleValidationError: If product with same barcode and source exists.
    
    Idempotency:
        No. Duplicate calls with same barcode/source will raise validation error.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Creates new Product aggregate for non-food items.
    """
    async with uow:
        products = await uow.products.query(filters={"barcode": cmd.barcode})
        try:
            next(
                p
                for p in products
                if p.source_id == cmd.source_id and p.barcode == cmd.barcode
            )
            raise BusinessRuleValidationError(
                f'Product with barcode "{cmd.barcode}" and source "{cmd.source_id}" already exists.'
            )
        except StopIteration:
            pass
        product = Product.add_non_food_product(**asdict(cmd))
        await uow.products.add(product)
        await uow.commit()
