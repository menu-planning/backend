"""Base repository for Products Catalog classification entities."""

from typing import Any, ClassVar

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.classification_sa_model import (
    ClassificationSaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification.classification import (
    Classification,
)
from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper
from src.contexts.seedwork.adapters.repositories.filter_mapper import FilterColumnMapper
from src.contexts.seedwork.adapters.repositories.protocols import CompositeRepository
from src.contexts.seedwork.adapters.repositories.sa_generic_repository import (
    SaGenericRepository,
)


class ClassificationRepo[E: Classification, S: ClassificationSaModel](
    CompositeRepository[E, S]
):
    """Generic repository for classification types (Category, Brand, etc.)."""

    filter_to_column_mappers: ClassVar[list[FilterColumnMapper]] = [
        FilterColumnMapper(
            sa_model_type=ClassificationSaModel,
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
        data_mapper: type[ModelMapper],
        domain_model_type: type[E],
        sa_model_type: type[S],
    ):
        self._session = db_session
        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=data_mapper,
            domain_model_type=domain_model_type,
            sa_model_type=sa_model_type,
            filter_to_column_mappers=[
                FilterColumnMapper(
                    sa_model_type=sa_model_type,
                    filter_key_to_column_name={
                        "id": "id",
                        "name": "name",
                        "author_id": "author_id",
                    },
                ),
            ],
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: E):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> E:
        return await self._generic_repo.get(id)

    async def get_sa_instance(self, id: str) -> S:
        return await self._generic_repo.get_sa_instance(id)

    async def query(
        self,
        *,
        filters: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        _return_sa_instance: bool = False,
    ) -> list[E]:
        filters = filters or {}
        return await self._generic_repo.query(
            filters=filters,
            starting_stmt=starting_stmt,
            _return_sa_instance=_return_sa_instance,
        )

    async def persist(self, domain_obj: E) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[E] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
