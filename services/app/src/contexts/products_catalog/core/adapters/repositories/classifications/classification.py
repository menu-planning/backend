from typing import Any, TypeVar

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.base_class import (
    ClassificationSaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification import (
    Classification,
)
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)

E = TypeVar("E", bound=Classification)
S = TypeVar("S", bound=ClassificationSaModel)


class ClassificationRepo(CompositeRepository[E, S]):
    filter_to_column_mappers = [
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
        model_obj = await self._generic_repo.get(id)
        return model_obj # type: ignore

    async def get_sa_instance(self, id: str) -> S:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj # type: ignore

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt: Select | None = None,
    ) -> list[E]:
        model_objs: list[E] = await self._generic_repo.query(
            filter=filter, starting_stmt=starting_stmt
        )
        return model_objs

    async def persist(self, domain_obj: E) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[E] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
