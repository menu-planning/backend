from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.recipe.recipe import (
    RecipeMapper,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.meal.meal import (
    MealSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.month import (
    MonthSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.repositories.name_search import (
    StrProcessor,
)
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.allergen import AllergenMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.cuisine import CuisineMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.flavor import FlavorMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.texture import TextureMapper


class MealMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: Meal) -> MealSaModel:
        return MealSaModel(
            id=domain_obj.id,
            # menu_id=domain_obj.menu_id,
            name=domain_obj.name,
            preprocessed_name=StrProcessor(domain_obj.name).output,
            description=domain_obj.description,
            recipes=[RecipeMapper.map_domain_to_sa(i) for i in domain_obj.recipes],
            author_id=domain_obj.author_id,
            notes=domain_obj.notes,
            total_time=domain_obj.total_time,
            cuisines=[CuisineMapper.map_domain_to_sa(c) for c in domain_obj.cuisines],
            flavors=[FlavorMapper.map_domain_to_sa(f) for f in domain_obj.flavors],
            textures=[TextureMapper.map_domain_to_sa(t) for t in domain_obj.textures],
            allergens=[
                AllergenMapper.map_domain_to_sa(a) for a in domain_obj.allergens
            ],
            weight_in_grams=domain_obj.weight_in_grams,
            calorie_density=domain_obj.calorie_density,
            carbo_percentage=domain_obj.carbo_percentage,
            protein_percentage=domain_obj.protein_percentage,
            total_fat_percentage=domain_obj.total_fat_percentage,
            like=domain_obj.like,
            season=[MonthSaModel(id=i.value) for i in domain_obj.season],
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
            # menu_id=sa_obj.menu_id,
            description=sa_obj.description,
            recipes=[RecipeMapper.map_sa_to_domain(i) for i in sa_obj.recipes],
            author_id=sa_obj.author_id,
            notes=sa_obj.notes,
            image_url=sa_obj.image_url,
            created_at=sa_obj.created_at,
            updated_at=sa_obj.updated_at,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
        )
