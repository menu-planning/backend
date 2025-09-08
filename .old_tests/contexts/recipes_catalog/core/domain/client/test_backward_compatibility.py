"""
Backward Compatibility Tests for Client Domain
==============================================

Ensures existing Client creation patterns remain unchanged after onboarding_data integration.
Validates that all existing workflows continue to function without breaking changes.
"""

from datetime import date

from src.contexts.recipes_catalog.core.domain.client.root_aggregate.client import Client
from src.contexts.shared_kernel.domain.value_objects.address import Address
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class TestClientBackwardCompatibility:
    """Test that existing Client creation patterns remain unchanged."""

    def test_client_creation_without_onboarding_data_unchanged(self):
        """Existing Client creation should work exactly as before."""
        # Arrange: Create client data using original pattern
        profile = Profile(name="Legacy Client", sex="M", birthday=date(1985, 5, 15))
        contact_info = ContactInfo(
            main_phone="555-0001",
            main_email="legacy@example.com",
            all_phones=frozenset({"555-0001"}),
            all_emails=frozenset({"legacy@example.com"}),
        )
        address = Address(street="123 Legacy St", city="Legacy City", zip_code="12345")

        # Act: Create client using original factory method (no onboarding_data)
        client = Client.create_client(
            author_id="legacy_author",
            profile=profile,
            contact_info=contact_info,
            address=address,
            notes="Legacy test client",
        )

        # Assert: All original functionality should work unchanged
        assert client.author_id == "legacy_author"
        assert client.profile == profile
        assert client.contact_info == contact_info
        assert client.address == address
        assert client.notes == "Legacy test client"
        assert client.menus == []
        assert client.tags == set()
        assert client.onboarding_data is None  # New field defaults to None
        assert not client.discarded
        assert client.version == 1

    def test_client_creation_minimal_parameters_unchanged(self):
        """Minimal Client creation should work with same parameters as before."""
        # Arrange: Create minimal client data
        profile = Profile(name="Minimal Client", sex="F", birthday=date(1990, 10, 20))
        contact_info = ContactInfo(
            main_phone="555-0002",
            main_email="minimal@example.com",
            all_phones=frozenset({"555-0002"}),
            all_emails=frozenset({"minimal@example.com"}),
        )

        # Act: Create client with minimal required data only
        client = Client.create_client(
            author_id="minimal_author", profile=profile, contact_info=contact_info
        )

        # Assert: Optional fields should have proper defaults
        assert client.author_id == "minimal_author"
        assert client.profile == profile
        assert client.contact_info == contact_info
        assert client.address is None
        assert client.notes is None
        assert client.tags == set()
        assert client.onboarding_data is None  # New field defaults to None
        assert client.menus == []
        assert not client.discarded
        assert client.version == 1

    def test_client_direct_constructor_backward_compatibility(self):
        """Direct Client constructor should handle onboarding_data as optional."""
        # Arrange: Create client data
        profile = Profile(name="Direct Client", sex="M", birthday=date(1988, 3, 12))

        # Act: Create client using direct constructor (original pattern)
        client = Client(
            id="direct_client_id", author_id="direct_author", profile=profile
        )

        # Assert: Should work with all optional fields defaulted
        assert client.id == "direct_client_id"
        assert client.author_id == "direct_author"
        assert client.profile == profile
        assert client.contact_info is None
        assert client.address is None
        assert client.notes is None
        assert client.onboarding_data is None  # New field defaults to None
        assert client.tags == set()
        assert client.menus == []
        assert not client.discarded
        assert client.version == 1

    def test_client_property_setters_unchanged(self):
        """Existing property setters should work unchanged."""
        # Arrange: Create client
        profile = Profile(name="Setter Test", sex="F", birthday=date(1992, 7, 8))
        contact_info = ContactInfo(
            main_phone="555-0003",
            main_email="setter@example.com",
            all_phones=frozenset({"555-0003"}),
            all_emails=frozenset({"setter@example.com"}),
        )
        client = Client.create_client(
            author_id="setter_author", profile=profile, contact_info=contact_info
        )
        original_version = client.version

        # Act: Update properties using existing setters
        new_profile = Profile(name="Updated Name", sex="F", birthday=date(1992, 7, 8))
        new_contact = ContactInfo(
            main_phone="555-9999",
            main_email="updated@example.com",
            all_phones=frozenset({"555-9999"}),
            all_emails=frozenset({"updated@example.com"}),
        )
        new_address = Address(street="456 New St", city="New City", zip_code="67890")

        client.profile = new_profile
        client.contact_info = new_contact
        client.address = new_address
        client.notes = "Updated notes"

        # Assert: All setters should work and increment version
        assert client.profile == new_profile
        assert client.contact_info == new_contact
        assert client.address == new_address
        assert client.notes == "Updated notes"
        assert client.onboarding_data is None  # Should remain None
        assert client.version == original_version + 4  # 4 property updates

    def test_client_update_properties_method_unchanged(self):
        """update_properties method should work with original parameters."""
        # Arrange: Create client
        profile = Profile(name="Update Test", sex="M", birthday=date(1987, 11, 25))
        contact_info = ContactInfo(
            main_phone="555-0004",
            main_email="update@example.com",
            all_phones=frozenset({"555-0004"}),
            all_emails=frozenset({"update@example.com"}),
        )
        client = Client.create_client(
            author_id="update_author", profile=profile, contact_info=contact_info
        )
        original_version = client.version

        # Act: Update using update_properties (original method)
        client.update_properties(notes="Updated via update_properties")

        # Assert: Should work and update version
        assert client.notes == "Updated via update_properties"
        assert client.version == original_version + 1


