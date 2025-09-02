"""
Test fixtures and utilities for ApiCreateRecipe and ApiCreateMeal testing.

This module provides comprehensive test fixtures leveraging the existing
data factories and creating specialized fixtures for command validation scenarios.
"""

import pytest
from uuid import uuid4
from typing import Dict, Any, List

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_recipe import ApiCreateRecipe
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_meal import ApiCreateMeal
from src.contexts.shared_kernel.domain.enums import Privacy, MeasureUnit

# Import existing data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    create_api_recipe_kwargs,
    create_simple_api_recipe,
    create_complex_api_recipe,
    create_minimal_api_recipe,
    create_api_recipe_with_max_fields,
    create_comprehensive_validation_test_cases_for_api_recipe,
    create_api_recipe_tag,  # Use existing tag creation function
    REALISTIC_RECIPE_SCENARIOS,
)

# Import meal data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.data_factories.api_meal_data_factories import (
    create_api_meal_kwargs
)

# Import nested object factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objects.data_factories.api_ingredient_data_factories import (
    create_api_ingredient,
)

# Import shared kernel factories
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
from pydantic import ValidationError


# =============================================================================
# TEST FIXTURES - RECIPE
# =============================================================================

@pytest.fixture
def valid_api_create_recipe_kwargs():
    """Create valid ApiCreateRecipe kwargs using existing data factories."""
    # Use existing factory but remove fields not needed for ApiCreateRecipe
    recipe_kwargs = create_api_recipe_kwargs()
    
    # Remove fields that don't exist in ApiCreateRecipe
    create_recipe_kwargs = {
        'name': recipe_kwargs['name'],
        'instructions': recipe_kwargs['instructions'],
        'author_id': recipe_kwargs['author_id'],
        'meal_id': recipe_kwargs['meal_id'],
        'ingredients': recipe_kwargs['ingredients'],
        'description': recipe_kwargs['description'],
        'utensils': recipe_kwargs['utensils'],
        'total_time': recipe_kwargs['total_time'],
        'notes': recipe_kwargs['notes'],
        'tags': recipe_kwargs['tags'],
        'privacy': recipe_kwargs['privacy'],
        'nutri_facts': recipe_kwargs['nutri_facts'],
        'weight_in_grams': recipe_kwargs['weight_in_grams'],
        'image_url': recipe_kwargs['image_url'],
    }
    
    return create_recipe_kwargs


@pytest.fixture
def valid_api_create_recipe(valid_api_create_recipe_kwargs):
    """Create valid ApiCreateRecipe instance."""
    return ApiCreateRecipe(**valid_api_create_recipe_kwargs)


@pytest.fixture
def minimal_api_create_recipe_kwargs():
    """Create minimal ApiCreateRecipe kwargs with only required fields."""
    author_id = str(uuid4())
    return {
        'name': 'Test Recipe',
        'instructions': 'Test instructions',
        'author_id': author_id,
        'meal_id': str(uuid4()),
        'ingredients': frozenset([
            create_api_ingredient(name='Test Ingredient', quantity=1.0, unit=MeasureUnit.GRAM, position=0)
        ]),
        'tags': frozenset([
            create_api_recipe_tag(key='test', value='value', author_id=author_id)
        ]),
    }


@pytest.fixture
def minimal_api_create_recipe(minimal_api_create_recipe_kwargs):
    """Create minimal ApiCreateRecipe instance."""
    return ApiCreateRecipe(**minimal_api_create_recipe_kwargs)


