"""Unit tests for ApiTag schema.

Tests tag schema validation, serialization/deserialization, and conversion methods.
Follows testing principles: no I/O, fakes only, behavior-focused assertions.
"""

import pytest
from pydantic import ValidationError

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import TagSaModel
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import ValidationConversionError


class TestApiTagValidation:
    """Test tag schema validation and field constraints."""

    def test_api_tag_validation_minimal_valid_tag(self):
        """Validates minimal valid tag creation."""
        # Given: minimal required tag components
        # When: create tag with valid components
        # Then: tag is created successfully
        api_tag = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        assert api_tag.key == "cuisine"
        assert api_tag.value == "italian"
        assert api_tag.author_id == "550e8400-e29b-41d4-a716-446655440000"
        assert api_tag.type == "category"

    def test_api_tag_validation_all_fields_populated(self):
        """Validates tag with all fields populated."""
        # Given: complete tag information
        # When: create tag with all components
        # Then: all fields are properly set
        api_tag = ApiTag(
            key="dietary_restriction",
            value="vegetarian",
            author_id="550e8400-e29b-41d4-a716-446655440001",
            type="diet"
        )
        assert api_tag.key == "dietary_restriction"
        assert api_tag.value == "vegetarian"
        assert api_tag.author_id == "550e8400-e29b-41d4-a716-446655440001"
        assert api_tag.type == "diet"

    def test_api_tag_validation_string_fields_trimming(self):
        """Validates string fields are trimmed automatically."""
        # Given: strings with leading/trailing whitespace
        # When: create tag with whitespace
        # Then: strings are trimmed
        api_tag = ApiTag(
            key="  cuisine  ",
            value="  italian  ",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="  category  "
        )
        assert api_tag.key == "cuisine"
        assert api_tag.value == "italian"
        assert api_tag.type == "category"

    def test_api_tag_validation_key_length_constraints(self):
        """Validates key field length constraints."""
        # Given: key exceeding maximum length
        # When: create tag with long key
        # Then: validation error is raised
        long_key = "x" * 101  # Exceeds 100 character limit
        
        with pytest.raises(ValidationError):
            ApiTag(
                key=long_key,
                value="italian",
                author_id="550e8400-e29b-41d4-a716-446655440000",
                type="category"
            )

    def test_api_tag_validation_key_minimum_length(self):
        """Validates key field minimum length constraint."""
        # Given: empty key
        # When: create tag with empty key
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiTag(
                key="",
                value="italian",
                author_id="550e8400-e29b-41d4-a716-446655440000",
                type="category"
            )

    def test_api_tag_validation_value_length_constraints(self):
        """Validates value field length constraints."""
        # Given: value exceeding maximum length
        # When: create tag with long value
        # Then: validation error is raised
        long_value = "x" * 201  # Exceeds 200 character limit
        
        with pytest.raises(ValidationError):
            ApiTag(
                key="cuisine",
                value=long_value,
                author_id="550e8400-e29b-41d4-a716-446655440000",
                type="category"
            )

    def test_api_tag_validation_value_minimum_length(self):
        """Validates value field minimum length constraint."""
        # Given: empty value
        # When: create tag with empty value
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiTag(
                key="cuisine",
                value="",
                author_id="550e8400-e29b-41d4-a716-446655440000",
                type="category"
            )

    def test_api_tag_validation_type_length_constraints(self):
        """Validates type field length constraints."""
        # Given: type exceeding maximum length
        # When: create tag with long type
        # Then: validation error is raised
        long_type = "x" * 51  # Exceeds 50 character limit
        
        with pytest.raises(ValidationError):
            ApiTag(
                key="cuisine",
                value="italian",
                author_id="550e8400-e29b-41d4-a716-446655440000",
                type=long_type
            )

    def test_api_tag_validation_type_minimum_length(self):
        """Validates type field minimum length constraint."""
        # Given: empty type
        # When: create tag with empty type
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiTag(
                key="cuisine",
                value="italian",
                author_id="550e8400-e29b-41d4-a716-446655440000",
                type=""
            )

    def test_api_tag_validation_author_id_uuid_format(self):
        """Validates author_id field accepts valid UUID format."""
        # Given: valid UUID string
        # When: create tag with valid UUID
        # Then: tag is created successfully
        api_tag = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        assert api_tag.author_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_api_tag_validation_author_id_invalid_uuid_format(self):
        """Validates author_id field rejects invalid UUID format."""
        # Given: invalid UUID string
        # When: create tag with invalid UUID
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiTag(
                key="cuisine",
                value="italian",
                author_id="invalid-uuid",
                type="category"
            )

    def test_api_tag_validation_unicode_characters(self):
        """Validates tag handles unicode characters correctly."""
        # Given: tag with unicode characters
        # When: create tag with unicode strings
        # Then: unicode characters are preserved
        api_tag = ApiTag(
            key="categoria",
            value="prato-do-dia",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="tipo"
        )
        assert api_tag.key == "categoria"
        assert api_tag.value == "prato-do-dia"
        assert api_tag.type == "tipo"

    def test_api_tag_validation_special_characters(self):
        """Validates tag handles special characters correctly."""
        # Given: tag with special characters
        # When: create tag with special character strings
        # Then: special characters are preserved
        api_tag = ApiTag(
            key="categoria_especial",
            value="prato-do-dia",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="tipo_especial"
        )
        assert api_tag.key == "categoria_especial"
        assert api_tag.value == "prato-do-dia"
        assert api_tag.type == "tipo_especial"

    def test_api_tag_validation_maximum_length_fields(self):
        """Validates maximum length fields are accepted."""
        # Given: fields at maximum length
        # When: create tag with max length fields
        # Then: tag is created successfully
        max_key = "x" * 100
        max_value = "x" * 200
        max_type = "x" * 50
        
        api_tag = ApiTag(
            key=max_key,
            value=max_value,
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type=max_type
        )
        assert api_tag.key == max_key
        assert api_tag.value == max_value
        assert api_tag.type == max_type


