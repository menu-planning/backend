"""
Data factories for ApiRating testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- JSON serialization/deserialization testing with model_validate_json and model_dump_json
- Parametrized test scenarios for rating validation
- Performance test scenarios with dataset expectations
- Specialized factory functions for different rating types
- Comprehensive attribute validation using check_missing_attributes
- Realistic data sets for production-like testing

All data follows the exact structure of ApiRating API entities and their validation rules.
Includes extensive testing for Pydantic model validation, JSON handling, and edge cases.
"""

import json
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import (
    ApiRating,
)
from src.contexts.recipes_catalog.core.domain.meal.value_objects.rating import Rating
from tests.utils.counter_manager import get_next_api_rating_id

# Import check_missing_attributes for validation
from tests.utils.utils import check_missing_attributes

# =============================================================================
# REALISTIC DATA SETS FOR PRODUCTION-LIKE TESTING
# =============================================================================

REALISTIC_RATING_COMMENTS = [
    "Absolutely delicious! The flavors were perfectly balanced and the recipe was easy to follow.",
    "Great recipe, but took longer than expected. The taste was worth the wait though.",
    "Perfect for a quick weeknight dinner. My family loved it!",
    "Good recipe overall, but I'd add more seasoning next time.",
    "Amazing! This has become our go-to recipe for special occasions.",
    "Simple ingredients but incredible results. Highly recommend!",
    "The instructions were clear and the final result was restaurant-quality.",
    "Love this recipe! It's become a regular in our meal rotation.",
    "Excellent balance of flavors. Even my picky kids enjoyed it.",
    "Outstanding recipe! The preparation time was accurate and the taste was phenomenal.",
    None,  # Some ratings don't have comments
    "",  # Empty comments should be handled
    "Quick and easy!",  # Short comments
    "This recipe changed my life! I've made it dozens of times and it never gets old. The combination of ingredients is perfect and the cooking method produces consistent results every time.",  # Long comments
]

REALISTIC_RATING_SCENARIOS = [
    {"taste": 5, "convenience": 5, "comment": "Perfect recipe in every way!"},
    {"taste": 4, "convenience": 5, "comment": "Great taste, super easy to make"},
    {"taste": 5, "convenience": 3, "comment": "Amazing flavor but takes some time"},
    {
        "taste": 3,
        "convenience": 5,
        "comment": "Quick and easy but flavor could be better",
    },
    {"taste": 4, "convenience": 4, "comment": "Good all-around recipe"},
    {"taste": 2, "convenience": 4, "comment": "Easy to make but not very tasty"},
    {
        "taste": 5,
        "convenience": 2,
        "comment": "Incredible taste but very time-consuming",
    },
    {"taste": 1, "convenience": 1, "comment": "Not worth the effort"},
    {"taste": 5, "convenience": 5, "comment": None},  # No comment
    {"taste": 3, "convenience": 3, "comment": ""},  # Empty comment
]

# =============================================================================
# API RATING DATA FACTORIES
# =============================================================================


