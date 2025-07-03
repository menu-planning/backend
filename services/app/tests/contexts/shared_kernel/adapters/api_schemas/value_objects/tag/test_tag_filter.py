import pytest
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag_filter import ApiTagFilter


class TestApiTagFilter:
    """Test suite for ApiTagFilter schema."""

    def test_create_valid_tag_filter(self):
        """Test creating a valid tag filter."""
        tag_filter = ApiTagFilter(
            key="category",
            value="food",
            author_id="user_123",
            type="recipe",
            skip=0,
            limit=10,
            sort="-key"
        )
        assert tag_filter.key == "category"
        assert tag_filter.value == "food"
        assert tag_filter.author_id == "user_123"
        assert tag_filter.type == "recipe"
        assert tag_filter.skip == 0
        assert tag_filter.limit == 10
        assert tag_filter.sort == "-key"

    def test_create_minimal_tag_filter(self):
        """Test creating a tag filter with minimal fields."""
        tag_filter = ApiTagFilter()
        assert tag_filter.key is None
        assert tag_filter.value is None
        assert tag_filter.author_id is None
        assert tag_filter.type is None
        assert tag_filter.skip is None
        assert tag_filter.limit == 100
        assert tag_filter.sort == "-key"

    def test_create_with_list_values(self):
        """Test creating a tag filter with list values."""
        tag_filter = ApiTagFilter(
            key=["category1", "category2"],
            value=["value1", "value2"],
            author_id=["user1", "user2"],
            type=["type1", "type2"]
        )
        assert tag_filter.key == ["category1", "category2"]
        assert tag_filter.value == ["value1", "value2"]
        assert tag_filter.author_id == ["user1", "user2"]
        assert tag_filter.type == ["type1", "type2"]

    def test_to_domain(self):
        """Test converting to domain filter dictionary."""
        tag_filter = ApiTagFilter(
            key="category",
            value="food",
            author_id="user_123",
            type="recipe",
            skip=0,
            limit=10,
            sort="-key"
        )
        domain_filter = tag_filter.to_domain()
        
        assert domain_filter["key"] == "category"
        assert domain_filter["value"] == "food"
        assert domain_filter["author_id"] == "user_123"
        assert domain_filter["type"] == "recipe"
        assert domain_filter["skip"] == 0
        assert domain_filter["limit"] == 10
        assert domain_filter["sort"] == "-key"

    def test_to_domain_with_list_values(self):
        """Test converting to domain filter dictionary with list values."""
        tag_filter = ApiTagFilter(
            key=["category1", "category2"],
            value=["value1", "value2"],
            author_id=["user1", "user2"],
            type=["type1", "type2"]
        )
        domain_filter = tag_filter.to_domain()
        
        assert domain_filter["key"] == ["category1", "category2"]
        assert domain_filter["value"] == ["value1", "value2"]
        assert domain_filter["author_id"] == ["user1", "user2"]
        assert domain_filter["type"] == ["type1", "type2"]

    def test_serialization(self):
        """Test that the tag filter serializes correctly."""
        tag_filter = ApiTagFilter(
            key="category",
            value="food",
            author_id="user_123",
            type="recipe",
            skip=0,
            limit=10,
            sort="-key"
        )
        serialized = tag_filter.model_dump()
        
        assert serialized["key"] == "category"
        assert serialized["value"] == "food"
        assert serialized["author_id"] == "user_123"
        assert serialized["type"] == "recipe"
        assert serialized["skip"] == 0
        assert serialized["limit"] == 10
        assert serialized["sort"] == "-key"

    def test_serialization_with_list_values(self):
        """Test that the tag filter serializes correctly with list values."""
        tag_filter = ApiTagFilter(
            key=["category1", "category2"],
            value=["value1", "value2"],
            author_id=["user1", "user2"],
            type=["type1", "type2"]
        )
        serialized = tag_filter.model_dump()
        
        assert serialized["key"] == ["category1", "category2"]
        assert serialized["value"] == ["value1", "value2"]
        assert serialized["author_id"] == ["user1", "user2"]
        assert serialized["type"] == ["type1", "type2"]

    def test_immutability(self):
        """Test that the tag filter is immutable."""
        tag_filter = ApiTagFilter(
            key="category",
            value="food"
        )
        with pytest.raises(ValueError):
            tag_filter.key = "new_category" 