@pytest.fixture
def invalid_field_scenarios():
    """Provide test scenarios for invalid field validation."""
    return [
        # Invalid name scenarios
        {'field': 'name', 'value': '', 'error_contains': 'name'},
        {'field': 'name', 'value': None, 'error_contains': 'name'},
        {'field': 'name', 'value': '   ', 'error_contains': 'name'},
        
        # Invalid instructions scenarios
        {'field': 'instructions', 'value': '', 'error_contains': 'instructions'},
        {'field': 'instructions', 'value': None, 'error_contains': 'instructions'},
        {'field': 'instructions', 'value': '   ', 'error_contains': 'instructions'},
        
        # Invalid UUID scenarios
        {'field': 'author_id', 'value': 'invalid-uuid', 'error_contains': 'author_id'},
        {'field': 'author_id', 'value': '', 'error_contains': 'author_id'},
        {'field': 'author_id', 'value': None, 'error_contains': 'author_id'},
        {'field': 'meal_id', 'value': 'invalid-uuid', 'error_contains': 'meal_id'},
        {'field': 'meal_id', 'value': '', 'error_contains': 'meal_id'},
        {'field': 'meal_id', 'value': None, 'error_contains': 'meal_id'},
        
        # Invalid numeric scenarios
        {'field': 'total_time', 'value': -1, 'error_contains': 'total_time'},
        {'field': 'total_time', 'value': 'invalid', 'error_contains': 'total_time'},
        {'field': 'weight_in_grams', 'value': -1, 'error_contains': 'weight_in_grams'},
        {'field': 'weight_in_grams', 'value': 'invalid', 'error_contains': 'weight_in_grams'},
    ]


@pytest.fixture
def boundary_value_scenarios():
    """Provide test scenarios for boundary value testing."""
    return [
        # Maximum length strings - updated to match actual validation constraints
        {'field': 'name', 'value': 'A' * 1000, 'should_pass': False},  # name has max_length=500
        {'field': 'description', 'value': 'B' * 1000, 'should_pass': True},   # description limit is 1000
        {'field': 'description', 'value': 'B' * 1001, 'should_pass': False},  # over the limit
        {'field': 'instructions', 'value': 'C' * 10000, 'should_pass': True}, # instructions limit is 15000
        {'field': 'notes', 'value': 'D' * 1000, 'should_pass': True},         # notes limit is 1000
        {'field': 'notes', 'value': 'D' * 1001, 'should_pass': False},        # over the limit
        {'field': 'utensils', 'value': 'E' * 500, 'should_pass': True},       # utensils limit is 500
        {'field': 'utensils', 'value': 'E' * 501, 'should_pass': False},      # over the limit
        
        # Boundary numeric values
        {'field': 'total_time', 'value': 0, 'should_pass': True},
        {'field': 'total_time', 'value': 9999, 'should_pass': True},
        {'field': 'weight_in_grams', 'value': 0, 'should_pass': True},
        {'field': 'weight_in_grams', 'value': 999999, 'should_pass': True},
    ]


@pytest.fixture
def privacy_enum_scenarios():
    """Provide test scenarios for privacy enum validation."""
    return [
        # Valid enum values
        {'value': Privacy.PUBLIC, 'should_pass': True},
        {'value': Privacy.PRIVATE, 'should_pass': True},
        {'value': 'public', 'should_pass': True},
        {'value': 'private', 'should_pass': True},
        {'value': None, 'should_pass': True},  # Should default to PRIVATE
        
        # Invalid enum values
        {'value': 'invalid', 'should_pass': False},
        {'value': 'INVALID', 'should_pass': False},
        {'value': 123, 'should_pass': False},
    ]


@pytest.fixture
def realistic_recipe_scenarios():
    """Provide realistic recipe scenarios from existing data factories."""
    return REALISTIC_RECIPE_SCENARIOS


@pytest.fixture
def complex_ingredients_scenarios():
    """Provide complex ingredients scenarios for testing."""
    return [
        # Empty ingredients
        {'ingredients': frozenset(), 'should_pass': True},
        
        # Single ingredient
        {'ingredients': frozenset([
            create_api_ingredient(name='Flour', quantity=2.0, unit=MeasureUnit.CUP, position=0)
        ]), 'should_pass': True},
        
        # Multiple ingredients
        {'ingredients': frozenset([
            create_api_ingredient(name='Flour', quantity=2.0, unit=MeasureUnit.CUP, position=0),
            create_api_ingredient(name='Sugar', quantity=1.0, unit=MeasureUnit.CUP, position=1),
            create_api_ingredient(name='Eggs', quantity=3.0, unit=MeasureUnit.UNIT, position=2),
        ]), 'should_pass': True},
        
        # Many ingredients
        {'ingredients': frozenset([
            create_api_ingredient(name=f'Ingredient {i}', quantity=float(i+1), unit=MeasureUnit.GRAM, position=i)
            for i in range(20)
        ]), 'should_pass': True},
    ]


