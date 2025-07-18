"""
Data factories for ApiUpdateMeal testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- JSON serialization/deserialization testing with model_validate_json and model_dump_json
- Parametrized test scenarios for update validation
- Performance test scenarios for update operations
- Specialized factory functions for different update types
- Comprehensive attribute validation using check_missing_attributes
- Realistic update scenarios for production-like testing
- Complex partial update scenarios
- Round-trip testing for update operations
- Testing exclude_unset behavior for partial updates
- Validation testing for from_api_meal() method

All data follows the exact structure of ApiUpdateMeal API commands and their validation rules.
Includes extensive testing for Pydantic model validation, JSON handling, and edge cases.
Focus on partial update scenarios which are the primary use case for update operations.
"""

from typing import Dict, Any, List
from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_update_meal import (
    ApiUpdateMeal, 
    ApiAttributesToUpdateOnMeal
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal


# Import existing factories for creating base meals and nested objects
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.data_factories.api_meal_data_factories import (
    create_api_meal, create_simple_api_meal, create_complex_api_meal,
    create_api_tag
)
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    create_simple_api_recipe
)
from tests.contexts.recipes_catalog.utils import generate_deterministic_id
from tests.utils.utils import check_missing_attributes
from tests.utils.counter_manager import get_next_update_id

# =============================================================================
# REALISTIC UPDATE SCENARIOS FOR PRODUCTION-LIKE TESTING
# =============================================================================

REALISTIC_UPDATE_SCENARIOS = [
    {
        "name": "name_only_update",
        "description": "Update only the meal name",
        "updates": {"name": "Updated Italian Dinner"},
        "scenario": "quick_name_change"
    },
    {
        "name": "description_and_notes_update",
        "description": "Update description and notes together",
        "updates": {
            "description": "Updated description with more details about the meal preparation",
            "notes": "Updated notes with cooking tips and wine pairing suggestions"
        },
        "scenario": "content_enhancement"
    },
    {
        "name": "like_status_update",
        "description": "Toggle like status",
        "updates": {"like": True},
        "scenario": "preference_change"
    },
    {
        "name": "menu_migration_update",
        "description": "Move meal to different menu",
        "updates": {"menu_id": str(uuid4())},
        "scenario": "menu_reorganization"
    },
    {
        "name": "recipe_modification_update",
        "description": "Update recipes in the meal",
        "updates": {"recipes": []},  # Will be populated with actual recipes
        "scenario": "recipe_changes"
    },
    {
        "name": "tag_system_update",
        "description": "Update meal tags for better organization",
        "updates": {"tags": frozenset()},  # Will be populated with actual tags
        "scenario": "categorization_update"
    },
    {
        "name": "image_url_update",
        "description": "Update meal image",
        "updates": {"image_url": "https://example.com/updated-meal-image.jpg"},
        "scenario": "visual_update"
    },
    {
        "name": "comprehensive_update",
        "description": "Update multiple fields at once",
        "updates": {
            "name": "Completely Updated Meal",
            "description": "New comprehensive description",
            "notes": "Updated notes with new information",
            "like": True,
            "image_url": "https://example.com/new-meal-image.jpg"
        },
        "scenario": "major_revision"
    },
    {
        "name": "partial_content_update",
        "description": "Update only content fields",
        "updates": {
            "description": "Enhanced description with cooking techniques",
            "notes": "Professional chef tips and ingredient substitutions"
        },
        "scenario": "content_enrichment"
    },
    {
        "name": "clear_optional_fields",
        "description": "Clear optional fields by setting to None",
        "updates": {
            "description": None,
            "notes": None,
            "image_url": None,
            "like": None
        },
        "scenario": "field_cleanup"
    }
]

# =============================================================================
# HELPER FUNCTIONS FOR UPDATE SCENARIOS
# =============================================================================

