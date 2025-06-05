import pytest
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.contact_info import ApiContactInfo
from src.contexts.shared_kernel.adapters.ORM.sa_models.contact_info import ContactInfoSaModel


class TestApiContactInfo:
    """Test suite for ApiContactInfo schema."""

    def test_create_valid_contact_info(self):
        """Test creating a valid contact info."""
        contact_info = ApiContactInfo(
            main_phone="+1234567890",
            main_email="test@example.com",
            all_phones={"+1234567890", "+0987654321"},
            all_emails={"test@example.com", "other@example.com"}
        )
        assert contact_info.main_phone == "+1234567890"
        assert contact_info.main_email == "test@example.com"
        assert contact_info.all_phones == {"+1234567890", "+0987654321"}
        assert contact_info.all_emails == {"test@example.com", "other@example.com"}

    def test_create_minimal_contact_info(self):
        """Test creating a contact info with minimal fields."""
        contact_info = ApiContactInfo(
            main_phone="+1234567890",
            main_email="test@example.com"
        )
        assert contact_info.main_phone == "+1234567890"
        assert contact_info.main_email == "test@example.com"
        assert contact_info.all_phones == set()
        assert contact_info.all_emails == set()

    def test_from_domain(self):
        """Test converting from domain object."""
        domain_contact_info = ContactInfo(
            main_phone="+1234567890",
            main_email="test@example.com",
            all_phones={"+1234567890", "+0987654321"},
            all_emails={"test@example.com", "other@example.com"}
        )
        api_contact_info = ApiContactInfo.from_domain(domain_contact_info)
        
        assert api_contact_info.main_phone == "+1234567890"
        assert api_contact_info.main_email == "test@example.com"
        assert api_contact_info.all_phones == {"+1234567890", "+0987654321"}
        assert api_contact_info.all_emails == {"test@example.com", "other@example.com"}

    def test_to_domain(self):
        """Test converting to domain object."""
        api_contact_info = ApiContactInfo(
            main_phone="+1234567890",
            main_email="test@example.com",
            all_phones={"+1234567890", "+0987654321"},
            all_emails={"test@example.com", "other@example.com"}
        )
        domain_contact_info = api_contact_info.to_domain()
        
        assert domain_contact_info.main_phone == "+1234567890"
        assert domain_contact_info.main_email == "test@example.com"
        assert domain_contact_info.all_phones == {"+1234567890", "+0987654321"}
        assert domain_contact_info.all_emails == {"test@example.com", "other@example.com"}

    def test_from_orm_model(self):
        """Test converting from ORM model."""
        orm_contact_info = ContactInfoSaModel(
            main_phone="+1234567890",
            main_email="test@example.com",
            all_phones=["+1234567890", "+0987654321"],
            all_emails=["test@example.com", "other@example.com"]
        )
        api_contact_info = ApiContactInfo.from_orm_model(orm_contact_info)
        
        assert api_contact_info.main_phone == "+1234567890"
        assert api_contact_info.main_email == "test@example.com"
        assert api_contact_info.all_phones == {"+1234567890", "+0987654321"}
        assert api_contact_info.all_emails == {"test@example.com", "other@example.com"}

    def test_to_orm_kwargs(self):
        """Test converting to ORM model kwargs."""
        api_contact_info = ApiContactInfo(
            main_phone="+1234567890",
            main_email="test@example.com",
            all_phones={"+1234567890", "+0987654321"},
            all_emails={"test@example.com", "other@example.com"}
        )
        orm_kwargs = api_contact_info.to_orm_kwargs()
        
        assert orm_kwargs["main_phone"] == "+1234567890"
        assert orm_kwargs["main_email"] == "test@example.com"
        assert set(orm_kwargs["all_phones"]) == {"+1234567890", "+0987654321"}
        assert set(orm_kwargs["all_emails"]) == {"test@example.com", "other@example.com"}

    def test_serialization(self):
        """Test that the contact info serializes correctly."""
        contact_info = ApiContactInfo(
            main_phone="+1234567890",
            main_email="test@example.com",
            all_phones={"+1234567890", "+0987654321"},
            all_emails={"test@example.com", "other@example.com"}
        )
        serialized = contact_info.model_dump()
        
        assert serialized["main_phone"] == "+1234567890"
        assert serialized["main_email"] == "test@example.com"
        assert set(serialized["all_phones"]) == {"+1234567890", "+0987654321"}
        assert set(serialized["all_emails"]) == {"test@example.com", "other@example.com"}

    def test_immutability(self):
        """Test that the contact info is immutable."""
        contact_info = ApiContactInfo(
            main_phone="+1234567890",
            main_email="test@example.com"
        )
        with pytest.raises(ValueError):
            contact_info.main_phone = "+0987654321"

    def test_orm_model_with_none_values(self):
        """Test ORM conversion with None values."""
        orm_contact_info = ContactInfoSaModel(
            main_phone=None,
            main_email=None,
            all_phones=None,
            all_emails=None
        )
        api_contact_info = ApiContactInfo.from_orm_model(orm_contact_info)
        
        assert api_contact_info.main_phone is None
        assert api_contact_info.main_email is None
        assert api_contact_info.all_phones == set()
        assert api_contact_info.all_emails == set()

    def test_orm_kwargs_with_none_values(self):
        """Test ORM kwargs conversion with None values."""
        api_contact_info = ApiContactInfo(
            main_phone=None,
            main_email=None,
            all_phones=set(),
            all_emails=set()
        )
        orm_kwargs = api_contact_info.to_orm_kwargs()
        
        assert orm_kwargs["main_phone"] is None
        assert orm_kwargs["main_email"] is None
        assert orm_kwargs["all_phones"] == []
        assert orm_kwargs["all_emails"] == [] 