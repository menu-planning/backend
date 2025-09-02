"""Message bus bootstrap: wire commands/events to their handlers for recipes_catalog."""
from collections.abc import Coroutine
from functools import partial

import src.contexts.recipes_catalog.core.domain.client.commands as client_commands
import src.contexts.recipes_catalog.core.domain.client.events as client_events
import src.contexts.recipes_catalog.core.domain.meal.commands as meal_commands
import src.contexts.recipes_catalog.core.domain.meal.events as meal_events
import src.contexts.recipes_catalog.core.services.client.command_handlers as client_cmd_handlers
import src.contexts.recipes_catalog.core.services.client.event_handlers as client_evt_handlers
import src.contexts.recipes_catalog.core.services.meal.command_handlers as meal_cmd_handlers
import src.contexts.recipes_catalog.core.services.meal.event_handlers as meal_evt_handlers
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.domain.commands.command import (
    Command as SeedworkCommand,
)
from src.contexts.seedwork.domain.event import Event as SeedworkEvent
from src.contexts.shared_kernel.services.messagebus import MessageBus


def bootstrap(
    uow: UnitOfWork,
) -> MessageBus:
    """Wire commands and events to their handlers for recipes_catalog domain.

    Args:
        uow: Unit of work instance for transaction management.

    Returns:
        MessageBus: Configured message bus with all handlers wired.

    Notes:
        Maps domain commands and events to their respective handlers.
        All handlers receive the unit of work for database operations.
    """
    injected_event_handlers: dict[type[SeedworkEvent], list[partial[Coroutine]]] = {
        meal_events.MealDeleted: [
            partial(
                meal_evt_handlers.remove_meals_from_menu,
                uow=uow,
            ),
        ],
        meal_events.UpdatedAttrOnMealThatReflectOnMenu: [
            partial(
                meal_evt_handlers.update_menu_meals,
                uow=uow,
            ),
        ],
        client_events.MenuDeleted: [
            partial(
                client_evt_handlers.delete_related_meals,
                uow=uow,
            ),
        ],
        client_events.MenuMealAddedOrRemoved: [
            partial(
                client_evt_handlers.update_menu_id_on_meals,
                uow=uow,
            ),
        ],
    }

    injected_command_handlers: dict[type[SeedworkCommand], partial[Coroutine]] = {
        meal_commands.CreateRecipe: partial(meal_cmd_handlers.create_recipe_handler, uow=uow),
        meal_commands.CopyRecipe: partial(meal_cmd_handlers.copy_recipe_handler, uow=uow),
        meal_commands.DeleteRecipe: partial(meal_cmd_handlers.delete_recipe_handler, uow=uow),
        meal_commands.UpdateRecipe: partial(meal_cmd_handlers.update_recipe_handler, uow=uow),
        meal_commands.CreateMeal: partial(meal_cmd_handlers.create_meal_handler, uow=uow),
        meal_commands.DeleteMeal: partial(meal_cmd_handlers.delete_meal_handler, uow=uow),
        meal_commands.UpdateMeal: partial(meal_cmd_handlers.update_meal_handler, uow=uow),
        meal_commands.CopyMeal: partial(meal_cmd_handlers.copy_meal_handler, uow=uow),
        client_commands.CreateClient: partial(client_cmd_handlers.create_client_handler, uow=uow),
        client_commands.DeleteClient: partial(client_cmd_handlers.delete_client_handler, uow=uow),
        client_commands.UpdateClient: partial(client_cmd_handlers.update_client_handler, uow=uow),
        client_commands.CreateMenu: partial(client_cmd_handlers.create_menu_handler, uow=uow),
        client_commands.DeleteMenu: partial(client_cmd_handlers.delete_menu_handler, uow=uow),
        client_commands.UpdateMenu: partial(client_cmd_handlers.update_menu_handler, uow=uow),
    }
    return MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )
