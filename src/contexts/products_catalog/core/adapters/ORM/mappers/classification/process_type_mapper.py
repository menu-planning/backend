"""Mapper between classification `ProcessType` and `ProcessTypeSaModel`."""
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.process_type_sa_model import (
    ProcessTypeSaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification.process_type import (
    ProcessType,
)
from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper

from . import utils


class ProcessTypeMapper(ModelMapper):
    """Map ProcessType domain entity to/from ProcessTypeSaModel."""
    
    @staticmethod
    async def map_domain_to_sa(session: AsyncSession, domain_obj: ProcessType) -> ProcessTypeSaModel:
        """Map domain ProcessType to SQLAlchemy ProcessTypeSaModel.
        
        Args:
            session: Database session (unused for this mapper).
            domain_obj: Domain ProcessType object.
            
        Returns:
            ProcessTypeSaModel instance.
        """
        return utils.classification_map_domain_to_sa(
            domain_obj=domain_obj,
            sa_model_type=ProcessTypeSaModel,
            polymorphic_identity="process_type",
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: ProcessTypeSaModel) -> ProcessType:
        """Map SQLAlchemy ProcessTypeSaModel to domain ProcessType.
        
        Args:
            sa_obj: SQLAlchemy ProcessTypeSaModel instance.
            
        Returns:
            Domain ProcessType object.
        """
        return utils.classification_map_sa_to_domain(
            sa_obj=sa_obj, domain_obj_type=ProcessType
        )
