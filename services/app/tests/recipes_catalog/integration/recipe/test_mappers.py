import pytest

from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.recipe.recipe import \
    RecipeMapper
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.recipe import \
    RecipeSaModel
from src.contexts.recipes_catalog.shared.adapters.repositories.recipe.recipe import \
    RecipeRepo
from src.contexts.recipes_catalog.shared.domain.entities.recipe import Recipe
from tests.recipes_catalog.random_refs import random_ingredient, random_recipe
from tests.utils import build_dict_from_instance

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


def check_if_attributes_on_the_two_recipes_are_equal(
    domain_instance: Recipe, sa_instance: RecipeSaModel
):
    domain_instance_dict = build_dict_from_instance(domain_instance)
    sa_instance_dict = build_dict_from_instance(sa_instance)
    domain_instance_dict.pop("events")
    domain_nutris = {
        k: v["value"] for k, v in domain_instance_dict["nutri_facts"].items()
    }
    domain_instance_dict["nutri_facts"] = domain_nutris
    for i in domain_instance_dict["nutri_facts"].keys():
        assert sa_instance_dict.pop(i) == domain_instance_dict["nutri_facts"][i]
    assert (
        sa_instance_dict.pop("average_convenience_rating")
        == None
        == domain_instance.average_convenience_rating
    )
    assert (
        sa_instance_dict.pop("average_taste_rating")
        == None
        == domain_instance.average_taste_rating
    )
    assert (
        sa_instance_dict.pop("calorie_density")
        == domain_instance.calorie_density
        != None
    )
    assert (
        sa_instance_dict.pop("carbo_percentage")
        == domain_instance.carbo_percentage
        != None
    )
    assert (
        sa_instance_dict.pop("total_fat_percentage")
        == domain_instance.total_fat_percentage
        != None
    )
    assert (
        sa_instance_dict.pop("protein_percentage")
        == domain_instance.protein_percentage
        != None
    )
    for i in sa_instance_dict["ingredients"]:
        assert i.pop("preprocessed_name") != None
        assert domain_instance_dict.get("preprocessed_name") == None
        assert i.pop("recipe_id") != None
        assert domain_instance_dict.get("recipe_id") == None
        try:
            i.pop("created_at")
        except KeyError:
            pass
    assert sa_instance_dict.pop("preprocessed_name") != None
    assert domain_instance_dict.get("preprocessed_name") == None
    for tag in sa_instance_dict["tags"]:
        try:
            tag.pop("id")
        except KeyError:
            pass
    assert domain_instance_dict == sa_instance_dict


class TestRecipeMapper:
    async def test_map_recipe_to_recipesamodel_when_entities_are_not_in_the_db(
        self, async_pg_session
    ):
        domain_instance = random_recipe()
        domain_instance_dict = build_dict_from_instance(domain_instance)
        mapper = RecipeMapper()
        sa_instance = await mapper.map_domain_to_sa(async_pg_session, domain_instance)
        sa_instance_dict = build_dict_from_instance(sa_instance)
        missing = [i for i in domain_instance_dict.keys() if i not in sa_instance_dict]
        missing.remove("events")
        assert not missing, f"Missing attributes: {missing}"
        assert domain_instance.created_at == None
        assert domain_instance.updated_at == None
        domain_instance._created_at = sa_instance.created_at
        domain_instance._updated_at = sa_instance.updated_at
        check_if_attributes_on_the_two_recipes_are_equal(domain_instance, sa_instance)

    async def test_map_Recipe_to_RecipeSaModel_and_back_to_Recipe_when_entities_are_NOT_in_the_db(
        self, async_pg_session
    ):
        domain_instance = random_recipe()
        domain_instance_dict = build_dict_from_instance(domain_instance)
        mapper = RecipeMapper()
        sa_instance = await mapper.map_domain_to_sa(async_pg_session, domain_instance)
        domain_instance_again = mapper.map_sa_to_domain(sa_instance)
        domain_instance_dict_again = build_dict_from_instance(domain_instance_again)
        assert domain_instance_dict.pop("created_at") == None != domain_instance_dict_again.pop(
            "created_at"
        )
        assert domain_instance_dict.pop("updated_at") == None != domain_instance_dict_again.pop(
            "updated_at"
        )
        assert domain_instance_dict == domain_instance_dict_again

    async def test_map_Recipe_to_RecipeSaModel_when_recipe_already_in_the_db(
        self, async_pg_session
    ):
        domain_instance = random_recipe()
        repo = RecipeRepo(async_pg_session)
        await repo.add(domain_instance)
        # await async_pg_session.commit()
        domain_instance = await repo.get(domain_instance.id)
        domain_instance_dict = build_dict_from_instance(domain_instance)
        mapper = RecipeMapper()
        sa_instance = await mapper.map_domain_to_sa(async_pg_session, domain_instance)
        sa_instance_dict = build_dict_from_instance(sa_instance)
        missing = [i for i in domain_instance_dict.keys() if i not in sa_instance_dict]
        missing.remove("events")
        assert not missing, f"Missing attributes: {missing}"
        check_if_attributes_on_the_two_recipes_are_equal(domain_instance, sa_instance)
        assert domain_instance.created_at == sa_instance.created_at != None
        # assert domain_instance.updated_at == sa_instance.updated_at != None
        assert sa_instance.tags[0].id != None
        assert sa_instance.ingredients[0].created_at != None

 
