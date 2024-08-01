from collections.abc import Coroutine
from functools import partial

from src.contexts.food_tracker.shared.domain import commands
from src.contexts.food_tracker.shared.domain.events import events
from src.contexts.food_tracker.shared.services import command_handlers as cmd_handlers
from src.contexts.food_tracker.shared.services import event_handlers as evt_handlers
from src.contexts.food_tracker.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.rabbitmq.aio_pika_manager import AIOPikaManager


def bootstrap(
    uow: UnitOfWork,
    aio_pika_manager: AIOPikaManager,
) -> MessageBus:
    injected_event_handlers: dict[type[events.Event], list[Coroutine]] = {
        events.ReceiptCreated: [
            partial(
                evt_handlers.add_receipt_to_and_retrieve_items_from_receipt_tracker,
                uow=uow,
            ),
            partial(
                evt_handlers.notify_admin_new_receipt,
                aio_pika_manager=aio_pika_manager,
            ),
        ],
        events.ItemAdded: [
            partial(
                evt_handlers.update_item_product,
                uow=uow,
            )
        ],
        events.WrongProductAllocated: [
            partial(
                evt_handlers.notify_admin_wrong_product_allocated,
                aio_pika_manager=aio_pika_manager,
            )
        ],
        events.ItemIsFoodChanged: [
            partial(
                evt_handlers.add_house_input_and_create_product_if_needed,
                uow=uow,
            )
        ],
        events.ProductNotFound: [
            partial(
                evt_handlers.notify_admin_product_not_found,
                aio_pika_manager=aio_pika_manager,
            )
        ],
    }

    injected_command_handlers: dict[type[Command], Coroutine] = {
        commands.CreateHouse: partial(cmd_handlers.create_house, uow=uow),
        commands.ChangeHouseName: partial(cmd_handlers.change_house_name, uow=uow),
        commands.DiscardHouses: partial(cmd_handlers.discard_houses, uow=uow),
        commands.AddReceipt: partial(cmd_handlers.add_receipt, uow=uow),
        commands.AddItemBulk: partial(cmd_handlers.add_item_bulk, uow=uow),
        commands.AddItem: partial(cmd_handlers.add_item, uow=uow),
        commands.DiscardItems: partial(cmd_handlers.discard_items, uow=uow),
        commands.UpdateItem: partial(cmd_handlers.update_item, uow=uow),
        commands.InviteMember: partial(cmd_handlers.invite_member, uow=uow),
        commands.RemoveMember: partial(cmd_handlers.remove_member, uow=uow),
        commands.InviteNutritionist: partial(cmd_handlers.invite_nutritionist, uow=uow),
        commands.RemoveNutritionist: partial(cmd_handlers.remove_nutritionist, uow=uow),
    }
    return MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )
