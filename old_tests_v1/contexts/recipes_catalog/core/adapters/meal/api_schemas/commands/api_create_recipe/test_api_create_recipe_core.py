"""
ApiCreateRecipe Core Functionality Test Suite

Test classes for core ApiCreateRecipe functionality including basic conversions,
recipe creation, and domain conversion.

Following the same pattern as test_api_meal_core.py but adapted for ApiCreateRecipe.
"""

from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_recipe import (
    ApiCreateRecipe,
)
from src.contexts.shared_kernel.domain.enums import MeasureUnit, Privacy

# Import the helper functions from conftest
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.conftest import (
    create_api_create_recipe_kwargs,
    create_api_create_recipe_with_author_id,
    create_api_create_recipe_with_custom_tags,
    create_api_create_recipe_with_ingredients_and_tags,
    create_minimal_api_create_recipe_kwargs,
    create_minimal_api_create_recipe_with_author_id,
)


class TestApiCreateRecipeBasics:
    """
    Test suite for basic ApiCreateRecipe functionality (>95% coverage target).
    """

    def test_valid_recipe_creation(self, valid_api_create_recipe_kwargs):
        """Test creation of valid ApiCreateRecipe instances."""
        recipe = ApiCreateRecipe(**valid_api_create_recipe_kwargs)
        assert recipe.name is not None
        assert recipe.instructions is not None
        assert recipe.author_id is not None
        assert recipe.meal_id is not None
        assert recipe.ingredients is not None
        assert recipe.tags is not None

    def test_minimal_recipe_creation(self, minimal_api_create_recipe_kwargs):
        """Test creation with minimal required fields."""
        recipe = ApiCreateRecipe(**minimal_api_create_recipe_kwargs)
        assert recipe.name is not None
        assert recipe.instructions is not None
        assert recipe.author_id is not None
        assert recipe.meal_id is not None
        assert recipe.ingredients is not None
        assert recipe.tags is not None
        # Optional fields should be None or have default values
        assert recipe.description is None
        assert recipe.utensils is None
        assert recipe.total_time is None
        assert recipe.notes is None
        assert recipe.privacy == Privacy.PRIVATE  # Default value
        assert recipe.nutri_facts is None
        assert recipe.weight_in_grams is None
        assert recipe.image_url is None

    def test_author_id_constraint_consistency(self):
        """Test that author_id constraint is properly maintained between recipe and tags."""
        # Create a specific author_id
        author_id = "550e8400-e29b-41d4-a716-446655440000"

        # Create recipe with custom tags using the helper function
        custom_tags = [
            {"key": "cuisine", "value": "italian"},
            {"key": "difficulty", "value": "easy"},
            {"key": "meal-type", "value": "dinner"},
        ]

        kwargs = create_api_create_recipe_with_custom_tags(
            author_id=author_id, tags=custom_tags
        )

        recipe = ApiCreateRecipe(**kwargs)

        # Verify that the recipe has the correct author_id
        assert recipe.author_id == author_id

        # Verify that all tags have the same author_id
        assert recipe.tags is not None
        assert len(recipe.tags) == 3
        for tag in recipe.tags:
            assert tag.author_id == author_id

    def test_ingredients_and_tags_custom_creation(self):
        """Test creating recipe with custom ingredients and tags."""
        # Create a specific author_id
        author_id = "550e8400-e29b-41d4-a716-446655440000"

        # Define custom ingredients
        custom_ingredients = [
            {
                "name": "Pasta",
                "quantity": 500.0,
                "unit": MeasureUnit.GRAM,
                "position": 0,
            },
            {
                "name": "Tomato Sauce",
                "quantity": 400.0,
                "unit": MeasureUnit.MILLILITER,
                "position": 1,
            },
            {
                "name": "Parmesan Cheese",
                "quantity": 100.0,
                "unit": MeasureUnit.GRAM,
                "position": 2,
            },
        ]

        # Define custom tags
        custom_tags = [
            {"key": "cuisine", "value": "italian"},
            {"key": "difficulty", "value": "easy"},
            {"key": "meal-type", "value": "dinner"},
        ]

        kwargs = create_api_create_recipe_with_ingredients_and_tags(
            author_id=author_id,
            ingredients=custom_ingredients,
            tags=custom_tags,
            name="Pasta with Tomato Sauce",
            instructions="1. Cook pasta. 2. Heat sauce. 3. Mix and serve.",
            total_time=20,
        )

        recipe = ApiCreateRecipe(**kwargs)

        # Verify recipe properties
        assert recipe.author_id == author_id
        assert recipe.name == "Pasta with Tomato Sauce"
        assert recipe.total_time == 20

        # Verify ingredients
        assert recipe.ingredients is not None
        assert len(recipe.ingredients) == 3
        ingredient_names = {ing.name for ing in recipe.ingredients}
        assert ingredient_names == {"Pasta", "Tomato Sauce", "Parmesan Cheese"}

        # Verify tags
        assert recipe.tags is not None
        assert len(recipe.tags) == 3
        for tag in recipe.tags:
            assert tag.author_id == author_id

        tag_values = {tag.value for tag in recipe.tags}
        assert tag_values == {"italian", "easy", "dinner"}


