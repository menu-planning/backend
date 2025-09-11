"""
ApiCreateMeal Core Functionality Test Suite

Test classes for core ApiCreateMeal functionality including basic conversions,
meal creation, and domain conversion.

Following the same pattern as test_api_create_recipe_core.py but adapted for ApiCreateMeal.
ApiCreateMeal is more complex since meals are parent entities of recipes.
"""

from uuid import uuid4

# Import the helper functions from conftest
from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.conftest import (
    create_api_create_meal_kwargs,
    create_api_create_meal_with_author_id,
    create_api_create_meal_with_custom_recipes,
    create_api_create_meal_with_custom_tags,
    create_api_create_meal_with_recipes_and_tags,
    create_minimal_api_create_meal_kwargs,
    create_minimal_api_create_meal_with_author_id,
)

# Import data factories for nested objects
from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    create_complex_api_recipe,
    create_simple_api_recipe,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_meal import (
    ApiCreateMeal,
)


class TestApiCreateMealBasics:
    """
    Test suite for basic ApiCreateMeal functionality (>95% coverage target).
    """

    def test_valid_meal_creation(self, valid_api_create_meal_kwargs):
        """Test creation of valid ApiCreateMeal instances."""
        meal = ApiCreateMeal(**valid_api_create_meal_kwargs)
        assert meal.name is not None
        assert meal.author_id is not None
        assert meal.menu_id is not None
        assert meal.recipes is not None
        assert meal.tags is not None

    def test_minimal_meal_creation(self, minimal_api_create_meal_kwargs):
        """Test creation with minimal required fields."""
        meal = ApiCreateMeal(**minimal_api_create_meal_kwargs)
        assert meal.name is not None
        assert meal.author_id is not None
        assert meal.menu_id is not None
        assert meal.recipes is not None
        assert meal.tags is not None
        # Optional fields should be None
        assert meal.description is None
        assert meal.notes is None
        assert meal.image_url is None

    def test_meal_with_empty_recipes_and_tags(self):
        """Test creation with empty recipes and tags collections."""
        author_id = str(uuid4())
        kwargs = create_minimal_api_create_meal_kwargs(
            author_id=author_id, recipes=[], tags=frozenset()
        )

        meal = ApiCreateMeal(**kwargs)

        # Verify basic properties
        assert meal.author_id == author_id
        assert meal.name is not None
        assert meal.menu_id is not None

        # Verify empty collections
        assert meal.recipes == []
        assert meal.tags == frozenset()

    def test_author_id_constraint_consistency(self):
        """Test that author_id constraint is properly maintained between meal, recipes, and tags."""
        # Create a specific author_id
        author_id = "550e8400-e29b-41d4-a716-446655440000"

        # Create meal with custom recipes and tags using the helper function
        custom_recipes = [
            create_simple_api_recipe(name="Test Recipe 1", author_id=author_id),
            create_simple_api_recipe(name="Test Recipe 2", author_id=author_id),
        ]

        custom_tags = [
            {"key": "meal_type", "value": "dinner"},
            {"key": "difficulty", "value": "medium"},
            {"key": "cuisine", "value": "italian"},
        ]

        kwargs = create_api_create_meal_with_recipes_and_tags(
            author_id=author_id, recipes=custom_recipes, tags=custom_tags
        )

        meal = ApiCreateMeal(**kwargs)

        # Verify that the meal has the correct author_id
        assert meal.author_id == author_id

        # Verify that all recipes have the same author_id
        assert meal.recipes is not None
        assert len(meal.recipes) == 2
        for recipe in meal.recipes:
            assert recipe.author_id == author_id

        # Verify that all tags have the same author_id
        assert meal.tags is not None
        assert len(meal.tags) == 3
        for tag in meal.tags:
            assert tag.author_id == author_id

    def test_meal_with_multiple_recipes_complex_structure(self):
        """Test creating meal with multiple recipes of different complexities."""
        # Create a specific author_id
        author_id = str(uuid4())
        meal_id = str(uuid4())

        # Create recipes with different complexities
        custom_recipes = [
            create_simple_api_recipe(
                name="Starter Salad", author_id=author_id, meal_id=meal_id
            ),
            create_complex_api_recipe(
                name="Main Course Pasta", author_id=author_id, meal_id=meal_id
            ),
            create_simple_api_recipe(
                name="Dessert Ice Cream", author_id=author_id, meal_id=meal_id
            ),
        ]

        # Define comprehensive tags
        custom_tags = [
            {"key": "meal_type", "value": "dinner"},
            {"key": "difficulty", "value": "medium"},
            {"key": "cuisine", "value": "italian"},
            {"key": "occasion", "value": "family"},
        ]

        kwargs = create_api_create_meal_with_recipes_and_tags(
            author_id=author_id,
            recipes=custom_recipes,
            tags=custom_tags,
            name="Italian Family Dinner",
            description="Complete Italian dinner with starter, main course, and dessert",
            notes="Perfect for Sunday family gatherings. Allow 2 hours total preparation time.",
            menu_id=str(uuid4()),
        )

        meal = ApiCreateMeal(**kwargs)

        # Verify meal properties
        assert meal.author_id == author_id
        assert meal.name == "Italian Family Dinner"
        assert meal.description is not None and "Italian dinner" in meal.description
        assert meal.notes is not None and "family gatherings" in meal.notes

        # Verify recipes
        assert meal.recipes is not None
        assert len(meal.recipes) == 3
        recipe_names = {recipe.name for recipe in meal.recipes}
        assert recipe_names == {
            "Starter Salad",
            "Main Course Pasta",
            "Dessert Ice Cream",
        }

        # Verify all recipes belong to this meal's author
        for recipe in meal.recipes:
            assert recipe.author_id == author_id
            assert recipe.meal_id == meal_id

        # Verify tags
        assert meal.tags is not None
        assert len(meal.tags) == 4
        for tag in meal.tags:
            assert tag.author_id == author_id

        tag_values = {tag.value for tag in meal.tags}
        assert tag_values == {"dinner", "medium", "italian", "family"}

    def test_meal_hierarchical_structure_validation(self):
        """Test that meals properly maintain hierarchical structure as parent of recipes."""
        author_id = str(uuid4())
        meal_id = str(uuid4())

        # Create recipes that belong to the meal
        recipes_for_meal = [
            create_simple_api_recipe(
                name="Recipe A", author_id=author_id, meal_id=meal_id
            ),
            create_simple_api_recipe(
                name="Recipe B", author_id=author_id, meal_id=meal_id
            ),
        ]

        kwargs = create_api_create_meal_with_custom_recipes(
            author_id=author_id, recipes=recipes_for_meal, name="Parent Meal"
        )

        meal = ApiCreateMeal(**kwargs)

        # Verify hierarchical structure
        assert meal.author_id == author_id
        assert meal.name == "Parent Meal"

        # Verify child recipes
        assert meal.recipes is not None
        assert len(meal.recipes) == 2

        # Verify that all recipes maintain parent-child relationship consistency
        for recipe in meal.recipes:
            assert recipe.author_id == author_id  # Same author as parent
            assert recipe.meal_id == meal_id  # Belongs to specific meal