class TestClientOnboardingDataHandling:
    """Test that onboarding_data field handles None values gracefully."""

    def test_onboarding_data_property_defaults_to_none(self):
        """onboarding_data property should default to None."""
        # Arrange & Act: Create client without onboarding_data
        profile = Profile(name="No Onboarding", sex="M", birthday=date(1985, 5, 15))
        contact_info = ContactInfo(
            main_phone="555-0005",
            main_email="none@example.com",
            all_phones=frozenset({"555-0005"}),
            all_emails=frozenset({"none@example.com"}),
        )
        client = Client.create_client(
            author_id="none_author", profile=profile, contact_info=contact_info
        )

        # Assert: onboarding_data should be None
        assert client.onboarding_data is None

    def test_onboarding_data_property_accepts_none(self):
        """onboarding_data property should accept None without error."""
        # Arrange: Create client
        profile = Profile(name="None Test", sex="F", birthday=date(1990, 8, 14))
        contact_info = ContactInfo(
            main_phone="555-0006",
            main_email="nonetest@example.com",
            all_phones=frozenset({"555-0006"}),
            all_emails=frozenset({"nonetest@example.com"}),
        )
        client = Client.create_client(
            author_id="none_test_author", profile=profile, contact_info=contact_info
        )
        original_version = client.version

        # Act: Set onboarding_data to None explicitly
        client.onboarding_data = None

        # Assert: Should accept None and not increment version (no change)
        assert client.onboarding_data is None
        assert client.version == original_version  # No change, same value

    def test_onboarding_data_property_accepts_dict(self):
        """onboarding_data property should accept valid dictionary."""
        # Arrange: Create client
        profile = Profile(name="Dict Test", sex="M", birthday=date(1988, 12, 3))
        contact_info = ContactInfo(
            main_phone="555-0007",
            main_email="dicttest@example.com",
            all_phones=frozenset({"555-0007"}),
            all_emails=frozenset({"dicttest@example.com"}),
        )
        client = Client.create_client(
            author_id="dict_test_author", profile=profile, contact_info=contact_info
        )
        original_version = client.version

        # Act: Set onboarding_data to valid dictionary
        onboarding_data = {"form_id": "test123", "response_id": "resp456"}
        client.onboarding_data = onboarding_data

        # Assert: Should accept dictionary and increment version
        assert client.onboarding_data == onboarding_data
        assert client.version == original_version + 1

    def test_onboarding_data_in_factory_method(self):
        """Factory method should accept onboarding_data parameter."""
        # Arrange: Create client data with onboarding_data
        profile = Profile(name="Factory Test", sex="F", birthday=date(1991, 4, 18))
        contact_info = ContactInfo(
            main_phone="555-0008",
            main_email="factory@example.com",
            all_phones=frozenset({"555-0008"}),
            all_emails=frozenset({"factory@example.com"}),
        )
        onboarding_data = {"form_id": "factory123", "response_id": "factory456"}

        # Act: Create client with onboarding_data
        client = Client.create_client(
            author_id="factory_author",
            profile=profile,
            contact_info=contact_info,
            onboarding_data=onboarding_data,
        )

        # Assert: Should create client with onboarding_data
        assert client.onboarding_data == onboarding_data
        assert client.version == 1

    def test_update_properties_supports_onboarding_data(self):
        """update_properties should support onboarding_data field."""
        # Arrange: Create client
        profile = Profile(name="Update Props Test", sex="M", birthday=date(1986, 9, 22))
        contact_info = ContactInfo(
            main_phone="555-0009",
            main_email="updateprops@example.com",
            all_phones=frozenset({"555-0009"}),
            all_emails=frozenset({"updateprops@example.com"}),
        )
        client = Client.create_client(
            author_id="update_props_author", profile=profile, contact_info=contact_info
        )
        original_version = client.version

        # Act: Update onboarding_data via update_properties
        onboarding_data = {"form_id": "update123", "response_id": "update456"}
        client.update_properties(onboarding_data=onboarding_data)

        # Assert: Should update onboarding_data and increment version
        assert client.onboarding_data == onboarding_data
        assert client.version == original_version + 1


