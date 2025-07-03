"""
Comprehensive behavior-focused tests for ApiTag schema standardization.

Following Phase 1 patterns: 80+ test methods with >95% coverage, behavior-focused approach,
round-trip validation, comprehensive error handling, edge cases, and performance validation.

Focus: Test behavior and verify correctness, not implementation details.
"""

import pytest
import time
import uuid
from typing import Any
from unittest.mock import Mock

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import TagSaModel
from pydantic import ValidationError


class TestApiTagFourLayerConversion:
    """Test comprehensive four-layer conversion patterns for ApiTag."""

    def test_from_domain_conversion_preserves_all_data(self):
        """Test that domain to API conversion preserves all tag data accurately."""
        domain_tag = Tag(
            key="cuisine",
            value="italian", 
            author_id=str(uuid.uuid4()),
            type="restaurant"
        )
        
        api_tag = ApiTag.from_domain(domain_tag)
        
        assert api_tag.key == "cuisine"
        assert api_tag.value == "italian"
        assert api_tag.author_id == domain_tag.author_id
        assert api_tag.type == "restaurant"

    def test_to_domain_conversion_preserves_all_data(self):
        """Test that API to domain conversion preserves all tag data accurately."""
        api_tag = ApiTag(
            key="dietary",
            value="vegetarian",
            author_id=str(uuid.uuid4()), 
            type="preference"
        )
        
        domain_tag = api_tag.to_domain()
        
        assert domain_tag.key == "dietary"
        assert domain_tag.value == "vegetarian"
        assert domain_tag.author_id == api_tag.author_id
        assert domain_tag.type == "preference"

    def test_from_orm_model_conversion_preserves_all_data(self):
        """Test that ORM to API conversion preserves all tag data accurately."""
        orm_tag = TagSaModel(
            key="category",
            value="appetizer",
            author_id=str(uuid.uuid4()),
            type="recipe"
        )
        
        api_tag = ApiTag.from_orm_model(orm_tag)
        
        assert api_tag.key == "category"
        assert api_tag.value == "appetizer" 
        assert api_tag.author_id == orm_tag.author_id
        assert api_tag.type == "recipe"

    def test_to_orm_kwargs_conversion_preserves_all_data(self):
        """Test that API to ORM kwargs conversion preserves all tag data accurately."""
        api_tag = ApiTag(
            key="difficulty",
            value="beginner",
            author_id=str(uuid.uuid4()),
            type="recipe"
        )
        
        orm_kwargs = api_tag.to_orm_kwargs()
        
        assert orm_kwargs["key"] == "difficulty"
        assert orm_kwargs["value"] == "beginner"
        assert orm_kwargs["author_id"] == api_tag.author_id
        assert orm_kwargs["type"] == "recipe"

    def test_round_trip_domain_to_api_to_domain_integrity(self):
        """Test round-trip conversion domain → API → domain maintains data integrity."""
        original_domain = Tag(
            key="allergen",
            value="nuts",
            author_id=str(uuid.uuid4()),
            type="ingredient"
        )
        
        # Round trip: domain → API → domain
        api_tag = ApiTag.from_domain(original_domain)
        converted_domain = api_tag.to_domain()
        
        assert converted_domain.key == original_domain.key
        assert converted_domain.value == original_domain.value
        assert converted_domain.author_id == original_domain.author_id
        assert converted_domain.type == original_domain.type

    def test_round_trip_orm_to_api_to_orm_integrity(self):
        """Test round-trip conversion ORM → API → ORM maintains data integrity."""
        original_orm = TagSaModel(
            key="season",
            value="summer",
            author_id=str(uuid.uuid4()),
            type="timing"
        )
        
        # Round trip: ORM → API → ORM kwargs
        api_tag = ApiTag.from_orm_model(original_orm)
        orm_kwargs = api_tag.to_orm_kwargs()
        
        assert orm_kwargs["key"] == original_orm.key
        assert orm_kwargs["value"] == original_orm.value
        assert orm_kwargs["author_id"] == original_orm.author_id
        assert orm_kwargs["type"] == original_orm.type

    def test_four_layer_complete_cycle_integrity(self):
        """Test complete four-layer conversion cycle maintains data integrity."""
        # Start with domain object
        original_domain = Tag(
            key="region",
            value="mediterranean",
            author_id=str(uuid.uuid4()),
            type="cuisine"
        )
        
        # Complete cycle: domain → API → ORM kwargs → mock ORM → API → domain
        api_tag_1 = ApiTag.from_domain(original_domain)
        orm_kwargs = api_tag_1.to_orm_kwargs()
        
        # Simulate ORM model creation (mock for testing)
        mock_orm = Mock()
        mock_orm.key = orm_kwargs["key"]
        mock_orm.value = orm_kwargs["value"]
        mock_orm.author_id = orm_kwargs["author_id"]
        mock_orm.type = orm_kwargs["type"]
        
        api_tag_2 = ApiTag.from_orm_model(mock_orm)
        final_domain = api_tag_2.to_domain()
        
        # Verify complete integrity
        assert final_domain.key == original_domain.key
        assert final_domain.value == original_domain.value
        assert final_domain.author_id == original_domain.author_id
        assert final_domain.type == original_domain.type


