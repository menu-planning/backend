from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.mappers.classification.parent_category_mapper import (
    ParentCategoryMapper,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.parent_categorysa_model import (
    ParentCategorySaModel,
)
from src.contexts.products_catalog.core.adapters.repositories.classifications.classification_repository import (
    ClassificationRepo,
)
from src.contexts.products_catalog.core.domain.entities.classification import (
    ParentCategory,
)
from src.contexts.seedwork.shared.adapters.repository import FilterColumnMapper


class ParentCategoryRepo(ClassificationRepo[ParentCategory, ParentCategorySaModel]):
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
