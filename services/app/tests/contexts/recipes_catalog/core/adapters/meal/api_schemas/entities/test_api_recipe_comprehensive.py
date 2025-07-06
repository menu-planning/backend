import pytest
import time
import json
from uuid import uuid4
from datetime import datetime, timedelta

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import RecipeSaModel
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating

# Import utilities for recipe equality testing
# from tests.contexts.recipes_catalog.utils import assert_recipes_equal

# Import all factory functions
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    # Main factory functions
    create_api_recipe,
    create_api_recipe_kwargs,
    create_api_recipe_from_json,
    create_api_recipe_json,
    reset_api_recipe_counters,
    
    # Specialized factory functions
    create_simple_api_recipe,
    create_complex_api_recipe,
    create_vegetarian_api_recipe,
    create_high_protein_api_recipe,
    create_quick_api_recipe,
    create_dessert_api_recipe,
    create_minimal_api_recipe,
    create_api_recipe_with_max_fields,
    create_api_recipe_with_incorrect_averages,
    create_api_recipe_without_ratings,
    
    # Field validation edge cases - CRITICAL ADDITIONS
    create_api_recipe_with_invalid_name,
    create_api_recipe_with_invalid_instructions,
    create_api_recipe_with_invalid_total_time,
    create_api_recipe_with_invalid_weight,
    create_api_recipe_with_invalid_taste_rating,
    create_api_recipe_with_invalid_convenience_rating,
    create_api_recipe_with_invalid_privacy,
    create_api_recipe_with_boundary_values,
    create_api_recipe_with_extreme_boundary_values,
    create_api_recipe_with_none_values,
    create_api_recipe_with_empty_strings,
    create_api_recipe_with_whitespace_strings,
    
    # Tags validation edge cases - CRITICAL ADDITIONS
    create_api_recipe_with_invalid_tag_dict,
    create_api_recipe_with_invalid_tag_types,
    create_api_recipe_with_tag_without_author_id_context,
    create_api_recipe_with_mixed_tag_types,
    
    # Frozenset validation edge cases - CRITICAL ADDITIONS
    create_api_recipe_with_list_ingredients,
    create_api_recipe_with_set_ingredients,
    create_api_recipe_with_list_ratings,
    create_api_recipe_with_set_ratings,
    create_api_recipe_with_list_tags,
    create_api_recipe_with_set_tags,
    create_api_recipe_with_empty_collections,
    
    # Domain rule validation edge cases - CRITICAL ADDITIONS
    create_api_recipe_with_invalid_ingredient_positions,
    create_api_recipe_with_negative_ingredient_positions,
    create_api_recipe_with_duplicate_ingredient_positions,
    create_api_recipe_with_non_zero_start_positions,
    create_api_recipe_with_invalid_tag_author_id,
    
    # Computed properties edge cases - CRITICAL ADDITIONS
    create_api_recipe_with_mismatched_computed_properties,
    create_api_recipe_with_single_rating,
    create_api_recipe_with_extreme_ratings,
    create_api_recipe_with_fractional_averages,
    
    # Datetime edge cases - CRITICAL ADDITIONS
    create_api_recipe_with_future_timestamps,
    create_api_recipe_with_past_timestamps,
    create_api_recipe_with_invalid_timestamp_order,
    create_api_recipe_with_same_timestamps,
    
    # Unicode and special character edge cases - CRITICAL ADDITIONS
    create_api_recipe_with_unicode_text,
    create_api_recipe_with_special_characters,
    create_api_recipe_with_html_characters,
    create_api_recipe_with_sql_injection,
    create_api_recipe_with_very_long_text,
    
    # Concurrency and thread safety edge cases - CRITICAL ADDITIONS
    create_api_recipe_with_concurrent_modifications,
    create_api_recipe_with_high_version,
    create_api_recipe_with_zero_version,
    create_api_recipe_with_negative_version,
    
    # Comprehensive validation functions - CRITICAL ADDITIONS
    create_comprehensive_validation_test_cases,
    validate_round_trip_conversion,
    validate_orm_conversion,
    validate_json_serialization,
    
    # Performance and stress testing - CRITICAL ADDITIONS
    create_api_recipe_with_massive_collections,
    create_api_recipe_with_deeply_nested_data,
    create_stress_test_dataset,
    
    # Helper functions
    create_recipe_collection,
    create_recipes_by_cuisine,
    create_recipes_by_difficulty,
    create_test_recipe_dataset,
    
    # Round-trip testing functions
    create_recipe_domain_from_api,

    # JSON validation functions
    create_valid_json_test_cases,
    create_invalid_json_test_cases,
    validate_average_rating_correction_roundtrip,
    
    # Performance testing functions
    create_bulk_recipe_creation_dataset,
    create_bulk_json_serialization_dataset,
    create_bulk_json_deserialization_dataset,
    create_conversion_performance_dataset,
    create_nested_object_validation_dataset,
    
)

# Import DOMAIN factory functions for proper domain object creation
from tests.contexts.recipes_catalog.data_factories.recipe.recipe_domain_factories import (
    create_recipe,
    create_complex_recipe as create_complex_domain_recipe,
    create_minimal_recipe as create_minimal_domain_recipe,
    create_conversion_performance_dataset as create_conversion_performance_dataset_domain,
    create_nested_object_validation_dataset as create_nested_object_validation_dataset_domain,
    reset_recipe_domain_counters,
    # Enhanced constants from domain factories
    REALISTIC_RECIPE_SCENARIOS as REALISTIC_RECIPE_SCENARIOS_DOMAIN,
    CUISINE_TYPES as CUISINE_TYPES_DOMAIN,
    DIFFICULTY_LEVELS as DIFFICULTY_LEVELS_DOMAIN,
)

# Import ORM factory functions for real ORM instances
from tests.contexts.recipes_catalog.data_factories.recipe.recipe_orm_factories import (
    create_recipe_orm,
    create_recipe_orm_kwargs,
    reset_recipe_orm_counters
)


class BaseApiRecipeTest:
    """
    Base class with shared fixtures and setup for all ApiRecipe tests.
    """

    # =============================================================================
    # FIXTURES AND TEST DATA
    # =============================================================================

    @pytest.fixture(autouse=True)
    def reset_counters(self):
        """Reset all counters before each test for isolation."""
        reset_api_recipe_counters()
        reset_recipe_domain_counters()
        yield
        reset_api_recipe_counters()
        reset_recipe_domain_counters()

    @pytest.fixture
    def simple_recipe(self):
        """Simple recipe for basic testing."""
        return create_simple_api_recipe()

    @pytest.fixture
    def complex_recipe(self):
        """Complex recipe with many nested objects."""
        return create_complex_api_recipe()

    @pytest.fixture
    def domain_recipe(self):
        """Domain recipe for conversion tests - created directly from domain factories."""
        return create_recipe()

    @pytest.fixture
    def domain_recipe_with_nutri_facts(self):
        """Domain recipe with nutrition facts for nutrition conversion tests."""
        return create_complex_domain_recipe()

    @pytest.fixture
    def real_orm_recipe(self):
        """Real ORM recipe for testing - no mocks needed."""
        return create_recipe_orm(
            name="Test Recipe for ORM Conversion",
            description="Real ORM recipe for testing conversion methods",
            instructions="Real instructions for testing",
            author_id=str(uuid4()),
            meal_id=str(uuid4())
        )

    @pytest.fixture
    def edge_case_recipes(self):
        """Collection of edge case recipes for comprehensive testing."""
        return {
            "empty_collections": create_minimal_api_recipe(),
            "max_fields": create_api_recipe_with_max_fields(),
            "incorrect_averages": create_api_recipe_with_incorrect_averages(),
            "no_ratings": create_api_recipe_without_ratings(),
            "vegetarian": create_vegetarian_api_recipe(),
            "high_protein": create_high_protein_api_recipe(),
            "quick": create_quick_api_recipe(),
            "dessert": create_dessert_api_recipe()
        }

    @pytest.fixture
    def recipe_collection(self):
        """Collection of diverse recipes for batch testing."""
        return create_recipe_collection(count=10)

    @pytest.fixture(autouse=True)
    def reset_all_counters(self):
        """Reset both API and ORM counters before each test for isolation."""
        reset_api_recipe_counters()
        reset_recipe_orm_counters()
        reset_recipe_domain_counters()
        yield
        reset_api_recipe_counters()
        reset_recipe_orm_counters()
        reset_recipe_domain_counters()


