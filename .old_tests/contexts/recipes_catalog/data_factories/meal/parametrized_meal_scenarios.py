# =============================================================================
# PARAMETRIZED TEST SCENARIOS
# =============================================================================

from typing import Any


def get_meal_filter_scenarios() -> list[dict[str, Any]]:
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


def get_tag_filtering_scenarios() -> list[dict[str, Any]]:
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


def get_performance_test_scenarios() -> list[dict[str, Any]]:
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