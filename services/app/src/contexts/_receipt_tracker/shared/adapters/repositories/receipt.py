from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts._receipt_tracker.shared.adapters.ORM.mappers.receipt import (
    ReceiptMapper,
)
from src.contexts._receipt_tracker.shared.adapters.ORM.sa_models.receipt import (
    ReceiptSaModel,
)
from src.contexts._receipt_tracker.shared.domain.entities.receipt import Receipt
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)


class ReceiptRepo(CompositeRepository[Receipt, ReceiptSaModel]):
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=ReceiptSaModel,
            filter_key_to_column_name={
                "date": "date",
                "state": "state",
                "seller_id": "seller_id",
                "scraped": "scraped",
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
            data_mapper=ReceiptMapper,
            domain_model_type=Receipt,
            sa_model_type=ReceiptSaModel,
            filter_to_column_mappers=ReceiptRepo.filter_to_column_mappers,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Receipt):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Receipt:
        model_obj = await self._generic_repo.get(id)
        return model_obj

    async def get_sa_instance(self, id: str) -> ReceiptSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj

    async def list_by_house_id(
        self, house_id: str, _return_sa_model: bool = False
    ) -> list[Receipt]:
        stmt = (
            select(ReceiptSaModel)
            .join(ReceiptSaModel.house_ids)
            .where(ReceiptSaModel.house_ids.any(id=house_id))
        )
        if _return_sa_model:
            return await self._session.execute(stmt)
        else:
            return await self._generic_repo.execute_stmt(stmt)

    async def list_sa_model_by_house_id(self, house_id: str) -> ReceiptSaModel:
        sa_obj = await self.list_by_house_id(house_id, _return_sa_model=True)
        return sa_obj

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt: Select | None = None,
    ) -> list[Receipt]:
        model_objs = await self._generic_repo.query(
            filter=filter, starting_stmt=starting_stmt
        )
        return model_objs

    async def persist(self, domain_obj: Receipt) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self) -> None:
        await self._generic_repo.persist_all()
