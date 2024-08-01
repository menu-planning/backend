from typing import Any

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.iam.shared.adapters.ORM.mappers.user import UserMapper
from src.contexts.iam.shared.adapters.ORM.sa_models.role import RoleSaModel
from src.contexts.iam.shared.adapters.ORM.sa_models.user import UserSaModel
from src.contexts.iam.shared.domain.entities.user import User
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)


class UserRepo(CompositeRepository[User, UserSaModel]):
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=RoleSaModel,
            filter_key_to_column_name={
                "context": "context",
                "name": "name",
            },
            join_target_and_on_clause=[(RoleSaModel, UserSaModel.roles)],
        ),
    ]

    def __init__(
        self,
        db_session: AsyncSession,
    ):
        self._session = db_session
        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=UserMapper(),
            domain_model_type=User,
            sa_model_type=UserSaModel,
            filter_to_column_mappers=UserRepo.filter_to_column_mappers,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: User):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> User:
        model_obj = await self._generic_repo.get(id)
        return model_obj

    async def get_sa_instance(self, id: str) -> UserSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt: Select | None = None,
    ) -> list[User]:
        model_objs = await self._generic_repo.query(
            filter=filter, starting_stmt=starting_stmt
        )
        return model_objs

    async def persist(self, domain_obj: User) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self) -> None:
        await self._generic_repo.persist_all()
