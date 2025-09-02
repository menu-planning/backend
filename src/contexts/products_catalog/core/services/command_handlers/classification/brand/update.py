from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.brand.update import (
    UpdateBrand,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def update_brand(cmd: UpdateBrand, uow: UnitOfWork) -> None:
    """Execute the update brand use case.
    
    Args:
        cmd: Command containing brand ID and updates to apply.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Raises:
        NotFoundError: If brand with given ID does not exist.
    
    Idempotency:
        Yes. Key: brand_id + updates hash. Duplicate calls with same updates are safe.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Updates brand classification entity properties.
    """
    async with uow:
        classification = await uow.brands.get(cmd.id)
        classification.update_properties(**asdict(cmd.updates, recurse=False))
        await uow.brands.persist(classification)
        await uow.commit()
