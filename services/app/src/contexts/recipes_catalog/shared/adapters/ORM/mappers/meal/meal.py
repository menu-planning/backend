from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

import src.contexts.seedwork.shared.adapters.utils as utils
from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.recipe.recipe import \
    RecipeMapper
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.meal.meal import \
    MealSaModel
from src.contexts.recipes_catalog.shared.adapters.repositories.name_search import \
    StrProcessor
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.nutri_facts import \
    NutriFactsMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.tag.tag import TagMapper
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
            # so we should not need merge  thechildren
            merge_children = True
        recipes_tasks = (
            [
                RecipeMapper.map_domain_to_sa(session, i, merge=merge_children)
                for i in domain_obj.recipes
            ]
            if domain_obj.recipes
            else []
        )
        if recipes_tasks:
            recipes = await utils.gather_results_with_timeout(
                recipes_tasks,
                timeout=5,
                timeout_message="Timeout mapping recipes in RecipeMapper",
            )
            all_tags = {}
            for recipe in recipes:
                current_recipe_tags = {}
                for tag in recipe.tags:
                    if (tag.key, tag.value, tag.author_id, tag.type) in all_tags:
                        current_recipe_tags[
                            (tag.key, tag.value, tag.author_id, tag.type)
                        ] = all_tags[(tag.key, tag.value, tag.author_id, tag.type)]
                    else:
                        current_recipe_tags[
                            (tag.key, tag.value, tag.author_id, tag.type)
                        ] = tag
                        all_tags[(tag.key, tag.value, tag.author_id, tag.type)] = tag
                recipe.tags = list(current_recipe_tags.values())
        else:
            recipes = []

        tags_tasks = (
            [TagMapper.map_domain_to_sa(session, i) for i in domain_obj.tags]
            if domain_obj.tags
            else []
        )
        if tags_tasks:
            tags = await utils.gather_results_with_timeout(
                tags_tasks,
                timeout=5,
                timeout_message="Timeout mapping tags in TagMapper",
            )
        else:
            tags = []

        sa_meal_kwargs = {
            "id": domain_obj.id,
            "name": domain_obj.name,
            "preprocessed_name": StrProcessor(domain_obj.name).output,
            "description": domain_obj.description,
            "author_id": domain_obj.author_id,
            "menu_id": domain_obj.menu_id,
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
            "discarded": domain_obj.discarded,
            "version": domain_obj.version,
            # relationships
            "recipes": recipes,
            "tags": tags,
        }
        logger.debug(f"SA Meal kwargs: {sa_meal_kwargs}")
        # if not domain_obj.created_at:
        #     sa_meal_kwargs.pop("created_at")
        #     sa_meal_kwargs.pop("updated_at")
        sa_meal = MealSaModel(**sa_meal_kwargs)
        if meal_on_db and merge:
            return await session.merge(sa_meal)  # , meal_on_db)
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
