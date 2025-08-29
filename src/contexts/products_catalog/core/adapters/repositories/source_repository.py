from typing import Any, ClassVar

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.products_catalog.core.adapters.ORM.mappers.classification import (
    SourceMapper,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.source import (
    SourceSaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification import Source
from src.contexts.seedwork.shared.adapters.repositories.seedwork_repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)


class SourceRepo(CompositeRepository[Source, SourceSaModel]):
    filter_to_column_mappers: ClassVar[list[FilterColumnMapper]] = [
        FilterColumnMapper(
            sa_model_type=SourceSaModel,
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
        self._session = db_session
        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=SourceMapper,
            domain_model_type=Source,
            sa_model_type=SourceSaModel,
            filter_to_column_mappers=SourceRepo.filter_to_column_mappers,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Source):
        await self._generic_repo.add(entity)

    async def get(self, entity_id: str) -> Source:
        return await self._generic_repo.get(entity_id)

    async def get_sa_instance(self, entity_id: str) -> SourceSaModel:
        return await self._generic_repo.get_sa_instance(entity_id)

    async def query(
        self,
        *,
        filters: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        _return_sa_instance: bool = False,
    ) -> list[Source]:
        filters = filters or {}
        model_objs: list[Source] = await self._generic_repo.query(
            filters=filters,
            starting_stmt=starting_stmt,
            _return_sa_instance=_return_sa_instance,
        )
        return model_objs

    async def persist(self, domain_obj: Source) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[Source] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
