from src.contexts.recipes_catalog.shared.domain.commands.diet_types.update import (
    UpdateDietType,
)
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def update_diet_type(cmd: UpdateDietType, uow: UnitOfWork) -> None:
    async with uow:
        diet_type = await uow.diet_types.get(cmd.diet_type_id)
        diet_type.update_properties(**cmd.updates)
        await uow.diet_types.persist(diet_type)
        await uow.commit()
