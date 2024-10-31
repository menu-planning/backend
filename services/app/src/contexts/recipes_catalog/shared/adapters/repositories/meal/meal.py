from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.meal.meal import (
    MealMapper,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.meal import MealSaModel
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.seedwork.shared.adapters.enums import FrontendFilterTypes
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)

from services.app.src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.recipe import (
    RecipeSaModel,
)


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
                "cuisine": "cuisine_id",
                "flavor": "flavor_id",
                "texture": "texture_id",
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
        ),
        FilterColumnMapper(
            sa_model_type=IngredientSaModel,
            filter_key_to_column_name={"products": "product_id"},
            join_target_and_on_clause=[(IngredientSaModel, MealSaModel.ingredients)],
        ),
        FilterColumnMapper(
            sa_model_type=DietTypeSaModel,
            filter_key_to_column_name={"diet_types": "name"},
            join_target_and_on_clause=[(DietTypeSaModel, MealSaModel.diet_types)],
        ),
        FilterColumnMapper(
            sa_model_type=CategorySaModel,
            filter_key_to_column_name={"categories": "name"},
            join_target_and_on_clause=[(CategorySaModel, MealSaModel.categories)],
        ),
        FilterColumnMapper(
            sa_model_type=AllergenSaModel,
            filter_key_to_column_name={"allergens": "name"},
            join_target_and_on_clause=[(AllergenSaModel, MealSaModel.allergens)],
        ),
        FilterColumnMapper(
            sa_model_type=MealPlanningSaModel,
            filter_key_to_column_name={"meal_planning": "name"},
            join_target_and_on_clause=[
                (MealPlanningSaModel, MealSaModel.meal_planning)
            ],
        ),
        FilterColumnMapper(
            sa_model_type=MonthSaModel,
            filter_key_to_column_name={"season": "id"},
            join_target_and_on_clause=[(MonthSaModel, MealSaModel.season)],
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
        if filter.get("allergens_not_exists"):
            allergens_not_exists = filter.pop("allergens_not_exists")
            subquery = (
                select(recipes_allergens_association.c.recipe_id).where(
                    recipes_allergens_association.c.recipe_id == Meal.id,
                    recipes_allergens_association.c.allergen_name.in_(
                        allergens_not_exists
                    ),
                )
            ).exists()
            if starting_stmt is None:
                starting_stmt = select(self.sa_model_type)
            starting_stmt = starting_stmt.where(~subquery)
        model_objs: list[Meal] = await self._generic_repo.query(
            filter=filter,
            starting_stmt=starting_stmt,
            already_joined={str(AllergenSaModel)},
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
