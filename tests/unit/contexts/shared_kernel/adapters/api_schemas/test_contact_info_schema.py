"""Unit tests for ApiContactInfo schema.

Tests contact info schema validation, serialization/deserialization, and conversion methods.
Follows testing principles: no I/O, fakes only, behavior-focused assertions.
"""

import pytest
from pydantic import ValidationError

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_contact_info import ApiContactInfo
from src.contexts.shared_kernel.adapters.ORM.sa_models.contact_info_sa_model import ContactInfoSaModel
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo


class TestApiContactInfoValidation:
    """Test contact info schema validation and field constraints."""

    def test_api_contact_info_validation_minimal_valid_contact(self):
        """Validates minimal valid contact info creation."""
        # Given: minimal contact info components
        # When: create contact info with valid components
        # Then: contact info is created successfully
        api_contact = ApiContactInfo(
            main_phone="+5511999999999",
            main_email="test@example.com"
        )
        assert api_contact.main_phone == "+5511999999999"
        assert api_contact.main_email == "test@example.com"
        assert api_contact.all_phones == frozenset()
        assert api_contact.all_emails == frozenset()

    def test_api_contact_info_validation_all_fields_populated(self):
        """Validates contact info with all fields populated."""
        # Given: complete contact information
        # When: create contact info with all components
        # Then: all fields are properly set
        api_contact = ApiContactInfo(
            main_phone="+5511999999999",
            main_email="primary@example.com",
            all_phones=frozenset(["+5511999999999", "+5511888888888"]),
            all_emails=frozenset(["primary@example.com", "secondary@example.com"])
        )
        assert api_contact.main_phone == "+5511999999999"
        assert api_contact.main_email == "primary@example.com"
        assert api_contact.all_phones == frozenset(["+5511999999999", "+5511888888888"])
        assert api_contact.all_emails == frozenset(["primary@example.com", "secondary@example.com"])

    def test_api_contact_info_validation_all_fields_none(self):
        """Validates contact info with all fields as None."""
        # Given: all fields as None
        # When: create contact info with None values
        # Then: contact info is created successfully with None values
        api_contact = ApiContactInfo()
        assert api_contact.main_phone is None
        assert api_contact.main_email is None
        assert api_contact.all_phones == frozenset()
        assert api_contact.all_emails == frozenset()

    def test_api_contact_info_validation_phone_format_validation(self):
        """Validates phone number format validation."""
        # Given: valid phone numbers
        # When: create contact info with valid phones
        # Then: phones are accepted
        valid_phones = [
            "+5511999999999",
            "11 99999-9999",
            "+1-555-123-4567"
        ]
        
        for phone in valid_phones:
            api_contact = ApiContactInfo(main_phone=phone)
            assert api_contact.main_phone == phone

    def test_api_contact_info_validation_email_format_validation(self):
        """Validates email address format validation."""
        # Given: valid email addresses
        # When: create contact info with valid emails
        # Then: emails are accepted and normalized to lowercase
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test+tag@example.org"
        ]
        
        for email in valid_emails:
            api_contact = ApiContactInfo(main_email=email)
            assert api_contact.main_email == email.lower()

    def test_api_contact_info_validation_invalid_phone_format(self):
        """Validates invalid phone number format raises validation error."""
        # Given: invalid phone numbers
        # When: create contact info with invalid phones
        # Then: validation errors are raised
        invalid_phones = [
            "123",  # Too short
            "12345678901234567890",  # Too long
            "abc-def-ghij",  # Non-numeric
            "(11) 99999-9999",  # Invalid format
            "555.123.4567",  # Invalid format
        ]
        
        for phone in invalid_phones:
            with pytest.raises(ValidationError):
                ApiContactInfo(main_phone=phone)

    def test_api_contact_info_validation_invalid_email_format(self):
        """Validates invalid email address format raises validation error."""
        # Given: invalid email addresses
        # When: create contact info with invalid emails
        # Then: validation errors are raised
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test@example",
            "a" * 65 + "@example.com",  # Local part too long
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                ApiContactInfo(main_email=email)

    def test_api_contact_info_validation_all_phones_collection_validation(self):
        """Validates all_phones collection validation raises error for invalid phones."""
        # Given: collection with valid and invalid phones
        # When: create contact info with mixed phone collection
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiContactInfo(
                all_phones=frozenset([
                    "+5511999999999",  # Valid
                    "invalid-phone",   # Invalid - causes validation error
                    "+5511888888888",  # Valid
                    "123",             # Invalid - causes validation error
                ])
            )

    def test_api_contact_info_validation_all_emails_collection_validation(self):
        """Validates all_emails collection validation raises error for invalid emails."""
        # Given: collection with valid and invalid emails
        # When: create contact info with mixed email collection
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiContactInfo(
                all_emails=frozenset([
                    "valid@example.com",    # Valid
                    "invalid-email",        # Invalid - causes validation error
                    "ANOTHER@EXAMPLE.COM",  # Valid
                    "@invalid.com",         # Invalid - causes validation error
                ])
            )

    def test_api_contact_info_validation_empty_collections(self):
        """Validates empty collections are handled correctly."""
        # Given: empty collections
        # When: create contact info with empty collections
        # Then: empty frozensets are created
        api_contact = ApiContactInfo(
            all_phones=frozenset(),
            all_emails=frozenset()
        )
        assert api_contact.all_phones == frozenset()
        assert api_contact.all_emails == frozenset()

    def test_api_contact_info_validation_valid_collections(self):
        """Validates valid collections are handled correctly."""
        # Given: collections with valid phones and emails
        # When: create contact info with valid collections
        # Then: collections are properly created
        api_contact = ApiContactInfo(
            all_phones=frozenset(["+5511999999999", "+5511888888888"]),
            all_emails=frozenset(["test@example.com", "other@example.com"])
        )
        assert api_contact.all_phones == frozenset(["+5511999999999", "+5511888888888"])
        assert api_contact.all_emails == frozenset(["test@example.com", "other@example.com"])

    def test_api_contact_info_validation_none_collections(self):
        """Validates None collections raise validation error."""
        # Given: None collections
        # When: create contact info with None collections
        # Then: validation error is raised (frozenset field doesn't accept None)
        with pytest.raises(ValidationError):
            ApiContactInfo(
                all_phones=None,  # type: ignore[arg-type]
                all_emails=None   # type: ignore[arg-type]
            )


