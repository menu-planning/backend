"""Mapper between classification `ParentCategory` and SA model."""
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.parent_categorysa_model import (
    ParentCategorySaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification.parent_category import (
    ParentCategory,
)
from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper

from . import utils


class ParentCategoryMapper(ModelMapper):
    """Map ParentCategory domain entity to/from ParentCategorySaModel."""
    
    @staticmethod
    async def map_domain_to_sa(session: AsyncSession, domain_obj: ParentCategory) -> ParentCategorySaModel:
        """Map domain ParentCategory to SQLAlchemy ParentCategorySaModel.
        
        Args:
            session: Database session (unused for this mapper).
            domain_obj: Domain ParentCategory object.
            
        Returns:
            ParentCategorySaModel instance.
        """
        return utils.classification_map_domain_to_sa(
            domain_obj=domain_obj,
            sa_model_type=ParentCategorySaModel,
            polymorphic_identity="parent_category",
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: ParentCategorySaModel) -> ParentCategory:
        """Map SQLAlchemy ParentCategorySaModel to domain ParentCategory.
        
        Args:
            sa_obj: SQLAlchemy ParentCategorySaModel instance.
            
        Returns:
            Domain ParentCategory object.
        """
        return utils.classification_map_sa_to_domain(
            sa_obj=sa_obj, domain_obj_type=ParentCategory
        )