@pytest.fixture
def complex_tags_scenarios():
    """Provide complex tags scenarios for testing."""
    author_id = str(uuid4())
    return [
        # Empty tags
        {'tags': frozenset(), 'should_pass': True},
        
        # Single tag
        {'tags': frozenset([
            create_api_recipe_tag(key='difficulty', value='easy', author_id=author_id)
        ]), 'should_pass': True},
        
        # Multiple tags
        {'tags': frozenset([
            create_api_recipe_tag(key='difficulty', value='easy', author_id=author_id),
            create_api_recipe_tag(key='cuisine', value='italian', author_id=author_id),
            create_api_recipe_tag(key='meal-type', value='dinner', author_id=author_id),
        ]), 'should_pass': True},
        
        # Many tags
        {'tags': frozenset([
            create_api_recipe_tag(key=f'tag{i}', value=f'value{i}', author_id=author_id)
            for i in range(10)
        ]), 'should_pass': True},
    ]


@pytest.fixture
def domain_conversion_scenarios():
    """Provide scenarios for testing domain conversion."""
    return [
        # Simple conversion
        {'scenario': 'simple', 'factory': create_simple_api_recipe},
        
        # Complex conversion
        {'scenario': 'complex', 'factory': create_complex_api_recipe},
        
        # Minimal conversion
        {'scenario': 'minimal', 'factory': create_minimal_api_recipe},
        
        # Maximum fields conversion
        {'scenario': 'maximum', 'factory': create_api_recipe_with_max_fields},
    ]


@pytest.fixture
def validation_test_cases():
    """Provide comprehensive validation test cases."""
    return create_comprehensive_validation_test_cases_for_api_recipe()


def create_api_create_recipe_kwargs(**overrides) -> Dict[str, Any]:
    """
    Helper function to create ApiCreateRecipe kwargs with overrides.
    
    This function properly handles the author_id constraint for tags by:
    1. Extracting author_id from overrides first
    2. Creating tags with the correct author_id after applying overrides
    
    Args:
        **overrides: Any field overrides to apply
        
    Returns:
        Dict with ApiCreateRecipe kwargs
    """
    # Extract author_id from overrides first, or generate a new one
    author_id = overrides.get('author_id', str(uuid4()))
    
    # Create base kwargs with the correct author_id
    base_kwargs = {
        'name': 'Test Recipe',
        'instructions': 'Test instructions for recipe',
        'author_id': author_id,
        'meal_id': str(uuid4()),
        'description': 'Test description',
        'utensils': 'Test utensils',
        'total_time': 30,
        'notes': 'Test notes',
        'privacy': Privacy.PRIVATE,
        'nutri_facts': None,
        'weight_in_grams': 200,
        'image_url': 'https://example.com/test.jpg',
    }
    
    # Apply overrides (except for ingredients and tags which need special handling)
    for key, value in overrides.items():
        if key not in ['ingredients', 'tags']:
            base_kwargs[key] = value
    
    # Update author_id if it was changed by overrides
    author_id = base_kwargs['author_id']
    
    # Create ingredients (use override if provided, otherwise default)
    if 'ingredients' in overrides:
        base_kwargs['ingredients'] = overrides['ingredients']
    else:
        base_kwargs['ingredients'] = frozenset([
            create_api_ingredient(name='Test Ingredient', quantity=1.0, unit=MeasureUnit.GRAM, position=0)
        ])
    
    # Create tags with the correct author_id (use override if provided, otherwise default)
    if 'tags' in overrides:
        base_kwargs['tags'] = overrides['tags']
    else:
        base_kwargs['tags'] = frozenset([
            create_api_recipe_tag(key='test', value='value', author_id=author_id)
        ])
    
    return base_kwargs


