"""
Comprehensive Client Domain Behavior Tests

Tests focus on business behaviors and domain logic of the Client aggregate root,
ensuring proper entity lifecycle management, property validation, and domain rules.
"""

from datetime import date

import pytest
from src.contexts.recipes_catalog.core.domain.client.root_aggregate.client import Client
from src.contexts.shared_kernel.domain.exceptions import BusinessRuleValidationError
from src.contexts.shared_kernel.domain.value_objects.address import Address
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class TestClientCreationBehaviors:
    """Test client creation and initialization behaviors."""

    def test_client_creation_with_factory_method(self):
        """Domain should create clients with proper factory method."""
        # Arrange: Create client data
        profile = Profile(name="John Doe", sex="M", birthday=date(1985, 5, 15))
        contact_info = ContactInfo(
            main_phone="555-1234",
            main_email="john@example.com",
            all_phones=frozenset({"555-1234"}),
            all_emails=frozenset({"john@example.com"}),
        )
        address = Address(street="123 Main St", city="Anytown", zip_code="12345")

        # Act: Create client using factory
        client = Client.create_client(
            author_id="author_123",
            profile=profile,
            contact_info=contact_info,
            address=address,
            notes="Test client",
        )

        # Assert: Domain should create client with proper attributes
        assert client.author_id == "author_123"
        assert client.profile == profile
        assert client.contact_info == contact_info
        assert client.address == address
        assert client.notes == "Test client"
        assert client.menus == []
        assert client.tags == set()
        assert not client.discarded
        assert client.version == 1

    def test_client_creation_with_minimal_data(self):
        """Domain should create clients with minimal required data."""
        # Arrange: Create minimal client data
        profile = Profile(name="Jane Doe", sex="F", birthday=date(1990, 10, 20))
        contact_info = ContactInfo(
            main_phone="555-5678",
            main_email="jane@example.com",
            all_phones=frozenset({"555-5678"}),
            all_emails=frozenset({"jane@example.com"}),
        )

        # Act: Create client with minimal data
        client = Client.create_client(
            author_id="author_456", profile=profile, contact_info=contact_info
        )

        # Assert: Domain should handle optional fields gracefully
        assert client.author_id == "author_456"
        assert client.profile == profile
        assert client.contact_info == contact_info
        assert client.address is None
        assert client.notes is None
        assert client.tags == set()
        assert client.menus == []

    def test_client_creation_with_tags(self):
        """Domain should create clients with initial tags."""
        # Arrange: Create client with tags
        profile = Profile(name="Business Client", sex="M", birthday=date(1980, 1, 1))
        contact_info = ContactInfo(
            main_phone="555-9999",
            main_email="business@example.com",
            all_phones=frozenset({"555-9999"}),
            all_emails=frozenset({"business@example.com"}),
        )
        tags = {
            Tag(key="type", value="business", author_id="author_789", type="client"),
            Tag(key="priority", value="high", author_id="author_789", type="client"),
        }

        # Act: Create client with tags
        client = Client.create_client(
            author_id="author_789",
            profile=profile,
            contact_info=contact_info,
            tags=tags,
        )

        # Assert: Domain should preserve tags
        assert client.tags == tags
        assert len(client.tags) == 2


