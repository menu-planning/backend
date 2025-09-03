"""Unit tests for ApiAddress schema.

Tests address schema validation, serialization/deserialization, and conversion methods.
Follows testing principles: no I/O, fakes only, behavior-focused assertions.
"""

import pytest
from pydantic import ValidationError

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_address import ApiAddress
from src.contexts.shared_kernel.adapters.ORM.sa_models.address_sa_model import AddressSaModel
from src.contexts.shared_kernel.domain.enums import State
from src.contexts.shared_kernel.domain.value_objects.address import Address


class TestApiAddressValidation:
    """Test address schema validation and field constraints."""

    def test_api_address_validation_minimal_valid_address(self):
        """Validates minimal valid address creation."""
        # Given: minimal required address components
        # When: create address with valid components
        # Then: address is created successfully
        api_address = ApiAddress(
            street="Rua das Flores",
            number="123",
            city="São Paulo",
            state=State.SP
        )
        assert api_address.street == "Rua das Flores"
        assert api_address.number == "123"
        assert api_address.city == "São Paulo"
        assert api_address.state == State.SP

    def test_api_address_validation_all_fields_populated(self):
        """Validates address with all fields populated."""
        # Given: complete address information
        # When: create address with all components
        # Then: all fields are properly set
        api_address = ApiAddress(
            street="Avenida Paulista",
            number="1000",
            zip_code="01310-100",
            district="Bela Vista",
            city="São Paulo",
            state=State.SP,
            complement="Apto 45",
            note="Próximo ao metrô"
        )
        assert api_address.street == "Avenida Paulista"
        assert api_address.number == "1000"
        assert api_address.zip_code == "01310-100"
        assert api_address.district == "Bela Vista"
        assert api_address.city == "São Paulo"
        assert api_address.state == State.SP
        assert api_address.complement == "Apto 45"
        assert api_address.note == "Próximo ao metrô"

    def test_api_address_validation_all_fields_none(self):
        """Validates address with all fields as None."""
        # Given: all fields as None
        # When: create address with None values
        # Then: address is created successfully with None values
        api_address = ApiAddress()
        assert api_address.street is None
        assert api_address.number is None
        assert api_address.zip_code is None
        assert api_address.district is None
        assert api_address.city is None
        assert api_address.state is None
        assert api_address.complement is None
        assert api_address.note is None

    def test_api_address_validation_string_fields_accept_any_string(self):
        """Validates string fields accept any string value including empty."""
        # Given: various string values
        # When: create address with different string values
        # Then: all string values are accepted (empty strings become None)
        api_address = ApiAddress(
            street="",
            number="0",
            zip_code="12345",
            district="Centro",
            city="Rio de Janeiro",
            complement="Sala 101",
            note="Test note"
        )
        assert api_address.street is None  # Empty string becomes None
        assert api_address.number == "0"
        assert api_address.zip_code == "12345"
        assert api_address.district == "Centro"
        assert api_address.city == "Rio de Janeiro"
        assert api_address.complement == "Sala 101"
        assert api_address.note == "Test note"

    def test_api_address_validation_state_enum_accepts_all_states(self):
        """Validates state field accepts all State enum values."""
        # Given: all state enum values
        # When: create address with each state
        # Then: all states are accepted
        for state in State:
            api_address = ApiAddress(state=state)
            assert api_address.state == state

    def test_api_address_validation_state_accepts_none(self):
        """Validates state field accepts None value."""
        # Given: None state value
        # When: create address with None state
        # Then: state is None
        api_address = ApiAddress(state=None)
        assert api_address.state is None

    def test_api_address_validation_string_length_constraints(self):
        """Validates string field length constraints."""
        # Given: strings exceeding maximum length
        # When: create address with long strings
        # Then: validation errors are raised
        long_string = "x" * 256  # Exceeds 255 character limit
        
        # Test that validation errors are raised for fields that exceed length limits
        with pytest.raises(ValidationError):
            ApiAddress(street=long_string)

        with pytest.raises(ValidationError):
            ApiAddress(number=long_string)

        # Note: zip_code currently uses same 255-char limit as other fields
        with pytest.raises(ValidationError):
            ApiAddress(zip_code="x" * 256)  # Exceeds 255 character limit

        with pytest.raises(ValidationError):
            ApiAddress(district=long_string)

        with pytest.raises(ValidationError):
            ApiAddress(city=long_string)

        with pytest.raises(ValidationError):
            ApiAddress(complement=long_string)

        with pytest.raises(ValidationError):
            ApiAddress(note=long_string)

    def test_api_address_validation_string_trimming(self):
        """Validates string fields are trimmed automatically."""
        # Given: strings with leading/trailing whitespace
        # When: create address with whitespace
        # Then: strings are trimmed
        api_address = ApiAddress(
            street="  Rua das Flores  ",
            number=" 123 ",
            zip_code=" 01310-100 ",
            district=" Bela Vista ",
            city=" São Paulo ",
            complement=" Apto 45 ",
            note=" Próximo ao metrô "
        )
        assert api_address.street == "Rua das Flores"
        assert api_address.number == "123"
        assert api_address.zip_code == "01310-100"
        assert api_address.district == "Bela Vista"
        assert api_address.city == "São Paulo"
        assert api_address.complement == "Apto 45"
        assert api_address.note == "Próximo ao metrô"

    def test_api_address_validation_empty_strings_become_none(self):
        """Validates empty strings are converted to None."""
        # Given: empty strings
        # When: create address with empty strings
        # Then: empty strings become None
        api_address = ApiAddress(
            street="",
            number="",
            zip_code="",
            district="",
            city="",
            complement="",
            note=""
        )
        assert api_address.street is None
        assert api_address.number is None
        assert api_address.zip_code is None
        assert api_address.district is None
        assert api_address.city is None
        assert api_address.complement is None
        assert api_address.note is None


