"""
Behavior-focused tests for ApiProfile schema standardization.

These tests validate the behavior and correctness of ApiProfile schema
following the documented API schema patterns.

Focus: Test behavior and verify correctness, not implementation details.
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_profile import ApiProfile


class TestApiProfileStandardization:
    """Test ApiProfile schema standardization and behavior."""

    def test_profile_creation_with_valid_data(self):
        """Test that ApiProfile accepts valid profile data."""
        profile = ApiProfile(
            name="John Doe",
            birthday=date(1990, 5, 15),
            sex="male"
        )
        
        assert profile.name == "John Doe"
        assert profile.birthday == date(1990, 5, 15)
        assert profile.sex == "male"

    def test_profile_creation_with_none_values(self):
        """Test that ApiProfile validates required fields properly."""
        # All fields are required, so this should raise validation errors
        with pytest.raises(ValueError):
            profile = ApiProfile(
                name=None,  # type: ignore
                birthday=None,  # type: ignore  
                sex=None  # type: ignore
            )

    def test_name_field_validation_trims_whitespace(self):
        """Test that name field trims whitespace as expected."""
        profile = ApiProfile(
            name="  John Doe  ",
            birthday=date(1990, 1, 1),
            sex="masculino"
        )
        assert profile.name == "John Doe"

    def test_name_field_validation_handles_empty_string(self):
        """Test that empty string raises validation error for required field."""
        with pytest.raises(ValueError):
            profile = ApiProfile(
                name="   ",
                birthday=date(1990, 1, 1),
                sex="masculino"
            )

    def test_sex_field_validation_normalizes_case(self):
        """Test that sex field normalizes to lowercase."""
        profile = ApiProfile(
            name="Test User",
            birthday=date(1990, 1, 1),
            sex="MASCULINO"
        )
        assert profile.sex == "masculino"

    def test_sex_field_validation_handles_valid_options(self):
        """Test that valid sex options are accepted."""
        valid_options = ["masculino", "feminino"]
        
        for option in valid_options:
            profile = ApiProfile(
                name="Test User",
                birthday=date(1990, 1, 1),
                sex=option
            )
            assert profile.sex == option.lower()

    def test_sex_field_validation_rejects_invalid_values(self):
        """Test that invalid sex values are rejected."""
        with pytest.raises(ValueError):
            profile = ApiProfile(
                name="Test User",
                birthday=date(1990, 1, 1),
                sex="invalid_value"
            )

    def test_birthday_validation_rejects_future_date(self):
        """Test that future birthdates are rejected."""
        future_date = date.today() + timedelta(days=1)
        
        with pytest.raises(ValueError, match="Birthday cannot be in the future"):
            ApiProfile(
                name="Test User",
                birthday=future_date,
                sex="masculino"
            )

    def test_birthday_validation_rejects_unreasonably_old_date(self):
        """Test that unreasonably old birthdates are rejected."""
        old_date = date(1800, 1, 1)
        
        with pytest.raises(ValueError, match="Birthday year must be after"):
            ApiProfile(
                name="Test User",
                birthday=old_date,
                sex="masculino"
            )

    def test_birthday_validation_accepts_reasonable_dates(self):
        """Test that reasonable birthdates are accepted."""
        reasonable_dates = [
            date(1950, 1, 1),
            date(1990, 6, 15),
            date(2000, 12, 31)
        ]
        
        for birth_date in reasonable_dates:
            profile = ApiProfile(
                name="Test User",
                birthday=birth_date,
                sex="masculino"
            )
            assert profile.birthday == birth_date

    def test_from_domain_conversion_preserves_data(self):
        """Test that from_domain conversion preserves all data correctly."""
        # Create mock domain object
        domain_profile = Mock()
        domain_profile.name = "Jane Smith"
        domain_profile.birthday = date(1985, 3, 20)
        domain_profile.sex = "female"
        
        api_profile = ApiProfile.from_domain(domain_profile)
        
        assert api_profile.name == "Jane Smith"
        assert api_profile.birthday == date(1985, 3, 20)
        assert api_profile.sex == "female"

    def test_to_domain_conversion_preserves_data(self):
        """Test that to_domain conversion preserves all data correctly."""
        api_profile = ApiProfile(
            name="Bob Johnson",
            birthday=date(1975, 8, 10),
            sex="male"
        )
        
        domain_profile = api_profile.to_domain()
        
        assert domain_profile.name == "Bob Johnson"
        assert domain_profile.birthday == date(1975, 8, 10)
        assert domain_profile.sex == "male"

    def test_from_orm_model_conversion_with_valid_data(self):
        """Test from_orm_model conversion with valid ORM data."""
        orm_model = Mock()
        orm_model.name = "Alice Brown"
        orm_model.birthday = date(1992, 11, 5)
        orm_model.sex = "female"
        
        api_profile = ApiProfile.from_orm_model(orm_model)
        
        assert api_profile.name == "Alice Brown"
        assert api_profile.birthday == date(1992, 11, 5)
        assert api_profile.sex == "female"

    def test_from_orm_model_rejects_none_input(self):
        """Test that from_orm_model rejects None input."""
        with pytest.raises(ValueError, match="ORM model cannot be None"):
            ApiProfile.from_orm_model(None)

    def test_to_orm_kwargs_conversion_provides_correct_format(self):
        """Test that to_orm_kwargs provides correctly formatted data."""
        api_profile = ApiProfile(
            name="Charlie Davis",
            birthday=date(1988, 2, 14),
            sex="other"
        )
        
        orm_kwargs = api_profile.to_orm_kwargs()
        
        expected_kwargs = {
            "name": "Charlie Davis",
            "birthday": date(1988, 2, 14),
            "sex": "other"
        }
        assert orm_kwargs == expected_kwargs

    def test_round_trip_conversion_preserves_data_integrity(self):
        """Test that domain → API → domain conversion preserves data integrity."""
        # Create mock domain object
        original_domain = Mock()
        original_domain.name = "Eva White"
        original_domain.birthday = date(1993, 7, 25)
        original_domain.sex = "non_binary"
        
        # Convert to API and back
        api_profile = ApiProfile.from_domain(original_domain)
        converted_domain = api_profile.to_domain()
        
        assert converted_domain.name == original_domain.name
        assert converted_domain.birthday == original_domain.birthday
        assert converted_domain.sex == original_domain.sex
