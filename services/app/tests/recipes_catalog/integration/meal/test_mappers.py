import pytest
from attrs import asdict

from src.contexts.recipes_catalog.shared.adapters.ORM.mappers.meal.meal import \
    MealMapper
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.meal.meal import \
    MealSaModel
from src.contexts.recipes_catalog.shared.adapters.repositories.meal.meal import \
    MealRepo
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from tests.recipes_catalog.integration.recipes.test_mappers import \
    check_if_attributes_on_the_two_recipes_are_equal
from tests.recipes_catalog.random_refs import random_meal
from tests.utils import build_dict_from_instance

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


def _test_if_attributes_are_equal(domain_instance: Meal, sa_instance: MealSaModel):
    domain_instance_dict = build_dict_from_instance(domain_instance)
    sa_instance_dict = build_dict_from_instance(sa_instance)
    domain_instance_dict.pop("events")
    domain_instance_dict["nutri_facts"] = {
        k: v["value"] for k, v in asdict(domain_instance.nutri_facts).items()
    }
    domain_instance_dict["weight_in_grams"] = domain_instance.weight_in_grams
    domain_instance_dict["total_time"] = domain_instance.total_time
    for i in sa_instance_dict["nutri_facts"].keys():
        assert sa_instance_dict.pop(i) == domain_instance_dict["nutri_facts"][i]
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
    for domain_recipe in domain_instance.recipes:
        for sa_recipe in sa_instance.recipes:
            if domain_recipe.id == sa_recipe.id:
                check_if_attributes_on_the_two_recipes_are_equal(
                    domain_recipe, sa_recipe
                )
    domain_instance_dict.pop("recipes")
    sa_instance_dict.pop("recipes")
    assert sa_instance_dict.pop("preprocessed_name") != None
    assert domain_instance_dict.get("preprocessed_name") == None
    for tag in sa_instance_dict["tags"]:
        try:
            tag.pop("id")
        except KeyError:
            pass
    assert domain_instance_dict == sa_instance_dict


class TestMealMapper:
    async def test_map_Meal_to_MealSaModel_when_entities_are_NOT_in_the_db(
        self, async_pg_session
    ):
        domain_instance = random_meal()
        for recipe in domain_instance.recipes:
            recipe.meal_id = domain_instance.id
        domain_instance_dict = build_dict_from_instance(domain_instance)
        mapper = MealMapper()
        sa_instance = await mapper.map_domain_to_sa(async_pg_session, domain_instance)
        sa_instance_dict = build_dict_from_instance(sa_instance)
        missing = [i for i in domain_instance_dict.keys() if i not in sa_instance_dict]
        missing.remove("events")
        assert not missing, f"Missing attributes: {missing}"
        assert domain_instance.created_at == None
        assert domain_instance.updated_at == None
        domain_instance._created_at = sa_instance.created_at
        domain_instance._updated_at = sa_instance.updated_at
        for domain_recipe in domain_instance.recipes:
            for sa_recipe in sa_instance.recipes:
                if domain_recipe.id == sa_recipe.id:
                    assert domain_recipe.created_at == None
                    assert domain_recipe.updated_at == None
                    domain_recipe._created_at = sa_recipe.created_at
                    domain_recipe._updated_at = sa_recipe.updated_at
        _test_if_attributes_are_equal(domain_instance, sa_instance)
        

    async def test_map_Meal_to_MealSaModel_and_back_to_Meal_when_entities_are_NOT_in_the_db(
        self, async_pg_session
    ):
        domain_instance = random_meal()
        domain_instance_dict = build_dict_from_instance(domain_instance)
        mapper = MealMapper()
        sa_instance = await mapper.map_domain_to_sa(async_pg_session, domain_instance)
        domain_instance_again = mapper.map_sa_to_domain(sa_instance)
        domain_instance_dict_again = build_dict_from_instance(domain_instance_again)
        assert domain_instance_dict.pop("created_at") == None != domain_instance_dict_again.pop("created_at")
        assert domain_instance_dict.pop("updated_at") == None != domain_instance_dict_again.pop("updated_at")
        for initial_recipe in domain_instance_dict["recipes"]:
            for back_recipe in domain_instance_dict_again["recipes"]:
                if initial_recipe["id"] == back_recipe["id"]:
                    assert initial_recipe.pop("created_at") == None != back_recipe.pop("created_at")
                    assert initial_recipe.pop("updated_at") == None != back_recipe.pop("updated_at")
        assert domain_instance_dict == domain_instance_dict_again

    async def test_map_Meal_to_MealSaModel_when_meal_already_in_the_db(
        self, async_pg_session
    ):
        domain_instance = random_meal()
        repo = MealRepo(async_pg_session)
        await repo.add(domain_instance)
        # await async_pg_session.commit()
        domain_instance = await repo.get(domain_instance.id)
        domain_instance_dict = build_dict_from_instance(domain_instance)
        mapper = MealMapper()
        sa_instance = await mapper.map_domain_to_sa(async_pg_session, domain_instance)
        sa_instance_dict = build_dict_from_instance(sa_instance)
        missing = [i for i in domain_instance_dict.keys() if i not in sa_instance_dict]
        missing.remove("events")
        assert not missing, f"Missing attributes: {missing}"
        _test_if_attributes_are_equal(domain_instance, sa_instance)
        assert domain_instance.created_at == sa_instance.created_at != None
        assert domain_instance.updated_at == sa_instance.updated_at != None
        assert sa_instance.tags[0].id != None
        for recipe in sa_instance.recipes:
            assert recipe.created_at != None
