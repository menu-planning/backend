"""
Simplified counter management for test data factories.

This module provides a clean, simple counter system that maintains the benefits
of deterministic test data while reducing complexity and maintenance burden.

Benefits over the original system:
- Single class instead of 20+ global variables
- Integer IDs instead of strings (simpler, more efficient)
- Automatic reset functionality
- Type safety with proper annotations
- Easier to extend and maintain

Key principles:
- Deterministic: Same test always produces same data
- Isolated: Each test starts with clean counters
- Simple: Minimal API surface
- Efficient: No unnecessary complexity
"""


class TestCounters:
    """
    Simple counter management for test data generation.

    Provides deterministic, isolated counters for test data factories.
    Each entity type gets its own counter, ensuring no ID collisions.
    """

    def __init__(self):
        """Initialize with empty counters."""
        self._counters: dict[str, int] = {}

    def next(self, entity_type: str = "general") -> int:
        """
        Get the next counter value for the specified entity type.

        Args:
            entity_type: Type of entity (e.g., "meal", "recipe", "user")

        Returns:
            Next integer ID for the entity type
        """
        self._counters[entity_type] = self._counters.get(entity_type, 0) + 1
        return self._counters[entity_type]

    def reset(self) -> None:
        """Reset all counters to start fresh for test isolation."""
        self._counters.clear()

    def get_current(self, entity_type: str = "general") -> int:
        """
        Get current counter value without incrementing.

        Args:
            entity_type: Type of entity

        Returns:
            Current counter value (0 if never used)
        """
        return self._counters.get(entity_type, 0)

    def set(self, entity_type: str, value: int) -> None:
        """
        Set counter value for specific entity type.

        Args:
            entity_type: Type of entity
            value: Counter value to set
        """
        self._counters[entity_type] = value


# Global instance for use across the test suite
test_counters = TestCounters()


# Convenience functions for backward compatibility
def get_next_meal_id() -> int:
    """Get next meal counter value."""
    return test_counters.next("meal")


def get_next_recipe_id() -> int:
    """Get next recipe counter value."""
    return test_counters.next("recipe")


def get_next_user_id() -> int:
    """Get next user counter value."""
    return test_counters.next("user")


def get_next_client_id() -> int:
    """Get next client counter value."""
    return test_counters.next("client")


def get_next_menu_id() -> int:
    """Get next menu counter value."""
    return test_counters.next("menu")


def get_next_product_id() -> int:
    """Get next product counter value."""
    return test_counters.next("product")


def get_next_supplier_id() -> int:
    """Get next supplier counter value."""
    return test_counters.next("supplier")


def get_next_customer_id() -> int:
    """Get next customer counter value."""
    return test_counters.next("customer")


def get_next_order_id() -> int:
    """Get next order counter value."""
    return test_counters.next("order")


def get_next_tag_id() -> int:
    """Get next tag counter value."""
    return test_counters.next("tag")


def get_next_ingredient_id() -> int:
    """Get next ingredient counter value."""
    return test_counters.next("ingredient")


def get_next_rating_id() -> int:
    """Get next rating counter value."""
    return test_counters.next("rating")


def get_next_general_id() -> int:
    """Get next general counter value."""
    return test_counters.next("general")


def get_next_category_id() -> int:
    """Get next category counter value."""
    return test_counters.next("category")


def reset_all_counters() -> None:
    """
    Reset all counters for test isolation.

    This function should be called before each test to ensure
    deterministic and isolated test behavior.
    """
    test_counters.reset()