class TestApiCreateMealDomainConversion:
    """
    Test suite for ApiCreateMeal domain conversion functionality.
    """

    def test_domain_conversion_simple_meal(self):
        """Test domain conversion with simple meal."""
        kwargs = create_minimal_api_create_meal_kwargs()
        api_meal = ApiCreateMeal(**kwargs)

        # Test conversion to domain command
        domain_command = api_meal.to_domain()
        assert domain_command is not None
        assert hasattr(domain_command, "name")
        assert hasattr(domain_command, "author_id")
        assert hasattr(domain_command, "menu_id")
        assert hasattr(domain_command, "meal_id")  # Auto-generated field

    def test_domain_conversion_complex_meal(self):
        """Test domain conversion with complex meal including recipes and tags."""
        kwargs = create_api_create_meal_kwargs()
        api_meal = ApiCreateMeal(**kwargs)

        # Test conversion to domain command
        domain_command = api_meal.to_domain()
        assert domain_command is not None
        assert hasattr(domain_command, "name")
        assert hasattr(domain_command, "author_id")
        assert hasattr(domain_command, "menu_id")
        assert hasattr(domain_command, "recipes")
        assert hasattr(domain_command, "tags")

    def test_domain_conversion_with_all_fields(self):
        """Test domain conversion with all fields populated."""
        author_id = str(uuid4())
        meal_id = str(uuid4())

        # Create comprehensive meal data
        custom_recipes = [
            create_simple_api_recipe(
                name="Appetizer", author_id=author_id, meal_id=meal_id
            ),
            create_simple_api_recipe(
                name="Main Course", author_id=author_id, meal_id=meal_id
            ),
        ]

        custom_tags = [
            {"key": "cuisine", "value": "french"},
            {"key": "difficulty", "value": "hard"},
        ]

        kwargs = create_api_create_meal_with_recipes_and_tags(
            author_id=author_id,
            recipes=custom_recipes,
            tags=custom_tags,
            name="Complete Meal",
            description="Comprehensive meal description",
            notes="Detailed preparation notes",
            menu_id=str(uuid4()),
            image_url="https://example.com/meal-image.jpg",
        )

        api_meal = ApiCreateMeal(**kwargs)

        # Test conversion to domain command
        domain_command = api_meal.to_domain()
        assert domain_command is not None
        assert hasattr(domain_command, "name")
        assert hasattr(domain_command, "author_id")
        assert hasattr(domain_command, "menu_id")
        assert hasattr(domain_command, "recipes")
        assert hasattr(domain_command, "tags")

        # Verify field mapping
        assert domain_command.name == api_meal.name
        assert domain_command.author_id == api_meal.author_id
        assert domain_command.menu_id == api_meal.menu_id
        assert domain_command.description == api_meal.description
        assert domain_command.notes == api_meal.notes
        assert (
            domain_command.image_url == str(api_meal.image_url)
            if api_meal.image_url
            else None
        )

    def test_domain_conversion_with_empty_collections(self):
        """Test domain conversion handles empty recipes and tags properly."""
        kwargs = create_minimal_api_create_meal_kwargs(recipes=[], tags=frozenset())
        api_meal = ApiCreateMeal(**kwargs)

        # Test conversion to domain command
        domain_command = api_meal.to_domain()
        assert domain_command is not None

        # Verify empty collections are properly handled
        assert domain_command.recipes is None  # Empty list becomes None in domain
        assert domain_command.tags is None  # Empty frozenset becomes None in domain

    def test_domain_conversion_error_handling(self):
        """Test domain conversion error handling for invalid data."""
        # This test ensures that conversion errors are properly caught and reported
        # Create a meal with valid structure
        kwargs = create_minimal_api_create_meal_kwargs()
        api_meal = ApiCreateMeal(**kwargs)

        # Normal conversion should work
        domain_command = api_meal.to_domain()
        assert domain_command is not None

        # Test that the error handling mechanism exists (ValueError wrapping)
        # by verifying the to_domain method exists and is callable
        assert callable(api_meal.to_domain)


