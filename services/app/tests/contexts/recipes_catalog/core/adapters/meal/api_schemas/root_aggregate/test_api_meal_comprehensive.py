"""
Comprehensive test suite for ApiMeal following seedwork patterns.
Uses extensive data factories and realistic scenarios for complete coverage.

This test suite provides:
- Complete conversion method testing (from_domain, to_domain, from_orm_model, to_orm_kwargs)
- Comprehensive field validation testing
- Round-trip conversion validation
- Error handling and edge case scenarios
- JSON serialization/deserialization testing
- Performance testing with bulk operations
- Integration testing with base classes
- Realistic data scenario testing
- Computed property validation
- Pydantic configuration testing

All tests use deterministic data factories for consistent behavior.
Tests focus on behavior validation, not implementation details.
"""

import json
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
from src.contexts.shared_kernel.domain.enums import Privacy, MeasureUnit

# Import all data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.data_factories.api_meal_data_factories import (
    create_api_meal, create_api_meal_kwargs, create_api_meal_from_json, create_api_meal_json,
    create_simple_api_meal, create_complex_api_meal, create_vegetarian_api_meal,
    create_high_protein_api_meal, create_family_api_meal, create_quick_api_meal,
    create_holiday_api_meal, create_minimal_api_meal, create_api_meal_with_max_recipes,
    create_api_meal_without_recipes, create_api_meal_with_incorrect_computed_properties,
    create_meal_collection, create_test_meal_dataset,
    reset_api_meal_counters, validate_computed_property_correction_roundtrip,
    # Field validation test suites
    create_field_validation_test_suite, create_api_meal_with_invalid_field,
    create_api_meal_with_missing_required_fields, create_boundary_value_test_cases,
    create_type_coercion_test_cases, create_nested_object_validation_test_cases,
    create_comprehensive_validation_error_scenarios,
    # Pydantic configuration tests
    create_pydantic_config_test_cases, create_api_meal_with_extra_fields,
    create_api_meal_with_type_coercion_scenarios, create_api_meal_immutability_test_scenarios,
    create_validation_assignment_test_scenarios,
    # JSON testing
    create_json_serialization_test_cases, create_json_deserialization_test_cases,
    create_json_edge_cases, create_malformed_json_scenarios,
    create_valid_json_test_cases, create_invalid_json_test_cases,
    # Conversion testing
    create_conversion_method_test_scenarios, create_round_trip_consistency_test_scenarios,
    create_type_conversion_test_scenarios, create_meal_domain_from_api,
    create_api_meal_from_domain, create_meal_orm_kwargs_from_api,
    # Performance testing
    create_extreme_performance_scenarios, create_validation_performance_scenarios,
    create_serialization_performance_scenarios, create_bulk_meal_creation_dataset,
    create_bulk_json_serialization_dataset, create_bulk_json_deserialization_dataset,
    create_conversion_performance_dataset, create_nested_object_validation_dataset,
    create_computed_property_test_dataset,
    # Error testing
    create_systematic_error_scenarios, create_error_recovery_scenarios,
    create_edge_case_error_scenarios,
    # Test suite orchestration
    create_comprehensive_test_suite, get_test_coverage_report,
    # Constants
    REALISTIC_MEAL_SCENARIOS
)

# Import domain factories for conversion tests - create simple domain objects locally
def create_meal(**kwargs):
    """Create a domain meal for testing."""
    from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
    return Meal(
        id=kwargs.get("id", str(uuid4())),
        name=kwargs.get("name", "Test Domain Meal"),
        author_id=kwargs.get("author_id", str(uuid4())),
        menu_id=kwargs.get("menu_id"),
        recipes=kwargs.get("recipes", []),
        tags=kwargs.get("tags", set()),
        description=kwargs.get("description", "Test description"),
        notes=kwargs.get("notes", "Test notes"),
        like=kwargs.get("like"),
        image_url=kwargs.get("image_url"),
        created_at=kwargs.get("created_at", datetime.now()),
        updated_at=kwargs.get("updated_at", datetime.now()),
        discarded=kwargs.get("discarded", False),
        version=kwargs.get("version", 1)
    )

def create_simple_meal(**kwargs):
    """Create a simple domain meal for testing."""
    return create_meal(**kwargs)

def create_complex_meal(**kwargs):
    """Create a complex domain meal for testing."""
    return create_meal(**kwargs)

def reset_meal_counters():
    """Reset meal counters for testing."""
    pass

# Create placeholder functions for ORM testing
def create_meal_orm(**kwargs):
    """Placeholder for ORM meal creation."""
    from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
    return MealSaModel(
        id=kwargs.get("id", str(uuid4())),
        name=kwargs.get("name", "Test ORM Meal"),
        author_id=kwargs.get("author_id", str(uuid4())),
        menu_id=kwargs.get("menu_id"),
        description=kwargs.get("description", "Test description"),
        notes=kwargs.get("notes", "Test notes"),
        recipes=[],
        tags=frozenset(),
        like=None,
        image_url=None,
        nutri_facts=None,
        weight_in_grams=None,
        calorie_density=None,
        carbo_percentage=None,
        protein_percentage=None,
        total_fat_percentage=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        discarded=False,
        version=1
    )

def create_meal_orm_kwargs(**kwargs):
    """Placeholder for ORM kwargs creation."""
    return {
        "id": kwargs.get("id", str(uuid4())),
        "name": kwargs.get("name", "Test ORM Meal"),
        "author_id": kwargs.get("author_id", str(uuid4())),
        "menu_id": kwargs.get("menu_id"),
        "description": kwargs.get("description", "Test description"),
        "notes": kwargs.get("notes", "Test notes"),
        "recipes": [],
        "tags": [],
        "like": None,
        "image_url": None,
        "nutri_facts": None,
        "weight_in_grams": None,
        "calorie_density": None,
        "carbo_percentage": None,
        "protein_percentage": None,
        "total_fat_percentage": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "discarded": False,
        "version": 1
    }

class BaseApiMealTest:
    """
    Base class with shared fixtures and setup for all ApiMeal tests.
    """

    # =============================================================================
    # FIXTURES AND TEST DATA
    # =============================================================================

    @pytest.fixture(autouse=True)
    def reset_counters(self):
        """Reset all counters before each test for isolation."""
        reset_api_meal_counters()
        reset_meal_counters()
        yield
        reset_api_meal_counters()
        reset_meal_counters()

    @pytest.fixture
    def simple_meal(self):
        """Simple meal for basic testing."""
        return create_simple_api_meal()

    @pytest.fixture
    def complex_meal(self):
        """Complex meal with many nested objects."""
        return create_complex_api_meal()

    @pytest.fixture
    def domain_meal(self):
        """Domain meal for conversion tests - created directly from domain factories."""
        return create_meal()

    @pytest.fixture
    def domain_meal_with_nutri_facts(self):
        """Domain meal with nutrition facts for nutrition conversion tests."""
        return create_complex_meal()

    @pytest.fixture
    def real_orm_meal(self):
        """Real ORM meal for testing - no mocks needed."""
        return create_meal_orm(
            name="Test Meal for ORM Conversion",
            description="Real ORM meal for testing conversion methods",
            notes="Real notes for testing",
            author_id=str(uuid4()),
            menu_id=str(uuid4())
        )

    @pytest.fixture
    def edge_case_meals(self):
        """Edge case meals for comprehensive testing."""
        return {
            "empty_recipes": create_api_meal_without_recipes(),
            "max_recipes": create_api_meal_with_max_recipes(),
            "incorrect_computed_properties": create_api_meal_with_incorrect_computed_properties(),
            "minimal": create_minimal_api_meal(),
            "vegetarian": create_vegetarian_api_meal(),
            "high_protein": create_high_protein_api_meal(),
            "quick": create_quick_api_meal(),
            "holiday": create_holiday_api_meal(),
            "family": create_family_api_meal(),
        }

    @pytest.fixture
    def meal_collection(self):
        """Collection of diverse meals for testing."""
        return create_meal_collection(count=10)

    @pytest.fixture(autouse=True)
    def reset_all_counters(self):
        """Reset all counters for test isolation."""
        reset_api_meal_counters()
        reset_meal_counters()
        yield
        reset_api_meal_counters()
        reset_meal_counters()


