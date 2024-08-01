import json
from typing import Any

from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
    get_uow,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipes.filter import (
    ApiRecipeFilter,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipes.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.db.database import get_db_session_factory


async def query(filter: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """
    API endpoint for getting a list of recipes.

    Attributes:
        filter (dict[str, Any], optional): A dictionary of filter criteria.
            Defaults to None.
        container (Container, optional): The dependency injection container
            to use. Defaults to the global container.

    Returns:
        list[dict[str, Any]]: A list of JSON representations of recipes.

    Raises:
        ValueError: If the filter key is invalid.
        ValidationError: If the filter value is invalid.

    Notes:
        The filter criteria are passed to the repository as keyword arguments.
        The filter criteria are validated against the ApiFilter schema.

    Examples:
        >>> get_recipes({"cuisine": "Italian"})

        >>> get_recipes({"cuisine": ["Italian","Greek"], "category": "main course"})

    """
    if filter:
        ApiRecipeFilter(**filter)
    bus: MessageBus = fastapi_bootstrap(
        get_uow(get_db_session_factory()), get_aio_pika_manager()
    )
    uow: UnitOfWork
    async with bus.uow as uow:
        recipes = await uow.recipes.query(
            filter=filter,
        )
    return json.dumps(
        [ApiRecipe.from_domain(recipe).model_dump() for recipe in recipes]
    )