def create_minimal_api_create_recipe_kwargs(**overrides) -> Dict[str, Any]:
    """
    Helper function to create minimal ApiCreateRecipe kwargs with overrides.
    
    This function creates only the required fields and properly handles
    the author_id constraint for tags.
    
    Args:
        **overrides: Any field overrides to apply
        
    Returns:
        Dict with minimal ApiCreateRecipe kwargs
    """
    # Extract author_id from overrides first, or generate a new one
    author_id = overrides.get('author_id', str(uuid4()))
    
    # Create minimal base kwargs
    base_kwargs = {
        'name': 'Test Recipe',
        'instructions': 'Test instructions',
        'author_id': author_id,
        'meal_id': str(uuid4()),
    }
    
    # Apply overrides (except for ingredients and tags which need special handling)
    for key, value in overrides.items():
        if key not in ['ingredients', 'tags']:
            base_kwargs[key] = value
    
    # Update author_id if it was changed by overrides
    author_id = base_kwargs['author_id']
    
    # Create ingredients (use override if provided, otherwise default)
    if 'ingredients' in overrides:
        base_kwargs['ingredients'] = overrides['ingredients']
    else:
        base_kwargs['ingredients'] = frozenset([
            create_api_ingredient(name='Test Ingredient', quantity=1.0, unit=MeasureUnit.GRAM, position=0)
        ])
    
    # Create tags with the correct author_id (use override if provided, otherwise default)
    if 'tags' in overrides:
        base_kwargs['tags'] = overrides['tags']
    else:
        base_kwargs['tags'] = frozenset([
            create_api_recipe_tag(key='test', value='value', author_id=author_id)
        ])
    
    return base_kwargs


def create_api_create_recipe_with_author_id(author_id: str, **overrides) -> Dict[str, Any]:
    """
    Helper function to create ApiCreateRecipe kwargs with a specific author_id.
    
    This is a convenience function that ensures the author_id is used consistently
    for both the recipe and its tags.
    
    Args:
        author_id: The author_id to use for the recipe and tags
        **overrides: Any other field overrides to apply
        
    Returns:
        Dict with ApiCreateRecipe kwargs
    """
    return create_api_create_recipe_kwargs(author_id=author_id, **overrides)


def create_minimal_api_create_recipe_with_author_id(author_id: str, **overrides) -> Dict[str, Any]:
    """
    Helper function to create minimal ApiCreateRecipe kwargs with a specific author_id.
    
    This is a convenience function that ensures the author_id is used consistently
    for both the recipe and its tags.
    
    Args:
        author_id: The author_id to use for the recipe and tags
        **overrides: Any other field overrides to apply
        
    Returns:
        Dict with minimal ApiCreateRecipe kwargs
    """
    return create_minimal_api_create_recipe_kwargs(author_id=author_id, **overrides)


def create_invalid_api_create_recipe_kwargs(field_name: str, invalid_value: Any, **base_overrides) -> Dict[str, Any]:
    """
    Helper function to create invalid ApiCreateRecipe kwargs for testing.
    
    This function creates valid kwargs and then sets one field to an invalid value.
    It properly handles the author_id constraint for tags.
    
    Args:
        field_name: The field to set to an invalid value
        invalid_value: The invalid value to use
        **base_overrides: Any other field overrides to apply first
        
    Returns:
        Dict with invalid ApiCreateRecipe kwargs
    """
    # Create valid kwargs with base overrides
    valid_kwargs = create_api_create_recipe_kwargs(**base_overrides)
    
    # Set the specified field to the invalid value
    valid_kwargs[field_name] = invalid_value
    
    # Special handling for author_id: if we're making it invalid, we need to keep tags valid
    # or if we're making tags invalid, we need to keep author_id valid
    if field_name == 'author_id':
        # Keep tags consistent with the new (invalid) author_id
        # but don't change the invalid author_id itself
        pass
    elif field_name == 'tags':
        # Don't modify tags further - use the provided invalid value
        pass
    
    return valid_kwargs


