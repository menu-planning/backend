import json

from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.meal.meal import (
    ApiMeal,
)
from tests.recipes_catalog.random_refs import random_meal, random_recipe
from tests.utils import build_dict_from_instance


class TestApiMeal:
    def test_can_convert_meal_to_and_from_domain(self) -> None:
        domain = random_meal()
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

    def test_can_serialize_a_meal(self) -> None:
        domain = random_meal()
        domain.add_recipe(random_recipe(meal_id=domain.id, author_id=domain.author_id))
        api = ApiMeal.from_domain(domain)
        serialized = json.loads(api.model_dump_json())
        assert domain.id == serialized["id"]
        assert domain.name == serialized["name"]
        recipes = [build_dict_from_instance(recipe) for recipe in domain.recipes]
        for recipe in recipes:
            recipe.pop("events")
        for recipe in serialized["recipes"]:
            recipe.pop("average_convenience_rating")
            recipe.pop("average_taste_rating")
        assert recipes == serialized["recipes"]
        assert len(serialized["recipes"]) > 0
        assert [build_dict_from_instance(tag) for tag in domain.tags] == serialized[
            "tags"
        ]
        assert len(serialized["tags"]) > 0
        assert domain.description == serialized["description"]
        assert domain.notes == serialized["notes"]
        assert domain.image_url == serialized["image_url"]
        assert domain.created_at == serialized["created_at"]
        assert domain.updated_at == serialized["updated_at"]
        assert build_dict_from_instance(domain.nutri_facts) == serialized["nutri_facts"]
        assert domain.calorie_density == serialized["calorie_density"]
        assert domain.carbo_percentage == serialized["carbo_percentage"]
        assert domain.protein_percentage == serialized["protein_percentage"]
        assert domain.total_fat_percentage == serialized["total_fat_percentage"]
        assert domain.weight_in_grams == serialized["weight_in_grams"]
