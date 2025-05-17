from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.domain.commands.classifications.source.delete import (
    DeleteSource,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def delete_source(
    id: str,
) -> None:
    """
    API endpoint for marking a Source entity as discarded.

    Attributes:
        id (str): The unique identifier of the Source to delete.
        container (Container, optional): The dependency injection container

    Examples:
        >>> delete_source("1234567890")
    """
    cmd = DeleteSource(
        id=id,
    )
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
