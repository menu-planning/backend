"""Repository facade for Products Catalog brands."""

from typing import Any, ClassVar

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.ORM.mappers.classification.brand_mapper import (
    BrandMapper,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.brand import (
    BrandSaModel,
)
from src.contexts.products_catalog.core.domain.entities.classification.brand import (
    Brand,
)
from src.contexts.seedwork.adapters.repositories.filter_mapper import FilterColumnMapper
from src.contexts.seedwork.adapters.repositories.protocols import CompositeRepository
from src.contexts.seedwork.adapters.repositories.sa_generic_repository import (
    SaGenericRepository,
)


class BrandRepo(CompositeRepository[Brand, BrandSaModel]):
    """Repository for Brand domain entity.

    Provides CRUD operations and querying capabilities for Brand entities
    with filtering support.
    """

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
        """Initialize brand repository.

        Args:
            db_session: Database session for operations.
        """
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
        """Add brand entity to repository.

        Args:
            entity: Brand entity to add.
        """
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Brand:
        """Get brand entity by ID.

        Args:
            id: Brand identifier.

        Returns:
            Brand entity.
        """
        return await self._generic_repo.get(id)

    async def get_sa_instance(self, id: str) -> BrandSaModel:
        """Get SQLAlchemy brand model by ID.

        Args:
            id: Brand identifier.

        Returns:
            BrandSaModel instance.
        """
        return await self._generic_repo.get_sa_instance(id)

    async def query(
        self,
        *,
        filters: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        _return_sa_instance: bool = False,
    ) -> list[Brand]:
        """Query brand entities with filters and custom statement.

        Args:
            filters: Filter criteria for querying.
            starting_stmt: Custom SQLAlchemy select statement.
            _return_sa_instance: Whether to return SQLAlchemy instances.

        Returns:
            List of Brand entities.
        """
        filters = filters or {}
        model_objs: list[Brand] = await self._generic_repo.query(
            filters=filters,
            starting_stmt=starting_stmt,
            _return_sa_instance=_return_sa_instance,
        )
        return model_objs

    async def persist(self, domain_obj: Brand) -> None:
        """Persist brand entity to database.

        Args:
            domain_obj: Brand entity to persist.
        """
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[Brand] | None = None) -> None:
        """Persist all brand entities to database.

        Args:
            domain_entities: List of Brand entities to persist.
        """
        await self._generic_repo.persist_all(domain_entities)
