from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.parent_category.api_create_parent_category import (
    ApiCreateParentCategory,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def create_parent_category(
    data: ApiCreateParentCategory,
) -> None:
    """
    API endpoint for creating a new ParentCategory entity.

    Attributes:
        data (ApiCreateParentCategory): The data to create a new ParentCategory.
        container (Container, optional): The dependency injection container
    """
    cmd = data.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
