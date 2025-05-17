from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.source.create import (
    ApiCreateSource,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def create_source(
    data: ApiCreateSource,
) -> None:
    """
    API endpoint for creating a new Source entity.

    Attributes:
        data (ApiCreateSource): The data to create a new Source.
        container (Container, optional): The dependency injection container
    """
    cmd = data.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
