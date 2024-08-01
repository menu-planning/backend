from attrs import asdict
from src.contexts.recipes_catalog.shared.domain.commands import CreateCategory
from src.contexts.recipes_catalog.shared.domain.entities.tags import Category
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork


async def create_category(cmd: CreateCategory, uow: UnitOfWork) -> None:
    async with uow:
        tag = Category.create_tag(**asdict(cmd, recurse=False))
        await uow.categories.add(tag)
        await uow.commit()
