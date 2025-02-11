from src.contexts.products_catalog.shared.bootstrap.container import Container
from src.contexts.products_catalog.shared.domain.commands.classifications.process_type.delete import (
    DeleteProcessType,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def delete_process_type(
    id: str,
) -> None:
    """
    API endpoint for marking a ProcessType entity as discarded.

    Attributes:
        id (str): The unique identifier of the ProcessType to delete.
        container (Container, optional): The dependency injection container

    Examples:
        >>> delete_process_type("1234567890")
    """
    cmd = DeleteProcessType(
        id=id,
    )
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
