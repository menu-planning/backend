from typing import Any

import src.contexts.recipes_catalog.shared.domain.commands as commands
from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
    get_uow,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.value_objects.rating import (
    ApiRating,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.db.database import get_db_session_factory


async def rate_recipe(
    rating: dict[str, Any],
) -> None:
    """
    API endpoint for rating a recipe.

    Attributes:
        rating (dict[str, Any]): A dictionary of rating attributes.
        container (Container, optional): The dependency injection container
            to use. Defaults to the global container.

    Raises:
        ValidationError: If the rating attributes are invalid.
        ValueError: If rating cannot be converted to a domain object.

    Notes:
        The rating attributes are validated against the ApiRating schema.

    Examples:
        >>> rate_recipe(
                rating = {
                    "user_id": "1234567890",
                    "recipe_id": "1234567890",
                    "taste": 5,
                    "convenience": 5,
                    "comments": "This is a great recipe!"
                }
            )
    """
    rating = ApiRating(**rating).to_domain()
    cmd = commands.RateRecipe(rating=rating)
    bus: MessageBus = fastapi_bootstrap(
        get_uow(get_db_session_factory()), get_aio_pika_manager()
    )
    await bus.handle(cmd)
