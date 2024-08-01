from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.shared.adapters.ORM.mappers.tags.process_type import (
    ProcessTypeMapper,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.tags.process_type import (
    ProcessTypeSaModel,
)
from src.contexts.products_catalog.shared.adapters.repositories.tags.tag import TagRepo
from src.contexts.products_catalog.shared.domain.entities.tags import ProcessType


class ProcessTypeRepo(TagRepo[ProcessType, ProcessTypeSaModel]):
    def __init__(
        self,
        db_session: AsyncSession,
    ):
        super().__init__(
            db_session=db_session,
            data_mapper=ProcessTypeMapper,
            domain_model_type=ProcessType,
            sa_model_type=ProcessTypeSaModel,
        )
