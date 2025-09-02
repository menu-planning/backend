"""Repository for Category classification entities."""

from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.mappers.classification.category_mapper import (
    CategoryMapper,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.category_sa_model import (
    CategorySaModel,
)
from src.contexts.products_catalog.core.adapters.repositories.classifications.classification_repository import (
    ClassificationRepo,
)
from src.contexts.products_catalog.core.domain.entities.classification.category import (
    Category,
)
from src.contexts.seedwork.adapters.repositories.filter_mapper import FilterColumnMapper


class CategoryRepo(ClassificationRepo[Category, CategorySaModel]):
    filter_to_column_mappers: ClassVar[list[FilterColumnMapper]] = [
        FilterColumnMapper(
            sa_model_type=CategorySaModel,
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
            data_mapper=CategoryMapper,
            domain_model_type=Category,
            sa_model_type=CategorySaModel,
        )
