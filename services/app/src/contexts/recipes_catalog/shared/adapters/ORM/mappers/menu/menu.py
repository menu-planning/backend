from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

import src.contexts.seedwork.shared.adapters.utils as utils
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.menu.menu import (
    MenuSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.menu.menu_meal import (
    MenuMealSaModel,
)
from src.contexts.recipes_catalog.shared.domain.entities.menu import Menu
from src.contexts.recipes_catalog.shared.domain.enums import MealType
from src.contexts.recipes_catalog.shared.domain.value_objects.menu_meal import MenuMeal
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.nutri_facts import NutriFactsMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.tag.tag import TagMapper
from src.contexts.shared_kernel.domain.enums import Weekday


class MenuMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession,
        domain_obj: Menu,
        merge: bool = True,
    ) -> MenuSaModel:
        merge_children = False
        menu_on_db = await utils.get_sa_entity(
            session=session, sa_model_type=MenuSaModel, filter={"id": domain_obj.id}
        )
        if not menu_on_db and merge:
            # if menu on db then it will be merged
            # so we should not need merge the children
            merge_children = True

        meals_tasks = (
            [
                _MenuMealMapper.map_domain_to_sa(
                    session=session,
                    domain_obj=i,
                    parent=domain_obj,
                    merge=merge_children,
                )
                for i in domain_obj.meals.values()
            ]
            if domain_obj.meals
            else []
        )
        if meals_tasks:
            meals = await utils.gather_results_with_timeout(
                meals_tasks,
                timeout=5,
                timeout_message="Timeout mapping items in MenuMealMapper",
            )
        else:
            meals = []

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

        sa_menu_kwargs = {
            "id": domain_obj.id,
            "author_id": domain_obj.author_id,
            "client_id": domain_obj.client_id,
            "description": domain_obj.description,
            "created_at": (
                domain_obj.created_at if domain_obj.created_at else datetime.now()
            ),
            "updated_at": (
                domain_obj.updated_at if domain_obj.created_at else datetime.now()
            ),
            "discarded": domain_obj.discarded,
            "version": domain_obj.version,
            # relationships
            "meals": meals,
            "tags": tags,
        }
        # if not domain_obj.created_at:
        #     sa_menu_kwargs.pop("created_at")
        #     sa_menu_kwargs.pop("updated_at")
        sa_menu = MenuSaModel(**sa_menu_kwargs)
        if menu_on_db and merge:
            return await session.merge(sa_menu)  # , meal_on_db)
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
            meals=[_MenuMealMapper.map_sa_to_domain(i) for i in sa_obj.meals],
            tags=[TagMapper.map_sa_to_domain(i) for i in sa_obj.tags],
        )


class _MenuMealMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession,
        domain_obj: MenuMeal,
        parent: Menu,
        merge: bool = True,
    ) -> MenuMealSaModel:
        item_on_db = await utils.get_sa_entity(
            session=session,
            sa_model_type=MenuMealSaModel,
            filter={
                "menu_id": parent.id,
                "week": str(domain_obj.week),
                "weekday": domain_obj.weekday.value,
                "meal_type": domain_obj.meal_type.value,
            },
        )
        if item_on_db and merge:
            sa_item = MenuMealSaModel(
                id=item_on_db.id,
                meal_id=domain_obj.meal_id,
                meal_name=domain_obj.meal_name,
                week=str(domain_obj.week),
                weekday=domain_obj.weekday.value,
                hour=domain_obj.hour,
                meal_type=domain_obj.meal_type.value,
                nutri_facts=domain_obj.nutri_facts,
            )
            sa_item = await session.merge(sa_item)  # , item_on_db)
            return sa_item
        if item_on_db and not merge:
            return MenuMealSaModel(
                id=item_on_db.id,
                menu_id=parent.id,
                meal_id=domain_obj.meal_id,
                meal_name=domain_obj.meal_name,
                week=str(domain_obj.week),
                weekday=domain_obj.weekday.value,
                hour=domain_obj.hour,
                meal_type=domain_obj.meal_type.value,
                nutri_facts=domain_obj.nutri_facts,
            )
        return MenuMealSaModel(
            menu_id=parent.id,
            meal_id=domain_obj.meal_id,
            meal_name=domain_obj.meal_name,
            week=str(domain_obj.week),
            weekday=domain_obj.weekday.value,
            hour=domain_obj.hour,
            meal_type=domain_obj.meal_type.value,
            nutri_facts=domain_obj.nutri_facts,
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: MenuMealSaModel) -> MenuMeal:
        return MenuMeal(
            meal_id=sa_obj.meal_id,
            meal_name=sa_obj.meal_name,
            week=int(sa_obj.week),
            weekday=Weekday(sa_obj.weekday),
            hour=sa_obj.hour,
            meal_type=MealType(sa_obj.meal_type),
            nutri_facts=NutriFactsMapper.map_sa_to_domain(sa_obj.nutri_facts),
        )
