# =============================================================================
# PARAMETRIZED TEST SCENARIOS
# =============================================================================

from datetime import datetime
from typing import Any


def get_client_filter_scenarios() -> list[dict[str, Any]]:
    """
    Get predefined scenarios for testing client filtering.
    
    Returns:
        List of test scenarios with client_kwargs, filter, and expected outcome
    """
    return [
        {
            "scenario_id": "author_id_match",
            "client_kwargs": {"author_id": "test_author_123"},
            "filter": {"author_id": "test_author_123"},
            "should_match": True,
            "description": "Client should match author_id filter"
        },
        {
            "scenario_id": "author_id_no_match",
            "client_kwargs": {"author_id": "test_author_123"},
            "filter": {"author_id": "different_author"},
            "should_match": False,
            "description": "Client should not match different author_id"
        },
        {
            "scenario_id": "created_at_gte_match",
            "client_kwargs": {"created_at": datetime(2024, 6, 1)},
            "filter": {"created_at_gte": datetime(2024, 5, 1)},
            "should_match": True,
            "description": "Client created after filter date should match"
        },
        {
            "scenario_id": "created_at_gte_no_match",
            "client_kwargs": {"created_at": datetime(2024, 4, 1)},
            "filter": {"created_at_gte": datetime(2024, 5, 1)},
            "should_match": False,
            "description": "Client created before filter date should not match"
        },
        {
            "scenario_id": "discarded_filter_false",
            "client_kwargs": {"discarded": False},
            "filter": {"discarded": False},
            "should_match": True,
            "description": "Non-discarded client should match discarded=False filter"
        },
        {
            "scenario_id": "discarded_filter_true",
            "client_kwargs": {"discarded": True},
            "filter": {"discarded": False},
            "should_match": False,
            "description": "Discarded client should not match discarded=False filter"
        }
    ]


def get_client_tag_filtering_scenarios() -> list[dict[str, Any]]:
    """
    Get predefined scenarios for testing complex client tag filtering logic.
    
    Returns:
        List of tag filtering test scenarios
    """
    return [
        {
            "scenario_id": "single_client_tag_match",
            "client_tags": [
                {"key": "category", "value": "restaurant", "author_id": "author_1", "type": "client"}
            ],
            "filter_tags": [("category", "restaurant", "author_1")],
            "should_match": True,
            "description": "Single client tag exact match should work"
        },
        {
            "scenario_id": "multiple_client_tags_and_logic",
            "client_tags": [
                {"key": "category", "value": "restaurant", "author_id": "author_1", "type": "client"},
                {"key": "size", "value": "large", "author_id": "author_1", "type": "client"}
            ],
            "filter_tags": [
                ("category", "restaurant", "author_1"),
                ("size", "large", "author_1")
            ],
            "should_match": True,
            "description": "Multiple different keys should use AND logic (all must match)"
        },
        {
            "scenario_id": "client_tags_or_logic",
            "client_tags": [
                {"key": "industry", "value": "hospitality", "author_id": "author_1", "type": "client"}
            ],
            "filter_tags": [
                ("industry", "hospitality", "author_1"),
                ("industry", "healthcare", "author_1")  # OR with hospitality
            ],
            "should_match": True,
            "description": "Multiple values for same key should use OR logic"
        }
    ]
