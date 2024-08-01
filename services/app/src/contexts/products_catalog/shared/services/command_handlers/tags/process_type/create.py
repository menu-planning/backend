from attrs import asdict
from src.contexts.products_catalog.shared.domain.commands import CreateProcessType
from src.contexts.products_catalog.shared.domain.entities.tags import ProcessType
from src.contexts.products_catalog.shared.services.uow import UnitOfWork


async def create_process_type(cmd: CreateProcessType, uow: UnitOfWork) -> None:
    async with uow:
        tag = ProcessType.create_tag(**asdict(cmd, recurse=False))
        await uow.process_types.add(tag)
        await uow.commit()