class TestApiContactInfoEquality:
    """Test contact info equality semantics and value object contracts."""

    def test_api_contact_info_equality_same_values(self):
        """Ensures proper equality semantics for identical values."""
        # Given: two contact info instances with same values
        # When: compare contact infos
        # Then: they should be equal
        contact1 = ApiContactInfo(
            main_phone="+5511999999999",
            main_email="test@example.com",
            all_phones=frozenset(["+5511999999999"]),
            all_emails=frozenset(["test@example.com"])
        )
        contact2 = ApiContactInfo(
            main_phone="+5511999999999",
            main_email="test@example.com",
            all_phones=frozenset(["+5511999999999"]),
            all_emails=frozenset(["test@example.com"])
        )
        assert contact1 == contact2

    def test_api_contact_info_equality_different_values(self):
        """Ensures proper inequality semantics for different values."""
        # Given: two contact info instances with different values
        # When: compare contact infos
        # Then: they should not be equal
        contact1 = ApiContactInfo(
            main_phone="+5511999999999",
            main_email="test@example.com"
        )
        contact2 = ApiContactInfo(
            main_phone="+5511888888888",
            main_email="test@example.com"
        )
        assert contact1 != contact2

    def test_api_contact_info_equality_different_collections(self):
        """Ensures different collections result in inequality."""
        # Given: two contact infos with different collections
        # When: compare contact infos
        # Then: they should not be equal
        contact1 = ApiContactInfo(
            all_phones=frozenset(["+5511999999999"]),
            all_emails=frozenset(["test@example.com"])
        )
        contact2 = ApiContactInfo(
            all_phones=frozenset(["+5511888888888"]),
            all_emails=frozenset(["test@example.com"])
        )
        assert contact1 != contact2

    def test_api_contact_info_equality_none_vs_empty(self):
        """Ensures None and empty values are treated consistently."""
        # Given: contact info with None and contact info with empty collections
        # When: compare contact infos
        # Then: they should be equal (both become empty frozensets)
        contact1 = ApiContactInfo(
            main_phone=None,
            main_email=None,
            all_phones=frozenset(),
            all_emails=frozenset()
        )
        contact2 = ApiContactInfo()
        assert contact1 == contact2


