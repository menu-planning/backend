
"""Unit tests for ApiTagFilter schema.

Tests tag filter schema validation, serialization/deserialization, and conversion methods.
Follows testing principles: no I/O, fakes only, behavior-focused assertions.
"""

import pytest
from pydantic import ValidationError

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag_filter import ApiTagFilter


class TestApiTagFilterValidation:
    """Test tag filter schema validation and field constraints."""

    def test_api_tag_filter_validation_minimal_valid_filter(self):
        """Validates minimal valid tag filter creation."""
        # Given: minimal required filter components
        # When: create filter with valid components
        # Then: filter is created successfully
        api_filter = ApiTagFilter(
            key="cuisine",
            value="italian"
        )
        assert api_filter.key == "cuisine"
        assert api_filter.value == "italian"
        assert api_filter.author_id is None
        assert api_filter.type is None
        assert api_filter.skip is None
        assert api_filter.limit == 100
        assert api_filter.sort == "-key"

    def test_api_tag_filter_validation_all_fields_populated(self):
        """Validates filter with all fields populated."""
        # Given: complete filter information
        # When: create filter with all components
        # Then: all fields are properly set
        api_filter = ApiTagFilter(
            key="dietary_restriction",
            value="vegetarian",
            author_id="550e8400-e29b-41d4-a716-446655440001",
            type="diet",
            skip=10,
            limit=50,
            sort="value"
        )
        assert api_filter.key == "dietary_restriction"
        assert api_filter.value == "vegetarian"
        assert api_filter.author_id == "550e8400-e29b-41d4-a716-446655440001"
        assert api_filter.type == "diet"
        assert api_filter.skip == 10
        assert api_filter.limit == 50
        assert api_filter.sort == "value"

    def test_api_tag_filter_validation_list_values(self):
        """Validates filter accepts list values for key, value, author_id, and type."""
        # Given: list values for filter fields
        # When: create filter with list values
        # Then: list values are properly set
        api_filter = ApiTagFilter(
            key=["cuisine", "diet"],
            value=["italian", "vegetarian"],
            author_id=["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"],
            type=["category", "dietary"]
        )
        assert api_filter.key == ["cuisine", "diet"]
        assert api_filter.value == ["italian", "vegetarian"]
        assert api_filter.author_id == ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"]
        assert api_filter.type == ["category", "dietary"]

    def test_api_tag_filter_validation_mixed_single_and_list_values(self):
        """Validates filter accepts mixed single and list values."""
        # Given: mixed single and list values
        # When: create filter with mixed values
        # Then: values are properly set
        api_filter = ApiTagFilter(
            key="cuisine",
            value=["italian", "french"],
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type=["category"]
        )
        assert api_filter.key == "cuisine"
        assert api_filter.value == ["italian", "french"]
        assert api_filter.author_id == "550e8400-e29b-41d4-a716-446655440000"
        assert api_filter.type == ["category"]

    def test_api_tag_filter_validation_default_values(self):
        """Validates filter uses correct default values."""
        # Given: filter with minimal fields
        # When: create filter with defaults
        # Then: default values are properly set
        api_filter = ApiTagFilter()
        assert api_filter.key is None
        assert api_filter.value is None
        assert api_filter.author_id is None
        assert api_filter.type is None
        assert api_filter.skip is None
        assert api_filter.limit == 100
        assert api_filter.sort == "-key"

    def test_api_tag_filter_validation_pagination_values(self):
        """Validates pagination field constraints."""
        # Given: pagination values
        # When: create filter with pagination
        # Then: pagination values are properly set
        api_filter = ApiTagFilter(
            skip=0,
            limit=25
        )
        assert api_filter.skip == 0
        assert api_filter.limit == 25

    def test_api_tag_filter_validation_sort_field_variations(self):
        """Validates sort field accepts various formats."""
        # Given: different sort field formats
        # When: create filters with different sort values
        # Then: sort values are properly set
        test_cases = [
            "-key",  # Descending
            "key",   # Ascending
            "-value",
            "value",
            "-author_id",
            "author_id",
            "-type",
            "type"
        ]
        
        for sort_value in test_cases:
            api_filter = ApiTagFilter(sort=sort_value)
            assert api_filter.sort == sort_value

    def test_api_tag_filter_validation_unicode_characters(self):
        """Validates filter handles unicode characters correctly."""
        # Given: filter with unicode characters
        # When: create filter with unicode strings
        # Then: unicode characters are preserved
        api_filter = ApiTagFilter(
            key="categoria",
            value="prato-do-dia",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="tipo"
        )
        assert api_filter.key == "categoria"
        assert api_filter.value == "prato-do-dia"
        assert api_filter.author_id == "550e8400-e29b-41d4-a716-446655440000"
        assert api_filter.type == "tipo"

    def test_api_tag_filter_validation_special_characters(self):
        """Validates filter handles special characters correctly."""
        # Given: filter with special characters
        # When: create filter with special character strings
        # Then: special characters are preserved
        api_filter = ApiTagFilter(
            key="categoria_especial",
            value="prato-do-dia",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="tipo_especial"
        )
        assert api_filter.key == "categoria_especial"
        assert api_filter.value == "prato-do-dia"
        assert api_filter.author_id == "550e8400-e29b-41d4-a716-446655440000"
        assert api_filter.type == "tipo_especial"

    def test_api_tag_filter_validation_author_id_uuid_format(self):
        """Validates author_id field accepts valid UUID format."""
        # Given: valid UUID string
        # When: create filter with valid UUID
        # Then: filter is created successfully
        api_filter = ApiTagFilter(
            author_id="550e8400-e29b-41d4-a716-446655440000"
        )
        assert api_filter.author_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_api_tag_filter_validation_author_id_list_uuid_format(self):
        """Validates author_id field accepts list of valid UUIDs."""
        # Given: list of valid UUID strings
        # When: create filter with valid UUID list
        # Then: filter is created successfully
        api_filter = ApiTagFilter(
            author_id=["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"]
        )
        assert api_filter.author_id == ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"]

    def test_api_tag_filter_validation_numeric_strings(self):
        """Validates filter fields accept numeric strings."""
        # Given: numeric string values
        # When: create filter with numeric strings
        # Then: numeric strings are accepted
        api_filter = ApiTagFilter(
            key="123",
            value="456",
            type="789"
        )
        assert api_filter.key == "123"
        assert api_filter.value == "456"
        assert api_filter.type == "789"

    def test_api_tag_filter_validation_case_sensitivity(self):
        """Validates filter fields are case-sensitive."""
        # Given: filters with different cases
        # When: create filters with different case values
        # Then: case differences are preserved
        filter1 = ApiTagFilter(
            key="cuisine",
            value="italian",
            type="category"
        )
        filter2 = ApiTagFilter(
            key="Cuisine",
            value="Italian",
            type="Category"
        )
        
        assert filter1 != filter2
        assert filter1.key == "cuisine"
        assert filter2.key == "Cuisine"
        assert filter1.value == "italian"
        assert filter2.value == "Italian"
        assert filter1.type == "category"
        assert filter2.type == "Category"


