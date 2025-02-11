from src.contexts.products_catalog.shared.bootstrap.container import Container
from src.contexts.products_catalog.shared.domain.commands.classifications.brand.delete import (
    DeleteBrand,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def delete_brand(
    id: str,
) -> None:
    """
    API endpoint for marking a Brand entity as discarded.

    Attributes:
        id (str): The unique identifier of the Brand to delete.
        container (Container, optional): The dependency injection container

    Examples:
        >>> delete_brand("1234567890")
    """
    cmd = DeleteBrand(
        id=id,
    )
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
