import json
from datetime import time

from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.menu.menu import \
    ApiMenu
from src.contexts.recipes_catalog.shared.domain.enums import MealType
from src.contexts.recipes_catalog.shared.domain.value_objects.menu_meal import \
    MenuMeal
from src.contexts.shared_kernel.domain.enums import Weekday
from tests.recipes_catalog.random_refs import (random_attr, random_menu,
                                               random_nutri_facts)
from tests.utils import build_dict_from_instance


class TestApiMenu:
    def test_can_convert_to_and_from_domain(self) -> None:
        domain = random_menu()
        domain.meals = [
            MenuMeal(
                meal_id=random_attr("meal_id"),
                meal_name=random_attr("meal_name"),
                nutri_facts=random_nutri_facts(),
                week=1,
                weekday=Weekday.MONDAY,
                meal_type=MealType.BREAKFAST,
                hour=time(8),
            )
        ]
        api = ApiMenu.from_domain(domain)
        back_to_domain = api.to_domain()
        assert domain.id == back_to_domain.id
        assert domain.author_id == back_to_domain.author_id
        assert domain.client_id == back_to_domain.client_id
        assert domain.tags == back_to_domain.tags
        assert domain.meals == back_to_domain.meals
        assert domain.description == back_to_domain.description
        assert domain.created_at == back_to_domain.created_at
        assert domain.updated_at == back_to_domain.updated_at
        assert domain.discarded == back_to_domain.discarded
        assert domain.version == back_to_domain.version

    def test_can_serialize_a_menu(self) -> None:
        domain = random_menu()
        domain.meals = [
            MenuMeal(
                meal_id=random_attr("meal_id"),
                meal_name=random_attr("meal_name"),
                nutri_facts=random_nutri_facts(),
                week=1,
                weekday=Weekday.MONDAY,
                meal_type=MealType.BREAKFAST,
                hour=time(8),
            )
        ]
        api = ApiMenu.from_domain(domain)
        domain_dict = build_dict_from_instance(domain)
        serialized = json.loads(api.model_dump_json())
        assert domain_dict.pop("id") == serialized.pop("id")
        assert domain_dict.pop("author_id") == serialized.pop("author_id")
        assert domain_dict.pop("client_id") == serialized.pop("client_id")
        assert domain_dict.pop("tags") == serialized.pop("tags")
        print(serialized)
        for k, meal in domain_dict.pop("meals").items():
            assert {
                "meal_id": meal.meal_id,
                "meal_name": meal.meal_name,
                "nutri_facts": build_dict_from_instance(meal.nutri_facts),
                "week": meal.week,
                "weekday": meal.weekday.value,
                "meal_type": meal.meal_type.value,
                "hour": str(meal.hour),
            } == serialized["meals"][
                ",".join(
                    map(
                        str,
                        (
                            k[0],
                            k[1].value,
                            k[2].value,
                        ),
                    )
                )
            ]
        serialized.pop("meals")
        assert domain_dict.pop("description") == serialized.pop("description")
        assert domain_dict.pop("created_at") == serialized.pop("created_at")
        assert domain_dict.pop("updated_at") == serialized.pop("updated_at")
        assert domain_dict.pop("discarded") == serialized.pop("discarded")
        assert domain_dict.pop("version") == serialized.pop("version")
        domain_dict.pop("events")
        assert len(serialized) == len(domain_dict) == 0
