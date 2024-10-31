from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.recipe.recipe import (
    RecipeMapper,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.recipe.tags.category import (
    CategoryMapper,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.meal.meal import (
    MealSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.repositories.name_search import (
    StrProcessor,
)
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.recipes_catalog.shared.domain.entities.menu import Menu
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.nutri_facts import NutriFactsMapper


class MenuMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: Meal) -> MealSaModel:
        return MealSaModel(
            id=domain_obj.id,
            menu_id=domain_obj.menu.id if domain_obj.menu else None,
            menu=(
                MenuMapper.map_domain_to_sa(domain_obj.menu)
                if domain_obj.menu
                else None
            ),
            name=domain_obj.name,
            preprocessed_name=StrProcessor(domain_obj.name).output,
            description=domain_obj.description,
            recipes=[RecipeMapper.map_domain_to_sa(i) for i in domain_obj.recipes],
            author_id=domain_obj.author_id,
            day=domain_obj.day,
            hour=domain_obj.hour,
            notes=domain_obj.notes,
            category_id=domain_obj.category.id if domain_obj.category else None,
            category=(
                CategoryMapper.map_domain_to_sa(domain_obj.category)
                if domain_obj.category
                else None
            ),
            target_nutri_facts=NutriFactsMapper.map_domain_to_sa(
                domain_obj.nutri_facts
            ),
            like=domain_obj.like,
            image_url=domain_obj.image_url,
            created_at=domain_obj.created_at,
            updated_at=domain_obj.updated_at,
            discarded=domain_obj.discarded,
            version=domain_obj.version,
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: MealSaModel) -> Meal:
        return Meal(
            id=sa_obj.id,
            name=sa_obj.name,
            menu=MenuMapper.map_sa_to_domain(sa_obj.menu) if sa_obj.menu else None,
            description=sa_obj.description,
            recipes=[RecipeMapper.map_sa_to_domain(i) for i in sa_obj.recipes],
            author_id=sa_obj.author_id,
            day=sa_obj.day,
            hour=sa_obj.hour,
            notes=sa_obj.notes,
            category=(
                CategoryMapper.map_sa_to_domain(sa_obj.category)
                if sa_obj.category
                else None
            ),
            target_nutri_facts=NutriFactsMapper.map_sa_to_domain(
                sa_obj.tagert_nutri_facts
            ),
            like=sa_obj.like,
            image_url=sa_obj.image_url,
            created_at=sa_obj.created_at,
            updated_at=sa_obj.updated_at,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
        )