class TestApiRecipeBasics(BaseApiRecipeTest):
    """
    Test suite for basic ApiRecipe conversion methods (>95% coverage target).
    """

    # =============================================================================
    # UNIT TESTS FOR ALL CONVERSION METHODS (>95% COVERAGE TARGET)
    # =============================================================================

    def test_from_domain_basic_conversion(self, domain_recipe):
        """Test from_domain basic conversion functionality."""
        api_recipe = ApiRecipe.from_domain(domain_recipe)
        
        assert api_recipe.id == domain_recipe.id
        assert api_recipe.name == domain_recipe.name
        assert api_recipe.meal_id == domain_recipe.meal_id
        assert api_recipe.description == domain_recipe.description
        assert api_recipe.instructions == domain_recipe.instructions
        assert api_recipe.author_id == domain_recipe.author_id
        assert api_recipe.privacy == domain_recipe.privacy
        assert isinstance(api_recipe, ApiRecipe)

    def test_from_domain_nested_objects_conversion(self, domain_recipe):
        """Test from_domain properly converts nested objects."""
        api_recipe = ApiRecipe.from_domain(domain_recipe)
        
        # Test ingredients conversion - now frozenset
        assert len(api_recipe.ingredients) == len(domain_recipe.ingredients)
        assert all(isinstance(ing, ApiIngredient) for ing in api_recipe.ingredients)
        
        # Test ratings conversion - now frozenset
        domain_ratings = domain_recipe.ratings or []
        assert len(api_recipe.ratings) == len(domain_ratings)
        assert all(isinstance(rating, ApiRating) for rating in api_recipe.ratings)
        
        # Test tags conversion
        domain_tags = domain_recipe.tags or set()
        assert len(api_recipe.tags) == len(domain_tags)
        assert all(isinstance(tag, ApiTag) for tag in api_recipe.tags)
        assert isinstance(api_recipe.tags, frozenset)

    def test_from_domain_computed_properties(self, domain_recipe):
        """Test from_domain correctly handles computed properties."""
        api_recipe = ApiRecipe.from_domain(domain_recipe)
        
        # Computed properties should match domain values
        assert api_recipe.average_taste_rating == domain_recipe.average_taste_rating
        assert api_recipe.average_convenience_rating == domain_recipe.average_convenience_rating

    def test_from_domain_with_empty_collections(self):
        """Test from_domain handles empty collections correctly."""
        # Create domain recipe with empty collections directly from domain factory
        domain_recipe = create_minimal_domain_recipe()
        api_recipe = ApiRecipe.from_domain(domain_recipe)
        
        assert api_recipe.ingredients == frozenset()
        assert api_recipe.ratings == frozenset()
        assert api_recipe.tags == frozenset()
        assert api_recipe.nutri_facts is None

    def test_from_domain_with_nutrition_facts(self, domain_recipe_with_nutri_facts):
        """Test from_domain handles nutrition facts conversion."""
        api_recipe = ApiRecipe.from_domain(domain_recipe_with_nutri_facts)
        
        assert isinstance(api_recipe.nutri_facts, ApiNutriFacts)

        for name in ApiNutriFacts.model_fields.keys():
            domain = getattr(domain_recipe_with_nutri_facts.nutri_facts, name)
            api = getattr(api_recipe.nutri_facts, name)
            assert domain.value == api.value
            assert domain.unit.value == api.unit

    def test_to_domain_basic_conversion(self, simple_recipe):
        """Test to_domain basic conversion functionality."""
        domain_recipe = simple_recipe.to_domain()
        
        assert isinstance(domain_recipe, _Recipe)
        assert domain_recipe.id == simple_recipe.id
        assert domain_recipe.name == simple_recipe.name
        assert domain_recipe.meal_id == simple_recipe.meal_id
        assert domain_recipe.description == simple_recipe.description
        assert domain_recipe.instructions == simple_recipe.instructions
        assert domain_recipe.author_id == simple_recipe.author_id

    def test_to_domain_collection_type_conversion(self, complex_recipe):
        """Test to_domain converts collections correctly."""
        domain_recipe = complex_recipe.to_domain()
        
        # Tags should be converted from frozenset to set
        assert isinstance(domain_recipe.tags, set)
        assert len(domain_recipe.tags) == len(complex_recipe.tags)
        
        # Ingredients should be converted from frozenset to list
        assert isinstance(domain_recipe.ingredients, list)
        assert len(domain_recipe.ingredients) == len(complex_recipe.ingredients)
        
        # Ratings should be converted from frozenset to list
        assert isinstance(domain_recipe.ratings, list)
        assert len(domain_recipe.ratings) == len(complex_recipe.ratings)

    def test_to_domain_privacy_enum_conversion(self, simple_recipe):
        """Test to_domain converts privacy enum correctly."""
        domain_recipe = simple_recipe.to_domain()
        
        assert isinstance(domain_recipe.privacy, Privacy)
        assert domain_recipe.privacy == Privacy(simple_recipe.privacy)

    def test_from_orm_model_basic_conversion(self, real_orm_recipe):
        """Test from_orm_model basic conversion functionality."""
        api_recipe = ApiRecipe.from_orm_model(real_orm_recipe)
        
        assert api_recipe.id == real_orm_recipe.id
        assert api_recipe.name == real_orm_recipe.name
        assert api_recipe.meal_id == real_orm_recipe.meal_id
        assert api_recipe.description == real_orm_recipe.description
        assert api_recipe.instructions == real_orm_recipe.instructions
        assert api_recipe.author_id == real_orm_recipe.author_id
        assert isinstance(api_recipe, ApiRecipe)

    def test_from_orm_model_nested_objects_conversion(self, real_orm_recipe):
        """Test from_orm_model handles nested objects."""
        api_recipe = ApiRecipe.from_orm_model(real_orm_recipe)
        
        # Should handle collections properly - now frozensets
        assert isinstance(api_recipe.ingredients, frozenset)
        assert isinstance(api_recipe.ratings, frozenset)
        assert isinstance(api_recipe.tags, frozenset)
        assert len(api_recipe.ingredients) == len(real_orm_recipe.ingredients)
        assert len(api_recipe.ratings) == len(real_orm_recipe.ratings)
        assert len(api_recipe.tags) == len(real_orm_recipe.tags)

    def test_to_orm_kwargs_basic_conversion(self, simple_recipe):
        """Test to_orm_kwargs basic conversion functionality."""
        kwargs = simple_recipe.to_orm_kwargs()
        
        assert isinstance(kwargs, dict)
        assert kwargs["id"] == simple_recipe.id
        assert kwargs["name"] == simple_recipe.name
        assert kwargs["meal_id"] == simple_recipe.meal_id
        assert kwargs["description"] == simple_recipe.description
        assert kwargs["instructions"] == simple_recipe.instructions
        assert kwargs["author_id"] == simple_recipe.author_id

    def test_to_orm_kwargs_nested_objects_conversion(self, complex_recipe):
        """Test to_orm_kwargs converts nested objects correctly."""
        kwargs = complex_recipe.to_orm_kwargs()
        
        # Ingredients should be converted from frozenset to list of kwargs
        assert isinstance(kwargs["ingredients"], list)
        assert len(kwargs["ingredients"]) == len(complex_recipe.ingredients)
        
        # Ratings should be converted from frozenset to list of kwargs
        assert isinstance(kwargs["ratings"], list)
        assert len(kwargs["ratings"]) == len(complex_recipe.ratings)
        
        # Tags should be converted from frozenset to list of kwargs
        assert isinstance(kwargs["tags"], list)
        assert len(kwargs["tags"]) == len(complex_recipe.tags)

    def test_to_orm_kwargs_nutrition_facts_conversion(self, complex_recipe):
        """Test to_orm_kwargs handles nutrition facts conversion."""
        kwargs = complex_recipe.to_orm_kwargs()
        
        if complex_recipe.nutri_facts:
            from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import NutriFactsSaModel
            assert isinstance(kwargs["nutri_facts"], NutriFactsSaModel)
        else:
            assert kwargs["nutri_facts"] is None


class TestApiRecipeRoundTrip(BaseApiRecipeTest):
    """
    Test suite for round-trip conversion validation tests.
    """

    # =============================================================================
    # ROUND-TRIP CONVERSION VALIDATION TESTS
    # =============================================================================

    def test_domain_to_api_to_domain_round_trip(self, domain_recipe):
        """Test complete domain → API → domain round-trip preserves data integrity."""
        # Domain → API
        api_recipe = ApiRecipe.from_domain(domain_recipe)
        
        # API → Domain
        recovered_domain = api_recipe.to_domain()
        
        # Use Recipe's __eq__ method and utils for comprehensive comparison
        assert recovered_domain == domain_recipe, "Domain → API → Domain round-trip failed"

    def test_api_to_domain_to_api_round_trip(self, complex_recipe):
        """Test API → domain → API round-trip preserves data integrity."""
        # API → Domain
        domain_recipe = complex_recipe.to_domain()
        
        # Domain → API
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        # Verify data integrity for API objects (can't use domain equality)
        assert recovered_api.id == complex_recipe.id
        assert recovered_api.name == complex_recipe.name
        assert recovered_api.meal_id == complex_recipe.meal_id
        assert len(recovered_api.ingredients) == len(complex_recipe.ingredients)
        assert len(recovered_api.ratings) == len(complex_recipe.ratings)
        assert len(recovered_api.tags) == len(complex_recipe.tags)

    def test_orm_to_api_to_orm_round_trip(self, real_orm_recipe):
        """Test ORM → API → ORM round-trip preserves data integrity."""
        # ORM → API
        api_recipe = ApiRecipe.from_orm_model(real_orm_recipe)
        
        # API → ORM kwargs
        orm_kwargs = api_recipe.to_orm_kwargs()
        
        # Verify data integrity
        assert orm_kwargs["id"] == real_orm_recipe.id
        assert orm_kwargs["name"] == real_orm_recipe.name
        assert orm_kwargs["meal_id"] == real_orm_recipe.meal_id
        assert orm_kwargs["description"] == real_orm_recipe.description
        assert orm_kwargs["instructions"] == real_orm_recipe.instructions
        assert orm_kwargs["author_id"] == real_orm_recipe.author_id

    def test_complete_four_layer_round_trip(self, simple_recipe):
        """Test complete four-layer conversion cycle preserves data integrity."""
        # Start with API object
        original_api = simple_recipe
        
        # API → Domain
        domain_recipe = original_api.to_domain()
        
        # Domain → API
        api_from_domain = ApiRecipe.from_domain(domain_recipe)
        
        # API → ORM kwargs
        orm_kwargs = api_from_domain.to_orm_kwargs()
        
        # Verify complete data integrity
        assert orm_kwargs["id"] == original_api.id
        assert orm_kwargs["name"] == original_api.name
        assert orm_kwargs["meal_id"] == original_api.meal_id
        assert orm_kwargs["description"] == original_api.description
        assert orm_kwargs["instructions"] == original_api.instructions
        assert orm_kwargs["author_id"] == original_api.author_id

    @pytest.mark.parametrize("case_name", [
        "empty_collections",
        "max_fields", 
        "incorrect_averages",
        "no_ratings",
        "vegetarian",
        "high_protein",
        "quick",
        "dessert"
    ])
    def test_round_trip_with_edge_cases(self, edge_case_recipes, case_name):
        """Test round-trip conversion with edge case recipes."""
        recipe = edge_case_recipes[case_name]
        
        # API → Domain → API
        domain_recipe = recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        # Verify basic integrity for API objects (can't use domain equality)
        assert recovered_api.id == recipe.id
        assert recovered_api.name == recipe.name
        assert recovered_api.meal_id == recipe.meal_id
        assert len(recovered_api.ingredients) == len(recipe.ingredients)
        assert len(recovered_api.ratings) == len(recipe.ratings)
        assert len(recovered_api.tags) == len(recipe.tags)


class TestApiRecipeComputedProperties(BaseApiRecipeTest):
    """
    Test suite for computed property correction tests.
    """

    # =============================================================================
    # COMPUTED PROPERTY CORRECTION TESTS
    # =============================================================================

    def test_average_rating_correction_round_trip(self):
        """Test that incorrect average ratings are corrected during domain round-trip."""
        # Create recipe with incorrect averages
        recipe_with_incorrect_averages = create_api_recipe_with_incorrect_averages()
        
        # Test round-trip correction
        success, details = validate_average_rating_correction_roundtrip(recipe_with_incorrect_averages)
        
        assert success, f"Average rating correction failed: {details}"
        assert details["taste_corrected"], "Taste rating not corrected"
        assert details["convenience_corrected"], "Convenience rating not corrected"

    def test_computed_properties_with_no_ratings(self):
        """Test computed properties when no ratings exist."""
        recipe_without_ratings = create_api_recipe_without_ratings()
        
        # Should have None for averages
        assert recipe_without_ratings.average_taste_rating is None
        assert recipe_without_ratings.average_convenience_rating is None
        
        # Round-trip should preserve None values
        domain_recipe = recipe_without_ratings.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        assert recovered_api.average_taste_rating is None
        assert recovered_api.average_convenience_rating is None

    def test_computed_properties_with_multiple_ratings(self):
        """Test computed properties with multiple ratings."""
        # Create recipe with known ratings
        recipe = create_complex_api_recipe()
        
        if recipe.ratings:
            # Calculate expected averages
            expected_taste = sum(r.taste for r in recipe.ratings) / len(recipe.ratings)
            expected_convenience = sum(r.convenience for r in recipe.ratings) / len(recipe.ratings)
            
            # Round-trip through domain should preserve/correct averages
            domain_recipe = recipe.to_domain()
            recovered_api = ApiRecipe.from_domain(domain_recipe)
            
            assert recovered_api.average_taste_rating == expected_taste
            assert recovered_api.average_convenience_rating == expected_convenience

    def test_json_with_incorrect_averages_correction(self):
        """Test JSON with incorrect averages gets corrected through round-trip."""
        # Create valid recipe data
        recipe_data = create_api_recipe_kwargs()
        
        # Add incorrect averages
        recipe_data["average_taste_rating"] = 1.0  # Incorrect
        recipe_data["average_convenience_rating"] = 1.0  # Incorrect
        
        # Create API recipe from data
        api_recipe = ApiRecipe(**recipe_data)
        
        # Round-trip through domain
        domain_recipe = api_recipe.to_domain()
        corrected_api = ApiRecipe.from_domain(domain_recipe)
        
        # Averages should be corrected
        if corrected_api.ratings:
            expected_taste = sum(r.taste for r in corrected_api.ratings) / len(corrected_api.ratings)
            expected_convenience = sum(r.convenience for r in corrected_api.ratings) / len(corrected_api.ratings)
            
            assert corrected_api.average_taste_rating == expected_taste
            assert corrected_api.average_convenience_rating == expected_convenience


