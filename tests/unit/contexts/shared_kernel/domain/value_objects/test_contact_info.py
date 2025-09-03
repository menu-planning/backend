"""Unit tests for ContactInfo value object.

Tests contact info validation, equality semantics, and value object contracts.
Follows testing principles: no I/O, fakes only, behavior-focused assertions.
"""
import pytest
import attrs

from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo


class TestContactInfoValidation:
    """Test contact info validation and format constraints."""

    def test_contact_info_validation_minimal_valid_contact(self):
        """Validates minimal valid contact info creation."""
        # Given: minimal required contact components
        # When: create contact info with valid components
        # Then: contact info is created successfully
        contact = ContactInfo(
            main_phone="+5511999999999",
            main_email="user@example.com",
            all_phones=frozenset(["+5511999999999"]),
            all_emails=frozenset(["user@example.com"])
        )
        assert contact.main_phone == "+5511999999999"
        assert contact.main_email == "user@example.com"
        assert contact.all_phones == frozenset(["+5511999999999"])
        assert contact.all_emails == frozenset(["user@example.com"])

    def test_contact_info_validation_all_fields_none(self):
        """Validates contact info with all fields as None."""
        # Given: no contact information
        # When: create contact info with all None values
        # Then: contact info is created with all None fields
        contact = ContactInfo(
            main_phone=None,
            main_email=None,
            all_phones=frozenset(),
            all_emails=frozenset()
        )
        assert contact.main_phone is None
        assert contact.main_email is None
        assert contact.all_phones == frozenset()
        assert contact.all_emails == frozenset()

    def test_contact_info_validation_multiple_phones_and_emails(self):
        """Validates contact info with multiple phones and emails."""
        # Given: multiple contact methods
        # When: create contact info with multiple phones and emails
        # Then: all contact methods are properly stored
        phones = frozenset(["+5511999999999", "+5511888888888", "+5511777777777"])
        emails = frozenset(["user@example.com", "backup@example.com", "work@company.com"])
        
        contact = ContactInfo(
            main_phone="+5511999999999",
            main_email="user@example.com",
            all_phones=phones,
            all_emails=emails
        )
        assert contact.main_phone == "+5511999999999"
        assert contact.main_email == "user@example.com"
        assert contact.all_phones == phones
        assert contact.all_emails == emails

    def test_contact_info_validation_string_fields_accept_any_string(self):
        """Validates string fields accept any string value including empty."""
        # Given: various string values including empty strings
        # When: create contact info with different string values
        # Then: all string values are accepted
        contact = ContactInfo(
            main_phone="",
            main_email="",
            all_phones=frozenset([""]),
            all_emails=frozenset([""])
        )
        assert contact.main_phone == ""
        assert contact.main_email == ""
        assert contact.all_phones == frozenset([""])
        assert contact.all_emails == frozenset([""])

    def test_contact_info_validation_phone_formats(self):
        """Validates various phone number formats are accepted."""
        # Given: different phone number formats
        # When: create contact info with various phone formats
        # Then: all formats are accepted
        phone_formats = [
            "+5511999999999",
            "11999999999",
            "(11) 99999-9999",
            "11 99999-9999",
            "+1-555-123-4567",
            "555.123.4567"
        ]
        
        for phone in phone_formats:
            contact = ContactInfo(
                main_phone=phone,
                main_email="user@example.com",
                all_phones=frozenset([phone]),
                all_emails=frozenset(["user@example.com"])
            )
            assert contact.main_phone == phone
            assert phone in contact.all_phones

    def test_contact_info_validation_email_formats(self):
        """Validates various email formats are accepted."""
        # Given: different email formats
        # When: create contact info with various email formats
        # Then: all formats are accepted
        email_formats = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "user123@subdomain.example.com",
            "test@localhost",
            "user@example-domain.com"
        ]
        
        for email in email_formats:
            contact = ContactInfo(
                main_phone="+5511999999999",
                main_email=email,
                all_phones=frozenset(["+5511999999999"]),
                all_emails=frozenset([email])
            )
            assert contact.main_email == email
            assert email in contact.all_emails

    def test_contact_info_validation_frozenset_immutability(self):
        """Validates that frozenset fields are immutable."""
        # Given: contact info with frozenset fields
        # When: attempt to modify the frozensets
        # Then: modification raises AttributeError
        phones = frozenset(["+5511999999999"])
        emails = frozenset(["user@example.com"])
        
        contact = ContactInfo(
            main_phone="+5511999999999",
            main_email="user@example.com",
            all_phones=phones,
            all_emails=emails
        )
        
        # Verify frozenset immutability
        with pytest.raises(AttributeError):
            contact.all_phones.add("+5511888888888")  # type: ignore[attr-defined]
        
        with pytest.raises(AttributeError):
            contact.all_emails.add("backup@example.com")  # type: ignore[attr-defined]