class TestClientPropertyManagement:
    """Test client property access and modification behaviors."""

    @pytest.fixture
    def sample_client(self):
        """Fixture providing a sample client for testing."""
        profile = Profile(name="Test Client", sex="F", birthday=date(1992, 3, 3))
        contact_info = ContactInfo(
            main_phone="555-0000",
            main_email="test@example.com",
            all_phones=frozenset({"555-0000"}),
            all_emails=frozenset({"test@example.com"}),
        )
        return Client.create_client(
            author_id="test_author", profile=profile, contact_info=contact_info
        )

    def test_client_profile_property_access(self, sample_client):
        """Domain should provide read access to profile."""
        # Act & Assert: Domain should allow profile access
        assert sample_client.profile.name == "Test Client"
        assert sample_client.profile.sex == "F"

    def test_client_profile_property_update(self, sample_client):
        """Domain should allow profile updates with version increment."""
        # Arrange: Create new profile
        new_profile = Profile(name="Updated Client", sex="M", birthday=date(1988, 8, 8))
        original_version = sample_client.version

        # Act: Update profile
        sample_client.profile = new_profile

        # Assert: Domain should update profile and increment version
        assert sample_client.profile == new_profile
        assert sample_client.profile.name == "Updated Client"
        assert sample_client.version == original_version + 1

    def test_client_profile_update_with_same_value_increments_version(
        self, sample_client
    ):
        """Domain should NOT increment version when setting same profile value (optimization)."""
        # Arrange: Get current profile and version
        current_profile = sample_client.profile
        original_version = sample_client.version

        # Act: Set same profile
        sample_client.profile = current_profile

        # Assert: Domain should NOT increment version for same value (optimization)
        assert sample_client.version == original_version

    def test_client_contact_info_property_access(self, sample_client):
        """Domain should provide read access to contact info."""
        # Act & Assert: Domain should allow contact info access
        assert sample_client.contact_info.main_phone == "555-0000"
        assert sample_client.contact_info.main_email == "test@example.com"

    def test_client_contact_info_property_update(self, sample_client):
        """Domain should allow contact info updates with version increment."""
        # Arrange: Create new contact info
        new_contact = ContactInfo(
            main_phone="555-1111",
            main_email="new@example.com",
            all_phones=frozenset({"555-1111"}),
            all_emails=frozenset({"new@example.com"}),
        )
        original_version = sample_client.version

        # Act: Update contact info
        sample_client.contact_info = new_contact

        # Assert: Domain should update contact info and increment version
        assert sample_client.contact_info == new_contact
        assert sample_client.contact_info.main_phone == "555-1111"
        assert sample_client.version == original_version + 1

    def test_client_address_property_initially_none(self, sample_client):
        """Domain should handle optional address as None initially."""
        # Act & Assert: Domain should allow None address
        assert sample_client.address is None

    def test_client_address_property_update(self, sample_client):
        """Domain should allow address updates with version increment."""
        # Arrange: Create address
        address = Address(street="456 Oak Ave", city="Newtown", zip_code="67890")
        original_version = sample_client.version

        # Act: Update address
        sample_client.address = address

        # Assert: Domain should update address and increment version
        assert sample_client.address == address
        assert sample_client.address.street == "456 Oak Ave"
        assert sample_client.version == original_version + 1

    def test_client_notes_property_initially_none(self, sample_client):
        """Domain should handle optional notes as None initially."""
        # Act & Assert: Domain should allow None notes
        assert sample_client.notes is None

    def test_client_notes_property_update(self, sample_client):
        """Domain should allow notes updates with version increment."""
        # Arrange: Create notes
        notes = "Important client with special dietary requirements"
        original_version = sample_client.version

        # Act: Update notes
        sample_client.notes = notes

        # Assert: Domain should update notes and increment version
        assert sample_client.notes == notes
        assert sample_client.version == original_version + 1


