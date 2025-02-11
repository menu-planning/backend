from src.contexts.products_catalog.shared.bootstrap.container import Container
from src.contexts.products_catalog.shared.domain.commands.classifications.parent_category.delete import (
    DeleteParentCategory,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def delete_parent_category(
    id: str,
) -> None:
    """
    API endpoint for marking a ParentCategory entity as discarded.

    Attributes:
        id (str): The unique identifier of the ParentCategory to delete.
        container (Container, optional): The dependency injection container

    Examples:
        >>> delete_category("1234567890")
    """
    cmd = DeleteParentCategory(
        id=id,
    )
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
