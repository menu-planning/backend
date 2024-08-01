from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
    get_uow,
)
from src.contexts.recipes_catalog.shared.domain.commands.diet_types.delete import (
    DeleteDietType,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.db.database import get_db_session_factory


async def delete_diet_type(
    id: str,
) -> None:
    """
    API endpoint for marking a DietType entity as discarded.

    Attributes:
        id (str): The unique identifier of the diet type to delete.
        container (Container, optional): The dependency injection container

    Examples:
        >>> delete_diet_type("1234567890")
    """
    cmd = DeleteDietType(
        id=id,
    )
    bus: MessageBus = fastapi_bootstrap(
        get_uow(get_db_session_factory()), get_aio_pika_manager()
    )
    await bus.handle(cmd)
