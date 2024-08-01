from src.contexts.receipt_tracker.shared.domain.commands import (
    CreateSellerAndUpdateWithScrapedData,
)
from src.contexts.receipt_tracker.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException


async def create_seller_and_update_receipt_with_scraped_data(
    cmd: CreateSellerAndUpdateWithScrapedData, uow: UnitOfWork
) -> None:
    """Update receipt data and create seller acording to scraper result.

    Args:
        cmd: A :class:`CreateSellerAndUpdateWithScrapedData <..domain.commands.CreateSellerAndUpdateWithScrapedData>` instance.
        uow: A :class:`UnitOfWork <..services.async_uow.UnitOfWork>` instance.

    Returns:
        None
    """
    async with uow:
        try:
            seller = await uow.sellers.get(cmd.seller.cnpj)
        except EntityNotFoundException:
            seller = cmd.seller
            await uow.sellers.add(seller)
        try:
            receipt = await uow.receipts.get(cmd.cfe_key)
            if not receipt.scraped:
                receipt.date = cmd.date
                receipt.seller_id = cmd.seller.cnpj
                receipt.add_items(cmd.items)
        finally:
            await uow.receipts.persist_all()
            await uow.commit()