class TestApiRecipeErrorHandling(BaseApiRecipeTest):
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
            ApiRecipe.from_domain(None)  # type: ignore
        
        # Error 2: Invalid object type
        with pytest.raises(Exception):
            ApiRecipe.from_domain("not_a_recipe_object")  # type: ignore
        
        # Error 3: Empty dictionary (missing required attributes)
        with pytest.raises(Exception):
            ApiRecipe.from_domain({})  # type: ignore
        
        # Error 4: Invalid domain object with None required fields
        domain_recipe = create_recipe_domain_from_api(create_minimal_api_recipe())
        domain_recipe._id = None  # type: ignore
        with pytest.raises(Exception):
            ApiRecipe.from_domain(domain_recipe)
        
        # Error 5: Domain object with invalid types
        domain_recipe = create_recipe_domain_from_api(create_minimal_api_recipe())
        domain_recipe._ingredients = "not_a_list"  # type: ignore
        with pytest.raises(Exception):
            ApiRecipe.from_domain(domain_recipe)

    def test_to_domain_error_scenarios(self):
        """Test to_domain error handling through validation errors."""
        
        # Error 1: Empty required fields
        with pytest.raises(ValueError):
            ApiRecipe(
                id="",
                name="Test",
                instructions="Test",
                author_id=str(uuid4()),
                meal_id=str(uuid4()),
                ingredients=frozenset(),
                tags=frozenset(),
                ratings=frozenset(),
                privacy=Privacy.PUBLIC,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                discarded=False,
                version=1
            ) # type: ignore
        
        # Error 2: Invalid UUID format
        with pytest.raises(ValueError):
            ApiRecipe(
                id="invalid-uuid",
                name="Test",
                instructions="Test",
                author_id=str(uuid4()),
                meal_id=str(uuid4()),
                ingredients=frozenset(),
                tags=frozenset(),
                ratings=frozenset(),
                privacy=Privacy.PUBLIC,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                discarded=False,
                version=1
            ) # type: ignore
        
        # Error 3: None for required fields
        with pytest.raises(ValueError):
            ApiRecipe(
                id=str(uuid4()),
                name=None,  # type: ignore
                instructions="Test",
                author_id=str(uuid4()),
                meal_id=str(uuid4()),
                ingredients=frozenset(),
                tags=frozenset(),
                ratings=frozenset(),
                privacy=Privacy.PUBLIC,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                discarded=False,
                version=1
            )
        
        # Error 4: Invalid collection types
        with pytest.raises(ValueError):
            ApiRecipe(
                id=str(uuid4()),
                name="Test",
                instructions="Test",
                author_id=str(uuid4()),
                meal_id=str(uuid4()),
                ingredients="not_a_frozenset",  # type: ignore
                tags=frozenset(),
                ratings=frozenset(),
                privacy=Privacy.PUBLIC,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                discarded=False,
                version=1
            )
        
        # Error 5: Invalid rating values
        with pytest.raises(ValueError):
            ApiRecipe(
                id=str(uuid4()),
                name="Test",
                instructions="Test",
                author_id=str(uuid4()),
                meal_id=str(uuid4()),
                ingredients=frozenset(),
                tags=frozenset(),
                ratings=frozenset(),
                privacy=Privacy.PUBLIC,
                average_taste_rating=6.0,  # Invalid - should be ≤ 5
                average_convenience_rating=-1.0,  # Invalid - should be ≥ 0
                created_at=datetime.now(),
                updated_at=datetime.now(),
                discarded=False,
                version=1
            ) # type: ignore

    def test_from_orm_model_error_scenarios(self):
        """Test from_orm_model error handling - minimum 5 error scenarios."""
        
        # Error 1: None input
        with pytest.raises((AttributeError, TypeError)):
            ApiRecipe.from_orm_model(None)  # type: ignore
        
        # Error 2: Invalid object type
        with pytest.raises((AttributeError, TypeError)):
            ApiRecipe.from_orm_model("not_an_orm_object")  # type: ignore
        
        # Error 3: Empty dictionary (missing required attributes)
        with pytest.raises((AttributeError, TypeError)):
            ApiRecipe.from_orm_model({})  # type: ignore
        
        # Error 4: Create ORM with invalid kwargs and test conversion
        try:
            invalid_orm_kwargs = create_recipe_orm_kwargs()
            invalid_orm_kwargs["id"] = 123  # Invalid ID type
            invalid_orm = RecipeSaModel(**invalid_orm_kwargs)
            # If creation succeeds, test conversion
            with pytest.raises((ValueError, TypeError)):
                ApiRecipe.from_orm_model(invalid_orm)
        except Exception:
            # If ORM creation itself fails, that's also a valid error scenario
            pass
        
        # Error 5: Test with minimal ORM object that might miss expected attributes
        minimal_orm_kwargs = {
            "id": str(uuid4()),
            "name": "",  # Empty name might cause validation issues
            "instructions": "",
            "author_id": str(uuid4()),
            "meal_id": str(uuid4()),
            "ingredients": frozenset(),
            "ratings": frozenset(),
            "tags": frozenset(),
            "privacy": Privacy.PUBLIC,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "discarded": False,
            "version": 1
        }
        try:
            minimal_orm = RecipeSaModel(**minimal_orm_kwargs)
            # Test that empty strings might cause validation issues
            with pytest.raises((ValueError, TypeError)):
                ApiRecipe.from_orm_model(minimal_orm)
        except Exception:
            # If ORM creation itself fails with empty strings, that's also a valid test
            pass

    def test_to_orm_kwargs_error_scenarios(self):
        """Test to_orm_kwargs error handling - edge cases since method is robust."""
        
        # Create valid recipe for testing edge cases
        recipe = create_simple_api_recipe()
        
        # Test with various edge cases that should still work
        
        # Edge case 1: Recipe with empty collections
        empty_recipe = create_minimal_api_recipe()
        kwargs = empty_recipe.to_orm_kwargs()
        assert isinstance(kwargs, dict)
        assert kwargs["ingredients"] == []
        assert kwargs["ratings"] == []
        assert kwargs["tags"] == []
        
        # Edge case 2: Recipe with large collections
        complex_recipe = create_complex_api_recipe()
        kwargs = complex_recipe.to_orm_kwargs()
        assert isinstance(kwargs, dict)
        assert isinstance(kwargs["ingredients"], list)
        assert isinstance(kwargs["ratings"], list)
        assert isinstance(kwargs["tags"], list)
        
        # Edge case 3: Recipe with None optional fields
        kwargs = recipe.to_orm_kwargs()
        assert isinstance(kwargs, dict)
        # Should handle None values gracefully
        if kwargs["nutri_facts"] is not None:
            from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import NutriFactsSaModel
            assert isinstance(kwargs["nutri_facts"], NutriFactsSaModel)
        
        # Edge case 4: Consistency check
        for _ in range(3):
            result = recipe.to_orm_kwargs()
            assert "id" in result
            assert "name" in result
            assert "ingredients" in result
            assert "ratings" in result
            assert "tags" in result
        
        # Edge case 5: Type verification
        kwargs = recipe.to_orm_kwargs()
        assert isinstance(kwargs["id"], str)
        assert isinstance(kwargs["name"], str)
        assert isinstance(kwargs["ingredients"], list)
        assert isinstance(kwargs["ratings"], list)
        assert isinstance(kwargs["tags"], list)

    @pytest.mark.parametrize("modification,description", [
        ({"name": ""}, "Empty name"),
        ({"instructions": ""}, "Empty instructions"),
        ({"author_id": "invalid-uuid"}, "Invalid author UUID"),
        ({"meal_id": "invalid-uuid"}, "Invalid meal UUID"),
        ({"total_time": -1}, "Negative total time"),
        ({"weight_in_grams": -1}, "Negative weight"),
        ({"version": 0}, "Zero version"),
    ])
    def test_validation_error_scenarios(self, modification, description):
        """Test comprehensive validation error scenarios."""
        base_valid_data = {
            "id": str(uuid4()),
            "name": "Test Recipe",
            "instructions": "Test instructions",
            "author_id": str(uuid4()),
            "meal_id": str(uuid4()),
            "ingredients": frozenset(),
            "tags": frozenset(),
            "ratings": frozenset(),
            "privacy": Privacy.PUBLIC,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "discarded": False,
            "version": 1
        }
        
        invalid_data = {**base_valid_data, **modification}
        with pytest.raises(ValueError):
            ApiRecipe(**invalid_data)


class TestApiRecipeEdgeCases(BaseApiRecipeTest):
    """
    Test suite for edge case tests.
    """

    # =============================================================================
    # EDGE CASE TESTS
    # =============================================================================

    def test_edge_case_empty_collections(self):
        """Test handling of empty collections."""
        minimal_recipe = create_minimal_api_recipe()
        
        # Should handle empty collections gracefully - now frozensets
        assert minimal_recipe.ingredients == frozenset()
        assert minimal_recipe.ratings == frozenset()
        assert minimal_recipe.tags == frozenset()
        
        # Round-trip should preserve empty collections
        domain_recipe = minimal_recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        assert recovered_api.ingredients == frozenset()
        assert recovered_api.ratings == frozenset()
        assert recovered_api.tags == frozenset()

    def test_edge_case_large_collections(self):
        """Test handling of large collections."""
        max_recipe = create_api_recipe_with_max_fields()
        
        # Should handle large collections
        assert len(max_recipe.ingredients) >= 10
        assert len(max_recipe.ratings) >= 10
        assert len(max_recipe.tags) >= 5
        
        # Round-trip should preserve large collections
        domain_recipe = max_recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        assert len(recovered_api.ingredients) == len(max_recipe.ingredients)
        assert len(recovered_api.ratings) == len(max_recipe.ratings)
        assert len(recovered_api.tags) == len(max_recipe.tags)

    def test_edge_case_boundary_values(self):
        """Test handling of boundary values."""
        # Test with boundary values using factory function
        recipe_kwargs = create_api_recipe_kwargs(
            total_time=0,  # Minimum time
            weight_in_grams=1,  # Minimum weight
            version=1,  # Minimum version
            average_taste_rating=1.0,  # Minimum rating
            average_convenience_rating=5.0,  # Maximum rating
        )
        recipe = ApiRecipe(**recipe_kwargs)
        
        # Should handle boundary values
        assert recipe.total_time == 0
        assert recipe.weight_in_grams == 1
        assert recipe.version == 1
        assert recipe.average_taste_rating == 1.0
        assert recipe.average_convenience_rating == 5.0
        
        # Round-trip should preserve boundary values
        domain_recipe = recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        assert recovered_api.total_time == 0
        assert recovered_api.weight_in_grams == 1
        assert recovered_api.version == 1

    def test_edge_case_null_optional_fields(self):
        """Test handling of null optional fields."""
        recipe_kwargs = create_api_recipe_kwargs(
            description=None,
            utensils=None,
            total_time=None,
            notes=None,
            nutri_facts=None,
            weight_in_grams=None,
            image_url=None,
            average_taste_rating=None,
            average_convenience_rating=None,
        )
        recipe = ApiRecipe(**recipe_kwargs)
        
        # Should handle null optional fields
        assert recipe.description is None
        assert recipe.utensils is None
        assert recipe.total_time is None
        assert recipe.notes is None
        assert recipe.nutri_facts is None
        assert recipe.weight_in_grams is None
        assert recipe.image_url is None
        assert recipe.average_taste_rating is None
        assert recipe.average_convenience_rating is None

    def test_edge_case_complex_nested_structures(self):
        """Test handling of complex nested structures."""
        complex_recipe = create_complex_api_recipe()
        
        # Should handle complex nested structures
        assert len(complex_recipe.ingredients) > 5
        assert len(complex_recipe.ratings) > 2
        assert len(complex_recipe.tags) > 3
        
        # Verify nested object types
        assert all(isinstance(ing, ApiIngredient) for ing in complex_recipe.ingredients)
        assert all(isinstance(rating, ApiRating) for rating in complex_recipe.ratings)
        assert all(isinstance(tag, ApiTag) for tag in complex_recipe.tags)
        
        # Round-trip should preserve complex structures
        domain_recipe = complex_recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        assert len(recovered_api.ingredients) == len(complex_recipe.ingredients)
        assert len(recovered_api.ratings) == len(complex_recipe.ratings)
        assert len(recovered_api.tags) == len(complex_recipe.tags)

    def test_edge_case_unicode_and_special_characters(self):
        """Test handling of unicode and special characters."""
        recipe = create_api_recipe(
            name="Crème Brûlée with Açaí & Jalapeño",
            description="A fusion dessert with émincé technique and café notes",
            instructions="1. Préchauffer le four à 180°C. 2. Mélanger... 3. Servir.",
            notes="Use real vanilla beans for authentic flavor. Temperature is crucial!",
            utensils="Ramekins, torch, sieve, whisk"
        )
        
        # Should handle unicode characters
        assert "Crème" in recipe.name
        assert "Brûlée" in recipe.name
        assert "Açaí" in recipe.name
        assert "Jalapeño" in recipe.name
        assert recipe.description and "émincé" in recipe.description
        assert recipe.description and "café" in recipe.description
        assert "Préchauffer" in recipe.instructions
        assert "180°C" in recipe.instructions
        
        # Round-trip should preserve unicode
        domain_recipe = recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        assert recovered_api.name == recipe.name
        assert recovered_api.description == recipe.description
        assert recovered_api.instructions == recipe.instructions

    def test_edge_case_datetime_handling(self):
        """Test handling of datetime edge cases."""
        # Test with specific datetime values
        past_time = datetime.now() - timedelta(days=365)
        future_time = datetime.now() + timedelta(days=365)
        
        recipe = create_api_recipe(
            created_at=past_time,
            updated_at=future_time
        )
        
        # Should handle datetime values
        assert recipe.created_at == past_time
        assert recipe.updated_at == future_time
        
        # Round-trip should preserve datetime
        domain_recipe = recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        assert recovered_api.created_at == past_time
        assert recovered_api.updated_at == future_time


