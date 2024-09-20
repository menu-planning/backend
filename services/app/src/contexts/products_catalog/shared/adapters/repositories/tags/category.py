from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.shared.adapters.ORM.mappers.tags.category import (
    CategoryMapper,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.tags.category import (
    CategorySaModel,
)
from src.contexts.products_catalog.shared.adapters.repositories.tags.tag import TagRepo
from src.contexts.products_catalog.shared.domain.entities.tags import Category
from src.contexts.seedwork.shared.adapters.repository import FilterColumnMapper


class CategoryRepo(TagRepo[Category, CategorySaModel]):
    filter_to_column_mappers = [
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
