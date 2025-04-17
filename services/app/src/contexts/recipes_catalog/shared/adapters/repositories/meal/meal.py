from itertools import groupby
from typing import Any

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.contexts.products_catalog.shared.adapters.repositories.product import \
    ProductRepo
from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.meal.meal import \
    MealMapper
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.meal.associations import \
    meals_tags_association
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.meal.meal import \
    MealSaModel
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.ingredient import \
    IngredientSaModel
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.recipe import \
    RecipeSaModel
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.seedwork.shared.adapters.enums import FrontendFilterTypes
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository, FilterColumnMapper, SaGenericRepository)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag import \
    TagSaModel
from src.logging.logger import logger


class MealRepo(CompositeRepository[Meal, MealSaModel]):
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=MealSaModel,
            filter_key_to_column_name={
                "id": "id",
                "name": "name",
                "menu_id": "menu_id",
                "author_id": "author_id",
                "total_time": "total_time",
                "weight_in_grams": "weight_in_grams",
                "created_at": "created_at",
                "updated_at": "updated_at",
                "like": "like",
                "calories": "calories",
                "protein": "protein",
                "carbohydrate": "carbohydrate",
                "total_fat": "total_fat",
                "saturated_fat": "saturated_fat",
                "trans_fat": "trans_fat",
                "sugar": "sugar",
                "sodium": "sodium",
                "calorie_density": "calorie_density",
                "carbo_percentage": "carbo_percentage",
                "protein_percentage": "protein_percentage",
                "total_fat_percentage": "total_fat_percentage",
            },
        ),
        FilterColumnMapper(
            sa_model_type=RecipeSaModel,
            filter_key_to_column_name={
                "recipe_id": "id",
                "recipe_name": "name",
            },
            join_target_and_on_clause=[(RecipeSaModel, MealSaModel.recipes)],
        ),
        FilterColumnMapper(
            sa_model_type=IngredientSaModel,
            filter_key_to_column_name={"products": "product_id"},
            join_target_and_on_clause=[
                (RecipeSaModel, MealSaModel.recipes),
                (IngredientSaModel, RecipeSaModel.ingredients),
            ],
        ),
    ]

    def __init__(
        self,
        db_session: AsyncSession,
    ):
        self._session = db_session
        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=MealMapper,
            domain_model_type=Meal,
            sa_model_type=MealSaModel,
            filter_to_column_mappers=MealRepo.filter_to_column_mappers,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Meal):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Meal:
        model_obj = await self._generic_repo.get(id)
        return model_obj

    async def get_sa_instance(self, id: str) -> MealSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj

    def get_subquery_for_tags_not_exists(self, outer_meal, tags: list[tuple[str, str, str]]) -> Select:
        conditions = []
        for t in tags:
            key, value, author_id = t
            condition = (
                select(1)
                .select_from(meals_tags_association)
                .join(TagSaModel, meals_tags_association.c.tag_id == TagSaModel.id)
                .where(
                    meals_tags_association.c.meal_id == outer_meal.id,
                    TagSaModel.key == key,
                    TagSaModel.value == value,
                    TagSaModel.author_id == author_id,
                    TagSaModel.type == "meal",
                )
            ).exists()
            conditions.append(condition)
        return or_(*conditions)
    
    def get_subquery_for_tags(self, outer_meal, tags: list[tuple[str, str, str]]) -> Select:
        """
        For the given list of tag tuples (key, value, author_id),
        this builds a condition such that:
        - For tag tuples sharing the same key, at least one of the provided values must match.
        - For different keys, every key group must be matched.
        
        This is equivalent to:
        EXISTS (SELECT 1 FROM association JOIN tag 
                WHERE association.meal_id = outer_meal.id 
                    AND tag.key = key1 
                    AND (tag.value = value1 OR tag.value = value2 ... )
                    AND tag.author_id = <common_author> 
                    AND tag.type = "meal")
        AND
        EXISTS (SELECT 1 FROM association JOIN tag 
                WHERE association.meal_id = outer_meal.id 
                    AND tag.key = key2 
                    AND (tag.value = value3 OR tag.value = value4 ... )
                    AND tag.author_id = <common_author> 
                    AND tag.type = "meal")
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
                TagSaModel.type == "meal"
            )

            # Create a correlated EXISTS subquery for this key group.
            subquery = (
                select(1)
                .select_from(meals_tags_association)
                .join(TagSaModel, meals_tags_association.c.tag_id == TagSaModel.id)
                .where(
                    meals_tags_association.c.meal_id == outer_meal.id,
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
    ) -> list[Meal]:
        filter = filter or {}
        if filter.get("product_name"):
            product_name = filter.pop("product_name")
            product_repo = ProductRepo(self._session)
            products = await product_repo.list_top_similar_names(product_name, limit=3)
            product_ids = [product.id for product in products]
            filter["products"] = product_ids
        if "tags" in filter or "tags_not_exists" in filter:
            outer_meal = aliased(self.sa_model_type)
            starting_stmt = select(outer_meal)
            if filter.get("tags"):
                tags = filter.pop("tags")
                subquery = self.get_subquery_for_tags(outer_meal, tags)
                starting_stmt = starting_stmt.where(subquery)
            if filter.get("tags_not_exists"):
                tags_not_exists = filter.pop("tags_not_exists")
                subquery = self.get_subquery_for_tags_not_exists(outer_meal, tags_not_exists)
                starting_stmt = starting_stmt.where(~subquery)
            model_objs: list[Meal] = await self._generic_repo.query(
                filter=filter,
                starting_stmt=starting_stmt,
                already_joined={str(TagSaModel)},
                sa_model=outer_meal
            )
            return model_objs
        model_objs: list[Meal] = await self._generic_repo.query(filter=filter,starting_stmt=starting_stmt)
        return model_objs
    
        # if filter.get("tags"):
        #     tags = filter.pop("tags")
        #     for t in tags:
        #         key, value, author_id = t
        #         subquery = (
        #             select(MealSaModel.id)
        #             .join(TagSaModel, MealSaModel.tags)
        #             .where(
        #                 meals_tags_association.c.meal_id == MealSaModel.id,
        #                 TagSaModel.key == key,
        #                 TagSaModel.value == value,
        #                 TagSaModel.author_id == author_id,
        #             )
        #         ).exists()
        #         if starting_stmt is None:
        #             starting_stmt = select(self.sa_model_type)
        #         starting_stmt = starting_stmt.where(subquery)
        # if filter.get("tags_not_exists"):
        #     tags_not_exists = filter.pop("tags_not_exists")
        #     for t in tags_not_exists:
        #         key, value, author_id = t
        #         subquery = (
        #             select(MealSaModel.id)
        #             .join(TagSaModel, MealSaModel.tags)
        #             .where(
        #                 meals_tags_association.c.meal_id == MealSaModel.id,
        #                 TagSaModel.key == key,
        #                 TagSaModel.value == value,
        #                 TagSaModel.author_id == author_id,
        #             )
        #         ).exists()
        #         if starting_stmt is None:
        #             starting_stmt = select(self.sa_model_type)
        #         starting_stmt = starting_stmt.where(~subquery)
        #     if starting_stmt is None:
        #         starting_stmt = select(self.sa_model_type)
        #     starting_stmt = starting_stmt.where(~subquery)
        # if filter.get("product_name"):
        #     product_name = filter.pop("product_name")
        #     product_repo = ProductRepo(self._session)
        #     products = await product_repo.list_top_similar_names(product_name, limit=3)
        #     product_ids = [product.id for product in products]
        #     filter["products"] = product_ids
        # model_objs: list[Meal] = await self._generic_repo.query(
        #     filter=filter,
        #     starting_stmt=starting_stmt,
        #     # _return_sa_instance=True,
        # )
        # return model_objs

    def list_filter_options(self) -> dict[str, dict]:
        return {
            "sort": {
                "type": FrontendFilterTypes.SORT.value,
                "options": [
                    "name",
                    "created_at",
                    "updated_at",
                    "total_time",
                    "average_taste_rating",
                    "average_convenience_rating",
                    "privacy",
                    "calories",
                    "protein",
                    "carbohydrate",
                    "total_fat",
                    "saturated_fat",
                    "trans_fat",
                    "dietary_fiber",
                    "sodium",
                    "sugar",
                ],
            },
        }

    async def persist(self, domain_obj: Meal) -> None:
        logger.debug(f"Persisting meal: {domain_obj}")
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self) -> None:
        await self._generic_repo.persist_all()
