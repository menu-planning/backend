from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.category.create import (
    CreateCategory,
)
from src.contexts.products_catalog.core.domain.entities.classification import Category
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def create_category(cmd: CreateCategory, uow: UnitOfWork) -> None:
    async with uow:
        classification = Category.create_classification(**asdict(cmd, recurse=False))
        await uow.categories.add(classification)
        await uow.commit()
