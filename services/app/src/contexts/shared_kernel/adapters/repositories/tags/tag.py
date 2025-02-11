from typing import Any

from sqlalchemy import Select, Table, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)
from src.contexts.shared_kernel.adapters.ORM.mappers.tag.tag import TagMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag import TagSaModel
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class TagRepo(CompositeRepository[Tag, TagSaModel]):
    filter_to_column_mappers = [
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
        await self._generic_repo.add(entity)

    # async def get(self, id: str) -> Tag:
    #     model_obj = await self._generic_repo.get(id)
    #     return model_obj

    # async def get_sa_instance(self, id: str) -> S:
    #     sa_obj = await self._generic_repo.get_sa_instance(id)
    #     return sa_obj

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt: Select | None = None,
    ) -> list[Tag]:
        model_objs: list[Tag] = await self._generic_repo.query(
            filter=filter, starting_stmt=starting_stmt
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
        await self._session.execute(
            delete(association_table).where(association_table.c.tag_id == tag.id)
        )
        await self._session.delete(tag)

    async def persist(self, domain_obj: Tag) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self) -> None:
        await self._generic_repo.persist_all()
