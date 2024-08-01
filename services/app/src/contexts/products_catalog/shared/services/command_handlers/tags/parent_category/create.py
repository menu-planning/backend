from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands import CreateParentCategory
from src.contexts.products_catalog.shared.domain.entities.tags import Category
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def create_parent_category(cmd: CreateParentCategory, uow: UnitOfWork) -> None:
    async with uow:
        tag = Category.create_tag(**asdict(cmd, recurse=False))
        await uow.parent_categories.add(tag)
        await uow.commit()
