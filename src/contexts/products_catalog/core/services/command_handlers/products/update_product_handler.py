from src.contexts.products_catalog.core.domain.commands.products.update import (
    UpdateProduct,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.logging.logger import StructlogFactory

logger = StructlogFactory.get_logger(__name__)


async def udpate_existing_product(cmd: UpdateProduct, uow: UnitOfWork) -> None:
    """Execute the update product use case.
    
    Args:
        cmd: Command containing product ID and updates to apply.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Events:
        UpdatedAttrOnProductThatReflectOnRecipeShoppingList: Emitted if updates affect recipes.
    
    Idempotency:
        Yes. Key: product_id + updates hash. Duplicate calls with same updates are safe.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Updates Product aggregate properties, may trigger recipe recalculation.
    """
    logger.info(
        "Updating product",
        action="update_product",
        product_id=cmd.product_id,
        update_fields=list(cmd.updates.keys())
    )

    try:
        async with uow:
            product = await uow.products.get(cmd.product_id)
            product.update_properties(**cmd.updates)
            await uow.products.persist(product)
            await uow.commit()

        logger.info(
            "Product updated successfully",
            action="update_product_success",
            product_id=cmd.product_id,
            updated_fields=list(cmd.updates.keys())
        )
    except Exception as e:
        logger.error(
            "Failed to update product",
            action="update_product_error",
            product_id=cmd.product_id,
            update_fields=list(cmd.updates.keys()),
            error_type=type(e).__name__,
            error_message=str(e),
            exc_info=True
        )
        raise
