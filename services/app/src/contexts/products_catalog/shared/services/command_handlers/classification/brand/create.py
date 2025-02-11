from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands.classifications.brand.create import (
    CreateBrand,
)
from src.contexts.products_catalog.shared.domain.entities.classification import Brand
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def create_brand(cmd: CreateBrand, uow: UnitOfWork) -> None:
    async with uow:
        classification = Brand.create_classification(**asdict(cmd, recurse=False))
        await uow.brands.add(classification)
        await uow.commit()
