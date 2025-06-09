from itertools import groupby
from typing import Any, Type

from sqlalchemy import ColumnElement, Select, and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.contexts.products_catalog.core.adapters.repositories.product_repository import ProductRepo
from src.contexts.recipes_catalog.core.adapters.meal.ORM.mappers.recipe_mapper import RecipeMapper
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.ingredient_sa_model import IngredientSaModel
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import RecipeSaModel
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.seedwork.shared.adapters.enums import FrontendFilterTypes
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag import TagSaModel
from src.logging.logger import logger


class RecipeRepo(CompositeRepository[_Recipe, RecipeSaModel]):
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
    ]

    def __init__(
        self,
        db_session: AsyncSession,
    ):
        self._session = db_session
        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=RecipeMapper,
            domain_model_type=_Recipe,
            sa_model_type=RecipeSaModel,
            filter_to_column_mappers=RecipeRepo.filter_to_column_mappers,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: _Recipe) -> None:
        raise NotImplementedError("Recipes must be added through the meal repo.")

    async def get(self, id: str) -> _Recipe:
        model_obj = await self._generic_repo.get(id)
        return model_obj # type: ignore

    async def get_sa_instance(self, id: str) -> RecipeSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj # type: ignore
    
    def _tag_match_condition(
        self,
        outer_recipe: Type[RecipeSaModel],
        tags: list[tuple[str, str, str]],
    ) -> ColumnElement[bool]:
        """
        Build a single AND(...) of `outer_recipe.tags.any(...)` for each key-group.
        """
        # group tags by key
        tags_sorted = sorted(tags, key=lambda t: t[0])
        conditions = []
        for key, group in groupby(tags_sorted, key=lambda t: t[0]):
            group_list = list(group)
            author_id = group_list[0][2]
            values = [t[1] for t in group_list]

            # outer_recipe.tags.any(...) will generate EXISTS(...) under the hood
            cond = outer_recipe.tags.any(
                and_(
                    TagSaModel.key == key,
                    TagSaModel.value.in_(values),
                    TagSaModel.author_id == author_id,
                    TagSaModel.type == "recipe",
                )
            )
            conditions.append(cond)

        # require _all_ key‐groups to match
        return and_(*conditions)


    def _tag_not_exists_condition(
        self,
        outer_recipe: Type[RecipeSaModel],
        tags: list[tuple[str, str, str]],
    ) -> ColumnElement[bool]:
        """
        Build the negation: none of these tags exist.
        """
        # Simply negate the positive match
        return ~self._tag_match_condition(outer_recipe, tags)


    async def query(
        self,
        filter: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
    ) -> list[_Recipe]:
        filter = filter or {}
        if filter.get("product_name"):
            product_name = filter.pop("product_name")
            product_repo = ProductRepo(self._session)
            products = await product_repo.list_top_similar_names(product_name, limit=3)
            product_ids = [product.id for product in products]
            filter["products"] = product_ids

        if "tags" in filter or "tags_not_exists" in filter:
            outer_recipe: Type[RecipeSaModel] = aliased(self.sa_model_type)
            stmt = starting_stmt.select(outer_recipe) if starting_stmt is not None else select(outer_recipe)

            if filter.get("tags"):
                tags = filter.pop("tags")
                stmt = stmt.where(self._tag_match_condition(outer_recipe, tags))

            if filter.get("tags_not_exists"):
                tags_not = filter.pop("tags_not_exists")
                stmt = stmt.where(self._tag_not_exists_condition(outer_recipe, tags_not))
            
            stmt = stmt.distinct()

            return await self._generic_repo.query(
                filter=filter,
                starting_stmt=stmt,
                already_joined={str(TagSaModel)},
                sa_model=outer_recipe
            )
        return await self._generic_repo.query(filter=filter,starting_stmt=starting_stmt)

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

    async def persist(self, domain_obj: _Recipe) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[_Recipe] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
