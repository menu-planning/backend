"""
Comprehensive behavior-focused tests for Menu domain behaviors.

These tests focus on what a high-quality Menu implementation SHOULD do,
testing business behaviors rather than implementation details.
Some tests may initially fail if the implementation needs improvement.
"""

import pytest

from src.contexts.recipes_catalog.core.domain.client.entities.menu import Menu
from src.contexts.shared_kernel.domain.exceptions import BusinessRuleValidationError
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.menu.menu_domain_factories import (
    create_menu,
    create_menu_meal,
)
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.shared_domain_factories import (
    create_menu_tag,
)


class TestMenuSortingBehaviors:
    """Test Menu sorting behaviors for chronological meal ordering."""

    def test_sorted_meals_should_order_chronologically_across_weeks(self):
        """Sorted meals should order by week first, then weekday, regardless of insertion order."""
        menu = create_menu()

        # Add meals in random order to test sorting
        meals = [
            create_menu_meal(
                meal_id="meal_3", week=2, weekday="Qua", meal_type="almoço"
            ),
            create_menu_meal(
                meal_id="meal_1", week=1, weekday="Seg", meal_type="café da manhã"
            ),
            create_menu_meal(
                meal_id="meal_4", week=2, weekday="Seg", meal_type="jantar"
            ),
            create_menu_meal(
                meal_id="meal_2", week=1, weekday="Dom", meal_type="almoço"
            ),
        ]
        menu.meals = set(meals)

        sorted_meals = menu.sorted_meals

        # Should be ordered: Week 1 Mon, Week 1 Sun, Week 2 Mon, Week 2 Wed
        expected_order = [
            ("meal_1", 1, "Seg"),  # Week 1, Monday
            ("meal_2", 1, "Dom"),  # Week 1, Sunday
            ("meal_4", 2, "Seg"),  # Week 2, Monday
            ("meal_3", 2, "Qua"),  # Week 2, Wednesday
        ]

        actual_order = [
            (meal.meal_id, meal.week, meal.weekday) for meal in sorted_meals
        ]
        assert actual_order == expected_order

    def test_sorted_meals_should_handle_empty_meals_gracefully(self):
        """Sorted meals should return empty list when no meals exist."""
        menu = create_menu()

        sorted_meals = menu.sorted_meals

        assert sorted_meals == []
        assert isinstance(sorted_meals, list)

    def test_sorted_meals_should_be_deterministic_with_same_week_and_weekday(self):
        """When meals have same week/weekday, sorting should be deterministic."""
        menu = create_menu()

        # Add multiple meals on same day
        meals = [
            create_menu_meal(
                meal_id="meal_dinner", week=1, weekday="Seg", meal_type="jantar"
            ),
            create_menu_meal(
                meal_id="meal_lunch", week=1, weekday="Seg", meal_type="almoço"
            ),
            create_menu_meal(
                meal_id="meal_breakfast",
                week=1,
                weekday="Seg",
                meal_type="café da manhã",
            ),
        ]
        menu.meals = set(meals)

        # Call multiple times to ensure deterministic ordering
        sorted_1 = menu.sorted_meals
        sorted_2 = menu.sorted_meals
        sorted_3 = menu.sorted_meals

        # Should be identical each time
        assert sorted_1 == sorted_2 == sorted_3
        assert len(sorted_1) == 3


