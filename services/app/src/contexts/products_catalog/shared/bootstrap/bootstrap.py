from collections.abc import Coroutine
from functools import partial

from src.contexts.products_catalog.shared.domain import commands, events
from src.contexts.products_catalog.shared.services import (
    command_handlers as cmd_handlers,
)
from src.contexts.products_catalog.shared.services import event_handlers as evt_handlers
from src.contexts.products_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.commands.command import (
    Command as SeedworkCommand,
)
from src.contexts.seedwork.shared.domain.event import Event as SeedworkEvent
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.rabbitmq.aio_pika_manager import AIOPikaManager


def bootstrap(
    uow: UnitOfWork,
    aio_pika_manager: AIOPikaManager,
) -> MessageBus:
    injected_event_handlers: dict[type[SeedworkEvent], list[partial[Coroutine]]] = {
        events.FoodProductCreated: [
            partial(
                evt_handlers.publish_scrape_image_for_new_product,
                aio_pika_manager=aio_pika_manager,
            ),
            partial(
                evt_handlers.publish_email_admin_of_new_food_product,
                aio_pika_manager=aio_pika_manager,
            ),
        ],
    }

    injected_command_handlers: dict[type[SeedworkCommand], partial[Coroutine]] = {
        commands.AddFoodProductBulk: partial(
            cmd_handlers.add_new_food_product, uow=uow
        ),
        commands.AddNonFoodProduct: partial(
            cmd_handlers.add_new_non_food_product, uow=uow
        ),
        commands.AddHouseInputAndCreateProductIfNeeded: partial(
            cmd_handlers.add_house_input_and_create_product_if_needed,
            uow=uow,
        ),
        commands.UpdateProduct: partial(cmd_handlers.udpate_existing_product, uow=uow),
        commands.AddProductImage: partial(
            cmd_handlers.publish_save_product_image,
            uow=uow,
            aio_pika_manager=aio_pika_manager,
        ),
        commands.CreateSource: partial(cmd_handlers.create_source, uow=uow),
        commands.DeleteSource: partial(cmd_handlers.delete_source, uow=uow),
        commands.UpdateSource: partial(cmd_handlers.update_source, uow=uow),
        commands.CreateBrand: partial(cmd_handlers.create_brand, uow=uow),
        commands.DeleteBrand: partial(cmd_handlers.delete_brand, uow=uow),
        commands.UpdateBrand: partial(cmd_handlers.update_brand, uow=uow),
        commands.CreateCategory: partial(cmd_handlers.create_category, uow=uow),
        commands.DeleteCategory: partial(cmd_handlers.delete_category, uow=uow),
        commands.UpdateCategory: partial(cmd_handlers.update_category, uow=uow),
        commands.CreateParentCategory: partial(
            cmd_handlers.create_parent_category, uow=uow
        ),
        commands.DeleteParentCategory: partial(
            cmd_handlers.delete_parent_category, uow=uow
        ),
        commands.UpdateParentCategory: partial(
            cmd_handlers.update_parent_category, uow=uow
        ),
        commands.CreateFoodGroup: partial(cmd_handlers.create_food_group, uow=uow),
        commands.DeleteFoodGroup: partial(cmd_handlers.delete_food_group, uow=uow),
        commands.UpdateFoodGroup: partial(cmd_handlers.update_food_group, uow=uow),
        commands.CreateProcessType: partial(cmd_handlers.create_process_type, uow=uow),
        commands.DeleteProcessType: partial(cmd_handlers.delete_process_type, uow=uow),
        commands.UpdateProcessType: partial(cmd_handlers.update_process_type, uow=uow),
    }
    return MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )
