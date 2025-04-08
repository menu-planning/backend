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
from src.logging.logger import logger

class RecipeMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: Recipe, merge: bool = True
    ) -> RecipeSaModel:
        is_domain_obj_discarded = False
        if domain_obj.discarded:
            is_domain_obj_discarded = True
            domain_obj._discarded = False
        merge_children = False
        recipe_on_db = await utils.get_sa_entity(
            session=session, sa_model_type=RecipeSaModel, filter={"id": domain_obj.id}
        )
        if not recipe_on_db and merge:
            # if recipe on db then it will be merged
            # so we should not need merge the children
            merge_children = True
        if not is_domain_obj_discarded:
            tags_tasks = (
                [TagMapper.map_domain_to_sa(session, i) for i in domain_obj.tags]
                if domain_obj.tags
                else []
            )
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

            combined_tasks = tags_tasks + ratings_tasks + ingredients_tasks

        # If we have any tasks, gather them in one call.
            if combined_tasks:
                combined_results = await utils.gather_results_with_timeout(
                    combined_tasks,
                    timeout=5,
                    timeout_message="Timeout mapping recipes and tags in RecipeMapper",
                )
                # Split the combined results back into recipes and tags.
                tags = combined_results[: len(tags_tasks)]
                ratings = combined_results[len(tags_tasks): len(tags_tasks) + len(ratings_tasks)]
                ingredients = combined_results[len(tags_tasks) + len(ratings_tasks):]
        else:
            logger.debug(
                f"Skipping mapping domain recipe to sa: {domain_obj.id}"
            )
            tags = []
            ratings = []
            ingredients = []

        sa_recipe_kwargs = {
            "id": domain_obj.id,
            "meal_id": domain_obj.meal_id if not is_domain_obj_discarded else None,
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
            "discarded": is_domain_obj_discarded,
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

        logger.debug(
            f"Ingredients: {sa_recipe_kwargs['ingredients']}"
        )

        sa_recipe = RecipeSaModel(**sa_recipe_kwargs)
        if recipe_on_db and merge and not is_domain_obj_discarded:
            return await session.merge(sa_recipe)  # , meal_on_db)
        domain_obj._discarded = is_domain_obj_discarded
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
            filter={"recipe_id": parent.id, "position": domain_obj.position},
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
        elif ingredient_on_db:
            ingredient_on_db.name = ingredient_on_entity.name
            ingredient_on_db.preprocessed_name = ingredient_on_entity.preprocessed_name
            ingredient_on_db.quantity = ingredient_on_entity.quantity
            ingredient_on_db.unit = ingredient_on_entity.unit
            ingredient_on_db.recipe_id = ingredient_on_entity.recipe_id
            ingredient_on_db.full_text = ingredient_on_entity.full_text
            ingredient_on_db.product_id = ingredient_on_entity.product_id
            ingredient_on_db.position = ingredient_on_entity.position
            return ingredient_on_db
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
            session=session,
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
        elif rating_on_db:
            rating_on_db.user_id = rating_on_entity.user_id
            rating_on_db.recipe_id = rating_on_entity.recipe_id
            rating_on_db.taste = rating_on_entity.taste
            rating_on_db.convenience = rating_on_entity.convenience
            rating_on_db.comment = rating_on_entity.comment
            return rating_on_db
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