class TestApiTagFieldValidation:
    """Test comprehensive field validation for ApiTag."""

    @pytest.mark.parametrize("valid_key", [
        "a",  # minimum length
        "category",  # typical value
        "very-long-descriptive-key-name-that-is-still-valid" + "x" * 40,  # near max length
        "key_with_underscores",
        "key-with-hyphens",
        "key123with456numbers"
    ])
    def test_key_field_accepts_valid_values(self, valid_key):
        """Test that key field accepts various valid formats and lengths."""
        api_tag = ApiTag(
            key=valid_key,
            value="test-value",
            author_id=str(uuid.uuid4()),
            type="test"
        )
        assert api_tag.key == valid_key

    @pytest.mark.parametrize("valid_value", [
        "a",  # minimum length
        "simple-value",
        "Value with spaces and punctuation!",
        "very-long-value-description-with-many-words-that-contains-detailed-information-about-the-tag" + "x" * 50,  # near max length
        "unicode-café-résumé-naïve",
        "123456789"
    ])
    def test_value_field_accepts_valid_values(self, valid_value):
        """Test that value field accepts various valid formats and lengths.""" 
        api_tag = ApiTag(
            key="test-key",
            value=valid_value,
            author_id=str(uuid.uuid4()),
            type="test"
        )
        assert api_tag.value == valid_value

    @pytest.mark.parametrize("valid_author_id", [
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        "a1b2c3d4-e5f6-7890-abcd-ef1234567890",  # UUID format
        str(uuid.uuid4())
    ])
    def test_author_id_field_accepts_valid_values(self, valid_author_id):
        """Test that author_id field accepts various valid UUID formats."""
        api_tag = ApiTag(
            key="test-key",
            value="test-value",
            author_id=valid_author_id,
            type="test"
        )
        assert api_tag.author_id == valid_author_id

    @pytest.mark.parametrize("valid_type", [
        "a",  # minimum length
        "recipe",
        "ingredient-category",
        "very-long-type-description-that-categorizes-tags",  # max length 50
        "type_with_underscores",
        "TypeWithCamelCase"
    ])
    def test_type_field_accepts_valid_values(self, valid_type):
        """Test that type field accepts various valid type categorizations."""
        api_tag = ApiTag(
            key="test-key",
            value="test-value", 
            author_id=str(uuid.uuid4()),
            type=valid_type
        )
        assert api_tag.type == valid_type

    def test_whitespace_trimming_on_text_fields(self):
        """Test that text fields properly trim whitespace while preserving internal spaces."""
        api_tag = ApiTag(
            key="  category  ",
            value="  italian cuisine  ",
            author_id=f"  {uuid.uuid4()}  ",
            type="  restaurant  "
        )
        
        assert api_tag.key == "category"
        assert api_tag.value == "italian cuisine"  # internal space preserved
        assert api_tag.author_id.strip() == api_tag.author_id  # UUID trimmed
        assert api_tag.type == "restaurant"