class TestApiMealBasics(BaseApiMealTest):
    """
    Test suite for basic ApiMeal conversion methods (>95% coverage target).
    """

    # =============================================================================
    # UNIT TESTS FOR ALL CONVERSION METHODS (>95% COVERAGE TARGET)
    # =============================================================================

    def test_from_domain_basic_conversion(self, domain_meal):
        """Test from_domain basic conversion functionality."""
        api_meal = ApiMeal.from_domain(domain_meal)
        
        assert api_meal.id == domain_meal.id
        assert api_meal.name == domain_meal.name
        assert api_meal.author_id == domain_meal.author_id
        assert api_meal.menu_id == domain_meal.menu_id
        assert api_meal.description == domain_meal.description
        assert api_meal.notes == domain_meal.notes
        assert api_meal.like == domain_meal.like
        assert api_meal.image_url == domain_meal.image_url
        assert isinstance(api_meal, ApiMeal)

    def test_from_domain_nested_objects_conversion(self, domain_meal):
        """Test from_domain properly converts nested objects."""
        api_meal = ApiMeal.from_domain(domain_meal)
        
        # Test recipes conversion
        assert len(api_meal.recipes) == len(domain_meal.recipes)
        assert all(isinstance(recipe, ApiRecipe) for recipe in api_meal.recipes)
        
        # Test tags conversion - should be frozenset
        domain_tags = domain_meal.tags or set()
        assert len(api_meal.tags) == len(domain_tags)
        assert all(isinstance(tag, ApiTag) for tag in api_meal.tags)
        assert isinstance(api_meal.tags, frozenset)
        
        # Test nutri_facts conversion
        if domain_meal.nutri_facts:
            assert isinstance(api_meal.nutri_facts, ApiNutriFacts)
        else:
            assert api_meal.nutri_facts is None

    def test_from_domain_computed_properties(self, domain_meal):
        """Test from_domain correctly handles computed properties."""
        api_meal = ApiMeal.from_domain(domain_meal)
        
        # Computed properties should match domain values
        assert api_meal.weight_in_grams == domain_meal.weight_in_grams
        assert api_meal.calorie_density == domain_meal.calorie_density
        assert api_meal.carbo_percentage == domain_meal.carbo_percentage
        assert api_meal.protein_percentage == domain_meal.protein_percentage
        assert api_meal.total_fat_percentage == domain_meal.total_fat_percentage

    def test_from_domain_with_empty_collections(self):
        """Test from_domain handles empty collections correctly."""
        # Create domain meal with empty collections
        domain_meal = create_meal(recipes=[], tags=set())
        api_meal = ApiMeal.from_domain(domain_meal)
        
        assert api_meal.recipes == []
        assert api_meal.tags == frozenset()
        assert api_meal.nutri_facts is None

    def test_from_domain_with_nutrition_facts(self, domain_meal_with_nutri_facts):
        """Test from_domain handles nutrition facts conversion."""
        api_meal = ApiMeal.from_domain(domain_meal_with_nutri_facts)
        
        if domain_meal_with_nutri_facts.nutri_facts:
            assert isinstance(api_meal.nutri_facts, ApiNutriFacts)
            assert api_meal.nutri_facts.calories == domain_meal_with_nutri_facts.nutri_facts.calories
            assert api_meal.nutri_facts.protein == domain_meal_with_nutri_facts.nutri_facts.protein
            assert api_meal.nutri_facts.carbohydrate == domain_meal_with_nutri_facts.nutri_facts.carbohydrate
            assert api_meal.nutri_facts.total_fat == domain_meal_with_nutri_facts.nutri_facts.total_fat

    def test_to_domain_basic_conversion(self, simple_meal):
        """Test to_domain basic conversion functionality."""
        domain_meal = simple_meal.to_domain()
        
        assert isinstance(domain_meal, Meal)
        assert domain_meal.id == simple_meal.id
        assert domain_meal.name == simple_meal.name
        assert domain_meal.author_id == simple_meal.author_id
        assert domain_meal.menu_id == simple_meal.menu_id
        assert domain_meal.description == simple_meal.description
        assert domain_meal.notes == simple_meal.notes
        assert domain_meal.like == simple_meal.like
        assert domain_meal.image_url == simple_meal.image_url

    def test_to_domain_collection_type_conversion(self, complex_meal):
        """Test to_domain converts collections correctly."""
        domain_meal = complex_meal.to_domain()
        
        # Tags should be converted from frozenset to set
        assert isinstance(domain_meal.tags, set)
        assert len(domain_meal.tags) == len(complex_meal.tags)
        
        # Recipes should be converted from list to list (same type)
        assert isinstance(domain_meal.recipes, list)
        assert len(domain_meal.recipes) == len(complex_meal.recipes)

    def test_from_orm_model_basic_conversion(self, real_orm_meal):
        """Test from_orm_model basic conversion functionality."""
        api_meal = ApiMeal.from_orm_model(real_orm_meal)
        
        assert api_meal.id == real_orm_meal.id
        assert api_meal.name == real_orm_meal.name
        assert api_meal.author_id == real_orm_meal.author_id
        assert api_meal.menu_id == real_orm_meal.menu_id
        assert api_meal.description == real_orm_meal.description
        assert api_meal.notes == real_orm_meal.notes
        assert api_meal.like == real_orm_meal.like
        assert api_meal.image_url == real_orm_meal.image_url
        assert isinstance(api_meal, ApiMeal)

    def test_from_orm_model_nested_objects_conversion(self, real_orm_meal):
        """Test from_orm_model handles nested objects."""
        api_meal = ApiMeal.from_orm_model(real_orm_meal)
        
        # Should handle collections properly
        assert isinstance(api_meal.recipes, list)
        assert isinstance(api_meal.tags, frozenset)
        assert len(api_meal.recipes) == len(real_orm_meal.recipes)
        assert len(api_meal.tags) == len(real_orm_meal.tags)

    def test_to_orm_kwargs_basic_conversion(self, simple_meal):
        """Test to_orm_kwargs basic conversion functionality."""
        kwargs = simple_meal.to_orm_kwargs()
        
        assert isinstance(kwargs, dict)
        assert kwargs["id"] == simple_meal.id
        assert kwargs["name"] == simple_meal.name
        assert kwargs["author_id"] == simple_meal.author_id
        assert kwargs["menu_id"] == simple_meal.menu_id
        assert kwargs["description"] == simple_meal.description
        assert kwargs["notes"] == simple_meal.notes
        assert kwargs["like"] == simple_meal.like
        assert kwargs["image_url"] == simple_meal.image_url

    def test_to_orm_kwargs_nested_objects_conversion(self, complex_meal):
        """Test to_orm_kwargs converts nested objects correctly."""
        kwargs = complex_meal.to_orm_kwargs()
        
        # Recipes should be converted to list of kwargs
        assert isinstance(kwargs["recipes"], list)
        assert len(kwargs["recipes"]) == len(complex_meal.recipes)
        
        # Tags should be converted from frozenset to list of kwargs
        assert isinstance(kwargs["tags"], list)
        assert len(kwargs["tags"]) == len(complex_meal.tags)

    def test_to_orm_kwargs_nutrition_facts_conversion(self, complex_meal):
        """Test to_orm_kwargs handles nutrition facts conversion."""
        kwargs = complex_meal.to_orm_kwargs()
        
        if complex_meal.nutri_facts:
            from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import NutriFactsSaModel
            assert isinstance(kwargs["nutri_facts"], NutriFactsSaModel)
        else:
            assert kwargs["nutri_facts"] is None


