from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.shared.adapters.ORM.mappers.tags.parent_category import (
    ParentCategoryMapper,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.tags.parent_category import (
    ParentCategorySaModel,
)
from src.contexts.products_catalog.shared.adapters.repositories.tags.tag import TagRepo
from src.contexts.products_catalog.shared.domain.entities.tags import ParentCategory
from src.contexts.seedwork.shared.adapters.repository import FilterColumnMapper


class ParentCategoryRepo(TagRepo[ParentCategory, ParentCategorySaModel]):
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=ParentCategorySaModel,
            filter_key_to_column_name={
                "id": "id",
                "name": "name",
                "author_id": "author_id",
            },
        ),
    ]

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