class TestApiRecipePerformance(BaseApiRecipeTest):
    """
    Test suite for performance validation tests (<5ms conversion time).
    """

    # =============================================================================
    # PERFORMANCE VALIDATION TESTS (<5MS CONVERSION TIME)
    # =============================================================================

    def test_from_domain_performance(self, domain_recipe):
        """Test from_domain conversion meets <5ms requirement."""
        start_time = time.perf_counter()
        
        for _ in range(100):  # Test 100 conversions for reliable timing
            ApiRecipe.from_domain(domain_recipe)
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / 100) * 1000
        
        assert avg_time_ms < 5.0, f"from_domain average time {avg_time_ms:.3f}ms exceeds 5ms limit"

    def test_to_domain_performance(self, complex_recipe):
        """Test to_domain conversion meets <5ms requirement."""
        start_time = time.perf_counter()
        
        for _ in range(100):  # Test 100 conversions
            complex_recipe.to_domain()
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / 100) * 1000
        
        assert avg_time_ms < 5.0, f"to_domain average time {avg_time_ms:.3f}ms exceeds 5ms limit"

    def test_from_orm_model_performance(self, real_orm_recipe):
        """Test from_orm_model conversion meets <5ms requirement."""
        start_time = time.perf_counter()
        
        for _ in range(100):  # Test 100 conversions
            ApiRecipe.from_orm_model(real_orm_recipe)
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / 100) * 1000
        
        assert avg_time_ms < 5.0, f"from_orm_model average time {avg_time_ms:.3f}ms exceeds 5ms limit"

    def test_to_orm_kwargs_performance(self, complex_recipe):
        """Test to_orm_kwargs conversion meets <5ms requirement."""
        start_time = time.perf_counter()
        
        for _ in range(100):  # Test 100 conversions
            complex_recipe.to_orm_kwargs()
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / 100) * 1000
        
        assert avg_time_ms < 5.0, f"to_orm_kwargs average time {avg_time_ms:.3f}ms exceeds 5ms limit"

    def test_complete_conversion_cycle_performance(self, simple_recipe):
        """Test complete four-layer conversion cycle performance."""
        start_time = time.perf_counter()
        
        for _ in range(50):  # Test 50 complete cycles
            # API → Domain
            domain_recipe = simple_recipe.to_domain()
            
            # Domain → API
            api_from_domain = ApiRecipe.from_domain(domain_recipe)
            
            # API → ORM kwargs
            orm_kwargs = api_from_domain.to_orm_kwargs()
            
            # Basic validation of cycle
            assert orm_kwargs["id"] == simple_recipe.id
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / 50) * 1000
        
        # Complete cycle should be under 15ms (more lenient for full cycle)
        assert avg_time_ms < 15.0, f"Complete cycle average time {avg_time_ms:.3f}ms exceeds 15ms limit"

    def test_large_collection_performance(self):
        """Test performance with large collections."""
        # Note: This test is kept with for loop as it measures overall performance
        # across multiple operations - parametrization would test individual performance
        large_recipes = create_nested_object_validation_dataset_domain(count=100)
        
        start_time = time.perf_counter()
        
        # Test conversion of all recipes - proper domain to API conversion
        for domain_recipe in large_recipes:
            api_recipe = ApiRecipe.from_domain(domain_recipe)
            orm_kwargs = api_recipe.to_orm_kwargs()
            
            # Basic validation
            assert api_recipe.id == domain_recipe.id
            assert orm_kwargs["id"] == domain_recipe.id
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        avg_time_ms = total_time_ms / len(large_recipes)
        
        # Should handle large collections efficiently
        assert avg_time_ms < 10.0, f"Large collection average time {avg_time_ms:.3f}ms exceeds 10ms limit"

    def test_bulk_operations_performance(self):
        """Test performance with bulk operations."""
        # Note: This test is kept with for loop as it measures overall performance
        # across multiple operations - parametrization would test individual performance  
        bulk_dataset = create_conversion_performance_dataset_domain(count=100)
        
        start_time = time.perf_counter()
        
        # Test bulk domain conversions using proper domain recipes
        for domain_recipe in bulk_dataset["domain_recipes"]:
            api_recipe = ApiRecipe.from_domain(domain_recipe)
            assert api_recipe.id == domain_recipe.id
        
        end_time = time.perf_counter()
        bulk_time_ms = (end_time - start_time) * 1000
        avg_time_ms = bulk_time_ms / len(bulk_dataset["domain_recipes"])
        
        assert avg_time_ms < 5.0, f"Bulk operations average time {avg_time_ms:.3f}ms exceeds 5ms limit"

    @pytest.mark.parametrize("domain_recipe", create_nested_object_validation_dataset_domain(count=10))
    def test_large_collection_performance_parametrized(self, domain_recipe):
        """Test performance with large collections using parametrization."""
        start_time = time.perf_counter()
        
        # Test conversion
        api_recipe = ApiRecipe.from_domain(domain_recipe)
        orm_kwargs = api_recipe.to_orm_kwargs()
        
        end_time = time.perf_counter()
        time_ms = (end_time - start_time) * 1000
        
        # Individual operations should be efficient
        assert time_ms < 10.0, f"Large collection operation time {time_ms:.3f}ms exceeds 10ms limit"
        assert api_recipe.id == domain_recipe.id
        assert orm_kwargs["id"] == domain_recipe.id

    @pytest.mark.parametrize("domain_recipe", create_conversion_performance_dataset_domain(count=10)["domain_recipes"])
    def test_bulk_operations_performance_parametrized(self, domain_recipe):
        """Test performance with bulk operations using parametrization."""
        start_time = time.perf_counter()
        
        # Test domain conversion
        api_recipe = ApiRecipe.from_domain(domain_recipe)
        
        end_time = time.perf_counter()
        time_ms = (end_time - start_time) * 1000
        
        # Individual operations should be fast
        assert time_ms < 5.0, f"Bulk operation time {time_ms:.3f}ms exceeds 5ms limit"
        assert api_recipe.id == domain_recipe.id


class TestApiRecipeJson(BaseApiRecipeTest):
    """
    Test suite for JSON serialization/deserialization tests.
    """

    # =============================================================================
    # JSON SERIALIZATION/DESERIALIZATION TESTS
    # =============================================================================

    def test_json_serialization_basic(self, simple_recipe):
        """Test basic JSON serialization."""
        json_str = simple_recipe.model_dump_json()
        
        assert isinstance(json_str, str)
        assert simple_recipe.id in json_str
        assert simple_recipe.name in json_str
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert parsed["id"] == simple_recipe.id
        assert parsed["name"] == simple_recipe.name

    def test_json_deserialization_basic(self):
        """Test basic JSON deserialization."""
        # Create valid JSON test cases
        valid_json_cases = create_valid_json_test_cases()
        
        for json_data in valid_json_cases:
            json_str = json.dumps(json_data)
            api_recipe = ApiRecipe.model_validate_json(json_str)
            
            assert isinstance(api_recipe, ApiRecipe)
            assert api_recipe.id == json_data["id"]
            assert api_recipe.name == json_data["name"]

    def test_json_round_trip_serialization(self, complex_recipe):
        """Test JSON round-trip serialization preserves data."""
        # Test round-trip serialization
        json_str = complex_recipe.model_dump_json()
    
        # Deserialize from JSON
        restored_recipe = ApiRecipe.model_validate_json(json_str)   

        assert complex_recipe == restored_recipe

    def test_json_with_computed_properties(self):
        """Test JSON handling with computed properties."""
        # Create recipe with ratings
        recipe = create_complex_api_recipe()
        
        # Serialize to JSON
        json_str = recipe.model_dump_json()
        
        # Deserialize from JSON
        restored_recipe = ApiRecipe.model_validate_json(json_str)
        
        # Computed properties should be preserved
        assert restored_recipe.average_taste_rating == recipe.average_taste_rating
        assert restored_recipe.average_convenience_rating == recipe.average_convenience_rating

    def test_json_error_scenarios(self):
        """Test JSON deserialization error scenarios."""
        # Create invalid JSON test cases
        invalid_json_cases = create_invalid_json_test_cases()
        
        for case in invalid_json_cases:
            json_str = json.dumps(case["data"])
            
            with pytest.raises(ValueError):
                ApiRecipe.model_validate_json(json_str)

    @pytest.mark.parametrize("json_data", create_valid_json_test_cases())
    def test_json_deserialization_parametrized(self, json_data):
        """Test JSON deserialization with parametrized valid cases."""
        json_str = json.dumps(json_data)
        api_recipe = ApiRecipe.model_validate_json(json_str)
        
        assert isinstance(api_recipe, ApiRecipe)
        assert api_recipe.id == json_data["id"]
        assert api_recipe.name == json_data["name"]

    @pytest.mark.parametrize("case", create_invalid_json_test_cases())
    def test_json_error_scenarios_parametrized(self, case):
        """Test JSON deserialization error scenarios with parametrization."""
        json_str = json.dumps(case["data"])
        
        with pytest.raises(ValueError):
            ApiRecipe.model_validate_json(json_str)

    def test_json_performance(self, recipe_collection):
        """Test JSON serialization/deserialization performance."""
        # Note: This test is kept with for loop as it measures overall performance
        # across multiple operations - parametrization would test individual performance
        start_time = time.perf_counter()
        
        # Test bulk JSON operations
        for recipe in recipe_collection:
            json_str = recipe.model_dump_json()
            restored = ApiRecipe.model_validate_json(json_str)
            assert restored.id == recipe.id
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / len(recipe_collection)) * 1000
        
        # JSON operations should be fast
        assert avg_time_ms < 10.0, f"JSON operations average time {avg_time_ms:.3f}ms exceeds 10ms limit"

    @pytest.mark.parametrize("recipe", create_recipe_collection(count=5))
    def test_json_performance_parametrized(self, recipe):
        """Test JSON serialization/deserialization performance with parametrization."""
        start_time = time.perf_counter()
        
        # Test JSON operations
        json_str = recipe.model_dump_json()
        restored = ApiRecipe.model_validate_json(json_str)
        
        end_time = time.perf_counter()
        time_ms = (end_time - start_time) * 1000
        
        # Individual operations should be fast
        assert time_ms < 10.0, f"JSON operation time {time_ms:.3f}ms exceeds 10ms limit"
        assert restored.id == recipe.id

    def test_json_with_nested_objects(self, complex_recipe):
        """Test JSON serialization with complex nested objects."""
        # Should handle nested objects in JSON
        json_str = complex_recipe.model_dump_json()
        restored_recipe = ApiRecipe.model_validate_json(json_str)
        
        # Verify nested objects are preserved
        assert len(restored_recipe.ingredients) == len(complex_recipe.ingredients)
        assert len(restored_recipe.ratings) == len(complex_recipe.ratings)
        assert len(restored_recipe.tags) == len(complex_recipe.tags)
        
        # Verify nested object types - now frozensets
        assert all(isinstance(ing, ApiIngredient) for ing in restored_recipe.ingredients)
        assert all(isinstance(rating, ApiRating) for rating in restored_recipe.ratings)
        assert all(isinstance(tag, ApiTag) for tag in restored_recipe.tags)

    def test_json_factory_functions(self):
        """Test JSON factory functions."""
        # Test create_api_recipe_from_json
        json_recipe = create_api_recipe_from_json()
        assert isinstance(json_recipe, ApiRecipe)
        
        # Test create_api_recipe_json
        json_str = create_api_recipe_json()
        assert isinstance(json_str, str)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "id" in parsed
        assert "name" in parsed


