from typing import Any

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.mappers.classification.brand_mapper import BrandMapper
from src.contexts.products_catalog.core.adapters.ORM.sa_models.brand import (
    BrandSaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification import Brand
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)


class BrandRepo(CompositeRepository[Brand, BrandSaModel]):
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=BrandSaModel,
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
            data_mapper=BrandMapper,
            domain_model_type=Brand,
            sa_model_type=BrandSaModel,
            filter_to_column_mappers=BrandRepo.filter_to_column_mappers,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Brand):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Brand:
        model_obj = await self._generic_repo.get(id)
        return model_obj # type: ignore

    async def get_sa_instance(self, id: str) -> BrandSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj # type: ignore

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt: Select | None = None,
    ) -> list[Brand]:
        model_objs: list[Brand] = await self._generic_repo.query(
            filter=filter, starting_stmt=starting_stmt
        )
        return model_objs

    async def persist(self, domain_obj: Brand) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[Brand] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
