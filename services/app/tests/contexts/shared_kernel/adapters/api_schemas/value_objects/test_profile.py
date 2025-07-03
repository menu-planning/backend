import pytest
from datetime import date
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_profile import ApiProfile
from src.contexts.shared_kernel.adapters.ORM.sa_models.profile_sa_model import ProfileSaModel


class TestApiProfile:
    """Test suite for ApiProfile schema."""

    def test_create_valid_profile(self):
        """Test creating a valid profile."""
        profile = ApiProfile(
            name="John Doe",
            birthday=date(1990, 1, 1),
            sex="M"
        )
        assert profile.name == "John Doe"
        assert profile.birthday == date(1990, 1, 1)
        assert profile.sex == "M"

    def test_create_minimal_profile(self):
        """Test creating a profile with minimal fields."""
        profile = ApiProfile(
            name="John Doe",
            sex="M"
        ) # type: ignore
        assert profile.name == "John Doe"
        assert profile.birthday is None
        assert profile.sex == "M"

    def test_from_domain(self):
        """Test converting from domain object."""
        domain_profile = Profile(
            name="John Doe",
            birthday=date(1990, 1, 1),
            sex="M"
        )
        api_profile = ApiProfile.from_domain(domain_profile)
        
        assert api_profile.name == "John Doe"
        assert api_profile.birthday == date(1990, 1, 1)
        assert api_profile.sex == "M"

    def test_to_domain(self):
        """Test converting to domain object."""
        api_profile = ApiProfile(
            name="John Doe",
            birthday=date(1990, 1, 1),
            sex="M"
        )
        domain_profile = api_profile.to_domain()
        
        assert domain_profile.name == "John Doe"
        assert domain_profile.birthday == date(1990, 1, 1)
        assert domain_profile.sex == "M"

    def test_from_orm_model(self):
        """Test converting from ORM model."""
        orm_profile = ProfileSaModel(
            name="John Doe",
            birthday=date(1990, 1, 1),
            sex="M"
        )
        api_profile = ApiProfile.from_orm_model(orm_profile)
        
        assert api_profile.name == "John Doe"
        assert api_profile.birthday == date(1990, 1, 1)
        assert api_profile.sex == "M"

    def test_to_orm_kwargs(self):
        """Test converting to ORM model kwargs."""
        api_profile = ApiProfile(
            name="John Doe",
            birthday=date(1990, 1, 1),
            sex="M"
        )
        orm_kwargs = api_profile.to_orm_kwargs()
        
        assert orm_kwargs["name"] == "John Doe"
        assert orm_kwargs["birthday"] == date(1990, 1, 1)
        assert orm_kwargs["sex"] == "M"

    def test_serialization(self):
        """Test that the profile serializes correctly."""
        profile = ApiProfile(
            name="John Doe",
            birthday=date(1990, 1, 1),
            sex="M"
        )
        serialized = profile.model_dump()
        
        assert serialized["name"] == "John Doe"
        assert serialized["birthday"] == date(1990, 1, 1)
        assert serialized["sex"] == "M"

    def test_immutability(self):
        """Test that the profile is immutable."""
        profile = ApiProfile(
            name="John Doe",
            birthday=date(1990, 1, 1),
            sex="M"
        )
        with pytest.raises(ValueError):
            profile.name = "Jane Doe"

    def test_orm_model_with_none_values(self):
        """Test ORM conversion with None values."""
        orm_profile = ProfileSaModel(
            name="John Doe",
            birthday=None,
            sex="M"
        )
        api_profile = ApiProfile.from_orm_model(orm_profile)
        
        assert api_profile.name == "John Doe"
        assert api_profile.birthday is None
        assert api_profile.sex == "M"

    def test_orm_kwargs_with_none_values(self):
        """Test ORM kwargs conversion with None values."""
        api_profile = ApiProfile(
            name="John Doe",
            birthday=None, # type: ignore
            sex="M"
        )
        orm_kwargs = api_profile.to_orm_kwargs()
        
        assert orm_kwargs["name"] == "John Doe"
        assert orm_kwargs["birthday"] is None
        assert orm_kwargs["sex"] == "M" 