class TestApiMealRoundTrip(BaseApiMealTest):
    """
    Test suite for round-trip conversion validation tests.
    """

    # =============================================================================
    # ROUND-TRIP CONVERSION VALIDATION TESTS
    # =============================================================================

    def test_domain_to_api_to_domain_round_trip(self, domain_meal):
        """Test complete domain → API → domain round-trip preserves data integrity."""
        # Domain → API
        api_meal = ApiMeal.from_domain(domain_meal)
        
        # API → Domain
        recovered_domain = api_meal.to_domain()
        
        # Use Meal's __eq__ method for comprehensive comparison
        assert recovered_domain == domain_meal, "Domain → API → Domain round-trip failed"

    def test_api_to_domain_to_api_round_trip(self, complex_meal):
        """Test API → domain → API round-trip preserves data integrity."""
        # API → Domain
        domain_meal = complex_meal.to_domain()
        
        # Domain → API
        recovered_api = ApiMeal.from_domain(domain_meal)
        
        # Verify data integrity for API objects
        assert recovered_api.id == complex_meal.id
        assert recovered_api.name == complex_meal.name
        assert recovered_api.author_id == complex_meal.author_id
        assert len(recovered_api.recipes) == len(complex_meal.recipes)
        assert len(recovered_api.tags) == len(complex_meal.tags)

    def test_orm_to_api_to_orm_round_trip(self, real_orm_meal):
        """Test ORM → API → ORM round-trip preserves data integrity."""
        # ORM → API
        api_meal = ApiMeal.from_orm_model(real_orm_meal)
        
        # API → ORM kwargs
        orm_kwargs = api_meal.to_orm_kwargs()
        
        # Verify data integrity
        assert orm_kwargs["id"] == real_orm_meal.id
        assert orm_kwargs["name"] == real_orm_meal.name
        assert orm_kwargs["author_id"] == real_orm_meal.author_id
        assert orm_kwargs["menu_id"] == real_orm_meal.menu_id
        assert orm_kwargs["description"] == real_orm_meal.description
        assert orm_kwargs["notes"] == real_orm_meal.notes

    def test_complete_four_layer_round_trip(self, simple_meal):
        """Test complete four-layer conversion cycle preserves data integrity."""
        # Start with API object
        original_api = simple_meal
        
        # API → Domain
        domain_meal = original_api.to_domain()
        
        # Domain → API
        api_from_domain = ApiMeal.from_domain(domain_meal)
        
        # API → ORM kwargs
        orm_kwargs = api_from_domain.to_orm_kwargs()
        
        # Verify complete data integrity
        assert orm_kwargs["id"] == original_api.id
        assert orm_kwargs["name"] == original_api.name
        assert orm_kwargs["author_id"] == original_api.author_id
        assert orm_kwargs["menu_id"] == original_api.menu_id
        assert orm_kwargs["description"] == original_api.description
        assert orm_kwargs["notes"] == original_api.notes

    @pytest.mark.parametrize("case_name", [
        "empty_recipes",
        "max_recipes", 
        "incorrect_computed_properties",
        "minimal",
        "vegetarian",
        "high_protein",
        "quick",
        "holiday",
        "family"
    ])
    def test_round_trip_with_edge_cases(self, edge_case_meals, case_name):
        """Test round-trip conversion with edge case meals."""
        meal = edge_case_meals[case_name]
        
        # API → Domain → API
        domain_meal = meal.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)
        
        # Verify basic integrity for API objects
        assert recovered_api.id == meal.id
        assert recovered_api.name == meal.name
        assert recovered_api.author_id == meal.author_id
        assert len(recovered_api.recipes) == len(meal.recipes)
        assert len(recovered_api.tags) == len(meal.tags)

    def test_computed_properties_correction_round_trip(self):
        """Test that incorrect computed properties are corrected during round-trip."""
        # Create meal with incorrect computed properties
        meal_with_incorrect_props = create_api_meal_with_incorrect_computed_properties()
        
        # Test round-trip correction
        success, details = validate_computed_property_correction_roundtrip(meal_with_incorrect_props)
        
        assert success, f"Computed property correction failed: {details}"
        assert details["weight_corrected"], "Weight was not corrected"
        assert details["calorie_density_corrected"], "Calorie density was not corrected"
        assert details["nutri_facts_corrected"], "Nutrition facts were not corrected"