class TestApiAddressEquality:
    """Test address equality semantics and value object contracts."""

    def test_api_address_equality_same_values(self):
        """Ensures proper equality semantics for identical values."""
        # Given: two address instances with same values
        # When: compare addresses
        # Then: they should be equal
        address1 = ApiAddress(
            street="Rua das Flores",
            number="123",
            city="São Paulo",
            state=State.SP
        )
        address2 = ApiAddress(
            street="Rua das Flores",
            number="123",
            city="São Paulo",
            state=State.SP
        )
        assert address1 == address2

    def test_api_address_equality_different_values(self):
        """Ensures proper inequality semantics for different values."""
        # Given: two address instances with different values
        # When: compare addresses
        # Then: they should not be equal
        address1 = ApiAddress(
            street="Rua das Flores",
            number="123",
            city="São Paulo",
            state=State.SP
        )
        address2 = ApiAddress(
            street="Avenida Paulista",
            number="123",
            city="São Paulo",
            state=State.SP
        )
        assert address1 != address2

    def test_api_address_equality_none_vs_empty(self):
        """Ensures None and empty string are treated as equal."""
        # Given: address with None and address with empty string
        # When: compare addresses
        # Then: they should be equal (both become None after validation)
        address1 = ApiAddress(street=None)
        address2 = ApiAddress(street="")
        assert address1 == address2

    def test_api_address_equality_different_state_values(self):
        """Ensures different state values result in inequality."""
        # Given: two addresses with different states
        # When: compare addresses
        # Then: they should not be equal
        address1 = ApiAddress(state=State.SP)
        address2 = ApiAddress(state=State.RJ)
        assert address1 != address2


