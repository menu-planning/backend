"""
ApiCreateMeal Edge Cases Test Suite

Test classes for ApiCreateMeal edge cases including boundary values,
complex scenarios, error handling, and comprehensive validation.

Following the same pattern as test_api_create_recipe_edge_cases.py but adapted for ApiCreateMeal.
ApiCreateMeal is more complex since meals are parent entities of recipes.
"""

import itertools
from uuid import uuid4

import pytest

# Import the helper functions from conftest
from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.conftest import (
    create_api_create_meal_kwargs,
    create_api_meal_tag,
    create_filtered_api_create_meal_kwargs,
    create_invalid_api_create_meal_kwargs,
    create_minimal_api_create_meal_kwargs,
)

# Import recipe factory for creating test recipes
from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    create_complex_api_recipe,
    create_simple_api_recipe,
)

# Import data factories
from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.data_factories.api_meal_data_factories import (
    REALISTIC_MEAL_SCENARIOS,
    create_api_meal_with_missing_required_fields,
    create_boundary_value_test_cases,
    create_comprehensive_validation_error_scenarios,
    create_field_validation_test_suite,
    create_nested_object_validation_test_cases,
    create_systematic_error_scenarios,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_meal import (
    ApiCreateMeal,
)


# Helper function to flatten boundary test cases for parametrization
def _generate_boundary_test_cases():
    """Generate flattened boundary test cases for parametrization."""
    boundary_data = create_boundary_value_test_cases()
    test_cases = []

    for category, test_case_list in boundary_data.items():
        if "string_lengths" in category:
            for i, test_case in enumerate(test_case_list):
                test_cases.append((f"{category}_{i}", test_case))

    return test_cases


# Helper function to flatten field validation test cases for parametrization
def _generate_field_validation_test_cases():
    """Generate flattened field validation test cases for parametrization."""
    validation_tests = create_field_validation_test_suite()
    test_cases = []

    for category, test_case_list in validation_tests.items():
        for i, invalid_data in enumerate(test_case_list):
            test_cases.append((f"{category}_{i}", invalid_data))

    return test_cases


# Helper function to flatten missing required fields test cases for parametrization
def _generate_missing_fields_test_cases():
    """Generate flattened missing required fields test cases for parametrization."""
    missing_fields_scenarios = create_api_meal_with_missing_required_fields()
    test_cases = []

    for i, scenario in enumerate(missing_fields_scenarios):
        test_cases.append((f"missing_fields_{i}", scenario))

    return test_cases


# Helper function to flatten nested object validation test cases for parametrization
def _generate_nested_object_test_cases():
    """Generate flattened nested object validation test cases for parametrization."""
    nested_validation_tests = create_nested_object_validation_test_cases()
    test_cases = []

    for category, test_case_list in nested_validation_tests.items():
        for i, invalid_data in enumerate(test_case_list):
            test_cases.append((f"{category}_{i}", invalid_data))

    return test_cases


# Helper function to flatten comprehensive validation scenarios for parametrization
def _generate_comprehensive_validation_test_cases():
    """Generate flattened comprehensive validation scenarios for parametrization."""
    validation_scenarios = create_comprehensive_validation_error_scenarios()
    test_cases = []

    for category, scenarios in validation_scenarios.items():
        for i, scenario in enumerate(scenarios):
            if "data" in scenario:
                test_cases.append((f"{category}_{i}", scenario))

    return test_cases


# Helper function to flatten systematic error scenarios for parametrization
def _generate_systematic_error_test_cases():
    """Generate flattened systematic error scenarios for parametrization."""
    error_scenarios = create_systematic_error_scenarios()
    test_cases = []

    for error_type, error_categories in error_scenarios.items():
        for category, error_data in error_categories.items():
            if "scenarios" in error_data:
                for i, scenario in enumerate(error_data["scenarios"]):
                    test_cases.append((f"{error_type}_{category}_{i}", scenario))

    return test_cases


class TestApiCreateMealBoundaryValues:
    """Test suite for boundary value scenarios."""

    @pytest.mark.parametrize(
        "test_case_name,test_case_data", _generate_boundary_test_cases()
    )
    def test_boundary_values_using_data_factories(self, test_case_name, test_case_data):
        """Test boundary values using data factories."""
        # Use the filtered boundary data with helper function
        kwargs = create_filtered_api_create_meal_kwargs(test_case_data)

        meal = ApiCreateMeal(**kwargs)
        # Verify the meal was created successfully
        assert meal.name is not None
        assert meal.author_id is not None

    @pytest.mark.parametrize(
        "scenario",
        [
            # Maximum length strings - updated to match actual validation constraints
            {
                "field": "name",
                "value": "A" * 255,
                "should_pass": True,
            },  # name has max_length=255
            {
                "field": "name",
                "value": "A" * 256,
                "should_pass": False,
            },  # over the limit
            {
                "field": "description",
                "value": "B" * 1000,
                "should_pass": True,
            },  # description limit is 1000
            {
                "field": "description",
                "value": "B" * 1001,
                "should_pass": False,
            },  # over the limit
            {
                "field": "notes",
                "value": "D" * 1000,
                "should_pass": True,
            },  # notes limit is 1000
            {
                "field": "notes",
                "value": "D" * 1001,
                "should_pass": False,
            },  # over the limit
            # Minimum length strings
            {
                "field": "name",
                "value": "A",
                "should_pass": True,
            },  # Single character name
            {
                "field": "name",
                "value": "",
                "should_pass": False,
            },  # Empty name should fail
        ],
    )
    def test_boundary_value_scenarios(self, scenario):
        """Test boundary value scenarios."""
        field_name = scenario["field"]
        value = scenario["value"]
        should_pass = scenario["should_pass"]

        kwargs = create_api_create_meal_kwargs(**{field_name: value})

        if should_pass:
            meal = ApiCreateMeal(**kwargs)
            assert meal is not None
        else:
            with pytest.raises(ValueError):
                ApiCreateMeal(**kwargs)

    def test_edge_cases_and_corner_cases(self):
        """Test various edge cases and corner cases."""
        # Test with minimum possible values
        kwargs = create_minimal_api_create_meal_kwargs(
            name="M",  # Single character
        )

        meal = ApiCreateMeal(**kwargs)
        assert meal.name == "M"
        assert meal.recipes == []
        assert meal.tags == frozenset()

        # Test with Unicode characters
        kwargs = create_minimal_api_create_meal_kwargs(
            name="Café Meal 🍽️",
            description="Delicious naïve meal",
            notes="Notes with émojis 🔥",
        )

        meal = ApiCreateMeal(**kwargs)
        assert "Café" in meal.name
        assert meal.description is not None and "naïve" in meal.description
        assert meal.notes is not None and "émojis" in meal.notes

        # Test with maximum reasonable values for optional fields
        author_id = str(uuid4())
        kwargs = create_minimal_api_create_meal_kwargs(
            name="A" * 255,  # Maximum length name
            description="B" * 1000,  # Maximum length description
            notes="C" * 1000,  # Maximum length notes
            author_id=author_id,
        )

        meal = ApiCreateMeal(**kwargs)
        assert len(meal.name) == 255
        assert meal.description is not None and len(meal.description) == 1000
        assert meal.notes is not None and len(meal.notes) == 1000


class TestApiCreateMealErrorHandling:
    """Test suite for error handling scenarios."""

    @pytest.mark.parametrize(
        "test_case_name,invalid_data", _generate_field_validation_test_cases()
    )
    def test_error_handling_with_field_validation_suite(
        self, test_case_name, invalid_data
    ):
        """Test error handling using field validation test suite from factories."""

        kwargs = create_filtered_api_create_meal_kwargs(invalid_data)
        with pytest.raises(ValueError):
            ApiCreateMeal(**kwargs)

    @pytest.mark.parametrize(
        "test_case_name,scenario", _generate_missing_fields_test_cases()
    )
    def test_error_handling_with_missing_required_fields(
        self, test_case_name, scenario
    ):
        """Test error handling with missing required fields."""

        kwargs = create_filtered_api_create_meal_kwargs(scenario)
        with pytest.raises(ValueError):
            ApiCreateMeal(**kwargs)

    @pytest.mark.parametrize(
        "test_case_name,invalid_data", _generate_nested_object_test_cases()
    )
    def test_error_handling_with_nested_objects(self, test_case_name, invalid_data):
        """Test error handling with invalid nested objects."""

        kwargs = create_filtered_api_create_meal_kwargs(invalid_data)
        with pytest.raises(ValueError):
            ApiCreateMeal(**kwargs)

    @pytest.mark.parametrize(
        "scenario",
        [
            # Invalid name scenarios
            {"field": "name", "value": "", "error_contains": "name"},
            {"field": "name", "value": None, "error_contains": "name"},
            {"field": "name", "value": "   ", "error_contains": "name"},
            {"field": "name", "value": "A" * 256, "error_contains": "name"},  # Too long
            # Invalid UUID scenarios
            {
                "field": "author_id",
                "value": "invalid-uuid",
                "error_contains": "author_id",
            },
            {"field": "author_id", "value": "", "error_contains": "author_id"},
            {"field": "author_id", "value": None, "error_contains": "author_id"},
            {"field": "menu_id", "value": "invalid-uuid", "error_contains": "menu_id"},
            {"field": "menu_id", "value": "", "error_contains": "menu_id"},
            # Invalid URL scenarios
            {"field": "image_url", "value": "not-a-url", "error_contains": "image_url"},
            {
                "field": "image_url",
                "value": "ftp://invalid",
                "error_contains": "image_url",
            },
            # Invalid type scenarios
            {"field": "name", "value": 123, "error_contains": "name"},
            {"field": "recipes", "value": "not-a-list", "error_contains": "recipes"},
            {"field": "tags", "value": "not-a-frozenset", "error_contains": "tags"},
        ],
    )
    def test_invalid_field_scenarios(self, scenario):
        """Test invalid field scenarios."""
        field_name = scenario["field"]
        invalid_value = scenario["value"]

        kwargs = create_invalid_api_create_meal_kwargs(field_name, invalid_value)

        with pytest.raises(ValueError):
            ApiCreateMeal(**kwargs)


class TestApiCreateMealComplexScenarios:
    """Test suite for complex validation scenarios."""

    @pytest.mark.parametrize(
        "test_case_name,scenario", _generate_comprehensive_validation_test_cases()
    )
    def test_comprehensive_validation_scenarios(self, test_case_name, scenario):
        """Test comprehensive validation scenarios using data factories."""
        if "data" in scenario:
            kwargs = create_filtered_api_create_meal_kwargs(scenario["data"])
            with pytest.raises(ValueError):
                ApiCreateMeal(**kwargs)

    @pytest.mark.parametrize(
        "test_case_name,scenario", _generate_systematic_error_test_cases()
    )
    def test_systematic_error_scenarios(self, test_case_name, scenario):
        """Test systematic error scenarios using data factories."""
        if isinstance(scenario, dict):
            kwargs = create_filtered_api_create_meal_kwargs(scenario)
            with pytest.raises(ValueError):
                ApiCreateMeal(**kwargs)

    def test_complex_recipes_scenarios(self):
        """Test complex recipes scenarios."""
        author_id = str(uuid4())
        meal_id = str(uuid4())

        # Create scenario with empty recipes
        kwargs = create_api_create_meal_kwargs(author_id=author_id, recipes=[])

        meal = ApiCreateMeal(**kwargs)
        assert meal is not None
        assert meal.recipes == []

        # Create scenario with single recipe
        single_recipe = [
            create_simple_api_recipe(
                name="Simple Recipe", author_id=author_id, meal_id=meal_id
            )
        ]
        kwargs = create_api_create_meal_kwargs(
            author_id=author_id, recipes=single_recipe
        )

        meal = ApiCreateMeal(**kwargs)
        assert meal is not None
        assert meal.recipes is not None
        assert len(meal.recipes) == 1

        # Create scenario with multiple recipes
        multiple_recipes = [
            create_simple_api_recipe(
                name="Recipe 1", author_id=author_id, meal_id=meal_id
            ),
            create_complex_api_recipe(
                name="Recipe 2", author_id=author_id, meal_id=meal_id
            ),
        ]
        kwargs = create_api_create_meal_kwargs(
            author_id=author_id, recipes=multiple_recipes
        )

        meal = ApiCreateMeal(**kwargs)
        assert meal is not None
        assert meal.recipes is not None
        assert len(meal.recipes) == 2

    def test_complex_tags_scenarios(self):
        """Test complex tags scenarios."""
        author_id = str(uuid4())

        # Create scenario with empty tags
        kwargs = create_api_create_meal_kwargs(author_id=author_id, tags=frozenset())

        meal = ApiCreateMeal(**kwargs)
        assert meal is not None
        assert meal.tags == frozenset()

        # Create scenario with single tag
        single_tag = frozenset(
            [create_api_meal_tag(key="meal_type", value="dinner", author_id=author_id)]
        )
        kwargs = create_api_create_meal_kwargs(author_id=author_id, tags=single_tag)

        meal = ApiCreateMeal(**kwargs)
        assert meal is not None
        assert meal.tags is not None
        assert len(meal.tags) == 1

        # Create scenario with multiple tags
        multiple_tags = frozenset(
            [
                create_api_meal_tag(
                    key="meal_type", value="dinner", author_id=author_id
                ),
                create_api_meal_tag(
                    key="difficulty", value="easy", author_id=author_id
                ),
                create_api_meal_tag(
                    key="cuisine", value="italian", author_id=author_id
                ),
            ]
        )
        kwargs = create_api_create_meal_kwargs(author_id=author_id, tags=multiple_tags)

        meal = ApiCreateMeal(**kwargs)
        assert meal is not None
        assert meal.tags is not None
        assert len(meal.tags) == 3

    @pytest.mark.parametrize(
        "name,author_id,menu_id",
        [
            (name, author_id, menu_id)
            for name, author_id, menu_id in itertools.product(
                ["Test Meal", "M", "Very Long Meal Name With Many Words"],
                ["550e8400-e29b-41d4-a716-446655440000"],
                ["550e8400-e29b-41d4-a716-446655440001", None],
            )
        ],
    )
    def test_comprehensive_field_validation_matrix(self, name, author_id, menu_id):
        """Test comprehensive field validation matrix covering all combinations."""
        kwargs = create_api_create_meal_kwargs(
            name=name,
            author_id=author_id,
            menu_id=(
                menu_id if menu_id is not None else str(uuid4())
            ),  # Ensure menu_id is never None for ApiCreateMeal
        )

        meal = ApiCreateMeal(**kwargs)
        assert meal.name == name
        assert meal.author_id == author_id
        assert meal.menu_id is not None  # menu_id is required for ApiCreateMeal


class TestApiCreateMealRealisticScenarios:
    """Test suite for realistic meal scenarios."""

    @pytest.mark.parametrize(
        "scenario_data", REALISTIC_MEAL_SCENARIOS[:10]
    )  # Test first 10 scenarios
    def test_realistic_scenarios_from_factory(self, scenario_data):
        """Test realistic meal scenarios from data factories."""
        # Create a copy of scenario_data to avoid mutating the shared global data
        scenario_copy = scenario_data.copy()

        # Use the filtered realistic scenario data with helper function
        author_id = str(uuid4())
        meal_id = str(uuid4())

        # Handle tags if present
        tags = []
        if scenario_copy.get("tags"):
            for tag_data in scenario_copy["tags"]:
                if (
                    isinstance(tag_data, dict)
                    and "key" in tag_data
                    and "value" in tag_data
                ):
                    tag = create_api_meal_tag(
                        key=tag_data["key"],
                        value=tag_data["value"],
                        author_id=author_id,
                    )
                    tags.append(tag)
                elif isinstance(tag_data, str) and ":" in tag_data:
                    key, value = tag_data.split(":", 1)
                    tag = create_api_meal_tag(key=key, value=value, author_id=author_id)
                    tags.append(tag)
        scenario_copy["tags"] = frozenset(tags)

        # Handle recipes if present
        recipes = []
        if scenario_copy.get("recipes"):
            # If recipes is a number, create that many simple recipes
            if isinstance(scenario_copy["recipes"], int):
                recipe_count = scenario_copy["recipes"]
                for i in range(recipe_count):
                    recipe = create_simple_api_recipe(
                        name=f"Recipe {i+1}", author_id=author_id, meal_id=meal_id
                    )
                    recipes.append(recipe)
            else:
                # If recipes is a list, process each recipe
                for recipe_data in scenario_copy["recipes"]:
                    if isinstance(recipe_data, dict):
                        recipe = create_simple_api_recipe(
                            author_id=author_id, meal_id=meal_id, **recipe_data
                        )
                        recipes.append(recipe)
        scenario_copy["recipes"] = recipes

        # Set consistent IDs
        scenario_copy["author_id"] = author_id
        scenario_copy["menu_id"] = str(uuid4())  # Ensure menu_id is always present

        kwargs = create_filtered_api_create_meal_kwargs(scenario_copy)
        meal = ApiCreateMeal(**kwargs)

        # Verify the meal was created successfully
        assert meal.name is not None
        assert meal.author_id is not None
        assert meal.menu_id is not None

        # Test domain conversion
        domain_command = meal.to_domain()
        assert domain_command is not None

    def test_realistic_meal_with_complex_recipes(self):
        """Test realistic meal scenarios with complex nested recipes."""
        author_id = str(uuid4())
        meal_id = str(uuid4())

        # Create complex recipes with full features
        complex_recipes = [
            create_complex_api_recipe(
                name="Main Course Recipe",
                author_id=author_id,
                meal_id=meal_id,
                description="Complex main course with multiple ingredients",
            ),
            create_simple_api_recipe(
                name="Side Dish Recipe",
                author_id=author_id,
                meal_id=meal_id,
                description="Simple side dish",
            ),
        ]

        # Create meal with complex recipes
        kwargs = create_api_create_meal_kwargs(
            name="Family Dinner",
            author_id=author_id,
            description="Complete family dinner with multiple courses",
            recipes=complex_recipes,
            tags=frozenset(
                [
                    create_api_meal_tag(
                        key="meal_type", value="dinner", author_id=author_id
                    ),
                    create_api_meal_tag(
                        key="occasion", value="family", author_id=author_id
                    ),
                ]
            ),
        )

        meal = ApiCreateMeal(**kwargs)
        assert meal is not None
        assert meal.recipes is not None and len(meal.recipes) == 2
        assert meal.tags is not None and len(meal.tags) == 2

        # Test domain conversion
        domain_command = meal.to_domain()
        assert domain_command is not None
        assert domain_command.recipes is not None and len(domain_command.recipes) == 2


class TestApiCreateMealPerformance:
    """Test suite for performance scenarios with complex data."""

    def test_performance_with_large_datasets(self):
        """Test performance with large recipe and tag datasets."""
        author_id = str(uuid4())
        meal_id = str(uuid4())

        # Create large datasets
        large_recipes = [
            create_simple_api_recipe(
                name=f"Recipe {i}", author_id=author_id, meal_id=meal_id
            )
            for i in range(20)  # 20 recipes per meal
        ]

        large_tags = frozenset(
            [
                create_api_meal_tag(
                    key=f"tag{i}", value=f"value{i}", author_id=author_id
                )
                for i in range(20)  # 20 tags per meal
            ]
        )

        kwargs = create_api_create_meal_kwargs(
            author_id=author_id, recipes=large_recipes, tags=large_tags
        )

        # This should still work efficiently
        meal = ApiCreateMeal(**kwargs)
        assert meal.recipes is not None
        assert meal.tags is not None
        assert len(meal.recipes) == 20
        assert len(meal.tags) == 20

        # Test domain conversion with large datasets
        domain_command = meal.to_domain()
        assert domain_command is not None
        assert domain_command.recipes is not None and len(domain_command.recipes) == 20

    @pytest.mark.parametrize("meal_index", range(100))
    def test_performance_with_minimal_data(self, meal_index):
        """Test performance with minimal data to ensure efficiency."""
        kwargs = create_minimal_api_create_meal_kwargs(
            name=f"Minimal Meal {meal_index}", author_id=str(uuid4())
        )

        meal = ApiCreateMeal(**kwargs)

        # Verify the meal was created successfully
        assert meal.name == f"Minimal Meal {meal_index}"
        assert meal.author_id is not None

        # Test domain conversion
        domain_command = meal.to_domain()
        assert domain_command is not None


class TestApiCreateMealComplexRelationships:
    """Test suite for complex relationship scenarios between meals, recipes, and tags."""

    def test_author_id_consistency_validation(self):
        """Test that author_id is consistent across meal, recipes, and tags."""
        author_id = str(uuid4())
        meal_id = str(uuid4())

        # Create recipes and tags with consistent author_id
        recipes = [
            create_simple_api_recipe(
                name="Recipe 1", author_id=author_id, meal_id=meal_id
            ),
            create_simple_api_recipe(
                name="Recipe 2", author_id=author_id, meal_id=meal_id
            ),
        ]

        tags = frozenset(
            [
                create_api_meal_tag(key="type", value="dinner", author_id=author_id),
                create_api_meal_tag(
                    key="cuisine", value="italian", author_id=author_id
                ),
            ]
        )

        kwargs = create_api_create_meal_kwargs(
            author_id=author_id, recipes=recipes, tags=tags
        )

        meal = ApiCreateMeal(**kwargs)
        assert meal.author_id == author_id

        # Verify all recipes have correct author_id
        if meal.recipes:
            for recipe in meal.recipes:
                assert recipe.author_id == author_id

        # Verify all tags have correct author_id
        if meal.tags:
            for tag in meal.tags:
                assert tag.author_id == author_id

    def test_meal_recipe_relationship_validation(self):
        """Test that meal-recipe relationships are properly validated."""
        author_id = str(uuid4())
        meal_id = str(uuid4())

        # This should work - recipes with correct meal_id
        correct_recipes = [
            create_simple_api_recipe(
                name="Recipe 1", author_id=author_id, meal_id=meal_id
            )
        ]

        # Note: For ApiCreateMeal, we don't need to set meal.id since it's a creation command
        # The validation happens at the ApiMeal level, not ApiCreateMeal
        kwargs = create_api_create_meal_kwargs(
            author_id=author_id, recipes=correct_recipes
        )

        meal = ApiCreateMeal(**kwargs)
        assert meal is not None
        assert meal.recipes is not None and len(meal.recipes) == 1

    def test_empty_relationships(self):
        """Test handling of empty relationships."""
        # Test with no recipes and no tags
        kwargs = create_minimal_api_create_meal_kwargs(
            name="Empty Meal", recipes=[], tags=frozenset()
        )

        meal = ApiCreateMeal(**kwargs)
        assert meal.recipes == []
        assert meal.tags == frozenset()

        # Test domain conversion with empty relationships
        domain_command = meal.to_domain()
        assert domain_command is not None
        assert domain_command.recipes is None or domain_command.recipes == []
        assert domain_command.tags is None or domain_command.tags == frozenset()
