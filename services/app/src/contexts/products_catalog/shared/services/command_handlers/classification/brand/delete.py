from src.contexts.products_catalog.shared.domain.commands import DeleteBrand
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def delete_brand(cmd: DeleteBrand, uow: UnitOfWork) -> None:
    async with uow:
        classification = await uow.brands.get(cmd.id)
        classification.delete()
        await uow.brands.persist(classification)
        await uow.commit()
