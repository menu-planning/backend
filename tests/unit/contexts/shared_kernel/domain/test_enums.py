"""Unit tests for shared kernel domain enumerations.

Tests enum completeness, value validation, and equality semantics.
"""
from __future__ import annotations

import pytest

from src.contexts.shared_kernel.domain.enums import (
    MeasureUnit,
    Privacy,
    State,
    Weekday,
)


class TestStateEnum:
    """Test State enum completeness and behavior."""

    def test_state_enum_values(self) -> None:
        """Validates all state enum values."""
        # Given: Expected Brazilian state codes
        expected_states = {
            "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
            "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
            "RS", "RO", "RR", "SC", "SP", "SE", "TO"
        }
        
        # When: Getting all state enum values
        actual_states = {state.value for state in State}
        
        # Then: All expected states should be present
        assert actual_states == expected_states
        assert len(State) == 27  # Total number of Brazilian states + DF

    def test_state_enum_equality(self) -> None:
        """Ensures proper equality semantics for State enum."""
        # Given: Two state instances with same value
        state1 = State.SP
        state2 = State.SP
        
        # When/Then: They should be equal
        assert state1 == state2
        assert state1 is state2  # Enum instances are singletons

    def test_state_enum_hash(self) -> None:
        """Ensures State enum can be used in sets and as dict keys."""
        # Given: State enum instances
        states = {State.SP, State.RJ, State.MG}
        
        # When/Then: Should work in set operations
        assert State.SP in states
        assert len(states) == 3


class TestMeasureUnitEnum:
    """Test MeasureUnit enum completeness and behavior."""

    def test_measure_unit_enum_values(self) -> None:
        """Validates all measure unit enum values."""
        # Given: Expected measurement units
        expected_units = {
            "un", "kg", "g", "mg", "mcg", "l", "ml", "percentual", "kcal", "IU",
            "colher de sopa", "colher de chá", "xícara", "pitada", "mão cheia",
            "fatia", "pedaço"
        }
        
        # When: Getting all measure unit enum values
        actual_units = {unit.value for unit in MeasureUnit}
        
        # Then: All expected units should be present
        assert actual_units == expected_units
        assert len(MeasureUnit) == 17

    def test_measure_unit_enum_equality(self) -> None:
        """Ensures proper equality semantics for MeasureUnit enum."""
        # Given: Two measure unit instances with same value
        unit1 = MeasureUnit.KILOGRAM
        unit2 = MeasureUnit.KILOGRAM
        
        # When/Then: They should be equal
        assert unit1 == unit2
        assert unit1 is unit2

    def test_measure_unit_enum_value_access(self) -> None:
        """Ensures MeasureUnit values are accessible."""
        # Given: A measure unit
        unit = MeasureUnit.GRAM
        
        # When/Then: Should have accessible string value
        assert unit.value == "g"
        assert isinstance(unit.value, str)


class TestPrivacyEnum:
    """Test Privacy enum completeness and behavior."""

    def test_privacy_enum_values(self) -> None:
        """Validates all privacy enum values."""
        # Given: Expected privacy levels
        expected_levels = {"private", "public"}
        
        # When: Getting all privacy enum values
        actual_levels = {privacy.value for privacy in Privacy}
        
        # Then: All expected levels should be present
        assert actual_levels == expected_levels
        assert len(Privacy) == 2

    def test_privacy_enum_equality(self) -> None:
        """Ensures proper equality semantics for Privacy enum."""
        # Given: Two privacy instances with same value
        privacy1 = Privacy.PRIVATE
        privacy2 = Privacy.PRIVATE
        
        # When/Then: They should be equal
        assert privacy1 == privacy2
        assert privacy1 is privacy2

    def test_privacy_enum_value_access(self) -> None:
        """Ensures Privacy values are accessible."""
        # Given: A privacy level
        privacy = Privacy.PUBLIC
        
        # When/Then: Should have accessible string value
        assert privacy.value == "public"
        assert isinstance(privacy.value, str)


class TestWeekdayEnum:
    """Test Weekday enum completeness and behavior."""

    def test_weekday_enum_values(self) -> None:
        """Validates all weekday enum values."""
        # Given: Expected weekdays
        expected_weekdays = {
            "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
            "Sexta-feira", "Sábado", "Domingo"
        }
        
        # When: Getting all weekday enum values
        actual_weekdays = {weekday.value for weekday in Weekday}
        
        # Then: All expected weekdays should be present
        assert actual_weekdays == expected_weekdays
        assert len(Weekday) == 7

    def test_weekday_enum_equality(self) -> None:
        """Ensures proper equality semantics for Weekday enum."""
        # Given: Two weekday instances with same value
        weekday1 = Weekday.MONDAY
        weekday2 = Weekday.MONDAY
        
        # When/Then: They should be equal
        assert weekday1 == weekday2
        assert weekday1 is weekday2


class TestEnumCrossCutting:
    """Test cross-cutting enum behaviors."""

    def test_all_enums_are_unique(self) -> None:
        """Ensures all enums marked with @unique are actually unique."""
        # Given: All enum classes
        enum_classes = [
            State, MeasureUnit, Privacy, Weekday
        ]
        
        # When/Then: Each enum should have unique values
        for enum_class in enum_classes:
            values = [member.value for member in enum_class]
            assert len(values) == len(set(values)), f"{enum_class.__name__} has duplicate values"

    def test_enum_values_are_accessible(self) -> None:
        """Ensures enum values are accessible and have expected types."""
        # Given: All enum classes
        enum_classes = [State, MeasureUnit, Privacy, Weekday]
        
        # When/Then: Each enum should have accessible values with expected types
        for enum_class in enum_classes:
            for member in enum_class:
                # Values should be accessible
                assert member.value is not None
                # String enums should have string values
                if enum_class in [MeasureUnit, Privacy, Weekday]:
                    assert isinstance(member.value, str)
                # State enum should have string values too
                elif enum_class == State:
                    assert isinstance(member.value, str)

    def test_enum_instances_are_singletons(self) -> None:
        """Ensures enum instances are singletons."""
        # Given: All enum classes
        enum_classes = [State, MeasureUnit, Privacy, Weekday]
        
        # When/Then: Multiple references to same enum should be identical
        for enum_class in enum_classes:
            member = list(enum_class)[0]
            assert member is enum_class(member.value)
            assert member is getattr(enum_class, member.name)