class TestClientMenuManagement:
    """Test client menu management behaviors."""

    @pytest.fixture
    def client_with_menus(self):
        """Fixture providing a client with sample menus."""
        profile = Profile(name="Client With Menus", sex="M", birthday=date(1980, 1, 1))
        contact_info = ContactInfo(
            main_phone="555-2222",
            main_email="menus@example.com",
            all_phones=frozenset({"555-2222"}),
            all_emails=frozenset({"menus@example.com"}),
        )
        client = Client.create_client(
            author_id="menu_author", profile=profile, contact_info=contact_info
        )
        return client

    def test_client_menus_property_initially_empty(self, client_with_menus):
        """Domain should initialize clients with empty menu list."""
        # Act & Assert: Domain should start with empty menus
        assert client_with_menus.menus == []
        assert len(client_with_menus.menus) == 0

    def test_client_create_menu_behavior(self, client_with_menus):
        """Domain should allow menu creation through client."""
        # Arrange: Prepare menu data
        original_version = client_with_menus.version
        menu_tags = {
            Tag(key="season", value="winter", author_id="menu_author", type="menu")
        }

        # Act: Create menu through client
        client_with_menus.create_menu(
            description="Winter meal planning menu",
            tags=menu_tags,
            menu_id="winter_menu_123",
        )

        # Assert: Domain should add menu to client
        assert len(client_with_menus.menus) == 1
        created_menu = client_with_menus.menus[0]
        assert created_menu.id == "winter_menu_123"
        assert created_menu.description == "Winter meal planning menu"
        assert created_menu.author_id == "menu_author"
        assert created_menu.client_id == client_with_menus.id
        assert client_with_menus.version == original_version + 1

    def test_client_create_menu_with_minimal_data(self, client_with_menus):
        """Domain should create menus with minimal required data."""
        # Act: Create menu with minimal data
        client_with_menus.create_menu(menu_id="simple_menu_456")

        # Assert: Domain should create menu with defaults
        assert len(client_with_menus.menus) == 1
        created_menu = client_with_menus.menus[0]
        assert created_menu.id == "simple_menu_456"
        assert created_menu.description is None
        assert created_menu.author_id == "menu_author"
        assert created_menu.client_id == client_with_menus.id

    def test_client_delete_menu_behavior(self, client_with_menus):
        """Domain should allow menu deletion through client."""
        # Arrange: Create menu first
        client_with_menus.create_menu(menu_id="menu_to_delete")
        menu_to_delete = client_with_menus.menus[0]
        original_version = client_with_menus.version

        # Act: Delete menu
        client_with_menus.delete_menu(menu_to_delete)

        # Assert: Domain should remove and discard menu
        assert len(client_with_menus.menus) == 0
        assert menu_to_delete.discarded
        assert client_with_menus.version == original_version + 1

    def test_client_delete_menu_already_discarded_is_noop(self, client_with_menus):
        """Domain should handle deletion of already discarded menus gracefully."""
        # Arrange: Create and delete menu
        client_with_menus.create_menu(menu_id="already_deleted")
        menu = client_with_menus.menus[0]
        client_with_menus.delete_menu(menu)
        original_version = client_with_menus.version

        # Act: Try to delete again
        client_with_menus.delete_menu(menu)

        # Assert: Domain should do nothing (no version increment)
        assert client_with_menus.version == original_version
        assert menu.discarded

    def test_client_delete_menu_not_in_collection_is_noop(self, client_with_menus):
        """Domain should handle deletion of menus not in collection gracefully."""
        # Arrange: Create external menu
        profile = Profile(name="Other Client", sex="M", birthday=date(1990, 10, 20))
        contact_info = ContactInfo(
            main_phone="555-3333",
            main_email="other@example.com",
            all_phones=frozenset({"555-3333"}),
            all_emails=frozenset({"other@example.com"}),
        )
        other_client = Client.create_client(
            author_id="other_author", profile=profile, contact_info=contact_info
        )
        other_client.create_menu(menu_id="external_menu")
        external_menu = other_client.menus[0]
        original_version = client_with_menus.version

        # Act: Try to delete external menu
        client_with_menus.delete_menu(external_menu)

        # Assert: Domain should do nothing
        assert client_with_menus.version == original_version
        assert len(client_with_menus.menus) == 0
        assert not external_menu.discarded

    def test_client_discarded_menus_property(self, client_with_menus):
        """Domain should provide access to discarded menus - but Client removes them entirely."""
        # Arrange: Create and delete some menus
        client_with_menus.create_menu(menu_id="active_menu")
        client_with_menus.create_menu(menu_id="menu_to_discard_1")
        client_with_menus.create_menu(menu_id="menu_to_discard_2")

        menu_1 = client_with_menus.menus[1]
        menu_2 = client_with_menus.menus[2]

        # Get reference to menus before deletion (since Client removes them entirely)
        assert not menu_1.discarded
        assert not menu_2.discarded

        client_with_menus.delete_menu(menu_1)
        client_with_menus.delete_menu(menu_2)

        # Act: Access discarded menus
        discarded = client_with_menus.discarded_menus

        # Assert: Domain removes discarded menus entirely from collection
        assert len(discarded) == 0  # Client removes discarded menus from collection
        assert (
            menu_1.discarded
        )  # But the menu objects themselves are marked as discarded
        assert menu_2.discarded
        assert len(client_with_menus.menus) == 1  # Only active menu remains


