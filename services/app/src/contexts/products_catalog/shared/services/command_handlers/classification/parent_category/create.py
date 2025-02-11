from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands.classifications.parent_category.create import (
    CreateParentCategory,
)
from src.contexts.products_catalog.shared.domain.entities.classification import Category
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def create_parent_category(cmd: CreateParentCategory, uow: UnitOfWork) -> None:
    async with uow:
        classification = Category.create_classification(**asdict(cmd, recurse=False))
        await uow.parent_categories.add(classification)
        await uow.commit()
