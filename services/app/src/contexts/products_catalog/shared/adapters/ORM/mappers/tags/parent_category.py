from src.contexts.products_catalog.shared.adapters.ORM.sa_models.tags.parent_category import (
    ParentCategorySaModel,
)
from src.contexts.products_catalog.shared.domain.entities.tags import ParentCategory
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper

from . import utils


class ParentCategoryMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: ParentCategory) -> ParentCategorySaModel:
        return utils.tag_map_domain_to_sa(
            domain_obj=domain_obj,
            sa_model_type=ParentCategorySaModel,
            polymorphic_identity="parent_category",
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: ParentCategorySaModel) -> ParentCategory:
        return utils.tag_map_sa_to_domain(sa_obj=sa_obj, domain_obj_type=ParentCategory)