def create_api_create_recipe_with_custom_tags(author_id: str, tags: listDict[str, Any]], **overrides) -> Dict[str, Any]:
    """
    Helper function to create ApiCreateRecipe kwargs with custom tags.
    
    This function creates kwargs with custom tags that all have the correct author_id.
    
    Args:
        author_id: The author_id to use for the recipe and tags
        tags: List of tag dictionaries to create ApiTag objects from
        **overrides: Any other field overrides to apply
        
    Returns:
        Dict with ApiCreateRecipe kwargs
    """
    # Create the tag objects with the correct author_id
    tag_objects = []
    for tag_data in tags:
        tag_kwargs = tag_data.copy()
        tag_kwargs['author_id'] = author_id  # Ensure correct author_id
        tag_objects.append(create_api_recipe_tag(**tag_kwargs))
    
    # Create the recipe kwargs with the custom tags
    return create_api_create_recipe_kwargs(
        author_id=author_id,
        tags=frozenset(tag_objects),
        **overrides
    )


def create_api_create_recipe_with_ingredients_and_tags(
    author_id: str,
    ingredients: listDict[str, Any]],
    tags: listDict[str, Any]],
    **overrides
) -> Dict[str, Any]:
    """
    Helper function to create ApiCreateRecipe kwargs with custom ingredients and tags.
    
    This function creates kwargs with custom ingredients and tags, ensuring
    the author_id constraint is properly handled.
    
    Args:
        author_id: The author_id to use for the recipe and tags
        ingredients: List of ingredient dictionaries to create ApiIngredient objects from
        tags: List of tag dictionaries to create ApiTag objects from
        **overrides: Any other field overrides to apply
        
    Returns:
        Dict with ApiCreateRecipe kwargs
    """
    # Create the ingredient objects
    ingredient_objects = []
    for ingredient_data in ingredients:
        ingredient_objects.append(create_api_ingredient(**ingredient_data))
    
    # Create the tag objects with the correct author_id
    tag_objects = []
    for tag_data in tags:
        tag_kwargs = tag_data.copy()
        tag_kwargs['author_id'] = author_id  # Ensure correct author_id
        tag_objects.append(create_api_recipe_tag(**tag_kwargs))
    
    # Create the recipe kwargs with the custom ingredients and tags
    return create_api_create_recipe_kwargs(
        author_id=author_id,
        ingredients=frozenset(ingredient_objects),
        tags=frozenset(tag_objects),
        **overrides
    )


def create_filtered_api_create_recipe_kwargs(source_data: dict[str, Any]) -> Dict[str, Any]:
    """
    Create ApiCreateRecipe kwargs from source data by filtering to valid fields.
    
    This function handles invalid test data gracefully by ensuring that
    tags are always explicitly provided (even if empty) so the data factory
    doesn't try to create defaults that might fail with invalid data.
    
    Args:
        source_data: Source data dictionary
        
    Returns:
        Dictionary with only valid ApiCreateRecipe fields
    """
    # Valid fields based on CreateRecipe domain command (excluding recipe_id which is auto-generated)
    valid_fields = {
        'name', 'instructions', 'author_id', 'meal_id', 'ingredients',
        'description', 'utensils', 'total_time', 'notes', 'tags',
        'privacy', 'nutri_facts', 'weight_in_grams', 'image_url'
    }
    
    # Ensure tags are always provided to prevent factory from creating defaults
    # that might fail with invalid author_id or other invalid data
    prepared_data = source_data.copy()
    
    # If tags not provided, use empty frozenset
    if 'tags' not in prepared_data:
        prepared_data['tags'] = frozenset()
    
    # If ingredients not provided, use empty frozenset
    if 'ingredients' not in prepared_data:
        prepared_data['ingredients'] = frozenset()
    
    # Use the data factory with explicit empty collections when needed
    try:
        kwargs = create_api_recipe_kwargs(**prepared_data)
        return {k: v for k, v in kwargs.items() if k in valid_fields}
    except (ValueError, ValidationError, AttributeError, TypeError) as e:
        # If the data factory still fails, fall back to direct filtering
        return {k: v for k, v in source_data.items() if k in valid_fields}


# =============================================================================
# TEST FIXTURES - MEAL
# =============================================================================

