from itertools import groupby
from typing import Any

from sqlalchemy import ColumnElement, Select, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.client.client import \
    ClientMapper
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.client.associations import \
    clients_tags_association
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.client.client import \
    ClientSaModel
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.menu.menu import MenuSaModel
from src.contexts.recipes_catalog.shared.domain.entities.client import Client
from src.contexts.seedwork.shared.adapters.enums import FrontendFilterTypes
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository, FilterColumnMapper, SaGenericRepository)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag import \
    TagSaModel
from src.logging.logger import logger


class ClientRepo(CompositeRepository[Client, ClientSaModel]):
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=ClientSaModel,
            filter_key_to_column_name={
                "id": "id",
                "author_id": "author_id",
                "created_at": "created_at",
                "updated_at": "updated_at",
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
    ):
        self._session = db_session
        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=ClientMapper,
            domain_model_type=Client,
            sa_model_type=ClientSaModel,
            filter_to_column_mappers=ClientRepo.filter_to_column_mappers,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Client):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Client:
        model_obj = await self._generic_repo.get(id)
        return model_obj # type: ignore

    async def get_sa_instance(self, id: str) -> ClientSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj

    def get_subquery_for_tags_not_exists(self, outer_client, tags: list[tuple[str, str, str]]) -> ColumnElement[bool]:
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
    
    def get_subquery_for_tags(self, outer_client, tags: list[tuple[str, str, str]]) -> ColumnElement[bool]:
        """
        For the given list of tag tuples (key, value, author_id),
        this builds a condition such that:
        - For tag tuples sharing the same key, at least one of the provided values must match.
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
        """
        # Sort tags by key so groupby works correctly.
        tags_sorted = sorted(tags, key=lambda t: t[0])
        conditions = []

        for key, group in groupby(tags_sorted, key=lambda t: t[0]):
            group_list = list(group)
            # Since authors are always the same, take the author_id from the first tuple.
            author_id = group_list[0][2]
            # Build OR condition for all tag values under this key.
            value_conditions = [TagSaModel.value == t[1] for t in group_list]

            group_condition = and_(
                TagSaModel.key == key,
                or_(*value_conditions),
                TagSaModel.author_id == author_id,
                TagSaModel.type == "client"
            )

            # Create a correlated EXISTS subquery for this key group.
            subquery = (
                select(1)
                .select_from(clients_tags_association)
                .join(TagSaModel, clients_tags_association.c.tag_id == TagSaModel.id)
                .where(
                    clients_tags_association.c.client_id == outer_client.id,
                    group_condition
                )
            ).exists()

            conditions.append(subquery)

        # Combine the conditions for each key group with AND.
        return and_(*conditions)

    async def query(
        self,
        filter: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
    ) -> list[Client]:
        filter = filter or {}
        if "tags" in filter or "tags_not_exists" in filter:
            outer_client = aliased(self.sa_model_type)
            starting_stmt = select(outer_client)
            if filter.get("tags"):
                tags = filter.pop("tags")
                subquery = self.get_subquery_for_tags(outer_client, tags)
                starting_stmt = starting_stmt.where(subquery)
            if filter.get("tags_not_exists"):
                tags_not_exists = filter.pop("tags_not_exists")
                subquery = self.get_subquery_for_tags_not_exists(outer_client, tags_not_exists)
                starting_stmt = starting_stmt.where(~subquery)
            model_objs: list[Client] = await self._generic_repo.query(
                filter=filter,
                starting_stmt=starting_stmt,
                already_joined={str(TagSaModel)},
                sa_model=outer_client
            )
            return model_objs
        logger.debug('Inside client query and going to call generic repo')
        model_objs: list[Client] = await self._generic_repo.query(filter=filter,starting_stmt=starting_stmt)
        return model_objs
    
    def list_filter_options(self) -> dict[str, dict]:
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
        logger.debug(f"Persisting client: {domain_obj}")
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[Client] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
