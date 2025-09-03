"""Unit tests for ApiProfile schema.

Tests profile schema validation, serialization/deserialization, and conversion methods.
Follows testing principles: no I/O, fakes only, behavior-focused assertions.
"""

import pytest
from datetime import date
from pydantic import ValidationError

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_profile import ApiProfile
from src.contexts.shared_kernel.adapters.ORM.sa_models.profile_sa_model import ProfileSaModel
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import ValidationConversionError


class TestApiProfileValidation:
    """Test profile schema validation and field constraints."""

    def test_api_profile_validation_minimal_valid_profile(self):
        """Validates minimal valid profile creation."""
        # Given: minimal required profile components
        # When: create profile with valid components
        # Then: profile is created successfully
        api_profile = ApiProfile(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        assert api_profile.name == "João Silva"
        assert api_profile.birthday == date(1990, 5, 15)
        assert api_profile.sex == "masculino"

    def test_api_profile_validation_all_fields_populated(self):
        """Validates profile with all fields populated."""
        # Given: complete profile information
        # When: create profile with all components
        # Then: all fields are properly set
        api_profile = ApiProfile(
            name="Maria Santos",
            birthday=date(1985, 12, 3),
            sex="feminino"
        )
        assert api_profile.name == "Maria Santos"
        assert api_profile.birthday == date(1985, 12, 3)
        assert api_profile.sex == "feminino"

    def test_api_profile_validation_name_trimming(self):
        """Validates name field is trimmed automatically."""
        # Given: name with leading/trailing whitespace
        # When: create profile with whitespace
        # Then: name is trimmed
        api_profile = ApiProfile(
            name="  João Silva  ",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        assert api_profile.name == "João Silva"

    def test_api_profile_validation_name_length_constraints(self):
        """Validates name field length constraints."""
        # Given: name exceeding maximum length
        # When: create profile with long name
        # Then: validation error is raised
        long_name = "x" * 256  # Exceeds 255 character limit
        
        with pytest.raises(ValidationError):
            ApiProfile(
                name=long_name,
                birthday=date(1990, 5, 15),
                sex="masculino"
            )

    def test_api_profile_validation_name_minimum_length(self):
        """Validates name field minimum length constraint."""
        # Given: empty name
        # When: create profile with empty name
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiProfile(
                name="",
                birthday=date(1990, 5, 15),
                sex="masculino"
            )

    def test_api_profile_validation_sex_options_masculino(self):
        """Validates sex field accepts 'masculino' value."""
        # Given: valid sex value
        # When: create profile with 'masculino'
        # Then: profile is created successfully
        api_profile = ApiProfile(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        assert api_profile.sex == "masculino"

    def test_api_profile_validation_sex_options_feminino(self):
        """Validates sex field accepts 'feminino' value."""
        # Given: valid sex value
        # When: create profile with 'feminino'
        # Then: profile is created successfully
        api_profile = ApiProfile(
            name="Maria Santos",
            birthday=date(1985, 12, 3),
            sex="feminino"
        )
        assert api_profile.sex == "feminino"

    def test_api_profile_validation_sex_options_case_insensitive(self):
        """Validates sex field is case insensitive."""
        # Given: sex value with different case
        # When: create profile with uppercase sex
        # Then: sex is normalized to lowercase
        api_profile = ApiProfile(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="MASCULINO"
        )
        assert api_profile.sex == "masculino"

    def test_api_profile_validation_sex_options_invalid(self):
        """Validates sex field rejects invalid values."""
        # Given: invalid sex value
        # When: create profile with invalid sex
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiProfile(
                name="João Silva",
                birthday=date(1990, 5, 15),
                sex="invalid"
            )

    def test_api_profile_validation_birthday_reasonable_range(self):
        """Validates birthday field accepts reasonable date range."""
        # Given: birthday within reasonable range
        # When: create profile with valid birthday
        # Then: profile is created successfully
        api_profile = ApiProfile(
            name="João Silva",
            birthday=date(1950, 1, 1),
            sex="masculino"
        )
        assert api_profile.birthday == date(1950, 1, 1)

    def test_api_profile_validation_birthday_too_early(self):
        """Validates birthday field rejects dates before 1900."""
        # Given: birthday before 1900
        # When: create profile with early birthday
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiProfile(
                name="João Silva",
                birthday=date(1899, 12, 31),
                sex="masculino"
            )

    def test_api_profile_validation_birthday_future_date(self):
        """Validates birthday field rejects future dates."""
        # Given: future birthday
        # When: create profile with future birthday
        # Then: validation error is raised
        future_date = date(2030, 1, 1)
        with pytest.raises(ValidationError):
            ApiProfile(
                name="João Silva",
                birthday=future_date,
                sex="masculino"
            )

    def test_api_profile_validation_unicode_characters(self):
        """Validates profile handles unicode characters correctly."""
        # Given: profile with unicode characters
        # When: create profile with unicode name
        # Then: unicode characters are preserved
        api_profile = ApiProfile(
            name="José da Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        assert api_profile.name == "José da Silva"


class TestApiProfileEquality:
    """Test profile equality semantics and value object contracts."""

    def test_api_profile_equality_same_values(self):
        """Ensures proper equality semantics for identical values."""
        # Given: two profile instances with same values
        # When: compare profiles
        # Then: they should be equal
        profile1 = ApiProfile(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        profile2 = ApiProfile(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        assert profile1 == profile2

    def test_api_profile_equality_different_values(self):
        """Ensures proper inequality semantics for different values."""
        # Given: two profile instances with different values
        # When: compare profiles
        # Then: they should not be equal
        profile1 = ApiProfile(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        profile2 = ApiProfile(
            name="Maria Santos",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        assert profile1 != profile2

    def test_api_profile_equality_different_birthdays(self):
        """Ensures different birthday values result in inequality."""
        # Given: two profiles with different birthdays
        # When: compare profiles
        # Then: they should not be equal
        profile1 = ApiProfile(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        profile2 = ApiProfile(
            name="João Silva",
            birthday=date(1991, 5, 15),
            sex="masculino"
        )
        assert profile1 != profile2

    def test_api_profile_equality_different_sex(self):
        """Ensures different sex values result in inequality."""
        # Given: two profiles with different sex
        # When: compare profiles
        # Then: they should not be equal
        profile1 = ApiProfile(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        profile2 = ApiProfile(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="feminino"
        )
        assert profile1 != profile2


class TestApiProfileSerialization:
    """Test profile serialization and deserialization contracts."""

    def test_api_profile_serialization_to_dict(self):
        """Validates profile can be serialized to dictionary."""
        # Given: profile with all fields
        # When: serialize to dict
        # Then: all fields are properly serialized
        api_profile = ApiProfile(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        
        result = api_profile.model_dump()
        
        assert result["name"] == "João Silva"
        assert result["birthday"] == date(1990, 5, 15)
        assert result["sex"] == "masculino"

    def test_api_profile_serialization_to_json(self):
        """Validates profile can be serialized to JSON."""
        # Given: profile with all fields
        # When: serialize to JSON
        # Then: JSON is properly formatted
        api_profile = ApiProfile(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        
        json_str = api_profile.model_dump_json()
        
        assert '"name":"João Silva"' in json_str
        assert '"birthday":"1990-05-15"' in json_str
        assert '"sex":"masculino"' in json_str

    def test_api_profile_deserialization_from_dict(self):
        """Validates profile can be deserialized from dictionary."""
        # Given: dictionary with profile data
        # When: create profile from dict
        # Then: profile is properly created
        data = {
            "name": "João Silva",
            "birthday": date(1990, 5, 15),
            "sex": "masculino"
        }
        
        api_profile = ApiProfile.model_validate(data)
        
        assert api_profile.name == "João Silva"
        assert api_profile.birthday == date(1990, 5, 15)
        assert api_profile.sex == "masculino"

    def test_api_profile_deserialization_from_json(self):
        """Validates profile can be deserialized from JSON."""
        # Given: JSON string with profile data
        # When: create profile from JSON
        # Then: profile is properly created
        json_str = '''
        {
            "name": "João Silva",
            "birthday": "1990-05-15",
            "sex": "masculino"
        }
        '''
        
        api_profile = ApiProfile.model_validate_json(json_str)
        
        assert api_profile.name == "João Silva"
        assert api_profile.birthday == date(1990, 5, 15)
        assert api_profile.sex == "masculino"

    def test_api_profile_serialization_unicode_characters(self):
        """Validates serialization handles unicode characters correctly."""
        # Given: profile with unicode characters
        # When: serialize and deserialize
        # Then: unicode characters are preserved
        api_profile = ApiProfile(
            name="José da Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        
        json_str = api_profile.model_dump_json()
        deserialized = ApiProfile.model_validate_json(json_str)
        
        assert deserialized.name == "José da Silva"
        assert deserialized.birthday == date(1990, 5, 15)
        assert deserialized.sex == "masculino"


class TestApiProfileDomainConversion:
    """Test profile conversion between API schema and domain model."""

    def test_api_profile_from_domain_conversion(self):
        """Validates conversion from domain model to API schema."""
        # Given: domain profile model
        # When: convert to API schema
        # Then: all fields are properly converted
        domain_profile = Profile(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        
        api_profile = ApiProfile.from_domain(domain_profile)
        
        assert api_profile.name == "João Silva"
        assert api_profile.birthday == date(1990, 5, 15)
        assert api_profile.sex == "masculino"

    def test_api_profile_to_domain_conversion(self):
        """Validates conversion from API schema to domain model."""
        # Given: API profile schema
        # When: convert to domain model
        # Then: all fields are properly converted
        api_profile = ApiProfile(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        
        domain_profile = api_profile.to_domain()
        
        assert domain_profile.name == "João Silva"
        assert domain_profile.birthday == date(1990, 5, 15)
        assert domain_profile.sex == "masculino"

    def test_api_profile_domain_conversion_roundtrip(self):
        """Validates roundtrip conversion maintains data integrity."""
        # Given: domain profile model
        # When: convert to API schema and back to domain
        # Then: data integrity is maintained
        original_domain = Profile(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        
        api_profile = ApiProfile.from_domain(original_domain)
        converted_domain = api_profile.to_domain()
        
        assert converted_domain == original_domain

    def test_api_profile_domain_conversion_unicode_handling(self):
        """Validates unicode conversion between API and domain."""
        # Given: API profile with unicode characters
        # When: convert to domain and back
        # Then: unicode characters are properly handled
        api_profile = ApiProfile(
            name="José da Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        
        domain_profile = api_profile.to_domain()
        converted_api = ApiProfile.from_domain(domain_profile)
        
        assert converted_api.name == "José da Silva"
        assert domain_profile.name == "José da Silva"


class TestApiProfileOrmConversion:
    """Test profile conversion between API schema and ORM model."""

    def test_api_profile_from_orm_model_conversion(self):
        """Validates conversion from ORM model to API schema."""
        # Given: ORM profile model
        # When: convert to API schema
        # Then: all fields are properly converted
        orm_profile = ProfileSaModel(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        
        api_profile = ApiProfile.from_orm_model(orm_profile)
        
        assert api_profile.name == "João Silva"
        assert api_profile.birthday == date(1990, 5, 15)
        assert api_profile.sex == "masculino"

    def test_api_profile_to_orm_kwargs_conversion(self):
        """Validates conversion from API schema to ORM kwargs."""
        # Given: API profile schema
        # When: convert to ORM kwargs
        # Then: all fields are properly converted
        api_profile = ApiProfile(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        
        orm_kwargs = api_profile.to_orm_kwargs()
        
        assert orm_kwargs["name"] == "João Silva"
        assert orm_kwargs["birthday"] == date(1990, 5, 15)
        assert orm_kwargs["sex"] == "masculino"

    def test_api_profile_orm_conversion_roundtrip(self):
        """Validates roundtrip conversion maintains data integrity."""
        # Given: ORM profile model
        # When: convert to API schema and back to ORM kwargs
        # Then: data integrity is maintained
        original_orm = ProfileSaModel(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        
        api_profile = ApiProfile.from_orm_model(original_orm)
        orm_kwargs = api_profile.to_orm_kwargs()
        
        # Create new ORM model from kwargs for comparison
        new_orm = ProfileSaModel(**orm_kwargs)
        
        assert new_orm.name == original_orm.name
        assert new_orm.birthday == original_orm.birthday
        assert new_orm.sex == original_orm.sex

    def test_api_profile_orm_conversion_with_none_birthday_raises_error(self):
        """Validates conversion raises error when ORM has None birthday."""
        # Given: ORM profile with None birthday
        # When: convert to API schema
        # Then: ValidationError is raised (API schema requires date)
        original_orm = ProfileSaModel(
            name="João Silva",
            birthday=None,
            sex="masculino"
        )
        
        with pytest.raises(ValidationError):
            ApiProfile.from_orm_model(original_orm)

    def test_api_profile_orm_conversion_unicode_handling(self):
        """Validates unicode conversion between API and ORM."""
        # Given: API profile with unicode characters
        # When: convert to ORM kwargs
        # Then: unicode characters are properly handled
        api_profile = ApiProfile(
            name="José da Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        
        orm_kwargs = api_profile.to_orm_kwargs()
        
        assert orm_kwargs["name"] == "José da Silva"
        assert orm_kwargs["birthday"] == date(1990, 5, 15)
        assert orm_kwargs["sex"] == "masculino"


class TestApiProfileEdgeCases:
    """Test profile schema edge cases and error handling."""

    def test_api_profile_from_orm_model_none_raises_error(self):
        """Validates from_orm_model raises error when ORM model is None."""
        # Given: None ORM model
        # When: convert to API schema
        # Then: ValidationConversionError is raised
        with pytest.raises(ValidationConversionError) as exc_info:
            ApiProfile.from_orm_model(None)
        
        assert "ORM model cannot be None" in str(exc_info.value)
        assert exc_info.value.schema_class == ApiProfile
        assert exc_info.value.conversion_direction == "orm_to_api"

    def test_api_profile_validation_whitespace_only_name(self):
        """Validates whitespace-only name is converted to None."""
        # Given: whitespace-only name
        # When: create profile with whitespace name
        # Then: name becomes None and validation fails
        with pytest.raises(ValidationError):
            ApiProfile(
                name="   ",
                birthday=date(1990, 5, 15),
                sex="masculino"
            )

    def test_api_profile_validation_mixed_whitespace_and_content(self):
        """Validates mixed whitespace and content is properly trimmed."""
        # Given: name with mixed whitespace and content
        # When: create profile with mixed content
        # Then: content is properly trimmed
        api_profile = ApiProfile(
            name="  João Silva  \t",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        assert api_profile.name == "João Silva"

    def test_api_profile_validation_maximum_length_name(self):
        """Validates maximum length name is accepted."""
        # Given: name at maximum length
        # When: create profile with max length name
        # Then: profile is created successfully
        max_name = "x" * 255
        
        api_profile = ApiProfile(
            name=max_name,
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        
        assert api_profile.name == max_name

    def test_api_profile_validation_birthday_boundary_values(self):
        """Validates birthday boundary values are handled correctly."""
        # Given: boundary birthday values
        # When: create profiles with boundary dates
        # Then: valid dates are accepted, invalid dates are rejected
        
        # Valid: exactly 1900-01-01
        api_profile = ApiProfile(
            name="João Silva",
            birthday=date(1900, 1, 1),
            sex="masculino"
        )
        assert api_profile.birthday == date(1900, 1, 1)
        
        # Invalid: one day before 1900
        with pytest.raises(ValidationError):
            ApiProfile(
                name="João Silva",
                birthday=date(1899, 12, 31),
                sex="masculino"
            )

    def test_api_profile_immutability(self):
        """Validates profile schema is immutable."""
        # Given: profile instance
        # When: attempt to modify fields
        # Then: modification raises error
        api_profile = ApiProfile(
            name="João Silva",
            birthday=date(1990, 5, 15),
            sex="masculino"
        )
        
        with pytest.raises(ValidationError):
            api_profile.name = "Maria Santos"

    def test_api_profile_validation_sex_case_normalization(self):
        """Validates sex field case normalization works correctly."""
        # Given: sex values with different cases
        # When: create profiles with different case sex values
        # Then: all valid cases are normalized to lowercase
        
        test_cases = [
            ("MASCULINO", "masculino"),
            ("Masculino", "masculino"),
            ("FEMININO", "feminino"),
            ("Feminino", "feminino"),
        ]
        
        for input_sex, expected_sex in test_cases:
            api_profile = ApiProfile(
                name="João Silva",
                birthday=date(1990, 5, 15),
                sex=input_sex
            )
            assert api_profile.sex == expected_sex

    def test_api_profile_validation_comprehensive_error_messages(self):
        """Validates comprehensive error messages for validation failures."""
        # Given: various invalid inputs
        # When: create profiles with invalid data
        # Then: clear error messages are provided
        
        # Test empty name
        with pytest.raises(ValidationError) as exc_info:
            ApiProfile(
                name="",
                birthday=date(1990, 5, 15),
                sex="masculino"
            )
        assert "Input should be a valid string" in str(exc_info.value)
        
        # Test invalid sex
        with pytest.raises(ValidationError) as exc_info:
            ApiProfile(
                name="João Silva",
                birthday=date(1990, 5, 15),
                sex="invalid"
            )
        assert "Invalid sex: invalid" in str(exc_info.value)
        
        # Test future birthday
        with pytest.raises(ValidationError) as exc_info:
            ApiProfile(
                name="João Silva",
                birthday=date(2030, 1, 1),
                sex="masculino"
            )
        assert "Birthday cannot be in the future" in str(exc_info.value)
