from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts._receipt_tracker.shared.adapters.ORM.mappers.seller import (
    SellerMapper,
)
from src.contexts._receipt_tracker.shared.adapters.ORM.sa_models.seller import (
    SellerSaModel,
)
from src.contexts._receipt_tracker.shared.domain.value_objects.seller import Seller
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)


class SellerRepo(CompositeRepository[Seller, SellerSaModel]):
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=SellerSaModel,
            filter_key_to_column_name={},
        ),
    ]

    def __init__(
        self,
        db_session: AsyncSession,
    ):
        self._session = db_session
        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=SellerMapper,
            domain_model_type=Seller,
            sa_model_type=SellerSaModel,
            filter_to_column_mappers=SellerRepo.filter_to_column_mappers,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Seller):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Seller:
        model_obj = await self._generic_repo.get(id)
        return model_obj

    async def get_sa_instance(self, id: str) -> SellerSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj

    async def list_by_partial_id(
        self,
        partial_id: str,
        _return_sa_model: bool = False,
    ) -> list[Seller]:
        assert len(partial_id) >= 8
        stmt = select(SellerSaModel).filter(SellerSaModel.id.contains(partial_id))
        if _return_sa_model:
            return await self._session.execute(stmt)
        else:
            return await self._generic_repo.execute_stmt(stmt)

    async def list_sa_model_by_partial_id(self, partial_id: str) -> SellerSaModel:
        sa_obj = await self.list_by_partial_id(partial_id, _return_sa_model=True)
        return sa_obj

    async def query(
        self, filter: dict[str, Any] = {}, starting_stmt: Select | None = None
    ) -> list[Seller]:
        model_objs = await self._generic_repo.query(
            filter=filter, starting_stmt=starting_stmt
        )
        return model_objs

    async def persist(self, domain_obj: Seller) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[Seller] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