class TestApiContactInfoSerialization:
    """Test contact info serialization and deserialization contracts."""

    def test_api_contact_info_serialization_to_dict(self):
        """Validates contact info can be serialized to dictionary."""
        # Given: contact info with all fields
        # When: serialize to dict
        # Then: all fields are properly serialized
        api_contact = ApiContactInfo(
            main_phone="+5511999999999",
            main_email="test@example.com",
            all_phones=frozenset(["+5511999999999", "+5511888888888"]),
            all_emails=frozenset(["test@example.com", "other@example.com"])
        )
        
        result = api_contact.model_dump()
        
        assert result["main_phone"] == "+5511999999999"
        assert result["main_email"] == "test@example.com"
        assert result["all_phones"] == frozenset(["+5511999999999", "+5511888888888"])
        assert result["all_emails"] == frozenset(["test@example.com", "other@example.com"])

    def test_api_contact_info_serialization_to_json(self):
        """Validates contact info can be serialized to JSON."""
        # Given: contact info with all fields
        # When: serialize to JSON
        # Then: JSON is properly formatted
        api_contact = ApiContactInfo(
            main_phone="+5511999999999",
            main_email="test@example.com",
            all_phones=frozenset(["+5511999999999"]),
            all_emails=frozenset(["test@example.com"])
        )
        
        json_str = api_contact.model_dump_json()
        
        assert '"main_phone":"+5511999999999"' in json_str
        assert '"main_email":"test@example.com"' in json_str
        assert '"all_phones":["+5511999999999"]' in json_str
        assert '"all_emails":["test@example.com"]' in json_str

    def test_api_contact_info_deserialization_from_dict(self):
        """Validates contact info can be deserialized from dictionary."""
        # Given: dictionary with contact info data
        # When: create contact info from dict
        # Then: contact info is properly created
        data = {
            "main_phone": "+5511999999999",
            "main_email": "test@example.com",
            "all_phones": frozenset(["+5511999999999", "+5511888888888"]),
            "all_emails": frozenset(["test@example.com", "other@example.com"])
        }
        
        api_contact = ApiContactInfo.model_validate(data)
        
        assert api_contact.main_phone == "+5511999999999"
        assert api_contact.main_email == "test@example.com"
        assert api_contact.all_phones == frozenset(["+5511999999999", "+5511888888888"])
        assert api_contact.all_emails == frozenset(["test@example.com", "other@example.com"])

    def test_api_contact_info_deserialization_from_json(self):
        """Validates contact info can be deserialized from JSON."""
        # Given: JSON string with contact info data
        # When: create contact info from JSON
        # Then: contact info is properly created
        json_str = '''
        {
            "main_phone": "+5511999999999",
            "main_email": "test@example.com",
            "all_phones": ["+5511999999999"],
            "all_emails": ["test@example.com"]
        }
        '''
        
        api_contact = ApiContactInfo.model_validate_json(json_str)
        
        assert api_contact.main_phone == "+5511999999999"
        assert api_contact.main_email == "test@example.com"
        assert api_contact.all_phones == frozenset(["+5511999999999"])
        assert api_contact.all_emails == frozenset(["test@example.com"])

    def test_api_contact_info_serialization_with_none_values(self):
        """Validates serialization handles None values correctly."""
        # Given: contact info with None values
        # When: serialize to dict
        # Then: None values are preserved
        api_contact = ApiContactInfo()
        
        result = api_contact.model_dump()
        
        assert result["main_phone"] is None
        assert result["main_email"] is None
        assert result["all_phones"] == frozenset()
        assert result["all_emails"] == frozenset()

    def test_api_contact_info_serialization_roundtrip(self):
        """Validates roundtrip serialization maintains data integrity."""
        # Given: contact info with all fields
        # When: serialize to JSON and deserialize back
        # Then: data integrity is maintained
        original_contact = ApiContactInfo(
            main_phone="+5511999999999",
            main_email="test@example.com",
            all_phones=frozenset(["+5511999999999", "+5511888888888"]),
            all_emails=frozenset(["test@example.com", "other@example.com"])
        )
        
        json_str = original_contact.model_dump_json()
        deserialized_contact = ApiContactInfo.model_validate_json(json_str)
        
        assert deserialized_contact == original_contact