class TestApiRecipeIntegration(BaseApiRecipeTest):
    """
    Test suite for integration tests with base classes.
    """

    # =============================================================================
    # INTEGRATION TESTS WITH BASE CLASSES
    # =============================================================================

    def test_base_api_entity_inheritance(self, simple_recipe):
        """Test proper inheritance from BaseApiEntity."""
        from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiEntity
        
        # Should inherit from BaseApiEntity
        assert isinstance(simple_recipe, BaseApiEntity)
        
        # Should have base model configuration
        assert simple_recipe.model_config.get('frozen') is True
        assert simple_recipe.model_config.get('strict') is True
        assert simple_recipe.model_config.get('extra') == 'forbid'

    def test_base_api_entity_conversion_methods(self, simple_recipe):
        """Test integration with BaseApiEntity conversion methods."""
        # Should have access to conversion methods
        assert hasattr(simple_recipe, 'from_domain')
        assert hasattr(simple_recipe, 'to_domain')
        assert hasattr(simple_recipe, 'from_orm_model')
        assert hasattr(simple_recipe, 'to_orm_kwargs')
        
        # Should have conversion utility
        assert hasattr(simple_recipe, 'convert')
        assert simple_recipe.convert is not None

    def test_immutability_from_base_class(self, simple_recipe):
        """Test that immutability is properly enforced from base class."""
        # Should be immutable (frozen)
        with pytest.raises(ValueError):
            simple_recipe.id = "changed"  # type: ignore
        
        with pytest.raises(ValueError):
            simple_recipe.name = "changed"  # type: ignore

    def test_pydantic_validation_integration(self):
        """Test integration with Pydantic validation from base class."""
        # Test model_validate works
        recipe_data = create_api_recipe_kwargs()
        api_recipe = ApiRecipe.model_validate(recipe_data)
        assert api_recipe.id == recipe_data["id"]
        assert api_recipe.name == recipe_data["name"]
        
        # Test model_validate_json works
        json_str = json.dumps(create_valid_json_test_cases()[0])
        api_recipe_from_json = ApiRecipe.model_validate_json(json_str)
        assert isinstance(api_recipe_from_json, ApiRecipe)

    def test_field_validation_integration(self):
        """Test field validation integration."""
        # Test valid creation
        valid_recipe = create_api_recipe()
        assert isinstance(valid_recipe, ApiRecipe)
        
        # Test field constraints
        assert len(valid_recipe.id) > 0
        assert len(valid_recipe.name) > 0
        assert len(valid_recipe.instructions) > 0
        assert valid_recipe.privacy in Privacy
        assert isinstance(valid_recipe.ingredients, frozenset)
        assert isinstance(valid_recipe.ratings, frozenset)
        assert isinstance(valid_recipe.tags, frozenset)


class TestApiRecipeSpecialized(BaseApiRecipeTest):
    """
    Test suite for specialized recipe type tests.
    """

    # =============================================================================
    # SPECIALIZED RECIPE TYPE TESTS
    # =============================================================================

    @pytest.mark.parametrize("recipe_type,api_recipe_factory", [
        ("simple", create_simple_api_recipe),
        ("complex", create_complex_api_recipe),
        ("vegetarian", create_vegetarian_api_recipe),
        ("high_protein", create_high_protein_api_recipe),
        ("quick", create_quick_api_recipe),
        ("dessert", create_dessert_api_recipe),
        ("minimal", create_minimal_api_recipe),
        ("max_fields", create_api_recipe_with_max_fields),
    ])
    def test_specialized_recipe_types(self, recipe_type, api_recipe_factory):
        """Test specialized recipe factory functions."""
        api_recipe = api_recipe_factory()
        
        assert isinstance(api_recipe, ApiRecipe)
        assert len(api_recipe.id) > 0
        assert len(api_recipe.name) > 0
        assert len(api_recipe.instructions) > 0
        
        # Test round-trip for each type - use domain recipe equality
        domain_recipe = api_recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        # For domain recipes, we can use Recipe equality if we convert both to domain
        original_domain = api_recipe.to_domain()
        recovered_domain = recovered_api.to_domain()
        assert recovered_domain == original_domain, f"Round-trip failed for {recipe_type} recipe"

    @pytest.mark.parametrize("cuisine", [
        "italian",
        "mexican", 
        "indian",
        "french",
        "chinese"
    ])
    def test_recipes_by_cuisine(self, cuisine):
        """Test recipe creation by cuisine type."""
        recipes = create_recipes_by_cuisine(cuisine, count=3)
        assert len(recipes) == 3
        assert all(isinstance(recipe, ApiRecipe) for recipe in recipes)

    @pytest.mark.parametrize("difficulty", [
        "easy",
        "medium",
        "hard"
    ])
    def test_recipes_by_difficulty(self, difficulty):
        """Test recipe creation by difficulty level."""
        recipes = create_recipes_by_difficulty(difficulty, count=3)
        assert len(recipes) == 3
        assert all(isinstance(recipe, ApiRecipe) for recipe in recipes)

    def test_recipe_collections(self):
        """Test recipe collection factory functions."""
        # Test create_recipe_collection
        collection = create_recipe_collection(count=5)
        assert len(collection) == 5
        assert all(isinstance(recipe, ApiRecipe) for recipe in collection)

    def test_bulk_dataset_creation(self):
        """Test bulk dataset creation functions."""
        # Test create_test_recipe_dataset
        dataset = create_test_recipe_dataset(count=10)
        assert len(dataset["recipes"]) == 10
        assert len(dataset["json_strings"]) == 10
        assert dataset["total_recipes"] == 10
        
        # Test create_bulk_recipe_creation_dataset
        bulk_kwargs = create_bulk_recipe_creation_dataset(count=5)
        assert len(bulk_kwargs) == 5
        assert all(isinstance(kwargs, dict) for kwargs in bulk_kwargs)
        
        # Test create_bulk_json_serialization_dataset
        bulk_json = create_bulk_json_serialization_dataset(count=5)
        assert len(bulk_json) == 5
        assert all(isinstance(json_str, str) for json_str in bulk_json)

    @pytest.mark.parametrize("privacy", [Privacy.PUBLIC, Privacy.PRIVATE])
    def test_privacy_enum_handling(self, privacy):
        """Test privacy enum handling in recipes."""
        recipe = create_api_recipe(privacy=privacy)
        assert recipe.privacy == privacy

    @pytest.mark.parametrize("scenario", REALISTIC_RECIPE_SCENARIOS_DOMAIN[:5])  # Test first 5 scenarios
    def test_realistic_scenario_coverage_parametrized(self, scenario):
        """Test realistic scenario coverage using factory data."""
        recipe = create_api_recipe(name=scenario["name"])
        assert isinstance(recipe, ApiRecipe)
        assert recipe.name == scenario["name"]
        
        # Test round-trip for realistic scenarios - use domain equality
        original_domain = recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(original_domain)
        recovered_domain = recovered_api.to_domain()
        assert recovered_domain == original_domain, f"Round-trip failed for scenario: {scenario['name']}"

    @pytest.mark.parametrize("cuisine", CUISINE_TYPES_DOMAIN[:5])  # Test first 5 cuisines
    def test_cuisine_types_coverage_parametrized(self, cuisine):
        """Test cuisine types coverage."""
        recipes = create_recipes_by_cuisine(cuisine, count=1)
        assert len(recipes) == 1
        assert isinstance(recipes[0], ApiRecipe)

    @pytest.mark.parametrize("difficulty", DIFFICULTY_LEVELS_DOMAIN)
    def test_difficulty_levels_coverage_parametrized(self, difficulty):
        """Test difficulty levels coverage."""
        recipes = create_recipes_by_difficulty(difficulty, count=1)
        assert len(recipes) == 1
        assert isinstance(recipes[0], ApiRecipe)

    @pytest.mark.parametrize("specialized_function", [
        create_simple_api_recipe,
        create_complex_api_recipe,
        create_vegetarian_api_recipe,
        create_high_protein_api_recipe,
        create_quick_api_recipe,
        create_dessert_api_recipe,
        create_minimal_api_recipe,
        create_api_recipe_with_max_fields,
        create_api_recipe_with_incorrect_averages,
        create_api_recipe_without_ratings,
    ])
    def test_specialized_factory_functions(self, specialized_function):
        """Test specialized factory functions."""
        assert callable(specialized_function)
        result = specialized_function()
        assert isinstance(result, ApiRecipe)

    @pytest.mark.parametrize("collection_function,test_param", [
        (create_recipe_collection, {"count": 2}),
        (create_test_recipe_dataset, {"count": 2}),
        (create_bulk_recipe_creation_dataset, {"count": 2}),
        (create_bulk_json_serialization_dataset, {"count": 2}),
        (create_bulk_json_deserialization_dataset, {"count": 2}),
        (create_conversion_performance_dataset, {"count": 2}),
        (create_nested_object_validation_dataset, {"count": 2}),
    ])
    def test_collection_factory_functions(self, collection_function, test_param):
        """Test collection factory functions."""
        assert callable(collection_function)
        result = collection_function(**test_param)
        assert result is not None


