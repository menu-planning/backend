from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.parent_category.create import (
    CreateParentCategory,
)
from src.contexts.products_catalog.core.domain.entities.classification.parent_category import ParentCategory
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def create_parent_category(cmd: CreateParentCategory, uow: UnitOfWork) -> None:
    async with uow:
        classification = ParentCategory.create_classification(**asdict(cmd, recurse=False))
        await uow.parent_categories.add(classification)
        await uow.commit()
