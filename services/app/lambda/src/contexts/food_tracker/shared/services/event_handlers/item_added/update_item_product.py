from src.contexts.food_tracker.shared.adapters.internal_providers.products_catalog.api import (
    ProductsCatalogProvider,
)
from src.contexts.food_tracker.shared.domain.events.events import ItemAdded
from src.contexts.food_tracker.shared.services.uow import UnitOfWork


async def update_item_product(
    event: ItemAdded,
    uow: UnitOfWork,
) -> None:
    """Update the item's product.

    Args:
        event: :class`ItemAdded <..domain.events.ItemAdded>` instance.
        uow: :class`UnitOfWork <..service.async_uow.UnitOfWork.` instance.

    Returns:
        None
    """
    async with uow:
        item = await uow.items.get(event.item_id)
        if item.product_id is not None:
            return
        if item.is_barcode_unique:
            products_data = await ProductsCatalogProvider.query(
                filter={"barcode": item.barcode}
            )
            if products_data:
                product = products_data[0]
                if product.get("is_food") is False:
                    item.delete()
                else:
                    item.is_food = product.get("is_food")
                    item.product_id = product.get("id")
            else:
                item.product_id = None
        else:
            top_similar_names = await ProductsCatalogProvider.search_by_name(
                item.description
            )
            if top_similar_names:
                top_3 = top_similar_names[:3]
                products_data = await ProductsCatalogProvider.query(
                    filter={"name": top_3}
                )
                ordered_products_data = []
                for name in top_3:
                    for product in products_data:
                        if product.get("name") == name:
                            ordered_products_data.append(product)
                            break
                if not products_data:
                    return
                item.is_food = ordered_products_data[0].get("is_food")
                item.product_id = ordered_products_data[0].get("id")
                item.ids_of_products_with_similar_names = [
                    i.get("id") for i in ordered_products_data
                ]
            else:
                item.product_id = None
        await uow.items.persist(item)
        await uow.commit()