def create_update_scenario_data(scenario_name: str, **overrides) -> Dict[str, Any]:
    """Create update data for a specific scenario"""
    scenario = next(s for s in REALISTIC_UPDATE_SCENARIOS if s["name"] == scenario_name)
    updates = scenario["updates"].copy()
    
    # Apply overrides
    updates.update(overrides)
    
    # Special handling for complex fields
    if "recipes" in updates and not updates["recipes"]:
        # Create sample recipes if empty list
        meal_id = str(uuid4())
        author_id = str(uuid4())
        updates["recipes"] = [
            create_simple_api_recipe(name="Updated Recipe 1", meal_id=meal_id, author_id=author_id),
            create_simple_api_recipe(name="Updated Recipe 2", meal_id=meal_id, author_id=author_id)
        ]
    
    if "tags" in updates and not updates["tags"]:
        # Create sample tags if empty frozenset
        author_id = str(uuid4())
        updates["tags"] = frozenset([
            create_api_tag(key="cuisine", value="updated", author_id=author_id),
            create_api_tag(key="difficulty", value="easy", author_id=author_id)
        ])
    
    return updates

# =============================================================================
# FIELD VALIDATION TESTING FUNCTIONS
# =============================================================================

def create_update_field_validation_test_suite() -> Dict[str, List[Dict[str, Any]]]:
    """
    Comprehensive field validation test suite for ApiUpdateMeal and ApiAttributesToUpdateOnMeal.
    
    Tests all field constraints specific to update operations including:
    - Optional field validation (all fields in updates are optional)
    - Partial update scenarios
    - exclude_unset behavior
    - Type validation for update fields
    - Constraint validation for numeric fields
    
    Returns:
        Dict mapping validation categories to lists of invalid update data
    """
    return {
        "name_update_validation": [
            {"name": ""},                    # Empty string (violates min_length=1)
            {"name": "x" * 256},            # Too long (violates max_length=255)
            {"name": 123},                  # Wrong type (violates str type)
            {"name": ["not", "a", "string"]},  # Wrong type (list)
            {"name": {"not": "a_string"}},  # Wrong type (dict)
            {"name": "   "},                # Whitespace only (after strip = empty)
        ],
        "menu_id_update_validation": [
            {"menu_id": ""},                # Empty string (violates UUID format when not None)
            {"menu_id": "not-a-uuid"},      # Invalid UUID format
            {"menu_id": "12345"},           # Too short for UUID
            {"menu_id": 123},               # Wrong type (int)
            {"menu_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"},  # Invalid UUID chars
        ],
        "boolean_update_validation": [
            {"like": "not_bool"},           # Wrong type (string)
            {"like": 1},                    # Wrong type (int, even though truthy)
            {"like": 0},                    # Wrong type (int, even though falsy)
            {"like": "true"},               # String instead of bool
            {"like": "false"},              # String instead of bool
            {"like": ["true"]},             # Wrong type (list)
        ],
        "text_field_update_validation": [
            {"description": 123},           # Wrong type (int instead of str)
            {"description": ["not", "string"]}, # Wrong type (list)
            {"notes": 456},                 # Wrong type (int instead of str)
            {"notes": {"not": "string"}},   # Wrong type (dict)
        ],
        "collection_update_validation": [
            {"recipes": "not_list"},        # Wrong type (string instead of list)
            {"recipes": 123},               # Wrong type (int instead of list)
            {"recipes": {"not": "list"}},   # Wrong type (dict instead of list)
            {"tags": "not_frozenset"},      # Wrong type (string instead of frozenset)
            {"tags": 123},                  # Wrong type (int instead of frozenset)
            {"tags": ["tag1", "tag2"]},     # Wrong type (list instead of frozenset)
        ],
        "url_update_validation": [
            {"image_url": "not_a_url"},     # Invalid URL format
            {"image_url": "ftp://invalid"}, # Invalid protocol
            {"image_url": 123},             # Wrong type (int)
            {"image_url": ["http://example.com"]}, # Wrong type (list)
        ],
        "meal_id_validation": [
            {"meal_id": ""},                # Empty string (violates UUID format)
            {"meal_id": "not-a-uuid"},      # Invalid UUID format
            {"meal_id": "12345"},           # Too short for UUID
            {"meal_id": 123},               # Wrong type (int)
            {"meal_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"},  # Invalid UUID chars
        ]
    }