class TestApiAddressSerialization:
    """Test address serialization and deserialization contracts."""

    def test_api_address_serialization_to_dict(self):
        """Validates address can be serialized to dictionary."""
        # Given: address with all fields
        # When: serialize to dict
        # Then: all fields are properly serialized
        api_address = ApiAddress(
            street="Rua das Flores",
            number="123",
            zip_code="01310-100",
            district="Bela Vista",
            city="São Paulo",
            state=State.SP,
            complement="Apto 45",
            note="Próximo ao metrô"
        )
        
        result = api_address.model_dump()
        
        assert result["street"] == "Rua das Flores"
        assert result["number"] == "123"
        assert result["zip_code"] == "01310-100"
        assert result["district"] == "Bela Vista"
        assert result["city"] == "São Paulo"
        assert result["state"] == State.SP
        assert result["complement"] == "Apto 45"
        assert result["note"] == "Próximo ao metrô"

    def test_api_address_serialization_to_json(self):
        """Validates address can be serialized to JSON."""
        # Given: address with all fields
        # When: serialize to JSON
        # Then: JSON is properly formatted
        api_address = ApiAddress(
            street="Rua das Flores",
            number="123",
            city="São Paulo",
            state=State.SP
        )
        
        json_str = api_address.model_dump_json()
        
        assert '"street":"Rua das Flores"' in json_str
        assert '"number":"123"' in json_str
        assert '"city":"São Paulo"' in json_str
        assert '"state":"SP"' in json_str

    def test_api_address_deserialization_from_dict(self):
        """Validates address can be deserialized from dictionary."""
        # Given: dictionary with address data
        # When: create address from dict
        # Then: address is properly created
        data = {
            "street": "Rua das Flores",
            "number": "123",
            "zip_code": "01310-100",
            "district": "Bela Vista",
            "city": "São Paulo",
            "state": State.SP,  # Use State enum, not string
            "complement": "Apto 45",
            "note": "Próximo ao metrô"
        }
        
        api_address = ApiAddress.model_validate(data)
        
        assert api_address.street == "Rua das Flores"
        assert api_address.number == "123"
        assert api_address.zip_code == "01310-100"
        assert api_address.district == "Bela Vista"
        assert api_address.city == "São Paulo"
        assert api_address.state == State.SP
        assert api_address.complement == "Apto 45"
        assert api_address.note == "Próximo ao metrô"

    def test_api_address_deserialization_from_json(self):
        """Validates address can be deserialized from JSON."""
        # Given: JSON string with address data
        # When: create address from JSON
        # Then: address is properly created
        json_str = '''
        {
            "street": "Rua das Flores",
            "number": "123",
            "city": "São Paulo",
            "state": "SP"
        }
        '''
        
        api_address = ApiAddress.model_validate_json(json_str)
        
        assert api_address.street == "Rua das Flores"
        assert api_address.number == "123"
        assert api_address.city == "São Paulo"
        assert api_address.state == State.SP

    def test_api_address_serialization_with_none_values(self):
        """Validates serialization handles None values correctly."""
        # Given: address with None values
        # When: serialize to dict
        # Then: None values are preserved
        api_address = ApiAddress()
        
        result = api_address.model_dump()
        
        assert result["street"] is None
        assert result["number"] is None
        assert result["zip_code"] is None
        assert result["district"] is None
        assert result["city"] is None
        assert result["state"] is None
        assert result["complement"] is None
        assert result["note"] is None


class TestApiAddressDomainConversion:
    """Test address conversion between API schema and domain model."""

    def test_api_address_from_domain_conversion(self):
        """Validates conversion from domain model to API schema."""
        # Given: domain address model
        # When: convert to API schema
        # Then: all fields are properly converted
        domain_address = Address(
            street="Rua das Flores",
            number="123",
            zip_code="01310-100",
            district="Bela Vista",
            city="São Paulo",
            state=State.SP,
            complement="Apto 45",
            note="Próximo ao metrô"
        )
        
        api_address = ApiAddress.from_domain(domain_address)
        
        assert api_address.street == "Rua das Flores"
        assert api_address.number == "123"
        assert api_address.zip_code == "01310-100"
        assert api_address.district == "Bela Vista"
        assert api_address.city == "São Paulo"
        assert api_address.state == State.SP
        assert api_address.complement == "Apto 45"
        assert api_address.note == "Próximo ao metrô"

    def test_api_address_to_domain_conversion(self):
        """Validates conversion from API schema to domain model."""
        # Given: API address schema
        # When: convert to domain model
        # Then: all fields are properly converted
        api_address = ApiAddress(
            street="Rua das Flores",
            number="123",
            zip_code="01310-100",
            district="Bela Vista",
            city="São Paulo",
            state=State.SP,
            complement="Apto 45",
            note="Próximo ao metrô"
        )
        
        domain_address = api_address.to_domain()
        
        assert domain_address.street == "Rua das Flores"
        assert domain_address.number == "123"
        assert domain_address.zip_code == "01310-100"
        assert domain_address.district == "Bela Vista"
        assert domain_address.city == "São Paulo"
        assert domain_address.state == State.SP
        assert domain_address.complement == "Apto 45"
        assert domain_address.note == "Próximo ao metrô"

    def test_api_address_domain_conversion_roundtrip(self):
        """Validates roundtrip conversion maintains data integrity."""
        # Given: domain address model
        # When: convert to API schema and back to domain
        # Then: data integrity is maintained
        original_domain = Address(
            street="Rua das Flores",
            number="123",
            zip_code="01310-100",
            district="Bela Vista",
            city="São Paulo",
            state=State.SP,
            complement="Apto 45",
            note="Próximo ao metrô"
        )
        
        api_address = ApiAddress.from_domain(original_domain)
        converted_domain = api_address.to_domain()
        
        assert converted_domain == original_domain

    def test_api_address_domain_conversion_with_none_values(self):
        """Validates conversion handles None values correctly."""
        # Given: domain address with None values
        # When: convert to API schema and back
        # Then: None values are preserved
        original_domain = Address()
        
        api_address = ApiAddress.from_domain(original_domain)
        converted_domain = api_address.to_domain()
        
        assert converted_domain == original_domain

    def test_api_address_domain_conversion_state_enum_handling(self):
        """Validates state enum conversion between API and domain."""
        # Given: API address with state enum
        # When: convert to domain and back
        # Then: state enum is properly handled
        api_address = ApiAddress(state=State.SP)
        
        domain_address = api_address.to_domain()
        converted_api = ApiAddress.from_domain(domain_address)
        
        assert converted_api.state == State.SP
        assert domain_address.state == State.SP

    def test_api_address_domain_conversion_none_state_handling(self):
        """Validates None state conversion between API and domain."""
        # Given: API address with None state
        # When: convert to domain and back
        # Then: None state is properly handled
        api_address = ApiAddress(state=None)
        
        domain_address = api_address.to_domain()
        converted_api = ApiAddress.from_domain(domain_address)
        
        assert converted_api.state is None
        assert domain_address.state is None


