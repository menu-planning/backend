import pytest


from src.contexts.recipes_catalog.core.domain.events.menu.menu_meals_changed import (
    MenuMealAddedOrRemoved,
)
from src.contexts.recipes_catalog.core.domain.value_objects.menu_meal import MenuMeal

from tests.recipes_catalog.random_refs import random_menu


class TestMenuMealsChangesEvent:
    async def test_can_identity_new_ids(self):
        menu = random_menu()
        assert not menu.meals
        assert not menu.events
        new_meals = [
            MenuMeal(
                week=1,
                weekday="Monday",
                meal_type="Lunch",
                meal_id="meal_id",
                meal_name="almoço",
            ),
            MenuMeal(
                week=1,
                weekday="Monday",
                meal_type="Dinner",
                meal_id="meal_id",
                meal_name="jantar",
            ),
        ]
        menu.meals = set(new_meals)
        assert menu.meals == set(new_meals)
        assert len(menu.events) == 1
        expected_event: MenuMealAddedOrRemoved = menu.events[0] # type: ignore
        assert expected_event.ids_of_meals_added == {"meal_id"}
        assert expected_event.ids_of_meals_removed == set()

    def test_can_identity_removed_events(self):
        menu = random_menu()
        assert not menu.meals
        assert not menu.events
        new_meals = [
            MenuMeal(
                week=1,
                weekday="Monday",
                meal_type="Lunch",
                meal_id="meal_id_1",
                meal_name="almoço",
            ),
            MenuMeal(
                week=1,
                weekday="Monday",
                meal_type="Dinner",
                meal_id="meal_id_2",
                meal_name="jantar",
            ),
        ]
        menu._meals = {
            meal for meal in new_meals
        }
        menu.meals = set([new_meals[0]])
        assert menu.meals == set(new_meals[:1])
        assert len(menu.events) == 1
        expected_event: MenuMealAddedOrRemoved = menu.events[0] # type: ignore
        assert expected_event.ids_of_meals_added == set()
        assert expected_event.ids_of_meals_removed == {"meal_id_2"}
        assert (
            MenuMealAddedOrRemoved(
                menu_id=menu.id, ids_of_meals_added=set(), ids_of_meals_removed={"meal_id_2"}
            )
            in menu.events
        )


def test_can_get_menu_meals_by_id():
    menu = random_menu()
    assert not menu.meals
    new_meals = [
        MenuMeal(
            week=1,
            weekday="Monday",
            meal_type="Lunch",
            meal_id="meal_id_1",
            meal_name="almoço",
        ),
        MenuMeal(
            week=1,
            weekday="Monday",
            meal_type="Dinner",
            meal_id="meal_id_2",
            meal_name="jantar",
        ),
    ]
    menu._meals = {
        meal for meal in new_meals
    }
    assert menu.get_meals_by_ids({"meal_id_1"}) == {new_meals[0]} # type: ignore
    assert menu.get_meals_by_ids({"meal_id_1", "meal_id_2"}) == set(new_meals) # type: ignore
    assert menu.get_meals_by_ids({"meal_id_2"}) == {new_meals[1]} # type: ignore
    assert menu.get_meals_by_ids({"meal_id_3"}) == set() # type: ignore


class TestCanFilterMeals:
    def test_return_empty_list_when_no_meals(self):
        menu = random_menu()
        assert not menu.meals
        new_meals = [
            MenuMeal(
                week=1,
                weekday="Monday",
                meal_type="Lunch",
                meal_id="meal_id_1",
                meal_name="almoço",
            ),
            MenuMeal(
                week=1,
                weekday="Monday",
                meal_type="Dinner",
                meal_id="meal_id_2",
                meal_name="jantar",
            ),
        ]
        menu._meals = {
            meal for meal in new_meals
        }
        assert (
            menu.filter_meals(
                week=1, weekday="Monday", meal_type="Café da manhã"
            )
            == []
        )
        assert (
            menu.filter_meals(week=1, weekday="Tuesday", meal_type="Lunch")
            == []
        )
        assert (
            menu.filter_meals(week=2, weekday="Monday", meal_type="Lunch")
            == []
        )

    def test_return_all_meals_new_no_filter(self):
        menu = random_menu()
        assert not menu.meals
        new_meals = [
            MenuMeal(
                week=1,
                weekday="Monday",
                meal_type="Lunch",
                meal_id="meal_id_1",
                meal_name="almoço",
            ),
            MenuMeal(
                week=1,
                weekday="Monday",
                meal_type="Dinner",
                meal_id="meal_id_2",
                meal_name="jantar",
            ),
        ]
        menu._meals = {
            meal for meal in new_meals
        }
        assert menu.filter_meals() == new_meals

    def test_match_exact_filter(self):
        menu = random_menu()
        assert not menu.meals
        new_meals = [
            MenuMeal(
                week=1,
                weekday="Monday",
                meal_type="Lunch",
                meal_id="meal_id_1",
                meal_name="almoço",
            ),
            MenuMeal(
                week=1,
                weekday="Monday",
                meal_type="Dinner",
                meal_id="meal_id_2",
                meal_name="jantar",
            ),
        ]
        menu._meals = {
            meal for meal in new_meals
        }
        assert menu.filter_meals(
            week=1, weekday="Monday", meal_type="Lunch"
        ) == [new_meals[0]]
        assert menu.filter_meals(
            week=1, weekday="Monday", meal_type="Dinner"
        ) == [new_meals[1]]

    def test_match_partial_filter(self):
        menu = random_menu()
        assert not menu.meals
        new_meals = [
            MenuMeal(
                week=1,
                weekday="Monday",
                meal_type="Lunch",
                meal_id="meal_id_1",
                meal_name="almoço",
            ),
            MenuMeal(
                week=1,
                weekday="Monday",
                meal_type="Dinner",
                meal_id="meal_id_2",
                meal_name="jantar",
            ),
        ]
        menu._meals = {
            meal for meal in new_meals
        }
        assert menu.filter_meals(week=1) == new_meals
        assert menu.filter_meals(weekday="Monday") == new_meals
        assert menu.filter_meals(meal_type="Lunch") == new_meals[:1]


class TestCanUpdateAMeal:
    def test_can_update_meal(self):
        menu = random_menu()
        assert not menu.meals
        new_meals = [
            MenuMeal(
                week=1,
                weekday="Monday",
                meal_type="Lunch",
                meal_id="meal_id_1",
                meal_name="almoço",
            ),
            MenuMeal(
                week=1,
                weekday="Monday",
                meal_type="Dinner",
                meal_id="meal_id_2",
                meal_name="jantar",
            ),
        ]
        menu._meals = {
            meal for meal in new_meals
        }
        upddated_meal = new_meals[0].replace(meal_name="almoço atualizado")
        menu.update_meal(upddated_meal)
        assert menu.get_meals_by_ids({"meal_id_1"}) == {upddated_meal} # type: ignore

    def test_can_only_update_a_meal_if_key_and_meal_id_match(self):
        menu = random_menu()
        assert not menu.meals
        new_meals = [
            MenuMeal(
                week=1,
                weekday="Monday",
                meal_type="Lunch",
                meal_id="meal_id_1",
                meal_name="almoço",
            ),
            MenuMeal(
                week=1,
                weekday="Monday",
                meal_type="Dinner",
                meal_id="meal_id_2",
                meal_name="jantar",
            ),
        ]
        menu._meals = {
            meal for meal in new_meals
        }
        upddated_meal = new_meals[0].replace(meal_id="meal_id_2")
        with pytest.raises(Exception):
            menu.update_meal(upddated_meal)
