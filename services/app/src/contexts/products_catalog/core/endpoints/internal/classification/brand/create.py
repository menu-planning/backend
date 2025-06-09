from src.contexts.products_catalog.core.adapters.api_schemas.commands.classification.brand.api_create_brand import (
    ApiCreateBrand,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def create_brand(
    data: ApiCreateBrand,
) -> None:
    """
    API endpoint for creating a new Brand entity.

    Attributes:
        data (ApiCreateBrand): The data to create a new Brand.
        container (Container, optional): The dependency injection container
    """
    cmd = data.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
