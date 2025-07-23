import pytest
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import TagSaModel


class TestApiTag:
    """Test suite for ApiTag schema."""

    @pytest.mark.parametrize("key,value,author_id,type", [
        ("category", "food", "550e8400-e29b-41d4-a716-446655440000", "recipe"),
        ("cuisine", "italian", "550e8400-e29b-41d4-a716-446655440001", "restaurant"),
        ("diet", "vegetarian", "550e8400-e29b-41d4-a716-446655440002", "preference"),
    ])
    def test_create_valid_tag(self, key: str, value: str, author_id: str, type: str):
        """Test creating valid tags with different combinations of values."""
        tag = ApiTag(
            key=key,
            value=value,
            author_id=author_id,
            type=type
        )
        assert tag.key == key
        assert tag.value == value
        assert tag.author_id == author_id
        assert tag.type == type

    def test_from_domain(self):
        """Test creating an ApiTag from a domain Tag object."""
        domain_tag = Tag(
            key="category",
            value="food",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="recipe"
        )
        api_tag = ApiTag.from_domain(domain_tag)
        
        assert api_tag.key == domain_tag.key
        assert api_tag.value == domain_tag.value
        assert api_tag.author_id == domain_tag.author_id
        assert api_tag.type == domain_tag.type

    def test_to_domain(self):
        """Test converting an ApiTag to a domain Tag object."""
        api_tag = ApiTag(
            key="category",
            value="food",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="recipe"
        )
        domain_tag = api_tag.to_domain()
        
        assert domain_tag.key == api_tag.key
        assert domain_tag.value == api_tag.value
        assert domain_tag.author_id == api_tag.author_id
        assert domain_tag.type == api_tag.type

    def test_from_orm_model(self):
        """Test creating an ApiTag from an ORM model."""
        # Create a mock ORM model with required attributes
        orm_model = TagSaModel()
        orm_model.key = "category"
        orm_model.value = "food"
        orm_model.author_id = "550e8400-e29b-41d4-a716-446655440000"
        orm_model.type = "recipe"
        
        api_tag = ApiTag.from_orm_model(orm_model)
        
        assert api_tag.key == orm_model.key
        assert api_tag.value == orm_model.value
        assert api_tag.author_id == orm_model.author_id
        assert api_tag.type == orm_model.type

    def test_to_orm_kwargs(self):
        """Test converting an ApiTag to ORM model kwargs."""
        api_tag = ApiTag(
            key="category",
            value="food",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="recipe"
        )
        kwargs = api_tag.to_orm_kwargs()
        
        assert kwargs["key"] == api_tag.key
        assert kwargs["value"] == api_tag.value
        assert kwargs["author_id"] == api_tag.author_id
        assert kwargs["type"] == api_tag.type

    def test_immutability(self):
        """Test that the tag is immutable after creation."""
        tag = ApiTag(
            key="category",
            value="food",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="recipe"
        )
        with pytest.raises(ValueError):
            tag.key = "new_category"

    def test_serialization(self):
        """Test that the tag can be serialized to a dictionary."""
        tag = ApiTag(
            key="category",
            value="food",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="recipe"
        )
        serialized = tag.model_dump()
        
        assert serialized["key"] == tag.key
        assert serialized["value"] == tag.value
        assert serialized["author_id"] == tag.author_id
        assert serialized["type"] == tag.type

    def test_deserialization(self):
        """Test that the tag can be deserialized from a dictionary."""
        data = {
            "key": "category",
            "value": "food",
            "author_id": "550e8400-e29b-41d4-a716-446655440000",
            "type": "recipe"
        }
        tag = ApiTag.model_validate(data)
        
        assert tag.key == data["key"]
        assert tag.value == data["value"]
        assert tag.author_id == data["author_id"]
        assert tag.type == data["type"] 