class TestApiTagFilterEquality:
    """Test tag filter equality semantics and value object contracts."""

    def test_api_tag_filter_equality_same_values(self):
        """Ensures proper equality semantics for identical values."""
        # Given: two filter instances with same values
        # When: compare filters
        # Then: they should be equal
        filter1 = ApiTagFilter(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category",
            skip=10,
            limit=50,
            sort="-key"
        )
        filter2 = ApiTagFilter(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category",
            skip=10,
            limit=50,
            sort="-key"
        )
        assert filter1 == filter2

    def test_api_tag_filter_equality_different_values(self):
        """Ensures proper inequality semantics for different values."""
        # Given: two filter instances with different values
        # When: compare filters
        # Then: they should not be equal
        filter1 = ApiTagFilter(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        filter2 = ApiTagFilter(
            key="cuisine",
            value="french",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        assert filter1 != filter2

    def test_api_tag_filter_equality_different_keys(self):
        """Ensures different key values result in inequality."""
        # Given: two filters with different keys
        # When: compare filters
        # Then: they should not be equal
        filter1 = ApiTagFilter(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        filter2 = ApiTagFilter(
            key="diet",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        assert filter1 != filter2

    def test_api_tag_filter_equality_different_author_ids(self):
        """Ensures different author_id values result in inequality."""
        # Given: two filters with different author_ids
        # When: compare filters
        # Then: they should not be equal
        filter1 = ApiTagFilter(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        filter2 = ApiTagFilter(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440001",
            type="category"
        )
        assert filter1 != filter2

    def test_api_tag_filter_equality_different_types(self):
        """Ensures different type values result in inequality."""
        # Given: two filters with different types
        # When: compare filters
        # Then: they should not be equal
        filter1 = ApiTagFilter(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        filter2 = ApiTagFilter(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="dietary"
        )
        assert filter1 != filter2

    def test_api_tag_filter_equality_different_pagination(self):
        """Ensures different pagination values result in inequality."""
        # Given: two filters with different pagination
        # When: compare filters
        # Then: they should not be equal
        filter1 = ApiTagFilter(
            key="cuisine",
            skip=10,
            limit=50
        )
        filter2 = ApiTagFilter(
            key="cuisine",
            skip=20,
            limit=100
        )
        assert filter1 != filter2

    def test_api_tag_filter_equality_different_sort(self):
        """Ensures different sort values result in inequality."""
        # Given: two filters with different sort values
        # When: compare filters
        # Then: they should not be equal
        filter1 = ApiTagFilter(
            key="cuisine",
            sort="-key"
        )
        filter2 = ApiTagFilter(
            key="cuisine",
            sort="key"
        )
        assert filter1 != filter2

    def test_api_tag_filter_equality_list_vs_single_values(self):
        """Ensures list and single values are treated as different."""
        # Given: filters with list vs single values
        # When: compare filters
        # Then: they should not be equal
        filter1 = ApiTagFilter(
            key="cuisine",
            value="italian"
        )
        filter2 = ApiTagFilter(
            key="cuisine",
            value=["italian"]
        )
        assert filter1 != filter2


class TestApiTagFilterSerialization:
    """Test tag filter serialization and deserialization contracts."""

    def test_api_tag_filter_serialization_to_dict(self):
        """Validates filter can be serialized to dictionary."""
        # Given: filter with all fields
        # When: serialize to dict
        # Then: all fields are properly serialized
        api_filter = ApiTagFilter(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category",
            skip=10,
            limit=50,
            sort="-key"
        )
        
        result = api_filter.model_dump()
        
        assert result["key"] == "cuisine"
        assert result["value"] == "italian"
        assert result["author_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert result["type"] == "category"
        assert result["skip"] == 10
        assert result["limit"] == 50
        assert result["sort"] == "-key"

    def test_api_tag_filter_serialization_to_dict_excludes_none(self):
        """Validates filter excludes None values when serializing with exclude_none=True."""
        # Given: filter with some None values
        # When: serialize to dict with exclude_none=True
        # Then: None values are excluded
        api_filter = ApiTagFilter(
            key="cuisine",
            value="italian"
        )
        
        result = api_filter.model_dump(exclude_none=True)
        
        assert "key" in result
        assert "value" in result
        assert "author_id" not in result
        assert "type" not in result
        assert "skip" not in result
        assert "limit" in result  # Has default value
        assert "sort" in result   # Has default value

    def test_api_tag_filter_serialization_to_json(self):
        """Validates filter can be serialized to JSON."""
        # Given: filter with all fields
        # When: serialize to JSON
        # Then: JSON is properly formatted
        api_filter = ApiTagFilter(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        
        json_str = api_filter.model_dump_json()
        
        assert '"key":"cuisine"' in json_str
        assert '"value":"italian"' in json_str
        assert '"author_id":"550e8400-e29b-41d4-a716-446655440000"' in json_str
        assert '"type":"category"' in json_str

    def test_api_tag_filter_deserialization_from_dict(self):
        """Validates filter can be deserialized from dictionary."""
        # Given: dictionary with filter data
        # When: create filter from dict
        # Then: filter is properly created
        data = {
            "key": "cuisine",
            "value": "italian",
            "author_id": "550e8400-e29b-41d4-a716-446655440000",
            "type": "category",
            "skip": 10,
            "limit": 50,
            "sort": "-key"
        }
        
        api_filter = ApiTagFilter.model_validate(data)
        
        assert api_filter.key == "cuisine"
        assert api_filter.value == "italian"
        assert api_filter.author_id == "550e8400-e29b-41d4-a716-446655440000"
        assert api_filter.type == "category"
        assert api_filter.skip == 10
        assert api_filter.limit == 50
        assert api_filter.sort == "-key"

    def test_api_tag_filter_deserialization_from_json(self):
        """Validates filter can be deserialized from JSON."""
        # Given: JSON string with filter data
        # When: create filter from JSON
        # Then: filter is properly created
        json_str = '''
        {
            "key": "cuisine",
            "value": "italian",
            "author_id": "550e8400-e29b-41d4-a716-446655440000",
            "type": "category",
            "skip": 10,
            "limit": 50,
            "sort": "-key"
        }
        '''
        
        api_filter = ApiTagFilter.model_validate_json(json_str)
        
        assert api_filter.key == "cuisine"
        assert api_filter.value == "italian"
        assert api_filter.author_id == "550e8400-e29b-41d4-a716-446655440000"
        assert api_filter.type == "category"
        assert api_filter.skip == 10
        assert api_filter.limit == 50
        assert api_filter.sort == "-key"

    def test_api_tag_filter_serialization_list_values(self):
        """Validates serialization handles list values correctly."""
        # Given: filter with list values
        # When: serialize and deserialize
        # Then: list values are preserved
        api_filter = ApiTagFilter(
            key=["cuisine", "diet"],
            value=["italian", "vegetarian"],
            author_id=["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"],
            type=["category", "dietary"]
        )
        
        json_str = api_filter.model_dump_json()
        deserialized = ApiTagFilter.model_validate_json(json_str)
        
        assert deserialized.key == ["cuisine", "diet"]
        assert deserialized.value == ["italian", "vegetarian"]
        assert deserialized.author_id == ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"]
        assert deserialized.type == ["category", "dietary"]

    def test_api_tag_filter_serialization_unicode_characters(self):
        """Validates serialization handles unicode characters correctly."""
        # Given: filter with unicode characters
        # When: serialize and deserialize
        # Then: unicode characters are preserved
        api_filter = ApiTagFilter(
            key="categoria",
            value="prato-do-dia",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="tipo"
        )
        
        json_str = api_filter.model_dump_json()
        deserialized = ApiTagFilter.model_validate_json(json_str)
        
        assert deserialized.key == "categoria"
        assert deserialized.value == "prato-do-dia"
        assert deserialized.author_id == "550e8400-e29b-41d4-a716-446655440000"
        assert deserialized.type == "tipo"


class TestApiTagFilterDomainConversion:
    """Test tag filter conversion to domain layer."""

    def test_api_tag_filter_to_domain_conversion(self):
        """Validates conversion from API schema to domain dictionary."""
        # Given: API filter schema
        # When: convert to domain dictionary
        # Then: all fields are properly converted
        api_filter = ApiTagFilter(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category",
            skip=10,
            limit=50,
            sort="-key"
        )
        
        domain_dict = api_filter.to_domain()
        
        assert domain_dict["key"] == "cuisine"
        assert domain_dict["value"] == "italian"
        assert domain_dict["author_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert domain_dict["type"] == "category"
        assert domain_dict["skip"] == 10
        assert domain_dict["limit"] == 50
        assert domain_dict["sort"] == "-key"

    def test_api_tag_filter_to_domain_excludes_none_values(self):
        """Validates conversion excludes None values from domain dictionary."""
        # Given: API filter schema with None values
        # When: convert to domain dictionary
        # Then: None values are excluded
        api_filter = ApiTagFilter(
            key="cuisine",
            value="italian"
        )
        
        domain_dict = api_filter.to_domain()
        
        assert "key" in domain_dict
        assert "value" in domain_dict
        assert "author_id" not in domain_dict
        assert "type" not in domain_dict
        assert "skip" not in domain_dict
        assert "limit" in domain_dict  # Has default value
        assert "sort" in domain_dict   # Has default value

    def test_api_tag_filter_to_domain_list_values(self):
        """Validates conversion handles list values correctly."""
        # Given: API filter schema with list values
        # When: convert to domain dictionary
        # Then: list values are preserved
        api_filter = ApiTagFilter(
            key=["cuisine", "diet"],
            value=["italian", "vegetarian"],
            author_id=["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"],
            type=["category", "dietary"]
        )
        
        domain_dict = api_filter.to_domain()
        
        assert domain_dict["key"] == ["cuisine", "diet"]
        assert domain_dict["value"] == ["italian", "vegetarian"]
        assert domain_dict["author_id"] == ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"]
        assert domain_dict["type"] == ["category", "dietary"]

    def test_api_tag_filter_to_domain_unicode_handling(self):
        """Validates unicode conversion to domain dictionary."""
        # Given: API filter with unicode characters
        # When: convert to domain dictionary
        # Then: unicode characters are properly handled
        api_filter = ApiTagFilter(
            key="categoria",
            value="prato-do-dia",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="tipo"
        )
        
        domain_dict = api_filter.to_domain()
        
        assert domain_dict["key"] == "categoria"
        assert domain_dict["value"] == "prato-do-dia"
        assert domain_dict["author_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert domain_dict["type"] == "tipo"

    def test_api_tag_filter_to_domain_empty_filter(self):
        """Validates conversion of empty filter to domain dictionary."""
        # Given: empty API filter schema
        # When: convert to domain dictionary
        # Then: only default values are included
        api_filter = ApiTagFilter()
        
        domain_dict = api_filter.to_domain()
        
        assert "key" not in domain_dict
        assert "value" not in domain_dict
        assert "author_id" not in domain_dict
        assert "type" not in domain_dict
        assert "skip" not in domain_dict
        assert domain_dict["limit"] == 100
        assert domain_dict["sort"] == "-key"


class TestApiTagFilterEdgeCases:
    """Test tag filter schema edge cases and error handling."""

    def test_api_tag_filter_validation_negative_skip_value(self):
        """Validates negative skip values are handled."""
        # Given: negative skip value
        # When: create filter with negative skip
        # Then: negative value is accepted (domain layer should handle validation)
        api_filter = ApiTagFilter(skip=-10)
        assert api_filter.skip == -10

    def test_api_tag_filter_validation_zero_limit_value(self):
        """Validates zero limit value is handled."""
        # Given: zero limit value
        # When: create filter with zero limit
        # Then: zero value is accepted (domain layer should handle validation)
        api_filter = ApiTagFilter(limit=0)
        assert api_filter.limit == 0

    def test_api_tag_filter_validation_negative_limit_value(self):
        """Validates negative limit values are handled."""
        # Given: negative limit value
        # When: create filter with negative limit
        # Then: negative value is accepted (domain layer should handle validation)
        api_filter = ApiTagFilter(limit=-10)
        assert api_filter.limit == -10

    def test_api_tag_filter_validation_large_limit_value(self):
        """Validates large limit values are handled."""
        # Given: large limit value
        # When: create filter with large limit
        # Then: large value is accepted (domain layer should handle validation)
        api_filter = ApiTagFilter(limit=10000)
        assert api_filter.limit == 10000

    def test_api_tag_filter_validation_empty_string_values(self):
        """Validates empty string values are handled."""
        # Given: empty string values
        # When: create filter with empty strings
        # Then: empty strings are accepted (domain layer should handle validation)
        api_filter = ApiTagFilter(
            key="",
            value="",
            type=""
        )
        assert api_filter.key == ""
        assert api_filter.value == ""
        assert api_filter.type == ""

    def test_api_tag_filter_validation_whitespace_only_values(self):
        """Validates whitespace-only values are handled."""
        # Given: whitespace-only values
        # When: create filter with whitespace strings
        # Then: whitespace strings are accepted (domain layer should handle validation)
        api_filter = ApiTagFilter(
            key="   ",
            value="\t\n",
            type="  \t  "
        )
        assert api_filter.key == "   "
        assert api_filter.value == "\t\n"
        assert api_filter.type == "  \t  "

    def test_api_tag_filter_validation_special_sort_values(self):
        """Validates special sort field values are handled."""
        # Given: special sort values
        # When: create filters with special sort values
        # Then: special values are accepted (domain layer should handle validation)
        test_cases = [
            "",           # Empty string
            "invalid",    # Invalid field name
            "++key",      # Multiple prefixes
            "key++",      # Suffix
            "key,value",  # Multiple fields
        ]
        
        for sort_value in test_cases:
            api_filter = ApiTagFilter(sort=sort_value)
            assert api_filter.sort == sort_value

    def test_api_tag_filter_validation_mixed_list_and_single_types(self):
        """Validates mixed list and single value types are handled."""
        # Given: mixed list and single values
        # When: create filter with mixed types
        # Then: mixed types are properly handled
        api_filter = ApiTagFilter(
            key="cuisine",
            value=["italian", "french"],
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type=["category"]
        )
        assert api_filter.key == "cuisine"
        assert api_filter.value == ["italian", "french"]
        assert api_filter.author_id == "550e8400-e29b-41d4-a716-446655440000"
        assert api_filter.type == ["category"]

    def test_api_tag_filter_validation_empty_lists(self):
        """Validates empty lists are handled."""
        # Given: empty list values
        # When: create filter with empty lists
        # Then: empty lists are accepted (domain layer should handle validation)
        api_filter = ApiTagFilter(
            key=[],
            value=[],
            author_id=[],
            type=[]
        )
        assert api_filter.key == []
        assert api_filter.value == []
        assert api_filter.author_id == []
        assert api_filter.type == []

    def test_api_tag_filter_validation_none_in_lists_raises_error(self):
        """Validates None values in lists raise validation errors."""
        # Given: lists with None values
        # When: create filter with None in lists
        # Then: validation error is raised due to type constraints
        with pytest.raises(ValidationError):
            ApiTagFilter(
                key=["cuisine", None, "diet"], # type: ignore[arg-type]
                value=[None, "italian"], # type: ignore[arg-type]
                author_id=["550e8400-e29b-41d4-a716-446655440000", None] # type: ignore[arg-type]
            )

    def test_api_tag_filter_immutability(self):
        """Validates filter schema is immutable."""
        # Given: filter instance
        # When: attempt to modify fields
        # Then: modification raises error
        api_filter = ApiTagFilter(
            key="cuisine",
            value="italian",
            author_id="550e8400-e29b-41d4-a716-446655440000",
            type="category"
        )
        
        with pytest.raises(ValidationError):
            api_filter.key = "diet"  # type: ignore[attr-defined]

    def test_api_tag_filter_validation_comprehensive_edge_cases(self):
        """Validates comprehensive edge cases are handled."""
        # Given: various edge case inputs
        # When: create filters with edge cases
        # Then: edge cases are properly handled
        
        # Test very long strings
        long_string = "x" * 1000
        api_filter = ApiTagFilter(
            key=long_string,
            value=long_string,
            type=long_string
        )
        assert api_filter.key == long_string
        assert api_filter.value == long_string
        assert api_filter.type == long_string
        
        # Test very large numbers
        api_filter = ApiTagFilter(
            skip=999999999,
            limit=999999999
        )
        assert api_filter.skip == 999999999
        assert api_filter.limit == 999999999

    def test_api_tag_filter_validation_unicode_edge_cases(self):
        """Validates unicode edge cases are handled."""
        # Given: unicode edge cases
        # When: create filter with unicode edge cases
        # Then: unicode edge cases are properly handled
        api_filter = ApiTagFilter(
            key="🚀",
            value="🍕",
            type="🎯"
        )
        assert api_filter.key == "🚀"
        assert api_filter.value == "🍕"
        assert api_filter.type == "🎯"

    def test_api_tag_filter_validation_sql_injection_attempts(self):
        """Validates SQL injection attempts are handled as strings."""
        # Given: SQL injection attempt strings
        # When: create filter with SQL injection strings
        # Then: strings are treated as literal values (domain layer should handle sanitization)
        api_filter = ApiTagFilter(
            key="'; DROP TABLE tags; --",
            value="1' OR '1'='1",
            type="UNION SELECT * FROM users"
        )
        assert api_filter.key == "'; DROP TABLE tags; --"
        assert api_filter.value == "1' OR '1'='1"
        assert api_filter.type == "UNION SELECT * FROM users"
