from itertools import groupby
from typing import Any, Callable

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.recipe.recipe import (
    RecipeMapper,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.associations import (
    recipes_tags_association,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.ingredient import (
    IngredientSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.recipe import (
    RecipeSaModel,
)
from src.contexts.recipes_catalog.shared.domain.entities import Recipe
from src.contexts.seedwork.shared.adapters.enums import FrontendFilterTypes
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag import TagSaModel
from src.logging.logger import logger


class RecipeRepo(CompositeRepository[Recipe, RecipeSaModel]):
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=RecipeSaModel,
            filter_key_to_column_name={
                "id": "id",
                "name": "name",
                "meal_id": "meal_id",
                "author_id": "author_id",
                "total_time": "total_time",
                "weight_in_grams": "weight_in_grams",
                "privacy": "privacy",
                "created_at": "created_at",
                "average_taste_rating": "average_taste_rating",
                "average_convenience_rating": "average_convenience_rating",
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
            sa_model_type=IngredientSaModel,
            filter_key_to_column_name={"products": "product_id"},
            join_target_and_on_clause=[(IngredientSaModel, RecipeSaModel.ingredients)],
        ),
        # FilterColumnMapper(
        #     sa_model_type=TagSaModel,
        #     filter_key_to_column_name={
        #         "tag_keys": "keys",
        #         "tag_names": "name",
        #         "tag_author_ids": "author_id",
        #     },
        #     join_target_and_on_clause=[(TagSaModel, RecipeSaModel.tags)],
        # ),
    ]

    def __init__(
        self,
        db_session: AsyncSession,
    ):
        self._session = db_session
        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=RecipeMapper,
            domain_model_type=Recipe,
            sa_model_type=RecipeSaModel,
            filter_to_column_mappers=RecipeRepo.filter_to_column_mappers,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Recipe):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Recipe:
        model_obj = await self._generic_repo.get(id)
        return model_obj # type: ignore

    async def get_sa_instance(self, id: str) -> RecipeSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj # type: ignore
    
    def get_subquery_for_tags_not_exists(self, outer_recipe, tags: list[tuple[str, str, str]]) -> Select:
        conditions = []
        for t in tags:
            key, value, author_id = t
            condition = (
                select(1)
                .select_from(recipes_tags_association)
                .join(TagSaModel, recipes_tags_association.c.tag_id == TagSaModel.id)
                .where(
                    recipes_tags_association.c.recipe_id == outer_recipe.id,
                    TagSaModel.key == key,
                    TagSaModel.value == value,
                    TagSaModel.author_id == author_id,
                    TagSaModel.type == "recipe",
                )
            ).exists()
            conditions.append(condition)
        return or_(*conditions)
    
    def get_subquery_for_tags(self, outer_recipe, tags: list[tuple[str, str, str]]) -> Select:
        """
        For the given list of tag tuples (key, value, author_id),
        this builds a condition such that:
        - For tag tuples sharing the same key, at least one of the provided values must match.
        - For different keys, every key group must be matched.
        
        This is equivalent to:
        EXISTS (SELECT 1 FROM association JOIN tag 
                WHERE association.recipe_id = outer_recipe.id 
                    AND tag.key = key1 
                    AND (tag.value = value1 OR tag.value = value2 ... )
                    AND tag.author_id = <common_author> 
                    AND tag.type = "recipe")
        AND
        EXISTS (SELECT 1 FROM association JOIN tag 
                WHERE association.recipe_id = outer_recipe.id 
                    AND tag.key = key2 
                    AND (tag.value = value3 OR tag.value = value4 ... )
                    AND tag.author_id = <common_author> 
                    AND tag.type = "recipe")
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
                TagSaModel.type == "recipe"
            )

            # Create a correlated EXISTS subquery for this key group.
            subquery = (
                select(1)
                .select_from(recipes_tags_association)
                .join(TagSaModel, recipes_tags_association.c.tag_id == TagSaModel.id)
                .where(
                    recipes_tags_association.c.recipe_id == outer_recipe.id,
                    group_condition
                )
            ).exists()

            conditions.append(subquery)

        # Combine the conditions for each key group with AND.
        return and_(*conditions)

    async def query(
        self,
        filter: dict[str, Any] |None = None,
        starting_stmt: Select | None = None,
    ) -> list[Recipe]:
        filter = filter or {}
        if "tags" in filter or "tags_not_exists" in filter:
            outer_recipe = aliased(self.sa_model_type)
            starting_stmt = select(outer_recipe)
            if filter.get("tags"):
                tags = filter.pop("tags")
                subquery = self.get_subquery_for_tags(outer_recipe, tags)
                starting_stmt = starting_stmt.where(subquery)
            if filter.get("tags_not_exists"):
                tags_not_exists = filter.pop("tags_not_exists")
                subquery = self.get_subquery_for_tags_not_exists(outer_recipe, tags_not_exists)
                starting_stmt = starting_stmt.where(~subquery)
            model_objs: list[Recipe] = await self._generic_repo.query(
                filter=filter,
                starting_stmt=starting_stmt,
                already_joined={str(TagSaModel)},
                sa_model=outer_recipe
            )
            return model_objs
        model_objs: list[Recipe] = await self._generic_repo.query(filter=filter,starting_stmt=starting_stmt)
        return model_objs

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

    async def persist(self, domain_obj: Recipe) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[Recipe] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
