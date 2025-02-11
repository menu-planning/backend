from attrs import asdict
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.meals.meal import (
    ApiMeal,
)
from tests.recipes_catalog.random_refs import (
    random_create_recipe_on_meal_kwargs,
    random_meal,
)


class TestApiMeal:
    def test_can_convert_meal_to_and_from_domain(self) -> None:
        domain = random_meal()
        new_recipe_cmd = random_create_recipe_on_meal_kwargs()
        domain.add_recipe(**new_recipe_cmd)
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

    # def test_to_view_model(self) -> None:
    #     domain = random_meal()
    #     api = ApiMeal.from_domain(domain)
    #     view = api.to_view_model()
    #     assert view["id"] == domain.id
    #     assert view["name"] == domain.name
    #     # assert view["menu_id"] == domain.menu_id
    #     assert view["description"] == domain.description
    #     assert view["notes"] == domain.notes
    #     assert view["image_url"] == domain.image_url
    #     assert view["created_at"] == domain.created_at
    #     assert view["updated_at"] == domain.updated_at
    #     assert view["nutri_facts"]["calories"] == asdict(domain.nutri_facts.calories)
    #     assert view["nutri_facts"]["protein"] == asdict(domain.nutri_facts.protein)
    #     assert view["nutri_facts"]["carbohydrate"] == asdict(
    #         domain.nutri_facts.carbohydrate
    #     )
    #     assert view["nutri_facts"]["total_fat"] == asdict(domain.nutri_facts.total_fat)
    #     assert view["nutri_facts"]["saturated_fat"] == asdict(
    #         domain.nutri_facts.saturated_fat
    #     )
    #     assert view["nutri_facts"]["trans_fat"] == asdict(domain.nutri_facts.trans_fat)
    #     assert view["nutri_facts"]["sugar"] == asdict(domain.nutri_facts.sugar)
    #     assert view["nutri_facts"]["sodium"] == asdict(domain.nutri_facts.sodium)
    #     assert view["diet_types_ids"] == domain.diet_types_ids
    #     assert view["meal_planning_ids"] == domain.meal_planning_ids
    #     assert view["cuisine"] == domain.cuisines
    #     assert view["flavor"] == domain.flavors
    #     assert view["texture"] == domain.textures
    #     assert view["allergens"] == domain.allergens
    #     assert view["calorie_density"] == domain.calorie_density
    #     assert view["carbo_percentage"] == domain.carbo_percentage
    #     assert view["protein_percentage"] == domain.protein_percentage
    #     assert view["total_fat_percentage"] == domain.total_fat_percentage


# class TestApiFilter:
#     def test_api_filters_match_repository_filters(self) -> None:
#         mappers = MealRepo.filter_to_column_mappers
#         generic_filters = SaGenericRepository.ALLOWED_FILTERS
#         filters = []
#         for mapper in mappers:
#             filters.extend(list(mapper.filter_key_to_column_name.keys()))

#         filters.extend(generic_filters)
#         api_filters = ApiMealFilter.model_fields.keys()
#         processed_api_filters = []
#         for k in api_filters:
#             processed_api_filters.append(SaGenericRepository.removePostfix(k))
#         assert set(filters) == set(processed_api_filters)
