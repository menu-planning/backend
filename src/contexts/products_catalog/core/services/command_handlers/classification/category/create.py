from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.category.create import (
    CreateCategory,
)
from src.contexts.products_catalog.core.domain.entities.classification.category import (
    Category,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.logging.logger import get_logger

logger = get_logger(__name__)


async def create_category(cmd: CreateCategory, uow: UnitOfWork) -> None:
    """Execute the create category use case.
    
    Args:
        cmd: Command containing category data to create.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Events:
        CategoryCreated: Emitted upon successful category creation.
    
    Idempotency:
        No. Duplicate calls with same name will create separate categories.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Creates new Category classification entity.
    """
    logger.info(
        "Creating category",
        action="create_category",
        category_name=cmd.name,
        category_type="category"
    )

    try:
        async with uow:
            classification = Category.create_classification(**asdict(cmd, recurse=False))
            await uow.categories.add(classification)
            await uow.commit()

        logger.info(
            "Category created successfully",
            action="create_category_success",
            category_id=classification.id,
            category_name=cmd.name
        )
    except Exception as e:
        logger.error(
            "Failed to create category",
            action="create_category_error",
            category_name=cmd.name,
            error_type=type(e).__name__,
            error_message=str(e),
            exc_info=True
        )
        raise
