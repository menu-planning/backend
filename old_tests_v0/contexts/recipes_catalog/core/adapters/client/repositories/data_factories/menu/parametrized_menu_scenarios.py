
# =============================================================================
# PARAMETRIZED TEST SCENARIOS
# =============================================================================

from datetime import datetime
from typing import Any


def get_menu_filter_scenarios() -> list[dict[str, Any]]:
    """
    Get predefined scenarios for testing menu filtering.
    
    Returns:
        List of test scenarios with menu_kwargs, filter, and expected outcome
    """
    return [
        {
            "scenario_id": "author_id_match",
            "menu_kwargs": {"author_id": "test_author_123"},
            "filter": {"author_id": "test_author_123"},
            "should_match": True,
            "description": "Menu should match author_id filter"
        },
        {
            "scenario_id": "client_id_match",
            "menu_kwargs": {"client_id": "test_client_456"},
            "filter": {"client_id": "test_client_456"},
            "should_match": True,
            "description": "Menu should match client_id filter"
        },
        {
            "scenario_id": "created_at_gte_match",
            "menu_kwargs": {"created_at": datetime(2024, 6, 1)},
            "filter": {"created_at_gte": datetime(2024, 5, 1)},
            "should_match": True,
            "description": "Menu created after filter date should match"
        },
        {
            "scenario_id": "description_like_match",
            "menu_kwargs": {"description": "Special wedding menu with gourmet dishes"},
            "filter": {"description_like": "wedding"},
            "should_match": True,
            "description": "Menu description containing 'wedding' should match like filter"
        },
        {
            "scenario_id": "complex_filter_match",
            "menu_kwargs": {
                "author_id": "complex_author",
                "client_id": "complex_client",
                "created_at": datetime(2024, 6, 15)
            },
            "filter": {
                "author_id": "complex_author",
                "client_id": "complex_client",
                "created_at_gte": datetime(2024, 6, 1)
            },
            "should_match": True,
            "description": "Menu should match all filter conditions"
        }
    ]


def get_menu_tag_filtering_scenarios() -> list[dict[str, Any]]:
    """
    Get predefined scenarios for testing complex menu tag filtering logic.
    
    Returns:
        List of tag filtering test scenarios
    """
    return [
        {
            "scenario_id": "single_menu_tag_match",
            "menu_tags": [
                {"key": "type", "value": "weekly", "author_id": "author_1", "type": "menu"}
            ],
            "filter_tags": [("type", "weekly", "author_1")],
            "should_match": True,
            "description": "Single menu tag exact match should work"
        },
        {
            "scenario_id": "multiple_menu_tags_and_logic",
            "menu_tags": [
                {"key": "type", "value": "special", "author_id": "author_1", "type": "menu"},
                {"key": "event", "value": "wedding", "author_id": "author_1", "type": "menu"}
            ],
            "filter_tags": [
                ("type", "special", "author_1"),
                ("event", "wedding", "author_1")
            ],
            "should_match": True,
            "description": "Multiple different keys should use AND logic (all must match)"
        },
        {
            "scenario_id": "menu_dietary_tags_or_logic",
            "menu_tags": [
                {"key": "dietary", "value": "vegetarian", "author_id": "author_1", "type": "menu"}
            ],
            "filter_tags": [
                ("dietary", "vegetarian", "author_1"),
                ("dietary", "vegan", "author_1")  # OR with vegetarian
            ],
            "should_match": True,
            "description": "Multiple values for same key should use OR logic"
        }
    ]