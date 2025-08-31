from typing import Any, ClassVar

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.mappers.classification import (
    BrandMapper,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.brand import (
    BrandSaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification import Brand
from src.contexts.seedwork.shared.adapters.repositories.seedwork_repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)


class BrandRepo(CompositeRepository[Brand, BrandSaModel]):
    filter_to_column_mappers: ClassVar[list[FilterColumnMapper]] = [
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

    async def get(self, entity_id: str) -> Brand:
        return await self._generic_repo.get(entity_id)

    async def get_sa_instance(self, entity_id: str) -> BrandSaModel:
        return await self._generic_repo.get_sa_instance(entity_id)

    async def query(
        self,
        *,
        filters: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        _return_sa_instance: bool = False,
    ) -> list[Brand]:
        filters = filters or {}
        model_objs: list[Brand] = await self._generic_repo.query(
            filters=filters,
            starting_stmt=starting_stmt,
            _return_sa_instance=_return_sa_instance,
        )
        return model_objs

    async def persist(self, domain_obj: Brand) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[Brand] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
