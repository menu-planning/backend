"""Bootstrap wiring for Products Catalog message bus."""

from collections.abc import Coroutine
from functools import partial

from src.contexts.products_catalog.core.domain import events
from src.contexts.products_catalog.core.domain.commands import (
    classifications as classifications_commands,
)
from src.contexts.products_catalog.core.domain.commands import (
    products as products_commands,
)
from src.contexts.products_catalog.core.services.command_handlers import (
    classification as classifications_cmd_handlers,
)
from src.contexts.products_catalog.core.services.command_handlers import (
    products as product_cmd_handlers,
)
from src.contexts.products_catalog.core.services.event_handlers import (
    products as evt_handlers,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.domain.commands.command import (
    Command as SeedworkCommand,
)
from src.contexts.seedwork.domain.event import Event as SeedworkEvent
from src.contexts.shared_kernel.services.messagebus import MessageBus


def bootstrap(
    uow: UnitOfWork,
) -> MessageBus:
    """Configure and wire the Products Catalog message bus with handlers.
    
    Creates a MessageBus instance with all command and event handlers
    registered for the Products Catalog context. Handlers are injected
    with the provided UnitOfWork for transaction management.
    
    Args:
        uow: UnitOfWork instance for transaction boundary management.
    
    Returns:
        MessageBus: Configured message bus with all handlers registered.
    
    Notes:
        Event handlers: FoodProductCreated triggers image scraping and
        admin email notifications. Command handlers cover product CRUD
        operations and classification management (sources, brands, categories,
        food groups, process types, parent categories).
    """
    injected_event_handlers: dict[type[SeedworkEvent], list[partial[Coroutine]]] = {
        events.FoodProductCreated: [
            partial(
                evt_handlers.publish_scrape_image_for_new_product,
            ),
            partial(
                evt_handlers.publish_email_admin_of_new_food_product,
            ),
        ],
    }

    injected_command_handlers: dict[type[SeedworkCommand], partial[Coroutine]] = {
        products_commands.AddFoodProductBulk: partial(
            product_cmd_handlers.add_new_food_product, uow=uow
        ),
        products_commands.AddNonFoodProduct: partial(
            product_cmd_handlers.add_new_non_food_product, uow=uow
        ),
        products_commands.AddHouseInputAndCreateProductIfNeeded: partial(
            product_cmd_handlers.add_house_input_and_create_product_if_needed,
            uow=uow,
        ),
        products_commands.UpdateProduct: partial(product_cmd_handlers.udpate_existing_product, uow=uow),
        products_commands.AddProductImage: partial(
            product_cmd_handlers.publish_save_product_image,
            uow=uow,
        ),
        classifications_commands.CreateSource: partial(classifications_cmd_handlers.create_source, uow=uow),
        classifications_commands.DeleteSource: partial(classifications_cmd_handlers.delete_source, uow=uow),
        classifications_commands.UpdateSource: partial(classifications_cmd_handlers.update_source, uow=uow),
        classifications_commands.CreateBrand: partial(classifications_cmd_handlers.create_brand, uow=uow),
        classifications_commands.DeleteBrand: partial(classifications_cmd_handlers.delete_brand, uow=uow),
        classifications_commands.UpdateBrand: partial(classifications_cmd_handlers.update_brand, uow=uow),
        classifications_commands.CreateCategory: partial(classifications_cmd_handlers.create_category, uow=uow),
        classifications_commands.DeleteCategory: partial(classifications_cmd_handlers.delete_category, uow=uow),
        classifications_commands.UpdateCategory: partial(classifications_cmd_handlers.update_category, uow=uow),
        classifications_commands.CreateParentCategory: partial(
            classifications_cmd_handlers.create_parent_category, uow=uow
        ),
        classifications_commands.DeleteParentCategory: partial(
            classifications_cmd_handlers.delete_parent_category, uow=uow
        ),
        classifications_commands.UpdateParentCategory: partial(
            classifications_cmd_handlers.update_parent_category, uow=uow
        ),
        classifications_commands.CreateFoodGroup: partial(classifications_cmd_handlers.create_food_group, uow=uow),
        classifications_commands.DeleteFoodGroup: partial(classifications_cmd_handlers.delete_food_group, uow=uow),
        classifications_commands.UpdateFoodGroup: partial(classifications_cmd_handlers.update_food_group, uow=uow),
        classifications_commands.CreateProcessType: partial(classifications_cmd_handlers.create_process_type, uow=uow),
        classifications_commands.DeleteProcessType: partial(classifications_cmd_handlers.delete_process_type, uow=uow),
        classifications_commands.UpdateProcessType: partial(classifications_cmd_handlers.update_process_type, uow=uow),
    }
    return MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )
