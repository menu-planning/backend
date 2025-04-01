from copy import deepcopy
from datetime import datetime

from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.recipes_catalog.shared.domain.entities.recipe import Recipe
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from tests.recipes_catalog.random_refs import (
    random_create_meal_classmethod_kwargs,
    random_create_recipe_classmethod_kwargs,
    random_create_recipe_tag_cmd_kwargs,
    random_meal,
    random_rating,
    random_recipe,
)


def test_can_add_recipe_to_meal():
    meal = Meal.create_meal(
        name="meal",
        author_id="author_id",
    )
    assert len(meal.recipes) == 0
    # cmd = random_create_recipe_on_meal_kwargs()
    recipe = meal.add_recipe(random_recipe(meal_id=meal.id, author_id=meal.author_id))
    assert recipe in meal.recipes
    assert len(meal.recipes) == 1


def test_can_delete_recipe_from_meal():
    meal = Meal.create_meal(
        name="meal",
        author_id="author_id",
    )
    assert len(meal.recipes) == 0
    # cmd = random_create_recipe_on_meal_kwargs()
    recipe = meal.add_recipe(random_recipe(meal_id=meal.id, author_id=meal.author_id))
    # cmd2 = random_create_recipe_on_meal_kwargs()
    recipe2 = meal.add_recipe(random_recipe(meal_id=meal.id, author_id=meal.author_id))
    assert len(meal.recipes) == 2
    meal.remove_recipe(recipe.id)
    assert len(meal.recipes) == 1
    meal.remove_recipe(recipe2.id)
    assert len(meal.recipes) == 0
    assert len(meal._recipes) == 2


def test_can_copy_a_recipe_to_meal():
    cmd = random_create_recipe_classmethod_kwargs()
    recipe = Recipe.create_recipe(**cmd)
    meal = Meal.create_meal(
        name="meal",
        author_id="author_id",
    )
    meal.copy_recipes([recipe])
    assert len(meal.recipes) == 1
    assert meal.recipes[0].meal_id == meal.id
    assert meal.recipes[0].id != recipe.id
    assert meal.recipes[0].author_id == meal.author_id
    for attr, value in vars(recipe).items():
        if (
            attr == "_id"
            or attr == "_meal_id"
            or attr == "_author_id"
            or attr == "_tags"
        ):
            assert value != getattr(meal.recipes[0], attr)
        else:
            assert value == getattr(meal.recipes[0], attr)


def test_can_copy_a_meal():
    cmd = random_create_meal_classmethod_kwargs(recipes=[])
    meal = Meal.create_meal(**cmd)
    assert len(meal.recipes) == 0
    meal.update_properties(
        description="meal description",
        notes="meal notes",
        image_url="meal image_url",
        like=True,
    )
    meal._created_at = datetime.now()
    meal._updated_at = datetime.now()
    assert meal.version == 2
    # cmd = random_create_recipe_on_meal_kwargs()
    meal.add_recipe(random_recipe(meal_id=meal.id, author_id=meal.author_id))
    meal._recipes[0]._ratings = [random_rating()]
    meal._recipes[0]._privacy == Privacy.PUBLIC
    meal._recipes[0]._created_at = datetime.now()
    meal._recipes[0]._updated_at = datetime.now()
    meal._recipes[0]._version = 2
    assert len(meal.recipes) == 1
    meal2 = Meal.copy_meal(meal, "author_id")
    assert len(meal2.recipes) == len(meal.recipes) == 1
    assert meal2.author_id == meal2.recipes[0].author_id == "author_id"
    assert meal2.created_at is None
    assert meal2.updated_at is None
    assert meal2.version == 1
    assert meal2.like is None
    assert len(meal2.recipes[0].ratings) == 0
    # what is different
    assert meal2.id != meal.id
    assert meal.author_id != meal2.author_id
    assert meal2.recipes[0].author_id != meal.recipes[0].author_id
    assert meal2.recipes[0].id != meal.recipes[0].id
    assert meal2.created_at != meal.created_at
    assert meal2.updated_at != meal.updated_at
    assert meal2.version != meal.version
    assert meal2.like != meal.like
    assert len(meal2.recipes[0].ratings) != len(meal.recipes[0].ratings)
    # what is the same
    assert meal2.name == meal.name
    assert meal2.description == meal.description
    assert meal2.notes == meal.notes
    assert meal2.image_url == meal.image_url
    for attr, value in vars(meal.recipes[0]).items():
        if (
            attr == "_id"
            or attr == "_meal_id"
            or attr == "_author_id"
            or attr == "_created_at"
            or attr == "_updated_at"
            or attr == "_version"
            or attr == "_ratings"
            or attr == "_tags"
        ):
            assert value != getattr(meal2.recipes[0], attr)
        else:
            assert value == getattr(meal2.recipes[0], attr)


