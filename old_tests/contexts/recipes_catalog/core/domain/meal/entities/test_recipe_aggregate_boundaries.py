"""
Tests for Recipe aggregate boundary enforcement.

These tests document the Pythonic aggregate boundary convention where _Recipe entities
should be mutated through their parent Meal aggregate root using protected _set_* methods.
This maintains domain integrity through clear API design and developer discipline.

Following Python conventions: underscore prefixes indicate protected methods that
should only be called through the proper aggregate root (Meal), but are not
runtime-enforced for flexibility and performance.
"""

import pytest
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from tests.contexts.recipes_catalog.data_factories.meal.meal_domain_factories import (
    create_meal,
)
from tests.contexts.recipes_catalog.data_factories.meal.recipe.recipe_domain_factories import (
    create_ingredient,
    create_recipe,
)

# Import data factories for consistent test data


@pytest.fixture
def sample_nutri_facts() -> NutriFacts:
    """Create sample nutritional facts using consistent values."""
    return NutriFacts(
        calories=NutriValue(value=200.0, unit=MeasureUnit.ENERGY),
        carbohydrate=NutriValue(value=30.0, unit=MeasureUnit.GRAM),
        protein=NutriValue(value=15.0, unit=MeasureUnit.GRAM),
        total_fat=NutriValue(value=8.0, unit=MeasureUnit.GRAM),
    )


@pytest.fixture
def recipe_outside_meal(sample_nutri_facts: NutriFacts) -> _Recipe:
    """Create a Recipe instance NOT created through Meal aggregate using data factories."""
    # Create ingredients using the factory
    ingredients = [
        create_ingredient(name="Chicken breast", quantity=200.0, position=0),
        create_ingredient(name="Rice", quantity=100.0, position=1),
    ]

    return create_recipe(
        id="recipe-123",
        name="Test Recipe",
        ingredients=ingredients,
        instructions="Cook everything",
        author_id="user-456",
        meal_id="meal-789",
        nutri_facts=sample_nutri_facts,
        description="A test recipe",
    )


@pytest.fixture
def meal_with_recipe(sample_nutri_facts: NutriFacts) -> tuple[Meal, _Recipe]:
    """Create a Meal with a Recipe through proper aggregate boundary using data factories."""
    # Create meal using factory
    meal = create_meal(id="meal-789", name="Test Meal", author_id="user-456")

    # Create ingredients for the recipe
    ingredients = [
        create_ingredient(name="Chicken breast", quantity=200.0, position=0),
        create_ingredient(name="Rice", quantity=100.0, position=1),
    ]

    # Create recipe through Meal aggregate but get it from the meal's recipes
    meal.create_recipe(
        name="Test Recipe",
        ingredients=ingredients,
        instructions="Cook everything",
        nutri_facts=sample_nutri_facts,
        description="A test recipe",
        author_id="user-456",  # Required parameter
        meal_id="meal-789",  # Required parameter
    )

    # Get the recipe that was just created
    recipe = meal.recipes[-1]  # Should be the last recipe added

    return meal, recipe


class TestRecipeProtectedSetterConvention:
    """Test that Recipe properties follow Pythonic conventions with protected setters."""

    def test_recipe_properties_are_read_only(self, recipe_outside_meal: _Recipe):
        """Recipe properties should be read-only (no public setters)."""
        # These should fail because properties have no setters
        with pytest.raises(AttributeError, match="property 'id'.*has no setter"):
            recipe_outside_meal.id = "changed-id"  # type: ignore # Try to set a read-only property

    def test_protected_setters_exist_and_work(self, recipe_outside_meal: _Recipe):
        """Protected setters should exist and work (following Python convention)."""
        # These work because they're the intended API (even if called directly)
        original_name = recipe_outside_meal.name
        recipe_outside_meal._set_name("New Name via Protected Setter")
        assert recipe_outside_meal.name != original_name
        assert recipe_outside_meal.name == "New Name via Protected Setter"

    def test_update_properties_routes_to_protected_setters(
        self, recipe_outside_meal: _Recipe
    ):
        """update_properties should route to protected setters using reflection."""
        original_name = recipe_outside_meal.name
        original_description = recipe_outside_meal.description

        recipe_outside_meal.update_properties(
            name="Updated via update_properties", description="Updated description"
        )

        assert recipe_outside_meal.name != original_name
        assert recipe_outside_meal.description != original_description
        assert recipe_outside_meal.name == "Updated via update_properties"
        assert recipe_outside_meal.description == "Updated description"

    def test_update_properties_validates_property_names(
        self, recipe_outside_meal: _Recipe
    ):
        """update_properties should validate that properties exist."""
        with pytest.raises(
            AttributeError, match="Recipe has no property 'nonexistent'"
        ):
            recipe_outside_meal.update_properties(nonexistent="value")

    def test_update_properties_rejects_private_properties(
        self, recipe_outside_meal: _Recipe
    ):
        """update_properties should reject private property names."""
        with pytest.raises(AttributeError, match="_private_prop is private"):
            recipe_outside_meal.update_properties(_private_prop="value")


