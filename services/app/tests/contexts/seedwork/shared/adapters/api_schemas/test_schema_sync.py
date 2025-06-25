"""
Schema synchronization validator for Domain/API/ORM triplets.

This module provides utilities to validate that Domain, API, and ORM classes
have consistent field mappings to prevent schema drift during development.
"""

import inspect
import logging
from dataclasses import fields as dataclass_fields, is_dataclass
from typing import Dict, List, Set, Type

import pytest
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy import inspect as sa_inspect

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiModel
from src.db.base import SaBase

logger = logging.getLogger(__name__)


class SchemaSyncResult:
    """Results of schema synchronization validation."""
    
    def __init__(self, 
                 domain_class: Type,
                 api_class: Type,
                 orm_class: Type):
        self.domain_class = domain_class
        self.api_class = api_class
        self.orm_class = orm_class
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.domain_fields: Set[str] = set()
        self.api_fields: Set[str] = set()
        self.orm_fields: Set[str] = set()
        
    @property
    def is_valid(self) -> bool:
        """Return True if no errors found."""
        return len(self.errors) == 0
        
    @property
    def summary(self) -> str:
        """Return a summary of validation results."""
        return (
            f"Domain: {len(self.domain_fields)} fields, "
            f"API: {len(self.api_fields)} fields, "
            f"ORM: {len(self.orm_fields)} fields, "
            f"Errors: {len(self.errors)}, "
            f"Warnings: {len(self.warnings)}"
        )


def get_domain_fields(domain_class: Type) -> Set[str]:
    """Extract field names from domain class (Entity, dataclass, or attrs)."""
    fields = set()
    
    # Check if it's an attrs class
    try:
        import attrs
        if attrs.has(domain_class):
            # Handle attrs classes
            attrs_fields = attrs.fields(domain_class)
            for attr_field in attrs_fields:
                # Exclude private fields
                if not attr_field.name.startswith('_'):
                    fields.add(attr_field.name)
            return fields
    except ImportError:
        pass
    
    if is_dataclass(domain_class):
        # Handle dataclass fields
        for field in dataclass_fields(domain_class):
            # Exclude private fields
            if not field.name.startswith('_'):
                fields.add(field.name)
    elif hasattr(domain_class, '__init__'):
        # Handle Entity classes by inspecting __init__ signature
        sig = inspect.signature(domain_class.__init__)
        for param_name in sig.parameters:
            # Exclude 'self' and private fields
            if param_name != 'self' and not param_name.startswith('_'):
                fields.add(param_name)
    
    # Also check properties (but filter out common inherited ones)
    for name in dir(domain_class):
        if (not name.startswith('_') and 
            isinstance(getattr(domain_class, name, None), property) and
            name not in {'events', 'domain_events'}):  # Exclude event-related properties
            fields.add(name)
    
    return fields


def get_api_fields(api_class: Type[BaseApiModel]) -> Set[str]:
    """Extract field names from API schema (Pydantic model)."""
    if not issubclass(api_class, BaseModel):
        raise ValueError(f"{api_class} is not a Pydantic model")
    
    return set(api_class.model_fields.keys())


