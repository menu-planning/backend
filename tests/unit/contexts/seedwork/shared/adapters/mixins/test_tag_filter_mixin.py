"""
Unit tests for TagFilter.

This module contains comprehensive tests for the TagFilter class, including
edge cases, error conditions, and proper SQLAlchemy condition generation.

The tests focus on validating the core logic of the TagFilter without
requiring real SQLAlchemy infrastructure.
"""

from unittest.mock import Mock, patch

import pytest
from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
    FilterNotAllowedError,
)
from src.contexts.seedwork.adapters.tag_filter_builder import (
    TagFilterBuilder,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)


class MockSaModelWithTags:
    """Mock SQLAlchemy model class with tags relationship."""

    __name__ = "MockSaModelWithTags"

    # Class-level tags attribute that mimics SQLAlchemy relationship
    tags = Mock()


class MockSaModelWithoutTags:
    """Mock SQLAlchemy model class without tags relationship."""

    __name__ = "MockSaModelWithoutTags"

    # Deliberately no tags attribute


class TestTagFilter:
    """Test cases for TagFilter functionality."""

    @pytest.fixture
    def tag_filter(self):
        """Create a testable tag filter instance."""
        return TagFilterBuilder(TagSaModel)

    @pytest.fixture
    def mock_sa_model_class(self):
        """Create a mock SA model class with tags relationship."""
        mock_model = MockSaModelWithTags()
        mock_model.tags.any = Mock(return_value=Mock())
        return mock_model

    @pytest.fixture
    def mock_sa_model_without_tags(self):
        """Create a mock SA model class without tags relationship."""
        return MockSaModelWithoutTags

    # =============================================================================
    # Tests for validate_tag_format method
    # =============================================================================

    @pytest.mark.parametrize(
        "valid_tags",
        [
            [],  # Empty list should be valid
            [("cuisine", "italian", "user123")],
            [("cuisine", "italian", "user123"), ("difficulty", "easy", "user456")],
            [
                ("type", "breakfast", "admin"),
                ("calories", "low", "admin"),
                ("time", "quick", "admin"),
            ],
        ],
    )
    @pytest.mark.unit
    def test_validate_tag_format_valid_cases(self, tag_filter, valid_tags):
        """Test that valid tag formats pass validation without raising exceptions."""
        # Should not raise any exception
        tag_filter.validate_tag_format(valid_tags)

    @pytest.mark.parametrize(
        "invalid_tags,expected_error_message",
        [
            # Not a list
            ("cuisine:italian", "Tags must be a list"),
            ({"cuisine": "italian"}, "Tags must be a list"),
            (123, "Tags must be a list"),
            # Items not tuples
            ([["cuisine", "italian", "user123"]], "must be a tuple"),
            (["cuisine:italian:user123"], "must be a tuple"),
            ([{"key": "cuisine", "value": "italian"}], "must be a tuple"),
            # Wrong tuple length
            ([("cuisine", "italian")], "must have exactly 3 elements"),
            ([("cuisine",)], "must have exactly 3 elements"),
            (
                [("cuisine", "italian", "user123", "extra")],
                "must have exactly 3 elements",
            ),
            # Non-string components
            ([("cuisine", 123, "user123")], "value must be a string"),
            ([(123, "italian", "user123")], "key must be a string"),
            ([("cuisine", "italian", 456)], "author_id must be a string"),
            ([("cuisine", None, "user123")], "value must be a string"),
        ],
    )
    @pytest.mark.unit
    def test_validate_tag_format_invalid_cases(
        self, tag_filter, invalid_tags, expected_error_message
    ):
        """Test that invalid tag formats raise FilterNotAllowedError with helpful messages."""
        with pytest.raises(FilterNotAllowedError) as exc_info:
            tag_filter.validate_tag_format(invalid_tags)

        assert expected_error_message in str(exc_info.value)

    @pytest.mark.unit
    def test_validate_tag_format_complex_invalid_case(self, tag_filter):
        """Test validation with mixed valid and invalid tags."""
        invalid_tags = [
            ("cuisine", "italian", "user123"),  # Valid
            ("difficulty", 123, "user456"),  # Invalid: non-string value
            ("type", "breakfast", "user789"),  # Valid
        ]

        with pytest.raises(FilterNotAllowedError) as exc_info:
            tag_filter.validate_tag_format(invalid_tags)

        error_message = str(exc_info.value)
        assert "Tag at index 1" in error_message
        assert "value must be a string" in error_message

    # =============================================================================
    # Tests for build_tag_filter method
    # =============================================================================

    @pytest.mark.unit
    def test_build_tag_filter_empty_tags(self, tag_filter, mock_sa_model_class):
        """Test that empty tag list returns True (no filtering)."""
        result = tag_filter.build_tag_filter(mock_sa_model_class, [], "meal")
        assert result is True

    @pytest.mark.unit
    def test_build_tag_filter_model_without_tags_relationship(
        self, tag_filter, mock_sa_model_without_tags
    ):
        """Test that model without tags relationship raises FilterNotAllowedError."""
        tags = [("cuisine", "italian", "user123")]

        with pytest.raises(FilterNotAllowedError) as exc_info:
            tag_filter.build_tag_filter(mock_sa_model_without_tags, tags, "meal")

        assert "does not have a 'tags' relationship" in str(exc_info.value)

    @patch("src.contexts.seedwork.adapters.mixins.tag_filter_mixin.and_")
    @pytest.mark.unit
    def test_build_tag_filter_single_tag(
        self, mock_and, tag_filter, mock_sa_model_class
    ):
        """Test filtering with a single tag creates proper SQLAlchemy condition."""
        tags = [("cuisine", "italian", "user123")]
        mock_and.return_value = Mock()

        result = tag_filter.build_tag_filter(mock_sa_model_class, tags, "meal")

        # Verify that tags.any() was called
        mock_sa_model_class.tags.any.assert_called_once()

        # Verify and_() was called (multiple times: for individual conditions and final combination)
        assert mock_and.call_count >= 1
        assert result is not None

    @patch("src.contexts.seedwork.adapters.mixins.tag_filter_mixin.and_")
    @pytest.mark.unit
    def test_build_tag_filter_multiple_tags_same_key(
        self, mock_and, tag_filter, mock_sa_model_class
    ):
        """Test that multiple tags with same key create OR logic within key group."""
        tags = [
            ("cuisine", "italian", "user123"),
            ("cuisine", "mexican", "user123"),
        ]
        mock_and.return_value = Mock()

        result = tag_filter.build_tag_filter(mock_sa_model_class, tags, "meal")

        # Should create a single condition for the cuisine key with IN clause for values
        assert mock_sa_model_class.tags.any.call_count == 1
        assert mock_and.call_count >= 1
        assert result is not None

    @patch("src.contexts.seedwork.adapters.mixins.tag_filter_mixin.and_")
    @pytest.mark.unit
    def test_build_tag_filter_multiple_tags_different_keys(
        self, mock_and, tag_filter, mock_sa_model_class
    ):
        """Test that multiple tags with different keys create AND logic between key groups."""
        tags = [
            ("cuisine", "italian", "user123"),
            ("difficulty", "easy", "user456"),
        ]
        mock_and.return_value = Mock()

        result = tag_filter.build_tag_filter(mock_sa_model_class, tags, "meal")

        # Should create two separate conditions (one for each key) combined with AND
        assert mock_sa_model_class.tags.any.call_count == 2
        assert (
            mock_and.call_count >= 2
        )  # Called for each key group plus final combination
        assert result is not None

    @patch("src.contexts.seedwork.adapters.mixins.tag_filter_mixin.and_")
    @pytest.mark.unit
    def test_build_tag_filter_complex_scenario(
        self, mock_and, tag_filter, mock_sa_model_class
    ):
        """Test complex tag filtering scenario with mixed keys and values."""
        tags = [
            ("cuisine", "italian", "user123"),
            ("cuisine", "mexican", "user123"),  # OR with italian
            ("difficulty", "easy", "user123"),  # AND with cuisine group
            ("type", "dinner", "user123"),  # AND with other groups
        ]
        mock_and.return_value = Mock()

        result = tag_filter.build_tag_filter(mock_sa_model_class, tags, "meal")

        # Should handle the complex grouping correctly (3 key groups)
        assert mock_sa_model_class.tags.any.call_count == 3
        assert (
            mock_and.call_count >= 3
        )  # Called for each key group plus final combination
        assert result is not None

    @patch("src.contexts.seedwork.adapters.mixins.tag_filter_mixin.and_")
    @pytest.mark.parametrize("tag_type", ["meal", "recipe", "menu", "custom"])
    @pytest.mark.unit
    def test_build_tag_filter_different_tag_types(
        self, mock_and, tag_filter, mock_sa_model_class, tag_type
    ):
        """Test that different tag types are handled correctly."""
        tags = [("cuisine", "italian", "user123")]
        mock_and.return_value = Mock()

        result = tag_filter.build_tag_filter(mock_sa_model_class, tags, tag_type)

        # Verify the method completes successfully
        assert result is not None

    # =============================================================================
    # Tests for build_negative_tag_filter method
    # =============================================================================

    @pytest.mark.unit
    def test_build_negative_tag_filter_empty_tags(
        self, tag_filter, mock_sa_model_class
    ):
        """Test that empty tag list returns True (no filtering) for negative filter."""
        result = tag_filter.build_negative_tag_filter(mock_sa_model_class, [], "meal")
        assert result is True

    @pytest.mark.unit
    def test_build_negative_tag_filter_model_without_tags_relationship(
        self, tag_filter, mock_sa_model_without_tags
    ):
        """Test that model without tags relationship raises FilterNotAllowedError."""
        tags = [("cuisine", "spicy", "user123")]

        with pytest.raises(FilterNotAllowedError) as exc_info:
            tag_filter.build_negative_tag_filter(
                mock_sa_model_without_tags, tags, "meal"
            )

        assert "does not have a 'tags' relationship" in str(exc_info.value)

    @patch("src.contexts.seedwork.adapters.mixins.tag_filter_mixin.and_")
    @pytest.mark.unit
    def test_build_negative_tag_filter_single_tag(
        self, mock_and, tag_filter, mock_sa_model_class
    ):
        """Test that negative filtering with single tag creates negated condition."""
        tags = [("cuisine", "spicy", "user123")]
        mock_condition = Mock()
        mock_condition.__invert__ = Mock(return_value=Mock())
        mock_and.return_value = mock_condition

        result = tag_filter.build_negative_tag_filter(mock_sa_model_class, tags, "meal")

        # Should create a negated condition
        mock_condition.__invert__.assert_called_once()
        assert result is not None

    @patch("src.contexts.seedwork.adapters.mixins.tag_filter_mixin.and_")
    @pytest.mark.unit
    def test_build_negative_tag_filter_multiple_tags(
        self, mock_and, tag_filter, mock_sa_model_class
    ):
        """Test negative filtering with multiple tags."""
        tags = [
            ("cuisine", "spicy", "user123"),
            ("difficulty", "hard", "user123"),
        ]
        mock_condition = Mock()
        mock_condition.__invert__ = Mock(return_value=Mock())
        mock_and.return_value = mock_condition

        result = tag_filter.build_negative_tag_filter(mock_sa_model_class, tags, "meal")

        # Should create a complex negated condition
        mock_condition.__invert__.assert_called_once()
        assert result is not None

    # =============================================================================
    # Integration tests
    # =============================================================================

    @patch("src.contexts.seedwork.adapters.mixins.tag_filter_mixin.and_")
    @pytest.mark.integration
    def test_tag_filter_integration_workflow(
        self, mock_and, tag_filter, mock_sa_model_class
    ):
        """Test the complete workflow of validation and filtering."""
        tags = [
            ("cuisine", "italian", "user123"),
            ("difficulty", "easy", "user123"),
        ]
        mock_condition = Mock()
        mock_condition.__invert__ = Mock(return_value=Mock())
        mock_and.return_value = mock_condition

        # First validate
        tag_filter.validate_tag_format(tags)  # Should not raise

        # Then create positive filter
        positive_condition = tag_filter.build_tag_filter(
            mock_sa_model_class, tags, "meal"
        )
        assert positive_condition is not None

        # And negative filter
        negative_condition = tag_filter.build_negative_tag_filter(
            mock_sa_model_class, tags, "meal"
        )
        assert negative_condition is not None

    @patch("src.contexts.seedwork.adapters.mixins.tag_filter_mixin.and_")
    @pytest.mark.integration
    def test_tag_filter_with_invalid_then_valid_tags(
        self, mock_and, tag_filter, mock_sa_model_class
    ):
        """Test that validation catches errors before filter building."""
        invalid_tags = [("cuisine", 123, "user123")]  # Invalid
        valid_tags = [("cuisine", "italian", "user123")]  # Valid
        mock_and.return_value = Mock()

        # Invalid tags should raise during validation
        with pytest.raises(FilterNotAllowedError):
            tag_filter.validate_tag_format(invalid_tags)

        # Valid tags should work fine
        tag_filter.validate_tag_format(valid_tags)
        result = tag_filter.build_tag_filter(mock_sa_model_class, valid_tags, "meal")
        assert result is not None

    # =============================================================================
    # Edge case tests
    # =============================================================================

    @patch("src.contexts.seedwork.adapters.mixins.tag_filter_mixin.and_")
    @pytest.mark.unit
    def test_tag_filter_with_special_characters(
        self, mock_and, tag_filter, mock_sa_model_class
    ):
        """Test tag filtering with special characters in keys and values."""
        tags = [
            ("cuisine-type", "italian/sicilian", "user-123"),
            ("difficulty_level", "easy_medium", "user_456"),
        ]
        mock_and.return_value = Mock()

        # Should handle special characters in validation
        tag_filter.validate_tag_format(tags)

        # And in filtering
        result = tag_filter.build_tag_filter(mock_sa_model_class, tags, "meal")
        assert result is not None

    @patch("src.contexts.seedwork.adapters.mixins.tag_filter_mixin.and_")
    @pytest.mark.unit
    def test_tag_filter_with_empty_strings(
        self, mock_and, tag_filter, mock_sa_model_class
    ):
        """Test tag filtering with empty string values."""
        tags = [("", "", "")]  # Empty strings but still valid format
        mock_and.return_value = Mock()

        # Should pass validation (empty strings are still strings)
        tag_filter.validate_tag_format(tags)

        # And filtering
        result = tag_filter.build_tag_filter(mock_sa_model_class, tags, "meal")
        assert result is not None

    @patch("src.contexts.seedwork.adapters.mixins.tag_filter_mixin.and_")
    @pytest.mark.unit
    def test_tag_filter_case_sensitivity(
        self, mock_and, tag_filter, mock_sa_model_class
    ):
        """Test that tag filtering preserves case sensitivity."""
        tags = [
            ("Cuisine", "Italian", "User123"),  # Mixed case
            ("DIFFICULTY", "EASY", "USER456"),  # Upper case
        ]
        mock_and.return_value = Mock()

        tag_filter.validate_tag_format(tags)
        result = tag_filter.build_tag_filter(mock_sa_model_class, tags, "meal")
        assert result is not None

    # =============================================================================
    # Pytest configuration
    # =============================================================================

    @pytest.fixture(autouse=True)
    def reset_mocks(self, mock_sa_model_class):
        """Reset all mocks between tests for isolation."""
        yield
        # Reset the mock after each test
        if hasattr(mock_sa_model_class, "tags"):
            mock_sa_model_class.tags.reset_mock()


