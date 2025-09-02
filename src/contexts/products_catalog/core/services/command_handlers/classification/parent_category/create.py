from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.parent_category.create import (
    CreateParentCategory,
)
from src.contexts.products_catalog.core.domain.entities.classification.parent_category import (
    ParentCategory,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork


async def create_parent_category(cmd: CreateParentCategory, uow: UnitOfWork) -> None:
    """Execute the create parent category use case.
    
    Args:
        cmd: Command containing parent category data to create.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Events:
        ParentCategoryCreated: Emitted upon successful parent category creation.
    
    Idempotency:
        No. Duplicate calls with same name will create separate parent categories.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Creates new ParentCategory classification entity.
    """
    async with uow:
        classification = ParentCategory.create_classification(**asdict(cmd, recurse=False))
        await uow.parent_categories.add(classification)
        await uow.commit()