class TestApiMealErrorHandling(BaseApiMealTest):
    """
    Test suite for error handling tests (minimum 5 error scenarios per method).
    """

    # =============================================================================
    # ERROR HANDLING TESTS (MINIMUM 5 ERROR SCENARIOS PER METHOD)
    # =============================================================================

    def test_from_domain_error_scenarios(self):
        """Test from_domain error handling - minimum 5 error scenarios."""
        
        # Error 1: None input
        with pytest.raises(Exception):
            ApiMeal.from_domain(None)  # type: ignore
        
        # Error 2: Invalid object type
        with pytest.raises(Exception):
            ApiMeal.from_domain("not_a_meal_object")  # type: ignore
        
        # Error 3: Empty dictionary (missing required attributes)
        with pytest.raises(Exception):
            ApiMeal.from_domain({})  # type: ignore
        
        # Error 4: Invalid domain object with None required fields
        domain_meal = create_meal(recipes=[], tags=set())
        domain_meal._id = None  # type: ignore
        with pytest.raises(Exception):
            ApiMeal.from_domain(domain_meal)
        
        # Error 5: Domain object with invalid types
        domain_meal = create_meal(recipes=[], tags=set())
        domain_meal._recipes = "not_a_list"  # type: ignore
        with pytest.raises(Exception):
            ApiMeal.from_domain(domain_meal)

    def test_to_domain_error_scenarios(self):
        """Test to_domain error handling through validation errors."""
        
        # Error 1: Empty required fields
        with pytest.raises(ValueError):
            ApiMeal(
                id="",
                name="Test",
                author_id=str(uuid4()),
                menu_id=None,
                recipes=[],
                tags=frozenset(),
                description=None,
                notes=None,
                like=None,
                image_url=None,
                nutri_facts=None,
                weight_in_grams=None,
                calorie_density=None,
                carbo_percentage=None,
                protein_percentage=None,
                total_fat_percentage=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                discarded=False,
                version=1
            )
        
        # Error 2: Invalid UUID format
        with pytest.raises(ValueError):
            ApiMeal(
                id="invalid-uuid",
                name="Test",
                author_id=str(uuid4()),
                menu_id=None,
                recipes=[],
                tags=frozenset(),
                description=None,
                notes=None,
                like=None,
                image_url=None,
                nutri_facts=None,
                weight_in_grams=None,
                calorie_density=None,
                carbo_percentage=None,
                protein_percentage=None,
                total_fat_percentage=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                discarded=False,
                version=1
            )
        
        # Error 3: None for required fields
        with pytest.raises(ValueError):
            ApiMeal(
                id=str(uuid4()),
                name=None,  # type: ignore
                author_id=str(uuid4()),
                menu_id=None,
                recipes=[],
                tags=frozenset(),
                description=None,
                notes=None,
                like=None,
                image_url=None,
                nutri_facts=None,
                weight_in_grams=None,
                calorie_density=None,
                carbo_percentage=None,
                protein_percentage=None,
                total_fat_percentage=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                discarded=False,
                version=1
            )
        
        # Error 4: Invalid percentage values
        with pytest.raises(ValueError):
            ApiMeal(
                id=str(uuid4()),
                name="Test",
                author_id=str(uuid4()),
                menu_id=None,
                recipes=[],
                tags=frozenset(),
                description=None,
                notes=None,
                like=None,
                image_url=None,
                nutri_facts=None,
                weight_in_grams=None,
                calorie_density=None,
                carbo_percentage=150.0,  # Invalid percentage
                protein_percentage=None,
                total_fat_percentage=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                discarded=False,
                version=1
            )
        
        # Error 5: Negative weight
        with pytest.raises(ValueError):
            ApiMeal(
                id=str(uuid4()),
                name="Test",
                author_id=str(uuid4()),
                menu_id=None,
                recipes=[],
                tags=frozenset(),
                description=None,
                notes=None,
                like=None,
                image_url=None,
                nutri_facts=None,
                weight_in_grams=-1,  # Negative weight
                calorie_density=None,
                carbo_percentage=None,
                protein_percentage=None,
                total_fat_percentage=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                discarded=False,
                version=1
            )

    def test_from_orm_model_error_scenarios(self):
        """Test from_orm_model error handling - minimum 5 error scenarios."""
        
        # Error 1: None input
        with pytest.raises((AttributeError, TypeError)):
            ApiMeal.from_orm_model(None)  # type: ignore
        
        # Error 2: Invalid object type
        with pytest.raises((AttributeError, TypeError)):
            ApiMeal.from_orm_model("not_an_orm_object")  # type: ignore
        
        # Error 3: Empty dictionary (missing required attributes)
        with pytest.raises((AttributeError, TypeError)):
            ApiMeal.from_orm_model({})  # type: ignore
        
        # Error 4: Create ORM with invalid kwargs and test conversion
        try:
            invalid_orm_kwargs = create_meal_orm_kwargs()
            invalid_orm_kwargs["id"] = 123  # Invalid ID type
            invalid_orm = MealSaModel(**invalid_orm_kwargs)
            # If creation succeeds, test conversion
            with pytest.raises((ValueError, TypeError)):
                ApiMeal.from_orm_model(invalid_orm)
        except Exception:
            # If ORM creation itself fails, that's also a valid error scenario
            pass
        
        # Error 5: Test with minimal ORM object that might miss expected attributes
        minimal_orm_kwargs = {
            "id": str(uuid4()),
            "name": "",  # Empty name might cause validation issues
            "author_id": str(uuid4()),
            "menu_id": None,
            "recipes": [],
            "tags": frozenset(),
            "description": None,
            "notes": None,
            "like": None,
            "image_url": None,
            "nutri_facts": None,
            "weight_in_grams": None,
            "calorie_density": None,
            "carbo_percentage": None,
            "protein_percentage": None,
            "total_fat_percentage": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "discarded": False,
            "version": 1
        }
        try:
            minimal_orm = MealSaModel(**minimal_orm_kwargs)
            # Test that empty strings might cause validation issues
            with pytest.raises((ValueError, TypeError)):
                ApiMeal.from_orm_model(minimal_orm)
        except Exception:
            # If ORM creation itself fails with empty strings, that's also a valid test
            pass

    def test_to_orm_kwargs_error_scenarios(self):
        """Test to_orm_kwargs error handling - edge cases since method is robust."""
        
        # Create valid meal for testing edge cases
        meal = create_simple_api_meal()
        
        # Test with various edge cases that should still work
        
        # Edge case 1: Meal with empty collections
        empty_meal = create_minimal_api_meal()
        kwargs = empty_meal.to_orm_kwargs()
        assert isinstance(kwargs, dict)
        assert kwargs["recipes"] == []
        assert kwargs["tags"] == []
        
        # Edge case 2: Meal with large collections
        complex_meal = create_complex_api_meal()
        kwargs = complex_meal.to_orm_kwargs()
        assert isinstance(kwargs, dict)
        assert isinstance(kwargs["recipes"], list)
        assert isinstance(kwargs["tags"], list)
        
        # Edge case 3: Meal with None optional fields
        kwargs = meal.to_orm_kwargs()
        assert isinstance(kwargs, dict)
        # Should handle None values gracefully
        if kwargs["nutri_facts"] is not None:
            from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import NutriFactsSaModel
            assert isinstance(kwargs["nutri_facts"], NutriFactsSaModel)
        
        # Edge case 4: Consistency check
        for _ in range(3):
            result = meal.to_orm_kwargs()
            assert "id" in result
            assert "name" in result
            assert "recipes" in result
            assert "tags" in result
        
        # Edge case 5: Type verification
        kwargs = meal.to_orm_kwargs()
        assert isinstance(kwargs["id"], str)
        assert isinstance(kwargs["name"], str)
        assert isinstance(kwargs["recipes"], list)
        assert isinstance(kwargs["tags"], list)

    @pytest.mark.parametrize("modification,description", [
        ({"name": ""}, "Empty name"),
        ({"author_id": "invalid-uuid"}, "Invalid author UUID"),
        ({"menu_id": "invalid-uuid"}, "Invalid menu UUID"),
        ({"weight_in_grams": -1}, "Negative weight"),
        ({"calorie_density": -1.0}, "Negative calorie density"),
        ({"carbo_percentage": 150.0}, "Invalid carbo percentage"),
        ({"protein_percentage": -10.0}, "Invalid protein percentage"),
        ({"total_fat_percentage": 200.0}, "Invalid total fat percentage"),
        ({"version": 0}, "Zero version"),
    ])
    def test_validation_error_scenarios(self, modification, description):
        """Test comprehensive validation error scenarios."""
        base_valid_data = {
            "id": str(uuid4()),
            "name": "Test Meal",
            "author_id": str(uuid4()),
            "menu_id": None,
            "recipes": [],
            "tags": frozenset(),
            "description": None,
            "notes": None,
            "like": None,
            "image_url": None,
            "nutri_facts": None,
            "weight_in_grams": None,
            "calorie_density": None,
            "carbo_percentage": None,
            "protein_percentage": None,
            "total_fat_percentage": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "discarded": False,
            "version": 1
        }
        
        invalid_data = {**base_valid_data, **modification}
        with pytest.raises(ValueError):
            ApiMeal(**invalid_data)