class TestApiContactInfoDomainConversion:
    """Test contact info conversion between API schema and domain model."""

    def test_api_contact_info_from_domain_conversion(self):
        """Validates conversion from domain model to API schema."""
        # Given: domain contact info model
        # When: convert to API schema
        # Then: all fields are properly converted
        domain_contact = ContactInfo(
            main_phone="+5511999999999",
            main_email="test@example.com",
            all_phones=frozenset(["+5511999999999", "+5511888888888"]),
            all_emails=frozenset(["test@example.com", "other@example.com"])
        )
        
        api_contact = ApiContactInfo.from_domain(domain_contact)
        
        assert api_contact.main_phone == "+5511999999999"
        assert api_contact.main_email == "test@example.com"
        assert api_contact.all_phones == frozenset(["+5511999999999", "+5511888888888"])
        assert api_contact.all_emails == frozenset(["test@example.com", "other@example.com"])

    def test_api_contact_info_to_domain_conversion(self):
        """Validates conversion from API schema to domain model."""
        # Given: API contact info schema
        # When: convert to domain model
        # Then: all fields are properly converted
        api_contact = ApiContactInfo(
            main_phone="+5511999999999",
            main_email="test@example.com",
            all_phones=frozenset(["+5511999999999", "+5511888888888"]),
            all_emails=frozenset(["test@example.com", "other@example.com"])
        )
        
        domain_contact = api_contact.to_domain()
        
        assert domain_contact.main_phone == "+5511999999999"
        assert domain_contact.main_email == "test@example.com"
        assert domain_contact.all_phones == frozenset(["+5511999999999", "+5511888888888"])
        assert domain_contact.all_emails == frozenset(["test@example.com", "other@example.com"])

    def test_api_contact_info_domain_conversion_roundtrip(self):
        """Validates roundtrip conversion maintains data integrity."""
        # Given: domain contact info model
        # When: convert to API schema and back to domain
        # Then: data integrity is maintained
        original_domain = ContactInfo(
            main_phone="+5511999999999",
            main_email="test@example.com",
            all_phones=frozenset(["+5511999999999", "+5511888888888"]),
            all_emails=frozenset(["test@example.com", "other@example.com"])
        )
        
        api_contact = ApiContactInfo.from_domain(original_domain)
        converted_domain = api_contact.to_domain()
        
        assert converted_domain == original_domain

    def test_api_contact_info_domain_conversion_with_none_values(self):
        """Validates conversion handles None values correctly."""
        # Given: domain contact info with None values
        # When: convert to API schema and back
        # Then: None values are preserved
        original_domain = ContactInfo(
            main_phone=None,
            main_email=None,
            all_phones=frozenset(),
            all_emails=frozenset()
        )
        
        api_contact = ApiContactInfo.from_domain(original_domain)
        converted_domain = api_contact.to_domain()
        
        assert converted_domain == original_domain


