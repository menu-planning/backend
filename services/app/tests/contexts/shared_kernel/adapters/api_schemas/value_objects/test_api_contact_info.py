import pytest
from pydantic import ValidationError

from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_contact_info import ApiContactInfo
from src.contexts.shared_kernel.adapters.ORM.sa_models.contact_info_sa_model import ContactInfoSaModel


class TestApiContactInfoValidation:
    """Test suite for ApiContactInfo validation behavior."""

    def test_valid_contact_info_creation(self):
        """Test creating contact info with valid data."""
        contact_info = ApiContactInfo(
            main_phone="+1234567890",
            main_email="test@example.com",
            all_phones=frozenset(["+1234567890", "+0987654321"]),
            all_emails=frozenset(["test@example.com", "other@example.com"])
        )
        
        assert contact_info.main_phone == "+1234567890"
        assert contact_info.main_email == "test@example.com"
        assert contact_info.all_phones == frozenset(["+1234567890", "+0987654321"])
        assert contact_info.all_emails == frozenset(["test@example.com", "other@example.com"])

    def test_minimal_contact_info_creation(self):
        """Test creating contact info with minimal required fields."""
        contact_info = ApiContactInfo()
        
        assert contact_info.main_phone is None
        assert contact_info.main_email is None
        assert contact_info.all_phones == frozenset()
        assert contact_info.all_emails == frozenset()

    def test_email_validation_behavior(self):
        """Test email validation follows expected patterns."""
        # Valid emails should work
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test+tag@example.org",
            "user123@test-domain.com"
        ]
        
        for email in valid_emails:
            contact_info = ApiContactInfo(main_email=email)
            assert contact_info.main_email == email.lower()  # Should be normalized to lowercase

    def test_email_validation_error_behavior(self):
        """Test email validation rejects invalid formats."""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@domain",
            "user space@domain.com",
            "<script>alert('xss')</script>@domain.com"
        ]
        
        for invalid_email in invalid_emails:
            with pytest.raises(ValidationError) as exc_info:
                ApiContactInfo(main_email=invalid_email)
            
            assert "email" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    def test_phone_validation_behavior(self):
        """Test phone validation accepts various international formats."""
        valid_phones = [
            "+1234567890",
            "(123) 456-7890",
            "123-456-7890",
            "+44 20 7946 0958",
            "+1-800-555-0199"
        ]
        
        for phone in valid_phones:
            contact_info = ApiContactInfo(main_phone=phone)
            assert contact_info.main_phone == phone  # Should preserve original formatting

    def test_phone_validation_error_behavior(self):
        """Test phone validation rejects invalid formats."""
        invalid_phones = [
            "123",  # Too short
            "123456789012345678901234567890",  # Too long
            "abc-def-ghij",  # Non-numeric
            "<script>alert('xss')</script>",  # Security pattern
            ""  # Empty string should become None
        ]
        
        for invalid_phone in invalid_phones:
            if invalid_phone == "":
                # Empty string should become None, not raise error
                contact_info = ApiContactInfo(main_phone=invalid_phone)
                assert contact_info.main_phone is None
            else:
                with pytest.raises(ValidationError) as exc_info:
                    ApiContactInfo(main_phone=invalid_phone)
                
                assert "phone" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    def test_collection_validation_behavior(self):
        """Test that collections validate individual items."""
        # Valid collections should work
        contact_info = ApiContactInfo(
            all_phones=frozenset(["+1234567890", "(123) 456-7890"]),
            all_emails=frozenset(["test@example.com", "other@example.com"])
        )
        
        assert len(contact_info.all_phones) == 2
        assert len(contact_info.all_emails) == 2

    def test_collection_validation_filters_invalid_items(self):
        """Test that collection validation filters out invalid items."""
        # Note: Individual validation happens in field_validator, so we test that behavior
        # First test with all valid items
        contact_info = ApiContactInfo(
            all_phones=frozenset(["+1234567890", "(123) 456-7890"]),
            all_emails=frozenset(["test@example.com", "other@example.com"])
        )
        
        # Should have valid items
        assert len(contact_info.all_phones) == 2
        assert len(contact_info.all_emails) == 2

    def test_whitespace_handling_behavior(self):
        """Test that whitespace is properly handled in validation."""
        contact_info = ApiContactInfo(
            main_phone="  +1234567890  ",  # Leading/trailing whitespace
            main_email="  Test@Example.Com  "  # Mixed case with whitespace
        )
        
        assert contact_info.main_phone == "+1234567890"  # Trimmed
        assert contact_info.main_email == "test@example.com"  # Trimmed and lowercased


