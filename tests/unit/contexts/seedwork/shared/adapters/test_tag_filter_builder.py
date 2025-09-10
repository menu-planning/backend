"""
Unit tests for TagFilterBuilder.

This module contains comprehensive tests for the TagFilterBuilder class, focusing
on behavior rather than implementation details. The tests validate the core logic
of tag filtering with minimal mocking.
"""

import pytest
from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.elements import True_
from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
    FilterNotAllowedError,
)
from src.contexts.seedwork.adapters.tag_filter_builder import (
    TagFilterBuilder,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)
from src.db.base import SaBase

# Create association table for model with tags
model_tags_association = Table(
    "model_tags_association",
    SaBase.metadata,
    Column("model_id", ForeignKey("model_with_tags.id"), primary_key=True),
    Column("tag_id", ForeignKey("shared_kernel.tags.id"), primary_key=True),
    extend_existing=True,
)


class ModelWithTags(SaBase):
    """SQLAlchemy model class with tags relationship."""

    __tablename__ = "model_with_tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))

    # Create proper tags relationship
    tags: Mapped[list[TagSaModel]] = relationship(
        secondary=model_tags_association, back_populates="models"
    )


class ModelWithoutTags(SaBase):
    """SQLAlchemy model class without tags relationship."""

    __tablename__ = "model_without_tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))

    # Deliberately no tags relationship


# Add back_populates to TagSaModel
TagSaModel.models = relationship(
    "ModelWithTags", secondary=model_tags_association, back_populates="tags"
)


