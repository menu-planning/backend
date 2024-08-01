from typing import Any

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.shared.adapters.ORM.mappers.source import (
    SourceMapper,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.source import (
    SourceSaModel,
)
from src.contexts.products_catalog.shared.domain.entities.tags import Source
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)


class SourceRepo(CompositeRepository[Source, SourceSaModel]):
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
            filter_to_column_mappers=[
                FilterColumnMapper(
                    sa_model_type=SourceSaModel,
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

    async def add(self, entity: Source):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Source:
        model_obj = await self._generic_repo.get(id)
        return model_obj

    async def get_sa_instance(self, id: str) -> SourceSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt: Select | None = None,
    ) -> list[Source]:
        model_objs: list[self.domain_model_type] = await self._generic_repo.query(
            filter=filter, starting_stmt=starting_stmt
        )
        return model_objs

    async def persist(self, domain_obj: Source) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self) -> None:
        await self._generic_repo.persist_all()