class TestContactInfoEquality:
    """Test contact info equality semantics and value object contracts."""

    def test_contact_info_equality_identical_contacts(self):
        """Ensures identical contact infos are equal."""
        # Given: two contact infos with identical values
        # When: compare the contact infos
        # Then: they are equal
        contact1 = ContactInfo(
            main_phone="+5511999999999",
            main_email="user@example.com",
            all_phones=frozenset(["+5511999999999"]),
            all_emails=frozenset(["user@example.com"])
        )
        contact2 = ContactInfo(
            main_phone="+5511999999999",
            main_email="user@example.com",
            all_phones=frozenset(["+5511999999999"]),
            all_emails=frozenset(["user@example.com"])
        )
        assert contact1 == contact2
        assert hash(contact1) == hash(contact2)

    def test_contact_info_equality_different_contacts(self):
        """Ensures different contact infos are not equal."""
        # Given: two contact infos with different values
        # When: compare the contact infos
        # Then: they are not equal
        contact1 = ContactInfo(
            main_phone="+5511999999999",
            main_email="user@example.com",
            all_phones=frozenset(["+5511999999999"]),
            all_emails=frozenset(["user@example.com"])
        )
        contact2 = ContactInfo(
            main_phone="+5511888888888",
            main_email="user@example.com",
            all_phones=frozenset(["+5511888888888"]),
            all_emails=frozenset(["user@example.com"])
        )
        assert contact1 != contact2
        assert hash(contact1) != hash(contact2)

    def test_contact_info_equality_different_phone_order(self):
        """Ensures contact infos with same phones in different order are equal."""
        # Given: two contact infos with same phones in different order
        # When: compare the contact infos
        # Then: they are equal (frozenset order doesn't matter)
        contact1 = ContactInfo(
            main_phone="+5511999999999",
            main_email="user@example.com",
            all_phones=frozenset(["+5511999999999", "+5511888888888"]),
            all_emails=frozenset(["user@example.com"])
        )
        contact2 = ContactInfo(
            main_phone="+5511999999999",
            main_email="user@example.com",
            all_phones=frozenset(["+5511888888888", "+5511999999999"]),
            all_emails=frozenset(["user@example.com"])
        )
        assert contact1 == contact2
        assert hash(contact1) == hash(contact2)

    def test_contact_info_equality_different_email_order(self):
        """Ensures contact infos with same emails in different order are equal."""
        # Given: two contact infos with same emails in different order
        # When: compare the contact infos
        # Then: they are equal (frozenset order doesn't matter)
        contact1 = ContactInfo(
            main_phone="+5511999999999",
            main_email="user@example.com",
            all_phones=frozenset(["+5511999999999"]),
            all_emails=frozenset(["user@example.com", "backup@example.com"])
        )
        contact2 = ContactInfo(
            main_phone="+5511999999999",
            main_email="user@example.com",
            all_phones=frozenset(["+5511999999999"]),
            all_emails=frozenset(["backup@example.com", "user@example.com"])
        )
        assert contact1 == contact2
        assert hash(contact1) == hash(contact2)

    def test_contact_info_equality_none_vs_empty_string(self):
        """Ensures None and empty string are treated as different values."""
        # Given: two contact infos with None vs empty string
        # When: compare the contact infos
        # Then: they are not equal
        contact_with_none = ContactInfo(
            main_phone=None,
            main_email=None,
            all_phones=frozenset(),
            all_emails=frozenset()
        )
        contact_with_empty = ContactInfo(
            main_phone="",
            main_email="",
            all_phones=frozenset([""]),
            all_emails=frozenset([""])
        )
        
        assert contact_with_none != contact_with_empty
        assert hash(contact_with_none) != hash(contact_with_empty)

    def test_contact_info_equality_immutability(self):
        """Ensures contact info objects are immutable."""
        # Given: a contact info instance
        # When: attempt to modify attributes
        # Then: modification raises FrozenInstanceError
        contact = ContactInfo(
            main_phone="+5511999999999",
            main_email="user@example.com",
            all_phones=frozenset(["+5511999999999"]),
            all_emails=frozenset(["user@example.com"])
        )
        
        # Verify immutability by attempting to modify attributes
        # The frozen decorator from attrs prevents attribute assignment
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            contact.main_phone = "+5511888888888"  # type: ignore[attr-defined]
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            contact.main_email = "backup@example.com"  # type: ignore[attr-defined]

    def test_contact_info_equality_replace_creates_new_instance(self):
        """Ensures replace method creates new instance without modifying original."""
        # Given: an original contact info
        # When: create new contact info using replace
        # Then: original remains unchanged and new instance is created
        original = ContactInfo(
            main_phone="+5511999999999",
            main_email="user@example.com",
            all_phones=frozenset(["+5511999999999"]),
            all_emails=frozenset(["user@example.com"])
        )
        new_contact = original.replace(main_phone="+5511888888888")
        
        # Original unchanged
        assert original.main_phone == "+5511999999999"
        assert original.main_email == "user@example.com"
        assert original.all_phones == frozenset(["+5511999999999"])
        assert original.all_emails == frozenset(["user@example.com"])
        
        # New instance has updated values
        assert new_contact.main_phone == "+5511888888888"
        assert new_contact.main_email == "user@example.com"  # Unchanged
        assert new_contact.all_phones == frozenset(["+5511999999999"])  # Unchanged
        assert new_contact.all_emails == frozenset(["user@example.com"])  # Unchanged
        
        # They are different instances
        assert original is not new_contact
        assert original != new_contact

    def test_contact_info_equality_hash_consistency(self):
        """Ensures hash values are consistent across multiple calls."""
        # Given: a contact info instance
        # When: call hash multiple times
        # Then: hash value is consistent
        contact = ContactInfo(
            main_phone="+5511999999999",
            main_email="user@example.com",
            all_phones=frozenset(["+5511999999999"]),
            all_emails=frozenset(["user@example.com"])
        )
        
        hash1 = hash(contact)
        hash2 = hash(contact)
        hash3 = hash(contact)
        
        assert hash1 == hash2 == hash3

    def test_contact_info_equality_different_frozenset_contents(self):
        """Ensures contact infos with different frozenset contents are not equal."""
        # Given: two contact infos with different frozenset contents
        # When: compare the contact infos
        # Then: they are not equal
        contact1 = ContactInfo(
            main_phone="+5511999999999",
            main_email="user@example.com",
            all_phones=frozenset(["+5511999999999"]),
            all_emails=frozenset(["user@example.com"])
        )
        contact2 = ContactInfo(
            main_phone="+5511999999999",
            main_email="user@example.com",
            all_phones=frozenset(["+5511999999999", "+5511888888888"]),
            all_emails=frozenset(["user@example.com"])
        )
        assert contact1 != contact2
        assert hash(contact1) != hash(contact2)
