"""
Comprehensive tests for BaseApiFilter class.

Tests cover filter validation, tag parsing, model dumping, and all filter functionality.
"""

from datetime import UTC, datetime
from typing import ClassVar

import pytest
from pydantic import ValidationError
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.base_api_filter import (
    BaseMealApiFilter,
)
from src.contexts.shared_kernel.domain.enums import Privacy


class TestBaseApiFilter:
    """Test suite for BaseApiFilter class."""

    @pytest.mark.unit
    def test_basic_filter_creation(self):
        """Test creating a basic filter with minimal fields."""
        filter_data = {
            "name": "test_meal",
            "limit": 50,
        }
        filter_obj = BaseMealApiFilter(**filter_data)

        assert filter_obj.name == "test_meal"
        assert filter_obj.limit == 50
        assert filter_obj.skip is None
        assert filter_obj.sort == "-created_at"  # default value

    @pytest.mark.unit
    def test_filter_with_all_fields(self):
        """Test creating a filter with all possible fields."""
        filter_data = {
            "id": "meal1|meal2|meal3",
            "name": "test_meal",
            "author_id": "user1|user2",
            "total_time_gte": 30,
            "total_time_lte": 60,
            "products": "product1|product2",
            "tags": "cuisine:italian|mediterranean,meal_type:breakfast",
            "tags_not_exists": "allergen:dairy|nuts",
            "privacy": Privacy.PUBLIC,
            "calories_gte": 200,
            "calories_lte": 500,
            "protein_gte": 20,
            "weight_in_grams_gte": 100,
            "created_at_gte": datetime.now(UTC),
            "skip": 10,
            "limit": 25,
            "sort": "name",
        }
        filter_api = BaseMealApiFilter(**filter_data)
        filter_dict = filter_api.model_dump()

        # Verify all fields are set correctly
        assert filter_dict["id"] == ["meal1", "meal2", "meal3"]
        assert filter_dict["name"] == "test_meal"
        assert filter_dict["author_id"] == ["user1", "user2"]
        assert filter_dict["total_time_gte"] == 30
        assert filter_dict["total_time_lte"] == 60
        assert filter_dict["products"] == ["product1", "product2"]
        assert filter_dict["privacy"] == Privacy.PUBLIC
        assert filter_dict["calories_gte"] == 200
        assert filter_dict["calories_lte"] == 500
        assert filter_dict["protein_gte"] == 20
        assert filter_dict["weight_in_grams_gte"] == 100
        assert filter_dict["skip"] == 10
        assert filter_dict["limit"] == 25
        assert filter_dict["sort"] == "name"

    @pytest.mark.unit
    def test_tag_parsing_simple(self):
        """Test parsing simple tag strings."""
        filter_obj = BaseMealApiFilter(tags="cuisine:italian|mediterranean")
        data = filter_obj.model_dump()

        assert data["tags"] == {"cuisine": ["italian", "mediterranean"]}

    @pytest.mark.unit
    def test_tag_parsing_complex(self):
        """Test parsing complex tag strings with multiple groups."""
        filter_obj = BaseMealApiFilter(
            tags="cuisine:italian|mediterranean,meal_type:breakfast|lunch,spice_level:hot"
        )
        data = filter_obj.model_dump()

        expected = {
            "cuisine": ["italian", "mediterranean"],
            "meal_type": ["breakfast", "lunch"],
            "spice_level": ["hot"],
        }
        assert data["tags"] == expected

    @pytest.mark.unit
    def test_tag_parsing_with_global_tags(self):
        """Test parsing tags without keys (global tags)."""
        filter_obj = BaseMealApiFilter(tags="quick,easy,healthy")
        data = filter_obj.model_dump()

        assert data["tags"] == {"global": ["quick", "easy", "healthy"]}

    @pytest.mark.unit
    def test_tag_parsing_mixed(self):
        """Test parsing mixed keyed and global tags."""
        filter_obj = BaseMealApiFilter(tags="cuisine:italian,quick,meal_type:breakfast")
        data = filter_obj.model_dump()

        expected = {
            "cuisine": ["italian"],
            "global": ["quick"],
            "meal_type": ["breakfast"],
        }
        assert data["tags"] == expected

    @pytest.mark.unit
    def test_tag_parsing_none(self):
        """Test parsing None tags."""
        filter_obj = BaseMealApiFilter(tags=None)
        data = filter_obj.model_dump()

        assert data["tags"] is None

    @pytest.mark.unit
    def test_tag_parsing_empty_string(self):
        """Test parsing empty string tags."""
        filter_obj = BaseMealApiFilter(tags="")
        data = filter_obj.model_dump()

        assert data["tags"] == {}

    @pytest.mark.unit
    def test_pipe_separated_strings(self):
        """Test converting pipe-separated strings to lists."""
        filter_obj = BaseMealApiFilter(
            id="meal1|meal2|meal3",
            author_id="user1|user2",
            products="product1|product2|product3",
        )
        data = filter_obj.model_dump()

        assert data["id"] == ["meal1", "meal2", "meal3"]
        assert data["author_id"] == ["user1", "user2"]
        assert data["products"] == ["product1", "product2", "product3"]

    @pytest.mark.unit
    def test_mixed_string_types(self):
        """Test mixing pipe-separated and regular strings."""
        filter_obj = BaseMealApiFilter(
            id="meal1|meal2",
            name="single_name",
            author_id="user1",
        )
        data = filter_obj.model_dump()

        assert data["id"] == ["meal1", "meal2"]
        assert data["name"] == "single_name"
        assert data["author_id"] == "user1"

    @pytest.mark.unit
    def test_nutritional_filters(self):
        """Test all nutritional filter fields."""
        filter_obj = BaseMealApiFilter(
            calories_gte=200.5,
            calories_lte=500.0,
            protein_gte=20.0,
            protein_lte=50.0,
            carbohydrate_gte=30.0,
            carbohydrate_lte=80.0,
            total_fat_gte=10.0,
            total_fat_lte=25.0,
            saturated_fat_gte=2.0,
            saturated_fat_lte=8.0,
            trans_fat_gte=0.0,
            trans_fat_lte=1.0,
            sugar_gte=5.0,
            sugar_lte=20.0,
            sodium_gte=100,
            sodium_lte=500,
            calorie_density_gte=1.0,
            calorie_density_lte=3.0,
            carbo_percentage_gte=40,
            carbo_percentage_lte=60,
            protein_percentage_gte=20,
            protein_percentage_lte=30,
            total_fat_percentage_gte=20,
            total_fat_percentage_lte=35,
        )

        # Verify all nutritional fields are set
        assert filter_obj.calories_gte == 200.5
        assert filter_obj.calories_lte == 500.0
        assert filter_obj.protein_gte == 20.0
        assert filter_obj.protein_lte == 50.0
        assert filter_obj.carbohydrate_gte == 30.0
        assert filter_obj.carbohydrate_lte == 80.0
        assert filter_obj.total_fat_gte == 10.0
        assert filter_obj.total_fat_lte == 25.0
        assert filter_obj.saturated_fat_gte == 2.0
        assert filter_obj.saturated_fat_lte == 8.0
        assert filter_obj.trans_fat_gte == 0.0
        assert filter_obj.trans_fat_lte == 1.0
        assert filter_obj.sugar_gte == 5.0
        assert filter_obj.sugar_lte == 20.0
        assert filter_obj.sodium_gte == 100
        assert filter_obj.sodium_lte == 500
        assert filter_obj.calorie_density_gte == 1.0
        assert filter_obj.calorie_density_lte == 3.0
        assert filter_obj.carbo_percentage_gte == 40
        assert filter_obj.carbo_percentage_lte == 60
        assert filter_obj.protein_percentage_gte == 20
        assert filter_obj.protein_percentage_lte == 30
        assert filter_obj.total_fat_percentage_gte == 20
        assert filter_obj.total_fat_percentage_lte == 35

    @pytest.mark.unit
    def test_privacy_filters(self):
        """Test privacy filter fields."""
        filter_obj = BaseMealApiFilter(privacy=Privacy.PUBLIC)
        assert filter_obj.privacy == Privacy.PUBLIC

        filter_obj = BaseMealApiFilter(privacy=[Privacy.PUBLIC, Privacy.PRIVATE])
        assert filter_obj.privacy == [Privacy.PUBLIC, Privacy.PRIVATE]

    @pytest.mark.unit
    def test_time_filters(self):
        """Test time-based filter fields."""
        filter_obj = BaseMealApiFilter(
            total_time_gte=30,
            total_time_lte=60,
        )

        assert filter_obj.total_time_gte == 30
        assert filter_obj.total_time_lte == 60

    @pytest.mark.unit
    def test_weight_filters(self):
        """Test weight filter fields."""
        filter_obj = BaseMealApiFilter(
            weight_in_grams_gte=100,
            weight_in_grams_lte=500,
        )

        assert filter_obj.weight_in_grams_gte == 100
        assert filter_obj.weight_in_grams_lte == 500

    @pytest.mark.unit
    def test_temporal_filters(self):
        """Test temporal filter fields."""
        now = datetime.now(UTC)
        filter_obj = BaseMealApiFilter(
            created_at_gte=now,
            created_at_lte=now,
        )

        assert filter_obj.created_at_gte == now
        assert filter_obj.created_at_lte == now

    @pytest.mark.unit
    def test_pagination_filters(self):
        """Test pagination filter fields."""
        filter_obj = BaseMealApiFilter(
            skip=20,
            limit=50,
            sort="name",
        )

        assert filter_obj.skip == 20
        assert filter_obj.limit == 50
        assert filter_obj.sort == "name"

    @pytest.mark.unit
    def test_default_values(self):
        """Test default values are set correctly."""
        filter_obj = BaseMealApiFilter()

        assert filter_obj.limit == 100
        assert filter_obj.sort == "-created_at"
        assert filter_obj.skip is None
        assert filter_obj.id is None
        assert filter_obj.name is None

    @pytest.mark.unit
    def test_limit_validation(self):
        """Test limit field validation constraints."""
        # Test minimum value
        with pytest.raises(ValidationError):
            BaseMealApiFilter(limit=0)

        # Test maximum value
        with pytest.raises(ValidationError):
            BaseMealApiFilter(limit=1001)

        # Test valid values
        BaseMealApiFilter(limit=1)
        BaseMealApiFilter(limit=1000)
        BaseMealApiFilter(limit=500)

    @pytest.mark.unit
    def test_get_allowed_filters(self):
        """Test getting allowed filter keys."""
        filter_obj = BaseMealApiFilter()
        allowed = filter_obj.get_allowed_filters()

        expected = [
            "discarded",
            "skip",
            "limit",
            "sort",
            "created_at",
            "tags",
            "tags_not_exists",
        ]
        assert allowed == expected

    @pytest.mark.integration
    def test_validate_repository_filters(self):
        """Test repository filter validation."""
        filter_obj = BaseMealApiFilter()

        # Test with valid filters
        values = {"skip": 10, "limit": 50, "name": "test"}
        result = filter_obj.validate_repository_filters(values, None)
        assert result == values

        # Test with invalid filter
        values = {"invalid_filter": "value"}
        with pytest.raises(ValueError, match="Invalid filter: invalid_filter"):
            filter_obj.validate_repository_filters(values, None)

    @pytest.mark.integration
    def test_validate_repository_filters_with_mappers(self):
        """Test repository filter validation with mappers."""
        filter_obj = BaseMealApiFilter()

        # Mock mapper with filter keys
        class MockMapper:
            filter_key_to_column_name: ClassVar[dict[str, str]] = {
                "name": "name",
                "author_id": "author_id",
            }

        mappers = [MockMapper()]

        # Test with valid filters
        values = {"name": "test", "author_id": "user1"}
        result = filter_obj.validate_repository_filters(values, mappers)
        assert result == values

        # Test with invalid filter
        values = {"invalid_filter": "value"}
        with pytest.raises(ValueError, match="Invalid filter: invalid_filter"):
            filter_obj.validate_repository_filters(values, mappers)

    @pytest.mark.unit
    def test_model_dump_preserves_original_data(self):
        """Test that model_dump preserves original data structure."""
        filter_obj = BaseMealApiFilter(
            id="meal1|meal2",
            name="test_meal",
            tags="cuisine:italian|mediterranean",
            calories_gte=200,
        )

        data = filter_obj.model_dump()

        # Verify processed fields
        assert data["id"] == ["meal1", "meal2"]
        assert data["tags"] == {"cuisine": ["italian", "mediterranean"]}

        # Verify unprocessed fields
        assert data["name"] == "test_meal"
        assert data["calories_gte"] == 200

    @pytest.mark.unit
    def test_filter_inheritance_compatibility(self):
        """Test that the filter can be properly inherited from."""

        class TestFilter(BaseMealApiFilter):
            custom_field: str | None = None

        filter_obj = TestFilter(
            name="test",
            custom_field="custom_value",
            id="item1|item2",
        )

        assert filter_obj.name == "test"
        assert filter_obj.custom_field == "custom_value"

        data = filter_obj.model_dump()
        assert data["id"] == ["item1", "item2"]
        assert data["custom_field"] == "custom_value"

    @pytest.mark.unit
    def test_edge_cases(self):
        """Test various edge cases and boundary conditions."""
        # Empty strings
        filter_obj = BaseMealApiFilter(
            id="",
            tags="",
            name="",
        )
        data = filter_obj.model_dump()
        assert data["id"] == [""]
        assert data["tags"] == {}
        assert data["name"] == ""

        # Whitespace handling
        filter_obj = BaseMealApiFilter(
            id="  item1  |  item2  ",
            tags="  key  :  value1  |  value2  ",
        )
        data = filter_obj.model_dump()
        assert data["id"] == ["  item1  ", "  item2  "]
        assert data["tags"] == {"  key  ": ["  value1  ", "  value2  "]}

        # Single item with pipe
        filter_obj = BaseMealApiFilter(id="item1|")
        data = filter_obj.model_dump()
        assert data["id"] == ["item1", ""]

        # Multiple consecutive pipes
        filter_obj = BaseMealApiFilter(id="item1||item2")
        data = filter_obj.model_dump()
        assert data["id"] == ["item1", "", "item2"]