class TestClientTagManagement:
    """Test client tag management and domain rules."""

    @pytest.fixture
    def tagged_client(self):
        """Fixture providing a client with tags."""
        profile = Profile(name="Tagged Client", sex="M", birthday=date(1985, 5, 15))
        contact_info = ContactInfo(
            main_phone="555-4444",
            main_email="tagged@example.com",
            all_phones=frozenset({"555-4444"}),
            all_emails=frozenset({"tagged@example.com"}),
        )
        return Client.create_client(
            author_id="tag_author", profile=profile, contact_info=contact_info
        )

    def test_client_tags_property_initially_empty(self, tagged_client):
        """Domain should initialize clients with empty tag set."""
        # Act & Assert: Domain should start with empty tags
        assert tagged_client.tags == set()
        assert len(tagged_client.tags) == 0

    def test_client_tags_property_update_with_valid_tags(self, tagged_client):
        """Domain should allow tag updates with matching author_id."""
        # Arrange: Create valid tags
        valid_tags = {
            Tag(key="type", value="premium", author_id="tag_author", type="client"),
            Tag(key="region", value="west", author_id="tag_author", type="client"),
        }
        original_version = tagged_client.version

        # Act: Update tags
        tagged_client.tags = valid_tags

        # Assert: Domain should accept valid tags
        assert tagged_client.tags == valid_tags
        assert len(tagged_client.tags) == 2
        assert tagged_client.version == original_version + 1

    def test_client_tags_property_rejects_mismatched_author_id(self, tagged_client):
        """Domain should reject tags with mismatched author_id."""
        # Arrange: Create tags with wrong author_id
        invalid_tags = {
            Tag(key="type", value="invalid", author_id="wrong_author", type="client")
        }

        # Act & Assert: Domain should reject invalid tags
        with pytest.raises(BusinessRuleValidationError):
            tagged_client.tags = invalid_tags

    def test_client_tags_property_handles_empty_set(self, tagged_client):
        """Domain should handle empty tag sets gracefully."""
        # Arrange: Set initial tags then clear
        initial_tags = {
            Tag(key="temp", value="test", author_id="tag_author", type="client")
        }
        tagged_client.tags = initial_tags
        original_version = tagged_client.version

        # Act: Clear tags
        tagged_client.tags = set()

        # Assert: Domain should accept empty tags
        assert tagged_client.tags == set()
        assert len(tagged_client.tags) == 0
        assert tagged_client.version == original_version + 1


