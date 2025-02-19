from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.meals.meal import (
    ApiMeal,
)
from tests.recipes_catalog.random_refs import random_meal, random_recipe


class TestApiMeal:
    def test_can_convert_meal_to_and_from_domain(self) -> None:
        domain = random_meal()
        # new_recipe_cmd = random_create_recipe_on_meal_kwargs()
        domain.add_recipe(random_recipe(meal_id=domain.id, author_id=domain.author_id))
        api = ApiMeal.from_domain(domain)
        back_to_domain = api.to_domain()
        assert domain.id == back_to_domain.id
        assert domain.name == back_to_domain.name
        assert domain.tags == back_to_domain.tags
        assert domain.description == back_to_domain.description
        assert domain.notes == back_to_domain.notes
        assert domain.image_url == back_to_domain.image_url
        assert domain.created_at == back_to_domain.created_at
        assert domain.updated_at == back_to_domain.updated_at
        assert domain.nutri_facts == back_to_domain.nutri_facts
        assert domain.calorie_density == back_to_domain.calorie_density
        assert domain.carbo_percentage == back_to_domain.carbo_percentage
        assert domain.protein_percentage == back_to_domain.protein_percentage
        assert domain.total_fat_percentage == back_to_domain.total_fat_percentage