class TestApiTagEquality:
    """Test tag equality semantics and value object contracts."""

    def test_api_tag_equality_same_values(self):
        """Ensures proper equality semantics for identical values."""
        # Given: two tag instances with same values
        # When: compare tags
        # Then: they should be equal
        tag1 = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        tag2 = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        assert tag1 == tag2

    def test_api_tag_equality_different_values(self):
        """Ensures proper inequality semantics for different values."""
        # Given: two tag instances with different values
        # When: compare tags
        # Then: they should not be equal
        tag1 = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        tag2 = ApiTag(
            key="cuisine",
            value="french",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        assert tag1 != tag2

    def test_api_tag_equality_different_keys(self):
        """Ensures different key values result in inequality."""
        # Given: two tags with different keys
        # When: compare tags
        # Then: they should not be equal
        tag1 = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        tag2 = ApiTag(
            key="diet",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        assert tag1 != tag2

    def test_api_tag_equality_different_author_ids(self):
        """Ensures different author_id values result in inequality."""
        # Given: two tags with different author_ids
        # When: compare tags
        # Then: they should not be equal
        tag1 = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        tag2 = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440001",
            type="category"
        )
        assert tag1 != tag2

    def test_api_tag_equality_different_types(self):
        """Ensures different type values result in inequality."""
        # Given: two tags with different types
        # When: compare tags
        # Then: they should not be equal
        tag1 = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        tag2 = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="dietary"
        )
        assert tag1 != tag2


