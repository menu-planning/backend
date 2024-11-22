import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.recipes_catalog.shared.adapters.repositories.meal.meal import MealRepo
from src.contexts.recipes_catalog.shared.adapters.repositories.recipe.recipe import (
    RecipeRepo,
)
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from tests.recipes_catalog.integration.utils import recipe_with_foreign_keys_added_to_db

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_adding_a_meal_correctly_adds_the_recipes(
    async_pg_session: AsyncSession,
):
    recipe = await recipe_with_foreign_keys_added_to_db(
        async_pg_session, allergens_names=["first_allergen", "second_allergen"]
    )
    recipe_repo = RecipeRepo(async_pg_session)
    await recipe_repo.add(recipe)

    meal = Meal.create_meal(
        name="meal_name",
        author_id="author_id",
    )
    meal.add_recipe_from_recipe(recipe)
    assert len(meal.recipes) == 1
    meal_repo = MealRepo(async_pg_session)
    await meal_repo.add(meal)

    all_recipes = await recipe_repo.query()
    assert len(all_recipes) == 2
    meal_on_db = await meal_repo.get(meal.id)
    assert len(meal_on_db.recipes[0].diet_types_ids) > 0
    for attr, value in vars(recipe).items():
        if (
            attr == "_id"
            or attr == "_meal_id"
            or attr == "_author_id"
            or attr == "_created_at"
            or attr == "_updated_at"
        ):
            assert value != getattr(meal_on_db.recipes[0], attr)
        else:
            assert value == getattr(meal_on_db.recipes[0], attr)


async def test_coping_a_whole_meal(
    async_pg_session: AsyncSession,
):
    recipe = await recipe_with_foreign_keys_added_to_db(
        async_pg_session, allergens_names=["first_allergen", "second_allergen"]
    )
    recipe_repo = RecipeRepo(async_pg_session)
    await recipe_repo.add(recipe)

    meal = Meal.create_meal(
        name="meal_name",
        author_id="author_id",
    )
    meal.add_recipe_from_recipe(recipe)
    assert len(meal.recipes) == 1
    meal_repo = MealRepo(async_pg_session)
    await meal_repo.add(meal)
    new_meal = Meal.copy_meal(meal, "another_user_id")
    await meal_repo.add(new_meal)

    all_meals = await meal_repo.query()
    assert len(all_meals) == 2
    for attr, value in vars(all_meals[0]).items():
        if attr == "_recipes":
            continue
        if attr == "_id" or attr == "_author_id" or attr == "_version":
            assert value != getattr(all_meals[1], attr)
        else:
            assert value == getattr(all_meals[1], attr)

    all_recipes = await recipe_repo.query()
    assert len(all_recipes) == 3
    original_recipe = await recipe_repo.get(recipe.id)
    meal_on_db = await meal_repo.get(meal.id)
    new_meal_on_db = await meal_repo.get(new_meal.id)
    for attr, value in vars(original_recipe).items():
        if attr == "_id" or attr == "_meal_id" or attr == "_author_id":
            assert value != getattr(meal_on_db.recipes[0], attr)
            assert value != getattr(new_meal_on_db.recipes[0], attr)
        else:
            assert value == getattr(meal_on_db.recipes[0], attr)
            assert value == getattr(new_meal_on_db.recipes[0], attr)


@pytest.mark.parametrize(
    "attribute,filter_key,filter_value",
    [
        ("diet_types_ids", "diet_types", ["diet_type_name", "another_name"]),
        ("categories_ids", "categories", ["category_name", "another_name"]),
        ("meal_planning_ids", "meal_planning", ["meal_planning_name", "another_name"]),
        ("cuisines", "cuisines", ["cuisine_name", "another_name"]),
        ("flavors", "flavors", ["flavor_name", "another_name"]),
        ("textures", "textures", ["texture_name", "another_name"]),
        ("allergens", "allergens_not_exists", ["allergen_name", "another_name"]),
    ],
)
async def test_query_by_tag(
    async_pg_session: AsyncSession, attribute, filter_key, filter_value
):
    target_recipe = await recipe_with_foreign_keys_added_to_db(
        async_pg_session,
        diet_types_names=["diet_type_name"],
        categories_names=["category_name"],
        cuisine_name="cuisine_name",
        flavor_name="flavor_name",
        texture_name="texture_name",
        meal_planning_names=["meal_planning_name"],
        # allergen_names=["allergen_name"],
    )
    excluded_recipe = await recipe_with_foreign_keys_added_to_db(
        async_pg_session,
        diet_types_names=["diet_type_not_in"],
        categories_names=["category_not_in"],
        cuisine_name="cuisine_not_in",
        flavor_name="flavor_not_in",
        texture_name="texture_not_in",
        meal_planning_names=["meal_planning_not_in"],
        allergens_names=["allergen_name"],
    )
    meal_repo = MealRepo(async_pg_session)
    target_meal = Meal.create_meal(
        name="target_meal",
        author_id="author_id",
    )
    target_meal.add_recipe_from_recipe(target_recipe)
    excluded_meal = Meal.create_meal(
        name="excluded_meal",
        author_id="author_id",
    )
    excluded_meal.add_recipe_from_recipe(excluded_recipe)
    await meal_repo.add(target_meal)
    await meal_repo.add(excluded_meal)
    filter = {filter_key: filter_value}
    query = await meal_repo.query(filter)
    assert len(query) == 1
    assert target_meal == query[0]
    assert getattr(target_meal, attribute) == getattr(query[0], attribute)
    query_all = await meal_repo.query()
    assert len(query_all) == 2
