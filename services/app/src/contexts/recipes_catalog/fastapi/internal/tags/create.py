from src.contexts.recipes_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
    get_uow,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.tags.create import (
    ApiCreateTag,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.db.database import get_db_session_factory


async def create_tag(
    data: ApiCreateTag,
) -> None:
    """
    API endpoint for creating a new tag entity.

    Attributes:
        data (ApiCreateTag): The data to create a new tag.
        container (Container, optional): The dependency injection container
    """
    cmd = data.to_domain()
    bus: MessageBus = fastapi_bootstrap(
        get_uow(get_db_session_factory()), get_aio_pika_manager()
    )
    await bus.handle(cmd)
