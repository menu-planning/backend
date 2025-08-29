from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.domain.commands.classifications.food_group.delete import (
    DeleteFoodGroup,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def delete_food_group(
    id: str,
) -> None:
    """
    API endpoint for marking a FoodGroup entity as discarded.

    Attributes:
        id (str): The unique identifier of the FoodGroup to delete.
        container (Container, optional): The dependency injection container

    Examples:
        >>> delete_food_group("1234567890")
    """
    cmd = DeleteFoodGroup(
        id=id,
    )
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
