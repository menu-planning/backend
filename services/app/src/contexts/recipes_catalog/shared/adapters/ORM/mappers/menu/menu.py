import src.contexts.seedwork.shared.adapters.utils as utils
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.menu.menu import (
    MenuSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.menu.menu_item import (
    MenuItemSaModel,
)
from src.contexts.recipes_catalog.shared.domain.entities.menu import Menu
from src.contexts.recipes_catalog.shared.domain.value_objects.menu_item import MenuItem
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.tag.tag import TagMapper


class MenuMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession,
        domain_obj: Menu,
        merge: bool = True,
    ) -> MenuSaModel:
        merge_children = False
        menu_on_db = await utils.get_sa_entity(
            session=session, sa_model=MenuSaModel, filter={"id": domain_obj.id}
        )
        if not menu_on_db and merge:
            # if menu on db then it will be merged
            # so we should not need merge the children
            merge_children = True

        items_tasks = (
            [
                _MenuItemMapper.map_domain_to_sa(
                    session=session,
                    domain_obj=i,
                    parent=domain_obj,
                    merge=merge_children,
                )
                for i in domain_obj.items
            ]
            if domain_obj.items
            else []
        )
        if items_tasks:
            items = await utils.gather_results_with_timeout(
                items_tasks,
                timeout=5,
                timeout_message="Timeout mapping items in MenuItemMapper",
            )
        else:
            items = []

        tags_tasks = (
            [TagMapper.map_domain_to_sa(session, i) for i in domain_obj.tags]
            if domain_obj.tags
            else []
        )

        if tags_tasks:
            tags = await utils.gather_results_with_timeout(
                tags_tasks,
                timeout=5,
                timeout_message="Timeout mapping tags in TagMapper",
            )
        else:
            tags = []

        sa_menu = MenuSaModel(
            id=domain_obj.id,
            author_id=domain_obj.author_id,
            client_id=domain_obj.client_id,
            description=domain_obj.description,
            created_at=domain_obj.created_at,
            updated_at=domain_obj.updated_at,
            discarded=domain_obj.discarded,
            version=domain_obj.version,
            # relationships
            items=items,
            tags=tags,
        )
        if menu_on_db and merge:
            sa_menu = session.merge(sa_menu)  # , menu_on_db)
            return sa_menu
        return sa_menu

    @staticmethod
    def map_sa_to_domain(sa_obj: MenuSaModel) -> Menu:
        return Menu(
            id=sa_obj.id,
            author_id=sa_obj.author_id,
            client_id=sa_obj.client_id,
            description=sa_obj.description,
            created_at=sa_obj.created_at,
            updated_at=sa_obj.updated_at,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
            # relationships
            items=[_MenuItemMapper.map_sa_to_domain(i) for i in sa_obj.items],
            tags=[TagMapper.map_sa_to_domain(i) for i in sa_obj.tags],
        )


class _MenuItemMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession,
        domain_obj: MenuItem,
        parent: Menu,
        merge: bool = True,
    ) -> MenuItemSaModel:
        item_on_db = await utils.get_sa_entity(
            session=session,
            sa_model=MenuItemSaModel,
            filter={
                "menu_id": parent.id,
                "week": domain_obj.week,
                "weekday": domain_obj.weekday,
                "meal_type": domain_obj.meal_type,
            },
        )
        if item_on_db and merge:
            sa_item = MenuItemSaModel(
                id=item_on_db.id,
                meal_id=domain_obj.meal_id,
                week=domain_obj.week,
                weekday=domain_obj.weekday,
                hour=domain_obj.hour,
                meal_type=domain_obj.meal_type,
            )
            sa_item = await session.merge(sa_item)  # , item_on_db)
            return sa_item
        if item_on_db and not merge:
            return MenuItemSaModel(
                id=item_on_db.id,
                menu_id=parent.id,
                meal_id=domain_obj.meal_id,
                week=domain_obj.week,
                weekday=domain_obj.weekday,
                hour=domain_obj.hour,
                meal_type=domain_obj.meal_type,
            )
        return MenuItemSaModel(
            menu_id=parent.id,
            meal_id=domain_obj.meal_id,
            week=domain_obj.week,
            weekday=domain_obj.weekday,
            hour=domain_obj.hour,
            meal_type=domain_obj.meal_type,
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: MenuItemSaModel) -> MenuItem:
        return MenuItem(
            meal_id=sa_obj.meal_id,
            week=sa_obj.week,
            weekday=sa_obj.weekday,
            hour=sa_obj.hour,
            meal_type=sa_obj.meal_type,
        )
