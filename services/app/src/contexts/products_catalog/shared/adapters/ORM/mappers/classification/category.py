from src.contexts.products_catalog.shared.adapters.ORM.sa_models.classification.category import (
    CategorySaModel,
)
from src.contexts.products_catalog.shared.domain.entities.classification import Category
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from sqlalchemy.ext.asyncio import AsyncSession

from . import utils


class CategoryMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(session: AsyncSession, domain_obj: Category) -> CategorySaModel:
        return utils.classification_map_domain_to_sa(
            domain_obj=domain_obj,
            sa_model_type=CategorySaModel,
            polymorphic_identity="category",
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: CategorySaModel) -> Category:
        return utils.classification_map_sa_to_domain(
            sa_obj=sa_obj, domain_obj_type=Category
        )
