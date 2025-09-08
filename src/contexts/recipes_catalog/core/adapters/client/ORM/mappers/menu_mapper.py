"""Mapper to convert between Menu domain objects and SQLAlchemy models."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.menu_meal_sa_model import (
    MenuMealSaModel,
)
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.menu_sa_model import (
    MenuSaModel,
)
from src.contexts.recipes_catalog.core.domain.client.entities.menu import Menu
from src.contexts.recipes_catalog.core.domain.client.value_objects.menu_meal import (
    MenuMeal,
)
from src.contexts.seedwork.adapters.ORM.mappers import helpers
from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.nutri_facts_mapper import (
    NutriFactsMapper,
)
from src.contexts.shared_kernel.adapters.ORM.mappers.tag.tag_mapper import TagMapper


class MenuMapper(ModelMapper):
    """Mapper for converting between Menu domain objects and SQLAlchemy models.

    Handles complex mapping including nested menu meals, tags, and nutritional facts.
    Performs concurrent mapping of child entities with timeout protection.

    Notes:
        Lossless: Yes. Timezone: UTC assumption. Currency: N/A.
        Handles async operations with 5-second timeout for child entity mapping.
        Maps menu meals with week/weekday scheduling information.
    """

    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession,
        domain_obj: Menu,
        merge: bool = True,
    ) -> MenuSaModel:
        """Map domain menu to SQLAlchemy model.

        Args:
            session: Database session for operations.
            domain_obj: Menu domain object to map.
            merge: Whether to merge with existing database entity.

        Returns:
            SQLAlchemy menu model ready for persistence.

        Notes:
            Maps child entities (menu meals, tags) concurrently with 5-second timeout.
            Handles existing menu merging and child entity updates.
            Menu meals include week/weekday scheduling and meal type information.
        """
        merge_children = False
        menu_on_db = await helpers.get_sa_entity(
            session=session,
            sa_model_type=MenuSaModel,
            filters={"id": domain_obj.id},
        )
        if not menu_on_db and merge:
            merge_children = True

        menu_meals_tasks = (
            [
                _MenuMealMapper.map_domain_to_sa(
                    session=session,
                    domain_obj=i,
                    parent=domain_obj,
                    merge=merge_children,
                )
                for i in domain_obj.meals
            ]
            if domain_obj.meals
            else []
        )
        if menu_meals_tasks:
            menu_meals = await helpers.gather_results_with_timeout(
                menu_meals_tasks,
                timeout=5,
                timeout_message="Timeout mapping items in MenuMealMapper",
            )
        else:
            menu_meals = []

        tags_tasks = (
            [TagMapper.map_domain_to_sa(session, i) for i in domain_obj.tags]
            if domain_obj.tags
            else []
        )

        if tags_tasks:
            tags = await helpers.gather_results_with_timeout(
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
                domain_obj.created_at if domain_obj.created_at else datetime.now(UTC)
            ),
            "updated_at": (
                domain_obj.updated_at if domain_obj.created_at else datetime.now(UTC)
            ),
            "discarded": domain_obj.discarded,
            "version": domain_obj.version,
            # relationships
            "meals": menu_meals,
            "tags": tags,
        }
        sa_menu = MenuSaModel(**sa_menu_kwargs)
        if menu_on_db and merge:
            return await session.merge(sa_menu)  # , meal_on_db)
        return sa_menu

    @staticmethod
    def map_sa_to_domain(sa_obj: MenuSaModel) -> Menu:
        """Map SQLAlchemy menu model to domain object.

        Args:
            sa_obj: SQLAlchemy menu model to convert.

        Returns:
            Menu domain object with all relationships mapped.

        Notes:
            Maps nested menu meals and tags using their respective mappers.
            Converts week string back to integer for domain model.
        """
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
            meals={_MenuMealMapper.map_sa_to_domain(i) for i in sa_obj.meals},
            tags={TagMapper.map_sa_to_domain(i) for i in sa_obj.tags},
        )


class _MenuMealMapper(ModelMapper):
    """Private mapper for converting between MenuMeal domain objects and SQLAlchemy models.

    Handles menu meal mapping within menu context, including week/weekday scheduling,
    meal type classification, and nutritional facts.

    Notes:
        Lossless: Yes. Timezone: N/A. Currency: N/A.
        Maps week as string in database, converts to int in domain.
        Handles meal scheduling with week, weekday, hour, and meal type.
    """

    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession,
        domain_obj: MenuMeal,
        parent: Menu,
        merge: bool = True,
    ) -> MenuMealSaModel:
        """Map domain menu meal to SQLAlchemy model.

        Args:
            session: Database session for operations.
            domain_obj: MenuMeal domain object to map.
            parent: Parent menu domain object.
            merge: Whether to merge with existing entity.

        Returns:
            SQLAlchemy menu meal model ready for persistence.

        Notes:
            Searches for existing menu meal by menu_id, week, weekday, and meal_type.
            Updates existing meal if found, otherwise creates new one.
            Converts week integer to string for database storage.
            Maps nutritional facts using NutriFactsMapper.
        """
        item_on_db = await helpers.get_sa_entity(
            session=session,
            sa_model_type=MenuMealSaModel,
            filters={
                "menu_id": parent.id,
                "week": str(domain_obj.week),
                "weekday": domain_obj.weekday,
                "meal_type": domain_obj.meal_type,
            },
        )
        if item_on_db and merge:
            sa_item = MenuMealSaModel(
                id=item_on_db.id,
                meal_id=domain_obj.meal_id,
                meal_name=domain_obj.meal_name,
                week=str(domain_obj.week),
                weekday=domain_obj.weekday,
                hour=domain_obj.hour,
                meal_type=domain_obj.meal_type,
                nutri_facts=await NutriFactsMapper.map_domain_to_sa(
                    session=session,
                    domain_obj=domain_obj.nutri_facts,
                ),
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
                weekday=domain_obj.weekday,
                hour=domain_obj.hour,
                meal_type=domain_obj.meal_type,
                nutri_facts=await NutriFactsMapper.map_domain_to_sa(
                    session=session,
                    domain_obj=domain_obj.nutri_facts,
                ),
            )
        return MenuMealSaModel(
            menu_id=parent.id,
            meal_id=domain_obj.meal_id,
            meal_name=domain_obj.meal_name,
            week=str(domain_obj.week),
            weekday=domain_obj.weekday,
            hour=domain_obj.hour,
            meal_type=domain_obj.meal_type,
            nutri_facts=await NutriFactsMapper.map_domain_to_sa(
                session=session,
                domain_obj=domain_obj.nutri_facts,
            ),
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: MenuMealSaModel) -> MenuMeal:
        """Map SQLAlchemy menu meal model to domain object.

        Args:
            sa_obj: SQLAlchemy menu meal model to convert.

        Returns:
            MenuMeal domain object.

        Notes:
            Converts week string back to integer for domain model.
            Maps nutritional facts using NutriFactsMapper.
        """
        return MenuMeal(
            meal_id=sa_obj.meal_id,
            meal_name=sa_obj.meal_name,
            week=int(sa_obj.week),
            weekday=sa_obj.weekday,
            hour=sa_obj.hour,
            meal_type=sa_obj.meal_type,
            nutri_facts=NutriFactsMapper.map_sa_to_domain(sa_obj.nutri_facts),
        )
