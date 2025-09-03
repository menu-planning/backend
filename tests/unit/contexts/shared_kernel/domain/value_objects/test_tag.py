"""Unit tests for Tag value object.

Tests tag validation, equality semantics, and value object contracts.
Follows testing principles: no I/O, fakes only, behavior-focused assertions.
"""
import pytest
import attrs

from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class TestTagValidation:
    """Test tag validation and format constraints."""

    def test_tag_validation_minimal_valid_tag(self):
        """Validates minimal valid tag creation."""
        # Given: minimal required tag components
        # When: create tag with valid components
        # Then: tag is created successfully
        tag = Tag(
            key="cuisine",
            value="italian",
            author_id="user123",
            type="category"
        )
        assert tag.key == "cuisine"
        assert tag.value == "italian"
        assert tag.author_id == "user123"
        assert tag.type == "category"

    def test_tag_validation_all_fields_populated(self):
        """Validates tag with all fields populated."""
        # Given: complete tag information
        # When: create tag with all components
        # Then: all fields are properly set
        tag = Tag(
            key="dietary_restriction",
            value="vegetarian",
            author_id="admin456",
            type="diet"
        )
        assert tag.key == "dietary_restriction"
        assert tag.value == "vegetarian"
        assert tag.author_id == "admin456"
        assert tag.type == "diet"

    def test_tag_validation_string_fields_accept_any_string(self):
        """Validates string fields accept any string value including empty."""
        # Given: various string values including empty strings
        # When: create tag with different string values
        # Then: all string values are accepted
        tag = Tag(
            key="",
            value="",
            author_id="",
            type=""
        )
        assert tag.key == ""
        assert tag.value == ""
        assert tag.author_id == ""
        assert tag.type == ""

    def test_tag_validation_special_characters_in_strings(self):
        """Validates string fields accept special characters and unicode."""
        # Given: strings with special characters and unicode
        # When: create tag with special character strings
        # Then: all special characters are accepted
        tag = Tag(
            key="categoria_especial",
            value="prato-do-dia",
            author_id="user@domain.com",
            type="tipo_especial"
        )
        assert tag.key == "categoria_especial"
        assert tag.value == "prato-do-dia"
        assert tag.author_id == "user@domain.com"
        assert tag.type == "tipo_especial"

    def test_tag_validation_unicode_characters(self):
        """Validates string fields accept unicode characters."""
        # Given: strings with unicode characters
        # When: create tag with unicode strings
        # Then: unicode characters are properly handled
        tag = Tag(
            key="categoria",
            value="prato-do-dia",
            author_id="usuário123",
            type="tipo"
        )
        assert tag.key == "categoria"
        assert tag.value == "prato-do-dia"
        assert tag.author_id == "usuário123"
        assert tag.type == "tipo"

    def test_tag_validation_whitespace_handling(self):
        """Validates string fields handle whitespace correctly."""
        # Given: strings with various whitespace
        # When: create tag with whitespace strings
        # Then: whitespace is preserved as-is
        tag = Tag(
            key="  spaced  ",
            value="\ttabbed\t",
            author_id="\nnewlined\n",
            type=" mixed "
        )
        assert tag.key == "  spaced  "
        assert tag.value == "\ttabbed\t"
        assert tag.author_id == "\nnewlined\n"
        assert tag.type == " mixed "

    def test_tag_validation_long_strings(self):
        """Validates string fields accept long strings."""
        # Given: very long string values
        # When: create tag with long strings
        # Then: long strings are accepted
        long_key = "a" * 1000
        long_value = "b" * 1000
        long_author_id = "c" * 1000
        long_type = "d" * 1000
        
        tag = Tag(
            key=long_key,
            value=long_value,
            author_id=long_author_id,
            type=long_type
        )
        assert tag.key == long_key
        assert tag.value == long_value
        assert tag.author_id == long_author_id
        assert tag.type == long_type

    def test_tag_validation_numeric_strings(self):
        """Validates string fields accept numeric strings."""
        # Given: numeric string values
        # When: create tag with numeric strings
        # Then: numeric strings are accepted
        tag = Tag(
            key="123",
            value="456",
            author_id="789",
            type="012"
        )
        assert tag.key == "123"
        assert tag.value == "456"
        assert tag.author_id == "789"
        assert tag.type == "012"