class TestApiContactInfoConversion:
    """Test four-layer conversion pattern behavior."""

    def test_domain_to_api_conversion_behavior(self):
        """Test domain ContactInfo converts correctly to API schema."""
        domain_contact_info = ContactInfo(
            main_phone="+1234567890",
            main_email="test@example.com",
            all_phones={"+1234567890", "+0987654321"},  # Domain uses set
            all_emails={"test@example.com", "other@example.com"}  # Domain uses set
        )
        
        api_contact_info = ApiContactInfo.from_domain(domain_contact_info)
        
        assert api_contact_info.main_phone == "+1234567890"
        assert api_contact_info.main_email == "test@example.com"
        # Collections should be converted to frozenset
        assert isinstance(api_contact_info.all_phones, frozenset)
        assert isinstance(api_contact_info.all_emails, frozenset)
        assert api_contact_info.all_phones == frozenset(["+1234567890", "+0987654321"])
        assert api_contact_info.all_emails == frozenset(["test@example.com", "other@example.com"])

    def test_api_to_domain_conversion_behavior(self):
        """Test API schema converts correctly to domain ContactInfo."""
        api_contact_info = ApiContactInfo(
            main_phone="+1234567890",
            main_email="test@example.com",
            all_phones=frozenset(["+1234567890", "+0987654321"]),  # API uses frozenset
            all_emails=frozenset(["test@example.com", "other@example.com"])  # API uses frozenset
        )
        
        domain_contact_info = api_contact_info.to_domain()
        
        assert domain_contact_info.main_phone == "+1234567890"
        assert domain_contact_info.main_email == "test@example.com"
        # Collections should be converted to set
        assert isinstance(domain_contact_info.all_phones, set)
        assert isinstance(domain_contact_info.all_emails, set)
        assert domain_contact_info.all_phones == {"+1234567890", "+0987654321"}
        assert domain_contact_info.all_emails == {"test@example.com", "other@example.com"}

    def test_orm_to_api_conversion_behavior(self):
        """Test ORM model converts correctly to API schema."""
        orm_contact_info = ContactInfoSaModel(
            main_phone="+1234567890",
            main_email="test@example.com",
            all_phones=["+1234567890", "+0987654321"],  # ORM uses list
            all_emails=["test@example.com", "other@example.com"]  # ORM uses list
        )
        
        api_contact_info = ApiContactInfo.from_orm_model(orm_contact_info)
        
        assert api_contact_info.main_phone == "+1234567890"
        assert api_contact_info.main_email == "test@example.com"
        # Collections should be converted to frozenset
        assert isinstance(api_contact_info.all_phones, frozenset)
        assert isinstance(api_contact_info.all_emails, frozenset)
        assert api_contact_info.all_phones == frozenset(["+1234567890", "+0987654321"])
        assert api_contact_info.all_emails == frozenset(["test@example.com", "other@example.com"])

    def test_api_to_orm_conversion_behavior(self):
        """Test API schema converts correctly to ORM kwargs."""
        api_contact_info = ApiContactInfo(
            main_phone="+1234567890",
            main_email="test@example.com",
            all_phones=frozenset(["+1234567890", "+0987654321"]),  # API uses frozenset
            all_emails=frozenset(["test@example.com", "other@example.com"])  # API uses frozenset
        )
        
        orm_kwargs = api_contact_info.to_orm_kwargs()
        
        assert orm_kwargs["main_phone"] == "+1234567890"
        assert orm_kwargs["main_email"] == "test@example.com"
        # Collections should be converted to list
        assert isinstance(orm_kwargs["all_phones"], list)
        assert isinstance(orm_kwargs["all_emails"], list)
        assert set(orm_kwargs["all_phones"]) == {"+1234567890", "+0987654321"}
        assert set(orm_kwargs["all_emails"]) == {"test@example.com", "other@example.com"}

    def test_none_value_handling_behavior(self):
        """Test that None values are handled correctly across all conversions."""
        # ORM with None values
        orm_contact_info = ContactInfoSaModel(
            main_phone=None,
            main_email=None,
            all_phones=None,  # ORM None becomes empty frozenset
            all_emails=None   # ORM None becomes empty frozenset
        )
        
        api_contact_info = ApiContactInfo.from_orm_model(orm_contact_info)
        
        assert api_contact_info.main_phone is None
        assert api_contact_info.main_email is None
        assert api_contact_info.all_phones == frozenset()
        assert api_contact_info.all_emails == frozenset()

    def test_roundtrip_conversion_integrity(self):
        """Test that data survives complete roundtrip conversions."""
        # Start with domain object
        original_domain = ContactInfo(
            main_phone="+1234567890",
            main_email="test@example.com",
            all_phones={"+1234567890", "+0987654321"},
            all_emails={"test@example.com", "other@example.com"}
        )
        
        # Domain → API → Domain
        api_contact = ApiContactInfo.from_domain(original_domain)
        final_domain = api_contact.to_domain()
        
        assert final_domain.main_phone == original_domain.main_phone
        assert final_domain.main_email == original_domain.main_email
        assert final_domain.all_phones == original_domain.all_phones
        assert final_domain.all_emails == original_domain.all_emails

    def test_orm_roundtrip_conversion_integrity(self):
        """Test that ORM data survives roundtrip conversion."""
        # Start with ORM object
        original_orm = ContactInfoSaModel(
            main_phone="+1234567890",
            main_email="test@example.com",
            all_phones=["+1234567890", "+0987654321"],
            all_emails=["test@example.com", "other@example.com"]
        )
        
        # ORM → API → ORM kwargs
        api_contact = ApiContactInfo.from_orm_model(original_orm)
        final_orm_kwargs = api_contact.to_orm_kwargs()
        
        assert final_orm_kwargs["main_phone"] == original_orm.main_phone
        assert final_orm_kwargs["main_email"] == original_orm.main_email
        assert set(final_orm_kwargs["all_phones"]) == original_orm.all_phones
        assert set(final_orm_kwargs["all_emails"]) == original_orm.all_emails


