from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.mappers.classification.process_type_mapper import (
    ProcessTypeMapper,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.process_type_sa_model import (
    ProcessTypeSaModel,
)
from src.contexts.products_catalog.core.adapters.repositories.classifications.classification_repository import (
    ClassificationRepo,
)
from src.contexts.products_catalog.core.domain.entities.classification import (
    ProcessType,
)
from src.contexts.seedwork.shared.adapters.seedwork_repository import FilterColumnMapper


class ProcessTypeRepo(ClassificationRepo[ProcessType, ProcessTypeSaModel]):
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=ProcessTypeSaModel,
            filter_key_to_column_name={
                "id": "id",
                "name": "name",
                "author_id": "author_id",
            },
        ),
    ]

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
