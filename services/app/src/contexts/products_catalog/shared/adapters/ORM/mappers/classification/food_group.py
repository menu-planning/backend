from src.contexts.products_catalog.shared.adapters.ORM.sa_models.classification.food_group import (
    FoodGroupSaModel,
)
from src.contexts.products_catalog.shared.domain.entities.classification import (
    FoodGroup,
)
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from sqlalchemy.ext.asyncio import AsyncSession

from . import utils


class FoodGroupMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(session: AsyncSession, domain_obj: FoodGroup) -> FoodGroupSaModel:
        return utils.classification_map_domain_to_sa(
            domain_obj=domain_obj,
            sa_model_type=FoodGroupSaModel,
            polymorphic_identity="food_group",
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: FoodGroupSaModel) -> FoodGroup:
        return utils.classification_map_sa_to_domain(
            sa_obj=sa_obj, domain_obj_type=FoodGroup
        )
