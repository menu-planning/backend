from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.recipe.tags.utils import (
    tag_map_domain_to_sa,
    tag_map_sa_to_domain,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.tags import (
    MealPlanningSaModel,
)
from src.contexts.recipes_catalog.shared.domain.entities.tags import MealPlanning
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper


class MealPlanningMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: MealPlanning) -> MealPlanningSaModel:
        return tag_map_domain_to_sa(
            domain_obj=domain_obj,
            sa_model_type=MealPlanningSaModel,
            polymorphic_identity="meal_planning",
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: MealPlanningSaModel) -> MealPlanning:
        return tag_map_sa_to_domain(sa_obj=sa_obj, domain_obj_type=MealPlanning)
