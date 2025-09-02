"""Mapper between classification `FoodGroup` and `FoodGroupSaModel`."""
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.food_group_sa_model import (
    FoodGroupSaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification.food_group import (
    FoodGroup,
)
from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper

from . import utils


class FoodGroupMapper(ModelMapper):
    """Map FoodGroup domain entity to/from FoodGroupSaModel."""
    
    @staticmethod
    async def map_domain_to_sa(session: AsyncSession, domain_obj: FoodGroup) -> FoodGroupSaModel:
        """Map domain FoodGroup to SQLAlchemy FoodGroupSaModel.
        
        Args:
            session: Database session (unused for this mapper).
            domain_obj: Domain FoodGroup object.
            
        Returns:
            FoodGroupSaModel instance.
        """
        return utils.classification_map_domain_to_sa(
            domain_obj=domain_obj,
            sa_model_type=FoodGroupSaModel,
            polymorphic_identity="food_group",
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: FoodGroupSaModel) -> FoodGroup:
        """Map SQLAlchemy FoodGroupSaModel to domain FoodGroup.
        
        Args:
            sa_obj: SQLAlchemy FoodGroupSaModel instance.
            
        Returns:
            Domain FoodGroup object.
        """
        return utils.classification_map_sa_to_domain(
            sa_obj=sa_obj, domain_obj_type=FoodGroup
        )
