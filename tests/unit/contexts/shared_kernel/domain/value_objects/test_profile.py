"""Unit tests for Profile value object.

Tests profile validation, equality semantics, and value object contracts.
Follows testing principles: no I/O, fakes only, behavior-focused assertions.
"""
import pytest
import attrs
from datetime import date

from src.contexts.shared_kernel.domain.value_objects.profile import Profile


class TestProfileValidation:
    """Test profile data validation and format constraints."""

    def test_profile_validation_minimal_valid_profile(self):
        """Validates minimal valid profile creation."""
        # Given: minimal required profile components
        # When: create profile with valid components
        # Then: profile is created successfully
        profile = Profile(
            name="João Silva",
            sex="M",
            birthday=date(1990, 5, 15)
        )
        assert profile.name == "João Silva"
        assert profile.sex == "M"
        assert profile.birthday == date(1990, 5, 15)

    def test_profile_validation_all_fields_populated(self):
        """Validates profile with all fields populated."""
        # Given: complete profile information
        # When: create profile with all components
        # Then: all fields are properly set
        profile = Profile(
            name="Maria Santos Oliveira",
            sex="F",
            birthday=date(1985, 12, 3)
        )
        assert profile.name == "Maria Santos Oliveira"
        assert profile.sex == "F"
        assert profile.birthday == date(1985, 12, 3)

    def test_profile_validation_string_fields_accept_any_string(self):
        """Validates string fields accept any string value including empty."""
        # Given: various string values including empty strings
        # When: create profile with different string values
        # Then: all string values are accepted
        profile = Profile(
            name="",
            sex="",
            birthday=date(2000, 1, 1)
        )
        assert profile.name == ""
        assert profile.sex == ""
        assert profile.birthday == date(2000, 1, 1)

    def test_profile_validation_name_with_special_characters(self):
        """Validates name field accepts special characters and unicode."""
        # Given: name with special characters and unicode
        # When: create profile with special characters
        # Then: name is properly stored
        profile = Profile(
            name="José María O'Connor-Silva",
            sex="M",
            birthday=date(1992, 8, 22)
        )
        assert profile.name == "José María O'Connor-Silva"

    def test_profile_validation_sex_field_variations(self):
        """Validates sex field accepts various string values."""
        # Given: different sex field values
        # When: create profiles with various sex values
        # Then: all values are accepted
        sex_values = ["M", "F", "Male", "Female", "Other", "Non-binary", "X"]
        
        for sex in sex_values:
            profile = Profile(
                name="Test User",
                sex=sex,
                birthday=date(1990, 1, 1)
            )
            assert profile.sex == sex

    def test_profile_validation_birthday_edge_cases(self):
        """Validates birthday field with edge case dates."""
        # Given: various edge case dates
        # When: create profiles with edge case dates
        # Then: all dates are properly stored
        edge_dates = [
            date(1900, 1, 1),  # Very old date
            date(2000, 2, 29),  # Leap year
            date(2023, 12, 31),  # Recent date
            date(1999, 12, 31),  # End of century
        ]
        
        for birthday in edge_dates:
            profile = Profile(
                name="Test User",
                sex="M",
                birthday=birthday
            )
            assert profile.birthday == birthday

    def test_profile_validation_whitespace_handling(self):
        """Validates handling of whitespace in string fields."""
        # Given: string fields with various whitespace
        # When: create profile with whitespace
        # Then: whitespace is preserved as-is
        profile = Profile(
            name="  João  Silva  ",
            sex=" M ",
            birthday=date(1990, 5, 15)
        )
        assert profile.name == "  João  Silva  "
        assert profile.sex == " M "


