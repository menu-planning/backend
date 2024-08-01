from src.contexts.receipt_tracker.shared.adapters.internal_providers.products_catalog.api import (
    ProductsCatalogProvider,
)
from src.contexts.receipt_tracker.shared.domain.events import ItemsAddedToReceipt
from src.contexts.receipt_tracker.shared.domain.value_objects.item import Item
from src.contexts.receipt_tracker.shared.services.uow import UnitOfWork


async def add_products_to_items(
    event: ItemsAddedToReceipt,
    uow: UnitOfWork,
) -> None:
    """Add products to items in receipt.

    Args:
        event: :class`ItemsAddedToReceipt <..domain.events.ItemsAddedToReceipt>` instance.

    Returns:
        None
    """
    async with uow:
        products_to_add = {}
        receipt = await uow.receipts.get(event.cfe_key)
        for item in receipt.items:
            if Item.unique_barcode(item.barcode):
                products = await ProductsCatalogProvider.query(
                    filter={"barcode": item.barcode}
                )
            else:
                top_similar_names = await ProductsCatalogProvider.search_by_name(
                    item.description
                )
                if top_similar_names:
                    top_3 = top_similar_names[:3]
                    products = await ProductsCatalogProvider.query(
                        filter={"name": top_3[0]}
                    )
            if products:
                products_to_add[item.barcode] = products[0]
        receipt.add_products_to_items(products_to_add)
        await uow.receipts.persist(receipt)
        await uow.commit()
