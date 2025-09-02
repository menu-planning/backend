"""Repository for FoodGroup classification entities."""

from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.mappers.classification.food_group_mapper import (
    FoodGroupMapper,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.food_group_sa_model import (
    FoodGroupSaModel,
)
from src.contexts.products_catalog.core.adapters.repositories.classifications.classification_repository import (
    ClassificationRepo,
)
from src.contexts.products_catalog.core.domain.entities.classification.food_group import (
    FoodGroup,
)
from src.contexts.seedwork.adapters.repositories.filter_mapper import FilterColumnMapper


class FoodGroupRepo(ClassificationRepo[FoodGroup, FoodGroupSaModel]):
    filter_to_column_mappers: ClassVar[list[FilterColumnMapper]] = [
        FilterColumnMapper(
            sa_model_type=FoodGroupSaModel,
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
            data_mapper=FoodGroupMapper,
            domain_model_type=FoodGroup,
            sa_model_type=FoodGroupSaModel,
        )