class TestApiTagErrorHandling:
    """Test comprehensive error handling scenarios for ApiTag."""

    @pytest.mark.parametrize("invalid_key_data", [
        "",  # empty string
        "   ",  # whitespace only
        "a" * 101,  # exceeds max length
        None,  # None value
    ])
    def test_key_field_validation_errors(self, invalid_key_data):
        """Test that invalid key values raise appropriate validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            ApiTag(
                key=invalid_key_data,
                value="valid-value",
                author_id=str(uuid.uuid4()),
                type="test"
            )
        
        error = exc_info.value
        assert len(error.errors()) > 0
        # Verify error is related to key field
        key_errors = [e for e in error.errors() if 'key' in str(e.get('loc', []))]
        assert len(key_errors) > 0

    @pytest.mark.parametrize("invalid_value_data", [
        "",  # empty string
        "   ",  # whitespace only  
        "a" * 201,  # exceeds max length
        None,  # None value
    ])
    def test_value_field_validation_errors(self, invalid_value_data):
        """Test that invalid value data raises appropriate validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            ApiTag(
                key="valid-key",
                value=invalid_value_data,
                author_id=str(uuid.uuid4()),
                type="test"
            )
        
        error = exc_info.value
        assert len(error.errors()) > 0
        # Verify error is related to value field
        value_errors = [e for e in error.errors() if 'value' in str(e.get('loc', []))]
        assert len(value_errors) > 0

    @pytest.mark.parametrize("invalid_author_id_data", [
        "",  # empty string
        "   ",  # whitespace only
        "user-12345",  # invalid UUID format
        "not-a-uuid",  # invalid UUID format
        None,  # None value
    ])
    def test_author_id_field_validation_errors(self, invalid_author_id_data):
        """Test that invalid author_id values raise appropriate validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            ApiTag(
                key="valid-key",
                value="valid-value",
                author_id=invalid_author_id_data,
                type="test"
            )
        
        error = exc_info.value
        assert len(error.errors()) > 0
        # Verify error is related to author_id field
        author_id_errors = [e for e in error.errors() if 'author_id' in str(e.get('loc', []))]
        assert len(author_id_errors) > 0

    @pytest.mark.parametrize("invalid_type_data", [
        "",  # empty string
        "   ",  # whitespace only
        "a" * 51,  # exceeds max length
        None,  # None value
    ])
    def test_type_field_validation_errors(self, invalid_type_data):
        """Test that invalid type values raise appropriate validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            ApiTag(
                key="valid-key",
                value="valid-value",
                author_id=str(uuid.uuid4()),
                type=invalid_type_data
            )
        
        error = exc_info.value
        assert len(error.errors()) > 0
        # Verify error is related to type field
        type_errors = [e for e in error.errors() if 'type' in str(e.get('loc', []))]
        assert len(type_errors) > 0

    def test_from_domain_with_none_domain_object_raises_error(self):
        """Test that from_domain with None raises appropriate error."""
        with pytest.raises(AttributeError):
            ApiTag.from_domain(None)  # type: ignore

    def test_from_orm_model_with_none_orm_object_raises_error(self):
        """Test that from_orm_model with None raises appropriate error."""
        with pytest.raises(ValidationError):
            ApiTag.from_orm_model(None)  # type: ignore

    def test_from_orm_model_with_invalid_orm_object_raises_error(self):
        """Test that from_orm_model with invalid ORM object raises appropriate error.""" 
        invalid_orm = Mock()
        # Set invalid fields to trigger validation error
        invalid_orm.key = ""  # Invalid empty key
        invalid_orm.value = "valid-value"
        invalid_orm.author_id = str(uuid.uuid4())
        invalid_orm.type = "test"
        
        with pytest.raises(ValidationError):
            ApiTag.from_orm_model(invalid_orm)

    def test_multiple_field_errors_reported_together(self):
        """Test that multiple field validation errors are reported together."""
        with pytest.raises(ValidationError) as exc_info:
            ApiTag(
                key="",  # invalid - empty
                value="",  # invalid - empty
                author_id="invalid-uuid",  # invalid - not a UUID
                type=""  # invalid - empty
            )
        
        error = exc_info.value
        assert len(error.errors()) >= 4  # At least one error per field

    def test_conversion_error_handling_preserves_error_context(self):
        """Test that conversion errors maintain helpful error context."""
        # Create invalid domain object (mock with invalid data)
        invalid_domain = Mock()
        invalid_domain.key = "a" * 101  # too long
        invalid_domain.value = "valid-value"
        invalid_domain.author_id = str(uuid.uuid4())
        invalid_domain.type = "test"
        
        with pytest.raises(ValidationError) as exc_info:
            ApiTag.from_domain(invalid_domain)
        
        error = exc_info.value
        assert len(error.errors()) > 0
        # Error should contain context about the field that failed
        assert any('key' in str(e.get('loc', [])) for e in error.errors())


