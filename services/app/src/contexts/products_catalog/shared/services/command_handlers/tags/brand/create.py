from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands import CreateBrand
from src.contexts.products_catalog.shared.domain.entities.tags import Brand
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def create_brand(cmd: CreateBrand, uow: UnitOfWork) -> None:
    async with uow:
        tag = Brand.create_tag(**asdict(cmd, recurse=False))
        await uow.brands.add(tag)
        await uow.commit()