@pytest.mark.parametrize(
    "tag_format_scenario",
    [
        {
            "scenario_id": "empty_list",
            "tags": [],
            "should_pass": True,
            "description": "Empty list should be valid",
        },
        {
            "scenario_id": "single_valid_tag",
            "tags": [("cuisine", "italian", "user123")],
            "should_pass": True,
            "description": "Single valid tag should pass",
        },
        {
            "scenario_id": "multiple_valid_tags",
            "tags": [
                ("cuisine", "italian", "user123"),
                ("difficulty", "easy", "user456"),
            ],
            "should_pass": True,
            "description": "Multiple valid tags should pass",
        },
        {
            "scenario_id": "not_a_list",
            "tags": "cuisine:italian",
            "should_pass": False,
            "description": "String instead of list should fail",
        },
        {
            "scenario_id": "tuple_too_short",
            "tags": [("cuisine", "italian")],
            "should_pass": False,
            "description": "Tuple with only 2 elements should fail",
        },
        {
            "scenario_id": "non_string_value",
            "tags": [("cuisine", 123, "user123")],
            "should_pass": False,
            "description": "Non-string value should fail",
        },
    ],
)
@pytest.mark.unit
def test_tag_format_scenarios(tag_format_scenario):
    """Parametrized test for various tag format scenarios."""
    tag_filter = TagFilterBuilder(TagSaModel)
    tags = tag_format_scenario["tags"]
    should_pass = tag_format_scenario["should_pass"]

    if should_pass:
        # Should not raise an exception
        tag_filter.validate_tag_format(tags)
    else:
        # Should raise FilterNotAllowedError
        with pytest.raises(FilterNotAllowedError):
            tag_filter.validate_tag_format(tags)