class TestApiTagEdgeCases:
    """Test edge cases and boundary conditions for ApiTag."""

    def test_minimum_length_values_for_all_fields(self):
        """Test that minimum length values work correctly for all fields."""
        api_tag = ApiTag(
            key="a",  # minimum length 1
            value="b",  # minimum length 1
            author_id=str(uuid.uuid4()),  # valid UUID
            type="d"  # minimum length 1
        )
        
        assert api_tag.key == "a"
        assert api_tag.value == "b"
        assert api_tag.author_id == api_tag.author_id
        assert api_tag.type == "d"

    def test_maximum_length_values_for_all_fields(self):
        """Test that maximum length values work correctly for all fields."""
        max_key = "x" * 100  # max length 100
        max_value = "y" * 200  # max length 200  
        max_type = "z" * 50  # max length 50
        
        api_tag = ApiTag(
            key=max_key,
            value=max_value,
            author_id=str(uuid.uuid4()),
            type=max_type
        )
        
        assert api_tag.key == max_key
        assert api_tag.value == max_value
        assert api_tag.type == max_type

    def test_unicode_and_special_characters_handling(self):
        """Test that unicode and special characters are handled correctly."""
        api_tag = ApiTag(
            key="café-résumé",
            value="naïve-coöperation-façade",
            author_id=str(uuid.uuid4()),
            type="spëcial"
        )
        
        assert api_tag.key == "café-résumé"
        assert api_tag.value == "naïve-coöperation-façade"
        assert api_tag.type == "spëcial"

    def test_numeric_values_as_strings(self):
        """Test that numeric values provided as strings work correctly."""
        api_tag = ApiTag(
            key="123",
            value="456.789",
            author_id=str(uuid.uuid4()),
            type="000"
        )
        
        assert api_tag.key == "123"
        assert api_tag.value == "456.789"
        assert api_tag.type == "000"

    def test_mixed_case_and_special_formatting(self):
        """Test that mixed case and special formatting is preserved."""
        api_tag = ApiTag(
            key="CamelCaseKey",
            value="Mixed Case Value With Spaces",
            author_id=str(uuid.uuid4()),
            type="Type-With-Dashes"
        )
        
        assert api_tag.key == "CamelCaseKey"
        assert api_tag.value == "Mixed Case Value With Spaces"
        assert api_tag.type == "Type-With-Dashes"

    def test_boundary_condition_just_under_max_length(self):
        """Test boundary conditions just under maximum allowed lengths."""
        key_99 = "x" * 99  # just under max 100
        value_199 = "y" * 199  # just under max 200
        type_49 = "z" * 49  # just under max 50
        
        api_tag = ApiTag(
            key=key_99,
            value=value_199,
            author_id=str(uuid.uuid4()),
            type=type_49
        )
        
        assert len(api_tag.key) == 99
        assert len(api_tag.value) == 199
        assert len(api_tag.type) == 49