class TestClientLegacyBehaviorPreservation:
    """Test that all legacy Client behaviors are preserved."""

    def test_client_menu_management_unchanged(self):
        """Client menu management should work unchanged."""
        # Arrange: Create client
        profile = Profile(name="Menu Test", sex="F", birthday=date(1989, 6, 30))
        contact_info = ContactInfo(
            main_phone="555-0010",
            main_email="menu@example.com",
            all_phones=frozenset({"555-0010"}),
            all_emails=frozenset({"menu@example.com"}),
        )
        client = Client.create_client(
            author_id="menu_author", profile=profile, contact_info=contact_info
        )

        # Act: Create menu using existing method
        client.create_menu(description="Test Menu", menu_id="menu123")

        # Assert: Menu creation should work unchanged
        assert len(client.menus) == 1
        assert client.menus[0].id == "menu123"
        assert client.menus[0].description == "Test Menu"

    def test_client_tag_management_unchanged(self):
        """Client tag management should work unchanged."""
        # Arrange: Create client and tags
        profile = Profile(name="Tag Test", sex="M", birthday=date(1984, 2, 14))
        contact_info = ContactInfo(
            main_phone="555-0011",
            main_email="tag@example.com",
            all_phones=frozenset({"555-0011"}),
            all_emails=frozenset({"tag@example.com"}),
        )
        client = Client.create_client(
            author_id="tag_author", profile=profile, contact_info=contact_info
        )
        tags = {
            Tag(key="type", value="premium", author_id="tag_author", type="client"),
            Tag(key="region", value="west", author_id="tag_author", type="client"),
        }

        # Act: Set tags using existing method
        client.tags = tags

        # Assert: Tag management should work unchanged
        assert client.tags == tags
        assert len(client.tags) == 2

    def test_client_deletion_unchanged(self):
        """Client deletion should work unchanged."""
        # Arrange: Create client
        profile = Profile(name="Delete Test", sex="F", birthday=date(1993, 1, 7))
        contact_info = ContactInfo(
            main_phone="555-0012",
            main_email="delete@example.com",
            all_phones=frozenset({"555-0012"}),
            all_emails=frozenset({"delete@example.com"}),
        )
        client = Client.create_client(
            author_id="delete_author", profile=profile, contact_info=contact_info
        )

        # Act: Delete client using existing method
        client.delete()

        # Assert: Deletion should work unchanged
        assert client.discarded

    def test_client_string_representation_unchanged(self):
        """Client string representation should work unchanged."""
        # Arrange: Create client
        profile = Profile(name="String Test", sex="M", birthday=date(1987, 10, 19))
        contact_info = ContactInfo(
            main_phone="555-0013",
            main_email="string@example.com",
            all_phones=frozenset({"555-0013"}),
            all_emails=frozenset({"string@example.com"}),
        )
        client = Client.create_client(
            author_id="string_author", profile=profile, contact_info=contact_info
        )

        # Act & Assert: String representation should work unchanged
        expected_repr = f"Client(client_id={client.id}, client_name=String Test)"
        assert str(client) == expected_repr
        assert repr(client) == expected_repr

    def test_client_equality_unchanged(self):
        """Client equality comparison should work unchanged."""
        # Arrange: Create two clients with same ID
        profile = Profile(name="Equality Test", sex="F", birthday=date(1990, 5, 26))
        contact_info = ContactInfo(
            main_phone="555-0014",
            main_email="equality@example.com",
            all_phones=frozenset({"555-0014"}),
            all_emails=frozenset({"equality@example.com"}),
        )

        client1 = Client(
            id="same_id",
            author_id="equality_author",
            profile=profile,
            contact_info=contact_info,
        )
        client2 = Client(
            id="same_id",
            author_id="equality_author",
            profile=profile,
            contact_info=contact_info,
        )

        # Act & Assert: Equality should work unchanged
        assert client1 == client2
        assert hash(client1) == hash(client2)
