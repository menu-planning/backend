from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.recipe.tags.utils import (
    tag_map_domain_to_sa,
    tag_map_sa_to_domain,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.tags import (
    CategorySaModel,
)
from src.contexts.recipes_catalog.shared.domain.entities.tags import Category
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper


class CategoryMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: Category) -> CategorySaModel:
        return tag_map_domain_to_sa(
            domain_obj=domain_obj,
            sa_model_type=CategorySaModel,
            polymorphic_identity="category",
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: CategorySaModel) -> Category:
        return tag_map_sa_to_domain(sa_obj=sa_obj, domain_obj_type=Category)
