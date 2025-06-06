from attrs import asdict

from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.recipe.copy import (
    ApiCopyRecipe,
)
from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.recipe.create import (
    ApiCreateRecipe,
)
from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.recipe.delete import (
    ApiDeleteRecipe,
)
from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.recipe.rate import (
    ApiRateRecipe,
)
from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.recipe.update import (
    ApiAttributesToUpdateOnRecipe,
    ApiUpdateRecipe,
)
from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.recipe.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.core.domain.commands.recipe.copy import CopyRecipe
from src.contexts.recipes_catalog.core.domain.commands.recipe.create import (
    CreateRecipe,
)
from src.contexts.recipes_catalog.core.domain.commands.recipe.delete import (
    DeleteRecipe,
)
from src.contexts.recipes_catalog.core.domain.commands.recipe.rate import RateRecipe
from src.contexts.recipes_catalog.core.domain.commands.recipe.update import (
    UpdateRecipe,
)
from tests.recipes_catalog.random_refs import (
    random_create_recipe_cmd_kwargs,
    random_recipe,
)


class TestApiCreateRecipe:
    def test_api_and_domain_have_same_attributes(self) -> None:
        assert set(ApiCreateRecipe.model_fields.keys()) == set(
            CreateRecipe.__annotations__.keys()
        )

    def test_can_convert_create_recipe_cmd_to_domain(self) -> None:
        kwargs = random_create_recipe_cmd_kwargs()
        domain = CreateRecipe(**kwargs)
        kwargs["ingredients"] = [asdict(i) for i in kwargs["ingredients"]]
        kwargs["instructions"] = kwargs["instructions"]
        kwargs["nutri_facts"] = asdict(kwargs["nutri_facts"])
        kwargs["privacy"] = kwargs["privacy"].value
        kwargs["tags"] = [asdict(t) for t in kwargs["tags"]]
        api = ApiCreateRecipe(**kwargs)
        assert domain == api.to_domain()

    def test_can_update_recipe_from_recipe(self):
        recipe = random_recipe()
        api_recipe = ApiRecipe.from_domain(recipe)
        update_recipe_cmd = ApiUpdateRecipe.from_api_recipe(api_recipe).to_domain()
        assert update_recipe_cmd.recipe_id == recipe.id
        for key in ApiAttributesToUpdateOnRecipe.model_fields.keys():
            assert update_recipe_cmd.updates.get(key) == getattr(recipe, key)


class TestDeleteRecipe:
    def test_api_and_domain_have_same_attributes(self) -> None:
        assert set(ApiDeleteRecipe.model_fields.keys()) == set(
            DeleteRecipe.__annotations__.keys()
        )


class TestCopyRecipe:
    def test_api_and_domain_have_same_attributes(self) -> None:
        assert set(ApiCopyRecipe.model_fields.keys()) == set(
            CopyRecipe.__annotations__.keys()
        )


class TestUpdateRecipe:
    def test_api_and_domain_have_same_attributes(self) -> None:
        assert set(ApiUpdateRecipe.model_fields.keys()) == set(
            UpdateRecipe.__annotations__.keys()
        )

    def test_only_the_fields_on_the_api_are_updated(self) -> None:
        recipe = random_recipe()
        api_recipe = ApiRecipe.from_domain(recipe)
        update_recipe_cmd = ApiUpdateRecipe.from_api_recipe(api_recipe).to_domain()
        assert len(ApiAttributesToUpdateOnRecipe.model_fields.keys()) == len(
            update_recipe_cmd.updates
        )
        for key in ApiAttributesToUpdateOnRecipe.model_fields.keys():
            assert update_recipe_cmd.updates.get(key) == getattr(recipe, key)
        assert api_recipe.author_id != None
        assert update_recipe_cmd.updates.get("author_id") == None


class TestRateRecipe:
    def test_api_and_domain_have_same_attributes(self) -> None:
        assert set(ApiRateRecipe.model_fields.keys()) == set(
            RateRecipe.__annotations__.keys()
        )
