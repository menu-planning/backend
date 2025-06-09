from attrs import asdict

from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.meal.copy_meal import (
    ApiCopyMeal,
)
from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.meal.create_meal import (
    ApiCreateMeal,
)
from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.meal.delete_meal import (
    ApiDeleteMeal,
)
from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.meal.update import (
    ApiAttributesToUpdateOnMeal,
    ApiUpdateMeal,
)
from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.recipe.update_recipe import ApiAttributesToUpdateOnRecipe
from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.meal.meal import (
    ApiMeal,
)
from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.recipe.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.core.domain.commands.commands.copy_meal import CopyMeal
from src.contexts.recipes_catalog.core.domain.commands.commands.create_meal import (
    CreateMeal,
)
from src.contexts.recipes_catalog.core.domain.commands.commands.delete_meal import (
    DeleteMeal,
)
from src.contexts.recipes_catalog.core.domain.commands.commands.update_meal import (
    UpdateMeal,
)
from tests.recipes_catalog.random_refs import random_create_meal_cmd_kwargs, random_meal


class TestApiCreateMeal:
    def test_api_and_domain_have_same_attributes(self) -> None:
        assert set(ApiCreateMeal.model_fields.keys()) == set(
            CreateMeal.__annotations__.keys()
        )

    def test_create_meal_cmd(self) -> None:
        kwargs = random_create_meal_cmd_kwargs()
        domain = CreateMeal(**kwargs)
        kwargs["recipes"] = [
            ApiRecipe.from_domain(i).model_dump() for i in kwargs["recipes"]
        ]
        kwargs["tags"] = [asdict(t) for t in kwargs["tags"]]
        api = ApiCreateMeal(**kwargs)
        assert domain == api.to_domain()


class TestApiUpdateMeal:
    def test_api_and_domain_have_same_attributes(self) -> None:
        assert set(ApiUpdateMeal.model_fields.keys()) == set(
            UpdateMeal.__annotations__.keys()
        )

    def test_to_domain_method_converts_recipes_to_recipes_updates(self):
        meal = random_meal()
        api_meal = ApiMeal.from_domain(meal)
        update_meal_cmd = ApiUpdateMeal.from_api_meal(api_meal).to_domain()
        assert update_meal_cmd.meal_id == meal.id
        for meal_attr_name in ApiAttributesToUpdateOnMeal.model_fields.keys():
            if meal_attr_name == "recipes":
                for recipe_id,recipe_updates in update_meal_cmd.updates.get(meal_attr_name).items(): # type: ignore
                    recipe_on_meal = meal.get_recipe_by_id(recipe_id)
                    assert recipe_on_meal is not None
                    for recipe_attr_name, value in recipe_updates.items():
                        assert value == getattr(recipe_on_meal, recipe_attr_name)
                        assert recipe_attr_name in ApiAttributesToUpdateOnRecipe.model_fields.keys()
            else:
                assert update_meal_cmd.updates.get(meal_attr_name) == getattr(meal, meal_attr_name)


class TestDeleteMeal:
    def test_api_and_domain_have_same_attributes(self) -> None:
        assert set(ApiDeleteMeal.model_fields.keys()) == set(
            DeleteMeal.__annotations__.keys()
        )


class TestCopyMeal:
    def test_api_and_domain_have_same_attributes(self) -> None:
        assert set(ApiCopyMeal.model_fields.keys()) == set(
            CopyMeal.__annotations__.keys()
        )