def create_api_rating_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create ApiRating kwargs with deterministic values and comprehensive validation.

    Uses check_missing_attributes to ensure completeness and generates
    realistic test data for comprehensive API testing.

    Args:
        **kwargs: Override any default values

    Returns:
        Dict with all required ApiRating creation parameters
    """

    # Get current counter value
    rating_counter = get_next_api_rating_id()

    # Get realistic rating scenario for deterministic values
    scenario = REALISTIC_RATING_SCENARIOS[
        (rating_counter - 1) % len(REALISTIC_RATING_SCENARIOS)
    ]
    comment = REALISTIC_RATING_COMMENTS[
        (rating_counter - 1) % len(REALISTIC_RATING_COMMENTS)
    ]

    final_kwargs = {
        "user_id": kwargs.get("user_id", str(uuid4())),
        "recipe_id": kwargs.get("recipe_id", str(uuid4())),
        "taste": kwargs.get("taste", scenario["taste"]),
        "convenience": kwargs.get("convenience", scenario["convenience"]),
        "comment": kwargs.get("comment", comment),
    }

    # Allow override of any attribute
    final_kwargs.update(kwargs)

    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(ApiRating, final_kwargs)
    missing = set(missing) - {
        "convert",
        "model_computed_fields",
        "model_config",
        "model_fields",
    }
    assert not missing, f"Missing attributes for ApiRating: {missing}"

    return final_kwargs


def create_api_rating(**kwargs) -> ApiRating:
    """
    Create an ApiRating instance with deterministic data and validation.

    Args:
        **kwargs: Override any default values

    Returns:
        ApiRating instance with comprehensive validation
    """
    rating_kwargs = create_api_rating_kwargs(**kwargs)
    return ApiRating(**rating_kwargs)


def create_api_rating_from_json(json_data: str | None = None, **kwargs) -> ApiRating:
    """
    Create an ApiRating instance from JSON using model_validate_json.

    This tests Pydantic's JSON validation and parsing capabilities.

    Args:
        json_data: JSON string to parse (if None, generates from kwargs)
        **kwargs: Override any default values

    Returns:
        ApiRating instance created from JSON
    """
    if json_data is None:
        rating_kwargs = create_api_rating_kwargs(**kwargs)
        json_data = json.dumps(rating_kwargs)

    return ApiRating.model_validate_json(json_data)


def create_api_rating_json(**kwargs) -> str:
    """
    Create JSON representation of ApiRating using model_dump_json.

    This tests Pydantic's JSON serialization capabilities.

    Args:
        **kwargs: Override any default values

    Returns:
        JSON string representation of ApiRating
    """
    rating = create_api_rating(**kwargs)
    return rating.model_dump_json()


# =============================================================================
# SPECIALIZED FACTORY FUNCTIONS
# =============================================================================


def create_excellent_rating(**kwargs) -> ApiRating:
    """
    Create a rating with excellent scores (5/5) and positive comment.

    Args:
        **kwargs: Override any default values

    Returns:
        ApiRating with high scores and positive feedback
    """
    final_kwargs = {
        "taste": kwargs.get("taste", 5),
        "convenience": kwargs.get("convenience", 5),
        "comment": kwargs.get(
            "comment",
            "Absolutely perfect! This recipe exceeded all expectations. The flavors were incredible and it was so easy to make. Will definitely make again!",
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k not in ["taste", "convenience", "comment"]
        },
    }
    return create_api_rating(**final_kwargs)


def create_poor_rating(**kwargs) -> ApiRating:
    """
    Create a rating with poor scores (1/5) and negative comment.

    Args:
        **kwargs: Override any default values

    Returns:
        ApiRating with low scores and negative feedback
    """
    final_kwargs = {
        "taste": kwargs.get("taste", 1),
        "convenience": kwargs.get("convenience", 1),
        "comment": kwargs.get(
            "comment",
            "Very disappointed. The taste was bland and the recipe was confusing. Too much effort for such poor results.",
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k not in ["taste", "convenience", "comment"]
        },
    }
    return create_api_rating(**final_kwargs)


def create_mixed_rating(**kwargs) -> ApiRating:
    """
    Create a rating with mixed scores (taste high, convenience low).

    Args:
        **kwargs: Override any default values

    Returns:
        ApiRating with mixed feedback
    """
    final_kwargs = {
        "taste": kwargs.get("taste", 5),
        "convenience": kwargs.get("convenience", 2),
        "comment": kwargs.get(
            "comment",
            "Amazing flavors but very time-consuming and complex. Worth it for special occasions but not for weeknight dinners.",
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k not in ["taste", "convenience", "comment"]
        },
    }
    return create_api_rating(**final_kwargs)


def create_rating_without_comment(**kwargs) -> ApiRating:
    """
    Create a rating without any comment.

    Args:
        **kwargs: Override any default values

    Returns:
        ApiRating with no comment
    """
    final_kwargs = {
        "comment": kwargs.get("comment"),
        **{k: v for k, v in kwargs.items() if k != "comment"},
    }
    return create_api_rating(**final_kwargs)


def create_rating_with_empty_comment(**kwargs) -> ApiRating:
    """
    Create a rating with an empty comment.

    Args:
        **kwargs: Override any default values

    Returns:
        ApiRating with empty comment
    """
    final_kwargs = {
        "comment": kwargs.get("comment", ""),
        **{k: v for k, v in kwargs.items() if k != "comment"},
    }
    return create_api_rating(**final_kwargs)


def create_rating_with_max_comment(**kwargs) -> ApiRating:
    """
    Create a rating with maximum allowed comment length (1000 chars).

    Args:
        **kwargs: Override any default values

    Returns:
        ApiRating with maximum length comment
    """
    max_comment = (
        "This is an extremely detailed review that tests the maximum comment length limit. "
        * 12
    )  # Creates ~996 chars
    max_comment = max_comment[:1000]  # Ensure exactly 1000 chars

    final_kwargs = {
        "comment": kwargs.get("comment", max_comment),
        **{k: v for k, v in kwargs.items() if k != "comment"},
    }
    return create_api_rating(**final_kwargs)


def create_quick_easy_rating(**kwargs) -> ApiRating:
    """
    Create a rating emphasizing convenience over taste.

    Args:
        **kwargs: Override any default values

    Returns:
        ApiRating with high convenience rating
    """
    final_kwargs = {
        "taste": kwargs.get("taste", 3),
        "convenience": kwargs.get("convenience", 5),
        "comment": kwargs.get(
            "comment",
            "Super quick and easy! Perfect for busy weeknights. Taste is decent but the convenience makes up for it.",
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k not in ["taste", "convenience", "comment"]
        },
    }
    return create_api_rating(**final_kwargs)


def create_gourmet_rating(**kwargs) -> ApiRating:
    """
    Create a rating emphasizing taste over convenience.

    Args:
        **kwargs: Override any default values

    Returns:
        ApiRating with high taste rating
    """
    final_kwargs = {
        "taste": kwargs.get("taste", 5),
        "convenience": kwargs.get("convenience", 2),
        "comment": kwargs.get(
            "comment",
            "Exceptional flavor profile! This recipe produces restaurant-quality results but requires time and skill. Worth every minute.",
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k not in ["taste", "convenience", "comment"]
        },
    }
    return create_api_rating(**final_kwargs)


# =============================================================================
# HELPER FUNCTIONS FOR TEST SETUP
# =============================================================================


def create_api_ratings_with_different_users(count: int = 5) -> list[ApiRating]:
    """Create multiple ratings from different users for testing"""
    ratings = []
    base_recipe_id = str(uuid4())

    for i in range(count):
        rating_kwargs = create_api_rating_kwargs()
        rating_kwargs["recipe_id"] = base_recipe_id  # Same recipe
        rating_kwargs["user_id"] = str(uuid4())  # Different users
        rating = create_api_rating(**rating_kwargs)
        ratings.append(rating)

    return ratings


def create_api_ratings_for_different_recipes(count: int = 5) -> list[ApiRating]:
    """Create multiple ratings for different recipes from same user"""
    ratings = []
    base_user_id = str(uuid4())

    for i in range(count):
        rating_kwargs = create_api_rating_kwargs()
        rating_kwargs["user_id"] = base_user_id  # Same user
        rating_kwargs["recipe_id"] = str(uuid4())  # Different recipes
        rating = create_api_rating(**rating_kwargs)
        ratings.append(rating)

    return ratings


def create_rating_range_dataset() -> list[ApiRating]:
    """Create ratings covering all possible rating values (0-5)"""
    ratings = []

    for taste in range(0, 6):
        for convenience in range(0, 6):
            rating_kwargs = create_api_rating_kwargs()
            rating_kwargs["taste"] = taste
            rating_kwargs["convenience"] = convenience
            rating_kwargs["comment"] = (
                f"Rating with taste={taste}, convenience={convenience}"
            )
            rating = create_api_rating(**rating_kwargs)
            ratings.append(rating)

    return ratings


def create_test_rating_dataset(rating_count: int = 100) -> dict[str, Any]:
    """Create a dataset of ratings for performance testing"""
    ratings = []
    json_strings = []

    for i in range(rating_count):
        # Create API rating
        rating_kwargs = create_api_rating_kwargs()
        rating = create_api_rating(**rating_kwargs)
        ratings.append(rating)

        # Create JSON representation
        json_string = rating.model_dump_json()
        json_strings.append(json_string)

    return {
        "ratings": ratings,
        "json_strings": json_strings,
        "total_ratings": len(ratings),
    }


# =============================================================================
# DOMAIN AND ORM CONVERSION HELPERS
# =============================================================================


def create_rating_domain_from_api(api_rating: ApiRating) -> Rating:
    """Convert ApiRating to domain Rating using to_domain method"""
    return api_rating.to_domain()


def create_api_rating_from_domain(domain_rating: Rating) -> ApiRating:
    """Convert domain Rating to ApiRating using from_domain method"""
    return ApiRating.from_domain(domain_rating)


def create_rating_orm_kwargs_from_api(api_rating: ApiRating) -> dict[str, Any]:
    """Convert ApiRating to ORM kwargs using to_orm_kwargs method"""
    return api_rating.to_orm_kwargs()


# =============================================================================
# JSON VALIDATION AND EDGE CASE TESTING
# =============================================================================


def create_valid_json_test_cases() -> list[dict[str, Any]]:
    """Create various valid JSON test cases for model_validate_json testing"""
    return [
        # Standard case
        {
            "user_id": str(uuid4()),
            "recipe_id": str(uuid4()),
            "taste": 5,
            "convenience": 4,
            "comment": "Great recipe!",
        },
        # No comment
        {
            "user_id": str(uuid4()),
            "recipe_id": str(uuid4()),
            "taste": 3,
            "convenience": 3,
            "comment": None,
        },
        # Empty comment
        {
            "user_id": str(uuid4()),
            "recipe_id": str(uuid4()),
            "taste": 4,
            "convenience": 5,
            "comment": "",
        },
        # Edge rating values
        {
            "user_id": str(uuid4()),
            "recipe_id": str(uuid4()),
            "taste": 0,
            "convenience": 5,
            "comment": "No taste but convenient",
        },
        # Maximum comment length
        {
            "user_id": str(uuid4()),
            "recipe_id": str(uuid4()),
            "taste": 5,
            "convenience": 5,
            "comment": "A" * 1000,  # Exactly 1000 characters
        },
    ]


def create_invalid_json_test_cases() -> list[dict[str, Any]]:
    """Create various invalid JSON test cases for validation error testing"""
    return [
        # Invalid taste rating (out of range)
        {
            "data": {
                "user_id": str(uuid4()),
                "recipe_id": str(uuid4()),
                "taste": 6,  # Invalid
                "convenience": 4,
                "comment": "Invalid taste rating",
            },
            "expected_errors": ["taste"],
        },
        # Invalid convenience rating (negative)
        {
            "data": {
                "user_id": str(uuid4()),
                "recipe_id": str(uuid4()),
                "taste": 4,
                "convenience": -1,  # Invalid
                "comment": "Invalid convenience rating",
            },
            "expected_errors": ["convenience"],
        },
        # Invalid user_id (not UUID format)
        {
            "data": {
                "user_id": "not-a-uuid",  # Invalid
                "recipe_id": str(uuid4()),
                "taste": 4,
                "convenience": 4,
                "comment": "Invalid user ID",
            },
            "expected_errors": ["user_id"],
        },
        # Comment too long
        {
            "data": {
                "user_id": str(uuid4()),
                "recipe_id": str(uuid4()),
                "taste": 4,
                "convenience": 4,
                "comment": "A" * 1001,  # Too long
            },
            "expected_errors": ["comment"],
        },
        # Missing required fields
        {
            "data": {
                "user_id": str(uuid4()),
                # Missing recipe_id, taste, convenience
                "comment": "Missing required fields",
            },
            "expected_errors": ["recipe_id", "taste", "convenience"],
        },
    ]


def check_json_serialization_roundtrip(api_rating: ApiRating) -> bool:
    """Test that JSON serialization and deserialization preserves data integrity"""
    # Serialize to JSON
    json_str = api_rating.model_dump_json()

    # Deserialize from JSON
    restored_rating = ApiRating.model_validate_json(json_str)

    # Compare original and restored
    return api_rating == restored_rating
