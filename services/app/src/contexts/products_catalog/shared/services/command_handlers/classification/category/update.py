from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands.classifications.category.update import (
    UpdateCategory,
)
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def update_category(cmd: UpdateCategory, uow: UnitOfWork) -> None:
    async with uow:
        classification = await uow.categories.get(cmd.id)
        classification.update_properties(**asdict(cmd.updates, recurse=False))
        await uow.categories.persist(classification)
        await uow.commit()
