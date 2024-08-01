from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands import CreateFoodGroup
from src.contexts.products_catalog.shared.domain.entities.tags import FoodGroup
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def create_food_group(cmd: CreateFoodGroup, uow: UnitOfWork) -> None:
    async with uow:
        tag = FoodGroup.create_tag(**asdict(cmd, recurse=False))
        await uow.food_groups.add(tag)
        await uow.commit()
