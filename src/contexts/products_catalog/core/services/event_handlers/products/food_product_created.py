from src.contexts.products_catalog.core.domain.events import FoodProductCreated


async def publish_scrape_image_for_new_product(
    event: FoodProductCreated,
) -> None:
    # TODO: implement this function
    raise NotImplementedError("Not implemented yet")


async def publish_email_admin_of_new_food_product(
    event: FoodProductCreated,
) -> None:
    # TODO: implement this function
    raise NotImplementedError("Not implemented yet")