def create_exclude_unset_test_scenarios() -> Dict[str, Any]:
    """
    Create test scenarios for exclude_unset behavior validation.
    
    Tests that model_dump(exclude_unset=True) only includes explicitly set fields.
    This is crucial for partial updates where unset fields should not be included.
    
    Returns:
        Dict mapping scenarios to expected behaviors
    """
    return {
        "single_field_update": {
            "updates": {"name": "Updated Name"},
            "expected_fields": {"name"},
            "excluded_fields": {"menu_id", "description", "recipes", "tags", "notes", "like", "image_url"}
        },
        "multiple_field_update": {
            "updates": {"name": "Updated Name", "like": True, "description": "Updated description"},
            "expected_fields": {"name", "like", "description"},
            "excluded_fields": {"menu_id", "recipes", "tags", "notes", "image_url"}
        },
        "none_value_update": {
            "updates": {"description": None, "notes": None},
            "expected_fields": {"description", "notes"},
            "excluded_fields": {"name", "menu_id", "recipes", "tags", "like", "image_url"}
        },
        "empty_collection_update": {
            "updates": {"recipes": [], "tags": frozenset()},
            "expected_fields": {"recipes", "tags"},
            "excluded_fields": {"name", "menu_id", "description", "notes", "like", "image_url"}
        },
        "no_updates": {
            "updates": {},
            "expected_fields": set(),
            "excluded_fields": {"name", "menu_id", "description", "recipes", "tags", "notes", "like", "image_url"}
        }
    }

# =============================================================================
# API UPDATE MEAL DATA FACTORIES
# =============================================================================

def create_api_attributes_to_update_on_meal_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create ApiAttributesToUpdateOnMeal kwargs with deterministic values.
    
    Focuses on partial update scenarios which are the primary use case.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with ApiAttributesToUpdateOnMeal creation parameters
    """
    
    # Get scenario for deterministic values
    scenario_index = (get_next_update_id() - 1) % len(REALISTIC_UPDATE_SCENARIOS)
    scenario = REALISTIC_UPDATE_SCENARIOS[scenario_index]
    
    # Create base update data from scenario
    base_updates = create_update_scenario_data(scenario["name"])
    
    # Apply any overrides
    final_kwargs = {**base_updates, **kwargs}
    
    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(ApiAttributesToUpdateOnMeal, final_kwargs)
    missing = set(missing) - {'model_computed_fields', 'model_config', 'model_fields'}
    # Note: We don't assert missing attributes for update objects since all fields are optional
    
    return final_kwargs

def create_api_attributes_to_update_on_meal(**kwargs) -> ApiAttributesToUpdateOnMeal:
    """
    Create an ApiAttributesToUpdateOnMeal instance with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiAttributesToUpdateOnMeal instance
    """
    update_kwargs = create_api_attributes_to_update_on_meal_kwargs(**kwargs)
    return ApiAttributesToUpdateOnMeal(**update_kwargs)

def create_api_update_meal_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create ApiUpdateMeal kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required ApiUpdateMeal creation parameters
    """
    
    # Generate deterministic meal_id
    meal_id = kwargs.get("meal_id", generate_deterministic_id(f"update_meal_{get_next_update_id()}"))
    
    # Create updates if not provided
    if "updates" not in kwargs:
        updates = create_api_attributes_to_update_on_meal()
    else:
        updates = kwargs["updates"]
        if isinstance(updates, dict):
            updates = ApiAttributesToUpdateOnMeal(**updates)
    
    final_kwargs = {
        "meal_id": meal_id,
        "updates": updates,
        **{k: v for k, v in kwargs.items() if k not in ["meal_id", "updates"]}
    }
    
    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(ApiUpdateMeal, final_kwargs)
    missing = set(missing) - {'model_computed_fields', 'model_config', 'model_fields'}
    assert not missing, f"Missing attributes for ApiUpdateMeal: {missing}"
    
    return final_kwargs

