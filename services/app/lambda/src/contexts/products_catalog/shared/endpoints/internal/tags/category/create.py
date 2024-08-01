from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.category.create import (
    ApiCreateCategory,
)
from src.contexts.products_catalog.shared.bootstrap.container import Container
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def create_category(
    data: ApiCreateCategory,
) -> None:
    """
    API endpoint for creating a new category entity.

    Attributes:
        data (ApiCreateCategory): The data to create a new category.
        container (Container, optional): The dependency injection container
    """
    cmd = data.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
