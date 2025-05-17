from attrs import asdict

from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.client.create_menu import ApiCreateMenu
from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.client.delete_menu import ApiDeleteMenu
from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.client.update_menu import ApiAttributesToUpdateOnMenu, ApiUpdateMenu
from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.menu.menu import \
    ApiMenu

from src.contexts.recipes_catalog.core.domain.commands.client.create_menu import CreateMenu
from src.contexts.recipes_catalog.core.domain.commands.client.delete_menu import DeleteMenu
from src.contexts.recipes_catalog.core.domain.commands.client.update_menu import UpdateMenu
from src.contexts.recipes_catalog.core.domain.value_objects.menu_meal import \
    MenuMeal

from tests.recipes_catalog.random_refs import (random_create_menu_cmd_kwargs,
                                               random_menu)


class TestApiCreateMenu:
    def test_api_and_domain_have_same_attributes(self) -> None:
        assert set(ApiCreateMenu.model_fields.keys()) == set(
            CreateMenu.__annotations__.keys()
        )

    def test_create_menu_cmd(self) -> None:
        kwargs = random_create_menu_cmd_kwargs()
        domain = CreateMenu(**kwargs)
        kwargs["tags"] = [asdict(t) for t in kwargs["tags"]]
        api = ApiCreateMenu(**kwargs)
        assert domain == api.to_domain()


class TestUpdateMenu:
    def test_api_and_domain_have_same_attributes(self) -> None:
        assert set(ApiUpdateMenu.model_fields.keys()) == set(
            UpdateMenu.__annotations__.keys()
        )

    def test_update_menu_from_menu(self):
        menu = random_menu()
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
        api_menu = ApiMenu.from_domain(menu)
        update_menu_cmd = ApiUpdateMenu.from_api_menu(api_menu).to_domain()
        assert update_menu_cmd.menu_id == menu.id
        for key in ApiAttributesToUpdateOnMenu.model_fields.keys():
            if key == "meals":
                for meal in update_menu_cmd.updates["meals"]:
                    assert meal in getattr(menu, key).values()
            else:
                assert update_menu_cmd.updates.get(key) == getattr(menu, key)


class TestDeleteMenu:
    def test_api_and_domain_have_same_attributes(self) -> None:
        assert set(ApiDeleteMenu.model_fields.keys()) == set(
            DeleteMenu.__annotations__.keys()
        )