class TestApiContactInfoOrmConversion:
    """Test contact info conversion between API schema and ORM model."""

    def test_api_contact_info_from_orm_model_conversion(self):
        """Validates conversion from ORM model to API schema."""
        # Given: ORM contact info model
        # When: convert to API schema
        # Then: all fields are properly converted
        orm_contact = ContactInfoSaModel(
            main_phone="+5511999999999",
            main_email="test@example.com",
            all_phones=["+5511999999999", "+5511888888888"],
            all_emails=["test@example.com", "other@example.com"]
        )
        
        api_contact = ApiContactInfo.from_orm_model(orm_contact)
        
        assert api_contact.main_phone == "+5511999999999"
        assert api_contact.main_email == "test@example.com"
        assert api_contact.all_phones == frozenset(["+5511999999999", "+5511888888888"])
        assert api_contact.all_emails == frozenset(["test@example.com", "other@example.com"])

    def test_api_contact_info_to_orm_kwargs_conversion(self):
        """Validates conversion from API schema to ORM kwargs."""
        # Given: API contact info schema
        # When: convert to ORM kwargs
        # Then: all fields are properly converted
        api_contact = ApiContactInfo(
            main_phone="+5511999999999",
            main_email="test@example.com",
            all_phones=frozenset(["+5511999999999", "+5511888888888"]),
            all_emails=frozenset(["test@example.com", "other@example.com"])
        )
        
        orm_kwargs = api_contact.to_orm_kwargs()
        
        assert orm_kwargs["main_phone"] == "+5511999999999"
        assert orm_kwargs["main_email"] == "test@example.com"
        assert set(orm_kwargs["all_phones"]) == {"+5511999999999", "+5511888888888"}
        assert set(orm_kwargs["all_emails"]) == {"test@example.com", "other@example.com"}

    def test_api_contact_info_orm_conversion_roundtrip(self):
        """Validates roundtrip conversion maintains data integrity."""
        # Given: ORM contact info model
        # When: convert to API schema and back to ORM kwargs
        # Then: data integrity is maintained
        original_orm = ContactInfoSaModel(
            main_phone="+5511999999999",
            main_email="test@example.com",
            all_phones=["+5511999999999", "+5511888888888"],
            all_emails=["test@example.com", "other@example.com"]
        )
        
        api_contact = ApiContactInfo.from_orm_model(original_orm)
        orm_kwargs = api_contact.to_orm_kwargs()
        
        # Create new ORM model from kwargs for comparison
        new_orm = ContactInfoSaModel(**orm_kwargs)
        
        assert new_orm.main_phone == original_orm.main_phone
        assert new_orm.main_email == original_orm.main_email
        assert set(new_orm.all_phones or []) == set(original_orm.all_phones or [])
        assert set(new_orm.all_emails or []) == set(original_orm.all_emails or [])

    def test_api_contact_info_orm_conversion_with_none_values(self):
        """Validates conversion handles None values correctly."""
        # Given: ORM contact info with None values
        # When: convert to API schema and back
        # Then: None values are preserved
        original_orm = ContactInfoSaModel()
        
        api_contact = ApiContactInfo.from_orm_model(original_orm)
        orm_kwargs = api_contact.to_orm_kwargs()
        
        new_orm = ContactInfoSaModel(**orm_kwargs)
        
        assert new_orm.main_phone is None
        assert new_orm.main_email is None
        assert new_orm.all_phones == []
        assert new_orm.all_emails == []

    def test_api_contact_info_orm_conversion_with_none_collections(self):
        """Validates conversion handles None collections correctly."""
        # Given: ORM contact info with None collections
        # When: convert to API schema and back
        # Then: None collections are handled properly
        original_orm = ContactInfoSaModel(
            main_phone="+5511999999999",
            main_email="test@example.com",
            all_phones=None,
            all_emails=None
        )
        
        api_contact = ApiContactInfo.from_orm_model(original_orm)
        orm_kwargs = api_contact.to_orm_kwargs()
        
        new_orm = ContactInfoSaModel(**orm_kwargs)
        
        assert new_orm.main_phone == "+5511999999999"
        assert new_orm.main_email == "test@example.com"
        assert new_orm.all_phones == []
        assert new_orm.all_emails == []


