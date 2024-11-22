from datetime import datetime

from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.recipes_catalog.shared.domain.entities.recipe import Recipe
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.domain.value_objects.name_tag.allergen import Allergen
from tests.recipes_catalog.random_refs import (
    random_create_meal_classmethod_kwargs,
    random_create_recipe_classmethod_kwargs,
    random_create_recipe_on_meal_kwargs,
    random_rating,
)


def test_can_add_recipe():
    meal = Meal.create_meal(
        name="meal",
        author_id="author_id",
    )
    assert len(meal.recipes) == 0
    cmd = random_create_recipe_on_meal_kwargs()
    recipe = meal.create_recipe(**cmd)
    assert recipe in meal.recipes
    assert len(meal.recipes) == 1


def test_can_delete_recipe():
    meal = Meal.create_meal(
        name="meal",
        author_id="author_id",
    )
    assert len(meal.recipes) == 0
    cmd = random_create_recipe_on_meal_kwargs()
    recipe = meal.create_recipe(**cmd)
    cmd2 = random_create_recipe_on_meal_kwargs()
    recipe2 = meal.create_recipe(**cmd2)
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
    meal.add_recipe_from_recipe(recipe)
    assert len(meal.recipes) == 1
    assert meal.recipes[0].meal_id == meal.id
    assert meal.recipes[0].id != recipe.id
    assert meal.recipes[0].author_id == meal.author_id
    # assert meal.recipes[0].
    for attr, value in vars(recipe).items():
        if attr == "_id" or attr == "_meal_id" or attr == "_author_id":
            assert value != getattr(meal.recipes[0], attr)
        else:
            assert value == getattr(meal.recipes[0], attr)


def test_can_copy_a_meal():
    cmd = random_create_meal_classmethod_kwargs()
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
    cmd = random_create_recipe_on_meal_kwargs()
    meal.create_recipe(**cmd)
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
        ):
            assert value != getattr(meal2.recipes[0], attr)
        else:
            assert value == getattr(meal2.recipes[0], attr)


def test_can_calculate_nutri_facts_from_recipes():
    meal = Meal.create_meal(
        name="meal",
        author_id="author_id",
    )
    cmd = random_create_recipe_on_meal_kwargs()
    recipe = meal.create_recipe(**cmd)
    cmd2 = random_create_recipe_on_meal_kwargs()
    recipe2 = meal.create_recipe(**cmd2)
    assert meal.nutri_facts == recipe.nutri_facts + recipe2.nutri_facts


def test_can_return_all_cuisines():
    meal = Meal.create_meal(
        name="meal",
        author_id="author_id",
    )
    cmd = random_create_recipe_on_meal_kwargs()
    recipe = meal.create_recipe(**cmd)
    cmd2 = random_create_recipe_on_meal_kwargs()
    recipe2 = meal.create_recipe(**cmd2)
    assert meal.cuisines == set([recipe.cuisine, recipe2.cuisine])


def test_can_return_diet_ypes_intersection():
    meal = Meal.create_meal(
        name="meal",
        author_id="author_id",
    )
    cmd = random_create_recipe_on_meal_kwargs(diet_types_ids={"Vegana"})
    meal.create_recipe(**cmd)
    cmd2 = random_create_recipe_on_meal_kwargs(diet_types_ids={"Vegana", "Sem lactose"})
    meal.create_recipe(**cmd2)
    assert len(meal.diet_types_ids) == 1
    assert "Vegana" in meal.diet_types_ids
    assert "Sem lactose" not in meal.diet_types_ids


def test_can_return_all_allergens():
    meal = Meal.create_meal(
        name="meal",
        author_id="author_id",
    )
    cmd = random_create_recipe_on_meal_kwargs(allergens={Allergen(name="Gluten")})
    meal.create_recipe(**cmd)
    cmd2 = random_create_recipe_on_meal_kwargs(
        allergens={Allergen(name="Gluten"), Allergen(name="Leite")}
    )
    meal.create_recipe(**cmd2)
    assert len(meal.allergens) == 2
    assert Allergen(name="Gluten") in meal.allergens
    assert Allergen(name="Leite") in meal.allergens
