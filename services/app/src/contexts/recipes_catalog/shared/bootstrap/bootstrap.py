from collections.abc import Coroutine
from functools import partial

from src.contexts.recipes_catalog.shared.domain import commands, events
from src.contexts.recipes_catalog.shared.services import (
    command_handlers as cmd_handlers,
)
from src.contexts.recipes_catalog.shared.services import event_handlers as evt_handlers
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
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
    injected_event_handlers: dict[type[SeedworkEvent], list[Coroutine]] = {
        events.RecipeCreated: [
            evt_handlers.recipe_created_place_holder,
        ],
        events.CategoryCreated: [
            evt_handlers.category_created_place_holder,
        ],
        events.MealPlanningCreated: [
            evt_handlers.meal_planning_created_place_holder,
        ],
    }

    injected_command_handlers: dict[type[SeedworkCommand], Coroutine] = {
        commands.CreateRecipe: partial(cmd_handlers.create_recipe, uow=uow),
        commands.DeleteRecipe: partial(cmd_handlers.delete_recipe, uow=uow),
        commands.UpdateRecipe: partial(cmd_handlers.update_recipe, uow=uow),
        commands.RateRecipe: partial(cmd_handlers.rate_recipe, uow=uow),
        commands.CreateDietType: partial(cmd_handlers.create_diet_type, uow=uow),
        commands.DeleteDietType: partial(cmd_handlers.delete_diet_type, uow=uow),
        commands.UpdateDietType: partial(cmd_handlers.update_diet_type, uow=uow),
        commands.CreateCategory: partial(cmd_handlers.create_category, uow=uow),
        commands.DeleteCategory: partial(cmd_handlers.delete_category, uow=uow),
        commands.CreateMealPlanning: partial(
            cmd_handlers.create_meal_planning, uow=uow
        ),
        commands.DeleteMealPlanning: partial(
            cmd_handlers.delete_meal_planning, uow=uow
        ),
        commands.UpdateCategory: partial(cmd_handlers.update_category, uow=uow),
        commands.UpdateMealPlanning: partial(
            cmd_handlers.update_meal_planning, uow=uow
        ),
    }
    return MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )
