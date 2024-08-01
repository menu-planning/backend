from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.parent_category.create import (
    ApiCreateParentCategory,
)
from src.contexts.products_catalog.shared.bootstrap.container import Container
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def create_category(
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