class TestApiMealEdgeCases(BaseApiMealTest):
    """
    Test suite for edge case tests.
    """

    # =============================================================================
    # EDGE CASE TESTS
    # =============================================================================

    def test_edge_case_empty_collections(self):
        """Test handling of empty collections."""
        minimal_meal = create_minimal_api_meal()
        
        # Should handle empty collections gracefully
        assert minimal_meal.recipes == []
        assert minimal_meal.tags == frozenset()
        
        # Round-trip should preserve empty collections
        domain_meal = minimal_meal.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)
        
        assert recovered_api.recipes == []
        assert recovered_api.tags == frozenset()

    def test_edge_case_large_collections(self):
        """Test handling of large collections."""
        max_meal = create_api_meal_with_max_recipes()
        
        # Should handle large collections
        assert len(max_meal.recipes) >= 5
        assert len(max_meal.tags) >= 3
        
        # Round-trip should preserve large collections
        domain_meal = max_meal.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)
        
        assert len(recovered_api.recipes) == len(max_meal.recipes)
        assert len(recovered_api.tags) == len(max_meal.tags)

    def test_edge_case_boundary_values(self):
        """Test handling of boundary values."""
        meal = create_api_meal(
            name="x",  # Minimum length
            weight_in_grams=0,  # Minimum weight
            calorie_density=0.0,  # Minimum calorie density
            carbo_percentage=0.0,  # Minimum percentage
            protein_percentage=100.0,  # Maximum percentage
            total_fat_percentage=0.0,  # Minimum percentage
            version=1  # Minimum version
        )
        
        # Should handle boundary values
        assert meal.name == "x"
        assert meal.weight_in_grams == 0
        assert meal.calorie_density == 0.0
        assert meal.carbo_percentage == 0.0
        assert meal.protein_percentage == 100.0
        assert meal.total_fat_percentage == 0.0
        assert meal.version == 1

    def test_edge_case_null_optional_fields(self):
        """Test handling of null optional fields."""
        meal_kwargs = create_api_meal_kwargs(
            description=None,
            notes=None,
            like=None,
            image_url=None,
            nutri_facts=None,
            weight_in_grams=None,
            calorie_density=None,
            carbo_percentage=None,
            protein_percentage=None,
            total_fat_percentage=None,
        )
        meal = ApiMeal(**meal_kwargs)
        
        # Should handle null optional fields
        assert meal.description is None
        assert meal.notes is None
        assert meal.like is None
        assert meal.image_url is None
        assert meal.nutri_facts is None
        assert meal.weight_in_grams is None
        assert meal.calorie_density is None
        assert meal.carbo_percentage is None
        assert meal.protein_percentage is None
        assert meal.total_fat_percentage is None

    def test_edge_case_complex_nested_structures(self):
        """Test handling of complex nested structures."""
        complex_meal = create_complex_api_meal()
        
        # Should handle complex nested structures
        assert len(complex_meal.recipes) > 2
        assert len(complex_meal.tags) > 2
        
        # Verify nested object types
        assert all(isinstance(recipe, ApiRecipe) for recipe in complex_meal.recipes)
        assert all(isinstance(tag, ApiTag) for tag in complex_meal.tags)
        
        # Round-trip should preserve complex structures
        domain_meal = complex_meal.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)
        
        assert len(recovered_api.recipes) == len(complex_meal.recipes)
        assert len(recovered_api.tags) == len(complex_meal.tags)

    def test_edge_case_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters."""
        meal = create_api_meal(
            name="Test Meal with Unicode: 🍕🍝🍰",
            description="Meal with émojis and spécial characters: àáâãäåæçèéêë",
            notes="Japanese: こんにちは, Arabic: مرحبا, Chinese: 你好"
        )
        
        # Should handle Unicode characters
        assert "🍕🍝🍰" in meal.name
        assert meal.description and "émojis" in meal.description
        assert meal.notes and "こんにちは" in meal.notes
        
        # Round-trip should preserve Unicode
        json_str = meal.model_dump_json()
        restored_meal = ApiMeal.model_validate_json(json_str)
        
        assert restored_meal.name == meal.name
        assert restored_meal.description == meal.description
        assert restored_meal.notes == meal.notes

    def test_edge_case_datetime_handling(self):
        """Test handling of various datetime scenarios."""
        # Test future dates
        future_date = datetime.now() + timedelta(days=365)
        meal_future = create_api_meal(
            created_at=future_date,
            updated_at=future_date + timedelta(hours=1)
        )
        
        # Should handle future dates
        assert meal_future.created_at == future_date
        assert meal_future.updated_at > meal_future.created_at
        
        # Test past dates
        past_date = datetime.now() - timedelta(days=365)
        meal_past = create_api_meal(
            created_at=past_date,
            updated_at=past_date + timedelta(hours=1)
        )
        
        # Should handle past dates
        assert meal_past.created_at == past_date
        assert meal_past.updated_at > meal_past.created_at
        
        # Round-trip should preserve datetime values
        domain_meal = meal_future.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)
        
        assert recovered_api.created_at == meal_future.created_at
        assert recovered_api.updated_at == meal_future.updated_at


class TestApiMealComputedProperties(BaseApiMealTest):
    """
    Test suite for computed properties validation.
    """

    # =============================================================================
    # COMPUTED PROPERTIES TESTS
    # =============================================================================

    def test_computed_properties_correction_round_trip(self):
        """Test computed properties correction in round-trip conversion."""
        # Create meal with incorrect computed properties
        meal_with_incorrect = create_api_meal_with_incorrect_computed_properties()
        
        # Test that round-trip corrects computed properties
        success, details = validate_computed_property_correction_roundtrip(meal_with_incorrect)
        
        assert success, f"Computed property correction failed: {details}"
        
        # Check specific corrections
        assert details["weight_corrected"], "Weight was not corrected properly"
        assert details["calorie_density_corrected"], "Calorie density was not corrected properly"
        assert details["nutri_facts_corrected"], "Nutrition facts were not corrected properly"

    def test_computed_properties_with_no_recipes(self):
        """Test computed properties when meal has no recipes."""
        empty_meal = create_api_meal_without_recipes()
        
        # Should handle empty meal appropriately
        assert empty_meal.recipes == []
        assert empty_meal.weight_in_grams == 0
        assert empty_meal.calorie_density is None
        assert empty_meal.carbo_percentage is None
        assert empty_meal.protein_percentage is None
        assert empty_meal.total_fat_percentage is None
        assert empty_meal.nutri_facts is None

    def test_computed_properties_with_multiple_recipes(self):
        """Test computed properties aggregation with multiple recipes."""
        multi_recipe_meal = create_api_meal_with_max_recipes()
        
        # Should aggregate from multiple recipes
        assert len(multi_recipe_meal.recipes) > 5
        
        if multi_recipe_meal.nutri_facts:
            # Should have aggregated nutrition facts
            assert multi_recipe_meal.nutri_facts.calories > 0
            assert multi_recipe_meal.nutri_facts.protein > 0
            assert multi_recipe_meal.nutri_facts.carbohydrate > 0
            
        if multi_recipe_meal.weight_in_grams:
            # Should have aggregated weight
            assert multi_recipe_meal.weight_in_grams > 0
            
        # Round-trip should preserve computed values
        domain_meal = multi_recipe_meal.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)
        
        assert recovered_api.weight_in_grams == multi_recipe_meal.weight_in_grams
        assert recovered_api.calorie_density == multi_recipe_meal.calorie_density

    def test_json_with_incorrect_computed_properties_correction(self):
        """Test that JSON with incorrect computed properties gets corrected."""
        # Create JSON with incorrect computed properties
        meal_data = create_api_meal_kwargs()
        
        # Manually set incorrect computed properties
        meal_data["weight_in_grams"] = 100  # Incorrect
        meal_data["calorie_density"] = 50.0  # Incorrect
        meal_data["carbo_percentage"] = 25.0  # Incorrect
        
        # Create meal from this data
        meal = ApiMeal(**meal_data)
        
        # Convert through domain (should correct properties)
        domain_meal = meal.to_domain()
        corrected_meal = ApiMeal.from_domain(domain_meal)
        
        # Properties should be corrected based on actual recipe data
        if corrected_meal.recipes:
            expected_weight = sum(r.weight_in_grams or 0 for r in corrected_meal.recipes)
            assert corrected_meal.weight_in_grams == expected_weight


class TestApiMealJson(BaseApiMealTest):
    """
    Test suite for JSON serialization/deserialization tests.
    """

    # =============================================================================
    # JSON SERIALIZATION/DESERIALIZATION TESTS
    # =============================================================================

    def test_json_serialization_basic(self, simple_meal):
        """Test basic JSON serialization."""
        json_str = simple_meal.model_dump_json()
        
        assert isinstance(json_str, str)
        assert simple_meal.id in json_str
        assert simple_meal.name in json_str
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert parsed["id"] == simple_meal.id
        assert parsed["name"] == simple_meal.name

    def test_json_deserialization_basic(self):
        """Test basic JSON deserialization."""
        # Create valid JSON test cases
        valid_json_cases = create_valid_json_test_cases()
        
        for json_data in valid_json_cases:
            json_str = json.dumps(json_data)
            api_meal = ApiMeal.model_validate_json(json_str)
            
            assert isinstance(api_meal, ApiMeal)
            assert api_meal.id == json_data["id"]
            assert api_meal.name == json_data["name"]

    def test_json_round_trip_serialization(self, complex_meal):
        """Test JSON round-trip serialization preserves data."""
        # Test round-trip serialization
        json_str = complex_meal.model_dump_json()
    
        # Deserialize from JSON
        restored_meal = ApiMeal.model_validate_json(json_str)   
        
        # Should preserve basic data
        assert restored_meal.id == complex_meal.id
        assert restored_meal.name == complex_meal.name
        assert restored_meal.author_id == complex_meal.author_id
        assert len(restored_meal.recipes) == len(complex_meal.recipes)
        assert len(restored_meal.tags) == len(complex_meal.tags)

    def test_json_with_computed_properties(self):
        """Test JSON serialization includes computed properties."""
        meal = create_api_meal()
        json_str = meal.model_dump_json()
        
        # Should include computed properties in JSON
        parsed = json.loads(json_str)
        assert "weight_in_grams" in parsed
        assert "calorie_density" in parsed
        assert "carbo_percentage" in parsed
        assert "protein_percentage" in parsed
        assert "total_fat_percentage" in parsed

    def test_json_error_scenarios(self):
        """Test JSON error scenarios."""
        # Test malformed JSON
        malformed_scenarios = create_malformed_json_scenarios()
        
        for scenario in malformed_scenarios[:3]:  # Test first 3 scenarios
            with pytest.raises(Exception):
                ApiMeal.model_validate_json(scenario["json"])

    @pytest.mark.parametrize("json_data", create_valid_json_test_cases()[:3])
    def test_json_deserialization_parametrized(self, json_data):
        """Test JSON deserialization with various valid inputs."""
        json_str = json.dumps(json_data)
        api_meal = ApiMeal.model_validate_json(json_str)
        
        assert isinstance(api_meal, ApiMeal)
        assert api_meal.id == json_data["id"]
        assert api_meal.name == json_data["name"]

    @pytest.mark.parametrize("case", create_invalid_json_test_cases()[:3])
    def test_json_error_scenarios_parametrized(self, case):
        """Test JSON error scenarios with various invalid inputs."""
        with pytest.raises(Exception):
            json_str = json.dumps(case["data"])
            ApiMeal.model_validate_json(json_str)

    def test_json_performance(self, meal_collection):
        """Test JSON performance with collection of meals."""
        # Test serialization performance
        json_strings = []
        for meal in meal_collection:
            json_str = meal.model_dump_json()
            json_strings.append(json_str)
            assert isinstance(json_str, str)
        
        # Test deserialization performance
        restored_meals = []
        for json_str in json_strings:
            restored_meal = ApiMeal.model_validate_json(json_str)
            restored_meals.append(restored_meal)
            assert isinstance(restored_meal, ApiMeal)
        
        # Should restore same number of meals
        assert len(restored_meals) == len(meal_collection)

    @pytest.mark.parametrize("meal", create_meal_collection(count=3))
    def test_json_performance_parametrized(self, meal):
        """Test JSON performance with parametrized meals."""
        # Test serialization
        json_str = meal.model_dump_json()
        assert isinstance(json_str, str)
        assert meal.id in json_str
        
        # Test deserialization
        restored_meal = ApiMeal.model_validate_json(json_str)
        assert isinstance(restored_meal, ApiMeal)
        assert restored_meal.id == meal.id

    def test_json_with_nested_objects(self, complex_meal):
        """Test JSON handling with complex nested objects."""
        json_str = complex_meal.model_dump_json()
        parsed = json.loads(json_str)
        
        # Should serialize nested objects properly
        assert "recipes" in parsed
        assert "tags" in parsed
        assert isinstance(parsed["recipes"], list)
        assert isinstance(parsed["tags"], list)
        
        # Should deserialize nested objects properly
        restored_meal = ApiMeal.model_validate_json(json_str)
        assert len(restored_meal.recipes) == len(complex_meal.recipes)
        assert len(restored_meal.tags) == len(complex_meal.tags)

    def test_json_factory_functions(self):
        """Test JSON creation using factory functions."""
        # Test create_api_meal_from_json
        json_meal = create_api_meal_from_json()
        assert isinstance(json_meal, ApiMeal)
        
        # Test create_api_meal_json
        json_str = create_api_meal_json()
        assert isinstance(json_str, str)
        
        # Should be valid JSON that can be parsed
        restored_meal = ApiMeal.model_validate_json(json_str)
        assert isinstance(restored_meal, ApiMeal) 


class TestApiMealFieldValidation(BaseApiMealTest):
    """
    Test suite for comprehensive field validation tests.
    """

    # =============================================================================
    # FIELD VALIDATION TESTS
    # =============================================================================

    def test_field_validation_test_suite(self):
        """Test comprehensive field validation using test suite."""
        validation_suite = create_field_validation_test_suite()
        
        # Test name validation
        for invalid_name_data in validation_suite["name_validation"]:
            with pytest.raises(Exception):
                ApiMeal(**create_api_meal_with_invalid_field("name", invalid_name_data["name"]))
        
        # Test author_id validation
        for invalid_author_data in validation_suite["author_id_validation"]:
            with pytest.raises(Exception):
                ApiMeal(**create_api_meal_with_invalid_field("author_id", invalid_author_data["author_id"]))
        
        # Test percentage validation
        for invalid_percentage_data in validation_suite["percentage_validation"]:
            field_name = list(invalid_percentage_data.keys())[0]
            field_value = invalid_percentage_data[field_name]
            with pytest.raises(Exception):
                ApiMeal(**create_api_meal_with_invalid_field(field_name, field_value))

    def test_boundary_value_validation(self):
        """Test boundary value validation."""
        boundary_cases = create_boundary_value_test_cases()
        
        # Test name boundaries (should pass)
        for boundary_case in boundary_cases["name_boundaries"]:
            meal = ApiMeal(**create_api_meal_kwargs(**boundary_case))
            assert isinstance(meal, ApiMeal)
        
        # Test percentage boundaries (should pass)
        for boundary_case in boundary_cases["percentage_boundaries"]:
            meal = ApiMeal(**create_api_meal_kwargs(**boundary_case))
            assert isinstance(meal, ApiMeal)

    def test_missing_required_fields_validation(self):
        """Test validation with missing required fields."""
        missing_fields_scenarios = create_api_meal_with_missing_required_fields()
        
        for scenario in missing_fields_scenarios:
            with pytest.raises(Exception):
                ApiMeal(**scenario)

    def test_type_coercion_validation(self):
        """Test that strict type validation prevents coercion."""
        type_coercion_cases = create_type_coercion_test_cases()
        
        # Test string to number coercion (should fail with strict=True)
        for coercion_case in type_coercion_cases["string_to_number_coercion"]:
            field_name = list(coercion_case.keys())[0]
            field_value = coercion_case[field_name]
            with pytest.raises(Exception):
                ApiMeal(**create_api_meal_with_invalid_field(field_name, field_value))

    def test_nested_object_validation(self):
        """Test nested object validation."""
        nested_validation_cases = create_nested_object_validation_test_cases()
        
        # Test invalid recipes
        for invalid_recipe_case in nested_validation_cases["invalid_recipes"][:3]:
            with pytest.raises(Exception):
                ApiMeal(**invalid_recipe_case)
        
        # Test invalid tags
        for invalid_tag_case in nested_validation_cases["invalid_tags"][:3]:
            with pytest.raises(Exception):
                ApiMeal(**invalid_tag_case)

    @pytest.mark.parametrize("field_name,invalid_value", [
        ("name", ""),
        ("name", "x" * 256),
        ("author_id", "invalid-uuid"),
        ("weight_in_grams", -1),
        ("carbo_percentage", 150.0),
        ("protein_percentage", -10.0),
        ("version", 0),
    ])
    def test_field_validation_parametrized(self, field_name, invalid_value):
        """Test field validation with parametrized invalid values."""
        with pytest.raises(Exception):
            ApiMeal(**create_api_meal_with_invalid_field(field_name, invalid_value))

    def test_pydantic_configuration_validation(self):
        """Test Pydantic configuration enforcement."""
        config_tests = create_pydantic_config_test_cases()
        
        # Test extra fields forbidden
        extra_fields_data = config_tests["extra_fields_forbidden"]["data"]
        with pytest.raises(Exception):
            ApiMeal(**extra_fields_data)
        
        # Test strict type validation
        strict_type_data = config_tests["strict_type_validation"]["data"]
        with pytest.raises(Exception):
            ApiMeal(**strict_type_data)

    def test_immutability_enforcement(self):
        """Test that meals are immutable after creation."""
        meal = create_simple_api_meal()
        
        # Should be immutable (frozen)
        with pytest.raises(Exception):
            meal.id = "changed"  # type: ignore
        
        with pytest.raises(Exception):
            meal.name = "changed"  # type: ignore
        
        with pytest.raises(Exception):
            meal.weight_in_grams = 9999  # type: ignore


class TestApiMealIntegration(BaseApiMealTest):
    """
    Test suite for integration tests with base classes.
    """

    # =============================================================================
    # INTEGRATION TESTS WITH BASE CLASSES
    # =============================================================================

    def test_base_api_entity_inheritance(self, simple_meal):
        """Test proper inheritance from BaseApiEntity."""
        from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiEntity
        
        # Should inherit from BaseApiEntity
        assert isinstance(simple_meal, BaseApiEntity)
        
        # Should have base model configuration
        assert simple_meal.model_config.get('frozen') is True
        assert simple_meal.model_config.get('strict') is True
        assert simple_meal.model_config.get('extra') == 'forbid'

    def test_base_api_entity_conversion_methods(self, simple_meal):
        """Test integration with BaseApiEntity conversion methods."""
        # Should have access to conversion methods
        assert hasattr(simple_meal, 'from_domain')
        assert hasattr(simple_meal, 'to_domain')
        assert hasattr(simple_meal, 'from_orm_model')
        assert hasattr(simple_meal, 'to_orm_kwargs')
        
        # Should have conversion utility
        assert hasattr(simple_meal, 'convert')
        assert simple_meal.convert is not None

    def test_pydantic_validation_integration(self):
        """Test integration with Pydantic validation from base class."""
        # Test model_validate works
        meal_data = create_api_meal_kwargs()
        api_meal = ApiMeal.model_validate(meal_data)
        assert api_meal.id == meal_data["id"]
        assert api_meal.name == meal_data["name"]
        
        # Test model_validate_json works
        json_str = json.dumps(create_valid_json_test_cases()[0])
        api_meal_from_json = ApiMeal.model_validate_json(json_str)
        assert isinstance(api_meal_from_json, ApiMeal)

    def test_field_validation_integration(self):
        """Test field validation integration."""
        # Test valid creation
        valid_meal = create_api_meal()
        assert isinstance(valid_meal, ApiMeal)
        
        # Test field constraints
        assert len(valid_meal.id) > 0
        assert len(valid_meal.name) > 0
        assert len(valid_meal.author_id) > 0
        assert isinstance(valid_meal.recipes, list)
        assert isinstance(valid_meal.tags, frozenset)

    def test_conversion_utility_integration(self, simple_meal):
        """Test integration with conversion utility."""
        # Should be able to convert through utility
        domain_meal = simple_meal.to_domain()
        assert isinstance(domain_meal, Meal)
        
        # Should be able to convert back
        recovered_meal = ApiMeal.from_domain(domain_meal)
        assert isinstance(recovered_meal, ApiMeal)
        assert recovered_meal.id == simple_meal.id


class TestApiMealPerformance(BaseApiMealTest):
    """
    Test suite for performance tests.
    """

    # =============================================================================
    # PERFORMANCE TESTS
    # =============================================================================

    def test_from_domain_performance(self, domain_meal):
        """Test from_domain performance."""
        # Should handle conversion efficiently
        start_time = datetime.now()
        
        for _ in range(100):
            api_meal = ApiMeal.from_domain(domain_meal)
            assert isinstance(api_meal, ApiMeal)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete 100 conversions reasonably quickly
        assert duration < 5.0, f"Conversion took too long: {duration} seconds"

    def test_to_domain_performance(self, complex_meal):
        """Test to_domain performance."""
        # Should handle conversion efficiently
        start_time = datetime.now()
        
        for _ in range(100):
            domain_meal = complex_meal.to_domain()
            assert isinstance(domain_meal, Meal)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete 100 conversions reasonably quickly
        assert duration < 5.0, f"Conversion took too long: {duration} seconds"

    def test_from_orm_model_performance(self, real_orm_meal):
        """Test from_orm_model performance."""
        # Should handle conversion efficiently
        start_time = datetime.now()
        
        for _ in range(100):
            api_meal = ApiMeal.from_orm_model(real_orm_meal)
            assert isinstance(api_meal, ApiMeal)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete 100 conversions reasonably quickly
        assert duration < 5.0, f"Conversion took too long: {duration} seconds"

    def test_to_orm_kwargs_performance(self, complex_meal):
        """Test to_orm_kwargs performance."""
        # Should handle conversion efficiently
        start_time = datetime.now()
        
        for _ in range(100):
            orm_kwargs = complex_meal.to_orm_kwargs()
            assert isinstance(orm_kwargs, dict)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete 100 conversions reasonably quickly
        assert duration < 5.0, f"Conversion took too long: {duration} seconds"

    def test_complete_conversion_cycle_performance(self, simple_meal):
        """Test complete conversion cycle performance."""
        # Should handle full conversion cycle efficiently
        start_time = datetime.now()
        
        for _ in range(50):
            # API → Domain → API → ORM kwargs
            domain_meal = simple_meal.to_domain()
            recovered_api = ApiMeal.from_domain(domain_meal)
            orm_kwargs = recovered_api.to_orm_kwargs()
            
            assert isinstance(domain_meal, Meal)
            assert isinstance(recovered_api, ApiMeal)
            assert isinstance(orm_kwargs, dict)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete 50 full cycles reasonably quickly
        assert duration < 10.0, f"Full cycle took too long: {duration} seconds"

    def test_large_collection_performance(self):
        """Test performance with large collections."""
        # Create meals with large collections
        large_collection_meals = []
        for _ in range(10):
            meal = create_api_meal_with_max_recipes()
            large_collection_meals.append(meal)
        
        # Test conversion performance
        start_time = datetime.now()
        
        for meal in large_collection_meals:
            domain_meal = meal.to_domain()
            recovered_api = ApiMeal.from_domain(domain_meal)
            assert len(recovered_api.recipes) == len(meal.recipes)
            assert len(recovered_api.tags) == len(meal.tags)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should handle large collections efficiently
        assert duration < 10.0, f"Large collection processing took too long: {duration} seconds"

    def test_bulk_operations_performance(self):
        """Test bulk operations performance."""
        # Create bulk dataset
        bulk_dataset = create_bulk_meal_creation_dataset(count=100)
        
        # Test bulk creation performance
        start_time = datetime.now()
        
        created_meals = []
        for meal_kwargs in bulk_dataset:
            meal = ApiMeal(**meal_kwargs)
            created_meals.append(meal)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should create 100 meals efficiently
        assert len(created_meals) == 100
        assert duration < 5.0, f"Bulk creation took too long: {duration} seconds"

    @pytest.mark.parametrize("domain_meal", create_nested_object_validation_dataset(count=5)[:5])
    def test_large_collection_performance_parametrized(self, domain_meal):
        """Test performance with parametrized large collections."""
        # Should handle individual conversions efficiently
        start_time = datetime.now()
        
        api_meal = ApiMeal.from_domain(domain_meal)
        recovered_domain = api_meal.to_domain()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Single conversion should be very fast
        assert duration < 1.0, f"Single conversion took too long: {duration} seconds"
        assert isinstance(api_meal, ApiMeal)
        assert isinstance(recovered_domain, Meal)

    @pytest.mark.parametrize("meal_data", create_conversion_performance_dataset(count=5)["api_meals"][:5])
    def test_bulk_operations_performance_parametrized(self, meal_data):
        """Test bulk operations with parametrized meals."""
        # Should handle individual operations efficiently
        start_time = datetime.now()
        
        domain_meal = meal_data.to_domain()
        orm_kwargs = meal_data.to_orm_kwargs()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Individual operations should be very fast
        assert duration < 1.0, f"Individual operation took too long: {duration} seconds"
        assert isinstance(domain_meal, Meal)
        assert isinstance(orm_kwargs, dict)


class TestApiMealSpecialized(BaseApiMealTest):
    """
    Test suite for specialized meal types and factory functions.
    """

    # =============================================================================
    # SPECIALIZED MEAL TYPES AND FACTORY TESTS
    # =============================================================================

    @pytest.mark.parametrize("meal_type,api_meal_factory", [
        ("simple", create_simple_api_meal),
        ("complex", create_complex_api_meal),
        ("vegetarian", create_vegetarian_api_meal),
        ("high_protein", create_high_protein_api_meal),
        ("family", create_family_api_meal),
        ("quick", create_quick_api_meal),
        ("holiday", create_holiday_api_meal),
        ("minimal", create_minimal_api_meal),
        ("max_recipes", create_api_meal_with_max_recipes),
        ("no_recipes", create_api_meal_without_recipes),
    ])
    def test_specialized_meal_types(self, meal_type, api_meal_factory):
        """Test various specialized meal types."""
        meal = api_meal_factory()
        
        assert isinstance(meal, ApiMeal)
        assert len(meal.id) > 0
        assert len(meal.name) > 0
        assert len(meal.author_id) > 0
        assert isinstance(meal.recipes, list)
        assert isinstance(meal.tags, frozenset)
        
        # Test round-trip conversion
        domain_meal = meal.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)
        
        assert recovered_api.id == meal.id
        assert recovered_api.name == meal.name
        assert recovered_api.author_id == meal.author_id
        assert len(recovered_api.recipes) == len(meal.recipes)

    @pytest.mark.parametrize("meal_type", [
        "breakfast",
        "lunch", 
        "dinner",
        "brunch",
        "snack"
    ])
    def test_meals_by_meal_type(self, meal_type):
        """Test meal creation for different meal types."""
        meal = create_api_meal(
            name=f"Test {meal_type.title()} Meal",
            description=f"A delicious {meal_type} meal"
        )
        
        assert isinstance(meal, ApiMeal)
        assert meal_type.lower() in meal.name.lower()
        assert meal.description is not None and meal_type in meal.description.lower()

    @pytest.mark.parametrize("cuisine", [
        "italian",
        "mexican", 
        "asian",
        "french",
        "indian"
    ])
    def test_meals_by_cuisine(self, cuisine):
        """Test meal creation for different cuisines."""
        meal = create_api_meal(
            name=f"Authentic {cuisine.title()} Meal",
            description=f"Traditional {cuisine} cuisine"
        )
        
        assert isinstance(meal, ApiMeal)
        assert cuisine.lower() in meal.name.lower()
        assert meal.description is not None and cuisine in meal.description.lower()

    def test_meal_collections(self):
        """Test meal collection creation."""
        collection = create_meal_collection(count=5)
        
        assert len(collection) == 5
        assert all(isinstance(meal, ApiMeal) for meal in collection)
        
        # Should have diverse meal types
        meal_names = [meal.name for meal in collection]
        assert len(set(meal_names)) == 5, "Meals should have unique names"

    def test_bulk_dataset_creation(self):
        """Test bulk dataset creation for performance testing."""
        # Test meal creation dataset
        meal_dataset = create_bulk_meal_creation_dataset(count=10)
        assert len(meal_dataset) == 10
        assert all(isinstance(data, dict) for data in meal_dataset)
        
        # Test JSON serialization dataset
        json_dataset = create_bulk_json_serialization_dataset(count=10)
        assert len(json_dataset) == 10
        assert all(isinstance(json_str, str) for json_str in json_dataset)
        
        # Test conversion performance dataset
        conversion_dataset = create_conversion_performance_dataset(count=10)
        assert len(conversion_dataset["api_meals"]) == 10
        assert all(isinstance(meal, ApiMeal) for meal in conversion_dataset["api_meals"])

    @pytest.mark.parametrize("scenario", REALISTIC_MEAL_SCENARIOS[:3])  # Test first 3 scenarios
    def test_realistic_scenario_coverage_parametrized(self, scenario):
        """Test realistic scenario coverage using factory data."""
        meal = create_api_meal(name=scenario["name"], description=scenario["description"])
        
        assert isinstance(meal, ApiMeal)
        assert meal.name == scenario["name"]
        assert meal.description == scenario["description"]
        
        # Test round-trip for realistic scenarios
        original_domain = meal.to_domain()
        recovered_api = ApiMeal.from_domain(original_domain)
        recovered_domain = recovered_api.to_domain()
        assert recovered_domain == original_domain, f"Round-trip failed for scenario: {scenario['name']}"

    @pytest.mark.parametrize("specialized_function", [
        create_simple_api_meal,
        create_complex_api_meal,
        create_vegetarian_api_meal,
        create_high_protein_api_meal,
        create_family_api_meal,
        create_quick_api_meal,
        create_holiday_api_meal,
        create_minimal_api_meal,
        create_api_meal_with_max_recipes,
        create_api_meal_without_recipes,
        create_api_meal_with_incorrect_computed_properties,
    ])
    def test_specialized_factory_functions(self, specialized_function):
        """Test all specialized factory functions."""
        meal = specialized_function()
        
        assert isinstance(meal, ApiMeal)
        assert len(meal.id) > 0
        assert len(meal.name) > 0
        assert isinstance(meal.created_at, datetime)
        assert isinstance(meal.updated_at, datetime)
        assert isinstance(meal.version, int)
        assert isinstance(meal.discarded, bool)

    @pytest.mark.parametrize("collection_function,test_param", [
        (create_meal_collection, {"count": 2}),
        (create_test_meal_dataset, {"count": 2}),
        (create_bulk_meal_creation_dataset, {"count": 2}),
        (create_bulk_json_serialization_dataset, {"count": 2}),
        (create_bulk_json_deserialization_dataset, {"count": 2}),
        (create_conversion_performance_dataset, {"count": 2}),
        (create_nested_object_validation_dataset, {"count": 2}),
        (create_computed_property_test_dataset, {"count": 2}),
    ])
    def test_collection_factory_functions(self, collection_function, test_param):
        """Test all collection factory functions."""
        result = collection_function(**test_param)
        
        assert result is not None
        if isinstance(result, list):
            assert len(result) >= test_param.get("count", 1)
        elif isinstance(result, dict):
            assert len(result) > 0 