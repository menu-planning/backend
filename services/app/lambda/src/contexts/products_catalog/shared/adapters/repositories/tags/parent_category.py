from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.shared.adapters.ORM.mappers.tags.parent_category import (
    ParentCategoryMapper,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.tags.parent_category import (
    ParentCategorySaModel,
)
from src.contexts.products_catalog.shared.adapters.repositories.tags.tag import TagRepo
from src.contexts.products_catalog.shared.domain.entities.tags import ParentCategory


class ParentCategoryRepo(TagRepo[ParentCategory, ParentCategorySaModel]):
    def __init__(
        self,
        db_session: AsyncSession,
    ):
        super().__init__(
            db_session=db_session,
            data_mapper=ParentCategoryMapper,
            domain_model_type=ParentCategory,
            sa_model_type=ParentCategorySaModel,
        )
