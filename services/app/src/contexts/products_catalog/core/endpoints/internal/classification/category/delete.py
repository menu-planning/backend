from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.domain.commands.classifications.category.delete import (
    DeleteCategory,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def delete_category(
    id: str,
) -> None:
    """
    API endpoint for marking a Category entity as discarded.

    Attributes:
        id (str): The unique identifier of the category to delete.
        container (Container, optional): The dependency injection container

    Examples:
        >>> delete_category("1234567890")
    """
    cmd = DeleteCategory(
        id=id,
    )
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
