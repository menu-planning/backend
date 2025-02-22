from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
    get_uow,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.recipe.update import (
    ApiAttributesToUpdateOnRecipe,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.db.database import get_db_session_factory


async def update_recipe(data: ApiAttributesToUpdateOnRecipe) -> None:
    """
    API endpoint for updating a recipe.

    Attributes:
        data (ApiAttributesToUpdateOnRecipe): The recipe data to update.
        container (Container, optional): The dependency injection container
            to use. Defaults to the global container.

    Raises:
        EntityNotFoundException: If the recipe with the given ID does not exist.
        ValidationError: If the recipe attributes are invalid.
        ValueError: If updates cannot be converted domain objects.

    Notes:
        The recipe attributes are validated against the ApiAttributesToUpdateOnRecipe
        schema.

    Examples:
        >>> update_recipe("1234567890", {"name": "Spaghetti Bolognese"})
    """

    cmd = data.to_domain()
    bus: MessageBus = fastapi_bootstrap(
        get_uow(get_db_session_factory()), get_aio_pika_manager()
    )
    await bus.handle(cmd)
