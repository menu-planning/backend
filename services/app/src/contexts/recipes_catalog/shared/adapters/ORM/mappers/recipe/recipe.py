from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

import src.contexts.seedwork.shared.adapters.utils as utils
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.ingredient import \
    IngredientSaModel
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.rating import \
    RatingSaModel
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.recipe import \
    RecipeSaModel
from src.contexts.recipes_catalog.shared.adapters.repositories.name_search import \
    StrProcessor
from src.contexts.recipes_catalog.shared.domain.entities import Recipe
from src.contexts.recipes_catalog.shared.domain.value_objects.ingredient import \
    Ingredient
from src.contexts.recipes_catalog.shared.domain.value_objects.rating import \
    Rating
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.nutri_facts import \
    NutriFactsMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.tag.tag import TagMapper
from src.contexts.shared_kernel.domain.enums import MeasureUnit, Privacy


class RecipeMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: Recipe, merge: bool = True
    ) -> RecipeSaModel:
        merge_children = False
        recipe_on_db = await utils.get_sa_entity(
            session=session, sa_model_type=RecipeSaModel, filter={"id": domain_obj.id}
        )
        if not recipe_on_db and merge:
            # if meal on db then it will be merged
            # so we should not need merge the children
            merge_children = True
        tags_tasks = (
            [TagMapper.map_domain_to_sa(session, i) for i in domain_obj.tags]
            if domain_obj.tags
            else []
        )
        if tags_tasks:
            tags = await utils.gather_results_with_timeout(
                tags_tasks,
                timeout=5,
                timeout_message="Timeout mapping tags in RecipeMapper",
            )
        else:
            tags = []

        ratings_tasks = (
            [
                _RatingMapper.map_domain_to_sa(
                    session=session,
                    parent=domain_obj,
                    domain_obj=r,
                    merge=merge_children,
                )
                for r in domain_obj.ratings
            ]
            if domain_obj.ratings
            else []
        )
        if ratings_tasks:
            ratings = await utils.gather_results_with_timeout(
                ratings_tasks,
                timeout=5,
                timeout_message="Timeout mapping ratings in RecipeMapper",
            )
        else:
            ratings = []

        ingredients_tasks = (
            [
                _IngredientMapper.map_domain_to_sa(
                    session=session,
                    parent=domain_obj,
                    domain_obj=i,
                    merge=merge_children,
                )
                for i in domain_obj.ingredients
            ]
            if domain_obj.ingredients
            else []
        )
        if ingredients_tasks:
            ingredients = await utils.gather_results_with_timeout(
                ingredients_tasks,
                timeout=5,
                timeout_message="Timeout mapping ingredients in RecipeMapper",
            )
        else:
            ingredients = []

        sa_recipe_kwargs = {
            "id": domain_obj.id,
            "meal_id": domain_obj.meal_id,
            "name": domain_obj.name,
            "preprocessed_name": StrProcessor(domain_obj.name).output,
            "description": domain_obj.description,
            "instructions": domain_obj.instructions,
            "author_id": domain_obj.author_id,
            "utensils": domain_obj.utensils,
            "total_time": domain_obj.total_time,
            "notes": domain_obj.notes,
            "privacy": domain_obj.privacy.value,
            "nutri_facts": await NutriFactsMapper.map_domain_to_sa(
                session, domain_obj.nutri_facts
            ),
            "calorie_density": domain_obj.calorie_density,
            "carbo_percentage": (
                domain_obj.macro_division.carbohydrate
                if domain_obj.macro_division
                else None
            ),
            "protein_percentage": (
                domain_obj.macro_division.protein if domain_obj.macro_division else None
            ),
            "total_fat_percentage": (
                domain_obj.macro_division.fat if domain_obj.macro_division else None
            ),
            "weight_in_grams": domain_obj.weight_in_grams,
            "image_url": domain_obj.image_url,
            "created_at": domain_obj.created_at if domain_obj.created_at else datetime.now(),
            "updated_at": domain_obj.updated_at if domain_obj.created_at else datetime.now(),
            "discarded": domain_obj.discarded,
            "version": domain_obj.version,
            "average_taste_rating": domain_obj.average_taste_rating,
            "average_convenience_rating": domain_obj.average_convenience_rating,
            # relationships
            "ingredients": ingredients,
            "tags": tags,
            "ratings": ratings,
        }
        # if not domain_obj.created_at:
        #     sa_recipe_kwargs.pop("created_at")
        #     sa_recipe_kwargs.pop("updated_at")
        sa_recipe = RecipeSaModel(**sa_recipe_kwargs)
        if recipe_on_db and merge:
            return await session.merge(sa_recipe)  # , meal_on_db)
        return sa_recipe

    @staticmethod
    def map_sa_to_domain(sa_obj: RecipeSaModel) -> Recipe:
        return Recipe(
            id=sa_obj.id,
            meal_id=sa_obj.meal_id,
            name=sa_obj.name,
            description=sa_obj.description,
            ingredients=[
                _IngredientMapper.map_sa_to_domain(i) for i in sa_obj.ingredients
            ],
            instructions=sa_obj.instructions,
            author_id=sa_obj.author_id,
            utensils=sa_obj.utensils,
            total_time=sa_obj.total_time,
            notes=sa_obj.notes,
            tags=set([TagMapper.map_sa_to_domain(t) for t in sa_obj.tags]),
            privacy=Privacy(sa_obj.privacy),
            ratings=[_RatingMapper.map_sa_to_domain(i) for i in sa_obj.ratings],
            nutri_facts=NutriFactsMapper.map_sa_to_domain(sa_obj.nutri_facts),
            weight_in_grams=sa_obj.weight_in_grams,
            image_url=sa_obj.image_url,
            created_at=sa_obj.created_at,
            updated_at=sa_obj.updated_at,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
        )


