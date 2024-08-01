from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.shared.adapters.ORM.mappers.tags.food_group import (
    FoodGroupMapper,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.tags.food_group import (
    FoodGroupSaModel,
)
from src.contexts.products_catalog.shared.adapters.repositories.tags.tag import TagRepo
from src.contexts.products_catalog.shared.domain.entities.tags import FoodGroup


class FoodGroupRepo(TagRepo[FoodGroup, FoodGroupSaModel]):
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