class TestMenuMealUpdateBehaviors:
    """Test Menu meal update behaviors including error handling."""

    def test_update_meal_should_handle_nonexistent_meal_gracefully(self):
        """Update meal should gracefully handle attempting to update meal not on menu."""
        menu = create_menu()
        existing_meal = create_menu_meal(
            meal_id="existing", week=1, weekday="Seg", meal_type="almoço"
        )
        menu.add_meal(existing_meal)

        initial_version = menu.version

        # Try to update a meal that doesn't exist on this menu
        nonexistent_meal = create_menu_meal(
            meal_id="nonexistent", week=1, weekday="Ter", meal_type="jantar"
        )

        # Should not raise exception
        menu.update_meal(nonexistent_meal)

        # Version should not increment when update fails
        assert menu.version == initial_version
        assert len(menu.meals) == 1  # Original meal still there
        assert nonexistent_meal not in menu.meals

    def test_update_meal_should_be_idempotent(self):
        """Update meal should be idempotent - calling multiple times should have same effect."""
        menu = create_menu()
        original_meal = create_menu_meal(
            meal_id="test_meal", week=1, weekday="Seg", meal_type="almoço"
        )
        menu.add_meal(original_meal)

        # Create updated version
        updated_meal = create_menu_meal(
            meal_id="test_meal",
            meal_name="Updated Name",
            week=1,
            weekday="Seg",
            meal_type="almoço",
        )

        # Update multiple times
        menu.update_meal(updated_meal)
        first_version = menu.version

        menu.update_meal(updated_meal)  # Second update
        menu.update_meal(updated_meal)  # Third update

        # Should handle multiple updates gracefully
        assert len(menu.meals) == 1
        updated_meal_in_menu = next(iter(menu.meals))
        assert updated_meal_in_menu.meal_name == "Updated Name"

    def test_update_meal_should_replace_meal_with_same_id(self):
        """Update meal should replace existing meal with same ID."""
        menu = create_menu()
        original_meal = create_menu_meal(
            meal_id="meal_123",
            meal_name="Original Name",
            week=1,
            weekday="Seg",
            meal_type="almoço",
        )
        menu.add_meal(original_meal)
        assert len(menu.meals) == 1

        # Update with different properties
        updated_meal = create_menu_meal(
            meal_id="meal_123",  # Same ID
            meal_name="Updated Name",
            week=2,  # Different week
            weekday="Ter",  # Different weekday
            meal_type="jantar",  # Different meal type
        )

        menu.update_meal(updated_meal)

        # Should have replaced the meal
        assert len(menu.meals) == 1
        meal_in_menu = next(iter(menu.meals))
        assert meal_in_menu.meal_name == "Updated Name"
        assert meal_in_menu.week == 2
        assert meal_in_menu.weekday == "Ter"
        assert meal_in_menu.meal_type == "jantar"


class TestMenuFilteringBehaviors:
    """Test Menu filtering behaviors with partial criteria."""

    def test_filter_meals_should_handle_partial_week_filter(self):
        """Filter meals should work correctly with only week parameter."""
        menu = create_menu()

        meals = [
            create_menu_meal(meal_id="w1_1", week=1, weekday="Seg", meal_type="almoço"),
            create_menu_meal(meal_id="w1_2", week=1, weekday="Ter", meal_type="jantar"),
            create_menu_meal(meal_id="w2_1", week=2, weekday="Seg", meal_type="almoço"),
            create_menu_meal(
                meal_id="w2_2", week=2, weekday="Qua", meal_type="café da manhã"
            ),
        ]
        menu.meals = set(meals)

        # Filter by week only
        week_1_meals = menu.filter_meals(week=1)
        week_2_meals = menu.filter_meals(week=2)

        assert len(week_1_meals) == 2
        assert len(week_2_meals) == 2

        week_1_ids = {meal.meal_id for meal in week_1_meals}
        week_2_ids = {meal.meal_id for meal in week_2_meals}

        assert week_1_ids == {"w1_1", "w1_2"}
        assert week_2_ids == {"w2_1", "w2_2"}

    def test_filter_meals_should_handle_partial_weekday_filter(self):
        """Filter meals should work correctly with only weekday parameter."""
        menu = create_menu()

        meals = [
            create_menu_meal(
                meal_id="mon_1", week=1, weekday="Seg", meal_type="almoço"
            ),
            create_menu_meal(
                meal_id="mon_2", week=2, weekday="Seg", meal_type="jantar"
            ),
            create_menu_meal(
                meal_id="tue_1", week=1, weekday="Ter", meal_type="café da manhã"
            ),
            create_menu_meal(
                meal_id="wed_1", week=1, weekday="Qua", meal_type="almoço"
            ),
        ]
        menu.meals = set(meals)

        # Filter by weekday only
        monday_meals = menu.filter_meals(weekday="Seg")
        tuesday_meals = menu.filter_meals(weekday="Ter")

        assert len(monday_meals) == 2
        assert len(tuesday_meals) == 1

        monday_ids = {meal.meal_id for meal in monday_meals}
        tuesday_ids = {meal.meal_id for meal in tuesday_meals}

        assert monday_ids == {"mon_1", "mon_2"}
        assert tuesday_ids == {"tue_1"}

    def test_filter_meals_should_return_empty_for_no_matches(self):
        """Filter meals should return empty list when no meals match criteria."""
        menu = create_menu()

        meals = [
            create_menu_meal(
                meal_id="meal_1", week=1, weekday="Seg", meal_type="almoço"
            ),
            create_menu_meal(
                meal_id="meal_2", week=1, weekday="Ter", meal_type="jantar"
            ),
        ]
        menu.meals = set(meals)

        # Filter for week that doesn't exist
        no_matches = menu.filter_meals(week=5)
        assert no_matches == []

        # Filter for weekday that doesn't exist
        no_matches = menu.filter_meals(weekday="Sab")
        assert no_matches == []

        # Filter for meal_type that doesn't exist
        no_matches = menu.filter_meals(meal_type="lanche")
        assert no_matches == []

    def test_filter_meals_should_handle_multiple_partial_criteria(self):
        """Filter meals should correctly combine multiple partial criteria."""
        menu = create_menu()

        meals = [
            create_menu_meal(
                meal_id="match", week=1, weekday="Seg", meal_type="almoço"
            ),
            create_menu_meal(
                meal_id="wrong_week", week=2, weekday="Seg", meal_type="almoço"
            ),
            create_menu_meal(
                meal_id="wrong_day", week=1, weekday="Ter", meal_type="almoço"
            ),
            create_menu_meal(
                meal_id="wrong_type", week=1, weekday="Seg", meal_type="jantar"
            ),
        ]
        menu.meals = set(meals)

        # Filter with multiple criteria (but not all three)
        filtered = menu.filter_meals(week=1, weekday="Seg")

        assert len(filtered) == 2  # Should match "match" and "wrong_type"
        filtered_ids = {meal.meal_id for meal in filtered}
        assert filtered_ids == {"match", "wrong_type"}


