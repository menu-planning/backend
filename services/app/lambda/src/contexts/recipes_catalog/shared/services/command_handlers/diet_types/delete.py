from src.contexts.recipes_catalog.shared.domain.commands import DeleteDietType
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def delete_diet_type(cmd: DeleteDietType, uow: UnitOfWork) -> None:
    async with uow:
        tag = await uow.diet_types.get(cmd.id)
        tag.delete()
        await uow.diet_types.persist(tag)
        await uow.commit()
