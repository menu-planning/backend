from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.process_type_sa_model import (
    ProcessTypeSaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification import (
    ProcessType,
)
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from sqlalchemy.ext.asyncio import AsyncSession

from . import utils


class ProcessTypeMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(session: AsyncSession, domain_obj: ProcessType) -> ProcessTypeSaModel:
        return utils.classification_map_domain_to_sa(
            domain_obj=domain_obj,
            sa_model_type=ProcessTypeSaModel,
            polymorphic_identity="process_type",
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: ProcessTypeSaModel) -> ProcessType:
        return utils.classification_map_sa_to_domain(
            sa_obj=sa_obj, domain_obj_type=ProcessType
        )
