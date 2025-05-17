from itertools import groupby
from typing import Any, Type

from sqlalchemy import ColumnElement, Select, and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.contexts.products_catalog.core.adapters.repositories.product import ProductRepo
from src.contexts.recipes_catalog.core.adapters.ORM.mappers.menu.menu import (
    MenuMapper,
)
from src.contexts.recipes_catalog.core.adapters.ORM.sa_models.menu.associations import (
    menus_tags_association,
)
from src.contexts.recipes_catalog.core.adapters.ORM.sa_models.menu.menu import (
    MenuSaModel,
)
from src.contexts.recipes_catalog.core.domain.entities.menu import Menu
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

    def _tag_match_condition(
        self,
        outer_menu: Type[MenuSaModel],
        tags: list[tuple[str, str, str]],
    ) -> ColumnElement[bool]:
        """
        Build a single AND(...) of `outer_menu.tags.any(...)` for each key-group.
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
                    TagSaModel.type == "meal",
                )
            )
            conditions.append(cond)

        # require _all_ key‐groups to match
        return and_(*conditions)


    def _tag_not_exists_condition(
        self,
        outer_menu: Type[MenuSaModel],
        tags: list[tuple[str, str, str]],
    ) -> ColumnElement[bool]:
        """
        Build the negation: none of these tags exist.
        """
        # Simply negate the positive match
        return ~self._tag_match_condition(outer_menu, tags)


    async def query(
        self,
        filter: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
    ) -> list[Menu]:
        filter = filter or {}
        if filter.get("product_name"):
            product_name = filter.pop("product_name")
            product_repo = ProductRepo(self._session)
            products = await product_repo.list_top_similar_names(product_name, limit=3)
            product_ids = [product.id for product in products]
            filter["products"] = product_ids

        if "tags" in filter or "tags_not_exists" in filter:
            outer_menu: Type[MenuSaModel] = aliased(self.sa_model_type)
            stmt = starting_stmt.select(outer_menu) if starting_stmt is not None else select(outer_menu)

            if filter.get("tags"):
                tags = filter.pop("tags")
                stmt = stmt.where(self._tag_match_condition(outer_menu, tags))

            if filter.get("tags_not_exists"):
                tags_not = filter.pop("tags_not_exists")
                stmt = stmt.where(self._tag_not_exists_condition(outer_menu, tags_not))
            
            stmt = stmt.distinct()

            return await self._generic_repo.query(
                filter=filter,
                starting_stmt=stmt,
                already_joined={str(TagSaModel)},
                sa_model=outer_menu
            )
        return await self._generic_repo.query(filter=filter,starting_stmt=starting_stmt)

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
