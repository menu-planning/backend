from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands.classifications.food_group.update import (
    UpdateFoodGroup,
)
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def update_food_group(cmd: UpdateFoodGroup, uow: UnitOfWork) -> None:
    async with uow:
        classification = await uow.food_groups.get(cmd.id)
        classification.update_properties(**asdict(cmd.updates, recurse=False))
        await uow.food_groups.persist(classification)
        await uow.commit()