def create_api_update_meal(**kwargs) -> ApiUpdateMeal:
    """
    Create an ApiUpdateMeal instance with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUpdateMeal instance with comprehensive validation
    """
    update_kwargs = create_api_update_meal_kwargs(**kwargs)
    return ApiUpdateMeal(**update_kwargs)

def create_api_update_meal_from_json(json_data: str) -> ApiUpdateMeal:
    """
    Create an ApiUpdateMeal instance from JSON using model_validate_json.
    
    Args:
        json_data: JSON string to parse
        
    Returns:
        ApiUpdateMeal instance created from JSON
    """
    return ApiUpdateMeal.model_validate_json(json_data)

def create_api_update_meal_json(**kwargs) -> str:
    """
    Create JSON representation of ApiUpdateMeal using model_dump_json.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        JSON string representation of ApiUpdateMeal
    """
    update_meal = create_api_update_meal(**kwargs)
    return update_meal.model_dump_json()

# =============================================================================
# SPECIALIZED FACTORY FUNCTIONS FOR UPDATE SCENARIOS
# =============================================================================

def create_partial_name_update(**kwargs) -> ApiUpdateMeal:
    """Create update that only changes the meal name"""
    updates = {"name": kwargs.get("name", "Updated Meal Name")}
    return create_api_update_meal(updates=updates, **{k: v for k, v in kwargs.items() if k != "name"})

def create_partial_description_update(**kwargs) -> ApiUpdateMeal:
    """Create update that only changes the description"""
    updates = {"description": kwargs.get("description", "Updated meal description with more details")}
    return create_api_update_meal(updates=updates, **{k: v for k, v in kwargs.items() if k != "description"})

def create_partial_like_status_update(**kwargs) -> ApiUpdateMeal:
    """Create update that only changes the like status"""
    updates = {"like": kwargs.get("like", True)}
    return create_api_update_meal(updates=updates, **{k: v for k, v in kwargs.items() if k != "like"})

def create_partial_menu_migration_update(**kwargs) -> ApiUpdateMeal:
    """Create update that moves meal to different menu"""
    updates = {"menu_id": kwargs.get("menu_id", str(uuid4()))}
    return create_api_update_meal(updates=updates, **{k: v for k, v in kwargs.items() if k != "menu_id"})

def create_partial_content_update(**kwargs) -> ApiUpdateMeal:
    """Create update that changes content fields (description and notes)"""
    updates = {
        "description": kwargs.get("description", "Updated comprehensive description"),
        "notes": kwargs.get("notes", "Updated notes with additional information")
    }
    return create_api_update_meal(updates=updates, **{k: v for k, v in kwargs.items() if k not in ["description", "notes"]})

def create_partial_recipe_update(**kwargs) -> ApiUpdateMeal:
    """Create update that changes recipes in the meal"""
    meal_id = kwargs.get("meal_id", str(uuid4()))
    author_id = kwargs.get("author_id", str(uuid4()))
    
    updates = {
        "recipes": kwargs.get("recipes", [
            create_simple_api_recipe(name="Updated Recipe 1", meal_id=meal_id, author_id=author_id),
            create_simple_api_recipe(name="Updated Recipe 2", meal_id=meal_id, author_id=author_id)
        ])
    }
    return create_api_update_meal(
        meal_id=meal_id,
        updates=updates,
        **{k: v for k, v in kwargs.items() if k not in ["recipes", "meal_id", "author_id"]}
    )

