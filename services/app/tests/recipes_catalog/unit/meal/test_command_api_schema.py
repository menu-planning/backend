from attrs import asdict

from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.meal.copy_meal import (
    ApiCopyMeal,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.meal.create_meal import (
    ApiCreateMeal,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.meal.delete_meal import (
    ApiDeleteMeal,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.meal.remove_recipe_from_meal import (
    ApiRemoveRecipeFromMeal,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.meal.update import (
    ApiAttributesToUpdateOnMeal,
    ApiUpdateMeal,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.meal.update_recipe_on_meal import (
    ApiUpdateRecipeOnMeal,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.meal.meal import (
    ApiMeal,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipe.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.shared.domain.commands.meal.copy_meal import CopyMeal
from src.contexts.recipes_catalog.shared.domain.commands.meal.create_meal import (
    CreateMeal,
)
from src.contexts.recipes_catalog.shared.domain.commands.meal.delete_meal import (
    DeleteMeal,
)
from src.contexts.recipes_catalog.shared.domain.commands.meal.remove_recipe_from_meal import (
    RemoveRecipeFromMeal,
)
from src.contexts.recipes_catalog.shared.domain.commands.meal.update_meal import (
    UpdateMeal,
)
from src.contexts.recipes_catalog.shared.domain.commands.meal.update_recipe_on_meal import (
    UpdateRecipeOnMeal,
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


class TestRemoveRecipeFromMeal:
    def test_api_and_domain_have_same_attributes(self) -> None:
        assert set(ApiRemoveRecipeFromMeal.model_fields.keys()) == set(
            RemoveRecipeFromMeal.__annotations__.keys()
        )


class TestUpdateRecipeOnMeal:
    def test_api_and_domain_have_same_attributes(self) -> None:
        assert set(ApiUpdateRecipeOnMeal.model_fields.keys()) == set(
            UpdateRecipeOnMeal.__annotations__.keys()
        )
