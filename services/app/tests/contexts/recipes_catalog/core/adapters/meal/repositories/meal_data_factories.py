"""
Data factories for MealRepository testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- Validation logic for entity completeness
- Parametrized test scenarios for filtering
- Performance test scenarios with dataset expectations
- Specialized factory functions for different meal types
- ORM equivalents for all domain factory methods

All data follows the exact structure of Meal domain entities and their relationships.
Both domain and ORM variants are provided for comprehensive testing scenarios.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
# ORM model imports
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import TagSaModel
from src.contexts.recipes_catalog.core.adapters.name_search import StrProcessor

# =============================================================================
# STATIC COUNTERS FOR DETERMINISTIC IDS
# =============================================================================

_MEAL_COUNTER = 1
_TAG_COUNTER = 1
_RECIPE_COUNTER = 1


def reset_counters() -> None:
    """Reset all counters for test isolation"""
    global _MEAL_COUNTER, _TAG_COUNTER, _RECIPE_COUNTER
    _MEAL_COUNTER = 1
    _TAG_COUNTER = 1
    _RECIPE_COUNTER = 1


# =============================================================================
# MEAL DATA FACTORIES (DOMAIN)
# =============================================================================

def create_meal_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create meal kwargs with deterministic values and validation.
    
    Following seedwork pattern with static counters for consistent test behavior.
    All required entity attributes are guaranteed to be present.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required meal creation parameters
        
    Raises:
        ValueError: If invalid attribute combinations are provided
    """
    global _MEAL_COUNTER
    
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    final_kwargs = {
        "id": kwargs.get("id", f"meal_{_MEAL_COUNTER:03d}"),
        "name": kwargs.get("name", f"Test Meal {_MEAL_COUNTER}"),
        "author_id": kwargs.get("author_id", f"author_{(_MEAL_COUNTER % 5) + 1}"),  # Cycle through 5 authors
        "menu_id": kwargs.get("menu_id", None),  # Set to None to avoid foreign key constraint since menus don't exist in tests
        "description": kwargs.get("description", f"Test meal description {_MEAL_COUNTER}"),
        "notes": kwargs.get("notes", f"Test notes for meal {_MEAL_COUNTER}"),
        "like": kwargs.get("like", _MEAL_COUNTER % 3 == 0),  # Every 3rd meal is liked
        "image_url": kwargs.get("image_url", f"https://example.com/meal_{_MEAL_COUNTER}.jpg" if _MEAL_COUNTER % 2 == 0 else None),
        "created_at": kwargs.get("created_at", base_time + timedelta(hours=_MEAL_COUNTER)),
        "updated_at": kwargs.get("updated_at", base_time + timedelta(hours=_MEAL_COUNTER, minutes=30)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
        "recipes": kwargs.get("recipes", []),  # Will be populated separately if needed
        "tags": kwargs.get("tags", set()),  # Will be populated separately if needed
    }
    
    # Validation logic to ensure required attributes
    required_fields = ["id", "name", "author_id"]
    for field in required_fields:
        if not final_kwargs.get(field):
            raise ValueError(f"Required field '{field}' cannot be empty")
    
    # Validate author_id format
    if not isinstance(final_kwargs["author_id"], str) or not final_kwargs["author_id"]:
        raise ValueError("author_id must be a non-empty string")
    
    # Increment counter for next call
    _MEAL_COUNTER += 1
    
    return final_kwargs


def create_meal(**kwargs) -> Meal:
    """
    Create a Meal domain entity with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Meal domain entity
    """
    meal_kwargs = create_meal_kwargs(**kwargs)
    return Meal(**meal_kwargs)


# =============================================================================
# MEAL DATA FACTORIES (ORM)
# =============================================================================

def create_meal_orm_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create meal ORM kwargs with deterministic values.
    
    Similar to create_meal_kwargs but includes ORM-specific fields like preprocessed_name
    and nutritional calculation fields.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required ORM meal creation parameters
    """
    global _MEAL_COUNTER
    
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    final_kwargs = {
        "id": kwargs.get("id", f"meal_{_MEAL_COUNTER:03d}"),
        "name": kwargs.get("name", f"Test Meal {_MEAL_COUNTER}"),
        "preprocessed_name": kwargs.get("preprocessed_name", StrProcessor(f"Test Meal {_MEAL_COUNTER}").output),
        "author_id": kwargs.get("author_id", f"author_{(_MEAL_COUNTER % 5) + 1}"),
        "menu_id": kwargs.get("menu_id", None),
        "description": kwargs.get("description", f"Test meal description {_MEAL_COUNTER}"),
        "notes": kwargs.get("notes", f"Test notes for meal {_MEAL_COUNTER}"),
        "like": kwargs.get("like", _MEAL_COUNTER % 3 == 0),
        "image_url": kwargs.get("image_url", f"https://example.com/meal_{_MEAL_COUNTER}.jpg" if _MEAL_COUNTER % 2 == 0 else None),
        "total_time": kwargs.get("total_time", 30 + (_MEAL_COUNTER % 60)),  # 30-90 minutes
        "weight_in_grams": kwargs.get("weight_in_grams", 400 + (_MEAL_COUNTER % 400)),  # 400-800g
        "calorie_density": kwargs.get("calorie_density", 1.5 + (_MEAL_COUNTER % 2)),  # 1.5-3.5 cal/g
        "carbo_percentage": kwargs.get("carbo_percentage", 40.0 + (_MEAL_COUNTER % 20)),  # 40-60%
        "protein_percentage": kwargs.get("protein_percentage", 15.0 + (_MEAL_COUNTER % 15)),  # 15-30%
        "total_fat_percentage": kwargs.get("total_fat_percentage", 20.0 + (_MEAL_COUNTER % 20)),  # 20-40%
        "nutri_facts": kwargs.get("nutri_facts", None),  # Will be created if needed
        "created_at": kwargs.get("created_at", base_time + timedelta(hours=_MEAL_COUNTER)),
        "updated_at": kwargs.get("updated_at", base_time + timedelta(hours=_MEAL_COUNTER, minutes=30)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
        "recipes": kwargs.get("recipes", []),  # Will be populated separately if needed
        "tags": kwargs.get("tags", []),  # List for ORM relationships
    }
    
    # Validation logic
    required_fields = ["id", "name", "author_id"]
    for field in required_fields:
        if not final_kwargs.get(field):
            raise ValueError(f"Required field '{field}' cannot be empty")
    
    # Validate author_id format
    if not isinstance(final_kwargs["author_id"], str) or not final_kwargs["author_id"]:
        raise ValueError("author_id must be a non-empty string")
    
    # Increment counter for next call
    _MEAL_COUNTER += 1
    
    return final_kwargs


def create_meal_orm(**kwargs) -> MealSaModel:
    """
    Create a MealSaModel ORM instance with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        MealSaModel ORM instance
    """
    meal_kwargs = create_meal_orm_kwargs(**kwargs)
    return MealSaModel(**meal_kwargs)


# =============================================================================
# TAG DATA FACTORIES (DOMAIN)
# =============================================================================

def create_tag_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create tag kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with tag creation parameters
    """
    global _TAG_COUNTER
    
    # Predefined tag types for realistic test data
    tag_types = ["meal", "recipe", "product"]
    keys = ["category", "diet", "cuisine", "difficulty", "season"]
    values_by_key = {
        "category": ["breakfast", "lunch", "dinner", "snack", "dessert"],
        "diet": ["vegetarian", "vegan", "keto", "paleo", "mediterranean"],
        "cuisine": ["italian", "mexican", "asian", "american", "french"],
        "difficulty": ["easy", "medium", "hard"],
        "season": ["spring", "summer", "fall", "winter"]
    }
    
    key = keys[(_TAG_COUNTER - 1) % len(keys)]
    value = values_by_key[key][(_TAG_COUNTER - 1) % len(values_by_key[key])]
    
    final_kwargs = {
        "key": kwargs.get("key", key),
        "value": kwargs.get("value", value),
        "author_id": kwargs.get("author_id", f"author_{((_TAG_COUNTER - 1) % 5) + 1}"),
        "type": kwargs.get("type", tag_types[(_TAG_COUNTER - 1) % len(tag_types)]),
    }
    
    # Validation
    required_fields = ["key", "value", "author_id", "type"]
    for field in required_fields:
        if not final_kwargs.get(field):
            raise ValueError(f"Required tag field '{field}' cannot be empty")
    
    _TAG_COUNTER += 1
    return final_kwargs


def create_tag(**kwargs) -> Tag:
    """
    Create a Tag value object with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Tag value object
    """
    tag_kwargs = create_tag_kwargs(**kwargs)
    return Tag(**tag_kwargs)


# =============================================================================
# TAG DATA FACTORIES (ORM)
# =============================================================================

def create_tag_orm_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create tag ORM kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with ORM tag creation parameters
    """
    # Use the same logic as domain tags but without incrementing counter twice
    tag_kwargs = create_tag_kwargs(**kwargs)
    
    # ORM models use auto-increment for id, so we remove it from kwargs if present
    final_kwargs = {
        "key": kwargs.get("key", tag_kwargs["key"]),
        "value": kwargs.get("value", tag_kwargs["value"]),
        "author_id": kwargs.get("author_id", tag_kwargs["author_id"]),
        "type": kwargs.get("type", tag_kwargs["type"]),
    }
    # Keep the id field for testing purposes - TagSaModel has auto-increment but we can override
    
    return final_kwargs


def create_tag_orm(**kwargs) -> TagSaModel:
    """
    Create a TagSaModel ORM instance with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        TagSaModel ORM instance
    """
    tag_kwargs = create_tag_orm_kwargs(**kwargs)
    return TagSaModel(**tag_kwargs)


# =============================================================================
# SPECIALIZED FACTORY FUNCTIONS (DOMAIN)
# =============================================================================

def create_low_calorie_meal(**kwargs) -> Meal:
    """
    Create a meal with low calorie characteristics.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Meal with low calorie density and appropriate tags
    """
    final_kwargs = {
        "name": kwargs.get("name", "Low Calorie Healthy Meal"),
        "description": kwargs.get("description", "A nutritious meal with reduced calories"),
        "tags": kwargs.get("tags", {
            create_tag(key="diet", value="low-calorie", type="meal"),
            create_tag(key="category", value="health", type="meal")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "tags"]}
    }
    return create_meal(**final_kwargs)


def create_quick_meal(**kwargs) -> Meal:
    """
    Create a meal with quick preparation time.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Meal with short total_time and appropriate tags
    """
    final_kwargs = {
        "name": kwargs.get("name", "Quick & Easy Meal"),
        "description": kwargs.get("description", "Fast preparation meal for busy schedules"),
        "tags": kwargs.get("tags", {
            create_tag(key="difficulty", value="easy", type="meal"),
            create_tag(key="category", value="quick", type="meal")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "tags"]}
    }
    return create_meal(**final_kwargs)


def create_vegetarian_meal(**kwargs) -> Meal:
    """
    Create a vegetarian meal with appropriate tags.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Meal with vegetarian tags and characteristics
    """
    final_kwargs = {
        "name": kwargs.get("name", "Delicious Vegetarian Meal"),
        "description": kwargs.get("description", "Plant-based nutritious meal"),
        "tags": kwargs.get("tags", {
            create_tag(key="diet", value="vegetarian", type="meal"),
            create_tag(key="category", value="plant-based", type="meal")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "tags"]}
    }
    return create_meal(**final_kwargs)


def create_high_protein_meal(**kwargs) -> Meal:
    """
    Create a meal with high protein content.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Meal with high protein characteristics and tags
    """
    final_kwargs = {
        "name": kwargs.get("name", "High Protein Power Meal"),
        "description": kwargs.get("description", "Protein-rich meal for muscle building and recovery"),
        "tags": kwargs.get("tags", {
            create_tag(key="diet", value="high-protein", type="meal"),
            create_tag(key="category", value="fitness", type="meal")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "tags"]}
    }
    return create_meal(**final_kwargs)


def create_family_meal(**kwargs) -> Meal:
    """
    Create a meal suitable for families.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Meal with family-friendly characteristics
    """
    final_kwargs = {
        "name": kwargs.get("name", "Family Dinner Meal"),
        "description": kwargs.get("description", "Perfect meal for the whole family to enjoy together"),
        "like": kwargs.get("like", True),  # Families usually like their regular meals
        "tags": kwargs.get("tags", {
            create_tag(key="category", value="family", type="meal"),
            create_tag(key="difficulty", value="medium", type="meal")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "like", "tags"]}
    }
    return create_meal(**final_kwargs)


# =============================================================================
# SPECIALIZED FACTORY FUNCTIONS (ORM)
# =============================================================================

def create_low_calorie_meal_orm(**kwargs) -> MealSaModel:
    """
    Create a meal ORM instance with low calorie characteristics.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        MealSaModel with low calorie density and appropriate tags
    """
    final_kwargs = {
        "name": kwargs.get("name", "Low Calorie Healthy Meal"),
        "description": kwargs.get("description", "A nutritious meal with reduced calories"),
        "calorie_density": kwargs.get("calorie_density", 1.2),  # Low calorie density
        "tags": kwargs.get("tags", [
            create_tag_orm(key="diet", value="low-calorie", type="meal"),
            create_tag_orm(key="category", value="health", type="meal")
        ]),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "calorie_density", "tags"]}
    }
    return create_meal_orm(**final_kwargs)


def create_quick_meal_orm(**kwargs) -> MealSaModel:
    """
    Create a meal ORM instance with quick preparation time.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        MealSaModel with short total_time and appropriate tags
    """
    final_kwargs = {
        "name": kwargs.get("name", "Quick & Easy Meal"),
        "description": kwargs.get("description", "Fast preparation meal for busy schedules"),
        "total_time": kwargs.get("total_time", 15),  # Quick preparation
        "tags": kwargs.get("tags", [
            create_tag_orm(key="difficulty", value="easy", type="meal"),
            create_tag_orm(key="category", value="quick", type="meal")
        ]),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "total_time", "tags"]}
    }
    return create_meal_orm(**final_kwargs)


def create_vegetarian_meal_orm(**kwargs) -> MealSaModel:
    """
    Create a vegetarian meal ORM instance with appropriate tags.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        MealSaModel with vegetarian tags and characteristics
    """
    final_kwargs = {
        "name": kwargs.get("name", "Delicious Vegetarian Meal"),
        "description": kwargs.get("description", "Plant-based nutritious meal"),
        "tags": kwargs.get("tags", [
            create_tag_orm(key="diet", value="vegetarian", type="meal"),
            create_tag_orm(key="category", value="plant-based", type="meal")
        ]),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "tags"]}
    }
    return create_meal_orm(**final_kwargs)


def create_high_protein_meal_orm(**kwargs) -> MealSaModel:
    """
    Create a meal ORM instance with high protein content.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        MealSaModel with high protein characteristics and tags
    """
    final_kwargs = {
        "name": kwargs.get("name", "High Protein Power Meal"),
        "description": kwargs.get("description", "Protein-rich meal for muscle building and recovery"),
        "protein_percentage": kwargs.get("protein_percentage", 35.0),  # High protein
        "tags": kwargs.get("tags", [
            create_tag_orm(key="diet", value="high-protein", type="meal"),
            create_tag_orm(key="category", value="fitness", type="meal")
        ]),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "protein_percentage", "tags"]}
    }
    return create_meal_orm(**final_kwargs)


def create_family_meal_orm(**kwargs) -> MealSaModel:
    """
    Create a meal ORM instance suitable for families.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        MealSaModel with family-friendly characteristics
    """
    final_kwargs = {
        "name": kwargs.get("name", "Family Dinner Meal"),
        "description": kwargs.get("description", "Perfect meal for the whole family to enjoy together"),
        "like": kwargs.get("like", True),  # Families usually like their regular meals
        "tags": kwargs.get("tags", [
            create_tag_orm(key="category", value="family", type="meal"),
            create_tag_orm(key="difficulty", value="medium", type="meal")
        ]),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "like", "tags"]}
    }
    return create_meal_orm(**final_kwargs)


# =============================================================================
# PARAMETRIZED TEST SCENARIOS
# =============================================================================

def get_meal_filter_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for testing meal filtering.
    
    Note: total_time is a computed property in the Meal domain object based on recipes,
    so it's not included in meal_kwargs. The filtering still works because the database
    has a total_time column that gets populated separately.
    
    Returns:
        List of test scenarios with meal_kwargs, filter, and expected outcome
    """
    return [
        {
            "scenario_id": "total_time_gte_match",
            "meal_kwargs": {"name": "Long Cooking Meal", "total_time": 50},
            "filter": {"total_time_gte": 45},
            "should_match": True,
            "description": "Meal with recipes having long total_time should match gte filter of 45min"
        },
        {
            "scenario_id": "total_time_gte_no_match",
            "meal_kwargs": {"name": "Quick Meal", "total_time": 15},
            "filter": {"total_time_gte": 45},
            "should_match": False,
            "description": "Meal with recipes having short total_time should not match gte filter of 45min"
        },
        {
            "scenario_id": "total_time_lte_match",
            "meal_kwargs": {"name": "Quick Meal", "total_time": 15},
            "filter": {"total_time_lte": 45},
            "should_match": True,
            "description": "Meal with recipes having short total_time should match lte filter of 45min"
        },
        {
            "scenario_id": "calorie_density_gte_match",
            "meal_kwargs": {
                "name": "High Calorie Meal",
                "calorie_density": 2.0,
                "recipes": []
            },
            "filter": {"calorie_density_gte": 2.0},
            "should_match": True,
            "description": "High calorie density meal should match gte filter"
        },
        {
            "scenario_id": "like_filter_true",
            "meal_kwargs": {"like": True, "name": "Liked Meal"},
            "filter": {"like": True},
            "should_match": True,
            "description": "Liked meal should match like=True filter"
        },
        {
            "scenario_id": "like_filter_false",
            "meal_kwargs": {"like": False, "name": "Not Liked Meal"},
            "filter": {"like": True},
            "should_match": False,
            "description": "Not liked meal should not match like=True filter"
        },
        {
            "scenario_id": "author_id_match",
            "meal_kwargs": {"author_id": "test_author_123", "name": "Author Meal"},
            "filter": {"author_id": "test_author_123"},
            "should_match": True,
            "description": "Meal should match author_id filter"
        },
        {
            "scenario_id": "name_like_match",
            "meal_kwargs": {"name": "Delicious Pasta Meal"},
            "filter": {"name_like": "Pasta"},
            "should_match": True,
            "description": "Meal name containing 'Pasta' should match like filter"
        },
        {
            "scenario_id": "complex_filter_all_match",
            "meal_kwargs": {
                "like": True,
                "author_id": "complex_author",
                "name": "Complex Filter Test Meal",
                "total_time": 45
            },
            "filter": {
                "total_time_gte": 30,
                "total_time_lte": 60,
                "like": True,
                "author_id": "complex_author"
            },
            "should_match": True,
            "description": "Meal should match all filter conditions"
        },
        {
            "scenario_id": "complex_filter_partial_match",
            "meal_kwargs": {
                "like": True,
                "author_id": "complex_author",
                "name": "Partial Match Meal",
                "total_time": 61
            },
            "filter": {
                "total_time_gte": 30,
                "total_time_lte": 60,  # This may fail depending on recipes
                "like": True,
                "author_id": "complex_author"
            },
            "should_match": False,
            "description": "Meal should not match when one filter condition fails"
        }
    ]


def get_tag_filtering_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for testing complex tag filtering logic.
    
    Tests the complex AND/OR logic:
    - Different keys must ALL match (AND logic)
    - Multiple values for same key use OR logic
    - Exact key-value-author combinations
    
    Returns:
        List of tag filtering test scenarios
    """
    return [
        {
            "scenario_id": "single_tag_exact_match",
            "meal_tags": [
                {"key": "diet", "value": "vegetarian", "author_id": "author_1", "type": "meal"}
            ],
            "filter_tags": [("diet", "vegetarian", "author_1")],
            "should_match": True,
            "description": "Single tag exact match should work"
        },
        {
            "scenario_id": "single_tag_no_match_value",
            "meal_tags": [
                {"key": "diet", "value": "vegetarian", "author_id": "author_1", "type": "meal"}
            ],
            "filter_tags": [("diet", "vegan", "author_1")],
            "should_match": False,
            "description": "Different tag value should not match"
        },
        {
            "scenario_id": "single_tag_no_match_author",
            "meal_tags": [
                {"key": "diet", "value": "vegetarian", "author_id": "author_1", "type": "meal"}
            ],
            "filter_tags": [("diet", "vegetarian", "author_2")],
            "should_match": False,
            "description": "Different author_id should not match"
        },
        {
            "scenario_id": "multiple_values_same_key_or_logic",
            "meal_tags": [
                {"key": "cuisine", "value": "italian", "author_id": "author_1", "type": "meal"}
            ],
            "filter_tags": [
                ("cuisine", "italian", "author_1"),
                ("cuisine", "mexican", "author_1")  # OR with italian
            ],
            "should_match": True,
            "description": "Multiple values for same key should use OR logic"
        },
        {
            "scenario_id": "multiple_keys_and_logic",
            "meal_tags": [
                {"key": "diet", "value": "vegetarian", "author_id": "author_1", "type": "meal"},
                {"key": "cuisine", "value": "italian", "author_id": "author_1", "type": "meal"}
            ],
            "filter_tags": [
                ("diet", "vegetarian", "author_1"),
                ("cuisine", "italian", "author_1")
            ],
            "should_match": True,
            "description": "Multiple different keys should use AND logic (all must match)"
        },
        {
            "scenario_id": "multiple_keys_and_logic_fail",
            "meal_tags": [
                {"key": "diet", "value": "vegetarian", "author_id": "author_1", "type": "meal"},
                {"key": "cuisine", "value": "mexican", "author_id": "author_1", "type": "meal"}  # Wrong value
            ],
            "filter_tags": [
                ("diet", "vegetarian", "author_1"),
                ("cuisine", "italian", "author_1")  # This won't match
            ],
            "should_match": False,
            "description": "AND logic should fail if any key doesn't match"
        },
        {
            "scenario_id": "complex_combination",
            "meal_tags": [
                {"key": "diet", "value": "vegetarian", "author_id": "author_1", "type": "meal"},
                {"key": "cuisine", "value": "italian", "author_id": "author_1", "type": "meal"},
                {"key": "difficulty", "value": "easy", "author_id": "author_1", "type": "meal"}
            ],
            "filter_tags": [
                ("diet", "vegetarian", "author_1"),
                ("diet", "vegan", "author_1"),  # OR with vegetarian
                ("cuisine", "italian", "author_1"),
                ("cuisine", "french", "author_1"),  # OR with italian
                ("difficulty", "easy", "author_1")
            ],
            "should_match": True,
            "description": "Complex AND/OR combination should work correctly"
        },
        {
            "scenario_id": "mixed_authors_same_meal",
            "meal_tags": [
                {"key": "diet", "value": "vegetarian", "author_id": "author_1", "type": "meal"},
                {"key": "cuisine", "value": "italian", "author_id": "author_2", "type": "meal"}
            ],
            "filter_tags": [
                ("diet", "vegetarian", "author_1"),
                ("cuisine", "italian", "author_2")  # Different author
            ],
            "should_match": True,
            "description": "Tags from different authors on same meal should work"
        }
    ]


def get_performance_test_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for performance testing with dataset size expectations.
    
    Returns:
        List of performance test scenarios with entity counts and time limits
    """
    return [
        {
            "scenario_id": "small_dataset_basic_query",
            "entity_count": 100,
            "operation": "basic_query",
            "max_duration_seconds": 0.5,
            "description": "Basic query on 100 meals should complete in < 0.5s"
        },
        {
            "scenario_id": "medium_dataset_basic_query",
            "entity_count": 500,
            "operation": "basic_query",
            "max_duration_seconds": 1.0,
            "description": "Basic query on 500 meals should complete in < 1.0s"
        },
        {
            "scenario_id": "large_dataset_basic_query",
            "entity_count": 1000,
            "operation": "basic_query",
            "max_duration_seconds": 2.0,
            "description": "Basic query on 1000 meals should complete in < 2.0s"
        },
        {
            "scenario_id": "small_dataset_tag_filtering",
            "entity_count": 100,
            "operation": "tag_filtering",
            "max_duration_seconds": 1.0,
            "description": "Tag filtering on 100 meals should complete in < 1.0s"
        },
        {
            "scenario_id": "medium_dataset_tag_filtering",
            "entity_count": 500,
            "operation": "tag_filtering",
            "max_duration_seconds": 2.0,
            "description": "Tag filtering on 500 meals should complete in < 2.0s"
        },
        {
            "scenario_id": "large_dataset_tag_filtering",
            "entity_count": 1000,
            "operation": "tag_filtering",
            "max_duration_seconds": 3.0,
            "description": "Tag filtering on 1000 meals should complete in < 3.0s"
        },
        {
            "scenario_id": "complex_query_with_joins",
            "entity_count": 500,
            "operation": "complex_query",
            "max_duration_seconds": 2.5,
            "description": "Complex query with joins should complete in < 2.5s"
        },
        {
            "scenario_id": "bulk_insert_performance",
            "entity_count": 1000,
            "operation": "bulk_insert",
            "max_duration_seconds": 5.0,
            "max_per_entity_ms": 5,
            "description": "Bulk insert of 1000 meals should complete in < 5s (< 5ms per entity)"
        }
    ]


# =============================================================================
# HELPER FUNCTIONS FOR TEST SETUP (DOMAIN & ORM)
# =============================================================================

def create_meals_with_tags(count: int = 3, tags_per_meal: int = 2) -> List[Meal]:
    """Create multiple meals with various tag combinations for testing"""
    meals = []
    
    # Create a pool of unique tags first to avoid potential duplicates
    unique_tags = {}  # Key: (key, value, author_id, type), Value: Tag
    
    # Calculate maximum possible unique tags
    tag_types = ["meal", "recipe", "product"]
    keys = ["category", "diet", "cuisine", "difficulty", "season"]
    values_by_key = {
        "category": ["breakfast", "lunch", "dinner", "snack", "dessert"],
        "diet": ["vegetarian", "vegan", "keto", "paleo", "mediterranean"],
        "cuisine": ["italian", "mexican", "asian", "american", "french"],
        "difficulty": ["easy", "medium", "hard"],
        "season": ["spring", "summer", "fall", "winter"]
    }
    max_authors = 5  # author_1 to author_5
    
    # Pre-create unique tags if we need them
    if tags_per_meal > 0:
        # Create unique tag combinations as needed
        for meal_idx in range(count):
            for tag_idx in range(tags_per_meal):
                # Use a deterministic approach to create unique combinations
                total_tag_index = meal_idx * tags_per_meal + tag_idx
                
                # Cycle through combinations to maximize uniqueness
                key_idx = total_tag_index % len(keys)
                key = keys[key_idx]
                
                value_idx = (total_tag_index // len(keys)) % len(values_by_key[key])
                value = values_by_key[key][value_idx]
                
                author_idx = (total_tag_index // (len(keys) * max(len(v) for v in values_by_key.values()))) % max_authors
                author_id = f"author_{author_idx + 1}"
                
                type_idx = (total_tag_index // (len(keys) * max(len(v) for v in values_by_key.values()) * max_authors)) % len(tag_types)
                tag_type = tag_types[type_idx]
                
                # Create unique combination key
                tag_key = (key, value, author_id, tag_type)
                
                # Only create if we haven't seen this combination before
                if tag_key not in unique_tags:
                    tag = create_tag(key=key, value=value, author_id=author_id, type=tag_type)
                    unique_tags[tag_key] = tag
    
    # Now create meals and assign tags from the unique pool
    unique_tag_list = list(unique_tags.values())
    
    for i in range(count):
        # Create tags for this meal
        tags = set()
        if tags_per_meal > 0 and unique_tag_list:
            # Select tags for this meal from the unique pool
            start_idx = (i * tags_per_meal) % len(unique_tag_list)
            for j in range(min(tags_per_meal, len(unique_tag_list))):
                tag_idx = (start_idx + j) % len(unique_tag_list)
                tags.add(unique_tag_list[tag_idx])
        
        meal_kwargs = create_meal_kwargs()
        meal_kwargs["tags"] = tags
        meal = create_meal(**meal_kwargs)
        meals.append(meal)
    return meals


def create_meals_with_tags_orm(count: int = 3, tags_per_meal: int = 2) -> List[MealSaModel]:
    """Create multiple ORM meals with various tag combinations for testing"""
    meals = []
    
    # Create a pool of unique tags first to avoid constraint violations
    unique_tags = {}  # Key: (key, value, author_id, type), Value: TagSaModel
    
    # Calculate maximum possible unique tags
    tag_types = ["meal", "recipe", "product"]
    keys = ["category", "diet", "cuisine", "difficulty", "season"]
    values_by_key = {
        "category": ["breakfast", "lunch", "dinner", "snack", "dessert"],
        "diet": ["vegetarian", "vegan", "keto", "paleo", "mediterranean"],
        "cuisine": ["italian", "mexican", "asian", "american", "french"],
        "difficulty": ["easy", "medium", "hard"],
        "season": ["spring", "summer", "fall", "winter"]
    }
    max_authors = 5  # author_1 to author_5
    
    # Pre-create unique tags if we need them
    if tags_per_meal > 0:
        # Create unique tag combinations as needed
        for meal_idx in range(count):
            for tag_idx in range(tags_per_meal):
                # Use a deterministic approach to create unique combinations
                total_tag_index = meal_idx * tags_per_meal + tag_idx
                
                # Cycle through combinations to maximize uniqueness
                key_idx = total_tag_index % len(keys)
                key = keys[key_idx]
                
                value_idx = (total_tag_index // len(keys)) % len(values_by_key[key])
                value = values_by_key[key][value_idx]
                
                author_idx = (total_tag_index // (len(keys) * max(len(v) for v in values_by_key.values()))) % max_authors
                author_id = f"author_{author_idx + 1}"
                
                type_idx = (total_tag_index // (len(keys) * max(len(v) for v in values_by_key.values()) * max_authors)) % len(tag_types)
                tag_type = tag_types[type_idx]
                
                # Create unique combination key
                tag_key = (key, value, author_id, tag_type)
                
                # Only create if we haven't seen this combination before
                if tag_key not in unique_tags:
                    tag = create_tag_orm(key=key, value=value, author_id=author_id, type=tag_type)
                    unique_tags[tag_key] = tag
    
    # Now create meals and assign tags from the unique pool
    unique_tag_list = list(unique_tags.values())
    
    for i in range(count):
        # Create tags for this meal
        tags = []
        if tags_per_meal > 0 and unique_tag_list:
            # Select tags for this meal from the unique pool
            start_idx = (i * tags_per_meal) % len(unique_tag_list)
            for j in range(min(tags_per_meal, len(unique_tag_list))):
                tag_idx = (start_idx + j) % len(unique_tag_list)
                tags.append(unique_tag_list[tag_idx])
        
        meal_kwargs = create_meal_orm_kwargs()
        meal_kwargs["tags"] = tags
        meal = create_meal_orm(**meal_kwargs)
        meals.append(meal)
    return meals


def create_test_dataset(meal_count: int = 100, tags_per_meal: int = 0) -> Dict[str, Any]:
    """Create a dataset of meals for performance testing"""
    meals = []
    all_tags = []
    
    # Create a pool of unique tags first to avoid potential duplicates
    unique_tags = {}  # Key: (key, value, author_id, type), Value: Tag
    
    # Calculate maximum possible unique tags
    tag_types = ["meal", "recipe", "product"]
    keys = ["category", "diet", "cuisine", "difficulty", "season"]
    values_by_key = {
        "category": ["breakfast", "lunch", "dinner", "snack", "dessert"],
        "diet": ["vegetarian", "vegan", "keto", "paleo", "mediterranean"],
        "cuisine": ["italian", "mexican", "asian", "american", "french"],
        "difficulty": ["easy", "medium", "hard"],
        "season": ["spring", "summer", "fall", "winter"]
    }
    max_authors = 5  # author_1 to author_5
    
    # Pre-create unique tags if we need them
    if tags_per_meal > 0:
        # Create unique tag combinations as needed
        for meal_idx in range(meal_count):
            for tag_idx in range(tags_per_meal):
                # Use a deterministic approach to create unique combinations
                total_tag_index = meal_idx * tags_per_meal + tag_idx
                
                # Cycle through combinations to maximize uniqueness
                key_idx = total_tag_index % len(keys)
                key = keys[key_idx]
                
                value_idx = (total_tag_index // len(keys)) % len(values_by_key[key])
                value = values_by_key[key][value_idx]
                
                author_idx = (total_tag_index // (len(keys) * max(len(v) for v in values_by_key.values()))) % max_authors
                author_id = f"author_{author_idx + 1}"
                
                type_idx = (total_tag_index // (len(keys) * max(len(v) for v in values_by_key.values()) * max_authors)) % len(tag_types)
                tag_type = tag_types[type_idx]
                
                # Create unique combination key
                tag_key = (key, value, author_id, tag_type)
                
                # Only create if we haven't seen this combination before
                if tag_key not in unique_tags:
                    tag = create_tag(key=key, value=value, author_id=author_id, type=tag_type)
                    unique_tags[tag_key] = tag
                    all_tags.append(tag)
    
    # Now create meals and assign tags from the unique pool
    unique_tag_list = list(unique_tags.values())
    
    for i in range(meal_count):
        # Create tags for this meal if requested
        tags = set()
        if tags_per_meal > 0 and unique_tag_list:
            # Select tags for this meal from the unique pool
            start_idx = (i * tags_per_meal) % len(unique_tag_list)
            for j in range(min(tags_per_meal, len(unique_tag_list))):
                tag_idx = (start_idx + j) % len(unique_tag_list)
                tags.add(unique_tag_list[tag_idx])
        
        meal_kwargs = create_meal_kwargs()
        if tags:
            meal_kwargs["tags"] = tags
        meal = create_meal(**meal_kwargs)
        meals.append(meal)
    
    return {
        "meals": meals,
        "all_tags": all_tags
    }


def create_test_dataset_orm(meal_count: int = 100, tags_per_meal: int = 0) -> Dict[str, Any]:
    """Create a dataset of ORM meals for performance testing"""
    meals = []
    all_tags = []
    
    # Create a pool of unique tags first to avoid constraint violations
    unique_tags = {}  # Key: (key, value, author_id, type), Value: TagSaModel
    
    # Calculate maximum possible unique tags
    tag_types = ["meal", "recipe", "product"]
    keys = ["category", "diet", "cuisine", "difficulty", "season"]
    values_by_key = {
        "category": ["breakfast", "lunch", "dinner", "snack", "dessert"],
        "diet": ["vegetarian", "vegan", "keto", "paleo", "mediterranean"],
        "cuisine": ["italian", "mexican", "asian", "american", "french"],
        "difficulty": ["easy", "medium", "hard"],
        "season": ["spring", "summer", "fall", "winter"]
    }
    max_authors = 5  # author_1 to author_5
    
    # Pre-create unique tags if we need them
    if tags_per_meal > 0:
        # Create unique tag combinations as needed
        for meal_idx in range(meal_count):
            for tag_idx in range(tags_per_meal):
                # Use a deterministic approach to create unique combinations
                total_tag_index = meal_idx * tags_per_meal + tag_idx
                
                # Cycle through combinations to maximize uniqueness
                key_idx = total_tag_index % len(keys)
                key = keys[key_idx]
                
                value_idx = (total_tag_index // len(keys)) % len(values_by_key[key])
                value = values_by_key[key][value_idx]
                
                author_idx = (total_tag_index // (len(keys) * max(len(v) for v in values_by_key.values()))) % max_authors
                author_id = f"author_{author_idx + 1}"
                
                type_idx = (total_tag_index // (len(keys) * max(len(v) for v in values_by_key.values()) * max_authors)) % len(tag_types)
                tag_type = tag_types[type_idx]
                
                # Create unique combination key
                tag_key = (key, value, author_id, tag_type)
                
                # Only create if we haven't seen this combination before
                if tag_key not in unique_tags:
                    tag = create_tag_orm(key=key, value=value, author_id=author_id, type=tag_type)
                    unique_tags[tag_key] = tag
                    all_tags.append(tag)
    
    # Now create meals and assign tags from the unique pool
    unique_tag_list = list(unique_tags.values())
    
    for i in range(meal_count):
        # Create tags for this meal if requested
        tags = []
        if tags_per_meal > 0 and unique_tag_list:
            # Select tags for this meal from the unique pool
            start_idx = (i * tags_per_meal) % len(unique_tag_list)
            for j in range(min(tags_per_meal, len(unique_tag_list))):
                tag_idx = (start_idx + j) % len(unique_tag_list)
                tags.append(unique_tag_list[tag_idx])
        
        meal_kwargs = create_meal_orm_kwargs()
        if tags:
            meal_kwargs["tags"] = tags
        meal = create_meal_orm(**meal_kwargs)
        meals.append(meal)
    
    return {
        "meals": meals,
        "all_tags": all_tags
    } 