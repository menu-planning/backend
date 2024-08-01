from typing import Any

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.food_tracker.shared.adapters.ORM.mappers.house import HouseMapper
from src.contexts.food_tracker.shared.adapters.ORM.sa_models.associations_tables import (
    HousesMembersAssociation,
    HousesNutritionistsAssociation,
    HousesReceiptsAssociation,
)
from src.contexts.food_tracker.shared.adapters.ORM.sa_models.houses import HouseSaModel
from src.contexts.food_tracker.shared.domain.entities.house import House
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)


class HousesRepo(CompositeRepository[House, HouseSaModel]):
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=HouseSaModel,
            filter_key_to_column_name={
                "id": "id",
                "owner_id": "owner_id",
                "name": "name",
            },
        ),
        FilterColumnMapper(
            sa_model_type=HousesReceiptsAssociation,
            join_target_and_on_clause=[
                (
                    HousesReceiptsAssociation,
                    HouseSaModel.receipts,
                )
            ],
            filter_key_to_column_name={"cfe_key": "receipt_id"},
        ),
        FilterColumnMapper(
            sa_model_type=HousesMembersAssociation,
            join_target_and_on_clause=[
                (HousesMembersAssociation, HouseSaModel.members)
            ],
            filter_key_to_column_name={"members": "user_id"},
        ),
        FilterColumnMapper(
            sa_model_type=HousesNutritionistsAssociation,
            join_target_and_on_clause=[
                (HousesNutritionistsAssociation, HouseSaModel.nutritionists)
            ],
            filter_key_to_column_name={"nutritionists": "user_id"},
        ),
    ]

    def __init__(
        self,
        db_session: AsyncSession,
    ):
        self._session = db_session
        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=HouseMapper,
            domain_model_type=House,
            sa_model_type=HouseSaModel,
            filter_to_column_mappers=HousesRepo.filter_to_column_mappers,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: House):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> House:
        model_obj = await self._generic_repo.get(id)
        return model_obj

    async def get_sa_instance(self, id: str) -> HouseSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt: Select | None = None,
    ) -> list[House]:
        model_objs = await self._generic_repo.query(
            filter=filter, starting_stmt=starting_stmt
        )
        return model_objs

    async def persist(self, domain_obj: House) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self) -> None:
        await self._generic_repo.persist_all()
