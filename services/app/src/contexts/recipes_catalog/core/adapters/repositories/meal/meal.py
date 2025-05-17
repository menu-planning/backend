from itertools import groupby
from typing import Any, Type

from sqlalchemy import ColumnElement, Select, and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.contexts.products_catalog.core.adapters.repositories.product import \
    ProductRepo
from src.contexts.recipes_catalog.core.adapters.ORM.mappers.meal.meal import \
    MealMapper
from src.contexts.recipes_catalog.core.adapters.ORM.sa_models.meal.meal import \
    MealSaModel
from src.contexts.recipes_catalog.core.adapters.ORM.sa_models.recipe.ingredient import \
    IngredientSaModel
from src.contexts.recipes_catalog.core.adapters.ORM.sa_models.recipe.recipe import \
    RecipeSaModel
from src.contexts.recipes_catalog.core.domain.entities.meal import Meal
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
        return model_obj # type: ignore

    async def get_sa_instance(self, id: str) -> MealSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj
    
    async def get_meal_by_recipe_id(self, recipe_id: str) -> Meal:
        """
        Get meal by recipe id.
        """
        result = await self._generic_repo.query(filter={"recipe_id": recipe_id})
        if len(result) == 0:
            raise ValueError(f"Meal with recipe id {recipe_id} not found.")
        if len(result) > 1:
            raise ValueError(f"Multiple meals with recipe id {recipe_id} found.")
        return result[0]

    from sqlalchemy import and_, or_

    def _tag_match_condition(
        self,
        outer_meal: Type[MealSaModel],
        tags: list[tuple[str, str, str]],
    ) -> ColumnElement[bool]:
        """
        Build a single AND(...) of `outer_meal.tags.any(...)` for each key-group.
        """
        # group tags by key
        tags_sorted = sorted(tags, key=lambda t: t[0])
        conditions = []
        for key, group in groupby(tags_sorted, key=lambda t: t[0]):
            group_list = list(group)
            author_id = group_list[0][2]
            values = [t[1] for t in group_list]

            # outer_meal.tags.any(...) will generate EXISTS(...) under the hood
            cond = outer_meal.tags.any(
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
        outer_meal: Type[MealSaModel],
        tags: list[tuple[str, str, str]],
    ) -> ColumnElement[bool]:
        """
        Build the negation: none of these tags exist.
        """
        # Simply negate the positive match
        return ~self._tag_match_condition(outer_meal, tags)


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
            outer_meal: Type[MealSaModel] = aliased(self.sa_model_type)
            stmt = starting_stmt.select(outer_meal) if starting_stmt is not None else select(outer_meal)

            if filter.get("tags"):
                tags = filter.pop("tags")
                stmt = stmt.where(self._tag_match_condition(outer_meal, tags))

            if filter.get("tags_not_exists"):
                tags_not = filter.pop("tags_not_exists")
                stmt = stmt.where(self._tag_not_exists_condition(outer_meal, tags_not))
            
            stmt = stmt.distinct()

            return await self._generic_repo.query(
                filter=filter,
                starting_stmt=stmt,
                already_joined={str(TagSaModel)},
                sa_model=outer_meal
            )
        return await self._generic_repo.query(filter=filter,starting_stmt=starting_stmt)
    
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

    async def persist_all(self, domain_entities: list[Meal] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
