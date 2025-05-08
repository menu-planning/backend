from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.menu.menu import (
    MenuMapper,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.menu.associations import (
    menus_tags_association,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.menu.menu import (
    MenuSaModel,
)
from src.contexts.recipes_catalog.shared.domain.entities.menu import Menu
from src.contexts.seedwork.shared.adapters.enums import FrontendFilterTypes
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag import TagSaModel


class MenuRepo(CompositeRepository[Menu, MenuSaModel]):
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=MenuSaModel,
            filter_key_to_column_name={
                "id": "id",
                "author_id": "author_id",
                "client_id": "client_id",
                "created_at": "created_at",
                "updated_at": "updated_at",
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
            data_mapper=MenuMapper,
            domain_model_type=Menu, # type: ignore
            sa_model_type=MenuSaModel, # type: ignore
            filter_to_column_mappers=MenuRepo.filter_to_column_mappers,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type # type: ignore
        self.sa_model_type = self._generic_repo.sa_model_type # type: ignore
        self.seen = self._generic_repo.seen

    async def add(self, entity: Menu):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Menu:
        model_obj = await self._generic_repo.get(id)
        return model_obj # type: ignore

    async def get_sa_instance(self, id: str) -> MenuSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj # type: ignore

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt: Select | None = None,
    ) -> list[Menu]:
        if filter.get("tags"):
            tags = filter.pop("tags")
            for t in tags:
                key, value, author_id = t
                subquery = (
                    select(MenuSaModel.id)
                    .join(TagSaModel, MenuSaModel.tags)
                    .where(
                        menus_tags_association.c.menu_id == MenuSaModel.id,
                        TagSaModel.key == key,
                        TagSaModel.value == value,
                        TagSaModel.author_id == author_id,
                    )
                ).exists()
                if starting_stmt is None:
                    starting_stmt = select(self.sa_model_type) # type: ignore
                starting_stmt = starting_stmt.where(subquery) # type: ignore
        if filter.get("tags_not_exists"):
            tags_not_exists = filter.pop("tags_not_exists")
            for t in tags_not_exists:
                key, value, author_id = t
                subquery = (
                    select(MenuSaModel.id)
                    .join(TagSaModel, MenuSaModel.tags)
                    .where(
                        menus_tags_association.c.menu_id == MenuSaModel.id,
                        TagSaModel.key == key,
                        TagSaModel.value == value,
                        TagSaModel.author_id == author_id,
                    )
                ).exists()
                if starting_stmt is None:
                    starting_stmt = select(self.sa_model_type) # type: ignore
                starting_stmt = starting_stmt.where(~subquery) # type: ignore
            if starting_stmt is None:
                starting_stmt = select(self.sa_model_type) # type: ignore
            starting_stmt = starting_stmt.where(~subquery) # type: ignore
        model_objs: list[Menu] = await self._generic_repo.query(
            filter=filter,
            starting_stmt=starting_stmt,
            # _return_sa_instance=True,
        )
        return model_objs

    def list_filter_options(self) -> dict[str, dict]:
        return {
            "sort": {
                "type": FrontendFilterTypes.SORT.value,
                "options": [],
            },
        }

    async def persist(self, domain_obj: Menu) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[Menu] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