def get_orm_fields(orm_class: Type[SaBase]) -> Set[str]:
    """Extract field names from ORM model (SQLAlchemy)."""
    if not issubclass(orm_class, DeclarativeBase):
        raise ValueError(f"{orm_class} is not a SQLAlchemy model")
    
    # Use SQLAlchemy inspector to get column names
    mapper = sa_inspect(orm_class)
    fields = set()
    
    # Get column names
    for column in mapper.columns:
        fields.add(column.name)
    
    # Get relationship names
    for relationship in mapper.relationships:
        fields.add(relationship.key)
    
    # Get composite names (like nutri_facts)
    for composite in mapper.composites:
        # Add the composite attribute key itself (e.g. "nutri_facts")
        fields.add(composite.key)

        # Attempt to extract sub-field names from the composite class so that
        # API schemas that expose the individual attributes (e.g. "calories")
        # are recognised as being present in the ORM model even though they are
        # stored inside a composite value-object.
        try:
            composite_cls = getattr(composite, "composite_class", None)
            if composite_cls is None:
                # SQLAlchemy <2.0 uses .class_ attribute instead of composite_class
                composite_cls = getattr(composite, "class_", None)
            if composite_cls is not None:
                # Re-use the domain-field extractor for maximum coverage. This
                # handles dataclasses, attrs classes, and conventional Python
                # value objects.
                sub_fields = get_domain_fields(composite_cls)
                fields.update(sub_fields)
        except Exception as exc:
            # Do not fail hard if reflection of the composite class fails –
            # simply log and continue. Failing would break the validator for
            # legitimate models that use exotic composite types.
            logger.debug("Could not introspect composite %s: %s", composite.key, exc)

    return fields


def compare_field_sets(
    domain_fields: Set[str], 
    api_fields: Set[str], 
    orm_fields: Set[str],
    result: SchemaSyncResult
) -> None:
    """Compare field sets and populate result with errors/warnings."""
    
    # Fields that should typically be excluded from comparison
    excluded_fields = {
        'events', 'domain_events', '_events',  # Domain event fields
        'preprocessed_name',  # ORM-specific search fields
        'total_time',  # Computed fields in ORM
        'model_config',  # Pydantic config
        '__table_args__', '__tablename__',  # SQLAlchemy metadata
    }
    
    # Remove excluded fields
    domain_fields = domain_fields - excluded_fields
    api_fields = api_fields - excluded_fields  
    orm_fields = orm_fields - excluded_fields
    
    # Identify read-only computed properties in the domain model (those defined
    # with @property and without a corresponding setter).
    computed_props = {
        name for name in domain_fields
        if isinstance(getattr(result.domain_class, name, None), property)
        and getattr(result.domain_class, name).fset is None
    }

    # Exclude *only* those computed props that are NOT represented in the API
    # schema. Computed props that *are* present in the API should still be
    # considered for symmetry checks.
    domain_fields_for_api_compare = domain_fields - (computed_props - api_fields)

    # Find missing fields ------------------------------------------------------
    domain_only = domain_fields_for_api_compare - api_fields - orm_fields
    api_only = api_fields - domain_fields_for_api_compare - orm_fields
    orm_only = orm_fields - domain_fields_for_api_compare - api_fields

    # Domain-API mismatches
    missing_from_api = domain_fields_for_api_compare - api_fields
    missing_from_domain = api_fields - domain_fields_for_api_compare
    
    # API-ORM mismatches  
    missing_from_orm = api_fields - orm_fields
    missing_from_api_orm = orm_fields - api_fields
    
    # Report errors for critical mismatches
    if missing_from_api:
        result.errors.append(
            f"Domain fields missing from API: {sorted(missing_from_api)}"
        )
    
    if missing_from_domain:
        result.errors.append(
            f"API fields missing from Domain: {sorted(missing_from_domain)}"
        )
    
    # Report warnings for ORM differences (more acceptable)
    if missing_from_orm:
        result.warnings.append(
            f"API fields missing from ORM: {sorted(missing_from_orm)}"
        )
    
    if missing_from_api_orm:
        result.warnings.append(
            f"ORM fields missing from API: {sorted(missing_from_api_orm)}"
        )
    
    # Report orphaned fields
    if domain_only:
        result.warnings.append(
            f"Domain-only fields: {sorted(domain_only)}"
        )
    
    if api_only:
        result.warnings.append(
            f"API-only fields: {sorted(api_only)}"
        )
    
    if orm_only:
        result.warnings.append(
            f"ORM-only fields: {sorted(orm_only)}"
        )


