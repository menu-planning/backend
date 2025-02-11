from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands.classifications.food_group.create import (
    CreateFoodGroup,
)
from src.contexts.products_catalog.shared.domain.entities.classification import (
    FoodGroup,
)
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def create_food_group(cmd: CreateFoodGroup, uow: UnitOfWork) -> None:
    async with uow:
        classification = FoodGroup.create_classification(**asdict(cmd, recurse=False))
        await uow.food_groups.add(classification)
        await uow.commit()