class TestApiCreateRecipeDomainConversion:
    """
    Test suite for ApiCreateRecipe domain conversion functionality.
    """

    def test_domain_conversion_simple_recipe(self):
        """Test domain conversion with simple recipe."""
        kwargs = create_minimal_api_create_recipe_kwargs()
        api_recipe = ApiCreateRecipe(**kwargs)

        # Test conversion to domain command
        domain_command = api_recipe.to_domain()
        assert domain_command is not None
        assert hasattr(domain_command, "name")
        assert hasattr(domain_command, "instructions")
        assert hasattr(domain_command, "author_id")

    def test_domain_conversion_complex_recipe(self):
        """Test domain conversion with complex recipe."""
        kwargs = create_api_create_recipe_kwargs()
        api_recipe = ApiCreateRecipe(**kwargs)

        # Test conversion to domain command
        domain_command = api_recipe.to_domain()
        assert domain_command is not None
        assert hasattr(domain_command, "name")
        assert hasattr(domain_command, "instructions")
        assert hasattr(domain_command, "author_id")

    def test_domain_conversion_with_all_fields(self):
        """Test domain conversion with all fields populated."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_tag,
        )
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objects.data_factories.api_ingredient_data_factories import (
            create_api_ingredient,
        )

        author_id = str(uuid4())
        kwargs = create_api_create_recipe_kwargs(
            name="Complete Recipe",
            instructions="Detailed instructions",
            author_id=author_id,
            description="Complete description",
            utensils="All utensils",
            total_time=60,
            notes="Complete notes",
            privacy=Privacy.PUBLIC,
            weight_in_grams=500,
            image_url="https://example.com/image.jpg",
            ingredients=frozenset(
                [
                    create_api_ingredient(
                        name="Ingredient 1",
                        quantity=1.0,
                        unit=MeasureUnit.GRAM,
                        position=0,
                    ),
                    create_api_ingredient(
                        name="Ingredient 2",
                        quantity=2.0,
                        unit=MeasureUnit.CUP,
                        position=1,
                    ),
                ]
            ),
            tags=frozenset(
                [
                    create_api_recipe_tag(
                        key="cuisine", value="test", author_id=author_id
                    ),
                    create_api_recipe_tag(
                        key="difficulty", value="easy", author_id=author_id
                    ),
                ]
            ),
        )

        api_recipe = ApiCreateRecipe(**kwargs)

        # Test conversion to domain command
        domain_command = api_recipe.to_domain()
        assert domain_command is not None
        assert hasattr(domain_command, "name")
        assert hasattr(domain_command, "instructions")
        assert hasattr(domain_command, "author_id")

        # Verify field mapping
        assert domain_command.name == api_recipe.name
        assert domain_command.instructions == api_recipe.instructions
        assert domain_command.author_id == api_recipe.author_id


class TestApiCreateRecipeIntegration:
    """
    Test suite for ApiCreateRecipe integration scenarios.
    """

    def test_integration_with_all_fixtures(
        self, valid_api_create_recipe_kwargs, minimal_api_create_recipe_kwargs
    ):
        """Test integration with all provided fixtures."""
        # Test with valid kwargs fixture
        recipe1 = ApiCreateRecipe(**valid_api_create_recipe_kwargs)
        assert recipe1.name is not None

        # Test with minimal kwargs fixture
        recipe2 = ApiCreateRecipe(**minimal_api_create_recipe_kwargs)
        assert recipe2.name is not None

        # Test domain conversion for both
        domain_command1 = recipe1.to_domain()
        domain_command2 = recipe2.to_domain()

        assert domain_command1 is not None
        assert domain_command2 is not None

    def test_new_helper_functions_comprehensive(self):
        """Test all new helper functions comprehensively."""
        author_id = str(uuid4())

        # Test create_api_create_recipe_kwargs
        kwargs1 = create_api_create_recipe_kwargs(name="Test Recipe 1")
        recipe1 = ApiCreateRecipe(**kwargs1)
        assert recipe1.name == "Test Recipe 1"

        # Test create_minimal_api_create_recipe_kwargs
        kwargs2 = create_minimal_api_create_recipe_kwargs(name="Test Recipe 2")
        recipe2 = ApiCreateRecipe(**kwargs2)
        assert recipe2.name == "Test Recipe 2"

        # Test create_api_create_recipe_with_author_id
        kwargs3 = create_api_create_recipe_with_author_id(
            author_id, name="Test Recipe 3"
        )
        recipe3 = ApiCreateRecipe(**kwargs3)
        assert recipe3.author_id == author_id

        # Test create_minimal_api_create_recipe_with_author_id
        kwargs4 = create_minimal_api_create_recipe_with_author_id(
            author_id, name="Test Recipe 4"
        )
        recipe4 = ApiCreateRecipe(**kwargs4)
        assert recipe4.author_id == author_id

        # Test create_api_create_recipe_with_custom_tags
        custom_tags = [{"key": "test", "value": "value"}]
        kwargs6 = create_api_create_recipe_with_custom_tags(author_id, custom_tags)
        recipe6 = ApiCreateRecipe(**kwargs6)
        assert recipe6.tags is not None
        assert len(recipe6.tags) == 1

        # Test create_api_create_recipe_with_ingredients_and_tags
        custom_ingredients = [
            {
                "name": "Test Ingredient",
                "quantity": 1.0,
                "unit": MeasureUnit.GRAM,
                "position": 0,
            }
        ]
        custom_tags = [{"key": "test", "value": "value"}]
        kwargs7 = create_api_create_recipe_with_ingredients_and_tags(
            author_id, custom_ingredients, custom_tags
        )
        recipe7 = ApiCreateRecipe(**kwargs7)
        assert recipe7.ingredients is not None
        assert recipe7.tags is not None
        assert len(recipe7.ingredients) == 1
        assert len(recipe7.tags) == 1
