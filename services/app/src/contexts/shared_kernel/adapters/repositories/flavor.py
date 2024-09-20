from typing import Any

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)
from src.contexts.shared_kernel.adapters.ORM.mappers.flavor import FlavorMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.flavor import FlavorSaModel
from src.contexts.shared_kernel.domain.value_objects.name_tag.flavor import Flavor


class FlavorRepo(CompositeRepository[Flavor, FlavorSaModel]):
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=FlavorSaModel,
            filter_key_to_column_name={
                "name": "id",
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
            data_mapper=FlavorMapper,
            domain_model_type=Flavor,
            sa_model_type=FlavorSaModel,
            filter_to_column_mappers=FlavorRepo.filter_to_column_mappers,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Flavor):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Flavor:
        model_obj = await self._generic_repo.get(id)
        return model_obj

    async def get_sa_instance(self, id: str) -> FlavorSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt: Select | None = None,
    ) -> list[Flavor]:
        model_objs: list[self.domain_model_type] = await self._generic_repo.query(
            filter=filter, starting_stmt=starting_stmt
        )
        return model_objs

    async def persist(self, domain_obj: Flavor) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self) -> None:
        await self._generic_repo.persist_all()