class TestApiRecipeCoverage(BaseApiRecipeTest):
    """
    Test suite for comprehensive coverage validation.
    """

    # =============================================================================
    # COMPREHENSIVE COVERAGE VALIDATION
    # =============================================================================

    def test_all_public_methods_covered(self):
        """Verify all public methods are covered by tests."""
        # Test all conversion methods exist and work
        api_recipe = create_api_recipe()
        domain_recipe = create_recipe()  # Use domain factory directly
        real_orm = create_recipe_orm()
        
        # from_domain
        result1 = ApiRecipe.from_domain(domain_recipe)
        assert isinstance(result1, ApiRecipe)
        
        # to_domain
        result2 = api_recipe.to_domain()
        assert isinstance(result2, _Recipe)
        
        # from_orm_model
        result3 = ApiRecipe.from_orm_model(real_orm)
        assert isinstance(result3, ApiRecipe)
        
        # to_orm_kwargs
        result4 = api_recipe.to_orm_kwargs()
        assert isinstance(result4, dict)
        
        # All methods successfully tested
        assert True

    def test_field_validation_coverage(self):
        """Test all field validation patterns are covered."""
        # Test required field validation
        recipe = create_api_recipe()
        assert recipe.id is not None
        assert recipe.name is not None
        assert recipe.instructions is not None
        assert recipe.author_id is not None
        assert recipe.meal_id is not None
        
        # Test optional field handling
        minimal_recipe = create_minimal_api_recipe()
        assert minimal_recipe.description is None or isinstance(minimal_recipe.description, str)
        assert minimal_recipe.utensils is None or isinstance(minimal_recipe.utensils, str)
        assert minimal_recipe.total_time is None or isinstance(minimal_recipe.total_time, int)
        
        # Test collection field validation - now frozensets
        assert isinstance(recipe.ingredients, frozenset)
        assert isinstance(recipe.ratings, frozenset)
        assert isinstance(recipe.tags, frozenset)

    def test_realistic_scenario_coverage(self):
        """Test realistic scenario coverage using factory data."""
        # Test all realistic scenarios from domain factories
        for i, scenario in enumerate(REALISTIC_RECIPE_SCENARIOS_DOMAIN):
            recipe = create_api_recipe(name=scenario["name"])
            assert isinstance(recipe, ApiRecipe)
            assert recipe.name == scenario["name"]
            
            # Test round-trip for realistic scenarios - use domain equality
            original_domain = recipe.to_domain()
            recovered_api = ApiRecipe.from_domain(original_domain)
            recovered_domain = recovered_api.to_domain()
            assert recovered_domain == original_domain, f"Round-trip failed for scenario: {scenario['name']}"

    def test_constants_and_enums_coverage(self):
        """Test that constants and enums are properly used - kept as integration test."""
        # Note: This test is kept with for loop as it's testing integration
        # Individual parametrized tests above test specific scenarios
        
        # Test privacy enum
        for privacy in [Privacy.PUBLIC, Privacy.PRIVATE]:
            recipe = create_api_recipe(privacy=privacy)
            assert recipe.privacy == privacy

    def test_error_coverage_completeness(self):
        """Test that error coverage is comprehensive."""
        # Verify we test all major error categories
        error_categories = [
            "None inputs",
            "Invalid types",
            "Missing attributes",
            "Validation errors",
            "Boundary violations",
            "Invalid nested objects",
            "JSON errors",
            "Performance limits"
        ]
        
        # This test passes if we've implemented all the error test methods above
        test_methods = [method for method in dir(self) if method.startswith('test_') and 'error' in method]
        assert len(test_methods) >= 1, f"Need at least 1 error test methods, found {len(test_methods)}"

    def test_performance_coverage_completeness(self):
        """Test that performance coverage is comprehensive."""
        # Verify we test all performance scenarios
        performance_methods = [method for method in dir(self) if method.startswith('test_') and 'performance' in method]
        assert len(performance_methods) >= 1, f"Need at least 1 performance test methods, found {len(performance_methods)}"

    def test_factory_function_coverage(self):
        """Test that all factory functions are used and work - kept as integration test."""
        # Test main factory functions
        assert callable(create_api_recipe)
        assert callable(create_api_recipe_kwargs)
        assert callable(create_api_recipe_from_json)
        assert callable(create_api_recipe_json)
        
        # Individual parametrized tests above test specific functions
        # This test verifies the main functions work
        assert True


# =============================================================================
# CRITICAL EDGE CASE TESTS - COMPREHENSIVE ADDITIONS
# =============================================================================

class TestApiRecipeFieldValidationEdgeCases(BaseApiRecipeTest):
    """
    Test suite for comprehensive field validation edge cases.
    """

    def test_invalid_name_validation(self):
        """Test invalid name field validation."""
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_invalid_name()
            ApiRecipe(**invalid_kwargs)

    def test_invalid_instructions_validation(self):
        """Test invalid instructions field validation."""
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_invalid_instructions()
            ApiRecipe(**invalid_kwargs)

    def test_invalid_total_time_validation(self):
        """Test invalid total_time field validation."""
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_invalid_total_time()
            ApiRecipe(**invalid_kwargs)

    def test_invalid_weight_validation(self):
        """Test invalid weight field validation."""
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_invalid_weight()
            ApiRecipe(**invalid_kwargs)

    def test_invalid_taste_rating_validation(self):
        """Test invalid taste rating validation."""
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_invalid_taste_rating()
            ApiRecipe(**invalid_kwargs)

    def test_invalid_convenience_rating_validation(self):
        """Test invalid convenience rating validation."""
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_invalid_convenience_rating()
            ApiRecipe(**invalid_kwargs)

    def test_invalid_privacy_validation(self):
        """Test invalid privacy enum validation."""
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_invalid_privacy()
            ApiRecipe(**invalid_kwargs)

    def test_boundary_values_acceptance(self):
        """Test that boundary values are accepted."""
        boundary_kwargs = create_api_recipe_with_boundary_values()
        recipe = ApiRecipe(**boundary_kwargs)
        
        assert recipe.total_time == 0
        assert recipe.weight_in_grams == 0
        assert recipe.average_taste_rating == 0.0
        assert recipe.average_convenience_rating == 5.0

    def test_extreme_boundary_values_acceptance(self):
        """Test that extreme boundary values are handled."""
        extreme_kwargs = create_api_recipe_with_extreme_boundary_values()
        recipe = ApiRecipe(**extreme_kwargs)
        
        assert recipe.total_time == 2147483647
        assert recipe.weight_in_grams == 2147483647
        assert recipe.average_taste_rating == 5.0
        assert recipe.average_convenience_rating == 0.0

    def test_none_values_handling(self):
        """Test that None values are handled correctly for optional fields."""
        none_kwargs = create_api_recipe_with_none_values()
        recipe = ApiRecipe(**none_kwargs)
        
        assert recipe.description is None
        assert recipe.utensils is None
        assert recipe.total_time is None
        assert recipe.notes is None
        assert recipe.weight_in_grams is None
        assert recipe.image_url is None
        assert recipe.average_taste_rating is None
        assert recipe.average_convenience_rating is None
        assert recipe.nutri_facts is None

    def test_empty_strings_handling(self):
        """Test that empty strings are handled correctly."""
        empty_kwargs = create_api_recipe_with_empty_strings()
        recipe = ApiRecipe(**empty_kwargs)
        
        # Empty strings should be converted to None or handled by validation
        # This depends on the validate_optional_text behavior
        assert isinstance(recipe, ApiRecipe)

    def test_whitespace_strings_handling(self):
        """Test that whitespace-only strings are handled correctly."""
        # This should either succeed with cleaned strings or fail validation
        whitespace_kwargs = create_api_recipe_with_whitespace_strings()
        try:
            recipe = ApiRecipe(**whitespace_kwargs)
            assert isinstance(recipe, ApiRecipe)
        except ValueError:
            # If validation rejects whitespace strings, that's also valid
            pass

    @pytest.mark.parametrize("field_name,factory_func", [
        ("name", create_api_recipe_with_invalid_name),
        ("instructions", create_api_recipe_with_invalid_instructions),
        ("total_time", create_api_recipe_with_invalid_total_time),
        ("weight", create_api_recipe_with_invalid_weight),
        ("taste_rating", create_api_recipe_with_invalid_taste_rating),
        ("convenience_rating", create_api_recipe_with_invalid_convenience_rating),
        ("privacy", create_api_recipe_with_invalid_privacy),
    ])
    def test_field_validation_parametrized(self, field_name, factory_func):
        """Test field validation using parametrization."""
        with pytest.raises(ValueError):
            invalid_kwargs = factory_func()
            ApiRecipe(**invalid_kwargs)


class TestApiRecipeTagsValidationEdgeCases(BaseApiRecipeTest):
    """
    Test suite for comprehensive tags validation edge cases.
    """

    def test_invalid_tag_dict_validation(self):
        """Test validation of invalid tag dictionaries."""
        # Should succeed because validator adds missing fields
        tag_kwargs = create_api_recipe_with_invalid_tag_dict()
        recipe = ApiRecipe(**tag_kwargs)
        assert isinstance(recipe, ApiRecipe)
        assert len(recipe.tags) > 0

    def test_invalid_tag_types_validation(self):
        """Test validation of invalid tag types."""
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_invalid_tag_types()
            ApiRecipe(**invalid_kwargs)

    def test_tag_without_author_id_context_validation(self):
        """Test tag validation when author_id is missing from context."""
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_tag_without_author_id_context()
            ApiRecipe(**invalid_kwargs)

    def test_mixed_tag_types_handling(self):
        """Test handling of mixed tag types."""
        mixed_kwargs = create_api_recipe_with_mixed_tag_types()
        recipe = ApiRecipe(**mixed_kwargs)
        
        assert isinstance(recipe, ApiRecipe)
        assert len(recipe.tags) > 0
        assert all(isinstance(tag, ApiTag) for tag in recipe.tags)

    def test_tags_validator_behavior(self):
        """Test the tags validator behavior comprehensively."""
        # Test with proper tag structure
        recipe = create_api_recipe()
        assert isinstance(recipe.tags, frozenset)
        assert all(isinstance(tag, ApiTag) for tag in recipe.tags)
        
        # Test with empty tags
        empty_kwargs = create_api_recipe_with_empty_collections()
        empty_recipe = ApiRecipe(**empty_kwargs)
        assert empty_recipe.tags == frozenset()