class TestApiAddressOrmConversion:
    """Test address conversion between API schema and ORM model."""

    def test_api_address_from_orm_model_conversion(self):
        """Validates conversion from ORM model to API schema."""
        # Given: ORM address model
        # When: convert to API schema
        # Then: all fields are properly converted
        orm_address = AddressSaModel(
            street="Rua das Flores",
            number="123",
            zip_code="01310-100",
            district="Bela Vista",
            city="São Paulo",
            state="SP",
            complement="Apto 45",
            note="Próximo ao metrô"
        )
        
        api_address = ApiAddress.from_orm_model(orm_address)
        
        assert api_address.street == "Rua das Flores"
        assert api_address.number == "123"
        assert api_address.zip_code == "01310-100"
        assert api_address.district == "Bela Vista"
        assert api_address.city == "São Paulo"
        assert api_address.state == State.SP
        assert api_address.complement == "Apto 45"
        assert api_address.note == "Próximo ao metrô"

    def test_api_address_to_orm_kwargs_conversion(self):
        """Validates conversion from API schema to ORM kwargs."""
        # Given: API address schema
        # When: convert to ORM kwargs
        # Then: all fields are properly converted
        api_address = ApiAddress(
            street="Rua das Flores",
            number="123",
            zip_code="01310-100",
            district="Bela Vista",
            city="São Paulo",
            state=State.SP,
            complement="Apto 45",
            note="Próximo ao metrô"
        )
        
        orm_kwargs = api_address.to_orm_kwargs()
        
        assert orm_kwargs["street"] == "Rua das Flores"
        assert orm_kwargs["number"] == "123"
        assert orm_kwargs["zip_code"] == "01310-100"
        assert orm_kwargs["district"] == "Bela Vista"
        assert orm_kwargs["city"] == "São Paulo"
        assert orm_kwargs["state"] == "SP"  # ORM expects string value
        assert orm_kwargs["complement"] == "Apto 45"
        assert orm_kwargs["note"] == "Próximo ao metrô"

    def test_api_address_orm_conversion_roundtrip(self):
        """Validates roundtrip conversion maintains data integrity."""
        # Given: ORM address model
        # When: convert to API schema and back to ORM kwargs
        # Then: data integrity is maintained
        original_orm = AddressSaModel(
            street="Rua das Flores",
            number="123",
            zip_code="01310-100",
            district="Bela Vista",
            city="São Paulo",
            state="SP",
            complement="Apto 45",
            note="Próximo ao metrô"
        )
        
        api_address = ApiAddress.from_orm_model(original_orm)
        orm_kwargs = api_address.to_orm_kwargs()
        
        # Create new ORM model from kwargs for comparison
        new_orm = AddressSaModel(**orm_kwargs)
        
        assert new_orm.street == original_orm.street
        assert new_orm.number == original_orm.number
        assert new_orm.zip_code == original_orm.zip_code
        assert new_orm.district == original_orm.district
        assert new_orm.city == original_orm.city
        # Note: state conversion from string to enum and back to string
        assert new_orm.state == "SP"  # Should be string in ORM
        assert new_orm.complement == original_orm.complement
        assert new_orm.note == original_orm.note

    def test_api_address_orm_conversion_with_none_values(self):
        """Validates conversion handles None values correctly."""
        # Given: ORM address with None values
        # When: convert to API schema and back
        # Then: None values are preserved
        original_orm = AddressSaModel()
        
        api_address = ApiAddress.from_orm_model(original_orm)
        orm_kwargs = api_address.to_orm_kwargs()
        
        new_orm = AddressSaModel(**orm_kwargs)
        
        assert new_orm.street is None
        assert new_orm.number is None
        assert new_orm.zip_code is None
        assert new_orm.district is None
        assert new_orm.city is None
        assert new_orm.state is None
        assert new_orm.complement is None
        assert new_orm.note is None

    def test_api_address_orm_conversion_state_enum_handling(self):
        """Validates state enum conversion between API and ORM."""
        # Given: API address with state enum
        # When: convert to ORM kwargs
        # Then: state enum is properly converted to string
        api_address = ApiAddress(state=State.SP)
        
        orm_kwargs = api_address.to_orm_kwargs()
        
        assert orm_kwargs["state"] == "SP"  # ORM expects string value

    def test_api_address_orm_conversion_none_state_handling(self):
        """Validates None state conversion between API and ORM."""
        # Given: API address with None state
        # When: convert to ORM kwargs
        # Then: None state is properly handled
        api_address = ApiAddress(state=None)
        
        orm_kwargs = api_address.to_orm_kwargs()
        
        assert orm_kwargs["state"] is None