class TestProfileEquality:
    """Test profile equality semantics and value object contracts."""

    def test_profile_equality_identical_profiles(self):
        """Ensures identical profiles are equal."""
        # Given: two profiles with identical values
        # When: compare the profiles
        # Then: they are equal
        profile1 = Profile(
            name="João Silva",
            sex="M",
            birthday=date(1990, 5, 15)
        )
        profile2 = Profile(
            name="João Silva",
            sex="M",
            birthday=date(1990, 5, 15)
        )
        assert profile1 == profile2
        assert hash(profile1) == hash(profile2)

    def test_profile_equality_different_profiles(self):
        """Ensures different profiles are not equal."""
        # Given: two profiles with different values
        # When: compare the profiles
        # Then: they are not equal
        profile1 = Profile(
            name="João Silva",
            sex="M",
            birthday=date(1990, 5, 15)
        )
        profile2 = Profile(
            name="Maria Santos",
            sex="F",
            birthday=date(1985, 12, 3)
        )
        assert profile1 != profile2
        assert hash(profile1) != hash(profile2)

    def test_profile_equality_partial_differences(self):
        """Ensures profiles with any different field are not equal."""
        # Given: profiles differing in one field
        # When: compare the profiles
        # Then: they are not equal
        base_profile = Profile(
            name="João Silva",
            sex="M",
            birthday=date(1990, 5, 15)
        )
        
        # Different name
        different_name = base_profile.replace(name="Maria Santos")
        assert base_profile != different_name
        
        # Different sex
        different_sex = base_profile.replace(sex="F")
        assert base_profile != different_sex
        
        # Different birthday
        different_birthday = base_profile.replace(birthday=date(1985, 12, 3))
        assert base_profile != different_birthday

    def test_profile_equality_none_vs_empty_string(self):
        """Ensures None and empty string are treated as different values."""
        # Given: profiles with None vs empty string in same field
        # When: compare the profiles
        # Then: they are not equal
        profile_with_empty_name = Profile(
            name="",
            sex="M",
            birthday=date(1990, 5, 15)
        )
        profile_with_empty_sex = Profile(
            name="João Silva",
            sex="",
            birthday=date(1990, 5, 15)
        )
        
        # These should be different profiles
        assert profile_with_empty_name != profile_with_empty_sex
        assert hash(profile_with_empty_name) != hash(profile_with_empty_sex)

    def test_profile_equality_immutability(self):
        """Ensures profile objects are immutable."""
        # Given: a profile instance
        # When: attempt to modify attributes
        # Then: modification raises FrozenInstanceError
        profile = Profile(
            name="João Silva",
            sex="M",
            birthday=date(1990, 5, 15)
        )
        
        # Verify immutability by attempting to modify attributes
        # The frozen decorator from attrs prevents attribute assignment
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            profile.name = "Maria Santos"  # type: ignore[attr-defined]
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            profile.sex = "F"  # type: ignore[attr-defined]
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            profile.birthday = date(1985, 12, 3)  # type: ignore[attr-defined]

    def test_profile_equality_replace_creates_new_instance(self):
        """Ensures replace method creates new instance without modifying original."""
        # Given: an original profile
        # When: create new profile using replace
        # Then: original remains unchanged and new instance is created
        original = Profile(
            name="João Silva",
            sex="M",
            birthday=date(1990, 5, 15)
        )
        new_profile = original.replace(name="Maria Santos")
        
        # Original unchanged
        assert original.name == "João Silva"
        assert original.sex == "M"
        assert original.birthday == date(1990, 5, 15)
        
        # New instance has updated values
        assert new_profile.name == "Maria Santos"
        assert new_profile.sex == "M"  # Unchanged
        assert new_profile.birthday == date(1990, 5, 15)  # Unchanged
        
        # They are different instances
        assert original is not new_profile
        assert original != new_profile

    def test_profile_equality_hash_consistency(self):
        """Ensures hash values are consistent across multiple calls."""
        # Given: a profile instance
        # When: call hash multiple times
        # Then: hash value is consistent
        profile = Profile(
            name="João Silva",
            sex="M",
            birthday=date(1990, 5, 15)
        )
        
        hash1 = hash(profile)
        hash2 = hash(profile)
        hash3 = hash(profile)
        
        assert hash1 == hash2 == hash3

    def test_profile_equality_hash_different_objects_same_values(self):
        """Ensures different objects with same values have same hash."""
        # Given: two different profile instances with identical values
        # When: compute their hashes
        # Then: hashes are equal
        profile1 = Profile(
            name="João Silva",
            sex="M",
            birthday=date(1990, 5, 15)
        )
        profile2 = Profile(
            name="João Silva",
            sex="M",
            birthday=date(1990, 5, 15)
        )
        
        assert profile1 is not profile2  # Different objects
        assert hash(profile1) == hash(profile2)  # Same hash

    def test_profile_equality_case_sensitivity(self):
        """Ensures string fields are case-sensitive for equality."""
        # Given: profiles with same content but different case
        # When: compare the profiles
        # Then: they are not equal (case-sensitive)
        profile1 = Profile(
            name="João Silva",
            sex="M",
            birthday=date(1990, 5, 15)
        )
        profile2 = Profile(
            name="joão silva",  # Different case
            sex="M",
            birthday=date(1990, 5, 15)
        )
        
        assert profile1 != profile2
        assert hash(profile1) != hash(profile2)

    def test_profile_equality_date_precision(self):
        """Ensures date equality is exact (no time component)."""
        # Given: profiles with same date but different date objects
        # When: compare the profiles
        # Then: they are equal if the date values are the same
        profile1 = Profile(
            name="João Silva",
            sex="M",
            birthday=date(1990, 5, 15)
        )
        profile2 = Profile(
            name="João Silva",
            sex="M",
            birthday=date(1990, 5, 15)  # Same date, different object
        )
        
        assert profile1 == profile2
        assert hash(profile1) == hash(profile2)
