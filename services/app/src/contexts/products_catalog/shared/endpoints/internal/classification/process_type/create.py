from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.process_type.create import (
    ApiCreateProcessType,
)
from src.contexts.products_catalog.shared.bootstrap.container import Container
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def create_process_type(
    data: ApiCreateProcessType,
) -> None:
    """
    API endpoint for creating a new ProcessType entity.

    Attributes:
        data (ApiCreateProcessType): The data to create a new ProcessType.
        container (Container, optional): The dependency injection container
    """
    cmd = data.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