class TestMenuFirstMealBehaviors:
    """Test Menu first meal identification behaviors."""

    def test_weekday_of_first_meal_should_find_earliest_weekday_on_week_1(self):
        """Should correctly identify the earliest weekday with meals on week 1."""
        menu = create_menu()

        # Add meals on week 1 in different weekdays
        meals = [
            create_menu_meal(meal_id="fri", week=1, weekday="Sex", meal_type="almoço"),
            create_menu_meal(meal_id="mon", week=1, weekday="Seg", meal_type="jantar"),
            create_menu_meal(
                meal_id="wed", week=1, weekday="Qua", meal_type="café da manhã"
            ),
        ]
        menu.meals = set(meals)

        first_weekday = menu.weekday_of_first_meal

        # Monday is earliest in the week
        assert first_weekday == "Seg"

    def test_weekday_of_first_meal_should_raise_error_when_no_week_1_meals(self):
        """Should raise meaningful error when no meals exist on week 1."""
        menu = create_menu()

        # Add meals only on week 2 and 3
        meals = [
            create_menu_meal(meal_id="w2", week=2, weekday="Seg", meal_type="almoço"),
            create_menu_meal(meal_id="w3", week=3, weekday="Ter", meal_type="jantar"),
        ]
        menu.meals = set(meals)

        with pytest.raises(ValueError, match="No meals found on week 1"):
            menu.weekday_of_first_meal

    def test_weekday_of_first_meal_should_handle_multiple_meals_same_earliest_day(self):
        """Should handle case where multiple meals exist on the earliest weekday."""
        menu = create_menu()

        # Add multiple meals on Monday (earliest) and other days
        meals = [
            create_menu_meal(
                meal_id="mon_lunch", week=1, weekday="Seg", meal_type="almoço"
            ),
            create_menu_meal(
                meal_id="mon_dinner", week=1, weekday="Seg", meal_type="jantar"
            ),
            create_menu_meal(
                meal_id="tue", week=1, weekday="Ter", meal_type="café da manhã"
            ),
        ]
        menu.meals = set(meals)

        first_weekday = menu.weekday_of_first_meal

        # Should still return Monday even with multiple meals
        assert first_weekday == "Seg"


class TestMenuDescriptionBehaviors:
    """Test Menu description property behaviors."""

    def test_description_setter_should_only_increment_version_on_actual_change(self):
        """Description setter should be efficient - only increment version when value changes."""
        menu = create_menu(description="Original description")
        initial_version = menu.version

        # Set same description - should not increment version
        menu.description = "Original description"
        assert menu.version == initial_version

        # Set different description - should increment version
        menu.description = "New description"
        assert menu.version == initial_version + 1

        # Set same new description again - should not increment
        current_version = menu.version
        menu.description = "New description"
        assert menu.version == current_version

    def test_description_setter_should_handle_empty_string_correctly(self):
        """Description setter should handle empty string values correctly."""
        menu = create_menu(description="Original description")
        initial_version = menu.version

        # Setting empty string when was non-empty should increment
        menu.description = ""
        assert menu.version == initial_version + 1
        assert menu.description == ""

        # Setting empty string again should not increment
        current_version = menu.version
        menu.description = ""
        assert menu.version == current_version


