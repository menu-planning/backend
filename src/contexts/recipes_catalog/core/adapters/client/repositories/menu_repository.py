from itertools import groupby
from typing import Any, ClassVar

from sqlalchemy import ColumnElement, Select, and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from src.contexts.products_catalog.core.adapters.repositories.product_repository import (
    ProductRepo,
)
from src.contexts.recipes_catalog.core.adapters.client.ORM.mappers.menu_mapper import (
    MenuMapper,
)
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.menu_sa_model import (
    MenuSaModel,
)
from src.contexts.recipes_catalog.core.domain.client.entities.menu import Menu
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


class MenuRepo(CompositeRepository[Menu, MenuSaModel]):
    """SQLAlchemy repository for Menu entities with tag filtering and product search.

    Provides advanced querying capabilities including tag-based filtering
    and product similarity search for menu entities.

    Notes:
        Adheres to CompositeRepository interface. Eager-loads: tags.
        Performance: uses EXISTS subqueries for efficient tag filtering.
        Transactions: methods require active UnitOfWork session.
    """

    filter_to_column_mappers: ClassVar[list[FilterColumnMapper]] = [
        FilterColumnMapper(
            sa_model_type=MenuSaModel,
            filter_key_to_column_name={
                "id": "id",
                "author_id": "author_id",
                "client_id": "client_id",
                "description": "description",
                "created_at": "created_at",
                "updated_at": "updated_at",
            },
        ),
    ]

    def __init__(
        self,
        db_session: AsyncSession,
        repository_logger: RepositoryLogger | None = None,
    ):
        """Initialize menu repository with database session and logging.

        Args:
            db_session: Active SQLAlchemy async session.
            repository_logger: Optional logger for query tracking.
        """
        self._session = db_session

        # Create default logger if none provided
        if repository_logger is None:
            repository_logger = RepositoryLogger.create_logger("MenuRepository")

        self._repository_logger = repository_logger

        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=MenuMapper,
            domain_model_type=Menu,
            sa_model_type=MenuSaModel,
            filter_to_column_mappers=MenuRepo.filter_to_column_mappers,
            repository_logger=self._repository_logger,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Menu):
        """Add menu entity to repository.

        Args:
            entity: Menu domain object to persist.
        """
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Menu:
        """Retrieve menu by ID.

        Args:
            id: Unique identifier for the menu.

        Returns:
            Menu domain object.

        Raises:
            ValueError: If menu not found.
        """
        return await self._generic_repo.get(id)

    async def get_sa_instance(self, id: str) -> MenuSaModel:
        """Retrieve SQLAlchemy model instance by ID.

        Args:
            id: Unique identifier for the menu.

        Returns:
            MenuSaModel SQLAlchemy instance.
        """
        return await self._generic_repo.get_sa_instance(id)

    def _tag_match_condition(
        self,
        outer_menu: type[MenuSaModel],
        tags: list[tuple[str, str, str]],
    ) -> ColumnElement[bool]:
        """Build tag matching condition for positive tag filtering.

        Args:
            outer_menu: Aliased menu model for correlation.
            tags: List of (key, value, author_id) tuples to include.

        Returns:
            SQLAlchemy condition requiring all key groups to match.

        Notes:
            Groups tags by key and creates AND condition across key groups.
            Within each key group, creates OR condition for values.
            Uses outer_menu.tags.any() which generates EXISTS under the hood.
        """
        # group tags by key
        tags_sorted = sorted(tags, key=lambda t: t[0])
        conditions = []
        for key, group in groupby(tags_sorted, key=lambda t: t[0]):
            group_list = list(group)
            author_id = group_list[0][2]
            values = [t[1] for t in group_list]

            # outer_menu.tags.any(...) will generate EXISTS(...) under the hood
            cond = outer_menu.tags.any(
                and_(
                    TagSaModel.key == key,
                    TagSaModel.value.in_(values),
                    TagSaModel.author_id == author_id,
                    TagSaModel.type == "menu",
                )
            )
            conditions.append(cond)

        # require _all_ key groups to match
        return and_(*conditions)

    def _tag_not_exists_condition(
        self,
        outer_menu: type[MenuSaModel],
        tags: list[tuple[str, str, str]],
    ) -> ColumnElement[bool]:
        """Build tag exclusion condition for negative tag filtering.

        Args:
            outer_menu: Aliased menu model for correlation.
            tags: List of (key, value, author_id) tuples to exclude.

        Returns:
            SQLAlchemy condition requiring none of the tags to exist.

        Notes:
            Simply negates the positive tag match condition.
        """
        # Simply negate the positive match
        return ~self._tag_match_condition(outer_menu, tags)

    async def query(
        self,
        *,
        filters: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        _return_sa_instance: bool = False,
    ) -> list[Menu]:
        """Query menus with advanced filtering and product search.

        Args:
            filters: Dictionary of filter criteria including tag and product filters.
            starting_stmt: Custom SQLAlchemy select statement to build upon.
            _return_sa_instance: Whether to return SQLAlchemy models.

        Returns:
            List of Menu domain objects matching criteria.

        Notes:
            Handles product similarity search and tag filtering automatically.
            Product search uses fuzzy matching with limit of 3 similar products.
            Tag filtering uses EXISTS subqueries for efficiency.
        """
        filters = filters or {}

        # Use the track_query context manager for structured logging
        async with self._repository_logger.track_query(
            operation="query", entity_type="Menu", filter_count=len(filters)
        ) as query_context:

            # Handle product name similarity search
            if filters.get("product_name"):
                product_name = filters.pop("product_name")
                product_repo = ProductRepo(self._session)
                products = await product_repo.list_top_similar_names(
                    product_name, limit=3
                )
                product_ids = [product.id for product in products]
                filters["products"] = product_ids

                query_context["product_similarity_search"] = {
                    "search_term": product_name,
                    "products_found": len(product_ids),
                }
                self._repository_logger.debug_filter_operation(
                    (
                        f"Applied product similarity search: found {len(product_ids)} "
                        f"products for '{product_name}'"
                    ),
                    product_search_term=product_name,
                    products_found=len(product_ids),
                )

            # Handle tag filtering
            if "tags" in filters or "tags_not_exists" in filters:
                query_context["tag_filtering"] = True

                outer_menu: type[MenuSaModel] = aliased(self.sa_model_type)
                stmt = (
                    starting_stmt.select(outer_menu)
                    if starting_stmt is not None
                    else select(outer_menu)
                )

                if filters.get("tags"):
                    tags = filters.pop("tags")
                    stmt = stmt.where(self._tag_match_condition(outer_menu, tags))

                    query_context["positive_tags"] = len(tags)
                    self._repository_logger.debug_filter_operation(
                        f"Applied positive tag filter: {len(tags)} tag conditions",
                        tags_count=len(tags),
                    )

                if filters.get("tags_not_exists"):
                    tags_not = filters.pop("tags_not_exists")
                    stmt = stmt.where(
                        self._tag_not_exists_condition(outer_menu, tags_not)
                    )

                    query_context["negative_tags"] = len(tags_not)
                    self._repository_logger.debug_filter_operation(
                        (
                            f"Applied negative tag filter: {len(tags_not)} "
                            f"exclusion conditions"
                        ),
                        exclusion_tags_count=len(tags_not),
                    )

                stmt = stmt.distinct()

                results = await self._generic_repo.query(
                    filters=filters,
                    starting_stmt=stmt,
                    already_joined={str(TagSaModel)},
                    sa_model=outer_menu,
                    _return_sa_instance=_return_sa_instance,
                )

                query_context["result_count"] = len(results)
                return results

            results = await self._generic_repo.query(
                filters=filters,
                starting_stmt=starting_stmt,
                _return_sa_instance=_return_sa_instance,
            )
            query_context["result_count"] = len(results)
            return results

    def list_filter_options(self) -> dict[str, dict]:
        """Return available filter and sort options for frontend.

        Returns:
            Dictionary mapping filter types to available options.
        """
        return {
            "sort": {
                "type": FrontendFilterTypes.SORT.value,
                "options": [],
            },
        }

    async def persist(self, domain_obj: Menu) -> None:
        """Persist menu changes to database.

        Args:
            domain_obj: Menu domain object to persist.
        """
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[Menu] | None = None) -> None:
        """Persist multiple menu entities in batch.

        Args:
            domain_entities: List of Menu domain objects to persist.
        """
        await self._generic_repo.persist_all(domain_entities)
