"""Repository facade for IAM users backed by SQLAlchemy.

Composes a generic repository with IAM-specific filtering and logging, and
exposes a narrow API tailored for domain operations.
"""

from typing import Any, ClassVar

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.iam.core.adapters.ORM.mappers.user_mapper import UserMapper
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.iam.core.domain.root_aggregate.user import User
from src.contexts.seedwork.adapters.repositories.filter_mapper import FilterColumnMapper
from src.contexts.seedwork.adapters.repositories.protocols import CompositeRepository
from src.contexts.seedwork.adapters.repositories.repository_logger import (
    RepositoryLogger,
)
from src.contexts.seedwork.adapters.repositories.sa_generic_repository import (
    SaGenericRepository,
)


class UserRepo(CompositeRepository[User, UserSaModel]):
    """Persistence port for User aggregate.

    Guarantees:
        - get(): returns None | raises NotFoundError
        - add(): insert rule
        - list(): ordering, pagination, filters

    Notes:
        Adheres to CompositeRepository. Eager-loads: roles.
        Performance: avoids N+1 via joinedload on roles.
        Transactions: methods require active UnitOfWork session.
    """

    filter_to_column_mappers: ClassVar[list[FilterColumnMapper]] = [
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
        repository_logger: RepositoryLogger | None = None,
    ):
        self._session = db_session

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
        """Add user entity to repository.

        Args:
            entity: User entity to add.
        """
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> User:
        """Get user entity by ID.

        Args:
            id: User ID to retrieve.

        Returns:
            User entity if found.

        Raises:
            NotFoundError: If user not found.
        """
        return await self._generic_repo.get(id)

    async def get_sa_instance(self, id: str) -> UserSaModel:
        """Get SQLAlchemy user model by ID.

        Args:
            id: User ID to retrieve.

        Returns:
            SQLAlchemy user model if found.
        """
        return await self._generic_repo.get_sa_instance(id, _return_discarded=True)

    async def query(
        self,
        *,
        filters: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        limit: int | None = None,
        _return_sa_instance: bool = False,
    ) -> list[User]:
        """Query users with filters and pagination.

        Args:
            filters: Filter criteria for querying users.
            starting_stmt: Custom SQLAlchemy statement to start from.
            limit: Maximum number of results to return.
            _return_sa_instance: Whether to return SQLAlchemy instances.

        Returns:
            List of user entities matching the criteria.
        """
        filters = filters or {}
        async with self._repository_logger.track_query(
            operation="query", entity_type="User", filter_count=len(filters)
        ) as query_context:

            model_objs = await self._generic_repo.query(
                filters=filters,
                starting_stmt=starting_stmt,
                limit=limit,
                _return_sa_instance=_return_sa_instance,
            )

            # Update query context with results
            query_context["result_count"] = len(model_objs)

            return model_objs

    async def persist(self, domain_obj: User) -> None:
        """Persist user entity changes.

        Args:
            domain_obj: User entity to persist.
        """
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[User] | None = None) -> None:
        """Persist all user entity changes.

        Args:
            domain_entities: List of user entities to persist.
        """
        await self._generic_repo.persist_all(domain_entities)
