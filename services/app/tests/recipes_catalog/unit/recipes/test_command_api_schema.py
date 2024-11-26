from attrs import asdict
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.diet_types.create import (
    ApiCreateDietType,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.recipes.create import (
    ApiCreateRecipe,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.recipes.update import (
    ApiAttributesToUpdateOnRecipe,
    ApiUpdateRecipe,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipes.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.shared.domain.commands import CreateRecipe
from src.contexts.recipes_catalog.shared.domain.commands.diet_types.create import (
    CreateDietType,
)
from tests.recipes_catalog.random_refs import (
    random_create_recipe_cmd_kwargs,
    random_create_tag_cmd_kwargs,
    random_recipe,
    random_tag_name,
)


class TestApiCreateRecipe:
    def test_can_convert_to_domain(self) -> None:
        kwargs = random_create_recipe_cmd_kwargs()
        domain = CreateRecipe(**kwargs)
        kwargs["ingredients"] = [asdict(i) for i in kwargs["ingredients"]]
        kwargs["instructions"] = kwargs["instructions"]
        kwargs["nutri_facts"] = asdict(kwargs["nutri_facts"])
        kwargs["privacy"] = kwargs["privacy"].value
        kwargs["season"] = [i.value for i in kwargs["season"]]
        kwargs["cuisine"] = kwargs["cuisine"].name
        kwargs["flavor"] = kwargs["flavor"].name
        kwargs["texture"] = kwargs["texture"].name
        kwargs["allergens"] = [i.name for i in kwargs["allergens"]]
        api = ApiCreateRecipe(**kwargs)
        assert domain == api.to_domain()


class TestApiCreateTag:
    def test_can_convert_to_domain(self) -> None:
        kwargs = random_create_tag_cmd_kwargs(name=random_tag_name("DietType"))
        domain = CreateDietType(**kwargs)
        api = ApiCreateDietType(**kwargs)
        assert domain == api.to_domain()


def test_can_create_update_recipe_from_recipe():
    recipe = random_recipe()
    api_recipe = ApiRecipe.from_domain(recipe)
    update_recipe_cmd = ApiUpdateRecipe.from_api_recipe(api_recipe).to_domain()
    assert update_recipe_cmd.id == recipe.id
    for key in ApiAttributesToUpdateOnRecipe.model_fields.keys():
        assert update_recipe_cmd.updates.get(key) == getattr(recipe, key)