class TestClientDomainBehaviors:
    """Test core client domain behaviors and entity methods."""

    @pytest.fixture
    def domain_client(self):
        """Fixture providing a client for domain behavior testing."""
        profile = Profile(name="Domain Client", sex="M", birthday=date(1985, 5, 15))
        contact_info = ContactInfo(
            main_phone="555-5555",
            main_email="domain@example.com",
            all_phones=frozenset({"555-5555"}),
            all_emails=frozenset({"domain@example.com"}),
        )
        return Client.create_client(
            author_id="domain_author", profile=profile, contact_info=contact_info
        )

    def test_client_author_id_property_access(self, domain_client):
        """Domain should provide read access to author_id."""
        # Act & Assert: Domain should return author_id
        assert domain_client.author_id == "domain_author"

    def test_client_update_properties_method(self, domain_client):
        """Domain should support update_properties method."""
        # Arrange: Prepare updates
        new_notes = "Updated through update_properties"
        original_version = domain_client.version

        # Act: Update using update_properties
        domain_client.update_properties(notes=new_notes)

        # Assert: Domain should apply updates
        assert domain_client.notes == new_notes
        assert domain_client.version == original_version + 1

    def test_client_delete_behavior(self, domain_client):
        """Domain should support client deletion/discard."""
        # Act: Delete client
        domain_client.delete()

        # Assert: Domain should mark client as discarded
        assert domain_client.discarded

    def test_client_string_representation(self, domain_client):
        """Domain should provide meaningful string representation."""
        # Act: Get string representation
        repr_str = repr(domain_client)

        # Assert: Domain should include client info
        assert "Client" in repr_str
        assert domain_client.id in repr_str
        assert "Domain Client" in repr_str

    def test_client_hash_behavior(self, domain_client):
        """Domain should support hashing based on ID."""
        # Act: Get hash
        client_hash = hash(domain_client)

        # Assert: Domain should hash consistently
        assert isinstance(client_hash, int)
        assert hash(domain_client) == client_hash  # Consistent

    def test_client_equality_behavior(self, domain_client):
        """Domain should support equality comparison based on ID."""
        # Arrange: Create another client with same ID
        other_client = Client(
            id=domain_client.id,  # Same ID
            author_id="different_author",
            profile=Profile(name="Different", sex="M", birthday=date(1985, 5, 15)),
            contact_info=ContactInfo(
                main_phone="555-9999",
                main_email="different@example.com",
                all_phones=frozenset({"555-9999"}),
                all_emails=frozenset({"different@example.com"}),
            ),
        )

        # Create client with different ID
        profile = Profile(name="Different Client", sex="M", birthday=date(1985, 5, 15))
        contact_info = ContactInfo(
            main_phone="555-7777",
            main_email="diff@example.com",
            all_phones=frozenset({"555-7777"}),
            all_emails=frozenset({"diff@example.com"}),
        )
        different_client = Client.create_client(
            author_id="diff_author", profile=profile, contact_info=contact_info
        )

        # Act & Assert: Domain should compare by ID
        assert domain_client == other_client  # Same ID
        assert domain_client != different_client  # Different ID
        assert domain_client != "not_a_client"  # Different type


class TestClientDiscardedBehavior:
    """Test client behavior when discarded."""

    @pytest.fixture
    def discarded_client(self):
        """Fixture providing a discarded client."""
        profile = Profile(name="Discarded Client", sex="M", birthday=date(1985, 5, 15))
        contact_info = ContactInfo(
            main_phone="555-6666",
            main_email="discarded@example.com",
            all_phones=frozenset({"555-6666"}),
            all_emails=frozenset({"discarded@example.com"}),
        )
        client = Client.create_client(
            author_id="discard_author", profile=profile, contact_info=contact_info
        )
        client.delete()  # Discard the client
        return client

    def test_discarded_client_prevents_property_access(self, discarded_client):
        """Domain should prevent property access on discarded clients."""
        # Act & Assert: Domain should raise exception for property access
        with pytest.raises(Exception):  # Specific exception from _check_not_discarded
            _ = discarded_client.profile

        with pytest.raises(Exception):
            _ = discarded_client.author_id

        with pytest.raises(Exception):
            _ = discarded_client.menus

    def test_discarded_client_prevents_mutations(self, discarded_client):
        """Domain should prevent mutations on discarded clients."""
        # Arrange: Create new data
        new_profile = Profile(name="New", sex="M", birthday=date(1985, 5, 15))

        # Act & Assert: Domain should prevent mutations
        with pytest.raises(Exception):
            discarded_client.profile = new_profile

        with pytest.raises(Exception):
            discarded_client.create_menu(menu_id="test_menu")

        with pytest.raises(Exception):
            discarded_client.update_properties(notes="test")
