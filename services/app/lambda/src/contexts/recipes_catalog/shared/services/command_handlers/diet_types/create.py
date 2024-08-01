from attrs import asdict
from src.contexts.recipes_catalog.shared.domain.commands import CreateDietType
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.shared_kernel.domain.entities.diet_type import DietType


async def create_diet_type(cmd: CreateDietType, uow: UnitOfWork) -> None:
    async with uow:
        tag = DietType.create(**asdict(cmd, recurse=False))
        await uow.diet_types.add(tag)
        await uow.commit()