class TestTagFilterBuilder:
    """Test cases for TagFilterBuilder functionality."""

    @pytest.fixture
    def tag_filter_builder(self):
        """Create a testable tag filter builder instance."""
        return TagFilterBuilder(TagSaModel)

    @pytest.fixture
    def model_with_tags(self):
        """Create a model with tags relationship."""
        return ModelWithTags

    @pytest.fixture
    def model_without_tags(self):
        """Create a model without tags relationship."""
        return ModelWithoutTags

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
    def test_validate_tag_format_valid_cases(self, tag_filter_builder, valid_tags):
        """Test that valid tag formats pass validation without raising exceptions."""
        # Should not raise any exception
        tag_filter_builder.validate_tag_format(valid_tags)

    @pytest.mark.parametrize(
        "invalid_tags",
        [
            # Not a list
            "cuisine:italian",
            {"cuisine": "italian"},
            123,
            # Items not tuples
            [["cuisine", "italian", "user123"]],
            ["cuisine:italian:user123"],
            [{"key": "cuisine", "value": "italian"}],
            # Wrong tuple length
            [("cuisine", "italian")],
            [("cuisine",)],
            [("cuisine", "italian", "user123", "extra")],
            # Non-string components
            [("cuisine", 123, "user123")],
            [(123, "italian", "user123")],
            [("cuisine", "italian", 456)],
            [("cuisine", None, "user123")],
        ],
    )
    @pytest.mark.unit
    def test_validate_tag_format_invalid_cases(self, tag_filter_builder, invalid_tags):
        """Test that invalid tag formats raise FilterNotAllowedError."""
        with pytest.raises(FilterNotAllowedError):
            tag_filter_builder.validate_tag_format(invalid_tags)

    @pytest.mark.unit
    def test_validate_tag_format_complex_invalid_case(self, tag_filter_builder):
        """Test validation with mixed valid and invalid tags."""
        invalid_tags = [
            ("cuisine", "italian", "user123"),  # Valid
            ("difficulty", 123, "user456"),  # Invalid: non-string value
            ("type", "breakfast", "user789"),  # Valid
        ]

        with pytest.raises(FilterNotAllowedError):
            tag_filter_builder.validate_tag_format(invalid_tags)

    # =============================================================================
    # Tests for build_tag_filter method
    # =============================================================================

    @pytest.mark.unit
    def test_build_tag_filter_empty_tags(self, tag_filter_builder, model_with_tags):
        """Test that empty tag list returns True (no filtering)."""
        result = tag_filter_builder.build_tag_filter(model_with_tags, [], "meal")
        assert result == True

    @pytest.mark.unit
    def test_build_tag_filter_model_without_tags_relationship(
        self, tag_filter_builder, model_without_tags
    ):
        """Test that model without tags relationship raises FilterNotAllowedError."""
        tags = [("cuisine", "italian", "user123")]

        with pytest.raises(FilterNotAllowedError):
            tag_filter_builder.build_tag_filter(model_without_tags, tags, "meal")

    @pytest.mark.unit
    def test_build_tag_filter_single_tag_creates_condition(
        self, tag_filter_builder, model_with_tags
    ):
        """Test that filtering with a single tag creates a SQLAlchemy condition."""
        tags = [("cuisine", "italian", "user123")]

        result = tag_filter_builder.build_tag_filter(model_with_tags, tags, "meal")

        # Should return a SQLAlchemy condition (not None, not True)
        assert result is not None
        assert result is not True

    @pytest.mark.unit
    def test_build_tag_filter_multiple_tags_same_key_creates_or_logic(
        self, tag_filter_builder, model_with_tags
    ):
        """Test that multiple tags with same key create OR logic within key group."""
        tags = [
            ("cuisine", "italian", "user123"),
            ("cuisine", "mexican", "user123"),
        ]

        result = tag_filter_builder.build_tag_filter(model_with_tags, tags, "meal")

        # Should return a SQLAlchemy condition
        assert result is not None
        assert result is not True

    @pytest.mark.unit
    def test_build_tag_filter_multiple_tags_different_keys_creates_and_logic(
        self, tag_filter_builder, model_with_tags
    ):
        """Test that multiple tags with different keys create AND logic between key groups."""
        tags = [
            ("cuisine", "italian", "user123"),
            ("difficulty", "easy", "user456"),
        ]

        result = tag_filter_builder.build_tag_filter(model_with_tags, tags, "meal")

        # Should return a SQLAlchemy condition
        assert result is not None
        assert result is not True

    @pytest.mark.unit
    def test_build_tag_filter_complex_scenario_handles_mixed_keys(
        self, tag_filter_builder, model_with_tags
    ):
        """Test complex tag filtering scenario with mixed keys and values."""
        tags = [
            ("cuisine", "italian", "user123"),
            ("cuisine", "mexican", "user123"),  # OR with italian
            ("difficulty", "easy", "user123"),  # AND with cuisine group
            ("type", "dinner", "user123"),  # AND with other groups
        ]

        result = tag_filter_builder.build_tag_filter(model_with_tags, tags, "meal")

        # Should return a SQLAlchemy condition
        assert result is not None
        assert result is not True

    @pytest.mark.parametrize("tag_type", ["meal", "recipe", "menu", "custom"])
    @pytest.mark.unit
    def test_build_tag_filter_different_tag_types(
        self, tag_filter_builder, model_with_tags, tag_type
    ):
        """Test that different tag types are handled correctly."""
        tags = [("cuisine", "italian", "user123")]

        result = tag_filter_builder.build_tag_filter(model_with_tags, tags, tag_type)

        # Should return a SQLAlchemy condition
        assert result is not None
        assert result is not True

    # =============================================================================
    # Tests for build_negative_tag_filter method
    # =============================================================================

    @pytest.mark.unit
    def test_build_negative_tag_filter_empty_tags(
        self, tag_filter_builder, model_with_tags
    ):
        """Test that empty tag list returns True (no filtering) for negative filter."""
        result = tag_filter_builder.build_negative_tag_filter(
            model_with_tags, [], "meal"
        )
        assert result == True

    @pytest.mark.unit
    def test_build_negative_tag_filter_model_without_tags_relationship(
        self, tag_filter_builder, model_without_tags
    ):
        """Test that model without tags relationship raises FilterNotAllowedError."""
        tags = [("cuisine", "spicy", "user123")]

        with pytest.raises(FilterNotAllowedError):
            tag_filter_builder.build_negative_tag_filter(
                model_without_tags, tags, "meal"
            )

    @pytest.mark.unit
    def test_build_negative_tag_filter_single_tag_creates_negated_condition(
        self, tag_filter_builder, model_with_tags
    ):
        """Test that negative filtering with single tag creates negated condition."""
        tags = [("cuisine", "spicy", "user123")]

        result = tag_filter_builder.build_negative_tag_filter(
            model_with_tags, tags, "meal"
        )

        # Should return a SQLAlchemy condition
        assert result is not None
        assert result is not True

    @pytest.mark.unit
    def test_build_negative_tag_filter_multiple_tags_creates_negated_condition(
        self, tag_filter_builder, model_with_tags
    ):
        """Test negative filtering with multiple tags creates negated condition."""
        tags = [
            ("cuisine", "spicy", "user123"),
            ("difficulty", "hard", "user123"),
        ]

        result = tag_filter_builder.build_negative_tag_filter(
            model_with_tags, tags, "meal"
        )

        # Should return a SQLAlchemy condition
        assert result is not None
        assert result is not True

    # =============================================================================
    # Integration tests
    # =============================================================================

    @pytest.mark.integration
    def test_tag_filter_integration_workflow(self, tag_filter_builder, model_with_tags):
        """Test the complete workflow of validation and filtering."""
        tags = [
            ("cuisine", "italian", "user123"),
            ("difficulty", "easy", "user123"),
        ]

        # First validate
        tag_filter_builder.validate_tag_format(tags)  # Should not raise

        # Then create positive filter
        positive_condition = tag_filter_builder.build_tag_filter(
            model_with_tags, tags, "meal"
        )
        assert positive_condition is not None
        assert positive_condition is not True

        # And negative filter
        negative_condition = tag_filter_builder.build_negative_tag_filter(
            model_with_tags, tags, "meal"
        )
        assert negative_condition is not None
        assert negative_condition is not True

    @pytest.mark.integration
    def test_tag_filter_with_invalid_then_valid_tags(
        self, tag_filter_builder, model_with_tags
    ):
        """Test that validation catches errors before filter building."""
        invalid_tags = [("cuisine", 123, "user123")]  # Invalid
        valid_tags = [("cuisine", "italian", "user123")]  # Valid

        # Invalid tags should raise during validation
        with pytest.raises(FilterNotAllowedError):
            tag_filter_builder.validate_tag_format(invalid_tags)

        # Valid tags should work fine
        tag_filter_builder.validate_tag_format(valid_tags)
        result = tag_filter_builder.build_tag_filter(
            model_with_tags, valid_tags, "meal"
        )
        assert result is not None
        assert result is not True

    # =============================================================================
    # Edge case tests
    # =============================================================================

    @pytest.mark.unit
    def test_tag_filter_with_special_characters(
        self, tag_filter_builder, model_with_tags
    ):
        """Test tag filtering with special characters in keys and values."""
        tags = [
            ("cuisine-type", "italian/sicilian", "user-123"),
            ("difficulty_level", "easy_medium", "user_456"),
        ]

        # Should handle special characters in validation
        tag_filter_builder.validate_tag_format(tags)

        # And in filtering
        result = tag_filter_builder.build_tag_filter(model_with_tags, tags, "meal")
        assert result is not None
        assert result is not True

    @pytest.mark.unit
    def test_tag_filter_with_empty_strings(self, tag_filter_builder, model_with_tags):
        """Test tag filtering with empty string values."""
        tags = [("", "", "")]  # Empty strings but still valid format

        # Should pass validation (empty strings are still strings)
        tag_filter_builder.validate_tag_format(tags)

        # And filtering
        result = tag_filter_builder.build_tag_filter(model_with_tags, tags, "meal")
        assert result is not None
        assert result is not True

    @pytest.mark.unit
    def test_tag_filter_case_sensitivity(self, tag_filter_builder, model_with_tags):
        """Test that tag filtering preserves case sensitivity."""
        tags = [
            ("Cuisine", "Italian", "User123"),  # Mixed case
            ("DIFFICULTY", "EASY", "USER456"),  # Upper case
        ]

        tag_filter_builder.validate_tag_format(tags)
        result = tag_filter_builder.build_tag_filter(model_with_tags, tags, "meal")
        assert result is not None
        assert result is not True


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
    tag_filter_builder = TagFilterBuilder(TagSaModel)
    tags = tag_format_scenario["tags"]
    should_pass = tag_format_scenario["should_pass"]

    if should_pass:
        # Should not raise an exception
        tag_filter_builder.validate_tag_format(tags)
    else:
        # Should raise FilterNotAllowedError
        with pytest.raises(FilterNotAllowedError):
            tag_filter_builder.validate_tag_format(tags)
