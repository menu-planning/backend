import random

import pytest

from src.contexts.recipes_catalog.core.domain.entities import _Recipe
from src.contexts.shared_kernel.domain.exceptions import BusinessRuleValidationException
from tests.recipes_catalog.random_refs import (
    random_create_recipe_cmd_kwargs,
    random_ingredient,
    random_rate_cmd_kwargs,
    random_tag,
    random_user,
)


def test_recipe_creation():
    user = random_user()
    cmd = random_create_recipe_cmd_kwargs(author_id=user.id)
    recipe = _Recipe.create_recipe(**cmd)

    assert recipe.name == cmd["name"]
    assert recipe.description == cmd["description"]
    assert recipe.ingredients == cmd["ingredients"]
    assert recipe.instructions == cmd["instructions"]
    assert recipe.author_id == user.id


def test_rule_cannot_have_duplicate_positions_for_ingredients():
    user = random_user()
    ingredient_1 = random_ingredient(position=2)
    ingredient_2 = random_ingredient(position=2)
    cmd = random_create_recipe_cmd_kwargs(
        author_id=user.id, ingredients=[ingredient_1, ingredient_2]
    )
    with pytest.raises(BusinessRuleValidationException):
        _Recipe.create_recipe(**cmd)


def test_rule_ingredients_positions_must_be_consecutive():
    user = random_user()
    ingredient_1 = random_ingredient(position=1)
    ingredient_2 = random_ingredient(position=3)
    cmd = random_create_recipe_cmd_kwargs(
        author_id=user.id, ingredients=[ingredient_1, ingredient_2]
    )
    with pytest.raises(BusinessRuleValidationException):
        _Recipe.create_recipe(**cmd)


def test_tule_ingredients_positions_must_start_from_1():
    user = random_user()
    ingredient_1 = random_ingredient(position=2)
    ingredient_2 = random_ingredient(position=3)
    cmd = random_create_recipe_cmd_kwargs(
        author_id=user.id, ingredients=[ingredient_1, ingredient_2]
    )
    with pytest.raises(BusinessRuleValidationException):
        _Recipe.create_recipe(**cmd)


def test_recipe_discard():
    cmd = random_create_recipe_cmd_kwargs()
    recipe = _Recipe.create_recipe(**cmd)
    recipe.delete()
    assert recipe.discarded == True


def test_happy_recipe_update():
    cmd = random_create_recipe_cmd_kwargs()
    recipe = _Recipe.create_recipe(**cmd)

    assert recipe.name == cmd["name"]
    assert recipe.tags == cmd["tags"]

    new_tags = set(random_tag(author_id=recipe.author_id) for _ in range(3))
    recipe.update_properties(tags=new_tags)

    assert recipe.tags == new_tags


def test_canNOT_update_recipe_author():
    cmd = random_create_recipe_cmd_kwargs()
    recipe = _Recipe.create_recipe(**cmd)

    assert recipe.author_id == cmd["author_id"]

    new_author = random_user()
    with pytest.raises(Exception):
        recipe.update_properties(author_id=new_author.id)


def test_can_rate_a_recipe():
    cmd = random_create_recipe_cmd_kwargs()
    recipe = _Recipe.create_recipe(**cmd)

    recipe.rate(**random_rate_cmd_kwargs())
    assert recipe.ratings is not None
    assert len(recipe.ratings) == 1

    recipe.rate(**random_rate_cmd_kwargs())
    assert len(recipe.ratings) == 2
    assert (
        recipe.average_convenience_rating
        == (recipe.ratings[0].convenience + recipe.ratings[1].convenience) / 2
    )
    assert (
        recipe.average_taste_rating
        == (recipe.ratings[0].taste + recipe.ratings[1].taste) / 2
    )


def test_same_user_can_rate_only_once():
    cmd = random_create_recipe_cmd_kwargs()
    recipe = _Recipe.create_recipe(**cmd)
    user_id = 1

    recipe.rate(**random_rate_cmd_kwargs(user_id=user_id))
    assert recipe.ratings is not None
    assert len(recipe.ratings) == 1

    current_taste_rate = recipe.ratings[0].taste
    current_convenience_rate = recipe.ratings[0].convenience
    t = list(range(0, 6))
    t.remove(current_taste_rate)
    c = list(range(0, 6))
    c.remove(current_convenience_rate)
    new_taste_rate = random.choice(t)
    new_convenience_rate = random.choice(c)
    recipe.rate(
        **random_rate_cmd_kwargs(
            user_id=user_id, taste=new_taste_rate, convenience=new_convenience_rate
        )
    )
    assert len(recipe.ratings) == 1
    assert current_taste_rate != new_taste_rate
    assert current_convenience_rate != new_convenience_rate
    assert recipe.ratings[0].taste == new_taste_rate
    assert recipe.ratings[0].convenience == new_convenience_rate


def test_can_delete_a_rating():
    cmd = random_create_recipe_cmd_kwargs()
    recipe = _Recipe.create_recipe(**cmd)
    user_id = '1'

    recipe.rate(**random_rate_cmd_kwargs(user_id=user_id))
    assert recipe.ratings is not None
    assert len(recipe.ratings) == 1

    recipe.delete_rate(user_id=user_id)
    assert len(recipe.ratings) == 0