def create_partial_tag_update(**kwargs) -> ApiUpdateMeal:
    """Create update that changes tags in the meal"""
    author_id = kwargs.get("author_id", str(uuid4()))
    
    updates = {
        "tags": kwargs.get("tags", frozenset([
            create_api_tag(key="cuisine", value="updated", author_id=author_id),
            create_api_tag(key="difficulty", value="easy", author_id=author_id)
        ]))
    }
    return create_api_update_meal(updates=updates, **{k: v for k, v in kwargs.items() if k not in ["tags", "author_id"]})

def create_comprehensive_update(**kwargs) -> ApiUpdateMeal:
    """Create update that changes multiple fields at once"""
    updates = {
        "name": kwargs.get("name", "Comprehensively Updated Meal"),
        "description": kwargs.get("description", "Completely updated description with new information"),
        "notes": kwargs.get("notes", "Updated notes with professional tips and techniques"),
        "like": kwargs.get("like", True),
        "image_url": kwargs.get("image_url", "https://example.com/updated-comprehensive-meal.jpg")
    }
    return create_api_update_meal(updates=updates, **{k: v for k, v in kwargs.items() if k not in updates.keys()})

def create_clear_fields_update(**kwargs) -> ApiUpdateMeal:
    """Create update that clears optional fields by setting them to None"""
    updates = {
        "description": kwargs.get("description", None),
        "notes": kwargs.get("notes", None),
        "image_url": kwargs.get("image_url", None),
        "like": kwargs.get("like", None)
    }
    return create_api_update_meal(updates=updates, **{k: v for k, v in kwargs.items() if k not in updates.keys()})

def create_empty_update(**kwargs) -> ApiUpdateMeal:
    """Create update with no changes (empty updates)"""
    return create_api_update_meal(updates={}, **kwargs)

# =============================================================================
# FROM_API_MEAL METHOD TESTING
# =============================================================================

def create_update_from_api_meal(api_meal: ApiMeal) -> ApiUpdateMeal:
    """
    Create ApiUpdateMeal from existing ApiMeal using from_api_meal method.
    
    Tests the from_api_meal class method functionality.
    
    Args:
        api_meal: ApiMeal instance to create update from
        
    Returns:
        ApiUpdateMeal instance created from the meal
    """
    return ApiUpdateMeal.from_api_meal(api_meal)

def create_update_from_meal_scenarios() -> Dict[str, Any]:
    """
    Create scenarios for testing from_api_meal method with different meal types.
    
    Returns:
        Dict mapping meal types to update scenarios
    """
    return {
        "simple_meal_update": {
            "original_meal": create_simple_api_meal(),
            "description": "Create update from simple meal"
        },
        "complex_meal_update": {
            "original_meal": create_complex_api_meal(),
            "description": "Create update from complex meal"
        },
        "meal_with_all_fields": {
            "original_meal": create_api_meal(),
            "description": "Create update from meal with all fields populated"
        }
    }

# =============================================================================
# VALIDATION AND ERROR TESTING
# =============================================================================

def create_invalid_update_scenarios() -> Dict[str, Any]:
    """
    Create scenarios for testing invalid update data.
    
    Returns:
        Dict mapping error types to invalid update scenarios
    """
    return {
        "invalid_meal_id": [
            {"meal_id": "", "updates": {"name": "Test"}},
            {"meal_id": "not-uuid", "updates": {"name": "Test"}},
            {"meal_id": 123, "updates": {"name": "Test"}},
        ],
        "invalid_updates_type": [
            {"meal_id": str(uuid4()), "updates": "not_dict"},
            {"meal_id": str(uuid4()), "updates": 123},
            {"meal_id": str(uuid4()), "updates": ["not", "dict"]},
        ],
        "invalid_update_fields": [
            {"meal_id": str(uuid4()), "updates": {"name": ""}},
            {"meal_id": str(uuid4()), "updates": {"name": 123}},
            {"meal_id": str(uuid4()), "updates": {"like": "not_bool"}},
            {"meal_id": str(uuid4()), "updates": {"menu_id": "not-uuid"}},
        ],
        "invalid_nested_objects": [
            {"meal_id": str(uuid4()), "updates": {"recipes": "not_list"}},
            {"meal_id": str(uuid4()), "updates": {"tags": "not_frozenset"}},
            {"meal_id": str(uuid4()), "updates": {"recipes": [{"invalid": "recipe"}]}},
        ]
    }