class TestMenuTagValidationBehaviors:
    """Test Menu tag validation business rules."""

    def test_tags_setter_should_validate_all_tags_have_matching_author_id(self):
        """Tags setter should enforce business rule that tag author must match menu author."""
        menu = create_menu(author_id="user_123")

        # Valid tags with matching author
        valid_tags = {
            create_menu_tag(key="diet", value="vegetarian", author_id="user_123"),
            create_menu_tag(key="cuisine", value="italian", author_id="user_123"),
        }

        # Should accept valid tags
        menu.tags = valid_tags
        assert len(menu.tags) == 2

        # Invalid tags with mismatched author
        invalid_tags = {
            create_menu_tag(key="diet", value="vegan", author_id="user_123"),  # Valid
            create_menu_tag(
                key="style", value="fancy", author_id="different_user"
            ),  # Invalid
        }

        # Should reject all tags if any are invalid
        with pytest.raises(BusinessRuleValidationError):
            menu.tags = invalid_tags

    def test_tags_setter_should_handle_empty_tag_set(self):
        """Tags setter should handle empty tag sets without validation errors."""
        menu = create_menu(author_id="user_123")

        # Should accept empty set
        menu.tags = set()
        assert len(menu.tags) == 0

        # Add some tags
        tags = {create_menu_tag(key="diet", value="keto", author_id="user_123")}
        menu.tags = tags
        assert len(menu.tags) == 1

        # Clear tags again
        menu.tags = set()
        assert len(menu.tags) == 0

    def test_tags_setter_should_validate_all_before_accepting_any(self):
        """Tags setter should validate all tags before accepting any (atomic operation)."""
        menu = create_menu(author_id="user_123")

        # Set initial valid tags
        initial_tags = {
            create_menu_tag(key="diet", value="paleo", author_id="user_123")
        }
        menu.tags = initial_tags

        # Try to set mix of valid and invalid tags
        mixed_tags = {
            create_menu_tag(
                key="diet", value="mediterranean", author_id="user_123"
            ),  # Valid
            create_menu_tag(
                key="occasion", value="party", author_id="wrong_user"
            ),  # Invalid
        }

        # Should reject and keep original tags
        with pytest.raises(BusinessRuleValidationError):
            menu.tags = mixed_tags

        # Original tags should still be there
        assert len(menu.tags) == 1
        original_tag = next(iter(menu.tags))
        assert original_tag.value == "paleo"


class TestMenuDeletionBehaviors:
    """Test Menu deletion behaviors."""

    def test_delete_should_mark_menu_as_discarded_and_generate_event(self):
        """Delete should properly mark menu as discarded and generate domain event."""
        menu = create_menu()
        menu.add_meal(
            create_menu_meal(meal_id="test", week=1, weekday="Seg", meal_type="almoço")
        )

        initial_events = len(menu.events)

        # Delete the menu
        menu.delete()

        # Should be marked as discarded
        assert menu.discarded is True

        # Should generate deletion event
        assert len(menu.events) == initial_events + 1
        deletion_event = menu.events[-1]
        assert deletion_event.__class__.__name__ == "MenuDeleted"
        # Check event has proper menu_id by accessing as dict-like
        assert hasattr(deletion_event, "menu_id")
        # Type assertion to access the attribute
        assert deletion_event.menu_id == menu.id

    def test_delete_should_prevent_further_operations(self):
        """Delete should prevent further operations on the menu."""
        menu = create_menu()

        # Delete the menu
        menu.delete()

        # Should prevent access to properties
        with pytest.raises(
            Exception
        ):  # Should raise some kind of "discarded" exception
            _ = menu.meals

        # Should prevent mutations
        with pytest.raises(Exception):
            menu.add_meal(
                create_menu_meal(
                    meal_id="test", week=1, weekday="Seg", meal_type="almoço"
                )
            )

    def test_delete_should_be_idempotent(self):
        """Delete should be idempotent - calling multiple times should be safe."""
        menu = create_menu()

        # Delete multiple times
        menu.delete()
        first_version = menu.version
        first_event_count = len(menu.events)

        # Second delete should handle gracefully (might be no-op or safe)
        try:
            menu.delete()
            # If it doesn't raise, check it handles gracefully
            assert menu.discarded is True
        except Exception:
            # If it raises, that's also acceptable behavior for discarded entity
            pass