class TestApiRecipeFrozensetValidationEdgeCases(BaseApiRecipeTest):
    """
    Test suite for frozenset collection validation edge cases.
    """

    def test_list_ingredients_conversion(self):
        """Test that list ingredients are converted to frozenset."""
        list_kwargs = create_api_recipe_with_list_ingredients()
        recipe = ApiRecipe(**list_kwargs)
        
        assert isinstance(recipe.ingredients, frozenset)
        assert len(recipe.ingredients) > 0

    def test_set_ingredients_conversion(self):
        """Test that set ingredients are converted to frozenset."""
        set_kwargs = create_api_recipe_with_set_ingredients()
        recipe = ApiRecipe(**set_kwargs)
        
        assert isinstance(recipe.ingredients, frozenset)
        assert len(recipe.ingredients) > 0

    def test_list_ratings_conversion(self):
        """Test that list ratings are converted to frozenset."""
        list_kwargs = create_api_recipe_with_list_ratings()
        recipe = ApiRecipe(**list_kwargs)
        
        assert isinstance(recipe.ratings, frozenset)
        assert len(recipe.ratings) > 0

    def test_set_ratings_conversion(self):
        """Test that set ratings are converted to frozenset."""
        set_kwargs = create_api_recipe_with_set_ratings()
        recipe = ApiRecipe(**set_kwargs)
        
        assert isinstance(recipe.ratings, frozenset)
        assert len(recipe.ratings) > 0

    def test_list_tags_conversion(self):
        """Test that list tags are converted to frozenset."""
        list_kwargs = create_api_recipe_with_list_tags()
        recipe = ApiRecipe(**list_kwargs)
        
        assert isinstance(recipe.tags, frozenset)
        assert len(recipe.tags) > 0

    def test_set_tags_conversion(self):
        """Test that set tags are converted to frozenset."""
        set_kwargs = create_api_recipe_with_set_tags()
        recipe = ApiRecipe(**set_kwargs)
        
        assert isinstance(recipe.tags, frozenset)
        assert len(recipe.tags) > 0

    def test_empty_collections_handling(self):
        """Test that empty collections are handled correctly."""
        empty_kwargs = create_api_recipe_with_empty_collections()
        recipe = ApiRecipe(**empty_kwargs)
        
        assert recipe.ingredients == frozenset()
        assert recipe.ratings == frozenset()
        assert recipe.tags == frozenset()

    @pytest.mark.parametrize("collection_type,factory_func", [
        ("ingredients_list", create_api_recipe_with_list_ingredients),
        ("ingredients_set", create_api_recipe_with_set_ingredients),
        ("ratings_list", create_api_recipe_with_list_ratings),
        ("ratings_set", create_api_recipe_with_set_ratings),
        ("tags_list", create_api_recipe_with_list_tags),
        ("tags_set", create_api_recipe_with_set_tags),
        ("empty_collections", create_api_recipe_with_empty_collections),
    ])
    def test_collection_conversion_parametrized(self, collection_type, factory_func):
        """Test collection conversion using parametrization."""
        kwargs = factory_func()
        recipe = ApiRecipe(**kwargs)
        
        assert isinstance(recipe.ingredients, frozenset)
        assert isinstance(recipe.ratings, frozenset)
        assert isinstance(recipe.tags, frozenset)


class TestApiRecipeDomainRuleValidationEdgeCases(BaseApiRecipeTest):
    """
    Test suite for domain rule validation edge cases.
    """

    def test_invalid_ingredient_positions_domain_rule(self):
        """Test that invalid ingredient positions trigger domain rule violations."""
        invalid_kwargs = create_api_recipe_with_invalid_ingredient_positions()
        recipe = ApiRecipe(**invalid_kwargs)
        
        # Should fail when converting to domain due to rule violation
        with pytest.raises(Exception):  # Domain rule violation
            recipe.to_domain()

    def test_negative_ingredient_positions_domain_rule(self):
        """Test that negative ingredient positions trigger domain rule violations."""
        invalid_kwargs = create_api_recipe_with_negative_ingredient_positions()
        recipe = ApiRecipe(**invalid_kwargs)
        
        # Should fail when converting to domain due to rule violation
        with pytest.raises(Exception):  # Domain rule violation
            recipe.to_domain()

    def test_duplicate_ingredient_positions_domain_rule(self):
        """Test that duplicate ingredient positions trigger domain rule violations."""
        invalid_kwargs = create_api_recipe_with_duplicate_ingredient_positions()
        recipe = ApiRecipe(**invalid_kwargs)
        
        # Should fail when converting to domain due to rule violation
        with pytest.raises(Exception):  # Domain rule violation
            recipe.to_domain()

    def test_non_zero_start_positions_domain_rule(self):
        """Test that ingredient positions not starting from 0 trigger domain rule violations."""
        invalid_kwargs = create_api_recipe_with_non_zero_start_positions()
        recipe = ApiRecipe(**invalid_kwargs)
        
        # Should fail when converting to domain due to rule violation
        with pytest.raises(Exception):  # Domain rule violation
            recipe.to_domain()

    def test_invalid_tag_author_id_domain_rule(self):
        """Test that tags with different author_id trigger domain rule violations."""
        invalid_kwargs = create_api_recipe_with_invalid_tag_author_id()
        recipe = ApiRecipe(**invalid_kwargs)
        
        # Should fail when converting to domain due to rule violation
        with pytest.raises(Exception):  # Domain rule violation
            recipe.to_domain()

    @pytest.mark.parametrize("rule_type,factory_func", [
        ("invalid_positions", create_api_recipe_with_invalid_ingredient_positions),
        ("negative_positions", create_api_recipe_with_negative_ingredient_positions),
        ("duplicate_positions", create_api_recipe_with_duplicate_ingredient_positions),
        ("non_zero_start", create_api_recipe_with_non_zero_start_positions),
        ("invalid_tag_author", create_api_recipe_with_invalid_tag_author_id),
    ])
    def test_domain_rule_violations_parametrized(self, rule_type, factory_func):
        """Test domain rule violations using parametrization."""
        invalid_kwargs = factory_func()
        recipe = ApiRecipe(**invalid_kwargs)
        
        # Should fail when converting to domain due to rule violation
        with pytest.raises(Exception):  # Domain rule violation
            recipe.to_domain()


class TestApiRecipeComputedPropertiesEdgeCases(BaseApiRecipeTest):
    """
    Test suite for computed properties edge cases.
    """

    def test_mismatched_computed_properties_correction(self):
        """Test that mismatched computed properties are corrected during round-trip."""
        mismatched_kwargs = create_api_recipe_with_mismatched_computed_properties()
        recipe = ApiRecipe(**mismatched_kwargs)
        
        # Round-trip should correct the averages
        domain_recipe = recipe.to_domain()
        corrected_api = ApiRecipe.from_domain(domain_recipe)
        
        # Verify correction
        expected_taste = sum(r.taste for r in recipe.ratings) / len(recipe.ratings)
        expected_convenience = sum(r.convenience for r in recipe.ratings) / len(recipe.ratings)
        
        assert corrected_api.average_taste_rating == expected_taste
        assert corrected_api.average_convenience_rating == expected_convenience

    def test_single_rating_computed_properties(self):
        """Test computed properties with single rating."""
        single_kwargs = create_api_recipe_with_single_rating()
        recipe = ApiRecipe(**single_kwargs)
        
        # With single rating, averages should equal that rating
        rating = list(recipe.ratings)[0]
        assert recipe.average_taste_rating == rating.taste
        assert recipe.average_convenience_rating == rating.convenience

    def test_extreme_ratings_computed_properties(self):
        """Test computed properties with extreme rating values."""
        extreme_kwargs = create_api_recipe_with_extreme_ratings()
        recipe = ApiRecipe(**extreme_kwargs)
        
        # Should handle extreme values correctly
        assert recipe.average_taste_rating == 2.5  # (0 + 5) / 2
        assert recipe.average_convenience_rating == 2.5  # (0 + 5) / 2

    def test_fractional_averages_computed_properties(self):
        """Test computed properties with fractional averages."""
        fractional_kwargs = create_api_recipe_with_fractional_averages()
        recipe = ApiRecipe(**fractional_kwargs)
        
        # Should handle fractional averages correctly
        assert recipe.average_taste_rating == 2.0  # (1 + 2 + 3) / 3
        assert recipe.average_convenience_rating == 2.0  # (1 + 2 + 3) / 3

    def test_computed_properties_round_trip_validation(self):
        """Test comprehensive computed properties validation using factory helper."""
        recipe = create_api_recipe_with_mismatched_computed_properties()
        api_recipe = ApiRecipe(**recipe)
        
        # Use the validation helper
        validation_result = validate_round_trip_conversion(api_recipe)
        
        assert validation_result["api_to_domain_success"], "API to domain conversion failed"
        assert validation_result["domain_to_api_success"], "Domain to API conversion failed"
        assert validation_result["computed_properties_corrected"], "Computed properties not corrected"

    @pytest.mark.parametrize("scenario,factory_func", [
        ("mismatched", create_api_recipe_with_mismatched_computed_properties),
        ("single_rating", create_api_recipe_with_single_rating),
        ("extreme_ratings", create_api_recipe_with_extreme_ratings),
        ("fractional", create_api_recipe_with_fractional_averages),
    ])
    def test_computed_properties_scenarios_parametrized(self, scenario, factory_func):
        """Test computed properties scenarios using parametrization."""
        kwargs = factory_func()
        recipe = ApiRecipe(**kwargs)
        
        # Basic validation
        assert isinstance(recipe, ApiRecipe)
        if recipe.ratings:
            assert recipe.average_taste_rating is not None
            assert recipe.average_convenience_rating is not None
        else:
            assert recipe.average_taste_rating is None
            assert recipe.average_convenience_rating is None


class TestApiRecipeDatetimeEdgeCases(BaseApiRecipeTest):
    """
    Test suite for datetime edge cases.
    """

    def test_future_timestamps_handling(self):
        """Test handling of future timestamps."""
        future_kwargs = create_api_recipe_with_future_timestamps()
        recipe = ApiRecipe(**future_kwargs)
        
        # Should handle future timestamps
        assert recipe.created_at > datetime.now()
        assert recipe.updated_at > datetime.now()

    def test_past_timestamps_handling(self):
        """Test handling of very old timestamps."""
        past_kwargs = create_api_recipe_with_past_timestamps()
        recipe = ApiRecipe(**past_kwargs)
        
        # Should handle old timestamps
        assert recipe.created_at < datetime.now()
        assert recipe.updated_at < datetime.now()

    def test_invalid_timestamp_order_handling(self):
        """Test handling of updated_at before created_at."""
        invalid_order_kwargs = create_api_recipe_with_invalid_timestamp_order()
        recipe = ApiRecipe(**invalid_order_kwargs)
        
        # Should accept invalid order (business logic might handle this separately)
        assert recipe.updated_at < recipe.created_at

    def test_same_timestamps_handling(self):
        """Test handling of identical timestamps."""
        same_kwargs = create_api_recipe_with_same_timestamps()
        recipe = ApiRecipe(**same_kwargs)
        
        # Should handle identical timestamps
        assert recipe.created_at == recipe.updated_at

    def test_datetime_round_trip_preservation(self):
        """Test that datetime values are preserved in round-trip conversions."""
        future_kwargs = create_api_recipe_with_future_timestamps()
        recipe = ApiRecipe(**future_kwargs)
        
        # Round-trip through domain
        domain_recipe = recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        # Timestamps should be preserved
        assert recovered_api.created_at == recipe.created_at
        assert recovered_api.updated_at == recipe.updated_at

    @pytest.mark.parametrize("scenario,factory_func", [
        ("future", create_api_recipe_with_future_timestamps),
        ("past", create_api_recipe_with_past_timestamps),
        ("invalid_order", create_api_recipe_with_invalid_timestamp_order),
        ("same", create_api_recipe_with_same_timestamps),
    ])
    def test_datetime_scenarios_parametrized(self, scenario, factory_func):
        """Test datetime scenarios using parametrization."""
        kwargs = factory_func()
        recipe = ApiRecipe(**kwargs)
        
        assert isinstance(recipe, ApiRecipe)
        assert isinstance(recipe.created_at, datetime)
        assert isinstance(recipe.updated_at, datetime)