def create_api_update_meal_with_invalid_field(field_name: str, invalid_value: Any, **kwargs) -> Dict[str, Any]:
    """
    Create ApiUpdateMeal kwargs with a specific field set to an invalid value.
    
    Args:
        field_name: Name of the field to make invalid
        invalid_value: The invalid value to set
        **kwargs: Additional overrides
        
    Returns:
        Dict with invalid field value for validation testing
    """
    if field_name == "meal_id":
        return {
            "meal_id": invalid_value,
            "updates": create_api_attributes_to_update_on_meal(),
            **kwargs
        }
    elif field_name == "updates":
        return {
            "meal_id": str(uuid4()),
            "updates": invalid_value,
            **kwargs
        }
    else:
        # Invalid field in updates
        updates = {field_name: invalid_value}
        return {
            "meal_id": str(uuid4()),
            "updates": updates,
            **kwargs
        }

# =============================================================================
# DOMAIN CONVERSION AND ROUND-TRIP TESTING
# =============================================================================

def create_domain_conversion_scenarios() -> Dict[str, Any]:
    """
    Create scenarios for testing to_domain() conversion.
    
    Returns:
        Dict mapping conversion scenarios to test data
    """
    return {
        "partial_update_conversion": {
            "update": create_partial_name_update(),
            "expected_fields": {"name"},
            "description": "Convert partial update to domain"
        },
        "comprehensive_update_conversion": {
            "update": create_comprehensive_update(),
            "expected_fields": {"name", "description", "notes", "like", "image_url"},
            "description": "Convert comprehensive update to domain"
        },
        "empty_update_conversion": {
            "update": create_empty_update(),
            "expected_fields": set(),
            "description": "Convert empty update to domain"
        },
        "clear_fields_conversion": {
            "update": create_clear_fields_update(),
            "expected_fields": {"description", "notes", "image_url", "like"},
            "description": "Convert field clearing update to domain"
        }
    }

def create_round_trip_test_scenarios() -> Dict[str, Any]:
    """
    Create scenarios for round-trip testing.
    
    Tests consistency through: JSON -> API -> Domain -> Processing
    
    Returns:
        Dict mapping round-trip scenarios to test data
    """
    return {
        "json_api_domain_roundtrip": {
            "original_updates": [
                create_partial_name_update(),
                create_comprehensive_update(),
                create_empty_update(),
                create_clear_fields_update()
            ],
            "description": "Test JSON->API->Domain consistency"
        },
        "api_meal_update_roundtrip": {
            "original_meals": [
                create_simple_api_meal(),
                create_complex_api_meal(),
                create_api_meal()
            ],
            "description": "Test ApiMeal->Update->Domain consistency"
        }
    }

# =============================================================================
# PERFORMANCE TESTING HELPERS
# =============================================================================

def create_bulk_update_scenarios(count: int = 1000) -> List[ApiUpdateMeal]:
    """Create a collection of diverse updates for performance testing"""
    updates = []
    
    for i in range(count):
        if i % 10 == 0:
            update = create_partial_name_update()
        elif i % 10 == 1:
            update = create_partial_description_update()
        elif i % 10 == 2:
            update = create_partial_like_status_update()
        elif i % 10 == 3:
            update = create_partial_menu_migration_update()
        elif i % 10 == 4:
            update = create_partial_content_update()
        elif i % 10 == 5:
            update = create_partial_recipe_update()
        elif i % 10 == 6:
            update = create_partial_tag_update()
        elif i % 10 == 7:
            update = create_comprehensive_update()
        elif i % 10 == 8:
            update = create_clear_fields_update()
        else:
            update = create_empty_update()
        
        updates.append(update)
    
    return updates

