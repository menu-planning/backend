from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
    get_uow,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.diet_types.create import (
    ApiCreateDietType,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.db.database import get_db_session_factory


async def create_diet_type(
    data: ApiCreateDietType,
) -> None:
    """
    API endpoint for creating a new DietType entity.

    Attributes:
        data (ApiCreateDataType): The data to create a new diet type.
        container (Container, optional): The dependency injection container
    """
    cmd = data.to_domain()
    bus: MessageBus = fastapi_bootstrap(
        get_uow(get_db_session_factory()), get_aio_pika_manager()
    )
    await bus.handle(cmd)
