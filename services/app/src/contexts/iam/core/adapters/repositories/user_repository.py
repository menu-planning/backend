from typing import Any, Optional

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.iam.core.adapters.ORM.mappers.user_mapper import UserMapper
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.iam.core.domain.root_aggregate.user import User
from src.contexts.seedwork.shared.adapters.repositories.seedwork_repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)
from src.contexts.seedwork.shared.adapters.repositories.repository_logger import RepositoryLogger


class UserRepo(CompositeRepository[User, UserSaModel]):
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=UserSaModel,
            filter_key_to_column_name={
                "id": "id",
                "discarded": "discarded",
                "version": "version",
                "created_at": "created_at",
                "updated_at": "updated_at",
            },
        ),
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
        repository_logger: Optional[RepositoryLogger] = None,
    ):
        self._session = db_session
        
        # Create default logger if none provided
        if repository_logger is None:
            repository_logger = RepositoryLogger.create_logger("UserRepository")
        
        self._repository_logger = repository_logger
        
        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=UserMapper,
            domain_model_type=User,
            sa_model_type=UserSaModel,
            filter_to_column_mappers=UserRepo.filter_to_column_mappers,
            repository_logger=self._repository_logger,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: User):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> User:
        model_obj = await self._generic_repo.get(id)
        return model_obj # type: ignore

    async def get_sa_instance(self, id: str, _return_discarded: bool = False) -> UserSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id, _return_discarded=_return_discarded)
        return sa_obj

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt: Select | None = None,
        limit: int | None = None,
        _return_sa_instance: bool = False,
    ) -> list[User]:
        # Use the track_query context manager for structured logging
        async with self._repository_logger.track_query(
            operation="query", 
            entity_type="User",
            filter_count=len(filter)
        ) as query_context:
            
            model_objs = await self._generic_repo.query(
                filter=filter, 
                starting_stmt=starting_stmt, 
                limit=limit, 
                _return_sa_instance=_return_sa_instance
            )
            
            # Update query context with results
            query_context["result_count"] = len(model_objs)
            
            return model_objs

    async def persist(self, domain_obj: User) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[User] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
