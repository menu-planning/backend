import random

import pytest
from attrs import asdict
from pydantic import ValidationError
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipes.filter import (
    ApiRecipeFilter,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipes.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.value_objects.ingredient import (
    ApiIngredient,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.value_objects.rating import (
    ApiRating,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.value_objects.user import (
    ApiUser,
)
from src.contexts.recipes_catalog.shared.adapters.repositories.recipe.recipe import (
    RecipeRepo,
)
from src.contexts.recipes_catalog.shared.domain.entities import Recipe
from src.contexts.recipes_catalog.shared.domain.enums import Role as EnumRoles
from src.contexts.recipes_catalog.shared.domain.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.recipes_catalog.shared.domain.value_objects.rating import Rating
from src.contexts.seedwork.shared.adapters.repository import SaGenericRepository
from src.contexts.shared_kernel.domain.entities.diet_type import DietType
from src.contexts.shared_kernel.domain.enums import Month
from src.contexts.shared_kernel.domain.value_objects.name_tag.allergen import Allergen
from src.contexts.shared_kernel.domain.value_objects.name_tag.cuisine import Cuisine
from src.contexts.shared_kernel.domain.value_objects.name_tag.flavor import Flavor
from src.contexts.shared_kernel.domain.value_objects.name_tag.texture import Texture
from src.contexts.shared_kernel.endpoints.api_schemas.entities.diet_type import (
    ApiDietType,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.nutri_facts import (
    ApiNutriFacts,
)
from tests.recipes_catalog.random_refs import (
    admin_user,
    random_attr,
    random_create_recipe_classmethod_kwargs,
    random_create_tag_classmethod_kwargs,
    random_ingredient_kwargs,
    random_nutri_facts,
    random_rate_cmd_kwargs,
    random_tag_name,
    random_user,
)


class TestApiUser:
    def test_admin_user(self) -> None:
        user = admin_user()
        assert user.roles[0].name == EnumRoles.ADMINISTRATOR.name.lower()
        api = ApiUser(
            id=user.id,
            roles=[asdict(i) for i in user.roles],
        )
        domain = api.to_domain()
        assert domain == user
        assert ApiUser.from_domain(domain) == api


class TestApiNutriFacts:
    def test_correct_nutri_facts(self) -> None:
        nutri_facts = random_nutri_facts()
        kwargs = asdict(nutri_facts)
        api = ApiNutriFacts(**kwargs)
        domain = api.to_domain()
        assert domain == nutri_facts
        assert ApiNutriFacts.from_domain(domain) == api

    def test_canNOT_have_negative_values(self) -> None:
        nutri_facts = random_nutri_facts()
        kwargs = asdict(nutri_facts)
        kwargs["calories"]["value"] = -1
        with pytest.raises(ValidationError):
            ApiNutriFacts(**kwargs)


class TestApiRating:
    def test_correct_rating(self) -> None:
        kwargs = random_rate_cmd_kwargs()
        kwargs["recipe_id"] = "1"
        rating = Rating(**kwargs)
        api = ApiRating(**kwargs)
        domain = api.to_domain()
        assert domain == rating
        assert ApiRating.from_domain(domain) == api

    def test_rate_must_be_between_0_and_5(self) -> None:
        kwargs = random_rate_cmd_kwargs()
        kwargs["recipe_id"] = "1"
        kwargs["taste"] = 6
        with pytest.raises(ValueError):
            ApiRating(**kwargs)

    def test_convenience_must_be_between_0_and_5(self) -> None:
        kwargs = random_rate_cmd_kwargs()
        kwargs["recipe_id"] = "1"
        kwargs["convenience"] = 6
        with pytest.raises(ValueError):
            ApiRating(**kwargs)


class TestApiIngredient:
    def test_can_convert_to_domain(self) -> None:
        kwargs = random_ingredient_kwargs()
        domain = Ingredient(**kwargs)
        api = ApiIngredient(**kwargs)
        assert domain == api.to_domain()

    def test_can_convert_from_domain(self) -> None:
        kwargs = random_ingredient_kwargs()
        domain = Ingredient(**kwargs)
        api = ApiIngredient(**kwargs)
        assert api == ApiIngredient.from_domain(domain)


class TestApiRecipe:
    def test_can_convert_to_and_from_domain(self) -> None:
        domain_kwargs = random_create_recipe_classmethod_kwargs(
            diet_types_ids=set(
                [random_attr("diet_type_id"), random_attr("diet_type_id")]
            ),
            ingredient_list=[
                Ingredient(**random_ingredient_kwargs()) for _ in range(3)
            ],
            categories_ids=set(
                [random_attr("category_id"), random_attr("category_id")]
            ),
            cuisine=Cuisine(name=random_attr("cuisine")),
            flavor=Flavor(name=random_attr("flavor")),
            texture=Texture(name=random_attr("texture")),
            allergens={
                Allergen(name=random_attr("allergen")),
                Allergen(name=random_attr("allergen")),
            },
            nutri_facts=random_nutri_facts(),
            meal_planning_ids=set(
                [
                    random_attr("meal_planning_id"),
                    random_attr("meal_planning_id"),
                ]
            ),
            season=set([random.choice([i for i in Month])]),
        )
        domain = Recipe.create_recipe(**domain_kwargs)
        domain.rate(**random_rate_cmd_kwargs())
        api = ApiRecipe.from_domain(domain)
        domain_after = api.to_domain()
        assert domain.id == domain_after.id
        assert domain.name == domain_after.name
        assert len(domain.ingredients) == len(domain_after.ingredients)
        for ingredient in domain.ingredients:
            assert ingredient in domain_after.ingredients
        assert domain.instructions == domain_after.instructions
        assert domain.author_id == domain_after.author_id
        assert domain.meal_id == domain_after.meal_id
        assert domain.description == domain_after.description
        assert domain.utensils == domain_after.utensils
        assert domain.total_time == domain_after.total_time
        assert domain.servings == domain_after.servings
        assert domain.notes == domain_after.notes
        assert domain.diet_types_ids == domain_after.diet_types_ids
        assert domain.categories_ids == domain_after.categories_ids
        assert domain.cuisine == domain_after.cuisine
        assert domain.flavor == domain_after.flavor
        assert domain.texture == domain_after.texture
        assert domain.allergens == domain_after.allergens
        assert domain.meal_planning_ids == domain_after.meal_planning_ids
        assert domain.privacy == domain_after.privacy
        assert domain.ratings == domain_after.ratings
        assert domain.nutri_facts == domain_after.nutri_facts
        assert domain.weight_in_grams == domain_after.weight_in_grams
        assert domain.season == domain_after.season
        assert domain.image_url == domain_after.image_url
        assert domain.created_at == domain_after.created_at
        assert domain.updated_at == domain_after.updated_at
        assert domain.discarded == domain_after.discarded
        assert domain.version == domain_after.version


class TestApiFilter:
    def test_api_filters_match_repository_filters(self) -> None:
        mappers = RecipeRepo.filter_to_column_mappers
        generic_filters = SaGenericRepository.ALLOWED_FILTERS
        filters = []
        for mapper in mappers:
            filters.extend(list(mapper.filter_key_to_column_name.keys()))

        filters.extend(generic_filters)
        api_filters = ApiRecipeFilter.model_fields.keys()
        processed_api_filters = []
        for k in api_filters:
            processed_api_filters.append(SaGenericRepository.removePostfix(k))
        assert set(filters) == set(processed_api_filters)


class TestTag:
    def test_can_convert_to_and_from_domain(self) -> None:
        domain_kwargs = random_create_tag_classmethod_kwargs(
            name=random_tag_name(type="DietType"),
            author_id=random_user().id,
        )
        domain = DietType.create(**domain_kwargs)
        api = ApiDietType.from_domain(domain)
        assert domain == api.to_domain()