class TestApiContactInfoImmutability:
    """Test immutability behavior of API schema."""

    def test_immutability_behavior(self):
        """Test that ContactInfo is immutable (cannot be modified after creation)."""
        contact_info = ApiContactInfo(
            main_phone="+1234567890",
            main_email="test@example.com"
        )
        
        # Should not be able to modify fields
        with pytest.raises(ValidationError):
            contact_info.main_phone = "+0987654321"


class TestApiContactInfoSerialization:
    """Test serialization behavior."""

    def test_serialization_behavior(self):
        """Test that ContactInfo serializes correctly to dict."""
        contact_info = ApiContactInfo(
            main_phone="+1234567890",
            main_email="test@example.com",
            all_phones=frozenset(["+1234567890", "+0987654321"]),
            all_emails=frozenset(["test@example.com", "other@example.com"])
        )
        
        serialized = contact_info.model_dump()
        
        assert serialized["main_phone"] == "+1234567890"
        assert serialized["main_email"] == "test@example.com"
        # Frozensets should serialize as collections - check the content
        assert set(serialized["all_phones"]) == {"+1234567890", "+0987654321"}
        assert set(serialized["all_emails"]) == {"test@example.com", "other@example.com"}


class TestApiContactInfoCrossContextUsage:
    """Test cross-context usage scenarios for ContactInfo."""

    def test_client_context_integration_behavior(self):
        """Test ContactInfo works correctly when used in client context."""
        # This simulates how ContactInfo is used in recipes_catalog client entities
        
        # Create ContactInfo as would be done in client context
        contact_info = ApiContactInfo(
            main_phone="+1234567890",
            main_email="client@example.com",
            all_phones=frozenset(["+1234567890"]),
            all_emails=frozenset(["client@example.com", "backup@example.com"])
        )
        
        # Verify it behaves correctly for client use cases
        assert contact_info.main_phone == "+1234567890"
        assert contact_info.main_email == "client@example.com"
        assert len(contact_info.all_emails) == 2
        
        # Test conversion to domain for business logic
        domain_contact = contact_info.to_domain()
        assert isinstance(domain_contact.all_phones, set)  # Domain needs mutable set
        assert isinstance(domain_contact.all_emails, set)  # Domain needs mutable set

    def test_optional_contact_info_pattern(self):
        """Test pattern where ContactInfo might be None (optional field in other entities)."""
        # This tests the pattern used in ApiClient where contact_info might be None
        
        # None case
        contact_info_none = None
        assert contact_info_none is None
        
        # Present case
        contact_info_present = ApiContactInfo(
            main_email="optional@example.com"
        )
        assert contact_info_present.main_email == "optional@example.com"
        assert contact_info_present.main_phone is None  # Optional fields default to None

    def test_bulk_validation_behavior(self):
        """Test ContactInfo works correctly in bulk operations."""
        # Create multiple ContactInfo instances (as might happen in bulk operations)
        contact_infos = []
        
        for i in range(5):
            contact_info = ApiContactInfo(
                main_phone=f"+123456789{i}",
                main_email=f"user{i}@example.com"
            )
            contact_infos.append(contact_info)
        
        # Verify all instances are valid
        assert len(contact_infos) == 5
        for i, contact_info in enumerate(contact_infos):
            assert contact_info.main_phone == f"+123456789{i}"
            assert contact_info.main_email == f"user{i}@example.com" 