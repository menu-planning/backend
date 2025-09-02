from src.contexts.products_catalog.core.domain.events.food_product_created import (
    FoodProductCreated,
)


async def publish_scrape_image_for_new_product(
    event: FoodProductCreated,
) -> None:
    """Handle image scraping for newly created food products.
    
    Args:
        event: FoodProductCreated event containing product information.
    
    Returns:
        None: No return value.
    
    Raises:
        NotImplementedError: Function is not yet implemented.
    
    Notes:
        This handler will trigger image scraping workflows when implemented.
        Currently raises NotImplementedError.
    """
    # TODO: implement this function
    raise NotImplementedError("Not implemented yet")


async def publish_email_admin_of_new_food_product(
    event: FoodProductCreated,
) -> None:
    """Handle admin email notification for newly created food products.
    
    Args:
        event: FoodProductCreated event containing product information.
    
    Returns:
        None: No return value.
    
    Raises:
        NotImplementedError: Function is not yet implemented.
    
    Notes:
        This handler will send email notifications to administrators when
        new food products are created. Currently raises NotImplementedError.
    """
    # TODO: implement this function
    raise NotImplementedError("Not implemented yet")
