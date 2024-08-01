from src.contexts.products_catalog.shared.adapters.ORM.sa_models.tags.food_group import (
    FoodGroupSaModel,
)
from src.contexts.products_catalog.shared.domain.entities.tags import FoodGroup
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper

from . import utils


class FoodGroupMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: FoodGroup) -> FoodGroupSaModel:
        return utils.tag_map_domain_to_sa(
            domain_obj=domain_obj,
            sa_model_type=FoodGroupSaModel,
            polymorphic_identity="food_group",
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: FoodGroupSaModel) -> FoodGroup:
        return utils.tag_map_sa_to_domain(sa_obj=sa_obj, domain_obj_type=FoodGroup)
