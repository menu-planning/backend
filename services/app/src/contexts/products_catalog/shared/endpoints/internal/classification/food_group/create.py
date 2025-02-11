from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.food_group.create import (
    ApiCreateFoodGroup,
)
from src.contexts.products_catalog.shared.bootstrap.container import Container
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def create_food_group(
    data: ApiCreateFoodGroup,
) -> None:
    """
    API endpoint for creating a new FoodGroup entity.

    Attributes:
        data (ApiCreateFoodGroup): The data to create a new FoodGroup.
        container (Container, optional): The dependency injection container
    """
    cmd = data.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
