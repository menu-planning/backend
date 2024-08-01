from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
    get_uow,
)
from src.contexts.recipes_catalog.shared.domain.commands.tags.meal_planning.delete import (
    DeleteMealPlanning,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.db.database import get_db_session_factory


async def delete_meal_planning(
    id: str,
) -> None:
    """
    API endpoint for marking a MealPlanning entity as discarded.

    Attributes:
        id (str): The unique identifier of the MealPlanning to delete.
        container (Container, optional): The dependency injection container

    Examples:
        >>> delete_meal_planning("1234567890")
    """
    cmd = DeleteMealPlanning(
        id=id,
    )
    bus: MessageBus = fastapi_bootstrap(
        get_uow(get_db_session_factory()), get_aio_pika_manager()
    )
    await bus.handle(cmd)