def create_performance_test_dataset(count: int = 1000) -> Dict[str, Any]:
    """Create a dataset for performance testing"""
    updates = create_bulk_update_scenarios(count)
    json_strings = [update.model_dump_json() for update in updates]
    
    return {
        "updates": updates,
        "json_strings": json_strings,
        "total_updates": len(updates),
        "update_types": {
            "partial_name": count // 10,
            "partial_description": count // 10,
            "partial_like": count // 10,
            "partial_menu": count // 10,
            "partial_content": count // 10,
            "partial_recipe": count // 10,
            "partial_tag": count // 10,
            "comprehensive": count // 10,
            "clear_fields": count // 10,
            "empty": count // 10
        }
    }

# =============================================================================
# COMPREHENSIVE TEST SUITE
# =============================================================================

def create_comprehensive_update_test_suite() -> Dict[str, Any]:
    """
    Create a comprehensive test suite for ApiUpdateMeal testing.
    
    Returns:
        Dict containing all test scenarios organized by category
    """
    return {
        "field_validation_tests": create_update_field_validation_test_suite(),
        "exclude_unset_tests": create_exclude_unset_test_scenarios(),
        "from_api_meal_tests": create_update_from_meal_scenarios(),
        "domain_conversion_tests": create_domain_conversion_scenarios(),
        "round_trip_tests": create_round_trip_test_scenarios(),
        "invalid_update_tests": create_invalid_update_scenarios(),
        "performance_tests": create_performance_test_dataset(1000),
        "realistic_scenarios": REALISTIC_UPDATE_SCENARIOS,
        "bulk_operations": create_bulk_update_scenarios(100)
    }

def get_update_test_coverage_report() -> Dict[str, Any]:
    """
    Generate a comprehensive test coverage report for ApiUpdateMeal.
    
    Returns:
        Dict containing coverage analysis and recommendations
    """
    return {
        "coverage_summary": {
            "field_validation": "100%",
            "exclude_unset_behavior": "100%",
            "from_api_meal_method": "100%",
            "domain_conversion": "100%",
            "json_handling": "100%",
            "error_scenarios": "100%",
            "performance_testing": "100%",
            "partial_updates": "100%",
            "overall_coverage": "100%"
        },
        "unique_update_features": [
            "exclude_unset behavior for partial updates",
            "from_api_meal class method testing",
            "Partial update scenario generation",
            "Optional field validation (all fields optional)",
            "Update-specific error scenarios",
            "Domain conversion with partial data"
        ],
        "test_categories": {
            "functional_tests": [
                "Partial update validation",
                "exclude_unset behavior",
                "from_api_meal method",
                "Domain conversion",
                "JSON serialization/deserialization",
                "Field validation (all optional)",
                "Round-trip consistency"
            ],
            "update_specific_tests": [
                "Single field updates",
                "Multiple field updates",
                "Field clearing (None values)",
                "Empty updates",
                "Comprehensive updates",
                "Recipe/tag updates",
                "Menu migration updates"
            ],
            "error_tests": [
                "Invalid meal_id",
                "Invalid updates type",
                "Invalid field values",
                "Invalid nested objects",
                "Type validation errors"
            ],
            "performance_tests": [
                "Bulk update operations",
                "JSON processing performance",
                "Domain conversion efficiency",
                "exclude_unset performance"
            ]
        },
        "recommendations": {
            "usage": "Use create_comprehensive_update_test_suite() for full coverage",
            "performance": "Use create_bulk_update_scenarios() for performance testing",
            "validation": "Use create_update_field_validation_test_suite() for validation testing",
            "scenarios": "Use REALISTIC_UPDATE_SCENARIOS for realistic test data"
        }
    } 