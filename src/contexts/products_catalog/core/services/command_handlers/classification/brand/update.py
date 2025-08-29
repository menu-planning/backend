from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.brand.update import (
    UpdateBrand,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def update_brand(cmd: UpdateBrand, uow: UnitOfWork) -> None:
    async with uow:
        classification = await uow.brands.get(cmd.id)
        classification.update_properties(**asdict(cmd.updates, recurse=False))
        await uow.brands.persist(classification)
        await uow.commit()
