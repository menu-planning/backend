from attrs import asdict
from src.contexts.products_catalog.core.domain.commands.classifications.brand.create import (
    CreateBrand,
)
from src.contexts.products_catalog.core.domain.entities.classification.brand import (
    Brand,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.logging.logger import StructlogFactory

logger = StructlogFactory.get_logger(__name__)


async def create_brand(cmd: CreateBrand, uow: UnitOfWork) -> None:
    """Execute the create brand use case.
    
    Args:
        cmd: Command containing brand data to create.
        uow: UnitOfWork instance for transaction management.
    
    Returns:
        None: No return value.
    
    Events:
        BrandCreated: Emitted upon successful brand creation.
    
    Idempotency:
        No. Duplicate calls with same name will create separate brands.
    
    Transactions:
        One UnitOfWork per call. Commit on success; rollback on exception.
    
    Side Effects:
        Creates new Brand classification entity.
    """
    logger.info(
        "Creating brand",
        action="create_brand",
        brand_name=cmd.name,
        category_type="brand"
    )

    try:
        async with uow:
            classification = Brand.create_classification(**asdict(cmd, recurse=False))
            await uow.brands.add(classification)
            await uow.commit()

        logger.info(
            "Brand created successfully",
            action="create_brand_success",
            brand_id=classification.id,
            brand_name=cmd.name
        )
    except Exception as e:
        logger.error(
            "Failed to create brand",
            action="create_brand_error",
            brand_name=cmd.name,
            error_type=type(e).__name__,
            error_message=str(e),
            exc_info=True
        )
        raise