def assert_schema_sync(
    domain_class: Type,
    api_class: Type[BaseApiModel],
    orm_class: Type[SaBase],
    strict: bool = True
) -> SchemaSyncResult:
    """
    Compare field names between Domain, API, and ORM classes.
    
    Args:
        domain_class: Domain entity or value object class
        api_class: API schema class (Pydantic model)
        orm_class: ORM model class (SQLAlchemy)
        strict: If True, treat warnings as errors
        
    Returns:
        SchemaSyncResult with validation results
        
    Raises:
        AssertionError: If validation fails and strict=True
    """
    result = SchemaSyncResult(domain_class, api_class, orm_class)
    
    try:
        # Extract field names from each class
        result.domain_fields = get_domain_fields(domain_class)
        result.api_fields = get_api_fields(api_class)
        result.orm_fields = get_orm_fields(orm_class)
        
        # Compare field sets
        compare_field_sets(
            result.domain_fields, 
            result.api_fields, 
            result.orm_fields,
            result
        )
        
        # Log results
        logger.info(
            f"Schema sync check: {domain_class.__name__} -> "
            f"{api_class.__name__} -> {orm_class.__name__}: {result.summary}"
        )
        
        if result.errors:
            logger.error(f"Schema sync errors: {result.errors}")
        if result.warnings:
            logger.warning(f"Schema sync warnings: {result.warnings}")
        
        # Assert if strict mode
        if strict and (result.errors or result.warnings):
            all_issues = result.errors + result.warnings
            raise AssertionError(
                f"Schema sync failed for {domain_class.__name__}: {all_issues}"
            )
        elif not strict and result.errors:
            raise AssertionError(
                f"Schema sync errors for {domain_class.__name__}: {result.errors}"
            )
            
    except AssertionError:
        # Re-raise AssertionError as-is (don't catch our own assertions)
        raise
    except Exception as e:
        result.errors.append(f"Validation failed: {str(e)}")
        if strict:
            raise
    
    return result


def discover_schema_triplets() -> List[Dict[str, Type]]:
    """
    Auto-discover Domain/API/ORM class triplets from the codebase.
    
    Returns:
        List of dictionaries with 'domain', 'api', 'orm' class mappings
    """
    triplets = []
    
    # This is a simplified discovery - in practice, you might need
    # more sophisticated mapping based on naming conventions
    # For now, we'll focus on the known exemplar case
    
    # Known exemplar triplet
    try:
        from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
        from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
        from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
        
        triplets.append({
            'domain': Meal,
            'api': ApiMeal,
            'orm': MealSaModel,
            'context': 'recipes_catalog.meal'
        })
    except ImportError as e:
        logger.warning(f"Could not import meal triplet: {e}")
    
    # TODO: Add more triplets as we discover them
    # This would typically involve scanning the file system
    # and mapping classes by naming conventions
    
    return triplets