@pytest.fixture
def valid_api_create_meal_kwargs():
    """Create valid ApiCreateMeal kwargs using existing data factories."""
    # Use existing factory but filter to fields needed for ApiCreateMeal
    meal_kwargs = create_api_meal_kwargs()
    
    # Filter to only ApiCreateMeal fields (remove computed and entity-specific fields)
    create_meal_kwargs = {
        'name': meal_kwargs['name'],
        'author_id': meal_kwargs['author_id'],
        'menu_id': meal_kwargs['menu_id'] if meal_kwargs['menu_id'] is not None else str(uuid4()),  # Ensure menu_id is never None
        'recipes': meal_kwargs['recipes'],
        'tags': meal_kwargs['tags'],
        'description': meal_kwargs['description'],
        'notes': meal_kwargs['notes'],
        'image_url': meal_kwargs['image_url'],
    }
    
    return create_meal_kwargs


@pytest.fixture
def valid_api_create_meal(valid_api_create_meal_kwargs):
    """Create valid ApiCreateMeal instance."""
    return ApiCreateMeal(**valid_api_create_meal_kwargs)


@pytest.fixture
def minimal_api_create_meal_kwargs():
    """Create minimal ApiCreateMeal kwargs with only required fields."""
    author_id = str(uuid4())
    return {
        'name': 'Test Meal',
        'author_id': author_id,
        'menu_id': str(uuid4()),
        'recipes': [],  # Optional but can be empty
        'tags': frozenset(),  # Optional but can be empty
    }


@pytest.fixture
def minimal_api_create_meal(minimal_api_create_meal_kwargs):
    """Create minimal ApiCreateMeal instance."""
    return ApiCreateMeal(**minimal_api_create_meal_kwargs)


# =============================================================================
# HELPER FUNCTIONS - RECIPE (EXISTING)
# =============================================================================

# =============================================================================
# HELPER FUNCTIONS - MEAL
# =============================================================================

def create_api_create_meal_kwargs(**overrides) -> Dict[str, Any]:
    """
    Helper function to create ApiCreateMeal kwargs with overrides.
    
    This function properly handles the author_id constraint for tags and recipes by:
    1. Extracting author_id from overrides first
    2. Creating tags and recipes with the correct author_id after applying overrides
    
    Args:
        **overrides: Any field overrides to apply
        
    Returns:
        Dict with ApiCreateMeal kwargs
    """
    # Extract author_id from overrides first, or generate a new one
    author_id = overrides.get('author_id', str(uuid4()))
    
    # Create base kwargs with the correct author_id
    base_kwargs = {
        'name': 'Test Meal',
        'author_id': author_id,
        'menu_id': str(uuid4()),  # Always ensure menu_id is a valid UUID for ApiCreateMeal
        'description': 'Test meal description',
        'notes': 'Test meal notes',
        'image_url': 'https://example.com/test-meal.jpg',
    }
    
    # Apply overrides (except for recipes and tags which need special handling)
    for key, value in overrides.items():
        if key not in ['recipes', 'tags']:
            base_kwargs[key] = value
    
    # Update author_id if it was changed by overrides
    author_id = base_kwargs['author_id']
    
    # Ensure menu_id is never None (required for ApiCreateMeal)
    if base_kwargs['menu_id'] is None:
        base_kwargs['menu_id'] = str(uuid4())
    
    # Create recipes (use override if provided, otherwise default)
    if 'recipes' in overrides:
        base_kwargs['recipes'] = overrides['recipes']
    else:
        # Create simple recipes with the correct author_id and meal_id (if meal has id)
        meal_id = base_kwargs.get('meal_id', str(uuid4()))
        base_kwargs['recipes'] = [
            create_simple_api_recipe(name='Test Recipe 1', author_id=author_id, meal_id=meal_id),
            create_simple_api_recipe(name='Test Recipe 2', author_id=author_id, meal_id=meal_id)
        ]
    
    # Create tags with the correct author_id (use override if provided, otherwise default)
    if 'tags' in overrides:
        base_kwargs['tags'] = overrides['tags']
    else:
        base_kwargs['tags'] = frozenset([
            create_api_meal_tag(key='meal_type', value='dinner', author_id=author_id),
            create_api_meal_tag(key='difficulty', value='medium', author_id=author_id)
        ])
    
    return base_kwargs


