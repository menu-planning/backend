from typing import Any

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)
from src.contexts.shared_kernel.adapters.ORM.mappers.cuisine import CuisineMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.cuisine import CuisineSaModel
from src.contexts.shared_kernel.domain.value_objects.name_tag.cuisine import Cuisine


class CuisineRepo(CompositeRepository[Cuisine, CuisineSaModel]):
    def __init__(
        self,
        db_session: AsyncSession,
    ):
        self._session = db_session
        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=CuisineMapper,
            domain_model_type=Cuisine,
            sa_model_type=CuisineSaModel,
            filter_to_column_mappers=[
                FilterColumnMapper(
                    sa_model_type=CuisineSaModel,
                    filter_key_to_column_name={
                        "name": "id",
                    },
                ),
            ],
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Cuisine):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Cuisine:
        model_obj = await self._generic_repo.get(id)
        return model_obj

    async def get_sa_instance(self, id: str) -> CuisineSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt: Select | None = None,
    ) -> list[Cuisine]:
        model_objs: list[self.domain_model_type] = await self._generic_repo.query(
            filter=filter, starting_stmt=starting_stmt
        )
        return model_objs

    async def persist(self, domain_obj: Cuisine) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self) -> None:
        await self._generic_repo.persist_all()
