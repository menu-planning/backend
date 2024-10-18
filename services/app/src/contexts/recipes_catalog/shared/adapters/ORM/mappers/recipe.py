from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.ingredient import (
    IngredientSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.month import (
    MonthSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.rating import (
    RatingSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe import (
    RecipeSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.repositories.name_search import (
    StrProcessor,
)
from src.contexts.recipes_catalog.shared.domain.entities import Recipe
from src.contexts.recipes_catalog.shared.domain.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.recipes_catalog.shared.domain.value_objects.rating import Rating
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.ORM.mappers.nutri_facts import NutriFactsMapper
from src.contexts.shared_kernel.domain.enums import MeasureUnit, Month, Privacy
from src.contexts.shared_kernel.domain.value_objects.name_tag.cuisine import Cuisine
from src.contexts.shared_kernel.domain.value_objects.name_tag.flavor import Flavor
from src.contexts.shared_kernel.domain.value_objects.name_tag.texture import Texture


class RecipeMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: Recipe) -> RecipeSaModel:
        return RecipeSaModel(
            id=domain_obj.id,
            name=domain_obj.name,
            preprocessed_name=StrProcessor(domain_obj.name).output,
            description=domain_obj.description,
            ingredients=[
                _IngredientMapper.map_domain_to_sa(domain_obj, i)
                for i in domain_obj.ingredients
            ],
            instructions=domain_obj.instructions,
            author_id=domain_obj.author_id,
            utensils=domain_obj.utensils,
            total_time=domain_obj.total_time,
            servings=domain_obj.servings,
            notes=domain_obj.notes,
            cuisine_id=domain_obj.cuisine.name if domain_obj.cuisine else None,
            flavor_id=domain_obj.flavor.name if domain_obj.flavor else None,
            texture_id=domain_obj.texture.name if domain_obj.texture else None,
            privacy=domain_obj.privacy.value,
            ratings=[
                _RatingMapper.map_domain_to_sa(domain_obj, i)
                for i in domain_obj.ratings
            ],
            nutri_facts=NutriFactsMapper.map_domain_to_sa(domain_obj.nutri_facts),
            calorie_density=domain_obj.calorie_density,
            carbo_percentage=(
                domain_obj.macro_division.carbohydrate
                if domain_obj.macro_division
                else None
            ),
            protein_percentage=(
                domain_obj.macro_division.protein if domain_obj.macro_division else None
            ),
            total_fat_percentage=(
                domain_obj.macro_division.fat if domain_obj.macro_division else None
            ),
            weight_in_grams=domain_obj.weight_in_grams,
            season=[MonthSaModel(id=i.value) for i in domain_obj.season],
            image_url=domain_obj.image_url,
            created_at=domain_obj.created_at,
            updated_at=domain_obj.updated_at,
            discarded=domain_obj.discarded,
            version=domain_obj.version,
            average_taste_rating=domain_obj.average_taste_rating,
            average_convenience_rating=domain_obj.average_convenience_rating,
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: RecipeSaModel) -> Recipe:
        return Recipe(
            id=sa_obj.id,
            name=sa_obj.name,
            description=sa_obj.description,
            ingredients=[
                _IngredientMapper.map_sa_to_domain(i) for i in sa_obj.ingredients
            ],
            instructions=sa_obj.instructions,
            author_id=sa_obj.author_id,
            utensils=sa_obj.utensils,
            total_time=sa_obj.total_time,
            servings=sa_obj.servings,
            notes=sa_obj.notes,
            diet_types_ids=set([i.id for i in sa_obj.diet_types]),
            categories_ids=set([i.id for i in sa_obj.categories]),
            cuisine=Cuisine(name=sa_obj.cuisine_id) if sa_obj.cuisine_id else None,
            flavor=Flavor(name=sa_obj.flavor_id) if sa_obj.flavor_id else None,
            texture=Texture(name=sa_obj.texture_id) if sa_obj.texture_id else None,
            allergens=set([i.id for i in sa_obj.allergens]),
            meal_planning_ids=set([i.id for i in sa_obj.meal_planning]),
            privacy=Privacy(sa_obj.privacy),
            ratings=[_RatingMapper.map_sa_to_domain(i) for i in sa_obj.ratings],
            nutri_facts=NutriFactsMapper.map_sa_to_domain(sa_obj.nutri_facts),
            weight_in_grams=sa_obj.weight_in_grams,
            season=set([Month(i.id) for i in sa_obj.season]),
            image_url=sa_obj.image_url,
            created_at=sa_obj.created_at,
            updated_at=sa_obj.updated_at,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
        )


class _IngredientMapper:
    @staticmethod
    def map_domain_to_sa(entity: Recipe, domain_obj: Ingredient) -> IngredientSaModel:
        return IngredientSaModel(
            name=domain_obj.name,
            preprocessed_name=StrProcessor(domain_obj.name).output,
            quantity=domain_obj.quantity,
            unit=domain_obj.unit.value,
            recipe_id=entity.id,
            full_text=domain_obj.full_text,
            product_id=domain_obj.product_id,
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: IngredientSaModel) -> Ingredient:
        return Ingredient(
            name=sa_obj.name,
            quantity=sa_obj.quantity,
            unit=MeasureUnit(sa_obj.unit),
            full_text=sa_obj.full_text,
            product_id=sa_obj.product_id,
        )


class _RatingMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(entity: Recipe, domain_obj: Rating) -> RatingSaModel:
        return RatingSaModel(
            user_id=domain_obj.user_id,
            recipe_id=entity.id,
            taste=domain_obj.taste,
            convenience=domain_obj.convenience,
            comment=domain_obj.comment,
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: RatingSaModel) -> Rating:
        return Rating(
            user_id=sa_obj.user_id,
            recipe_id=sa_obj.recipe_id,
            taste=sa_obj.taste,
            convenience=sa_obj.convenience,
            comment=sa_obj.comment,
        )
