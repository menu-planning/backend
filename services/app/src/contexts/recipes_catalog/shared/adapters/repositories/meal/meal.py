from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.shared.adapters.repositories.product import (
    ProductRepo,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.meal.meal import (
    MealMapper,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.meal.associations import (
    meals_tags_association,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.meal.meal import (
    MealSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.ingredient import (
    IngredientSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.recipe import (
    RecipeSaModel,
)
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.seedwork.shared.adapters.enums import FrontendFilterTypes
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag import TagSaModel


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
                "like": "like",
                "calories": "calories",
                "protein": "protein",
                "carbohydrate": "carbohydrate",
                "total_fat": "total_fat",
                "saturated_fat": "saturated_fat",
                "trans_fat": "trans_fat",
                "sugar": "sugar",
                "sodium": "sodium",
                # "cuisine": "cuisine_id",
                # "flavor": "flavor_id",
                # "texture": "texture_id",
                "calories_density": "calorie_density",
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

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt: Select | None = None,
    ) -> list[Meal]:
        if filter.get("tags"):
            tags = filter.pop("tags")
            for t in tags:
                key, value, author_id = t
                subquery = (
                    select(MealSaModel.id)
                    .join(TagSaModel, MealSaModel.tags)
                    .where(
                        meals_tags_association.c.meal_id == MealSaModel.id,
                        TagSaModel.key == key,
                        TagSaModel.value == value,
                        TagSaModel.author_id == author_id,
                    )
                ).exists()
                if starting_stmt is None:
                    starting_stmt = select(self.sa_model_type)
                starting_stmt = starting_stmt.where(subquery)
        if filter.get("tags_not_exists"):
            tags_not_exists = filter.pop("tags_not_exists")
            for t in tags_not_exists:
                key, value, author_id = t
                subquery = (
                    select(MealSaModel.id)
                    .join(TagSaModel, MealSaModel.tags)
                    .where(
                        meals_tags_association.c.meal_id == MealSaModel.id,
                        TagSaModel.key == key,
                        TagSaModel.value == value,
                        TagSaModel.author_id == author_id,
                    )
                ).exists()
                if starting_stmt is None:
                    starting_stmt = select(self.sa_model_type)
                starting_stmt = starting_stmt.where(~subquery)
            if starting_stmt is None:
                starting_stmt = select(self.sa_model_type)
            starting_stmt = starting_stmt.where(~subquery)
        if filter.get("product_name"):
            product_name = filter.pop("product_name")
            product_repo = ProductRepo(self._session)
            products = await product_repo.list_top_similar_names(product_name, limit=3)
            product_ids = [product.id for product in products]
            filter["products"] = product_ids
        model_objs: list[Meal] = await self._generic_repo.query(
            filter=filter,
            starting_stmt=starting_stmt,
            # _return_sa_instance=True,
        )
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

    async def persist(self, domain_obj: Meal) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self) -> None:
        await self._generic_repo.persist_all()