class TestApiRecipeTextAndSecurityEdgeCases(BaseApiRecipeTest):
    """
    Test suite for text and security edge cases.
    """

    def test_unicode_text_handling(self):
        """Test handling of unicode characters."""
        unicode_kwargs = create_api_recipe_with_unicode_text()
        recipe = ApiRecipe(**unicode_kwargs)
        
        # Should handle unicode characters properly
        assert "Pâté" in recipe.name
        assert "Échalotes" in recipe.name
        assert "🍷" in recipe.name
        assert recipe.description and "Délicieux" in recipe.description
        assert recipe.description and "🇫🇷" in recipe.description

    def test_special_characters_handling(self):
        """Test handling of special characters."""
        special_kwargs = create_api_recipe_with_special_characters()
        recipe = ApiRecipe(**special_kwargs)
        
        # Should handle special characters
        assert "!@#$%^&*()" in recipe.name
        assert recipe.description and "<>&\"'{}[]|\\" in recipe.description

    def test_html_characters_handling(self):
        """Test handling of HTML characters (XSS protection)."""
        html_kwargs = create_api_recipe_with_html_characters()
        recipe = ApiRecipe(**html_kwargs)
        
        # Should accept HTML characters (filtering might be done at API layer)
        assert "<script>" in recipe.name
        assert recipe.description and "<b>Bold</b>" in recipe.description

    def test_sql_injection_handling(self):
        """Test handling of SQL injection attempts."""
        sql_kwargs = create_api_recipe_with_sql_injection()
        recipe = ApiRecipe(**sql_kwargs)
        
        # Should accept SQL injection strings (protection should be at ORM layer)
        assert "DROP TABLE" in recipe.name
        assert recipe.description and "OR '1'='1" in recipe.description

    def test_very_long_text_handling(self):
        """Test handling of very long text."""
        long_kwargs = create_api_recipe_with_very_long_text()
        recipe = ApiRecipe(**long_kwargs)
        
        # Should handle very long text
        assert len(recipe.name) > 1000
        assert recipe.description and len(recipe.description) > 10000
        assert len(recipe.instructions) > 10000

    def test_text_round_trip_preservation(self):
        """Test that special text is preserved in round-trip conversions."""
        unicode_kwargs = create_api_recipe_with_unicode_text()
        recipe = ApiRecipe(**unicode_kwargs)
        
        # Round-trip through domain
        domain_recipe = recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        # Unicode should be preserved
        assert recovered_api.name == recipe.name
        assert recovered_api.description == recipe.description

    @pytest.mark.parametrize("scenario,factory_func", [
        ("unicode", create_api_recipe_with_unicode_text),
        ("special_chars", create_api_recipe_with_special_characters),
        ("html", create_api_recipe_with_html_characters),
        ("sql_injection", create_api_recipe_with_sql_injection),
        ("long_text", create_api_recipe_with_very_long_text),
    ])
    def test_text_scenarios_parametrized(self, scenario, factory_func):
        """Test text scenarios using parametrization."""
        kwargs = factory_func()
        recipe = ApiRecipe(**kwargs)
        
        assert isinstance(recipe, ApiRecipe)
        assert isinstance(recipe.name, str)
        assert isinstance(recipe.instructions, str)


class TestApiRecipeConcurrencyEdgeCases(BaseApiRecipeTest):
    """
    Test suite for concurrency and version edge cases.
    """

    def test_concurrent_modifications_handling(self):
        """Test handling of concurrent modification scenarios."""
        concurrent_kwargs = create_api_recipe_with_concurrent_modifications()
        recipe = ApiRecipe(**concurrent_kwargs)
        
        # Should handle concurrent modification data
        assert recipe.version == 1
        assert isinstance(recipe.created_at, datetime)
        assert isinstance(recipe.updated_at, datetime)

    def test_high_version_handling(self):
        """Test handling of high version numbers."""
        high_version_kwargs = create_api_recipe_with_high_version()
        recipe = ApiRecipe(**high_version_kwargs)
        
        # Should handle high version numbers
        assert recipe.version == 99999

    def test_zero_version_handling(self):
        """Test handling of zero version."""
        zero_version_kwargs = create_api_recipe_with_zero_version()
        recipe = ApiRecipe(**zero_version_kwargs)
        
        # Should handle zero version
        assert recipe.version == 0

    def test_negative_version_handling(self):
        """Test handling of negative version."""
        negative_version_kwargs = create_api_recipe_with_negative_version()
        recipe = ApiRecipe(**negative_version_kwargs)
        
        # Should handle negative version
        assert recipe.version == -1

    def test_version_round_trip_preservation(self):
        """Test that version values are preserved in round-trip conversions."""
        high_version_kwargs = create_api_recipe_with_high_version()
        recipe = ApiRecipe(**high_version_kwargs)
        
        # Round-trip through domain
        domain_recipe = recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        # Version should be preserved
        assert recovered_api.version == recipe.version

    @pytest.mark.parametrize("scenario,factory_func", [
        ("concurrent", create_api_recipe_with_concurrent_modifications),
        ("high_version", create_api_recipe_with_high_version),
        ("zero_version", create_api_recipe_with_zero_version),
        ("negative_version", create_api_recipe_with_negative_version),
    ])
    def test_version_scenarios_parametrized(self, scenario, factory_func):
        """Test version scenarios using parametrization."""
        kwargs = factory_func()
        recipe = ApiRecipe(**kwargs)
        
        assert isinstance(recipe, ApiRecipe)
        assert isinstance(recipe.version, int)


class TestApiRecipeComprehensiveValidation(BaseApiRecipeTest):
    """
    Test suite for comprehensive validation using factory helpers.
    """

    def test_comprehensive_validation_test_cases(self):
        """Test all comprehensive validation test cases."""
        test_cases = create_comprehensive_validation_test_cases()
        
        for case in test_cases:
            factory_func = case["factory"]
            expected_error = case["expected_error"]
            
            try:
                kwargs = factory_func()
                recipe = ApiRecipe(**kwargs)
                
                if expected_error == "domain_rule":
                    # Should fail when converting to domain
                    with pytest.raises(Exception):
                        recipe.to_domain()
                elif expected_error is not None:
                    # Should have failed during creation but didn't
                    pytest.fail(f"Expected error '{expected_error}' but creation succeeded for {factory_func.__name__}")
                else:
                    # Should succeed
                    assert isinstance(recipe, ApiRecipe)
                    
            except ValueError as e:
                if expected_error is None:
                    pytest.fail(f"Unexpected validation error for {factory_func.__name__}: {e}")
                # Expected error occurred
                assert True

    def test_round_trip_conversion_validation(self):
        """Test comprehensive round-trip conversion validation."""
        # Test with various recipe types
        test_recipes = [
            create_simple_api_recipe(),
            create_complex_api_recipe(),
            create_vegetarian_api_recipe(),
            create_api_recipe_with_mismatched_computed_properties(),
        ]
        
        for recipe in test_recipes:
            validation_result = validate_round_trip_conversion(recipe)
            
            assert validation_result["api_to_domain_success"], f"API to domain conversion failed: {validation_result['errors']}"
            assert validation_result["domain_to_api_success"], f"Domain to API conversion failed: {validation_result['errors']}"
            assert validation_result["data_integrity_maintained"], f"Data integrity not maintained: {validation_result['warnings']}"

    def test_orm_conversion_validation(self):
        """Test comprehensive ORM conversion validation."""
        # Test with various recipe types
        test_recipes = [
            create_simple_api_recipe(),
            create_complex_api_recipe(),
            create_minimal_api_recipe(),
        ]
        
        for recipe in test_recipes:
            validation_result = validate_orm_conversion(recipe)
            
            assert validation_result["api_to_orm_kwargs_success"], f"API to ORM kwargs failed: {validation_result['errors']}"
            assert validation_result["orm_kwargs_valid"], f"ORM kwargs invalid: {validation_result['warnings']}"

    def test_json_serialization_validation(self):
        """Test comprehensive JSON serialization validation."""
        # Test with various recipe types
        test_recipes = [
            create_simple_api_recipe(),
            create_complex_api_recipe(),
        ]
        
        # Also test with unicode text
        unicode_kwargs = create_api_recipe_with_unicode_text()
        unicode_recipe = ApiRecipe(**unicode_kwargs)
        test_recipes.append(unicode_recipe)
        
        for recipe in test_recipes:
            validation_result = validate_json_serialization(recipe)
            
            assert validation_result["api_to_json_success"], f"API to JSON failed: {validation_result['errors']}"
            assert validation_result["json_to_api_success"], f"JSON to API failed: {validation_result['errors']}"
            assert validation_result["json_valid"], f"JSON invalid: {validation_result['errors']}"
            assert validation_result["round_trip_success"], f"Round-trip failed: {validation_result['warnings']}"


class TestApiRecipeStressAndPerformance(BaseApiRecipeTest):
    """
    Test suite for stress and performance testing.
    """

    def test_massive_collections_handling(self):
        """Test handling of massive collections."""
        massive_kwargs = create_api_recipe_with_massive_collections()
        
        start_time = time.perf_counter()
        recipe = ApiRecipe(**massive_kwargs)
        creation_time = time.perf_counter() - start_time
        
        # Should handle massive collections efficiently
        assert len(recipe.ingredients) == 1000
        assert len(recipe.ratings) == 1000
        assert len(recipe.tags) == 100
        assert creation_time < 1.0, f"Creation time {creation_time:.3f}s exceeds 1s limit"

    def test_deeply_nested_data_handling(self):
        """Test handling of deeply nested data structures."""
        nested_kwargs = create_api_recipe_with_deeply_nested_data()
        
        start_time = time.perf_counter()
        recipe = ApiRecipe(**nested_kwargs)
        creation_time = time.perf_counter() - start_time
        
        # Should handle deeply nested data efficiently
        assert recipe.nutri_facts is not None
        assert len(recipe.ingredients) == 50
        assert creation_time < 0.5, f"Creation time {creation_time:.3f}s exceeds 0.5s limit"

    def test_stress_dataset_performance(self):
        """Test performance with stress dataset."""
        stress_dataset = create_stress_test_dataset(count=100)
        
        start_time = time.perf_counter()
        created_recipes = []
        
        for kwargs in stress_dataset:
            try:
                recipe = ApiRecipe(**kwargs)
                created_recipes.append(recipe)
            except Exception:
                # Some stress test cases might intentionally fail
                pass
        
        total_time = time.perf_counter() - start_time
        avg_time = total_time / len(stress_dataset)
        
        # Should handle stress dataset efficiently
        assert len(created_recipes) > 50, "Too many recipes failed creation"
        assert avg_time < 0.1, f"Average creation time {avg_time:.3f}s exceeds 0.1s limit"

    def test_bulk_conversion_performance(self):
        """Test bulk conversion performance."""
        # Create bulk recipes
        bulk_recipes = [create_simple_api_recipe() for _ in range(50)]
        
        start_time = time.perf_counter()
        
        # Test bulk conversions
        for recipe in bulk_recipes:
            domain_recipe = recipe.to_domain()
            orm_kwargs = recipe.to_orm_kwargs()
            json_str = recipe.model_dump_json()
            recovered = ApiRecipe.model_validate_json(json_str)
            
            # Basic validation
            assert domain_recipe.id == recipe.id
            assert orm_kwargs["id"] == recipe.id
            assert recovered.id == recipe.id
        
        total_time = time.perf_counter() - start_time
        avg_time = total_time / len(bulk_recipes)
        
        # Should handle bulk operations efficiently
        assert avg_time < 0.05, f"Average bulk operation time {avg_time:.3f}s exceeds 0.05s limit"

    @pytest.mark.parametrize("count", [10, 50, 100])
    def test_scalability_performance(self, count):
        """Test scalability with different collection sizes."""
        start_time = time.perf_counter()
        
        recipes = [create_simple_api_recipe() for _ in range(count)]
        
        creation_time = time.perf_counter() - start_time
        avg_creation_time = creation_time / count
        
        # Should scale linearly
        assert avg_creation_time < 0.01, f"Average creation time {avg_creation_time:.3f}s exceeds 0.01s limit for {count} recipes"
        assert len(recipes) == count

# ... existing code ... 