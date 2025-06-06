import pytest
from src.contexts.shared_kernel.domain.enums import State
from src.contexts.shared_kernel.domain.value_objects.address import Address
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.address import ApiAddress
from src.contexts.shared_kernel.adapters.ORM.sa_models.address import AddressSaModel
import attr


class TestApiAddress:
    """Test suite for ApiAddress schema."""

    def test_create_valid_address(self):
        """Test creating a valid address."""
        address = ApiAddress(
            street="Main St",
            number="123",
            zip_code="12345",
            district="Downtown",
            city="Metropolis",
            state=State.SP,
            complement="Apt 4B",
            note="Ring twice"
        )
        assert address.street == "Main St"
        assert address.number == "123"
        assert address.zip_code == "12345"
        assert address.district == "Downtown"
        assert address.city == "Metropolis"
        assert address.state == 'SP'
        assert address.complement == "Apt 4B"
        assert address.note == "Ring twice"

    def test_create_minimal_address(self):
        """Test creating an address with minimal fields."""
        address = ApiAddress(
            street="Main St",
            number="123",
            city="Metropolis",
            state=State.SP
        )
        assert address.street == "Main St"
        assert address.number == "123"
        assert address.city == "Metropolis"
        assert address.state == 'SP'
        assert address.zip_code is None
        assert address.district is None
        assert address.complement is None
        assert address.note is None

    def test_from_domain(self):
        """Test converting from domain object."""
        domain_address = Address(
            street="Main St",
            number="123",
            zip_code="12345",
            district="Downtown",
            city="Metropolis",
            state=State.SP,
            complement="Apt 4B",
            note="Ring twice"
        )
        api_address = ApiAddress.from_domain(domain_address)
        
        assert api_address.street == "Main St"
        assert api_address.number == "123"
        assert api_address.zip_code == "12345"
        assert api_address.district == "Downtown"
        assert api_address.city == "Metropolis"
        assert api_address.state == 'SP'
        assert api_address.complement == "Apt 4B"
        assert api_address.note == "Ring twice"

    def test_to_domain(self):
        """Test converting to domain object."""
        api_address = ApiAddress(
            street="Main St",
            number="123",
            zip_code="12345",
            district="Downtown",
            city="Metropolis",
            state=State.SP,
            complement="Apt 4B",
            note="Ring twice"
        )
        domain_address = api_address.to_domain()
        
        assert domain_address.street == "Main St"
        assert domain_address.number == "123"
        assert domain_address.zip_code == "12345"
        assert domain_address.district == "Downtown"
        assert domain_address.city == "Metropolis"
        assert domain_address.state == State.SP
        assert domain_address.complement == "Apt 4B"
        assert domain_address.note == "Ring twice"

    def test_from_orm_model(self):
        """Test converting from ORM model."""
        orm_address = AddressSaModel(
            street="Main St",
            number="123",
            zip_code="12345",
            district="Downtown",
            city="Metropolis",
            state=State.SP.value,
            complement="Apt 4B",
            note="Ring twice"
        )
        api_address = ApiAddress.from_orm_model(orm_address)
        
        assert api_address.street == "Main St"
        assert api_address.number == "123"
        assert api_address.zip_code == "12345"
        assert api_address.district == "Downtown"
        assert api_address.city == "Metropolis"
        assert api_address.state == 'SP'
        assert api_address.complement == "Apt 4B"
        assert api_address.note == "Ring twice"

    def test_to_orm_kwargs(self):
        """Test converting to ORM model kwargs."""
        api_address = ApiAddress(
            street="Main St",
            number="123",
            zip_code="12345",
            district="Downtown",
            city="Metropolis",
            state=State.SP,
            complement="Apt 4B",
            note="Ring twice"
        )
        orm_kwargs = api_address.to_orm_kwargs()
        
        assert orm_kwargs["street"] == "Main St"
        assert orm_kwargs["number"] == "123"
        assert orm_kwargs["zip_code"] == "12345"
        assert orm_kwargs["district"] == "Downtown"
        assert orm_kwargs["city"] == "Metropolis"
        assert orm_kwargs["state"] == 'SP'
        assert orm_kwargs["complement"] == "Apt 4B"
        assert orm_kwargs["note"] == "Ring twice"

    def test_serialization(self):
        """Test that the address serializes correctly."""
        address = ApiAddress(
            street="Main St",
            number="123",
            city="Metropolis",
            state=State.SP
        )
        serialized = address.model_dump()
        
        assert serialized["street"] == "Main St"
        assert serialized["number"] == "123"
        assert serialized["city"] == "Metropolis"
        assert serialized["state"] == 'SP'
        assert serialized["zip_code"] is None
        assert serialized["district"] is None
        assert serialized["complement"] is None
        assert serialized["note"] is None

    def test_immutability(self):
        """Test that the address is immutable."""
        address = ApiAddress(
            street="Main St",
            number="123",
            city="Metropolis",
            state=State.SP
        )
        with pytest.raises(ValueError):
            address.street = "New St"

    def test_orm_model_with_none_values(self):
        """Test ORM conversion with None values."""
        orm_address = AddressSaModel(
            street="Main St",
            number="123",
            city="Metropolis",
            state=None
        )
        api_address = ApiAddress.from_orm_model(orm_address)
        
        assert api_address.street == "Main St"
        assert api_address.number == "123"
        assert api_address.city == "Metropolis"
        assert api_address.state is None
        assert api_address.zip_code is None
        assert api_address.district is None
        assert api_address.complement is None
        assert api_address.note is None

    def test_orm_kwargs_with_none_values(self):
        """Test ORM kwargs conversion with None values."""
        api_address = ApiAddress(
            street="Main St",
            number="123",
            city="Metropolis",
            state=None
        )
        orm_kwargs = api_address.to_orm_kwargs()
        
        assert orm_kwargs["street"] == "Main St"
        assert orm_kwargs["number"] == "123"
        assert orm_kwargs["city"] == "Metropolis"
        assert orm_kwargs["state"] is None
        assert orm_kwargs["zip_code"] is None
        assert orm_kwargs["district"] is None
        assert orm_kwargs["complement"] is None
        assert orm_kwargs["note"] is None

    def test_all_attributes_covered_in_conversion(self):
        """Test that all attributes are covered in conversions between Address and ApiAddress."""
        # Create a domain object with all fields set
        domain_address = Address(
            street="Main St",
            number="123",
            zip_code="12345",
            district="Downtown",
            city="Metropolis",
            state=State.SP,
            complement="Apt 4B",
            note="Ring twice"
        )
        # Convert to API and back
        api_address = ApiAddress.from_domain(domain_address)
        roundtrip_address = api_address.to_domain()

        # Check that all fields are equal
        for field in attr.fields(Address):
            assert getattr(domain_address, field.name) == getattr(roundtrip_address, field.name)

        # Also check that all ApiAddress fields are present in the model_dump
        api_dump = api_address.model_dump()
        for field in ApiAddress.model_fields:
            assert field in api_dump 