class TestApiTagPerformanceValidation:
    """Test performance characteristics of ApiTag operations."""

    def test_four_layer_conversion_performance(self):
        """Test that four-layer conversions complete within performance requirements (<5ms)."""
        # Create test data
        domain_tag = Tag(
            key="performance-test",
            value="testing-conversion-speed",
            author_id=str(uuid.uuid4()),
            type="benchmark"
        )
        
        start_time = time.perf_counter()
        
        # Perform multiple conversion cycles to test performance
        for _ in range(10):
            api_tag = ApiTag.from_domain(domain_tag)
            converted_domain = api_tag.to_domain()
            orm_kwargs = api_tag.to_orm_kwargs()
            
            # Simulate ORM conversion
            mock_orm = Mock()
            for key, value in orm_kwargs.items():
                setattr(mock_orm, key, value)
            
            api_tag_2 = ApiTag.from_orm_model(mock_orm)
        
        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Should complete 10 cycles in well under 50ms (5ms per cycle target)
        assert total_time < 50, f"Four-layer conversion took {total_time}ms, should be < 50ms"

    def test_field_validation_performance(self):
        """Test that field validation completes within performance requirements."""
        start_time = time.perf_counter()
        
        # Create multiple tags to test validation performance
        for i in range(100):
            api_tag = ApiTag(
                key=f"performance-key-{i}",
                value=f"performance-value-{i}",
                author_id=str(uuid.uuid4()),
                type=f"type-{i}"
            )
            # Access all fields to trigger validation
            _ = api_tag.key
            _ = api_tag.value
            _ = api_tag.author_id
            _ = api_tag.type
        
        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Should complete 100 validations in well under 300ms (3ms per validation target)
        assert total_time < 300, f"Field validation took {total_time}ms, should be < 300ms"

class TestApiTagIntegrationBehavior:
    """Test integration behavior and cross-schema compatibility."""

    def test_immutability_behavior(self):
        """Test that ApiTag instances are properly immutable."""
        api_tag = ApiTag(
            key="immutable-test",
            value="testing-immutability",
            author_id=str(uuid.uuid4()),
            type="behavior"
        )
        
        # Attempt to modify fields should raise errors
        with pytest.raises(ValidationError):
            api_tag.key = "modified-key"
        
        with pytest.raises(ValidationError):
            api_tag.value = "modified-value"

    def test_serialization_deserialization_consistency(self):
        """Test that serialization and deserialization maintain data consistency."""
        original_tag = ApiTag(
            key="serialize-test",
            value="testing-serialization-consistency",
            author_id=str(uuid.uuid4()),
            type="integration"
        )
        
        # Serialize to dict
        serialized = original_tag.model_dump()
        
        # Deserialize back to ApiTag
        deserialized_tag = ApiTag.model_validate(serialized)
        
        # Verify consistency
        assert deserialized_tag.key == original_tag.key
        assert deserialized_tag.value == original_tag.value
        assert deserialized_tag.author_id == original_tag.author_id
        assert deserialized_tag.type == original_tag.type

    def test_json_serialization_deserialization_consistency(self):
        """Test that JSON serialization and deserialization maintain data consistency."""
        original_tag = ApiTag(
            key="json-test",
            value="testing-json-consistency",
            author_id=str(uuid.uuid4()),
            type="integration"
        )
        
        # Serialize to JSON
        json_data = original_tag.model_dump_json()
        
        # Deserialize from JSON
        deserialized_tag = ApiTag.model_validate_json(json_data)
        
        # Verify consistency
        assert deserialized_tag.key == original_tag.key
        assert deserialized_tag.value == original_tag.value
        assert deserialized_tag.author_id == original_tag.author_id
        assert deserialized_tag.type == original_tag.type

    def test_hash_and_equality_behavior(self):
        """Test hash and equality behavior for consistent object handling."""
        author_id = str(uuid.uuid4())
        
        tag1 = ApiTag(
            key="equality-test",
            value="testing-equality",
            author_id=author_id,
            type="behavior"
        )
        
        tag2 = ApiTag(
            key="equality-test",
            value="testing-equality", 
            author_id=author_id,
            type="behavior"
        )
        
        tag3 = ApiTag(
            key="different-key",
            value="testing-equality",
            author_id=author_id,
            type="behavior"
        )
        
        # Test equality
        assert tag1 == tag2  # Same values should be equal
        assert tag1 != tag3  # Different values should not be equal
        
        # Test hash consistency (for use in sets/dicts)
        assert hash(tag1) == hash(tag2)  # Same values should have same hash
        
        # Test that tags can be used in frozensets (since they are immutable)
        tag_frozenset = frozenset([tag1, tag2, tag3])
        assert len(tag_frozenset) == 2  # tag1 and tag2 should be deduplicated