def create_minimal_api_create_meal_kwargs(**overrides) -> Dict[str, Any]:
    """
    Helper function to create minimal ApiCreateMeal kwargs with overrides.
    
    This function creates only the required fields and properly handles
    the author_id constraint for any tags or recipes.
    
    Args:
        **overrides: Any field overrides to apply
        
    Returns:
        Dict with minimal ApiCreateMeal kwargs
    """
    # Extract author_id from overrides first, or generate a new one
    author_id = overrides.get('author_id', str(uuid4()))
    
    # Create minimal base kwargs
    base_kwargs = {
        'name': 'Test Meal',
        'author_id': author_id,
        'menu_id': str(uuid4()),  # Always ensure menu_id is a valid UUID for ApiCreateMeal
    }
    
    # Apply overrides (except for recipes and tags which need special handling)
    for key, value in overrides.items():
        if key not in ['recipes', 'tags']:
            base_kwargs[key] = value
    
    # Update author_id if it was changed by overrides
    author_id = base_kwargs['author_id']
    
    # Ensure menu_id is never None (required for ApiCreateMeal)
    if base_kwargs['menu_id'] is None:
        base_kwargs['menu_id'] = str(uuid4())
    
    # Create recipes (use override if provided, otherwise empty list)
    if 'recipes' in overrides:
        base_kwargs['recipes'] = overrides['recipes']
    else:
        base_kwargs['recipes'] = []
    
    # Create tags (use override if provided, otherwise empty frozenset)
    if 'tags' in overrides:
        base_kwargs['tags'] = overrides['tags']
    else:
        base_kwargs['tags'] = frozenset()
    
    return base_kwargs


def create_api_create_meal_with_author_id(author_id: str, **overrides) -> Dict[str, Any]:
    """
    Helper function to create ApiCreateMeal kwargs with a specific author_id.
    
    This is a convenience function that ensures the author_id is used consistently
    for the meal, its recipes, and its tags.
    
    Args:
        author_id: The author_id to use for the meal, recipes, and tags
        **overrides: Any other field overrides to apply
        
    Returns:
        Dict with ApiCreateMeal kwargs
    """
    return create_api_create_meal_kwargs(author_id=author_id, **overrides)


def create_minimal_api_create_meal_with_author_id(author_id: str, **overrides) -> Dict[str, Any]:
    """
    Helper function to create minimal ApiCreateMeal kwargs with a specific author_id.
    
    This is a convenience function that ensures the author_id is used consistently
    for the meal and any nested objects.
    
    Args:
        author_id: The author_id to use for the meal and nested objects
        **overrides: Any other field overrides to apply
        
    Returns:
        Dict with minimal ApiCreateMeal kwargs
    """
    return create_minimal_api_create_meal_kwargs(author_id=author_id, **overrides)


def create_api_create_meal_with_custom_recipes(author_id: str, recipes: listAny], **overrides) -> Dict[str, Any]:
    """
    Helper function to create ApiCreateMeal kwargs with custom recipes.
    
    This function creates kwargs with custom recipes that all have the correct author_id.
    
    Args:
        author_id: The author_id to use for the meal and recipes
        recipes: List of recipe objects to include in the meal
        **overrides: Any other field overrides to apply
        
    Returns:
        Dict with ApiCreateMeal kwargs
    """
    return create_api_create_meal_kwargs(
        author_id=author_id,
        recipes=recipes,
        **overrides
    )


def create_api_create_meal_with_custom_tags(author_id: str, tags: listDict[str, Any]], **overrides) -> Dict[str, Any]:
    """
    Helper function to create ApiCreateMeal kwargs with custom tags.
    
    This function creates kwargs with custom tags that all have the correct author_id.
    
    Args:
        author_id: The author_id to use for the meal and tags
        tags: List of tag dictionaries to create ApiTag objects from
        **overrides: Any other field overrides to apply
        
    Returns:
        Dict with ApiCreateMeal kwargs
    """
    # Create the tag objects with the correct author_id
    tag_objects = []
    for tag_data in tags:
        tag_kwargs = tag_data.copy()
        tag_kwargs['author_id'] = author_id  # Ensure correct author_id
        tag_kwargs['type'] = 'meal'  # Ensure correct type for meal tags
        tag_objects.append(create_api_meal_tag(**tag_kwargs))
    
    # Create the meal kwargs with the custom tags
    return create_api_create_meal_kwargs(
        author_id=author_id,
        tags=frozenset(tag_objects),
        **overrides
    )


