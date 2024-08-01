from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
    get_uow,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.tags.meal_planning.create import (
    ApiCreateMealPlanning,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.db.database import get_db_session_factory


async def create_meal_planning(
    data: ApiCreateMealPlanning,
) -> None:
    """
    API endpoint for creating a new MealPlanning entity.

    Attributes:
        data (ApiCreateMealPlanning): The data to create a new MealPlanning.
        container (Container, optional): The dependency injection container
    """
    cmd = data.to_domain()
    bus: MessageBus = fastapi_bootstrap(
        get_uow(get_db_session_factory()), get_aio_pika_manager()
    )
    await bus.handle(cmd)
