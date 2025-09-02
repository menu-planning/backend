from typing import Any, ClassVar

from sqlalchemy import Select, Table, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.seedwork.adapters.repositories.filter_mapper import FilterColumnMapper
from src.contexts.seedwork.adapters.repositories.sa_generic_repository import (
    SaGenericRepository,
)
from src.contexts.shared_kernel.adapters.ORM.mappers.tag.tag_mapper import TagMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class TagRepo:
    """SQLAlchemy repository for Tag value objects.

    Notes:
        Adheres to Tag repository interface. Eager-loads: none.
        Performance: Uses generic repository with filter mappings for efficient queries.
        Transactions: methods require active UnitOfWork session.
    """
    filter_to_column_mappers: ClassVar[list[FilterColumnMapper]] = [
        FilterColumnMapper(
            sa_model_type=TagSaModel,
            filter_key_to_column_name={
                "key": "key",
                "value": "value",
                "author_id": "author_id",
                "type": "type",
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
            data_mapper=TagMapper,
            domain_model_type=Tag,
            sa_model_type=TagSaModel,
            filter_to_column_mappers=TagRepo.filter_to_column_mappers,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Tag):
        error_msg = "Tags must be added through Entities that use them."
        raise NotImplementedError(error_msg)

    async def get(self, entity_id: str) -> Tag:
        return await self._generic_repo.get(entity_id)

    async def get_sa_instance(self, entity_id: str) -> TagSaModel:
        return await self._generic_repo.get_sa_instance(entity_id)

    async def query(
        self,
        *,
        filters: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
    ) -> list[Tag]:
        filters = filters or {}
        model_objs: list[Tag] = await self._generic_repo.query(
            filters=filters, starting_stmt=starting_stmt
        )
        return model_objs

    async def delete(self, domain_obj: Tag, association_table: Table) -> None:
        tag = await self._session.execute(
            select(TagSaModel)
            .where(TagSaModel.key == domain_obj.key)
            .where(TagSaModel.value == domain_obj.value)
            .where(TagSaModel.author_id == domain_obj.author_id)
            .where(TagSaModel.type == domain_obj.type)
        )
        tag = tag.scalars().first()
        assert tag is not None, "Tag not found in the database"
        await self._session.execute(
            delete(association_table).where(association_table.c.tag_id == tag.id)
        )
        await self._session.delete(tag)

    async def persist(self, domain_obj: Tag) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[Tag] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
