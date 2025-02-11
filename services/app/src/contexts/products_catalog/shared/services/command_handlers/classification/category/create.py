from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands.classifications.category.create import (
    CreateCategory,
)
from src.contexts.products_catalog.shared.domain.entities.classification import Category
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def create_category(cmd: CreateCategory, uow: UnitOfWork) -> None:
    async with uow:
        classification = Category.create_classification(**asdict(cmd, recurse=False))
        await uow.categories.add(classification)
        await uow.commit()
