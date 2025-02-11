from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands.classifications.parent_category.update import (
    UpdateParentCategory,
)
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def update_parent_category(cmd: UpdateParentCategory, uow: UnitOfWork) -> None:
    async with uow:
        classification = await uow.parent_categories.get(cmd.id)
        classification.update_properties(**asdict(cmd.updates, recurse=False))
        await uow.parent_categories.persist(classification)
        await uow.commit()
