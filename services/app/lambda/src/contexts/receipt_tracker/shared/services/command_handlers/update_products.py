from src.contexts.receipt_tracker.shared.domain.commands import UpdateProducts
from src.contexts.receipt_tracker.shared.services.uow import UnitOfWork


async def update_products(cmd: UpdateProducts, uow: UnitOfWork) -> None:
    """Update products in receipt with cfe_key.

    Args:
        cmd: A :class:`UpdateProducts <..domain.commands.UpdateProducts>` instance.
        uow: A :class:`UnitOfWork <..services.async_uow.UnitOfWork>` instance.

    Returns:
        None
    """
    async with uow:
        receipt = await uow.receipts.get(cmd.cfe_key)
        receipt.add_products_to_items(
            barcode_product_mapping=cmd.barcode_product_mapping
        )
        await uow.receipts.persist(receipt)
        await uow.commit()
