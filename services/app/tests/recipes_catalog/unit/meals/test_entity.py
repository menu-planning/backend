from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
from src.contexts.recipes_catalog.shared.domain.entities.recipe import Recipe
from src.contexts.shared_kernel.domain.value_objects.name_tag.allergen import Allergen
from tests.recipes_catalog.random_refs import random_create_recipe_on_meal_kwargs


def test_can_add_recipe():
    meal = Meal.create_meal(
        name="meal",
        author_id="author_id",
        recipes=[],
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
        recipes=[],
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


def test_creating_meal_with_existing_recipe_change_recipe_id_and_meal_id():
    cmd = random_create_recipe_on_meal_kwargs()
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


def test_can_calculate_nutri_facts_from_recipes():
    meal = Meal.create_meal(
        name="meal",
        author_id="author_id",
        recipes=[],
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
        recipes=[],
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
        recipes=[],
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
        recipes=[],
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
