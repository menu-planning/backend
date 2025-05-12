from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.recipe import RecipeSaModel
from src.contexts.recipes_catalog.shared.domain.entities.recipe import _Recipe
import src.contexts.seedwork.shared.utils as utils
from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.recipe.recipe import RecipeMapper
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.meal.meal import MealSaModel
from src.contexts.recipes_catalog.shared.adapters.repositories.name_search import StrProcessor
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.nutri_facts import NutriFactsMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.tag.tag import TagMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag import TagSaModel
from src.logging.logger import logger


class MealMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: Meal, merge: bool = True
    ) -> MealSaModel:
        merge_children = False
        meal_on_db = await utils.get_sa_entity(
            session=session, sa_model_type=MealSaModel, filter={"id": domain_obj.id}
        )
        if not meal_on_db and merge:
            # if meal on db then it will be merged
            # so we should not need merge the children
            merge_children = True

        recipes_already_discarded: list[_Recipe] = []
        if meal_on_db:
            # Check if any of the recipes in the meal are already discarded
            for recipe in meal_on_db.recipes:
                if recipe.discarded:
                    recipes_already_discarded.append(recipe)
        # Prepare tasks for mapping recipes and tags
        # being_discarded_now = [i for i in domain_obj.discarded_recipes if i.id not in [j.id for j in recipes_already_discarded]]
        ids_of_recipes_on_domain_meal = [recipe.id for recipe in domain_obj.recipes]
        for recipe in meal_on_db.recipes:
            if recipe.id not in ids_of_recipes_on_domain_meal:
                recipe.discarded = True
        # being_discarded_now = [recipe for recipe in meal_on_db.recipes if recipe.id not in [recipe.id for recipe in domain_obj.recipes]] 
        # recipes_to_map = (domain_obj.recipes + being_discarded_now)
        recipes_tasks = (
            [RecipeMapper.map_domain_to_sa(session, i, merge=merge_children)
             for i in domain_obj.recipes]
            if domain_obj.recipes
            else []
        )
        tags_tasks = (
            [TagMapper.map_domain_to_sa(session, i)
             for i in domain_obj.tags]
            if domain_obj.tags
            else []
        )

        # Combine both lists of awaitables into one list
        combined_tasks = recipes_tasks + tags_tasks

        # If we have any tasks, gather them in one call.
        if combined_tasks: # and not is_domain_obj_discarded:
            combined_results = await utils.gather_results_with_timeout(
                combined_tasks,
                timeout=5,
                timeout_message="Timeout mapping recipes and tags in MealMapper",
            )
            # Split the combined results back into recipes and tags.
            recipes = combined_results[: len(recipes_tasks)]
            tags = combined_results[len(recipes_tasks):]

            # Global deduplication of tags across all recipes.
            all_tags = {}
            for recipe in recipes:
                current_recipe_tags = {}
                for tag in recipe.tags:
                    key = (tag.key, tag.value, tag.author_id, tag.type)
                    if key in all_tags:
                        current_recipe_tags[key] = all_tags[key]
                    else:
                        current_recipe_tags[key] = tag
                        all_tags[key] = tag
                recipe.tags = list(current_recipe_tags.values())
        else:
            recipes = []
            tags = []
        logger.debug(f"Recipes: {recipes}")
        logger.debug(f"NutriFacts: {domain_obj.nutri_facts}")
        sa_meal_kwargs = {
            "id": domain_obj.id,
            "name": domain_obj.name,
            "preprocessed_name": StrProcessor(domain_obj.name).output,
            "description": domain_obj.description,
            "author_id": domain_obj.author_id,
            "menu_id": domain_obj.menu_id, # if not is_domain_obj_discarded else None,
            "notes": domain_obj.notes,
            "total_time": domain_obj.total_time,
            "weight_in_grams": domain_obj.weight_in_grams,
            "calorie_density": domain_obj.calorie_density,
            "carbo_percentage": domain_obj.carbo_percentage,
            "protein_percentage": domain_obj.protein_percentage,
            "total_fat_percentage": domain_obj.total_fat_percentage,
            "nutri_facts": await NutriFactsMapper.map_domain_to_sa(
                session, domain_obj.nutri_facts
            ),
            "like": domain_obj.like,
            "image_url": domain_obj.image_url,
            "created_at": domain_obj.created_at if domain_obj.created_at else datetime.now(),
            "updated_at": domain_obj.updated_at if domain_obj.created_at else datetime.now(),
            "discarded": domain_obj.discarded, # is_domain_obj_discarded,
            "version": domain_obj.version,
            # relationships
            "recipes": recipes,
            "tags": tags,
        }
        # domain_obj._discarded = is_domain_obj_discarded
        logger.debug(f"SA Meal kwargs: {sa_meal_kwargs}")
        sa_meal = MealSaModel(**sa_meal_kwargs)
        if meal_on_db and merge:
            return await session.merge(sa_meal)
        return sa_meal

    @staticmethod
    def map_sa_to_domain(sa_obj: MealSaModel) -> Meal:
        return Meal(
            id=sa_obj.id,
            name=sa_obj.name,
            description=sa_obj.description,
            recipes=[RecipeMapper.map_sa_to_domain(i) for i in sa_obj.recipes],
            tags=set([TagMapper.map_sa_to_domain(i) for i in sa_obj.tags]),
            author_id=sa_obj.author_id,
            menu_id=sa_obj.menu_id,
            notes=sa_obj.notes,
            image_url=sa_obj.image_url,
            created_at=sa_obj.created_at,
            updated_at=sa_obj.updated_at,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
        )
