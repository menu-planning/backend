"""Mapper between classification `Category` and `CategorySaModel`."""
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.category_sa_model import (
    CategorySaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification.category import (
    Category,
)
from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper

from . import utils


class CategoryMapper(ModelMapper):
    """Map Category domain entity to/from CategorySaModel."""
    
    @staticmethod
    async def map_domain_to_sa(session: AsyncSession, domain_obj: Category) -> CategorySaModel:
        """Map domain Category to SQLAlchemy CategorySaModel.
        
        Args:
            session: Database session (unused for this mapper).
            domain_obj: Domain Category object.
            
        Returns:
            CategorySaModel instance.
        """
        return utils.classification_map_domain_to_sa(
            domain_obj=domain_obj,
            sa_model_type=CategorySaModel,
            polymorphic_identity="category",
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: CategorySaModel) -> Category:
        """Map SQLAlchemy CategorySaModel to domain Category.
        
        Args:
            sa_obj: SQLAlchemy CategorySaModel instance.
            
        Returns:
            Domain Category object.
        """
        return utils.classification_map_sa_to_domain(
            sa_obj=sa_obj, domain_obj_type=Category
        )