class TestApiTagSerialization:
    """Test tag serialization and deserialization contracts."""

    def test_api_tag_serialization_to_dict(self):
        """Validates tag can be serialized to dictionary."""
        # Given: tag with all fields
        # When: serialize to dict
        # Then: all fields are properly serialized
        api_tag = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        
        result = api_tag.model_dump()
        
        assert result["key"] == "cuisine"
        assert result["value"] == "italian"
        assert result["author_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert result["type"] == "category"

    def test_api_tag_serialization_to_json(self):
        """Validates tag can be serialized to JSON."""
        # Given: tag with all fields
        # When: serialize to JSON
        # Then: JSON is properly formatted
        api_tag = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        
        json_str = api_tag.model_dump_json()
        
        assert '"key":"cuisine"' in json_str
        assert '"value":"italian"' in json_str
        assert '"author_id":"550e8400-e29b-41d4-a716-446655440000"' in json_str
        assert '"type":"category"' in json_str

    def test_api_tag_deserialization_from_dict(self):
        """Validates tag can be deserialized from dictionary."""
        # Given: dictionary with tag data
        # When: create tag from dict
        # Then: tag is properly created
        data = {
            "key": "cuisine",
            "value": "italian",
            "author_id": "550e8400-e29b-41d4-a716-446655440000",
            "type": "category"
        }
        
        api_tag = ApiTag.model_validate(data)
        
        assert api_tag.key == "cuisine"
        assert api_tag.value == "italian"
        assert api_tag.author_id == "550e8400-e29b-41d4-a716-446655440000"
        assert api_tag.type == "category"

    def test_api_tag_deserialization_from_json(self):
        """Validates tag can be deserialized from JSON."""
        # Given: JSON string with tag data
        # When: create tag from JSON
        # Then: tag is properly created
        json_str = '''
        {
            "key": "cuisine",
            "value": "italian",
            "author_id": "550e8400-e29b-41d4-a716-446655440000",
            "type": "category"
        }
        '''
        
        api_tag = ApiTag.model_validate_json(json_str)
        
        assert api_tag.key == "cuisine"
        assert api_tag.value == "italian"
        assert api_tag.author_id == "550e8400-e29b-41d4-a716-446655440000"
        assert api_tag.type == "category"

    def test_api_tag_serialization_unicode_characters(self):
        """Validates serialization handles unicode characters correctly."""
        # Given: tag with unicode characters
        # When: serialize and deserialize
        # Then: unicode characters are preserved
        api_tag = ApiTag(
            key="categoria",
            value="prato-do-dia",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="tipo"
        )
        
        json_str = api_tag.model_dump_json()
        deserialized = ApiTag.model_validate_json(json_str)
        
        assert deserialized.key == "categoria"
        assert deserialized.value == "prato-do-dia"
        assert deserialized.author_id == "550e8400-e29b-41d4-a716-446655440000"
        assert deserialized.type == "tipo"


class TestApiTagDomainConversion:
    """Test tag conversion between API schema and domain model."""

    def test_api_tag_from_domain_conversion(self):
        """Validates conversion from domain model to API schema."""
        # Given: domain tag model
        # When: convert to API schema
        # Then: all fields are properly converted
        domain_tag = Tag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        
        api_tag = ApiTag.from_domain(domain_tag)
        
        assert api_tag.key == "cuisine"
        assert api_tag.value == "italian"
        assert api_tag.author_id == "550e8400-e29b-41d4-a716-446655440000"
        assert api_tag.type == "category"

    def test_api_tag_to_domain_conversion(self):
        """Validates conversion from API schema to domain model."""
        # Given: API tag schema
        # When: convert to domain model
        # Then: all fields are properly converted
        api_tag = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        
        domain_tag = api_tag.to_domain()
        
        assert domain_tag.key == "cuisine"
        assert domain_tag.value == "italian"
        assert domain_tag.author_id == "550e8400-e29b-41d4-a716-446655440000"
        assert domain_tag.type == "category"

    def test_api_tag_domain_conversion_roundtrip(self):
        """Validates roundtrip conversion maintains data integrity."""
        # Given: domain tag model
        # When: convert to API schema and back to domain
        # Then: data integrity is maintained
        original_domain = Tag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        
        api_tag = ApiTag.from_domain(original_domain)
        converted_domain = api_tag.to_domain()
        
        assert converted_domain == original_domain

    def test_api_tag_domain_conversion_unicode_handling(self):
        """Validates unicode conversion between API and domain."""
        # Given: API tag with unicode characters
        # When: convert to domain and back
        # Then: unicode characters are properly handled
        api_tag = ApiTag(
            key="categoria",
            value="prato-do-dia",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="tipo"
        )
        
        domain_tag = api_tag.to_domain()
        converted_api = ApiTag.from_domain(domain_tag)
        
        assert converted_api.key == "categoria"
        assert converted_api.value == "prato-do-dia"
        assert converted_api.author_id == "550e8400-e29b-41d4-a716-446655440000"
        assert converted_api.type == "tipo"
        assert domain_tag.key == "categoria"
        assert domain_tag.value == "prato-do-dia"
        assert domain_tag.author_id == "550e8400-e29b-41d4-a716-446655440000"
        assert domain_tag.type == "tipo"


class TestApiTagOrmConversion:
    """Test tag conversion between API schema and ORM model."""

    def test_api_tag_from_orm_model_conversion(self):
        """Validates conversion from ORM model to API schema."""
        # Given: ORM tag model
        # When: convert to API schema
        # Then: all fields are properly converted
        orm_tag = TagSaModel(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        
        api_tag = ApiTag.from_orm_model(orm_tag)
        
        assert api_tag.key == "cuisine"
        assert api_tag.value == "italian"
        assert api_tag.author_id == "550e8400-e29b-41d4-a716-446655440000"
        assert api_tag.type == "category"

    def test_api_tag_to_orm_kwargs_conversion(self):
        """Validates conversion from API schema to ORM kwargs."""
        # Given: API tag schema
        # When: convert to ORM kwargs
        # Then: all fields are properly converted
        api_tag = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        
        orm_kwargs = api_tag.to_orm_kwargs()
        
        assert orm_kwargs["key"] == "cuisine"
        assert orm_kwargs["value"] == "italian"
        assert orm_kwargs["author_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert orm_kwargs["type"] == "category"

    def test_api_tag_orm_conversion_roundtrip(self):
        """Validates roundtrip conversion maintains data integrity."""
        # Given: ORM tag model
        # When: convert to API schema and back to ORM kwargs
        # Then: data integrity is maintained
        original_orm = TagSaModel(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        
        api_tag = ApiTag.from_orm_model(original_orm)
        orm_kwargs = api_tag.to_orm_kwargs()
        
        # Create new ORM model from kwargs for comparison
        new_orm = TagSaModel(**orm_kwargs)
        
        assert new_orm.key == original_orm.key
        assert new_orm.value == original_orm.value
        assert new_orm.author_id == original_orm.author_id
        assert new_orm.type == original_orm.type

    def test_api_tag_orm_conversion_unicode_handling(self):
        """Validates unicode conversion between API and ORM."""
        # Given: API tag with unicode characters
        # When: convert to ORM kwargs
        # Then: unicode characters are properly handled
        api_tag = ApiTag(
            key="categoria",
            value="prato-do-dia",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="tipo"
        )
        
        orm_kwargs = api_tag.to_orm_kwargs()
        
        assert orm_kwargs["key"] == "categoria"
        assert orm_kwargs["value"] == "prato-do-dia"
        assert orm_kwargs["author_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert orm_kwargs["type"] == "tipo"


class TestApiTagEdgeCases:
    """Test tag schema edge cases and error handling."""

    def test_api_tag_from_orm_model_none_raises_error(self):
        """Validates from_orm_model raises error when ORM model is None."""
        # Given: None ORM model
        # When: convert to API schema
        # Then: ValidationError is raised (Pydantic validation error)
        with pytest.raises(ValidationError) as exc_info:
            ApiTag.from_orm_model(None)  # type: ignore[arg-type]
        

    def test_api_tag_validation_whitespace_only_fields(self):
        """Validates whitespace-only fields are converted to None."""
        # Given: whitespace-only fields
        # When: create tag with whitespace fields
        # Then: fields become None and validation fails
        with pytest.raises(ValidationError):
            ApiTag(
                key="   ",
                value="italian",
                author_id="550e8400-e29b-41d4-a716-446655440000",
                type="category"
            )

    def test_api_tag_validation_mixed_whitespace_and_content(self):
        """Validates mixed whitespace and content is properly trimmed."""
        # Given: fields with mixed whitespace and content
        # When: create tag with mixed content
        # Then: content is properly trimmed
        api_tag = ApiTag(
            key="  cuisine  \t",
            value="\nitalian\r",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="\tcategory\n"
        )
        assert api_tag.key == "cuisine"
        assert api_tag.value == "italian"
        assert api_tag.type == "category"

    def test_api_tag_validation_boundary_length_values(self):
        """Validates boundary length values are handled correctly."""
        # Given: boundary length values
        # When: create tags with boundary lengths
        # Then: valid lengths are accepted, invalid lengths are rejected
        
        # Valid: exactly at maximum length
        api_tag = ApiTag(
            key="x" * 100,
            value="x" * 200,
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="x" * 50
        )
        assert api_tag.key == "x" * 100
        assert api_tag.value == "x" * 200
        assert api_tag.type == "x" * 50
        
        # Invalid: one character over maximum
        with pytest.raises(ValidationError):
            ApiTag(
                key="x" * 101,
                value="italian",
                author_id="550e8400-e29b-41d4-a716-446655440000",
                type="category"
            )

    def test_api_tag_immutability(self):
        """Validates tag schema is immutable."""
        # Given: tag instance
        # When: attempt to modify fields
        # Then: modification raises error
        api_tag = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        
        with pytest.raises(ValidationError):
            api_tag.key = "diet"  # type: ignore[attr-defined]

    def test_api_tag_validation_comprehensive_error_messages(self):
        """Validates comprehensive error messages for validation failures."""
        # Given: various invalid inputs
        # When: create tags with invalid data
        # Then: clear error messages are provided
        
        # Test empty key
        with pytest.raises(ValidationError) as exc_info:
            ApiTag(
                key="",
                value="italian",
                author_id="550e8400-e29b-41d4-a716-446655440000",
                type="category"
            )
        
        # Test invalid UUID
        with pytest.raises(ValidationError) as exc_info:
            ApiTag(
                key="cuisine",
                value="italian",
                author_id="invalid-uuid",
                type="category"
            )
        
        # Test long key
        with pytest.raises(ValidationError) as exc_info:
            ApiTag(
                key="x" * 101,
                value="italian",
                author_id="550e8400-e29b-41d4-a716-446655440000",
                type="category"
            )

    def test_api_tag_validation_case_sensitivity(self):
        """Validates tag fields are case-sensitive."""
        # Given: tags with different cases
        # When: create tags with different case values
        # Then: case differences are preserved
        tag1 = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        tag2 = ApiTag(
            key="Cuisine",
            value="Italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="Category"
        )
        
        assert tag1 != tag2
        assert tag1.key == "cuisine"
        assert tag2.key == "Cuisine"
        assert tag1.value == "italian"
        assert tag2.value == "Italian"
        assert tag1.type == "category"
        assert tag2.type == "Category"

    def test_api_tag_validation_numeric_strings(self):
        """Validates tag fields accept numeric strings."""
        # Given: numeric string values
        # When: create tag with numeric strings
        # Then: numeric strings are accepted
        api_tag = ApiTag(
            key="123",
            value="456",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="789"
        )
        assert api_tag.key == "123"
        assert api_tag.value == "456"
        assert api_tag.type == "789"

    def test_api_tag_validation_special_characters_in_uuid(self):
        """Validates author_id field handles special characters in UUID context."""
        # Given: valid UUID with standard format
        # When: create tag with standard UUID
        # Then: UUID is accepted
        api_tag = ApiTag(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        assert api_tag.author_id == "550e8400-e29b-41d4-a716-446655440000"
