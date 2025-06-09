from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.parent_categorysa_model import (
    ParentCategorySaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification import (
    ParentCategory,
)
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from sqlalchemy.ext.asyncio import AsyncSession

from . import utils


class ParentCategoryMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(session: AsyncSession, domain_obj: ParentCategory) -> ParentCategorySaModel:
        return utils.classification_map_domain_to_sa(
            domain_obj=domain_obj,
            sa_model_type=ParentCategorySaModel,
            polymorphic_identity="parent_category",
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: ParentCategorySaModel) -> ParentCategory:
        return utils.classification_map_sa_to_domain(
            sa_obj=sa_obj, domain_obj_type=ParentCategory
        )