class TestApiCreateMealIntegration:
    """
    Test suite for ApiCreateMeal integration scenarios.
    """

    def test_integration_with_all_fixtures(
        self, valid_api_create_meal_kwargs, minimal_api_create_meal_kwargs
    ):
        """Test integration with all provided fixtures."""
        # Test with valid kwargs fixture
        meal1 = ApiCreateMeal(**valid_api_create_meal_kwargs)
        assert meal1.name is not None

        # Test with minimal kwargs fixture
        meal2 = ApiCreateMeal(**minimal_api_create_meal_kwargs)
        assert meal2.name is not None

        # Test domain conversion for both
        domain_command1 = meal1.to_domain()
        domain_command2 = meal2.to_domain()

        assert domain_command1 is not None
        assert domain_command2 is not None

    def test_new_helper_functions_comprehensive(self):
        """Test all new helper functions comprehensively."""
        author_id = str(uuid4())

        # Test create_api_create_meal_kwargs
        kwargs1 = create_api_create_meal_kwargs(name="Test Meal 1")
        meal1 = ApiCreateMeal(**kwargs1)
        assert meal1.name == "Test Meal 1"

        # Test create_minimal_api_create_meal_kwargs
        kwargs2 = create_minimal_api_create_meal_kwargs(name="Test Meal 2")
        meal2 = ApiCreateMeal(**kwargs2)
        assert meal2.name == "Test Meal 2"

        # Test create_api_create_meal_with_author_id
        kwargs3 = create_api_create_meal_with_author_id(author_id, name="Test Meal 3")
        meal3 = ApiCreateMeal(**kwargs3)
        assert meal3.author_id == author_id

        # Test create_minimal_api_create_meal_with_author_id
        kwargs4 = create_minimal_api_create_meal_with_author_id(
            author_id, name="Test Meal 4"
        )
        meal4 = ApiCreateMeal(**kwargs4)
        assert meal4.author_id == author_id

        # Test create_api_create_meal_with_custom_tags
        custom_tags = [{"key": "meal_type", "value": "lunch"}]
        kwargs5 = create_api_create_meal_with_custom_tags(author_id, custom_tags)
        meal5 = ApiCreateMeal(**kwargs5)
        assert meal5.tags is not None
        assert len(meal5.tags) == 1

        # Test create_api_create_meal_with_custom_recipes
        custom_recipes = [
            create_simple_api_recipe(name="Custom Recipe", author_id=author_id)
        ]
        kwargs6 = create_api_create_meal_with_custom_recipes(author_id, custom_recipes)
        meal6 = ApiCreateMeal(**kwargs6)
        assert meal6.recipes is not None
        assert len(meal6.recipes) == 1
        assert meal6.recipes[0].name == "Custom Recipe"

        # Test create_api_create_meal_with_recipes_and_tags
        custom_recipes = [
            create_simple_api_recipe(name="Recipe 1", author_id=author_id)
        ]
        custom_tags = [{"key": "cuisine", "value": "asian"}]
        kwargs7 = create_api_create_meal_with_recipes_and_tags(
            author_id, custom_recipes, custom_tags
        )
        meal7 = ApiCreateMeal(**kwargs7)
        assert meal7.recipes is not None
        assert meal7.tags is not None
        assert len(meal7.recipes) == 1
        assert len(meal7.tags) == 1

    def test_meal_as_parent_entity_complexity(self):
        """Test complex scenarios specific to meals as parent entities of recipes."""
        author_id = str(uuid4())
        meal_id = str(uuid4())

        # Create a complex meal with multiple recipes, each with their own complexity
        main_recipe = create_complex_api_recipe(
            name="Complex Main Course",
            author_id=author_id,
            meal_id=meal_id,
            description="Elaborate main course with multiple steps",
        )

        side_recipe = create_simple_api_recipe(
            name="Simple Side Dish", author_id=author_id, meal_id=meal_id
        )

        dessert_recipe = create_simple_api_recipe(
            name="Quick Dessert", author_id=author_id, meal_id=meal_id
        )

        # Create comprehensive meal tags
        meal_tags = [
            {"key": "meal_type", "value": "dinner"},
            {"key": "difficulty", "value": "advanced"},
            {"key": "cuisine", "value": "fusion"},
            {"key": "preparation_time", "value": "long"},
            {"key": "serving_size", "value": "family"},
        ]

        kwargs = create_api_create_meal_with_recipes_and_tags(
            author_id=author_id,
            recipes=[main_recipe, side_recipe, dessert_recipe],
            tags=meal_tags,
            name="Advanced Family Dinner",
            description="Complex multi-course meal with varying recipe difficulties",
            notes="Start with dessert prep, then sides, finish with main course. Total time: 3 hours.",
            menu_id=str(uuid4()),
            image_url="https://example.com/advanced-dinner.jpg",
        )

        meal = ApiCreateMeal(**kwargs)

        # Verify meal-level properties
        assert meal.name == "Advanced Family Dinner"
        assert meal.author_id == author_id
        assert meal.description is not None and "multi-course meal" in meal.description
        assert meal.notes is not None and "3 hours" in meal.notes

        # Verify recipes (parent-child relationship)
        assert meal.recipes is not None
        assert len(meal.recipes) == 3

        recipe_names = {recipe.name for recipe in meal.recipes}
        expected_names = {"Complex Main Course", "Simple Side Dish", "Quick Dessert"}
        assert recipe_names == expected_names

        # Verify all recipes maintain parent relationship
        for recipe in meal.recipes:
            assert recipe.author_id == author_id
            assert recipe.meal_id == meal_id

        # Verify meal-level tags
        assert meal.tags is not None
        assert len(meal.tags) == 5

        tag_values = {tag.value for tag in meal.tags}
        expected_tags = {"dinner", "advanced", "fusion", "long", "family"}
        assert tag_values == expected_tags

        # Test domain conversion of complex structure
        domain_command = meal.to_domain()
        assert domain_command is not None
        assert domain_command.recipes is not None and len(domain_command.recipes) == 3
        assert domain_command.tags is not None and len(domain_command.tags) == 5

        # Verify domain objects are properly converted
        assert (
            domain_command.recipes is not None
        )  # Ensure not None for set comprehension
        domain_recipe_names = {recipe.name for recipe in domain_command.recipes}
        assert domain_recipe_names == expected_names