class TestRecipeActionMethodConvention:
    """Test that Recipe action methods follow Pythonic conventions."""

    def test_rate_method_works_directly(self, recipe_outside_meal: _Recipe):
        """Rating methods work directly (following convention that they should be called through Meal)."""
        original_ratings_count = (
            len(recipe_outside_meal.ratings) if recipe_outside_meal.ratings else 0
        )

        # This works (convention says it should be through Meal, but no runtime enforcement)
        recipe_outside_meal.rate(user_id="user-123", taste=4, convenience=3)

        recipe_ratings = recipe_outside_meal.ratings or []
        assert len(recipe_ratings) == original_ratings_count + 1
        assert recipe_ratings[-1].user_id == "user-123"
        assert recipe_ratings[-1].taste == 4

    def test_delete_method_works_directly(self, recipe_outside_meal: _Recipe):
        """Delete method works directly (convention says it should be through Meal)."""
        assert not recipe_outside_meal.discarded

        # This works (convention says it should be through Meal, but no runtime enforcement)
        recipe_outside_meal.delete()

        assert recipe_outside_meal.discarded


class TestMealRecipeMutationAllowed:
    """Test that Recipe mutations ARE allowed when called through Meal aggregate."""

    def test_meal_can_mutate_recipe_name(self, meal_with_recipe: tuple[Meal, _Recipe]):
        """Meal should be able to mutate Recipe name through update_recipes."""
        meal, recipe = meal_with_recipe
        original_name = recipe.name

        # This should work - mutation through Meal aggregate
        meal.update_recipes({recipe.id: {"name": "New Name via Meal"}})

        assert recipe.name != original_name
        assert recipe.name == "New Name via Meal"

    def test_meal_can_mutate_recipe_rating(
        self, meal_with_recipe: tuple[Meal, _Recipe]
    ):
        """Meal should be able to mutate Recipe ratings through rate_recipe."""
        meal, recipe = meal_with_recipe
        original_ratings_count = len(recipe.ratings) if recipe.ratings else 0

        # This should work - rating through Meal aggregate
        meal.rate_recipe(
            recipe_id=recipe.id,
            user_id="user-123",
            taste=4,
            convenience=3,
            comment="Great recipe!",
        )

        recipe_ratings = recipe.ratings or []
        assert len(recipe_ratings) == original_ratings_count + 1
        assert recipe_ratings[-1].user_id == "user-123"
        assert recipe_ratings[-1].taste == 4

    def test_meal_can_delete_recipe(self, meal_with_recipe: tuple[Meal, _Recipe]):
        """Meal should be able to delete Recipe through delete_recipe."""
        meal, recipe = meal_with_recipe
        assert not recipe.discarded

        # This should work - deletion through Meal aggregate
        meal.delete_recipe(recipe.id)

        assert recipe.discarded


class TestBoundaryEnforcementDocumentation:
    """Test edge cases documenting the Pythonic boundary convention."""

    def test_recipe_created_with_class_constructor_follows_convention(
        self, sample_nutri_facts: NutriFacts
    ):
        """Recipe created directly with constructor should follow Pythonic conventions."""
        ingredients = [
            create_ingredient(name="Direct ingredient", quantity=100.0, position=0)
        ]

        recipe = _Recipe(
            id="direct-recipe",
            name="Direct Recipe",
            ingredients=ingredients,
            instructions="Direct instructions",
            author_id="user-123",
            meal_id="meal-456",
            nutri_facts=sample_nutri_facts,
        )

        # Convention: should use protected setters, but not runtime-enforced
        recipe._set_name("Updated via protected setter")
        assert recipe.name == "Updated via protected setter"

    def test_recipe_created_with_create_recipe_follows_convention(
        self, sample_nutri_facts: NutriFacts
    ):
        """Recipe created with class method should follow Pythonic conventions."""
        ingredients = [
            create_ingredient(
                name="Class method ingredient", quantity=150.0, position=0
            )
        ]

        recipe = _Recipe.create_recipe(
            name="Class Method Recipe",
            ingredients=ingredients,
            instructions="Class method instructions",
            author_id="user-123",
            meal_id="meal-456",
            nutri_facts=sample_nutri_facts,
        )

        # Convention: should use protected setters, but not runtime-enforced
        recipe._set_description("Updated via protected setter")
        assert recipe.description == "Updated via protected setter"

    def test_copied_recipe_follows_convention(self, recipe_outside_meal: _Recipe):
        """Copied recipe should follow Pythonic conventions."""
        copied_recipe = _Recipe.copy_recipe(
            recipe=recipe_outside_meal, user_id="new-user", meal_id="new-meal"
        )

        # Convention: should use protected setters, but not runtime-enforced
        copied_recipe._set_instructions("Updated via protected setter")
        assert copied_recipe.instructions == "Updated via protected setter"
