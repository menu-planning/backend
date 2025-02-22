from typing import Any

from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
    get_uow,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipe.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.db.database import get_db_session_factory


async def get(id: str) -> dict[str, Any]:
    """
    API endpoint for getting a recipe by its ID.

    Attributes:
        id (str): The unique identifier of the recipe to get.
        container (Container, optional): The dependency injection container
            to use. Defaults to the global container.

    Raises:
        EntityNotFoundException: If the recipe with the given ID does not exist.

    Returns:
        dict[str, Any]: The JSON representation of the recipe.
    """
    bus: MessageBus = fastapi_bootstrap(
        get_uow(get_db_session_factory()), get_aio_pika_manager()
    )
    uow: UnitOfWork
    async with bus.uow as uow:
        recipe = await uow.recipes.get(id)
        return ApiRecipe.from_domain(recipe).model_dump()