class TestApiContactInfoEdgeCases:
    """Test contact info schema edge cases and error handling."""

    def test_api_contact_info_validation_whitespace_handling(self):
        """Validates whitespace in phone and email is handled correctly."""
        # Given: phone and email with whitespace
        # When: create contact info with whitespace
        # Then: whitespace is properly handled
        api_contact = ApiContactInfo(
            main_phone="  +5511999999999  ",
            main_email="  test@example.com  "
        )
        
        # Phone should be trimmed (validation trims whitespace)
        assert api_contact.main_phone == "+5511999999999"
        # Email should be normalized to lowercase
        assert api_contact.main_email == "test@example.com"

    def test_api_contact_info_validation_empty_strings(self):
        """Validates empty strings are handled correctly."""
        # Given: empty strings
        # When: create contact info with empty strings
        # Then: empty strings become None
        api_contact = ApiContactInfo(
            main_phone="",
            main_email=""
        )
        
        assert api_contact.main_phone is None
        assert api_contact.main_email is None

    def test_api_contact_info_validation_collection_with_empty_strings(self):
        """Validates collections filter out empty strings."""
        # Given: collection with empty strings
        # When: create contact info with empty strings in collections
        # Then: empty strings are filtered out
        api_contact = ApiContactInfo(
            all_phones=frozenset(["+5511999999999", "", "  "]),
            all_emails=frozenset(["test@example.com", "", "  "])
        )
        
        # Only valid values should remain
        assert api_contact.all_phones == frozenset(["+5511999999999"])
        assert api_contact.all_emails == frozenset(["test@example.com"])

    def test_api_contact_info_validation_duplicate_values_in_collections(self):
        """Validates duplicate values in collections are handled correctly."""
        # Given: collection with duplicate values
        # When: create contact info with duplicates
        # Then: duplicates are automatically removed (frozenset behavior)
        api_contact = ApiContactInfo(
            all_phones=frozenset(["+5511999999999", "+5511999999999"]),
            all_emails=frozenset(["test@example.com", "test@example.com"])
        )
        
        # Frozenset automatically removes duplicates
        assert api_contact.all_phones == frozenset(["+5511999999999"])
        assert api_contact.all_emails == frozenset(["test@example.com"])

    def test_api_contact_info_validation_case_sensitivity_emails(self):
        """Validates email case sensitivity is handled correctly."""
        # Given: emails with different cases
        # When: create contact info with mixed case emails
        # Then: emails are normalized to lowercase
        api_contact = ApiContactInfo(
            main_email="TEST@EXAMPLE.COM",
            all_emails=frozenset(["Test@Example.Com", "ANOTHER@DOMAIN.ORG"])
        )
        
        assert api_contact.main_email == "test@example.com"
        assert api_contact.all_emails == frozenset(["test@example.com", "another@domain.org"])

    def test_api_contact_info_validation_unicode_characters(self):
        """Validates unicode characters are handled correctly."""
        # Given: contact info with unicode characters
        # When: serialize and deserialize
        # Then: unicode characters are preserved
        api_contact = ApiContactInfo(
            main_phone="+5511999999999",
            main_email="test@example.com"
        )
        
        json_str = api_contact.model_dump_json()
        deserialized = ApiContactInfo.model_validate_json(json_str)
        
        assert deserialized.main_phone == "+5511999999999"
        assert deserialized.main_email == "test@example.com"

    def test_api_contact_info_immutability(self):
        """Validates contact info schema is immutable."""
        # Given: contact info instance
        # When: attempt to modify fields
        # Then: modification raises error
        api_contact = ApiContactInfo(main_phone="+5511999999999")
        
        with pytest.raises(ValidationError):
            api_contact.main_phone = "+5511888888888"

    def test_api_contact_info_validation_security_patterns_blocked(self):
        """Validates security patterns are blocked in phone and email."""
        # Given: phone and email with security patterns
        # When: create contact info with dangerous patterns
        # Then: validation errors are raised
        dangerous_patterns = [
            "<script>alert('xss')</script>@example.com",
            "phone<script>alert('xss')</script>",
            "test@example.com<script>alert('xss')</script>",
        ]
        
        for pattern in dangerous_patterns:
            with pytest.raises(ValidationError):
                if "@" in pattern:
                    ApiContactInfo(main_email=pattern)
                else:
                    ApiContactInfo(main_phone=pattern)

    def test_api_contact_info_validation_maximum_length_emails(self):
        """Validates maximum length emails are handled correctly."""
        # Given: email at maximum length
        # When: create contact info with max length email
        # Then: email is accepted
        max_local = "a" * 64  # Maximum local part length
        max_domain = "example.com"
        max_email = f"{max_local}@{max_domain}"
        
        api_contact = ApiContactInfo(main_email=max_email)
        assert api_contact.main_email == max_email

    def test_api_contact_info_validation_exceeds_maximum_length_emails(self):
        """Validates emails exceeding maximum length raise validation error."""
        # Given: email exceeding maximum length
        # When: create contact info with too long email
        # Then: validation error is raised
        too_long_local = "a" * 65  # Exceeds local part length limit
        too_long_email = f"{too_long_local}@example.com"
        
        with pytest.raises(ValidationError):
            ApiContactInfo(main_email=too_long_email)