class TestApiAddressEdgeCases:
    """Test address schema edge cases and error handling."""

    def test_api_address_validation_invalid_state_string(self):
        """Validates invalid state string raises validation error."""
        # Given: invalid state string
        # When: create address with invalid state
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiAddress(state="INVALID") # type: ignore[arg-type]

    def test_api_address_validation_whitespace_only_strings(self):
        """Validates whitespace-only strings are converted to None."""
        # Given: whitespace-only strings
        # When: create address with whitespace
        # Then: whitespace becomes None
        api_address = ApiAddress(
            street="   ",
            number="\t\t",
            zip_code="\n\n",
            district="  \t  ",
            city="\r\n",
            complement="   \t\n  ",
            note="\t\r\n"
        )
        
        assert api_address.street is None
        assert api_address.number is None
        assert api_address.zip_code is None
        assert api_address.district is None
        assert api_address.city is None
        assert api_address.complement is None
        assert api_address.note is None

    def test_api_address_validation_mixed_whitespace_and_content(self):
        """Validates mixed whitespace and content is properly trimmed."""
        # Given: strings with mixed whitespace and content
        # When: create address with mixed content
        # Then: content is properly trimmed
        api_address = ApiAddress(
            street="  Rua das Flores  \t",
            number="\n123\r",
            zip_code="\t01310-100\n",
            district="  Bela Vista  ",
            city="\rSão Paulo\t",
            complement="\nApto 45\r",
            note="\tPróximo ao metrô\n"
        )
        
        assert api_address.street == "Rua das Flores"
        assert api_address.number == "123"
        assert api_address.zip_code == "01310-100"
        assert api_address.district == "Bela Vista"
        assert api_address.city == "São Paulo"
        assert api_address.complement == "Apto 45"
        assert api_address.note == "Próximo ao metrô"

    def test_api_address_validation_maximum_length_strings(self):
        """Validates maximum length strings are accepted."""
        # Given: strings at maximum length
        # When: create address with max length strings
        # Then: addresses are created successfully
        max_street = "x" * 255
        max_number = "x" * 255
        max_zip = "x" * 20
        max_district = "x" * 255
        max_city = "x" * 255
        max_complement = "x" * 255
        max_note = "x" * 255
        
        api_address = ApiAddress(
            street=max_street,
            number=max_number,
            zip_code=max_zip,
            district=max_district,
            city=max_city,
            complement=max_complement,
            note=max_note
        )
        
        assert api_address.street == max_street
        assert api_address.number == max_number
        assert api_address.zip_code == max_zip
        assert api_address.district == max_district
        assert api_address.city == max_city
        assert api_address.complement == max_complement
        assert api_address.note == max_note

    def test_api_address_serialization_unicode_characters(self):
        """Validates serialization handles unicode characters correctly."""
        # Given: address with unicode characters
        # When: serialize and deserialize
        # Then: unicode characters are preserved
        api_address = ApiAddress(
            street="Rua das Flores",
            number="123",
            city="São Paulo",
            state=State.SP,
            note="Próximo ao metrô"
        )
        
        json_str = api_address.model_dump_json()
        deserialized = ApiAddress.model_validate_json(json_str)
        
        assert deserialized.street == "Rua das Flores"
        assert deserialized.number == "123"
        assert deserialized.city == "São Paulo"
        assert deserialized.state == State.SP
        assert deserialized.note == "Próximo ao metrô"

    def test_api_address_immutability(self):
        """Validates address schema is immutable."""
        # Given: address instance
        # When: attempt to modify fields
        # Then: modification raises error
        api_address = ApiAddress(street="Rua das Flores")
        
        with pytest.raises(ValidationError):
            api_address.street = "Avenida Paulista"