# Test Suite
class TestSchemaSynchronization:
    """Test suite for schema synchronization validation."""
    
    @pytest.fixture
    def exemplar_triplet(self):
        """Provide the exemplar Meal triplet for testing."""
        try:
            from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
            from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
            from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
            
            return {
                'domain': Meal,
                'api': ApiMeal,
                'orm': MealSaModel,
                'context': 'recipes_catalog.meal'
            }
        except ImportError:
            pytest.skip("Meal triplet classes not available")
    
    def test_get_domain_fields(self, exemplar_triplet):
        """Test extraction of domain fields."""
        domain_class = exemplar_triplet['domain']
        fields = get_domain_fields(domain_class)
        
        # Check that basic expected fields are present
        expected_fields = {'id', 'name', 'author_id', 'description', 'like'}
        assert expected_fields.issubset(fields)
        
        # Check that we get a reasonable number of fields
        assert len(fields) > 10  # Meal should have many fields
        
    def test_get_api_fields(self, exemplar_triplet):
        """Test extraction of API fields."""
        api_class = exemplar_triplet['api']
        fields = get_api_fields(api_class)
        
        # Check that basic expected fields are present
        expected_fields = {'id', 'name', 'author_id', 'description', 'like'}
        assert expected_fields.issubset(fields)
        
        # Check that we get a reasonable number of fields
        assert len(fields) > 10  # ApiMeal should have many fields
        
    def test_get_orm_fields(self, exemplar_triplet):
        """Test extraction of ORM fields."""
        orm_class = exemplar_triplet['orm']
        fields = get_orm_fields(orm_class)
        
        # Check that basic expected fields are present
        expected_fields = {'id', 'name', 'author_id', 'description', 'like'}
        assert expected_fields.issubset(fields)
        
        # Check that we get a reasonable number of fields
        assert len(fields) > 10  # MealSaModel should have many fields
        
    def test_schema_sync_validation_non_strict(self, exemplar_triplet):
        """Test schema sync validation in non-strict mode."""
        result = assert_schema_sync(
            domain_class=exemplar_triplet['domain'],
            api_class=exemplar_triplet['api'],
            orm_class=exemplar_triplet['orm'],
            strict=False  # Allow warnings
        )
        
        # Should complete without raising exceptions
        assert isinstance(result, SchemaSyncResult)
        assert result.domain_fields
        assert result.api_fields
        assert result.orm_fields
        
        # Log the results for inspection
        print(f"Domain fields: {sorted(result.domain_fields)}")
        print(f"API fields: {sorted(result.api_fields)}")
        print(f"ORM fields: {sorted(result.orm_fields)}")
        if result.errors:
            print(f"Errors: {result.errors}")
        if result.warnings:
            print(f"Warnings: {result.warnings}")
            
    @pytest.mark.parametrize("triplet", discover_schema_triplets())
    def test_all_discovered_triplets_sync(self, triplet):
        """Test that all discovered schema triplets are in sync."""
        # Use non-strict mode initially to discover patterns
        result = assert_schema_sync(
            domain_class=triplet['domain'],
            api_class=triplet['api'],
            orm_class=triplet['orm'],
            strict=False  # Allow warnings for now
        )
        
        # Report detailed field-level differences
        if result.errors or result.warnings:
            context = triplet.get('context', 'unknown')
            print(f"\n=== Schema Sync Report for {context} ===")
            print(f"Domain: {triplet['domain'].__name__}")
            print(f"API: {triplet['api'].__name__}")
            print(f"ORM: {triplet['orm'].__name__}")
            print(f"Summary: {result.summary}")
            
            if result.errors:
                print("ERRORS:")
                for error in result.errors:
                    print(f"  - {error}")
                    
            if result.warnings:
                print("WARNINGS:")
                for warning in result.warnings:
                    print(f"  - {warning}")
                    
        # For now, only fail on errors (not warnings)
        assert result.is_valid, f"Schema sync errors found: {result.errors}"
        
    def test_schema_sync_result_properties(self, exemplar_triplet):
        """Test SchemaSyncResult properties and methods."""
        result = SchemaSyncResult(
            domain_class=exemplar_triplet['domain'],
            api_class=exemplar_triplet['api'],
            orm_class=exemplar_triplet['orm']
        )
        
        # Test initial state
        assert result.is_valid  # No errors initially
        assert "0 fields" in result.summary  # Empty initially
        
        # Add some test data
        result.domain_fields = {'field1', 'field2'}
        result.api_fields = {'field1', 'field2'}
        result.orm_fields = {'field1', 'field2'}
        result.warnings.append("Test warning")
        
        assert result.is_valid  # Still valid with warnings
        assert "2 fields" in result.summary
        
        # Add error
        result.errors.append("Test error")
        assert not result.is_valid  # Invalid with errors 

    def test_schema_sync_detects_mismatch(self):
        """Ensure validator detects mismatches across Domain/API/ORM layers."""

        from dataclasses import dataclass, fields as dataclass_fields
        from sqlalchemy import String, Float
        from sqlalchemy.orm import mapped_column, composite

        from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiModel
        from src.db.base import SaBase

        # ------------------ Shared composite type ---------------------------
        @dataclass
        class NutriFactsComposite:
            calories: float | None = None
            protein: float | None = None

        # ------------------ Domain model -----------------------------------
        class DummyDomain:
            """Mimics a rich domain entity with computed props."""

            def __init__(self, id: str, name: str, weight_in_grams: int, nutri_facts: NutriFactsComposite):
                self.id = id
                self.name = name
                self.weight_in_grams = weight_in_grams
                self.nutri_facts = nutri_facts
                self.only_domain = "domain_specific"  # Domain-only field

            # Computed read-only properties (should be discovered by validator)
            @property
            def calorie_density(self) -> float | None:
                if not self.nutri_facts or self.nutri_facts.calories is None:
                    return None
                return (self.nutri_facts.calories / self.weight_in_grams) * 100

        # ------------------ API schema -------------------------------------
        class DummyApi(BaseApiModel):
            """API schema exposing both normal & computed attributes."""

            id: str
            name: str
            weight_in_grams: int
            calorie_density: float | None  # Mirrors domain computed property
            only_api: str  # API-only field

        # ------------------ ORM model --------------------------------------
        class DummyOrm(SaBase):
            __tablename__ = "dummy"

            # Scalar columns that directly match domain fields
            id = mapped_column(String, primary_key=True)
            name = mapped_column(String)
            weight_in_grams = mapped_column(Float)

            # Store calorie_density as a materialised column (not computed)
            calorie_density = mapped_column(Float)

            # Composite column storing nutri_facts components
            nutri_facts: Mapped[NutriFactsComposite] = composite(
                *[
                    mapped_column(field.name, Float)
                    for field in dataclass_fields(NutriFactsComposite)
                ],
            )

            # An ORM-only field
            only_orm = mapped_column(String)

        # -------------------------------------------------------------------
        # The schema sync in *strict* mode should raise because of
        # the intentionally introduced layer-specific fields.
        with pytest.raises(AssertionError):
            assert_schema_sync(DummyDomain, DummyApi, DummyOrm, strict=True)

    @pytest.mark.parametrize("scenario,expected_behavior", [
        # Scenario 1: Happy path - Scalar + Scalar + Scalar
        ("happy_path", "pass"),
        
        # Scenario 2: Computed in Domain only (should be ignored)
        ("computed_domain_only", "pass"),
        
        # Scenario 3: Computed in Domain, materialised in API but not in ORM
        ("computed_domain_materialised_api_missing_orm", "warning"),  # API missing from ORM = warning
        
        # Scenario 6: Field exists in ORM only
        ("orm_only_field", "warning"),
        
        # Scenario 8: Composite in ORM, composite object in Domain, API lacks both
        ("composite_orm_domain_missing_api", "error"),  # Domain missing from API = error
        
        # Scenario 9: Composite in ORM, but Domain has no matching attribute
        ("composite_orm_missing_domain", "warning"),
        
        # Scenario 10: Composite in ORM, Domain holds materialised scalar attrs, API follows Domain
        ("composite_orm_scalar_domain_api", "warning"),  # Composite key will be missing from API = warning
    ])
    def test_schema_sync_mismatch_scenarios(self, scenario, expected_behavior):
        """Test specific mismatch scenarios with expected behaviors."""
        
        from dataclasses import dataclass, fields as dataclass_fields
        from sqlalchemy import String, Float, Integer
        from sqlalchemy.orm import mapped_column, composite, Mapped
        from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiModel
        from src.db.base import SaBase

        # Shared composite type
        @dataclass
        class TestComposite:
            value_a: float | None = None
            value_b: float | None = None

        if scenario == "happy_path":
            # Scenario 1: All layers have matching scalar fields
            class HappyDomain:
                def __init__(self, id: str, name: str, score: float):
                    self.id = id
                    self.name = name
                    self.score = score

            class HappyApi(BaseApiModel):
                id: str
                name: str
                score: float

            class HappyOrm(SaBase):
                __tablename__ = "test_happy_path"
                id = mapped_column(String, primary_key=True)
                name = mapped_column(String)
                score = mapped_column(Float)

            Domain, Api, Orm = HappyDomain, HappyApi, HappyOrm

        elif scenario == "computed_domain_only":
            # Scenario 2: Domain has computed property, others don't
            class ComputedDomain:
                def __init__(self, id: str, base_value: float):
                    self.id = id
                    self.base_value = base_value

                @property
                def computed_value(self) -> float:
                    return self.base_value * 2

            class ComputedApi(BaseApiModel):
                id: str
                base_value: float

            class ComputedOrm(SaBase):
                __tablename__ = "test_computed_only"
                id = mapped_column(String, primary_key=True)
                base_value = mapped_column(Float)

            Domain, Api, Orm = ComputedDomain, ComputedApi, ComputedOrm

        elif scenario == "computed_domain_materialised_api_missing_orm":
            # Scenario 3: Domain computed, API materialised, ORM missing
            class MaterialisedDomain:
                def __init__(self, id: str, base_value: float):
                    self.id = id
                    self.base_value = base_value

                @property
                def computed_value(self) -> float:
                    return self.base_value * 2

            class MaterialisedApi(BaseApiModel):
                id: str
                base_value: float
                computed_value: float  # Materialised in API

            class MaterialisedOrm(SaBase):
                __tablename__ = "test_computed_api_missing_orm"
                id = mapped_column(String, primary_key=True)
                base_value = mapped_column(Float)
                # computed_value is missing from ORM

            Domain, Api, Orm = MaterialisedDomain, MaterialisedApi, MaterialisedOrm

        elif scenario == "orm_only_field":
            # Scenario 6: Field exists in ORM only
            class OrmOnlyDomain:
                def __init__(self, id: str, name: str):
                    self.id = id
                    self.name = name

            class OrmOnlyApi(BaseApiModel):
                id: str
                name: str

            class OrmOnlyOrm(SaBase):
                __tablename__ = "test_orm_only"
                id = mapped_column(String, primary_key=True)
                name = mapped_column(String)
                orm_only_field = mapped_column(String)  # Only in ORM

            Domain, Api, Orm = OrmOnlyDomain, OrmOnlyApi, OrmOnlyOrm

        elif scenario == "composite_orm_domain_missing_api":
            # Scenario 8: Composite in ORM and Domain, API lacks both composite & sub-attrs
            class CompositeMissingApiDomain:
                def __init__(self, id: str, composite_data: TestComposite):
                    self.id = id
                    self.composite_data = composite_data

            class CompositeMissingApiApi(BaseApiModel):
                id: str
                # Missing both composite_data and its sub-fields

            class CompositeMissingApiOrm(SaBase):
                __tablename__ = "test_composite_missing_api"
                id = mapped_column(String, primary_key=True)
                composite_data: Mapped[TestComposite] = composite(
                    *[mapped_column(field.name, Float) for field in dataclass_fields(TestComposite)]
                )

            Domain, Api, Orm = CompositeMissingApiDomain, CompositeMissingApiApi, CompositeMissingApiOrm

        elif scenario == "composite_orm_missing_domain":
            # Scenario 9: Composite in ORM, but Domain has no matching attribute
            class CompositeMissingDomainDomain:
                def __init__(self, id: str, name: str):
                    self.id = id
                    self.name = name
                    # Missing composite_data

            class CompositeMissingDomainApi(BaseApiModel):
                id: str
                name: str

            class CompositeMissingDomainOrm(SaBase):
                __tablename__ = "test_composite_missing_domain"
                id = mapped_column(String, primary_key=True)
                name = mapped_column(String)
                composite_data: Mapped[TestComposite] = composite(
                    *[mapped_column(field.name, Float) for field in dataclass_fields(TestComposite)]
                )

            Domain, Api, Orm = CompositeMissingDomainDomain, CompositeMissingDomainApi, CompositeMissingDomainOrm

        elif scenario == "composite_orm_scalar_domain_api":
            # Scenario 10: Composite in ORM, Domain holds materialised scalar attrs, API follows Domain
            class CompositeScalarDomain:
                def __init__(self, id: str, value_a: float, value_b: float):
                    self.id = id
                    self.value_a = value_a  # Materialised scalar
                    self.value_b = value_b  # Materialised scalar

            class CompositeScalarApi(BaseApiModel):
                id: str
                value_a: float  # Following Domain's scalar approach
                value_b: float

            class CompositeScalarOrm(SaBase):
                __tablename__ = "test_composite_scalar_domain"
                id = mapped_column(String, primary_key=True)
                composite_data: Mapped[TestComposite] = composite(
                    *[mapped_column(field.name, Float) for field in dataclass_fields(TestComposite)]
                )

            Domain, Api, Orm = CompositeScalarDomain, CompositeScalarApi, CompositeScalarOrm

        # Run the validation and check expected behavior
        if expected_behavior == "pass":
            # Should not raise any exceptions
            result = assert_schema_sync(Domain, Api, Orm, strict=False)
            assert result.is_valid, f"Expected {scenario} to pass but got errors: {result.errors}"
            assert len(result.warnings) == 0, f"Expected {scenario} to have no warnings but got: {result.warnings}"
            
        elif expected_behavior == "warning":
            # Should pass in non-strict mode but have warnings
            result = assert_schema_sync(Domain, Api, Orm, strict=False)
            assert result.is_valid, f"Expected {scenario} to be valid (warnings only) but got errors: {result.errors}"
            assert len(result.warnings) > 0, f"Expected {scenario} to have warnings but got none"
            
            # Should fail in strict mode due to warnings
            with pytest.raises(AssertionError):
                assert_schema_sync(Domain, Api, Orm, strict=True)
                
        elif expected_behavior == "error":
            # Should fail even in non-strict mode due to errors
            with pytest.raises(AssertionError):
                assert_schema_sync(Domain, Api, Orm, strict=False)

    def test_schema_sync_excluded_fields(self):
        """Test that excluded/internal fields are properly filtered out."""
        
        from sqlalchemy import String
        from sqlalchemy.orm import mapped_column
        from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiModel
        from src.db.base import SaBase

        class ExcludedDomain:
            def __init__(self, id: str, name: str):
                self.id = id
                self.name = name
                self.events = []  # Should be excluded
                self._events = []  # Should be excluded

        class ExcludedApi(BaseApiModel):
            id: str
            name: str
            model_config = {"extra": "forbid"}  # Should be excluded

        class ExcludedOrm(SaBase):
            __tablename__ = "test_excluded"
            __table_args__ = {'schema': 'test'}  # Should be excluded
            
            id = mapped_column(String, primary_key=True)
            name = mapped_column(String)
            preprocessed_name = mapped_column(String)  # Should be excluded

        # Should pass - excluded fields shouldn't cause mismatches
        result = assert_schema_sync(ExcludedDomain, ExcludedApi, ExcludedOrm, strict=True)
        assert result.is_valid

    def test_schema_sync_computed_properties_with_setters(self):
        """Test that computed properties with setters are handled correctly."""
        
        from sqlalchemy import String, Float
        from sqlalchemy.orm import mapped_column
        from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiModel
        from src.db.base import SaBase

        class SetterDomain:
            def __init__(self, id: str, _temperature: float):
                self.id = id
                self._temperature = _temperature

            @property
            def temperature(self) -> float:
                return self._temperature

            @temperature.setter
            def temperature(self, value: float):
                self._temperature = value

        class SetterApi(BaseApiModel):
            id: str
            temperature: float  # Property with setter should be included

        class SetterOrm(SaBase):
            __tablename__ = "test_computed_setter"
            id = mapped_column(String, primary_key=True)
            temperature = mapped_column(Float)

        # Should pass - properties with setters should be treated as regular fields
        result = assert_schema_sync(SetterDomain, SetterApi, SetterOrm, strict=True)
        assert result.is_valid 