class TestTagEquality:
    """Test tag equality semantics and value object contracts."""

    def test_tag_equality_identical_tags(self):
        """Ensures identical tags are equal."""
        # Given: two tags with identical values
        # When: compare the tags
        # Then: they are equal
        tag1 = Tag(
            key="cuisine",
            value="italian",
            author_id="user123",
            type="category"
        )
        tag2 = Tag(
            key="cuisine",
            value="italian",
            author_id="user123",
            type="category"
        )
        assert tag1 == tag2
        assert hash(tag1) == hash(tag2)

    def test_tag_equality_different_tags(self):
        """Ensures different tags are not equal."""
        # Given: two tags with different values
        # When: compare the tags
        # Then: they are not equal
        tag1 = Tag(
            key="cuisine",
            value="italian",
            author_id="user123",
            type="category"
        )
        tag2 = Tag(
            key="cuisine",
            value="french",
            author_id="user123",
            type="category"
        )
        assert tag1 != tag2
        assert hash(tag1) != hash(tag2)

    def test_tag_equality_partial_differences(self):
        """Ensures tags with any different field are not equal."""
        # Given: tags differing in one field
        # When: compare the tags
        # Then: they are not equal
        base_tag = Tag(
            key="cuisine",
            value="italian",
            author_id="user123",
            type="category"
        )
        
        # Different key
        different_key = base_tag.replace(key="diet")
        assert base_tag != different_key
        
        # Different value
        different_value = base_tag.replace(value="french")
        assert base_tag != different_value
        
        # Different author_id
        different_author = base_tag.replace(author_id="user456")
        assert base_tag != different_author
        
        # Different type
        different_type = base_tag.replace(type="dietary")
        assert base_tag != different_type

    def test_tag_equality_case_sensitivity(self):
        """Ensures tag comparison is case-sensitive."""
        # Given: two tags differing only in case
        # When: compare the tags
        # Then: they are not equal (case-sensitive)
        tag1 = Tag(
            key="cuisine",
            value="italian",
            author_id="user123",
            type="category"
        )
        tag2 = Tag(
            key="Cuisine",
            value="Italian",
            author_id="User123",
            type="Category"
        )
        assert tag1 != tag2
        assert hash(tag1) != hash(tag2)

    def test_tag_equality_whitespace_differences(self):
        """Ensures tags with different whitespace are not equal."""
        # Given: two tags differing only in whitespace
        # When: compare the tags
        # Then: they are not equal
        tag1 = Tag(
            key="cuisine",
            value="italian",
            author_id="user123",
            type="category"
        )
        tag2 = Tag(
            key=" cuisine ",
            value=" italian ",
            author_id=" user123 ",
            type=" category "
        )
        assert tag1 != tag2
        assert hash(tag1) != hash(tag2)

    def test_tag_equality_immutability(self):
        """Ensures tag objects are immutable."""
        # Given: a tag instance
        # When: attempt to modify attributes
        # Then: modification raises FrozenInstanceError
        tag = Tag(
            key="cuisine",
            value="italian",
            author_id="user123",
            type="category"
        )
        
        # Verify immutability by attempting to modify attributes
        # The frozen decorator from attrs prevents attribute assignment
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            tag.key = "diet"  # type: ignore[attr-defined]
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            tag.value = "french"  # type: ignore[attr-defined]
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            tag.author_id = "user456"  # type: ignore[attr-defined]
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            tag.type = "dietary"  # type: ignore[attr-defined]

    def test_tag_equality_replace_creates_new_instance(self):
        """Ensures replace method creates new instance without modifying original."""
        # Given: an original tag
        # When: create new tag using replace
        # Then: original remains unchanged and new instance is created
        original = Tag(
            key="cuisine",
            value="italian",
            author_id="user123",
            type="category"
        )
        new_tag = original.replace(value="french")
        
        # Original unchanged
        assert original.key == "cuisine"
        assert original.value == "italian"
        assert original.author_id == "user123"
        assert original.type == "category"
        
        # New instance has updated values
        assert new_tag.key == "cuisine"  # Unchanged
        assert new_tag.value == "french"  # Changed
        assert new_tag.author_id == "user123"  # Unchanged
        assert new_tag.type == "category"  # Unchanged
        
        # They are different instances
        assert original is not new_tag
        assert original != new_tag

    def test_tag_equality_hash_consistency(self):
        """Ensures hash values are consistent across multiple calls."""
        # Given: a tag instance
        # When: call hash multiple times
        # Then: hash value is consistent
        tag = Tag(
            key="cuisine",
            value="italian",
            author_id="user123",
            type="category"
        )
        
        hash1 = hash(tag)
        hash2 = hash(tag)
        hash3 = hash(tag)
        
        assert hash1 == hash2 == hash3

    def test_tag_equality_hash_different_objects_same_values(self):
        """Ensures different objects with same values have same hash."""
        # Given: two different tag instances with identical values
        # When: compute their hashes
        # Then: hashes are equal
        tag1 = Tag(
            key="cuisine",
            value="italian",
            author_id="user123",
            type="category"
        )
        tag2 = Tag(
            key="cuisine",
            value="italian",
            author_id="user123",
            type="category"
        )
        
        assert tag1 is not tag2  # Different objects
        assert hash(tag1) == hash(tag2)  # Same hash

    def test_tag_equality_hash_different_values(self):
        """Ensures different tag values produce different hashes."""
        # Given: two tags with different values
        # When: compute their hashes
        # Then: hashes are different
        tag1 = Tag(
            key="cuisine",
            value="italian",
            author_id="user123",
            type="category"
        )
        tag2 = Tag(
            key="cuisine",
            value="french",
            author_id="user123",
            type="category"
        )
        
        assert hash(tag1) != hash(tag2)

    def test_tag_equality_replace_multiple_fields(self):
        """Ensures replace method can update multiple fields at once."""
        # Given: an original tag
        # When: create new tag using replace with multiple fields
        # Then: all specified fields are updated
        original = Tag(
            key="cuisine",
            value="italian",
            author_id="user123",
            type="category"
        )
        new_tag = original.replace(
            value="french",
            author_id="user456",
            type="dietary"
        )
        
        # Original unchanged
        assert original.key == "cuisine"
        assert original.value == "italian"
        assert original.author_id == "user123"
        assert original.type == "category"
        
        # New instance has updated values
        assert new_tag.key == "cuisine"  # Unchanged
        assert new_tag.value == "french"  # Changed
        assert new_tag.author_id == "user456"  # Changed
        assert new_tag.type == "dietary"  # Changed
        
        # They are different instances
        assert original is not new_tag
        assert original != new_tag
