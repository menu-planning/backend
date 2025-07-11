"""
Test suite for ApiUpdateMeal.from_api_meal() factory method.
Tests the conversion of ApiMeal instances to ApiUpdateMeal instances.
"""

import pytest
from uuid import uuid4
from typing import Dict, Any

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_update_meal import (
    ApiUpdateMeal,
    ApiAttributesToUpdateOnMeal
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag

# Import existing data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.data_factories.api_meal_data_factories import (
    create_api_meal,
    create_simple_api_meal,
    create_complex_api_meal,
    create_api_meal_without_recipes,
    create_api_meal_with_max_recipes,
    create_api_meal_kwargs,
    create_api_meal_with_incorrect_computed_properties,
    create_meal_collection,
    REALISTIC_MEAL_SCENARIOS,
    reset_api_meal_counters
)

# Rebuild models to resolve forward references
ApiAttributesToUpdateOnMeal.model_rebuild()
ApiUpdateMeal.model_rebuild()


class TestApiUpdateMealFromApiMeal:
    """Test suite for ApiUpdateMeal.from_api_meal() factory method."""

    def setup_method(self):
        """Reset counters before each test for deterministic results."""
        reset_api_meal_counters()

    def test_factory_method_exists(self):
        """Test that the from_api_meal factory method exists."""
        assert hasattr(ApiUpdateMeal, 'from_api_meal')
        assert callable(ApiUpdateMeal.from_api_meal)

    def test_factory_method_returns_api_update_meal(self):
        """Test that factory method returns ApiUpdateMeal instance."""
        api_meal = create_simple_api_meal()
        update_meal = ApiUpdateMeal.from_api_meal(api_meal)
        
        assert isinstance(update_meal, ApiUpdateMeal)
        assert isinstance(update_meal.updates, ApiAttributesToUpdateOnMeal)
        assert update_meal.meal_id == api_meal.id

    def test_simple_meal_conversion(self):
        """Test factory method with simple meal configuration."""
        # Create simple meal with basic fields
        simple_meal = create_simple_api_meal()
        
        # Convert to update meal
        update_meal = ApiUpdateMeal.from_api_meal(simple_meal)
        
        # Verify basic structure
        assert update_meal.meal_id == simple_meal.id
        assert update_meal.updates.name == simple_meal.name
        assert update_meal.updates.description == simple_meal.description
        assert update_meal.updates.notes == simple_meal.notes
        assert update_meal.updates.like == simple_meal.like
        # image_url is converted from HttpUrl to string
        if simple_meal.image_url:
            assert update_meal.updates.image_url == str(simple_meal.image_url)
        else:
            assert update_meal.updates.image_url is None
        assert update_meal.updates.menu_id == simple_meal.menu_id
        
        # Verify collections
        assert simple_meal.recipes is not None
        assert simple_meal.tags is not None
        assert update_meal.updates.recipes is not None
        assert update_meal.updates.tags is not None
        assert len(update_meal.updates.recipes) == len(simple_meal.recipes)
        assert len(update_meal.updates.tags) == len(simple_meal.tags)
        
        # Verify recipes mapping
        for i, recipe in enumerate(update_meal.updates.recipes):
            assert recipe.id == simple_meal.recipes[i].id
            assert recipe.name == simple_meal.recipes[i].name
            assert recipe.meal_id == simple_meal.recipes[i].meal_id
        
        # Verify tags mapping
        original_tags = {tag.key: tag.value for tag in simple_meal.tags}
        update_tags = {tag.key: tag.value for tag in update_meal.updates.tags}
        assert original_tags == update_tags

    def test_simple_meal_with_minimal_fields(self):
        """Test factory method with minimal meal configuration."""
        # Create meal with only required fields
        minimal_meal = create_simple_api_meal(
            description=None,
            notes=None,
            like=None,
            image_url=None,
            tags=frozenset(),
            recipes=[]
        )
        
        # Convert to update meal
        update_meal = ApiUpdateMeal.from_api_meal(minimal_meal)
        
        # Verify required fields
        assert update_meal.meal_id == minimal_meal.id
        assert update_meal.updates.name == minimal_meal.name
        assert update_meal.updates.menu_id == minimal_meal.menu_id
        
        # Verify optional fields are properly handled
        assert update_meal.updates.description is None
        assert update_meal.updates.notes is None
        assert update_meal.updates.like is None
        assert update_meal.updates.image_url is None
        
        # Verify empty collections
        assert update_meal.updates.recipes is not None
        assert update_meal.updates.tags is not None
        assert len(update_meal.updates.recipes) == 0
        assert len(update_meal.updates.tags) == 0

    def test_complex_meal_conversion(self):
        """Test factory method with complex meal configuration."""
        # Create complex meal with multiple recipes and tags
        complex_meal = create_complex_api_meal()
        
        # Convert to update meal
        update_meal = ApiUpdateMeal.from_api_meal(complex_meal)
        
        # Verify basic structure
        assert update_meal.meal_id == complex_meal.id
        assert update_meal.updates.name == complex_meal.name
        assert update_meal.updates.description == complex_meal.description
        assert update_meal.updates.notes == complex_meal.notes
        assert update_meal.updates.like == complex_meal.like
        assert update_meal.updates.menu_id == complex_meal.menu_id
        
        # Verify complex collections
        assert complex_meal.recipes is not None
        assert complex_meal.tags is not None
        assert update_meal.updates.recipes is not None
        assert update_meal.updates.tags is not None
        assert len(update_meal.updates.recipes) == len(complex_meal.recipes)
        assert len(update_meal.updates.tags) == len(complex_meal.tags)
        
        # Verify all recipes are correctly mapped
        for i, recipe in enumerate(update_meal.updates.recipes):
            original_recipe = complex_meal.recipes[i]
            assert recipe.id == original_recipe.id
            assert recipe.name == original_recipe.name
            assert recipe.meal_id == original_recipe.meal_id
            assert recipe.author_id == original_recipe.author_id
            assert recipe.description == original_recipe.description
            assert recipe.instructions == original_recipe.instructions
            assert recipe.ingredients is not None
            assert recipe.tags is not None
            assert original_recipe.ingredients is not None
            assert original_recipe.tags is not None
            assert len(recipe.ingredients) == len(original_recipe.ingredients)
            assert len(recipe.tags) == len(original_recipe.tags)
        
        # Verify all tags are correctly mapped
        original_tags = {(tag.key, tag.value, tag.author_id) for tag in complex_meal.tags}
        update_tags = {(tag.key, tag.value, tag.author_id) for tag in update_meal.updates.tags}
        assert original_tags == update_tags

    def test_meal_with_max_recipes_conversion(self):
        """Test factory method with maximum number of recipes."""
        # Create meal with maximum recipes
        max_recipes_meal = create_api_meal_with_max_recipes()
        
        # Convert to update meal
        update_meal = ApiUpdateMeal.from_api_meal(max_recipes_meal)
        
        # Verify basic structure
        assert update_meal.meal_id == max_recipes_meal.id
        assert update_meal.updates.name == max_recipes_meal.name
        
        # Verify large recipe collection handling
        assert max_recipes_meal.recipes is not None
        assert update_meal.updates.recipes is not None
        assert len(update_meal.updates.recipes) == len(max_recipes_meal.recipes)
        
        # Verify first and last recipes for performance
        if max_recipes_meal.recipes:
            first_recipe = max_recipes_meal.recipes[0]
            last_recipe = max_recipes_meal.recipes[-1]
            
            assert update_meal.updates.recipes[0].id == first_recipe.id
            assert update_meal.updates.recipes[0].name == first_recipe.name
            assert update_meal.updates.recipes[-1].id == last_recipe.id
            assert update_meal.updates.recipes[-1].name == last_recipe.name
        
        # Verify all recipes have correct meal_id
        for recipe in update_meal.updates.recipes:
            assert recipe.meal_id == max_recipes_meal.id

    def test_meal_with_incorrect_computed_properties(self):
        """Test factory method with complex nutritional data."""
        # Create meal with computed properties that may be incorrect
        meal_with_computed = create_api_meal_with_incorrect_computed_properties()
        
        # Convert to update meal
        update_meal = ApiUpdateMeal.from_api_meal(meal_with_computed)
        
        # Verify basic structure
        assert update_meal.meal_id == meal_with_computed.id
        assert update_meal.updates.name == meal_with_computed.name
        
        # Verify all fields are properly mapped regardless of computed property state
        assert update_meal.updates.description == meal_with_computed.description
        assert update_meal.updates.notes == meal_with_computed.notes
        assert update_meal.updates.like == meal_with_computed.like
        assert update_meal.updates.menu_id == meal_with_computed.menu_id
        
        # Verify collections are handled correctly
        assert meal_with_computed.recipes is not None
        assert meal_with_computed.tags is not None
        assert update_meal.updates.recipes is not None
        assert update_meal.updates.tags is not None
        assert len(update_meal.updates.recipes) == len(meal_with_computed.recipes)
        assert len(update_meal.updates.tags) == len(meal_with_computed.tags)

    def test_field_mapping_accuracy_all_fields(self):
        """Test that all ApiMeal fields correctly map to ApiUpdateMeal."""
        # Create meal with all possible field combinations
        meal_kwargs = create_api_meal_kwargs(
            name="Test Meal Field Mapping",
            description="Comprehensive field mapping test",
            notes="Testing all field mappings",
            like=True,
            image_url="https://example.com/meal-image.jpg",
            menu_id=str(uuid4()),
            recipes=[],  # Will be populated with test recipes
            tags=frozenset()  # Will be populated with test tags
        )
        
        # Create the meal
        test_meal = create_api_meal(**meal_kwargs)
        
        # Convert to update meal
        update_meal = ApiUpdateMeal.from_api_meal(test_meal)
        
        # Verify all scalar fields are correctly mapped
        assert update_meal.meal_id == test_meal.id
        assert update_meal.updates.name == test_meal.name
        assert update_meal.updates.description == test_meal.description
        assert update_meal.updates.notes == test_meal.notes
        assert update_meal.updates.like == test_meal.like
        # image_url is converted from HttpUrl to string
        assert update_meal.updates.image_url == str(test_meal.image_url) if test_meal.image_url else None
        assert update_meal.updates.menu_id == test_meal.menu_id
        
        # Verify collection fields are correctly mapped
        assert update_meal.updates.recipes == test_meal.recipes
        assert update_meal.updates.tags == test_meal.tags

    def test_field_mapping_with_various_combinations(self):
        """Test field mapping with various field combinations."""
        # Test different field combinations
        test_combinations = [
            {"name": "Meal 1", "description": "Test 1", "notes": None, "like": True},
            {"name": "Meal 2", "description": None, "notes": "Test 2", "like": False},
            {"name": "Meal 3", "description": "Test 3", "notes": "Test 3", "like": None},
            {"name": "Meal 4", "description": None, "notes": None, "like": None},
        ]
        
        for i, combination in enumerate(test_combinations):
            # Create meal with specific field combination
            test_meal = create_api_meal(**combination)
            
            # Convert to update meal
            update_meal = ApiUpdateMeal.from_api_meal(test_meal)
            
            # Verify all fields are correctly mapped
            assert update_meal.meal_id == test_meal.id
            assert update_meal.updates.name == test_meal.name
            assert update_meal.updates.description == test_meal.description
            assert update_meal.updates.notes == test_meal.notes
            assert update_meal.updates.like == test_meal.like
            assert update_meal.updates.menu_id == test_meal.menu_id
            
            # Verify collections maintain their structure
            assert test_meal.recipes is not None
            assert test_meal.tags is not None
            assert update_meal.updates.recipes is not None
            assert update_meal.updates.tags is not None
            assert len(update_meal.updates.recipes) == len(test_meal.recipes)
            assert len(update_meal.updates.tags) == len(test_meal.tags)

    def test_field_mapping_preserves_data_types(self):
        """Test that field mapping preserves all data types correctly."""
        # Create meal with diverse data types
        test_meal = create_api_meal()
        
        # Convert to update meal
        update_meal = ApiUpdateMeal.from_api_meal(test_meal)
        
        # Verify data types are preserved
        assert type(update_meal.meal_id) == type(test_meal.id)
        assert type(update_meal.updates.name) == type(test_meal.name)
        
        # Verify optional fields maintain their types (or None)
        if test_meal.description is not None:
            assert type(update_meal.updates.description) == type(test_meal.description)
        else:
            assert update_meal.updates.description is None
            
        if test_meal.notes is not None:
            assert type(update_meal.updates.notes) == type(test_meal.notes)
        else:
            assert update_meal.updates.notes is None
            
        if test_meal.like is not None:
            assert type(update_meal.updates.like) == type(test_meal.like)
        else:
            assert update_meal.updates.like is None
            
        if test_meal.image_url is not None:
            # image_url is converted from HttpUrl to string
            assert type(update_meal.updates.image_url) == str
            assert update_meal.updates.image_url == str(test_meal.image_url)
        else:
            assert update_meal.updates.image_url is None
            
        if test_meal.menu_id is not None:
            assert type(update_meal.updates.menu_id) == type(test_meal.menu_id)
        else:
            assert update_meal.updates.menu_id is None
        
        # Verify collection types are preserved
        assert type(update_meal.updates.recipes) == type(test_meal.recipes)
        assert type(update_meal.updates.tags) == type(test_meal.tags)

    def test_all_realistic_meal_scenarios(self):
        """Test all existing ApiMeal fixtures with REALISTIC_MEAL_SCENARIOS."""
        # Reset counters to ensure deterministic results
        reset_api_meal_counters()
        
        # Test each realistic meal scenario by creating meals sequentially
        # The factory function internally cycles through REALISTIC_MEAL_SCENARIOS
        for i in range(len(REALISTIC_MEAL_SCENARIOS)):
            scenario_data = REALISTIC_MEAL_SCENARIOS[i]
            
            # Create meal using factory function (it will use the scenario at index i)
            api_meal = create_api_meal()
            
            # Convert to update meal
            update_meal = ApiUpdateMeal.from_api_meal(api_meal)
            
            # Verify basic structure for each scenario
            assert update_meal.meal_id == api_meal.id, f"Failed for scenario {i}: {scenario_data.get('name', 'unknown')}"
            assert update_meal.updates.name == api_meal.name, f"Failed for scenario {i}: {scenario_data.get('name', 'unknown')}"
            assert update_meal.updates.description == api_meal.description, f"Failed for scenario {i}: {scenario_data.get('name', 'unknown')}"
            assert update_meal.updates.notes == api_meal.notes, f"Failed for scenario {i}: {scenario_data.get('name', 'unknown')}"
            assert update_meal.updates.like == api_meal.like, f"Failed for scenario {i}: {scenario_data.get('name', 'unknown')}"
            assert update_meal.updates.menu_id == api_meal.menu_id, f"Failed for scenario {i}: {scenario_data.get('name', 'unknown')}"
            
            # Verify image_url conversion (HttpUrl to string)
            if api_meal.image_url:
                assert update_meal.updates.image_url == str(api_meal.image_url), f"Failed for scenario {i}: {scenario_data.get('name', 'unknown')}"
            else:
                assert update_meal.updates.image_url is None, f"Failed for scenario {i}: {scenario_data.get('name', 'unknown')}"
            
            # Verify collections are correctly mapped
            assert api_meal.recipes is not None
            assert api_meal.tags is not None
            assert update_meal.updates.recipes is not None
            assert update_meal.updates.tags is not None
            assert len(update_meal.updates.recipes) == len(api_meal.recipes), f"Failed for scenario {i}: {scenario_data.get('name', 'unknown')}"
            assert len(update_meal.updates.tags) == len(api_meal.tags), f"Failed for scenario {i}: {scenario_data.get('name', 'unknown')}"
            
            # Verify recipes are correctly mapped
            for j, recipe in enumerate(update_meal.updates.recipes):
                original_recipe = api_meal.recipes[j]
                assert recipe.id == original_recipe.id, f"Failed for scenario {i}: {scenario_data.get('name', 'unknown')}, recipe {j}"
                assert recipe.name == original_recipe.name, f"Failed for scenario {i}: {scenario_data.get('name', 'unknown')}, recipe {j}"
                assert recipe.meal_id == original_recipe.meal_id, f"Failed for scenario {i}: {scenario_data.get('name', 'unknown')}, recipe {j}"
            
            # Verify tags are correctly mapped
            original_tags = {(tag.key, tag.value, tag.author_id) for tag in api_meal.tags}
            update_tags = {(tag.key, tag.value, tag.author_id) for tag in update_meal.updates.tags}
            assert original_tags == update_tags, f"Failed for scenario {i}: {scenario_data.get('name', 'unknown')}"

    def test_meal_collection_fixtures(self):
        """Test all existing ApiMeal fixtures with create_meal_collection()."""
        # Create collection of meals
        meal_collection = create_meal_collection(count=10)
        
        # Test each meal in the collection
        for i, api_meal in enumerate(meal_collection):
            # Convert to update meal
            update_meal = ApiUpdateMeal.from_api_meal(api_meal)
            
            # Verify basic structure
            assert update_meal.meal_id == api_meal.id, f"Failed for meal {i} in collection"
            assert update_meal.updates.name == api_meal.name, f"Failed for meal {i} in collection"
            assert update_meal.updates.menu_id == api_meal.menu_id, f"Failed for meal {i} in collection"
            
            # Verify collections are properly handled
            assert api_meal.recipes is not None
            assert api_meal.tags is not None
            assert update_meal.updates.recipes is not None
            assert update_meal.updates.tags is not None
            assert len(update_meal.updates.recipes) == len(api_meal.recipes), f"Failed for meal {i} in collection"
            assert len(update_meal.updates.tags) == len(api_meal.tags), f"Failed for meal {i} in collection"
            
            # Verify instance type
            assert isinstance(update_meal, ApiUpdateMeal), f"Failed for meal {i} in collection"
            assert isinstance(update_meal.updates, ApiAttributesToUpdateOnMeal), f"Failed for meal {i} in collection"

    def test_validate_created_api_update_meal_instances(self):
        """Validate created ApiUpdateMeal instances follow validation patterns."""
        # Test with different meal configurations
        test_meals = [
            create_simple_api_meal(),
            create_complex_api_meal(),
            create_api_meal_with_max_recipes(),
            create_api_meal_without_recipes(),
        ]
        
        for api_meal in test_meals:
            # Convert to update meal
            update_meal = ApiUpdateMeal.from_api_meal(api_meal)
            
            # Validate ApiUpdateMeal instance structure
            assert isinstance(update_meal, ApiUpdateMeal), "Must be ApiUpdateMeal instance"
            assert hasattr(update_meal, 'meal_id'), "Must have meal_id attribute"
            assert hasattr(update_meal, 'updates'), "Must have updates attribute"
            assert isinstance(update_meal.updates, ApiAttributesToUpdateOnMeal), "Updates must be ApiAttributesToUpdateOnMeal instance"
            
            # Validate meal_id is valid UUID string
            assert isinstance(update_meal.meal_id, str), "meal_id must be string"
            assert len(update_meal.meal_id) == 36, "meal_id must be valid UUID length"
            assert update_meal.meal_id.count('-') == 4, "meal_id must be valid UUID format"
            
            # Validate required fields in updates
            assert hasattr(update_meal.updates, 'name'), "Updates must have name attribute"
            assert hasattr(update_meal.updates, 'menu_id'), "Updates must have menu_id attribute"
            assert isinstance(update_meal.updates.name, str), "Name must be string"
            assert len(update_meal.updates.name.strip()) > 0, "Name must not be empty"
            
            # Validate optional fields in updates
            optional_fields = ['description', 'notes', 'like', 'image_url']
            for field in optional_fields:
                assert hasattr(update_meal.updates, field), f"Updates must have {field} attribute"
                field_value = getattr(update_meal.updates, field)
                if field_value is not None:
                    if field in ['description', 'notes', 'image_url']:
                        assert isinstance(field_value, str), f"{field} must be string when not None"
                    elif field == 'like':
                        assert isinstance(field_value, bool), f"{field} must be boolean when not None"
            
            # Validate collections in updates
            assert hasattr(update_meal.updates, 'recipes'), "Updates must have recipes attribute"
            assert hasattr(update_meal.updates, 'tags'), "Updates must have tags attribute"
            assert isinstance(update_meal.updates.recipes, list), "Recipes must be list"
            assert isinstance(update_meal.updates.tags, frozenset), "Tags must be frozenset"
            
            # Validate recipe instances in collection
            for recipe in update_meal.updates.recipes:
                assert isinstance(recipe, ApiRecipe), "Each recipe must be ApiRecipe instance"
                assert hasattr(recipe, 'id'), "Recipe must have id attribute"
                assert hasattr(recipe, 'name'), "Recipe must have name attribute"
                assert hasattr(recipe, 'meal_id'), "Recipe must have meal_id attribute"
                assert recipe.meal_id == update_meal.meal_id, "Recipe meal_id must match update meal_id"
            
            # Validate tag instances in collection
            for tag in update_meal.updates.tags:
                assert isinstance(tag, ApiTag), "Each tag must be ApiTag instance"
                assert hasattr(tag, 'key'), "Tag must have key attribute"
                assert hasattr(tag, 'value'), "Tag must have value attribute"
                assert hasattr(tag, 'author_id'), "Tag must have author_id attribute"
                assert isinstance(tag.key, str), "Tag key must be string"
                assert isinstance(tag.value, str), "Tag value must be string"
                assert isinstance(tag.author_id, str), "Tag author_id must be string"

    def test_validate_field_completeness(self):
        """Validate that all fields from ApiMeal are present in ApiUpdateMeal."""
        # Create comprehensive meal
        api_meal = create_complex_api_meal()
        update_meal = ApiUpdateMeal.from_api_meal(api_meal)
        
        # Check all expected fields are present in updates
        expected_fields = [
            'name', 'description', 'notes', 'like', 'image_url', 
            'menu_id', 'recipes', 'tags'
        ]
        
        for field in expected_fields:
            assert hasattr(update_meal.updates, field), f"Missing field: {field}"
            
        # Verify no unexpected fields exist
        actual_fields = set(update_meal.updates.model_fields.keys())
        expected_fields_set = set(expected_fields)
        
        # Allow for additional fields that might be added in the future
        # but ensure all expected fields are present
        assert expected_fields_set.issubset(actual_fields), "Missing required fields in ApiAttributesToUpdateOnMeal"

    def test_validate_conversion_completeness(self):
        """Validate that conversion preserves all data without loss."""
        # Test with various meal scenarios
        test_scenarios = [
            create_simple_api_meal(),
            create_complex_api_meal(),
            create_api_meal_with_max_recipes(),
            create_api_meal_without_recipes(),
        ]
        
        for api_meal in test_scenarios:
            update_meal = ApiUpdateMeal.from_api_meal(api_meal)
            
            # Verify no data loss in conversion
            assert update_meal.meal_id == api_meal.id, "meal_id conversion failed"
            assert update_meal.updates.name == api_meal.name, "name conversion failed"
            assert update_meal.updates.description == api_meal.description, "description conversion failed"
            assert update_meal.updates.notes == api_meal.notes, "notes conversion failed"
            assert update_meal.updates.like == api_meal.like, "like conversion failed"
            assert update_meal.updates.menu_id == api_meal.menu_id, "menu_id conversion failed"
            
            # Verify image_url conversion (HttpUrl to string)
            if api_meal.image_url is not None:
                assert update_meal.updates.image_url == str(api_meal.image_url), "image_url conversion failed"
            else:
                assert update_meal.updates.image_url is None, "image_url None conversion failed"
            
            # Verify collection size preservation
            assert api_meal.recipes is not None
            assert api_meal.tags is not None
            assert update_meal.updates.recipes is not None
            assert update_meal.updates.tags is not None
            assert len(update_meal.updates.recipes) == len(api_meal.recipes), "recipes collection size changed"
            assert len(update_meal.updates.tags) == len(api_meal.tags), "tags collection size changed"
            
            # Verify recipe data preservation
            for i, (original_recipe, update_recipe) in enumerate(zip(api_meal.recipes, update_meal.updates.recipes)):
                assert original_recipe.id == update_recipe.id, f"recipe {i} id conversion failed"
                assert original_recipe.name == update_recipe.name, f"recipe {i} name conversion failed"
                assert original_recipe.meal_id == update_recipe.meal_id, f"recipe {i} meal_id conversion failed"
            
            # Verify tag data preservation
            original_tags = {(tag.key, tag.value, tag.author_id) for tag in api_meal.tags}
            update_tags = {(tag.key, tag.value, tag.author_id) for tag in update_meal.updates.tags}
            assert original_tags == update_tags, "tags data conversion failed" 