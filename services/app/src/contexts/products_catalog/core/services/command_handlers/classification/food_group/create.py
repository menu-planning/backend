from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.food_group.create import (
    CreateFoodGroup,
)
from src.contexts.products_catalog.core.domain.entities.classification import (
    FoodGroup,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def create_food_group(cmd: CreateFoodGroup, uow: UnitOfWork) -> None:
    async with uow:
        classification = FoodGroup.create_classification(**asdict(cmd, recurse=False))
        await uow.food_groups.add(classification)
        await uow.commit()
