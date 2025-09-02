from itertools import groupby
from typing import Any, ClassVar

from sqlalchemy import ColumnElement, Select, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from src.contexts.recipes_catalog.core.adapters.client.ORM.mappers.client_mapper import (
    ClientMapper,
)
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.client_associations import (
    clients_tags_association,
)
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.client_sa_model import (
    ClientSaModel,
)
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.menu_sa_model import (
    MenuSaModel,
)
from src.contexts.recipes_catalog.core.domain.client.root_aggregate.client import Client
from src.contexts.seedwork.adapters.enums import FrontendFilterTypes
from src.contexts.seedwork.adapters.repositories.filter_mapper import FilterColumnMapper
from src.contexts.seedwork.adapters.repositories.protocols import CompositeRepository
from src.contexts.seedwork.adapters.repositories.repository_logger import (
    RepositoryLogger,
)
from src.contexts.seedwork.adapters.repositories.sa_generic_repository import (
    SaGenericRepository,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)
from src.logging.logger import StructlogFactory


class ClientRepo(CompositeRepository[Client, ClientSaModel]):
    """SQLAlchemy repository for Client aggregate with advanced tag filtering.

    Provides sophisticated tag filtering with complex boolean logic for
    client queries, including positive and negative tag conditions.

    Notes:
        Adheres to CompositeRepository interface. Eager-loads: menus.
        Performance: uses EXISTS subqueries for efficient tag filtering.
        Transactions: methods require active UnitOfWork session.
    """

    filter_to_column_mappers: ClassVar[list[FilterColumnMapper]] = [
        FilterColumnMapper(
            sa_model_type=ClientSaModel,
            filter_key_to_column_name={
                "id": "id",
                "author_id": "author_id",
                "created_at": "created_at",
                "updated_at": "updated_at",
                "discarded": "discarded",
            },
        ),
        FilterColumnMapper(
            sa_model_type=MenuSaModel,
            filter_key_to_column_name={
                "menu_id": "id",
            },
            join_target_and_on_clause=[(MenuSaModel, ClientSaModel.menus)],
        ),
    ]

    def __init__(
        self,
        db_session: AsyncSession,
        repository_logger: RepositoryLogger | None = None,
    ):
        """Initialize client repository with database session and logging.

        Args:
            db_session: Active SQLAlchemy async session.
            repository_logger: Optional logger for query tracking.
        """
        self._session = db_session

        # Create default logger if none provided
        if repository_logger is None:
            repository_logger = RepositoryLogger.create_logger("ClientRepository")

        self._repository_logger = repository_logger

        # Initialize structured logger for this repository
        self._logger = StructlogFactory.get_logger("ClientRepository")

        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=ClientMapper,
            domain_model_type=Client,
            sa_model_type=ClientSaModel,
            filter_to_column_mappers=ClientRepo.filter_to_column_mappers,
            repository_logger=self._repository_logger,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Client):
        """Add client entity to repository.

        Args:
            entity: Client domain object to persist.
        """
        await self._generic_repo.add(entity)

    async def get(self, entity_id: str) -> Client:
        """Retrieve client by ID.

        Args:
            entity_id: Unique identifier for the client.

        Returns:
            Client domain object.

        Raises:
            ValueError: If client not found.
        """
        return await self._generic_repo.get(entity_id)

    async def get_sa_instance(self, entity_id: str) -> ClientSaModel:
        """Retrieve SQLAlchemy model instance by ID.

        Args:
            entity_id: Unique identifier for the client.

        Returns:
            ClientSaModel SQLAlchemy instance.
        """
        return await self._generic_repo.get_sa_instance(entity_id)

    def get_subquery_for_tags_not_exists(
        self, outer_client, tags: list[tuple[str, str, str]]
    ) -> ColumnElement[bool]:
        """Build EXISTS subquery for negative tag filtering.

        Args:
            outer_client: Aliased client model for correlation.
            tags: List of (key, value, author_id) tuples to exclude.

        Returns:
            SQLAlchemy EXISTS condition for tags that must not exist.

        Notes:
            Creates OR condition across all excluded tags.
            Each tag tuple represents (key, value, author_id).
        """
        conditions = []
        for t in tags:
            key, value, author_id = t
            condition = (
                select(1)
                .select_from(clients_tags_association)
                .join(TagSaModel, clients_tags_association.c.tag_id == TagSaModel.id)
                .where(
                    clients_tags_association.c.client_id == outer_client.id,
                    TagSaModel.key == key,
                    TagSaModel.value == value,
                    TagSaModel.author_id == author_id,
                    TagSaModel.type == "client",
                )
            ).exists()
            conditions.append(condition)
        return or_(*conditions)

    def get_subquery_for_tags(
        self, outer_client, tags: list[tuple[str, str, str]]
    ) -> ColumnElement[bool]:
        """Build EXISTS subquery for positive tag filtering with complex logic.

        For the given list of tag tuples (key, value, author_id),
        this builds a condition such that:
        - For tag tuples sharing the same key, at least one of the provided
          values must match.
        - For different keys, every key group must be matched.

        This is equivalent to:
        EXISTS (SELECT 1 FROM association JOIN tag
                WHERE association.client_id = outer_client.id
                    AND tag.key = key1
                    AND (tag.value = value1 OR tag.value = value2 ... )
                    AND tag.author_id = <common_author>
                    AND tag.type = "client")
        AND
        EXISTS (SELECT 1 FROM association JOIN tag
                WHERE association.client_id = outer_client.id
                    AND tag.key = key2
                    AND (tag.value = value3 OR tag.value = value4 ... )
                    AND tag.author_id = <common_author>
                    AND tag.type = "client")
        ...

        Args:
            outer_client: Aliased client model for correlation.
            tags: List of (key, value, author_id) tuples to include.

        Returns:
            SQLAlchemy EXISTS condition for required tag matches.

        Notes:
            Groups tags by key and creates AND condition across key groups.
            Within each key group, creates OR condition for values.
        """
        # Sort tags by key so groupby works correctly.
        tags_sorted = sorted(tags, key=lambda t: t[0])
        conditions = []

        for key, group in groupby(tags_sorted, key=lambda t: t[0]):
            group_list = list(group)
            # Since authors are always the same,
            # take the author_id from the first tuple.
            author_id = group_list[0][2]
            # Build OR condition for all tag values under this key.
            value_conditions = [TagSaModel.value == t[1] for t in group_list]

            group_condition = and_(
                TagSaModel.key == key,
                or_(*value_conditions),
                TagSaModel.author_id == author_id,
                TagSaModel.type == "client",
            )

            # Create a correlated EXISTS subquery for this key group.
            subquery = (
                select(1)
                .select_from(clients_tags_association)
                .join(TagSaModel, clients_tags_association.c.tag_id == TagSaModel.id)
                .where(
                    clients_tags_association.c.client_id == outer_client.id,
                    group_condition,
                )
            ).exists()

            conditions.append(subquery)

        # Combine the conditions for each key group with AND.
        return and_(*conditions)

    async def query(
        self,
        *,
        filters: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        _return_sa_instance: bool = False,
    ) -> list[Client]:
        """Query clients with advanced tag filtering support.

        Args:
            filters: Dictionary of filter criteria including tag filters.
            starting_stmt: Custom SQLAlchemy select statement to build upon.
            _return_sa_instance: Whether to return SQLAlchemy models.

        Returns:
            List of Client domain objects matching criteria.

        Notes:
            Handles complex tag filtering with positive and negative conditions.
            Uses EXISTS subqueries for efficient tag-based filtering.
            Automatically handles tag association joins when needed.
        """
        filters = filters or {}
        async with self._repository_logger.track_query(
            operation="query", entity_type="Client", filter_count=len(filters)
        ) as query_context:

            if "tags" in filters or "tags_not_exists" in filters:
                query_context["tag_filtering"] = True

                outer_client = aliased(self.sa_model_type)
                starting_stmt = select(outer_client)

                if filters.get("tags"):
                    tags = filters.pop("tags")
                    subquery = self.get_subquery_for_tags(outer_client, tags)
                    starting_stmt = starting_stmt.where(subquery)

                    query_context["positive_tags"] = len(tags)
                    self._repository_logger.debug_filter_operation(
                        f"Applied positive tag filter: {len(tags)} tag conditions",
                        tags_count=len(tags),
                    )

                if filters.get("tags_not_exists"):
                    tags_not_exists = filters.pop("tags_not_exists")
                    subquery = self.get_subquery_for_tags_not_exists(
                        outer_client, tags_not_exists
                    )
                    starting_stmt = starting_stmt.where(~subquery)

                    query_context["negative_tags"] = len(tags_not_exists)
                    self._repository_logger.debug_filter_operation(
                        (
                            f"Applied negative tag filter: {len(tags_not_exists)} "
                            f"exclusion conditions"
                        ),
                        exclusion_tags_count=len(tags_not_exists),
                    )

                model_objs: list[Client] | list[ClientSaModel] = (
                    await self._generic_repo.query(
                        filters=filters,
                        starting_stmt=starting_stmt,
                        already_joined={str(TagSaModel)},
                        sa_model=outer_client,
                        _return_sa_instance=_return_sa_instance,
                    )
                )

                query_context["result_count"] = len(model_objs)
                return model_objs

            # Standard query path without tag filtering
            model_objs: list[Client] | list[ClientSaModel] = (
                await self._generic_repo.query(
                    filters=filters,
                    starting_stmt=starting_stmt,
                    _return_sa_instance=_return_sa_instance,
                )
            )

            query_context["result_count"] = len(model_objs)
            return model_objs

    def list_filter_options(self) -> dict[str, dict]:
        """Return available filter and sort options for frontend.

        Returns:
            Dictionary mapping filter types to available options.
        """
        return {
            "sort": {
                "type": FrontendFilterTypes.SORT.value,
                "options": [
                    "created_at",
                    "updated_at",
                ],
            },
        }

    async def persist(self, domain_obj: Client) -> None:
        """Persist client changes to database.

        Args:
            domain_obj: Client domain object to persist.

        Notes:
            Logs persistence operation with client details.
        """
        self._logger.info(
            "Persisting client entity",
            client_id=domain_obj.id,
            author_id=getattr(domain_obj, 'author_id', None),
            operation="persist_single"
        )
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[Client] | None = None) -> None:
        """Persist multiple client entities in batch.

        Args:
            domain_entities: List of Client domain objects to persist.
        """
        await self._generic_repo.persist_all(domain_entities)
