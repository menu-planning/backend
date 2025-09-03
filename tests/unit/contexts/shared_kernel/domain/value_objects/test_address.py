"""Unit tests for Address value object.

Tests address validation, equality semantics, and value object contracts.
Follows testing principles: no I/O, fakes only, behavior-focused assertions.
"""
import pytest
import attrs

from src.contexts.shared_kernel.domain.enums import State
from src.contexts.shared_kernel.domain.value_objects.address import Address


class TestAddressValidation:
    """Test address component validation and format constraints."""

    def test_address_validation_minimal_valid_address(self):
        """Validates minimal valid address creation."""
        # Given: minimal required address components
        # When: create address with valid components
        # Then: address is created successfully
        address = Address(
            street="Rua das Flores",
            number="123",
            city="São Paulo",
            state=State.SP
        )
        assert address.street == "Rua das Flores"
        assert address.number == "123"
        assert address.city == "São Paulo"
        assert address.state == State.SP

    def test_address_validation_all_fields_populated(self):
        """Validates address with all fields populated."""
        # Given: complete address information
        # When: create address with all components
        # Then: all fields are properly set
        address = Address(
            street="Avenida Paulista",
            number="1000",
            zip_code="01310-100",
            district="Bela Vista",
            city="São Paulo",
            state=State.SP,
            complement="Apto 45",
            note="Próximo ao metrô"
        )
        assert address.street == "Avenida Paulista"
        assert address.number == "1000"
        assert address.zip_code == "01310-100"
        assert address.district == "Bela Vista"
        assert address.city == "São Paulo"
        assert address.state == State.SP
        assert address.complement == "Apto 45"
        assert address.note == "Próximo ao metrô"

    def test_address_validation_all_fields_none(self):
        """Validates address with all fields as None."""
        # Given: no address information
        # When: create address with all None values
        # Then: address is created with all None fields
        address = Address()
        assert address.street is None
        assert address.number is None
        assert address.zip_code is None
        assert address.district is None
        assert address.city is None
        assert address.state is None
        assert address.complement is None
        assert address.note is None

    def test_address_validation_state_enum_validation(self):
        """Validates state field accepts only valid State enum values."""
        # Given: valid State enum value
        # When: create address with State enum
        # Then: state is properly set and validated
        address = Address(state=State.RJ)
        assert address.state == State.RJ
        assert isinstance(address.state, State)

    def test_address_validation_string_fields_accept_any_string(self):
        """Validates string fields accept any string value including empty."""
        # Given: various string values including empty strings
        # When: create address with different string values
        # Then: all string values are accepted
        address = Address(
            street="",
            number="0",
            zip_code="00000-000",
            district="Centro",
            city="A",
            complement=" ",
            note="\n\t"
        )
        assert address.street == ""
        assert address.number == "0"
        assert address.zip_code == "00000-000"
        assert address.district == "Centro"
        assert address.city == "A"
        assert address.complement == " "
        assert address.note == "\n\t"


class TestAddressEquality:
    """Test address equality semantics and value object contracts."""

    def test_address_equality_identical_addresses(self):
        """Ensures identical addresses are equal."""
        # Given: two addresses with identical values
        # When: compare the addresses
        # Then: they are equal
        address1 = Address(
            street="Rua A",
            number="123",
            city="São Paulo",
            state=State.SP
        )
        address2 = Address(
            street="Rua A",
            number="123",
            city="São Paulo",
            state=State.SP
        )
        assert address1 == address2
        assert hash(address1) == hash(address2)

    def test_address_equality_different_addresses(self):
        """Ensures different addresses are not equal."""
        # Given: two addresses with different values
        # When: compare the addresses
        # Then: they are not equal
        address1 = Address(
            street="Rua A",
            number="123",
            city="São Paulo",
            state=State.SP
        )
        address2 = Address(
            street="Rua B",
            number="123",
            city="São Paulo",
            state=State.SP
        )
        assert address1 != address2
        assert hash(address1) != hash(address2)

    def test_address_equality_partial_differences(self):
        """Ensures addresses with any different field are not equal."""
        # Given: addresses differing in one field
        # When: compare the addresses
        # Then: they are not equal
        base_address = Address(
            street="Rua A",
            number="123",
            zip_code="01234-567",
            city="São Paulo",
            state=State.SP
        )
        
        # Different street
        different_street = base_address.replace(street="Rua B")
        assert base_address != different_street
        
        # Different number
        different_number = base_address.replace(number="456")
        assert base_address != different_number
        
        # Different zip_code
        different_zip = base_address.replace(zip_code="98765-432")
        assert base_address != different_zip
        
        # Different city
        different_city = base_address.replace(city="Rio de Janeiro")
        assert base_address != different_city
        
        # Different state
        different_state = base_address.replace(state=State.RJ)
        assert base_address != different_state

    def test_address_equality_none_vs_empty_string(self):
        """Ensures None and empty string are treated as different values."""
        # Given: addresses with None vs empty string in same field
        # When: compare the addresses
        # Then: they are not equal
        address_with_none = Address(street=None)
        address_with_empty = Address(street="")
        
        assert address_with_none != address_with_empty
        assert hash(address_with_none) != hash(address_with_empty)

    def test_address_equality_immutability(self):
        """Ensures address objects are immutable."""
        # Given: an address instance
        # When: attempt to modify attributes
        # Then: modification raises FrozenInstanceError
        address = Address(street="Rua A", city="São Paulo")
        
        # Verify immutability by attempting to modify attributes
        # The frozen decorator from attrs prevents attribute assignment
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            address.street = "Rua B" # type: ignore[attr-defined]
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            address.city = "Rio de Janeiro" # type: ignore[attr-defined]

    def test_address_equality_replace_creates_new_instance(self):
        """Ensures replace method creates new instance without modifying original."""
        # Given: an original address
        # When: create new address using replace
        # Then: original remains unchanged and new instance is created
        original = Address(street="Rua A", city="São Paulo", state=State.SP)
        new_address = original.replace(street="Rua B")
        
        # Original unchanged
        assert original.street == "Rua A"
        assert original.city == "São Paulo"
        assert original.state == State.SP
        
        # New instance has updated values
        assert new_address.street == "Rua B"
        assert new_address.city == "São Paulo"  # Unchanged
        assert new_address.state == State.SP    # Unchanged
        
        # They are different instances
        assert original is not new_address
        assert original != new_address

    def test_address_equality_hash_consistency(self):
        """Ensures hash values are consistent across multiple calls."""
        # Given: an address instance
        # When: call hash multiple times
        # Then: hash value is consistent
        address = Address(
            street="Rua A",
            number="123",
            zip_code="01234-567",
            district="Centro",
            city="São Paulo",
            state=State.SP,
            complement="Apto 1",
            note="Test"
        )
        
        hash1 = hash(address)
        hash2 = hash(address)
        hash3 = hash(address)
        
        assert hash1 == hash2 == hash3

    def test_address_equality_hash_different_objects_same_values(self):
        """Ensures different objects with same values have same hash."""
        # Given: two different address instances with identical values
        # When: compute their hashes
        # Then: hashes are equal
        address1 = Address(street="Rua A", city="São Paulo", state=State.SP)
        address2 = Address(street="Rua A", city="São Paulo", state=State.SP)
        
        assert address1 is not address2  # Different objects
        assert hash(address1) == hash(address2)  # Same hash
