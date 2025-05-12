import json

from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.meal.meal import (
    ApiMeal,
)
from tests.recipes_catalog.random_refs import random_create_recipe_classmethod_kwargs, random_meal, random_recipe
from tests.utils import build_dict_from_instance


class TestApiMeal:
    def test_can_convert_meal_to_and_from_domain(self) -> None:
        domain = random_meal()
        domain.create_recipe(**random_create_recipe_classmethod_kwargs(meal_id=domain.id, author_id=domain.author_id))
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
        domain.create_recipe(**random_create_recipe_classmethod_kwargs(meal_id=domain.id, author_id=domain.author_id))
        api = ApiMeal.from_domain(domain)
        serialized = json.loads(api.model_dump_json())
        domain_dict = build_dict_from_instance(domain)
        assert domain_dict.pop("id") == serialized.pop("id")
        assert domain_dict.pop("name") == serialized.pop("name")
        recipes = domain_dict.pop("recipes")
        for recipe in recipes:
            recipe.pop("events")
        for recipe in serialized["recipes"]:
            recipe.pop("average_convenience_rating")
            recipe.pop("average_taste_rating")
        assert len(serialized["recipes"]) > 0
        assert recipes == serialized.pop("recipes")
        assert domain_dict.pop("tags") == serialized.pop("tags")
        assert domain_dict.pop("description") == serialized.pop("description")
        assert domain_dict.pop("notes") == serialized.pop("notes")
        assert domain_dict.pop("image_url") == serialized.pop("image_url")
        assert domain_dict.pop("created_at") == serialized.pop("created_at")
        assert domain_dict.pop("updated_at") == serialized.pop("updated_at")
        assert build_dict_from_instance(domain.nutri_facts) == serialized.pop(
            "nutri_facts"
        )
        assert domain.calorie_density == serialized.pop("calorie_density")
        assert domain.carbo_percentage == serialized.pop("carbo_percentage")
        assert domain.protein_percentage == serialized.pop("protein_percentage")
        assert domain.total_fat_percentage == serialized.pop("total_fat_percentage")
        assert domain.weight_in_grams == serialized.pop("weight_in_grams")
        recipes_tags = [build_dict_from_instance(tag) for tag in domain.recipes_tags]
        for tag in serialized.pop("recipes_tags"):
            assert tag in recipes_tags
        assert domain_dict.pop("author_id") == serialized.pop("author_id")
        assert domain_dict.pop("discarded") == serialized.pop("discarded")
        assert domain.total_time == serialized.pop("total_time")
        assert domain_dict.pop("menu_id") == serialized.pop("menu_id")
        assert domain_dict.pop("version") == serialized.pop("version")
        assert domain_dict.pop("like") == serialized.pop("like")
        assert domain_dict.pop("events") == []
        assert len(serialized) == len(domain_dict) == 0