def create_api_create_meal_with_recipes_and_tags(
    author_id: str,
    recipes: listAny],
    tags: listDict[str, Any]],
    **overrides
) -> Dict[str, Any]:
    """
    Helper function to create ApiCreateMeal kwargs with custom recipes and tags.
    
    This function creates kwargs with custom recipes and tags, ensuring
    the author_id constraint is properly handled.
    
    Args:
        author_id: The author_id to use for the meal, recipes, and tags
        recipes: List of recipe objects to include in the meal
        tags: List of tag dictionaries to create ApiTag objects from
        **overrides: Any other field overrides to apply
        
    Returns:
        Dict with ApiCreateMeal kwargs
    """
    # Create the tag objects with the correct author_id
    tag_objects = []
    for tag_data in tags:
        tag_kwargs = tag_data.copy()
        tag_kwargs['author_id'] = author_id  # Ensure correct author_id
        tag_kwargs['type'] = 'meal'  # Ensure correct type for meal tags
        tag_objects.append(create_api_meal_tag(**tag_kwargs))
    
    # Create the meal kwargs with the custom recipes and tags
    return create_api_create_meal_kwargs(
        author_id=author_id,
        recipes=recipes,
        tags=frozenset(tag_objects),
        **overrides
    )


def create_invalid_api_create_meal_kwargs(field_name: str, invalid_value: Any, **base_overrides) -> Dict[str, Any]:
    """
    Helper function to create invalid ApiCreateMeal kwargs for testing.
    
    This function creates valid kwargs and then sets one field to an invalid value.
    It properly handles the author_id constraint for tags and recipes.
    
    Args:
        field_name: The field to set to an invalid value
        invalid_value: The invalid value to use
        **base_overrides: Any other field overrides to apply first
        
    Returns:
        Dict with invalid ApiCreateMeal kwargs
    """
    # Create valid kwargs with base overrides
    valid_kwargs = create_api_create_meal_kwargs(**base_overrides)
    
    # Set the specified field to the invalid value
    valid_kwargs[field_name] = invalid_value
    
    return valid_kwargs


def create_filtered_api_create_meal_kwargs(source_data: dict[str, Any]) -> Dict[str, Any]:
    """
    Create ApiCreateMeal kwargs from source data by filtering to valid fields.
    
    This function handles invalid test data gracefully by ensuring that
    recipes and tags are always explicitly provided (even if empty) so the
    data factory doesn't try to create defaults that might fail with invalid data.
    
    Args:
        source_data: Source data dictionary
        
    Returns:
        Dictionary with only valid ApiCreateMeal fields
    """
    # Valid fields based on CreateMeal domain command (excluding meal_id which is auto-generated)
    valid_fields = {
        'name', 'author_id', 'menu_id', 'recipes', 'tags',
        'description', 'notes', 'image_url'
    }
    
    # Ensure recipes and tags are always provided to prevent factory from creating defaults
    # that might fail with invalid author_id or other invalid data
    prepared_data = source_data.copy()
    
    # If recipes not provided, use empty list
    if 'recipes' not in prepared_data:
        prepared_data['recipes'] = []
    
    # If tags not provided, use empty frozenset
    if 'tags' not in prepared_data:
        prepared_data['tags'] = frozenset()
    
    # Use the data factory with explicit empty collections when needed
    try:
        kwargs = create_api_meal_kwargs(**prepared_data)
        return {k: v for k, v in kwargs.items() if k in valid_fields}
    except (ValueError, ValidationError, AttributeError, TypeError) as e:
        # If the data factory still fails (e.g., due to nutrition calculation on invalid recipes), 
        # fall back to direct filtering
        return {k: v for k, v in source_data.items() if k in valid_fields}


# =============================================================================
# HELPER UTILITIES
# =============================================================================

def create_api_meal_tag(**kwargs) -> ApiTag:
    """Create an ApiTag specifically for meal entities."""
    defaults = {
        'type': 'meal',
        'key': 'test',
        'value': 'value',
        'author_id': str(uuid4())
    }
    defaults.update(kwargs)
    return ApiTag(**defaults)
