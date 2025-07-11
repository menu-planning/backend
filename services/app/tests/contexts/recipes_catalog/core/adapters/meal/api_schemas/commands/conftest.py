"""
Test fixtures and utilities for ApiCreateRecipe testing.

This module provides comprehensive test fixtures leveraging the existing
api_recipe_data_factories.py utilities and creating specialized fixtures
for ApiCreateRecipe validation scenarios.
"""

import pytest
from uuid import uuid4
from typing import Dict, Any, List

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_recipe import ApiCreateRecipe
from src.contexts.recipes_catalog.core.domain.meal.commands.create_recipe import CreateRecipe
from src.contexts.shared_kernel.domain.enums import Privacy, MeasureUnit

# Import existing data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    create_api_recipe_kwargs,
    create_api_recipe,
    create_simple_api_recipe,
    create_complex_api_recipe,
    create_minimal_api_recipe,
    create_api_recipe_with_max_fields,
    create_api_recipe_with_none_values,
    create_api_recipe_with_empty_strings,
    create_api_recipe_with_whitespace_strings,
    create_api_recipe_with_very_long_text,
    create_api_recipe_with_boundary_values,
    create_api_recipe_with_extreme_boundary_values,
    create_comprehensive_validation_test_cases,
    create_api_recipe_tag,  # Use existing tag creation function
    REALISTIC_RECIPE_SCENARIOS,
)

# Import nested object factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objects.data_factories.api_ingredient_data_factories import (
    create_api_ingredient,
    create_recipe_ingredients,
)


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
        # Maximum length strings
        {'field': 'name', 'value': 'A' * 1000, 'should_pass': False},
        {'field': 'description', 'value': 'B' * 5000, 'should_pass': True},
        {'field': 'instructions', 'value': 'C' * 10000, 'should_pass': True},
        {'field': 'notes', 'value': 'D' * 2000, 'should_pass': True},
        {'field': 'utensils', 'value': 'E' * 1000, 'should_pass': True},
        
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
    return create_comprehensive_validation_test_cases()


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


def create_api_create_recipe_with_custom_tags(author_id: str, tags: List[Dict[str, Any]], **overrides) -> Dict[str, Any]:
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
    ingredients: List[Dict[str, Any]],
    tags: List[Dict[str, Any]],
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


def create_filtered_api_create_recipe_kwargs(source_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create ApiCreateRecipe kwargs from source data by filtering to valid fields.
    
    Simply removes fields that don't exist in the CreateRecipe domain command.
    
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
    
    # Simply filter to valid fields
    return {k: v for k, v in source_data.items() if k in valid_fields}
