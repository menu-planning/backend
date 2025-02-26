from collections.abc import Coroutine
from functools import partial

from src.contexts.recipes_catalog.shared.domain import commands, events
from src.contexts.recipes_catalog.shared.services import \
    command_handlers as cmd_handlers
from src.contexts.recipes_catalog.shared.services import \
    event_handlers as evt_handlers
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.commands.command import \
    Command as SeedworkCommand
from src.contexts.seedwork.shared.domain.event import Event as SeedworkEvent
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.rabbitmq.aio_pika_manager import AIOPikaManager


def bootstrap(
    uow: UnitOfWork,
    aio_pika_manager: AIOPikaManager,
) -> MessageBus:
    injected_event_handlers: dict[type[SeedworkEvent], list[Coroutine]] = {
        # Meal events
        events.MealDeleted: [
            partial(
                evt_handlers.remove_meals_from_menu,
                uow=uow,
            ),
        ],
        events.UpdatedAttrOnMealThatReflectOnMenu: [
            partial(
                evt_handlers.update_meals_on_menu,
                uow=uow,
            ),
        ],
        # Menu events
        events.MenuDeleted: [
            partial(
                evt_handlers.delete_related_meals,
                uow=uow,
            ),
        ],
        events.MenuMealsChanged: [
            partial(
                evt_handlers.update_menu_id_on_meals,
                uow=uow,
            ),
        ],
    }

    injected_command_handlers: dict[type[SeedworkCommand], Coroutine] = {
        # Recipe commands
        commands.CreateRecipe: partial(cmd_handlers.create_recipe_handler, uow=uow),
        commands.CopyRecipe: partial(cmd_handlers.copy_recipe_handler, uow=uow),
        commands.DeleteRecipe: partial(cmd_handlers.delete_recipe_handler, uow=uow),
        commands.UpdateRecipe: partial(cmd_handlers.update_recipe_handler, uow=uow),
        commands.RateRecipe: partial(cmd_handlers.rate_recipe_handler, uow=uow),
        # Tag commands
        commands.CreateTag: partial(cmd_handlers.create_tag_handler, uow=uow),
        commands.DeleteTag: partial(cmd_handlers.delete_tag_handler, uow=uow),
        # Meal commands
        commands.AddRecipeToMeal: partial(cmd_handlers.add_recipe_to_meal_handler, uow=uow),
        commands.RemoveRecipeFromMeal: partial(
            cmd_handlers.remove_recipe_from_meal_handler, uow=uow
        ),
        commands.CreateMeal: partial(cmd_handlers.create_meal_handler, uow=uow),
        commands.DeleteMeal: partial(cmd_handlers.delete_meal_handler, uow=uow),
        commands.UpdateMeal: partial(cmd_handlers.update_meal_handler, uow=uow),
        commands.CopyMeal: partial(cmd_handlers.copy_meal_handler, uow=uow),
        commands.CopyRecipeToMeal: partial(
            cmd_handlers.copy_recipe_to_meal_handler, uow=uow
        ),
        commands.UpdateRecipeOnMeal: partial(
            cmd_handlers.update_recipe_on_meal_handler, uow=uow
        ),
        # Menu commands
        commands.CreateMenu: partial(cmd_handlers.create_menu_handler, uow=uow),
        commands.DeleteMenu: partial(cmd_handlers.delete_menu_handler, uow=uow),
        commands.UpdateMenu: partial(cmd_handlers.update_menu_handler, uow=uow),
    }
    return MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )
