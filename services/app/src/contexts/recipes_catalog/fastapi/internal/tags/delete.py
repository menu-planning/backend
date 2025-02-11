from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
    get_uow,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.tags.delete import (
    ApiDeleteTag,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.db.database import get_db_session_factory


async def delete_tag(
    data: ApiDeleteTag,
) -> None:
    """
    API endpoint for marking a Tag entity as discarded.

    Attributes:
        id (str): The unique identifier of the tag to delete.
        container (Container, optional): The dependency injection container

    Examples:
        >>> delete_tag("1234567890")
    """
    cmd = data.to_domain()
    bus: MessageBus = fastapi_bootstrap(
        get_uow(get_db_session_factory()), get_aio_pika_manager()
    )
    await bus.handle(cmd)