class _IngredientMapper:
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession,
        parent: Recipe,
        domain_obj: Ingredient,
        merge: bool = True,
    ) -> IngredientSaModel:
        ingredient_on_db = await utils.get_sa_entity(
            session=session,
            sa_model_type=IngredientSaModel,
            filter={"recipe_id": parent.id, "name": domain_obj.name},
        )
        ingredient_on_entity = IngredientSaModel(
            name=domain_obj.name,
            preprocessed_name=StrProcessor(domain_obj.name).output,
            quantity=domain_obj.quantity,
            unit=domain_obj.unit.value,
            recipe_id=parent.id,
            full_text=domain_obj.full_text,
            product_id=domain_obj.product_id,
            position=domain_obj.position,
        )
        if ingredient_on_db and merge:
            return await session.merge(ingredient_on_entity)  # , ingredient_on_db)
        return ingredient_on_entity

    @staticmethod
    def map_sa_to_domain(sa_obj: IngredientSaModel) -> Ingredient:
        return Ingredient(
            name=sa_obj.name,
            quantity=sa_obj.quantity,
            unit=MeasureUnit(sa_obj.unit),
            full_text=sa_obj.full_text,
            product_id=sa_obj.product_id,
            position=sa_obj.position,
        )


class _RatingMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession,
        parent: Recipe,
        domain_obj: Rating,
        merge: bool = True,
    ) -> RatingSaModel:
        rating_on_db = utils.get_sa_entity(
            sa_model_type=RatingSaModel,
            filter={"user_id": domain_obj.user_id, "recipe_id": parent.id},
        )
        rating_on_entity = RatingSaModel(
            user_id=domain_obj.user_id,
            recipe_id=parent.id,
            taste=domain_obj.taste,
            convenience=domain_obj.convenience,
            comment=domain_obj.comment,
        )
        if rating_on_db and merge:
            return await session.merge(rating_on_entity)  # , rating_on_db)
        return rating_on_entity

    @staticmethod
    def map_sa_to_domain(sa_obj: RatingSaModel) -> Rating:
        return Rating(
            user_id=sa_obj.user_id,
            recipe_id=sa_obj.recipe_id,
            taste=sa_obj.taste,
            convenience=sa_obj.convenience,
            comment=sa_obj.comment,
        )
