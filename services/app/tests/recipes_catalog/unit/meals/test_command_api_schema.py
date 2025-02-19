from attrs import asdict

from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.meals.copy_meal import (
    ApiCopyMeal,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.meals.create import (
    ApiCreateMeal,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.meals.delete_meal import (
    ApiDeleteMeal,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.meals.update import (
    ApiAttributesToUpdateOnMeal,
    ApiUpdateMeal,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.meals.meal import (
    ApiMeal,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipes.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.shared.domain.commands.meals.copy_meal import CopyMeal
from src.contexts.recipes_catalog.shared.domain.commands.meals.create_meal import (
    CreateMeal,
)
from src.contexts.recipes_catalog.shared.domain.commands.meals.delete_meal import (
    DeleteMeal,
)
from src.contexts.recipes_catalog.shared.domain.commands.meals.update_meal import (
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

    def test_update_meal_from_meal(self):
        meal = random_meal()
        api_meal = ApiMeal.from_domain(meal)
        update_meal_cmd = ApiUpdateMeal.from_api_meal(api_meal).to_domain()
        assert update_meal_cmd.meal_id == meal.id
        for key in ApiAttributesToUpdateOnMeal.model_fields.keys():
            assert update_meal_cmd.updates.get(key) == getattr(meal, key)


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
