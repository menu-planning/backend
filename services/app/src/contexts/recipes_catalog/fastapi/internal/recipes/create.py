from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
    get_uow,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.recipes.create import (
    ApiCreateRecipe,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.db.database import get_db_session_factory


async def create_recipe(data: ApiCreateRecipe) -> None:
    """
    API endpoint for adding a recipe.

    Attributes:
        data (ApiCreateRecipe): The recipe data to add.
        container (Container, optional): The dependency injection container
            to use. Defaults to the global container.

    Raises:
        ValidationError: If the recipe attributes are invalid.

    Notes:
        The recipe attributes are validated against the ApiAddRecipe schema.

    Examples:
        >>> add_recipe({"name": "Spaghetti Bolognese", "cuisine": "Italian"})

        >>> add_recipe({"name": "Spaghetti Bolognese", "cuisine": "Italian", "category": "main course"})
    """
    cmd = data.to_domain()
    bus: MessageBus = fastapi_bootstrap(
        get_uow(get_db_session_factory()), get_aio_pika_manager()
    )
    await bus.handle(cmd)
