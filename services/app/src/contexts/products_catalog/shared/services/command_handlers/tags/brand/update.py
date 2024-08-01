from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands.tags.brand.update import (
    UpdateBrand,
)
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def update_brand(cmd: UpdateBrand, uow: UnitOfWork) -> None:
    async with uow:
        tag = await uow.brands.get(cmd.id)
        tag.update_properties(**asdict(cmd.updates, recurse=False))
        await uow.brands.persist(tag)
        await uow.commit()
