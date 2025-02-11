import src.contexts.recipes_catalog.shared.domain.commands as commands
from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
    get_uow,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.db.database import get_db_session_factory


async def delete_recipe(recipe_id: str) -> None:
    """
    API endpoint for deleting a recipe.

    Attributes:
        recipe_id (str): The unique identifier of the recipe to delete.
        container (Container, optional): The dependency injection container
            to use. Defaults to the global container.

    Raises:
        EntityNotFoundException: If the recipe with the given ID does not exist.

    Examples:
        >>> delete_recipe("1234567890")
    """
    cmd = commands.DeleteRecipe(recipe_id=recipe_id)
    bus: MessageBus = fastapi_bootstrap(
        get_uow(get_db_session_factory()), get_aio_pika_manager()
    )
    await bus.handle(cmd)