def test_can_calculate_nutri_facts_from_recipes():
    meal = Meal.create_meal(
        name="meal",
        author_id="author_id",
    )
    # cmd = random_create_recipe_on_meal_kwargs()
    recipe = meal.add_recipe(random_recipe(meal_id=meal.id, author_id=meal.author_id))
    # cmd2 = random_create_recipe_on_meal_kwargs()
    recipe2 = meal.add_recipe(random_recipe(meal_id=meal.id, author_id=meal.author_id))
    assert meal.nutri_facts == recipe.nutri_facts + recipe2.nutri_facts


def test_can_return_all_recipes_tags():
    meal = Meal.create_meal(
        name="meal",
        author_id="author_id",
    )
    recipe1_tag_cmd = random_create_recipe_tag_cmd_kwargs()
    recipe1_tag = Tag(**recipe1_tag_cmd)
    recipe2_tag_cmd = random_create_recipe_tag_cmd_kwargs()
    recipe2_tag = Tag(**recipe2_tag_cmd)
    # cmd = random_create_recipe_on_meal_kwargs(tags=[recipe1_tag])
    meal.add_recipe(
        random_recipe(meal_id=meal.id, author_id=meal.author_id, tags=[recipe1_tag])
    )
    # cmd2 = random_create_recipe_on_meal_kwargs(tags=[recipe2_tag])
    meal.add_recipe(
        random_recipe(meal_id=meal.id, author_id=meal.author_id, tags=[recipe2_tag])
    )
    assert set(meal.recipes_tags) == {recipe1_tag, recipe2_tag}


def test_update_properties_can_add_new_recipes_and_update_version_on_old_ones():
    meal = random_meal()
    assert len(meal.recipes) == 3
    aditional_recipes = [
        random_recipe(author_id=meal.author_id, meal_id=meal.id) for _ in range(3)
    ]
    meal.update_properties(
        recipes=[r for r in meal.recipes] + aditional_recipes,
    )
    assert len(meal.recipes) == 6
    for recipe in meal.recipes:
        assert recipe in [r for r in meal.recipes] + aditional_recipes
        if recipe.id in [r.id for r in aditional_recipes]:
            assert recipe._version == 1
        else:
            assert recipe._version == 2


def test_update_properties_can_delete_recipes():
    meal = random_meal()
    assert len(meal.recipes) == 3
    recipe1 = meal.recipes[0]
    aditional_recipes = [
        random_recipe(author_id=meal.author_id, meal_id=meal.id) for _ in range(3)
    ]
    meal.update_properties(
        recipes=[recipe1] + aditional_recipes,
    )
    assert len(meal.recipes) == 4
    for recipe in meal.recipes:
        assert recipe in [recipe1] + aditional_recipes
        if recipe.id in [r.id for r in aditional_recipes]:
            assert recipe._version == 1
        else:
            assert recipe._version == 2


def test_updating_recipes_reflects_on_meal_properties_and_version():
    meal = random_meal()
    assert meal.version == 1
    assert len(meal.recipes) == 3
    recipe1 = meal.recipes[0]
    aditional_recipes = [
        random_recipe(author_id=meal.author_id, meal_id=meal.id) for _ in range(3)
    ]
    meal.update_properties(
        name=meal.name,
        recipes=[recipe1] + aditional_recipes,
    )
    assert len(meal.recipes) == 4
    assert meal.weight_in_grams == sum(
        recipe.weight_in_grams for recipe in meal.recipes
    ) == recipe1.weight_in_grams + sum(
        recipe.weight_in_grams for recipe in aditional_recipes
    )
    assert meal.nutri_facts == sum(
        recipe.nutri_facts for recipe in meal.recipes
    ) == recipe1.nutri_facts + sum(
        recipe.nutri_facts for recipe in aditional_recipes
    )
    assert meal.version == 2
    
def test_update_properties():
    meal = random_meal()
    meal_original_recipe_ids = [r.id for r in meal.recipes]
    assert len(meal.recipes) == 3
    another_meal = random_meal(author_id=meal.author_id)
    recipe_id_to_remove = meal.recipes[0].id
    meal.remove_recipe(recipe_id_to_remove)
    assert len(meal.recipes) == 2
    another_meal_recipes = [deepcopy(r) for r in another_meal.recipes]
    for recipe in another_meal_recipes:
        recipe._meal_id = meal.id
    all_recipes = [r for r in meal.recipes] + another_meal_recipes
    for recipe in all_recipes:
        assert recipe._version == 1
    assert recipe_id_to_remove not in [r.id for r in all_recipes]
    meal.update_properties(
        description=another_meal.description,
        notes=another_meal.notes,
        image_url=another_meal.image_url,
        like=another_meal.like,
        recipes=all_recipes,
    )
    for recipe in another_meal.recipes:
        assert recipe._version == 1
    assert meal.description == another_meal.description
    assert meal.notes == another_meal.notes
    assert meal.image_url == another_meal.image_url
    assert meal.like == another_meal.like
    for recipe in meal.recipes:
        assert recipe.id in [r.id for r in all_recipes]
        if recipe.id in meal_original_recipe_ids:
            assert recipe._version == 2
        else:
            assert recipe._version == 1