class TestMenuEqualityAndHashBehaviors:
    """Test Menu equality and hash behaviors for proper object identity."""

    def test_menus_with_same_id_should_be_equal(self):
        """Menus with same ID should be considered equal regardless of other properties."""
        menu_1 = Menu(
            entity_id="same_id",
            author_id="user_1",
            client_id="client_1",
            description="Description 1",
        )

        menu_2 = Menu(
            entity_id="same_id",  # Same ID
            author_id="user_2",  # Different author
            client_id="client_2",  # Different client
            description="Description 2",  # Different description
        )

        assert menu_1 == menu_2
        assert menu_2 == menu_1

    def test_menus_with_different_ids_should_not_be_equal(self):
        """Menus with different IDs should not be equal even with same other properties."""
        menu_1 = Menu(
            entity_id="id_1",
            author_id="user_1",
            client_id="client_1",
            description="Same description",
        )

        menu_2 = Menu(
            entity_id="id_2",  # Different ID
            author_id="user_1",  # Same author
            client_id="client_1",  # Same client
            description="Same description",  # Same description
        )

        assert menu_1 != menu_2
        assert menu_2 != menu_1

    def test_menu_should_have_consistent_hash(self):
        """Menu hash should be consistent and based on ID."""
        menu = Menu(entity_id="test_id", author_id="user_1", client_id="client_1")

        # Hash should be consistent
        hash_1 = hash(menu)
        hash_2 = hash(menu)
        assert hash_1 == hash_2

        # Hash should be based on ID
        same_id_menu = Menu(
            entity_id="test_id", author_id="different", client_id="different"
        )
        assert hash(menu) == hash(same_id_menu)

    def test_menu_equality_should_handle_non_menu_objects(self):
        """Menu equality should handle comparison with non-Menu objects gracefully."""
        menu = Menu(entity_id="test_id", author_id="user_1", client_id="client_1")

        # Should not be equal to non-Menu objects
        assert menu != "string"
        assert menu != 123
        assert menu != None
        assert menu != {}

        # Should not raise exceptions
        assert (menu == "string") is False
        assert (menu == None) is False


class TestMenuUpdatePropertiesBehaviors:
    """Test Menu update_properties behaviors."""

    def test_update_properties_should_route_to_appropriate_setters(self):
        """Update properties should route to appropriate property setters."""
        menu = create_menu(description="Original")
        initial_version = menu.version

        # Update properties
        menu.update_properties(description="Updated description")

        # Should update the property
        assert menu.description == "Updated description"
        assert menu.version > initial_version

    def test_update_properties_should_validate_property_names(self):
        """Update properties should validate that properties exist and are settable."""
        menu = create_menu()

        # Should reject invalid property names
        with pytest.raises(Exception):  # Should raise some validation error
            menu.update_properties(invalid_property="value")

        # Should reject read-only properties
        with pytest.raises(Exception):  # Should raise some validation error
            menu.update_properties(id="new_id")

    def test_update_properties_should_handle_multiple_properties(self):
        """Update properties should handle updating multiple properties at once."""
        menu = create_menu(description="Original")

        # Create valid tags
        new_tags = {
            create_menu_tag(key="diet", value="vegan", author_id=menu.author_id)
        }

        # Update multiple properties
        menu.update_properties(description="New description", tags=new_tags)

        # Should update all properties
        assert menu.description == "New description"
        assert len(menu.tags) == 1
        tag = next(iter(menu.tags))
        assert tag.value == "vegan"

    def test_update_properties_should_handle_business_rule_validation(self):
        """Update properties should enforce business rules during updates."""
        menu = create_menu(author_id="user_123")

        # Try to update with invalid tags
        invalid_tags = {
            create_menu_tag(key="diet", value="vegan", author_id="wrong_user")
        }

        # Should enforce business rules
        with pytest.raises(BusinessRuleValidationError):
            menu.update_properties(tags=invalid_tags)

        # Menu should remain unchanged after failed update
        assert len(menu.tags) == 0
