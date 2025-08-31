from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.category.create import (
    CreateCategory,
)
from src.contexts.products_catalog.core.domain.entities.classification import Category
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.logging.logger import StructlogFactory

logger = StructlogFactory.get_logger(__name__)


async def create_category(cmd: CreateCategory, uow: UnitOfWork) -> None:
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
