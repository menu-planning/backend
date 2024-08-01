from attrs import asdict
from sqlalchemy import inspect
from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.recipe import RecipeMapper
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
    NutriFactsSaModel,
    RecipeSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.tags import (
    CategorySaModel,
    MealPlanningSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.repositories.name_search import (
    StrProcessor,
)
from src.contexts.recipes_catalog.shared.domain.entities import Recipe
from src.contexts.shared_kernel.adapters.ORM.mappers.diet_type import DietTypeMapper
from src.contexts.shared_kernel.adapters.ORM.sa_models.diet_type import DietTypeSaModel
from src.contexts.shared_kernel.domain.entities.diet_type import DietType
from tests.recipes_catalog.random_refs import (
    random_create_recipe_classmethod_kwargs,
    random_create_tag_classmethod_kwargs,
    random_recipe,
    random_tag_name,
)


class TestRecipeMapper:
    def test_map_Recipe_to_RecipeSaModel_back_to_Recipe(self):
        mapper = RecipeMapper()
        domain = random_recipe()
        sa_model = mapper.map_domain_to_sa(domain)
        domain2 = mapper.map_sa_to_domain(sa_model)
        assert domain2.id == domain.id
        assert domain2.author_id == domain.author_id
        assert domain2.author_id == domain.author_id
        assert domain2.name == domain.name
        assert domain2.description == domain.description
        assert domain2.ingredients == domain.ingredients
        assert domain2.instructions == domain.instructions
        assert domain2.total_time == domain.total_time
        assert domain2.servings == domain.servings
        assert domain2.notes == domain.notes
        assert domain2.cuisine == domain.cuisine
        assert domain2.flavor == domain.flavor
        assert domain2.texture == domain.texture
        assert domain2.privacy == domain.privacy.value
        assert domain2.ratings == domain.ratings
        assert domain2.nutri_facts == domain.nutri_facts
        assert domain2.season == domain.season
        assert domain2.image_url == domain.image_url
        assert domain2.created_at == domain.created_at
        assert domain2.discarded == domain.discarded
        assert domain2.version == domain.version
        assert domain2.average_taste_rating == domain.average_taste_rating
        assert domain2.average_convenience_rating == domain.average_convenience_rating
        assert len(domain2.diet_types_ids) == 0
        assert len(domain.diet_types_ids) > 0

    def test_Recipe_IDs_references_doesNOT_map_to_sa_relationships(self):
        mapper = RecipeMapper()
        domain = random_recipe()
        sa_model = mapper.map_domain_to_sa(domain)
        assert len(domain.diet_types_ids) > 0
        assert len(domain.categories_ids) > 0
        assert len(domain.meal_planning_ids) > 0
        assert domain.cuisine is not None
        assert domain.flavor is not None
        assert domain.texture is not None
        assert len(sa_model.diet_types) == 0
        assert len(sa_model.categories) == 0
        assert len(sa_model.meal_planning) == 0
        assert sa_model.cuisine_id == domain.cuisine.name
        assert sa_model.flavor_id == domain.flavor.name
        assert sa_model.texture_id == domain.texture.name

    def test_map_RecipeSaModel_to_Recipe(self):
        mapper = RecipeMapper()
        recipe_kwargs = random_create_recipe_classmethod_kwargs()
        domain = Recipe.create_recipe(**recipe_kwargs)
        sa_model_kwargs = {
            "id": domain.id,
            "preprocessed_name": StrProcessor(domain.name).output,
            "discarded": domain.discarded,
            "version": domain.version,
            "author_id": domain.author_id,
            "ingredients": [
                IngredientSaModel(
                    name=i.name,
                    preprocessed_name=StrProcessor(i.name).output,
                    quantity=i.quantity,
                    unit=i.unit,
                    recipe_id=domain.id,
                    full_text=i.full_text,
                    product_id=i.product_id,
                )
                for i in domain.ingredients
            ],
            "instructions": domain.instructions,
            "diet_types": [
                DietTypeSaModel(
                    id=i,
                    name="name",
                    author_id="author_id",
                )
                for i in recipe_kwargs.pop("diet_types_ids", [])
            ],
            "categories": [
                CategorySaModel(
                    id=i,
                    name="name",
                    author_id="author_id",
                    type="category",
                )
                for i in recipe_kwargs.pop("categories_ids", [])
            ],
            "meal_planning": [
                MealPlanningSaModel(
                    id=i,
                    name="name",
                    author_id="author_id",
                    type="category",
                )
                for i in recipe_kwargs.pop("meal_planning_ids", [])
            ],
            "ratings": [
                RatingSaModel(
                    user_id=i.user_id,
                    recipe_id=domain.id,
                    taste=i.taste,
                    convenience=i.convenience,
                    comment=i.comment,
                )
                for i in domain.ratings
            ],
            "nutri_facts": NutriFactsSaModel(**asdict(domain.nutri_facts)),
            "season": [MonthSaModel(id=i.value) for i in domain.season],
        }
        sa_model_kwargs = recipe_kwargs | sa_model_kwargs
        # sa_model_kwargs.pop("author")
        sa_model_kwargs["cuisine_id"] = (
            sa_model_kwargs.pop("cuisine").name
            if sa_model_kwargs.get("cuisine")
            else None
        )
        sa_model_kwargs["flavor_id"] = (
            sa_model_kwargs.pop("flavor").name
            if sa_model_kwargs.get("flavor")
            else None
        )
        sa_model_kwargs["texture_id"] = (
            sa_model_kwargs.pop("texture").name
            if sa_model_kwargs.get("texture")
            else None
        )
        sa_model = RecipeSaModel(**sa_model_kwargs)
        domain2 = mapper.map_sa_to_domain(sa_model)
        assert len(domain.diet_types_ids) > 0
        assert len(domain.categories_ids) > 0
        assert len(domain.meal_planning_ids) > 0
        assert domain.cuisine is not None
        assert domain.flavor is not None
        assert domain.texture is not None
        assert domain.id == domain2.id
        assert domain.author_id == domain2.author_id
        assert domain.name == domain2.name
        assert domain.description == domain2.description
        assert domain.ingredients == domain2.ingredients
        assert domain.instructions == domain2.instructions
        assert domain.total_time == domain2.total_time
        assert domain.servings == domain2.servings
        assert domain.notes == domain2.notes
        assert (
            domain.diet_types_ids
            == domain2.diet_types_ids
            == set([i.id for i in sa_model.diet_types])
        )
        assert (
            domain.categories_ids
            == domain2.categories_ids
            == set([i.id for i in sa_model.categories])
        )
        assert (
            domain.meal_planning_ids
            == domain2.meal_planning_ids
            == set([i.id for i in sa_model.meal_planning])
        )
        assert domain.cuisine == domain2.cuisine
        assert domain.flavor == domain2.flavor
        assert domain.texture == domain2.texture
        assert domain.privacy == domain2.privacy
        assert domain.ratings == domain2.ratings
        assert domain.nutri_facts == domain2.nutri_facts
        assert domain.season == domain2.season
        assert domain.image_url == domain2.image_url
        assert domain.created_at == domain2.created_at
        assert domain.discarded == domain2.discarded
        assert domain.version == domain2.version
        assert domain.average_taste_rating == domain2.average_taste_rating
        assert domain.average_convenience_rating == domain2.average_convenience_rating


class TestTagMapper:
    def test_map_DietType_to_DietTypeSaModel_back_to_DietType(self):
        mapper = DietTypeMapper()
        kwargs = random_create_tag_classmethod_kwargs(
            name=random_tag_name(type="DietType")
        )
        domain = DietType.create(**kwargs)
        sa_model = mapper.map_domain_to_sa(domain)
        domain2 = mapper.map_sa_to_domain(sa_model)
        assert domain2.id == domain.id
        assert domain2.name == domain.name
        assert domain2.author_id == domain.author_id
        assert domain2.description == domain.description
        assert domain2.privacy == domain.privacy
        assert domain2.created_at == domain.created_at
        assert domain2.discarded == domain.discarded
        assert domain2.version == domain.version


async def test_if_sa_model_relationship_name_match_domain_model_attribute_name():
    inspector = inspect(RecipeSaModel)
    for attribute in inspector.relationships.keys():
        assert (
            attribute in dir(Recipe)
            or attribute + "_id" in dir(Recipe)
            or attribute + "_ids" in dir(Recipe)
        )
