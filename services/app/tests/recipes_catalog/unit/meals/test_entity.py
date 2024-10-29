import pytest
from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.recipes_catalog.shared.domain.entities.recipe import Recipe
from src.contexts.shared_kernel.domain.exceptions import DiscardedEntityException
from tests.recipes_catalog.random_refs import random_create_recipe_cmd_kwargs


def test_can_add_recipe():
    meal = Meal.create_meal(
        name="meal",
        author_id="author_id",
        recipes=[],
    )
    assert len(meal.recipes) == 0
    cmd = random_create_recipe_cmd_kwargs()
    recipe = meal.create_recipe(**cmd)
    assert recipe in meal.recipes
    assert len(meal.recipes) == 1


def test_can_delete_recipe():
    meal = Meal.create_meal(
        name="meal",
        author_id="author_id",
        recipes=[],
    )
    assert len(meal.recipes) == 0
    cmd = random_create_recipe_cmd_kwargs()
    recipe = meal.create_recipe(**cmd)
    cmd2 = random_create_recipe_cmd_kwargs()
    recipe2 = meal.create_recipe(**cmd2)
    assert len(meal.recipes) == 2
    meal.remove_recipe(recipe.id)
    assert len(meal.recipes) == 1
    meal.remove_recipe(recipe2.id)
    assert len(meal.recipes) == 0
    assert len(meal._recipes) == 2


def test_creating_meal_with_existing_recipe_change_recipe_id_and_meal_id():
    cmd = random_create_recipe_cmd_kwargs()
    recipe = Recipe.create_recipe(**cmd)
    meal = Meal.create_meal(
        name="meal",
        author_id="author_id",
        recipes=[recipe],
    )
    assert len(meal.recipes) == 1
    assert recipe.meal_id is None
    assert meal.recipes[0].meal_id == meal.id
    for attr, value in vars(recipe).items():
        if attr == "_id" or attr == "_meal_id":
            assert value != getattr(meal.recipes[0], attr)
        else:
            assert value == getattr(meal.recipes[0], attr)
