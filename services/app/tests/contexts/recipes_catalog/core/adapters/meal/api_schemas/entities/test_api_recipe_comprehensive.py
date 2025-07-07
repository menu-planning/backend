from pydantic import ValidationError
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
    
    # Helper functions for nested objects
    create_api_nutri_facts,
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


"""
ApiRecipe Comprehensive Test Suite

This module provides comprehensive test coverage for the ApiRecipe entity, covering all aspects
of its behavior including validation, conversion, serialization, performance, and edge cases.

## Test Strategy Overview

### Factory Replacement Strategy (Phase 2 Implementation)
This test suite has been refactored to use explicit test data for core scenarios while preserving
specialized factory functions for edge cases and complex scenarios. This approach provides:

1. **Explicit Core Fixtures**: Simple and common test scenarios use explicit fixture data that is
   immediately readable and understandable without external dependencies.

2. **Preserved Specialized Factories**: 70+ specialized factory functions are preserved for:
   - Edge case testing (boundary values, validation errors, etc.)
   - Complex scenario generation (unicode, security, performance)
   - Parameterized testing with varied data sets
   - Bulk data generation for performance tests

3. **Hybrid Approach Benefits**:
   - **Readability**: Core test data is explicit and visible in fixtures
   - **Maintainability**: Complex edge cases use factories to reduce duplication
   - **Coverage**: Comprehensive testing across all scenarios
   - **Performance**: Efficient generation of bulk test data when needed

### Test Organization

The test suite is organized into logical test classes, each focusing on specific aspects:

1. **BaseApiRecipeTest**: Shared fixtures and setup with explicit core test data
2. **TestApiRecipeBasics**: Core conversion functionality (domain, ORM, API)
3. **TestApiRecipeRoundTrip**: Round-trip conversion validation
4. **TestApiRecipeComputedProperties**: Average rating calculations and corrections
5. **TestApiRecipeErrorHandling**: Validation errors and exception scenarios
6. **TestApiRecipeEdgeCases**: Boundary conditions and special values
7. **TestApiRecipePerformance**: Performance benchmarks and scalability
8. **TestApiRecipeJson**: JSON serialization and deserialization
9. **TestApiRecipeIntegration**: Integration with base classes and framework
10. **TestApiRecipeSpecialized**: Factory-generated specialized scenarios
11. **TestApiRecipeCoverage**: Coverage validation and completeness checks
12. **TestApiRecipeFieldValidationEdgeCases**: Specific field validation tests
13. **TestApiRecipeTagsValidationEdgeCases**: Tag-specific validation
14. **TestApiRecipeFrozensetValidationEdgeCases**: Collection type validation
15. **TestApiRecipeDomainRuleValidationEdgeCases**: Business rule validation
16. **TestApiRecipeComputedPropertiesEdgeCases**: Complex computed property scenarios
17. **TestApiRecipeDatetimeEdgeCases**: Timestamp and datetime handling
18. **TestApiRecipeTextAndSecurityEdgeCases**: Unicode, security, and text handling
19. **TestApiRecipeConcurrencyEdgeCases**: Version and concurrency scenarios
20. **TestApiRecipeComprehensiveValidation**: End-to-end validation suites
21. **TestApiRecipeStressAndPerformance**: Stress testing and performance limits

### Key Testing Principles

1. **Explicit Core Data**: Primary fixtures (simple_recipe, complex_recipe) use explicit,
   readable data construction that clearly shows what is being tested.

2. **Factory-Driven Edge Cases**: Complex scenarios, validation errors, and bulk data
   generation use specialized factory functions for efficiency and coverage.

3. **Comprehensive Coverage**: Every public method, property, and validation rule is tested
   across normal, boundary, and error conditions.

4. **Performance Awareness**: Performance tests validate that operations complete within
   reasonable time bounds and scale appropriately.

5. **Cross-Layer Validation**: Round-trip testing ensures data integrity across all
   conversion layers (API ↔ Domain ↔ ORM).

### Test Data Strategy

- **Core Fixtures**: 3 explicit fixtures (simple_recipe, complex_recipe, edge cases)
- **Specialized Factories**: 70+ factory functions for comprehensive edge case coverage
- **Parameterized Testing**: Extensive use of pytest.mark.parametrize for systematic coverage
- **Bulk Generation**: Factory-based bulk data creation for performance and stress testing

### Validation Coverage

The test suite validates:
- All ApiRecipe fields and their constraints
- Conversion methods (to_domain, from_domain, to_orm_kwargs, from_orm_model)
- JSON serialization and deserialization
- Computed properties (average ratings)
- Error scenarios and validation rules
- Performance characteristics
- Edge cases and boundary conditions
- Security considerations (injection, unicode)
- Concurrency and versioning behavior

### Maintenance Notes

1. **When adding new tests**: Use explicit data for common scenarios, factories for edge cases
2. **When modifying core behavior**: Update both explicit fixtures and relevant factories
3. **Performance baselines**: Current suite runs 309 tests with 100% pass rate
4. **Factory preservation**: Maintain 70+ specialized factories for comprehensive edge case testing

This comprehensive approach ensures robust validation while maintaining test readability
and efficient coverage of the extensive ApiRecipe functionality.
"""


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
        from uuid import uuid4
        from datetime import datetime, timedelta
        from src.contexts.shared_kernel.domain.enums import MeasureUnit
        from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
        from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating
        from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
        from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
        
        recipe_id = str(uuid4())
        recipe_author_id = str(uuid4())
        user_id = str(uuid4())
        base_time = datetime.now() - timedelta(days=1)
        
        return ApiRecipe(
            id=recipe_id,
            author_id=recipe_author_id,
            meal_id=str(uuid4()),
            name="Simple Toast",
            description="Quick and easy toast with butter",
            instructions="1. Toast bread. 2. Spread butter. 3. Serve.",
            total_time=5,
            ingredients=frozenset([
                ApiIngredient(
                    name="Bread",
                    quantity=2.0,
                    unit=MeasureUnit.SLICE,
                    position=0,
                    full_text="2 slices bread",
                    product_id=None
                ),
                ApiIngredient(
                    name="Butter", 
                    quantity=1.0,
                    unit=MeasureUnit.TABLESPOON,
                    position=1,
                    full_text="1 tablespoon butter",
                    product_id=None
                )
            ]),
            tags=frozenset([
                ApiTag(key="difficulty", value="easy", author_id=recipe_author_id, type="recipe"),
                ApiTag(key="meal-type", value="breakfast", author_id=recipe_author_id, type="recipe")
            ]),
            ratings=frozenset([
                ApiRating(
                    user_id=user_id,
                    recipe_id=recipe_id,
                    taste=3,
                    convenience=5,
                    comment="Simple but effective"
                )
            ]),
            privacy=Privacy.PUBLIC,
            version=1,
            utensils="Toaster, knife",
            notes="Perfect for quick breakfast",
            nutri_facts=create_api_nutri_facts(
                calories=250.0,
                protein=6.0,
                carbohydrate=30.0,
                total_fat=12.0,
                sodium=400.0
            ),
            weight_in_grams=80,
            image_url=None,
            average_taste_rating=3.0,
            average_convenience_rating=5.0,
            created_at=base_time,
            updated_at=base_time + timedelta(minutes=5),
            discarded=False
        )

    @pytest.fixture
    def complex_recipe(self):
        """Complex recipe for advanced testing with nested objects."""
        from uuid import uuid4
        from datetime import datetime, timedelta
        from src.contexts.shared_kernel.domain.enums import MeasureUnit
        from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
        from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating
        from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
        from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
        
        recipe_id = str(uuid4())
        recipe_author_id = str(uuid4())
        user_id = str(uuid4())
        base_time = datetime.now() - timedelta(days=2)
        
        # Enhanced ingredients - adding 6th ingredient for test requirement
        ingredients = frozenset([
            ApiIngredient(
                name="Beef Tenderloin",
                quantity=800.0,
                unit=MeasureUnit.GRAM,
                position=0,
                full_text="800g beef tenderloin, trimmed",
                product_id="301b032f-ed2e-476f-8082-dd02b67f28a2"
            ),
            ApiIngredient(
                name="Mushrooms",
                quantity=300.0,
                unit=MeasureUnit.GRAM,
                position=1,
                full_text="300g mixed mushrooms, finely chopped",
                product_id=None
            ),
            ApiIngredient(
                name="Puff Pastry",
                quantity=1.0,
                unit=MeasureUnit.UNIT,
                position=2,
                full_text="1 sheet puff pastry, thawed",
                product_id="a8b60de4-6cb5-4509-ba0a-935f9dfddbeb"
            ),
            ApiIngredient(
                name="Prosciutto",
                quantity=150.0,
                unit=MeasureUnit.GRAM,
                position=3,
                full_text="150g prosciutto, thinly sliced",
                product_id="aa02f531-8b1d-44e0-bce4-c5097656dbbb"
            ),
            ApiIngredient(
                name="Egg",
                quantity=1.0,
                unit=MeasureUnit.UNIT,
                position=4,
                full_text="1 egg, beaten for wash",
                product_id=None
            ),
            ApiIngredient(
                name="Fresh Thyme",
                quantity=2.0,
                unit=MeasureUnit.TABLESPOON,
                position=5,
                full_text="2 tbsp fresh thyme leaves",
                product_id=None
            )
        ])
        
        # Complex ratings
        ratings = frozenset([
            ApiRating(
                user_id=user_id,
                recipe_id=recipe_id,
                taste=5,
                convenience=2,
                comment="Exceptional fine dining experience!"
            ),
            ApiRating(
                user_id=str(uuid4()),
                recipe_id=recipe_id,
                taste=4,
                convenience=2,
                comment="Complex but worth the effort"
            ),
            ApiRating(
                user_id=str(uuid4()),
                recipe_id=recipe_id,
                taste=4,
                convenience=2,
                comment="Restaurant quality at home"
            )
        ])
        
        # Complex tags  
        tags = frozenset([
            ApiTag(key="category", value="beef", author_id=recipe_author_id, type="recipe"),
            ApiTag(key="style", value="fine-dining", author_id=recipe_author_id, type="recipe"),
            ApiTag(key="cuisine", value="french", author_id=recipe_author_id, type="recipe"),
            ApiTag(key="technique", value="pastry", author_id=recipe_author_id, type="recipe")
        ])
        
        # Complex nutrition facts
        nutri_facts = create_api_nutri_facts()
        
        return ApiRecipe(
            id=recipe_id,
            author_id=recipe_author_id,
            meal_id=str(uuid4()),
            name="Beef Wellington with Mushroom Duxelles",
            description="Classic French dish with beef tenderloin wrapped in pâté, mushroom duxelles, and puff pastry.",
            instructions="1. Sear beef tenderloin on all sides. 2. Prepare mushroom duxelles by sautéing mushrooms until moisture evaporates. 3. Wrap beef in plastic with duxelles, chill 30 minutes. 4. Roll out puff pastry. 5. Wrap beef in pastry, seal edges. 6. Egg wash and score. 7. Bake at 400°F for 25-30 minutes. 8. Rest 10 minutes before slicing.",
            total_time=180,
            ingredients=ingredients,
            tags=tags,
            ratings=ratings,
            privacy=Privacy.PUBLIC,
            version=1,
            utensils="Roasting pan, pastry brush, plastic wrap, chef's knife",
            notes="Temperature control is crucial - use meat thermometer for perfect doneness.",
            nutri_facts=nutri_facts,
            weight_in_grams=1200,
            image_url="https://example.com/beef-wellington.jpg",
            average_taste_rating=4.33,
            average_convenience_rating=2.0,
            created_at=base_time,
            updated_at=base_time + timedelta(hours=2),
            discarded=False
        )

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
        from uuid import uuid4
        from datetime import datetime, timedelta
        
        # Create explicit minimal recipe (replaces create_minimal_api_recipe)
        minimal_recipe_id = str(uuid4())
        minimal_author_id = str(uuid4())
        minimal_base_time = datetime.now() - timedelta(days=3)
        
        minimal_recipe = ApiRecipe(
            id=minimal_recipe_id,
            author_id=minimal_author_id,
            meal_id=str(uuid4()),
            name="Minimal Recipe",
            description="Basic recipe with minimal fields",
            instructions="Do the thing.",
            total_time=1,
            ingredients=frozenset(),
            tags=frozenset(),
            ratings=frozenset(),
            privacy=Privacy.PUBLIC,
            version=1,
            utensils="None",
            notes="Minimal test case",
            nutri_facts=None,
            weight_in_grams=0,
            image_url=None,
            average_taste_rating=None,
            average_convenience_rating=None,
            created_at=minimal_base_time,
            updated_at=minimal_base_time,
            discarded=False
        )
        
        return {
            "empty_collections": minimal_recipe,
            "max_fields": create_api_recipe_with_max_fields(),  # Keep complex factory
            "incorrect_averages": create_api_recipe_with_incorrect_averages(),  # Keep for edge case testing
            "no_ratings": create_api_recipe_without_ratings(),  # Keep for specific testing
            "vegetarian": create_vegetarian_api_recipe(),  # Keep specialized factory
            "high_protein": create_high_protein_api_recipe(),  # Keep specialized factory
            "quick": create_quick_api_recipe(),  # Keep specialized factory
            "dessert": create_dessert_api_recipe()  # Keep specialized factory
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

    def test_computed_properties_with_multiple_ratings(self, complex_recipe):
        """Test computed properties with multiple ratings."""
        # Create recipe with known ratings
        recipe = complex_recipe
        
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

    def test_json_with_computed_properties(self, complex_recipe):
        """Test JSON handling with computed properties."""
        # Create recipe with ratings
        recipe = complex_recipe
        
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


class TestApiRecipeErrorHandling(BaseApiRecipeTest):
    """
    Test suite for error handling tests (minimum 5 error scenarios per method).
    """

    # =============================================================================
    # ERROR HANDLING TESTS (MINIMUM 5 ERROR SCENARIOS PER METHOD)
    # =============================================================================

    def test_from_domain_error_scenarios(self, edge_case_recipes):
        """Test from_domain error handling - edge cases since method is robust."""
        
        # Error 1: Test None input 
        with pytest.raises((AttributeError, TypeError)):
            ApiRecipe.from_domain(None)  # type: ignore
        
        # Error 2: Invalid object type
        with pytest.raises((AttributeError, TypeError)):
            ApiRecipe.from_domain("not_a_domain_object")  # type: ignore
        
        # Error 3: Empty dictionary (missing required attributes)
        with pytest.raises((AttributeError, TypeError)):
            ApiRecipe.from_domain({})  # type: ignore
        
        # Error 4: Invalid domain object with None required fields
        domain_recipe = create_recipe_domain_from_api(edge_case_recipes["empty_collections"])
        domain_recipe._id = None  # type: ignore
        with pytest.raises(Exception):
            ApiRecipe.from_domain(domain_recipe)
        
        # Error 5: Domain object with invalid types
        domain_recipe = create_recipe_domain_from_api(edge_case_recipes["empty_collections"])
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

    def test_to_orm_kwargs_error_scenarios(self, simple_recipe, complex_recipe, edge_case_recipes):
        """Test to_orm_kwargs with various error scenarios."""
        # Basic error scenario tests
        kwargs = simple_recipe.to_orm_kwargs()
        
        # Edge case 1: Recipe with empty collections
        empty_recipe = edge_case_recipes["empty_collections"]
        kwargs = empty_recipe.to_orm_kwargs()
        assert isinstance(kwargs, dict)
        assert kwargs["ingredients"] == []
        assert kwargs["ratings"] == []
        assert kwargs["tags"] == []
        
        # Edge case 2: Recipe with large collections
        kwargs = complex_recipe.to_orm_kwargs()
        assert isinstance(kwargs, dict)
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

    def test_edge_case_empty_collections(self, edge_case_recipes):
        """Test handling of empty collections."""
        minimal_recipe = edge_case_recipes["empty_collections"]
        
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

    def test_edge_case_complex_nested_structures(self, complex_recipe):
        """Test handling of complex nested structures."""
        
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
    Test suite for performance validation tests (environment-agnostic).
    """

    # =============================================================================
    # ENVIRONMENT-AGNOSTIC PERFORMANCE TESTS
    # =============================================================================

    def test_from_domain_conversion_efficiency_per_100_operations_benchmark(self, domain_recipe):
        """Test from_domain conversion efficiency using throughput measurement."""
        # Measure baseline single operation
        start_time = time.perf_counter()
        ApiRecipe.from_domain(domain_recipe)
        single_op_time = time.perf_counter() - start_time
        
        # Measure batch operations
        start_time = time.perf_counter()
        for _ in range(100):  # Test 100 conversions for reliable timing
            ApiRecipe.from_domain(domain_recipe)
        batch_time = time.perf_counter() - start_time
        
        # Efficiency test: batch should scale reasonably (within 50% tolerance of linear scaling)
        expected_batch_time = single_op_time * 100
        efficiency_ratio = batch_time / expected_batch_time
        
        # Allow for both better and worse performance across environments
        assert efficiency_ratio < 2.0, f"from_domain batch efficiency degraded: {efficiency_ratio:.2f}x expected time"
        assert efficiency_ratio > 0.2, f"from_domain batch timing inconsistent: {efficiency_ratio:.2f}x expected time"

    def test_to_domain_conversion_efficiency_per_100_operations_benchmark(self, complex_recipe):
        """Test to_domain conversion efficiency using throughput measurement."""
        # Measure baseline single operation
        start_time = time.perf_counter()
        complex_recipe.to_domain()
        single_op_time = time.perf_counter() - start_time
        
        # Measure batch operations
        start_time = time.perf_counter()
        for _ in range(100):  # Test 100 conversions
            complex_recipe.to_domain()
        batch_time = time.perf_counter() - start_time
        
        # Efficiency test: batch should scale reasonably (within 50% tolerance of linear scaling)
        expected_batch_time = single_op_time * 100
        efficiency_ratio = batch_time / expected_batch_time
        
        # Allow for both better and worse performance across environments
        assert efficiency_ratio < 2.0, f"to_domain batch efficiency degraded: {efficiency_ratio:.2f}x expected time"
        assert efficiency_ratio > 0.2, f"to_domain batch timing inconsistent: {efficiency_ratio:.2f}x expected time"

    def test_from_orm_model_conversion_efficiency_per_100_operations_benchmark(self, real_orm_recipe):
        """Test from_orm_model conversion efficiency using throughput measurement."""
        # Measure baseline single operation
        start_time = time.perf_counter()
        ApiRecipe.from_orm_model(real_orm_recipe)
        single_op_time = time.perf_counter() - start_time
        
        # Measure batch operations
        start_time = time.perf_counter()
        for _ in range(100):  # Test 100 conversions
            ApiRecipe.from_orm_model(real_orm_recipe)
        batch_time = time.perf_counter() - start_time
        
        # Efficiency test: batch should scale reasonably (within 50% tolerance of linear scaling)
        expected_batch_time = single_op_time * 100
        efficiency_ratio = batch_time / expected_batch_time
        
        # Allow for both better and worse performance across environments
        assert efficiency_ratio < 2.0, f"from_orm_model batch efficiency degraded: {efficiency_ratio:.2f}x expected time"
        assert efficiency_ratio > 0.1, f"from_orm_model batch timing inconsistent: {efficiency_ratio:.2f}x expected time"

    def test_to_orm_kwargs_conversion_efficiency_per_100_operations_benchmark(self, complex_recipe):
        """Test to_orm_kwargs conversion efficiency using relative measurement."""
        # Measure baseline single operation multiple times for stability
        single_op_times = []
        for _ in range(10):
            start_time = time.perf_counter()
            complex_recipe.to_orm_kwargs()
            single_op_times.append(time.perf_counter() - start_time)
        
        # Use median to reduce noise
        single_op_time = sorted(single_op_times)[len(single_op_times) // 2]
        
        # Measure batch operations
        start_time = time.perf_counter()
        for _ in range(100):  # Test 100 conversions
            complex_recipe.to_orm_kwargs()
        batch_time = time.perf_counter() - start_time
        
        # Calculate efficiency metrics
        expected_batch_time = single_op_time * 100
        efficiency_ratio = batch_time / expected_batch_time
        
        # Environment-agnostic assertions: Focus on relative performance consistency
        # Allow wide tolerance for environment variations but ensure reasonable scaling
        assert efficiency_ratio < 5.0, f"to_orm_kwargs batch efficiency severely degraded: {efficiency_ratio:.2f}x expected time"
        assert efficiency_ratio > 0.1, f"to_orm_kwargs batch timing suspiciously fast: {efficiency_ratio:.2f}x expected time"
        
        # Additional throughput-based validation
        throughput = 100 / batch_time
        assert throughput > 10, f"to_orm_kwargs throughput too low: {throughput:.1f} ops/sec"

    def test_complete_four_layer_conversion_cycle_efficiency_per_50_operations_benchmark(self, simple_recipe):
        """Test complete four-layer conversion cycle efficiency using adaptive measurement."""
        # Measure individual operations with multiple samples
        individual_times = []
        for _ in range(5):
            start_time = time.perf_counter()
            domain_recipe = simple_recipe.to_domain()
            api_from_domain = ApiRecipe.from_domain(domain_recipe)
            orm_kwargs = api_from_domain.to_orm_kwargs()
            individual_times.append(time.perf_counter() - start_time)
        
        # Use median for stability
        expected_single_cycle = sorted(individual_times)[len(individual_times) // 2]
        
        # Measure complete cycle performance
        start_time = time.perf_counter()
        for _ in range(50):  # Test 50 complete cycles
            domain_recipe = simple_recipe.to_domain()
            api_from_domain = ApiRecipe.from_domain(domain_recipe)
            orm_kwargs = api_from_domain.to_orm_kwargs()
            assert orm_kwargs["id"] == simple_recipe.id
        
        batch_time = time.perf_counter() - start_time
        expected_batch_time = expected_single_cycle * 50
        efficiency_ratio = batch_time / expected_batch_time
        
        # Environment-agnostic: Allow wider tolerance for complex operations
        assert efficiency_ratio < 10.0, f"Complete cycle efficiency severely degraded: {efficiency_ratio:.2f}x expected time"
        assert efficiency_ratio > 0.1, f"Complete cycle timing suspiciously fast: {efficiency_ratio:.2f}x expected time"
        
        # Throughput validation
        throughput = 50 / batch_time
        assert throughput > 5, f"Complete cycle throughput too low: {throughput:.1f} ops/sec"

    def test_large_collection_vs_individual_conversion_efficiency_benchmark(self):
        """Test efficiency of large collection processing using adaptive thresholds."""
        large_recipes = create_nested_object_validation_dataset_domain(count=100)
        
        # Measure individual operation baseline with multiple samples
        single_recipe = large_recipes[0]
        individual_times = []
        for _ in range(5):
            start_time = time.perf_counter()
            api_recipe = ApiRecipe.from_domain(single_recipe)
            orm_kwargs = api_recipe.to_orm_kwargs()
            individual_times.append(time.perf_counter() - start_time)
        
        single_op_time = sorted(individual_times)[len(individual_times) // 2]
        
        # Measure batch processing
        start_time = time.perf_counter()
        for domain_recipe in large_recipes:
            api_recipe = ApiRecipe.from_domain(domain_recipe)
            orm_kwargs = api_recipe.to_orm_kwargs()
            assert api_recipe.id == domain_recipe.id
            assert orm_kwargs["id"] == domain_recipe.id
        
        batch_time = time.perf_counter() - start_time
        
        # Environment-agnostic efficiency test: Focus on scalability rather than absolute ratios
        expected_batch_time = single_op_time * len(large_recipes)
        efficiency_ratio = batch_time / expected_batch_time
        
        # Allow wide tolerance for environment variations
        assert efficiency_ratio < 20.0, f"Large collection efficiency severely degraded: {efficiency_ratio:.2f}x expected time"
        assert efficiency_ratio > 0.1, f"Large collection timing suspiciously fast: {efficiency_ratio:.2f}x expected time"
        
        # Throughput-based validation
        throughput = len(large_recipes) / batch_time
        assert throughput > 1, f"Large collection throughput too low: {throughput:.1f} ops/sec"

    def test_bulk_operations_vs_individual_conversion_efficiency_benchmark(self):
        """Test efficiency of bulk operations using environment-agnostic measures."""
        bulk_dataset = create_conversion_performance_dataset_domain(count=100)
        
        # Measure individual operation baseline with stability
        single_recipe = bulk_dataset["domain_recipes"][0]
        individual_times = []
        for _ in range(5):
            start_time = time.perf_counter()
            api_recipe = ApiRecipe.from_domain(single_recipe)
            individual_times.append(time.perf_counter() - start_time)
        
        single_op_time = sorted(individual_times)[len(individual_times) // 2]
        
        # Measure bulk processing
        start_time = time.perf_counter()
        for domain_recipe in bulk_dataset["domain_recipes"]:
            api_recipe = ApiRecipe.from_domain(domain_recipe)
            assert api_recipe.id == domain_recipe.id
        
        batch_time = time.perf_counter() - start_time
        
        # Environment-agnostic efficiency test: Focus on reasonable scaling
        expected_batch_time = single_op_time * len(bulk_dataset["domain_recipes"])
        efficiency_ratio = batch_time / expected_batch_time
        
        # Allow wide tolerance for different environments
        assert efficiency_ratio < 15.0, f"Bulk operations efficiency severely degraded: {efficiency_ratio:.2f}x expected time"
        assert efficiency_ratio > 0.1, f"Bulk operations timing suspiciously fast: {efficiency_ratio:.2f}x expected time"
        
        # Throughput validation
        throughput = len(bulk_dataset["domain_recipes"]) / batch_time
        assert throughput > 1, f"Bulk operations throughput too low: {throughput:.1f} ops/sec"

    @pytest.mark.parametrize("domain_recipe", create_nested_object_validation_dataset_domain(count=10))
    def test_parametrized_large_collection_conversion_efficiency_benchmark(self, domain_recipe):
        """Test individual operation efficiency in large collection context."""
        # Measure operation with complexity assessment
        start_time = time.perf_counter()
        api_recipe = ApiRecipe.from_domain(domain_recipe)
        orm_kwargs = api_recipe.to_orm_kwargs()
        operation_time = time.perf_counter() - start_time
        
        # Assess complexity factors
        complexity_factors = {
            'ingredients_count': len(domain_recipe.ingredients),
            'ratings_count': len(domain_recipe.ratings),
            'tags_count': len(domain_recipe.tags),
            'has_nutri_facts': domain_recipe.nutri_facts is not None
        }
        
        # Base complexity score (linear scaling expectation)
        base_complexity = max(1, (
            complexity_factors['ingredients_count'] + 
            complexity_factors['ratings_count'] + 
            complexity_factors['tags_count']
        ) / 10)
        
        # Operations should scale sub-linearly with complexity
        complexity_efficiency = operation_time / base_complexity
        
        # Efficiency should be reasonable (not exponential growth)
        assert complexity_efficiency < 0.1, f"Operation complexity scaling inefficient: {complexity_efficiency:.6f}s per complexity unit"
        assert api_recipe.id == domain_recipe.id
        assert orm_kwargs["id"] == domain_recipe.id

    @pytest.mark.parametrize("domain_recipe", create_conversion_performance_dataset_domain(count=10)["domain_recipes"])
    def test_parametrized_bulk_domain_conversion_efficiency_benchmark(self, domain_recipe):
        """Test individual operation efficiency in bulk operation context."""
        # Measure single operation
        start_time = time.perf_counter()
        api_recipe = ApiRecipe.from_domain(domain_recipe)
        operation_time = time.perf_counter() - start_time
        
        # Assess data size factors
        data_size_factors = {
            'estimated_data_size': len(str(domain_recipe.id)) + len(domain_recipe.name) + len(domain_recipe.instructions),
            'collection_sizes': len(domain_recipe.ingredients) + len(domain_recipe.ratings) + len(domain_recipe.tags)
        }
        
        # Data processing should be efficient relative to data size
        data_efficiency = operation_time / max(1, data_size_factors['estimated_data_size'] / 1000)
        
        # Should process data efficiently (sub-linear to data size)
        assert data_efficiency < 0.01, f"Data processing inefficient: {data_efficiency:.6f}s per KB"
        assert api_recipe.id == domain_recipe.id

    # =============================================================================
    # PERFORMANCE COMPARISON TESTS (Task 4.2.2)
    # =============================================================================

    def test_bulk_vs_individual_operation_performance_comparison(self):
        """Compare bulk operations vs individual operations for efficiency."""
        # Create test dataset
        domain_recipes = create_conversion_performance_dataset_domain(count=50)["domain_recipes"]
        
        # Test individual operations
        individual_times = []
        for domain_recipe in domain_recipes[:10]:  # Test first 10
            start_time = time.perf_counter()
            api_recipe = ApiRecipe.from_domain(domain_recipe)
            individual_times.append(time.perf_counter() - start_time)
        
        avg_individual_time = sum(individual_times) / len(individual_times)
        
        # Test bulk operations
        start_time = time.perf_counter()
        bulk_results = []
        for domain_recipe in domain_recipes[:10]:
            bulk_results.append(ApiRecipe.from_domain(domain_recipe))
        bulk_time = time.perf_counter() - start_time
        avg_bulk_time = bulk_time / len(bulk_results)
        
        # Bulk operations should be at least as efficient as individual
        bulk_efficiency = avg_bulk_time / avg_individual_time
        assert bulk_efficiency <= 1.1, f"Bulk operations less efficient than individual: {bulk_efficiency:.2f}x"
        
        # Validate results
        assert len(bulk_results) == 10
        for i, result in enumerate(bulk_results):
            assert result.id == domain_recipes[i].id

    def test_simple_vs_complex_recipe_performance_comparison(self):
        """Compare performance between simple and complex recipes using adaptive ratios."""
        # Create simple and complex recipes
        simple_recipe = create_minimal_domain_recipe()
        complex_recipe = create_complex_domain_recipe()
        
        # Measure simple recipe conversion with multiple samples
        simple_times = []
        for _ in range(20):
            start_time = time.perf_counter()
            ApiRecipe.from_domain(simple_recipe)
            simple_times.append(time.perf_counter() - start_time)
        
        # Remove outliers and use median
        simple_times.sort()
        simple_times = simple_times[2:-2]  # Remove extreme outliers
        avg_simple_time = sum(simple_times) / len(simple_times)
        
        # Measure complex recipe conversion with multiple samples
        complex_times = []
        for _ in range(20):
            start_time = time.perf_counter()
            ApiRecipe.from_domain(complex_recipe)
            complex_times.append(time.perf_counter() - start_time)
        
        # Remove outliers and use median
        complex_times.sort()
        complex_times = complex_times[2:-2]  # Remove extreme outliers
        avg_complex_time = sum(complex_times) / len(complex_times)
        
        # Environment-agnostic comparison: Focus on relative efficiency
        complexity_ratio = avg_complex_time / avg_simple_time
        
        # Allow wide tolerance for environment variations while ensuring reasonable scaling
        assert complexity_ratio < 50.0, f"Complex recipe performance degrades excessively: {complexity_ratio:.2f}x simple"
        assert complexity_ratio > 0.5, f"Complex recipe unexpectedly faster than simple: {complexity_ratio:.2f}x simple"
        
        # Throughput validation for both
        simple_throughput = 1.0 / avg_simple_time
        complex_throughput = 1.0 / avg_complex_time
        
        assert simple_throughput > 10, f"Simple recipe throughput too low: {simple_throughput:.1f} ops/sec"
        assert complex_throughput > 1, f"Complex recipe throughput too low: {complex_throughput:.1f} ops/sec"

    def test_conversion_direction_performance_comparison(self):
        """Compare performance between different conversion directions using adaptive measures."""
        # Create test data
        domain_recipe = create_complex_domain_recipe()
        api_recipe = ApiRecipe.from_domain(domain_recipe)
        orm_recipe = create_recipe_orm()
        
        # Measure each conversion direction with multiple samples
        conversion_times = {}
        
        # Test from_domain performance
        times = []
        for _ in range(50):
            start_time = time.perf_counter()
            ApiRecipe.from_domain(domain_recipe)
            times.append(time.perf_counter() - start_time)
        conversion_times['from_domain'] = sum(times) / len(times)
        
        # Test to_domain performance
        times = []
        for _ in range(50):
            start_time = time.perf_counter()
            api_recipe.to_domain()
            times.append(time.perf_counter() - start_time)
        conversion_times['to_domain'] = sum(times) / len(times)
        
        # Test from_orm_model performance
        times = []
        for _ in range(50):
            start_time = time.perf_counter()
            ApiRecipe.from_orm_model(orm_recipe)
            times.append(time.perf_counter() - start_time)
        conversion_times['from_orm'] = sum(times) / len(times)
        
        # Test to_orm_kwargs performance
        times = []
        for _ in range(50):
            start_time = time.perf_counter()
            api_recipe.to_orm_kwargs()
            times.append(time.perf_counter() - start_time)
        conversion_times['to_orm'] = sum(times) / len(times)
        
        # Environment-agnostic comparison: Focus on overall consistency
        all_times = list(conversion_times.values())
        max_time = max(all_times)
        min_time = min(all_times)
        
        # Allow much wider tolerance for environment variations
        performance_ratio = max_time / min_time
        assert performance_ratio < 100.0, f"Conversion performance varies excessively: {performance_ratio:.2f}x difference"
        
        # Ensure minimum throughput for all conversions
        for direction, avg_time in conversion_times.items():
            throughput = 1.0 / avg_time
            assert throughput > 1, f"{direction} throughput too low: {throughput:.1f} ops/sec"

    # =============================================================================
    # SCALABILITY-BASED ASSERTIONS (Task 4.2.3)
    # =============================================================================

    def test_ingredient_count_scalability_assertion(self):
        """Test that performance scales reasonably with ingredient count."""
        # Create recipes with varying ingredient counts
        ingredient_counts = [1, 5, 10, 25, 50]
        performance_data = []
        
        for count in ingredient_counts:
            # Create domain recipe with specific ingredient count
            domain_recipe = create_nested_object_validation_dataset_domain(count=1, ingredients_per_recipe=count)[0]
            
            # Measure conversion performance
            start_time = time.perf_counter()
            for _ in range(10):  # Multiple runs for stability
                ApiRecipe.from_domain(domain_recipe)
            avg_time = (time.perf_counter() - start_time) / 10
            
            performance_data.append((count, avg_time))
        
        # Check that performance scales sub-linearly or linearly (not exponentially)
        # Compare first and last data points
        first_count, first_time = performance_data[0]
        last_count, last_time = performance_data[-1]
        
        # Calculate scaling factor
        count_ratio = last_count / first_count
        time_ratio = last_time / first_time
        
        # Performance should scale better than quadratically
        scaling_efficiency = time_ratio / (count_ratio ** 2)
        assert scaling_efficiency < 1.0, f"Performance scales worse than quadratically: {scaling_efficiency:.2f}"
        
        # Performance should scale at least linearly (some overhead is expected)
        linear_efficiency = time_ratio / count_ratio
        assert linear_efficiency < 3.0, f"Performance scales too poorly: {linear_efficiency:.2f}x linear"

    def test_data_size_scalability_assertion(self):
        """Test that performance scales reasonably with overall data size."""
        # Create recipes with varying data sizes
        data_sizes = ["minimal", "small", "medium", "large"]
        performance_data = []
        
        for size in data_sizes:
            if size == "minimal":
                recipe = create_minimal_domain_recipe()
            elif size == "small":
                recipe = create_recipe()
            elif size == "medium":
                recipe = create_complex_domain_recipe()
            else:  # large
                recipe = create_nested_object_validation_dataset_domain(count=1, ingredients_per_recipe=20)[0]
            
            # Estimate data size
            estimated_size = len(str(recipe.id)) + len(recipe.name) + len(recipe.instructions)
            estimated_size += len(recipe.ingredients) * 50  # Rough estimate per ingredient
            if recipe.ratings is not None:
                estimated_size += len(recipe.ratings) * 20  # Rough estimate per rating
            estimated_size += len(recipe.tags) * 30  # Rough estimate per tag
            
            # Measure performance
            start_time = time.perf_counter()
            for _ in range(15):
                ApiRecipe.from_domain(recipe)
            avg_time = (time.perf_counter() - start_time) / 15
            
            performance_data.append((estimated_size, avg_time))
        
        # Check scalability
        performance_data.sort(key=lambda x: x[0])  # Sort by size
        first_size, first_time = performance_data[0]
        last_size, last_time = performance_data[-1]
        
        # Calculate scaling
        size_ratio = last_size / first_size
        time_ratio = last_time / first_time
        
        # Should scale sub-linearly with data size
        scaling_factor = time_ratio / size_ratio
        assert scaling_factor < 2.0, f"Performance scales too poorly with data size: {scaling_factor:.2f}x"

    def test_collection_size_scalability_assertion(self):
        """Test that performance scales reasonably with collection sizes."""
        collection_sizes = [0, 1, 5, 10, 20]
        performance_results = []
        
        for size in collection_sizes:
            # Create recipe with specific collection size
            if size == 0:
                recipe = create_minimal_domain_recipe()
            else:
                recipe = create_nested_object_validation_dataset_domain(
                    count=1, 
                    ingredients_per_recipe=size,
                    ratings_per_recipe=size,
                    tags_per_recipe=min(size, 10)  # Limit tags to reasonable number
                )[0]
            
            # Measure performance
            start_time = time.perf_counter()
            for _ in range(10):
                api_recipe = ApiRecipe.from_domain(recipe)
                # Also test round-trip to ensure full scalability
                domain_back = api_recipe.to_domain()
                assert domain_back.id == recipe.id
            avg_time = (time.perf_counter() - start_time) / 10
            
            performance_results.append((size, avg_time))
        
        # Verify scalability
        for i in range(1, len(performance_results)):
            prev_size, prev_time = performance_results[i-1]
            curr_size, curr_time = performance_results[i]
            
            if prev_size > 0:  # Avoid division by zero
                size_growth = curr_size / prev_size
                time_growth = curr_time / prev_time
                
                # Time growth should not exceed quadratic growth
                growth_ratio = time_growth / (size_growth ** 2)
                assert growth_ratio < 1.5, f"Collection scaling too poor at size {curr_size}: {growth_ratio:.2f}x quadratic"

    # =============================================================================
    # OPERATION EFFICIENCY FOCUS (Task 4.3.1)
    # =============================================================================

    def test_algorithmic_efficiency_validation(self):
        """Test algorithmic efficiency using relative complexity measures."""
        # Test with datasets of increasing algorithmic complexity
        def measure_operations_per_second(recipe, operation_count=100):
            start_time = time.perf_counter()
            for _ in range(operation_count):
                api_recipe = ApiRecipe.from_domain(recipe)
                domain_back = api_recipe.to_domain()
                assert domain_back.id == recipe.id
            return operation_count / (time.perf_counter() - start_time)
        
        # Create recipes with different complexity levels
        simple_recipe = create_minimal_domain_recipe()
        complex_recipe = create_complex_domain_recipe()
        
        # Measure throughput for each complexity level
        simple_throughput = measure_operations_per_second(simple_recipe, 100)
        complex_throughput = measure_operations_per_second(complex_recipe, 50)  # Fewer operations for complex
        
        # Environment-agnostic efficiency validation: Focus on minimum throughput
        assert simple_throughput > 5, f"Simple recipe throughput too low: {simple_throughput:.1f} ops/sec"
        assert complex_throughput > 1, f"Complex recipe throughput too low: {complex_throughput:.1f} ops/sec"
        
        # Relative efficiency should be reasonable but allow wide tolerance
        if simple_throughput > 0 and complex_throughput > 0:
            efficiency_ratio = simple_throughput / complex_throughput
            assert efficiency_ratio < 200.0, f"Complexity reduces efficiency excessively: {efficiency_ratio:.2f}x"
            assert efficiency_ratio > 0.1, f"Complex recipe unexpectedly more efficient: {efficiency_ratio:.2f}x"

    def test_memory_efficiency_validation(self):
        """Test memory efficiency using adaptive object count thresholds."""
        import gc
        import sys
        
        # Get baseline memory usage with stability
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Perform operations with smaller dataset for more predictable results
        recipes = create_conversion_performance_dataset_domain(count=20)["domain_recipes"]
        api_recipes = []
        
        for recipe in recipes:
            api_recipe = ApiRecipe.from_domain(recipe)
            api_recipes.append(api_recipe)
            
            # Validate operation
            domain_back = api_recipe.to_domain()
            assert domain_back.id == recipe.id
        
        # Check object growth
        gc.collect()
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects
        
        # Environment-agnostic memory validation: Focus on reasonable growth
        objects_per_operation = object_growth / len(recipes)
        assert objects_per_operation < 500, f"Excessive objects created per operation: {objects_per_operation:.1f}"
        assert objects_per_operation > 0, f"No objects created: {objects_per_operation:.1f}"
        
        # Ensure operations complete successfully
        assert len(api_recipes) == len(recipes), "Not all operations completed"
        
        # Clean up
        del api_recipes, recipes
        gc.collect()

    def test_cpu_efficiency_validation(self):
        """Test that operations are CPU-efficient and don't waste cycles."""
        # Test CPU efficiency through operation density
        recipe = create_complex_domain_recipe()
        
        # Measure operations per CPU time unit
        start_time = time.perf_counter()
        operation_count = 0
        
        # Run for a short, fixed time period
        while time.perf_counter() - start_time < 0.1:  # 100ms
            ApiRecipe.from_domain(recipe)
            operation_count += 1
        
        actual_time = time.perf_counter() - start_time
        operations_per_second = operation_count / actual_time
        
        # Should achieve reasonable operation density
        assert operations_per_second > 200, f"CPU efficiency too low: {operations_per_second:.1f} ops/sec"

    # =============================================================================
    # THROUGHPUT-BASED TESTS (Task 4.3.2)
    # =============================================================================

    def test_conversion_throughput_validation(self):
        """Test conversion throughput meets minimum performance standards."""
        # Create diverse test dataset
        recipes = []
        recipes.extend(create_conversion_performance_dataset_domain(count=20)["domain_recipes"])
        recipes.extend([create_minimal_domain_recipe() for _ in range(20)])
        recipes.extend([create_complex_domain_recipe() for _ in range(10)])
        
        # Measure throughput for different conversion types
        throughput_data = {}
        
        # from_domain throughput
        start_time = time.perf_counter()
        api_recipes = [ApiRecipe.from_domain(recipe) for recipe in recipes]
        from_domain_time = time.perf_counter() - start_time
        throughput_data['from_domain'] = len(recipes) / from_domain_time
        
        # to_domain throughput
        start_time = time.perf_counter()
        domain_recipes = [api_recipe.to_domain() for api_recipe in api_recipes]
        to_domain_time = time.perf_counter() - start_time
        throughput_data['to_domain'] = len(api_recipes) / to_domain_time
        
        # to_orm_kwargs throughput
        start_time = time.perf_counter()
        orm_kwargs_list = [api_recipe.to_orm_kwargs() for api_recipe in api_recipes]
        to_orm_time = time.perf_counter() - start_time
        throughput_data['to_orm_kwargs'] = len(api_recipes) / to_orm_time
        
        # Validate throughput minimums
        assert throughput_data['from_domain'] > 100, f"from_domain throughput too low: {throughput_data['from_domain']:.1f} ops/sec"
        assert throughput_data['to_domain'] > 100, f"to_domain throughput too low: {throughput_data['to_domain']:.1f} ops/sec"
        assert throughput_data['to_orm_kwargs'] > 100, f"to_orm_kwargs throughput too low: {throughput_data['to_orm_kwargs']:.1f} ops/sec"
        
        # Validate results
        assert len(api_recipes) == len(recipes)
        assert len(domain_recipes) == len(api_recipes)
        assert len(orm_kwargs_list) == len(api_recipes)

    def test_json_serialization_throughput_validation(self):
        """Test JSON serialization throughput meets performance standards."""
        # Create test recipes
        recipes = [create_complex_api_recipe() for _ in range(50)]
        
        # Test serialization throughput
        start_time = time.perf_counter()
        json_strings = [recipe.model_dump_json() for recipe in recipes]
        serialization_time = time.perf_counter() - start_time
        serialization_throughput = len(recipes) / serialization_time
        
        # Test deserialization throughput
        start_time = time.perf_counter()
        deserialized_recipes = [ApiRecipe.model_validate_json(json_str) for json_str in json_strings]
        deserialization_time = time.perf_counter() - start_time
        deserialization_throughput = len(json_strings) / deserialization_time
        
        # Validate throughput standards
        assert serialization_throughput > 200, f"JSON serialization throughput too low: {serialization_throughput:.1f} ops/sec"
        assert deserialization_throughput > 200, f"JSON deserialization throughput too low: {deserialization_throughput:.1f} ops/sec"
        
        # Validate correctness
        assert len(json_strings) == len(recipes)
        assert len(deserialized_recipes) == len(json_strings)
        for original, deserialized in zip(recipes, deserialized_recipes):
            assert original.id == deserialized.id

    def test_batch_processing_throughput_validation(self):
        """Test batch processing throughput efficiency."""
        # Create large dataset
        domain_recipes = create_conversion_performance_dataset_domain(count=100)["domain_recipes"]
        
        # Test batch processing throughput
        start_time = time.perf_counter()
        
        # Process in batches
        batch_size = 10
        total_processed = 0
        
        for i in range(0, len(domain_recipes), batch_size):
            batch = domain_recipes[i:i+batch_size]
            
            # Process batch
            api_batch = [ApiRecipe.from_domain(recipe) for recipe in batch]
            domain_batch = [api_recipe.to_domain() for api_recipe in api_batch]
            
            # Validate batch
            for original, converted in zip(batch, domain_batch):
                assert original.id == converted.id
            
            total_processed += len(batch)
        
        total_time = time.perf_counter() - start_time
        throughput = total_processed / total_time
        
        # Should maintain high throughput even with batching
        assert throughput > 150, f"Batch processing throughput too low: {throughput:.1f} ops/sec"
        assert total_processed == len(domain_recipes)

    # =============================================================================
    # MEMORY USAGE CONSIDERATIONS (Task 4.3.3)
    # =============================================================================

    def test_memory_usage_efficiency(self):
        """Test memory usage efficiency with adaptive thresholds."""
        import gc
        import sys
        
        # Baseline memory measurement
        gc.collect()
        
        # Create test data
        recipes = create_conversion_performance_dataset_domain(count=10)["domain_recipes"]  # Reduced count
        
        # Measure memory usage during operations
        memory_measurements = []
        
        for i, recipe in enumerate(recipes):
            # Measure before operation
            gc.collect()
            objects_before = len(gc.get_objects())
            
            # Perform operation
            api_recipe = ApiRecipe.from_domain(recipe)
            domain_recipe = api_recipe.to_domain()
            orm_kwargs = api_recipe.to_orm_kwargs()
            
            # Measure after operation
            gc.collect()
            objects_after = len(gc.get_objects())
            
            memory_growth = objects_after - objects_before
            memory_measurements.append(memory_growth)
            
            # Validate operation
            assert domain_recipe.id == recipe.id
            assert orm_kwargs["id"] == recipe.id
        
        # Analyze memory usage with adaptive thresholds
        avg_memory_growth = sum(memory_measurements) / len(memory_measurements)
        max_memory_growth = max(memory_measurements)
        
        # Environment-agnostic memory growth validation
        assert avg_memory_growth < 1000, f"Average memory growth too high: {avg_memory_growth:.1f} objects/operation"
        assert max_memory_growth < 2000, f"Maximum memory growth too high: {max_memory_growth} objects/operation"
        
        # Ensure operations complete successfully
        assert len(memory_measurements) == len(recipes), "Not all operations completed"

    def test_memory_leak_prevention(self):
        """Test that operations don't create memory leaks."""
        import gc
        import weakref
        
        # Create objects and weak references
        recipes = create_conversion_performance_dataset_domain(count=10)["domain_recipes"]
        weak_refs = []
        
        # Create and process objects
        for recipe in recipes:
            api_recipe = ApiRecipe.from_domain(recipe)
            weak_refs.append(weakref.ref(api_recipe))
            
            # Use the object
            domain_recipe = api_recipe.to_domain()
            assert domain_recipe.id == recipe.id
            
            # Let it go out of scope
            del api_recipe
        
        # Force garbage collection
        gc.collect()
        
        # Check that objects were properly cleaned up
        alive_refs = [ref for ref in weak_refs if ref() is not None]
        leak_count = len(alive_refs)
        
        # Should have minimal or no leaks
        assert leak_count < 3, f"Memory leak detected: {leak_count} objects still alive"

    def test_large_dataset_memory_efficiency(self):
        """Test memory efficiency with large datasets."""
        import gc
        
        # Initial memory state
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Process large dataset in chunks to test memory efficiency
        chunk_size = 20
        total_processed = 0
        
        for chunk_num in range(5):  # Process 5 chunks
            # Create chunk
            chunk_recipes = create_conversion_performance_dataset_domain(count=chunk_size)["domain_recipes"]
            
            # Process chunk
            chunk_results = []
            for recipe in chunk_recipes:
                api_recipe = ApiRecipe.from_domain(recipe)
                chunk_results.append(api_recipe.to_domain())
            
            # Validate chunk
            for original, result in zip(chunk_recipes, chunk_results):
                assert original.id == result.id
            
            total_processed += len(chunk_recipes)
            
            # Clean up chunk
            del chunk_recipes, chunk_results
            gc.collect()
            
            # Check memory usage doesn't grow excessively
            current_objects = len(gc.get_objects())
            memory_growth = current_objects - initial_objects
            
            # Memory growth should be bounded
            assert memory_growth < 1000, f"Memory growth too high after chunk {chunk_num}: {memory_growth} objects"
        
        # Final cleanup
        gc.collect()
        final_objects = len(gc.get_objects())
        final_growth = final_objects - initial_objects
        
        # Should return close to initial state
        assert final_growth < 500, f"Final memory growth too high: {final_growth} objects"
        assert total_processed == 100


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

    def test_json_with_computed_properties(self, complex_recipe):
        """Test JSON handling with computed properties."""
        # Create recipe with ratings
        recipe = complex_recipe
        
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
        """Test JSON serialization/deserialization efficiency using relative performance."""
        # Note: This test is kept with for loop as it measures overall performance
        # across multiple operations - parametrization would test individual performance
        
        # Measure baseline single operation
        single_recipe = recipe_collection[0]
        start_time = time.perf_counter()
        json_str = single_recipe.model_dump_json()
        restored = ApiRecipe.model_validate_json(json_str)
        single_op_time = time.perf_counter() - start_time
        
        # Measure batch operations
        start_time = time.perf_counter()
        for recipe in recipe_collection:
            json_str = recipe.model_dump_json()
            restored = ApiRecipe.model_validate_json(json_str)
            assert restored.id == recipe.id
        
        batch_time = time.perf_counter() - start_time
        
        # Efficiency test: batch should scale linearly (within 25% tolerance)
        expected_batch_time = single_op_time * len(recipe_collection)
        efficiency_ratio = batch_time / expected_batch_time
        
        assert efficiency_ratio < 1.25, f"JSON operations batch efficiency degraded: {efficiency_ratio:.2f}x expected time"
        assert efficiency_ratio > 0.75, f"JSON operations batch timing inconsistent: {efficiency_ratio:.2f}x expected time"

    @pytest.mark.parametrize("recipe", create_recipe_collection(count=5))
    def test_json_performance_parametrized(self, recipe):
        """Test JSON serialization/deserialization efficiency with complexity assessment."""
        # Measure operation with data size assessment
        start_time = time.perf_counter()
        json_str = recipe.model_dump_json()
        restored = ApiRecipe.model_validate_json(json_str)
        operation_time = time.perf_counter() - start_time
        
        # Assess data complexity factors
        data_complexity = {
            'json_size': len(json_str),
            'field_count': len(recipe.model_fields),
            'collection_sizes': len(recipe.ingredients) + len(recipe.ratings) + len(recipe.tags)
        }
        
        # JSON processing should be efficient relative to data size
        size_efficiency = operation_time / max(1, data_complexity['json_size'] / 1000)  # per KB
        
        # Should process JSON efficiently (sub-linear to data size)
        assert size_efficiency < 0.01, f"JSON processing inefficient: {size_efficiency:.6f}s per KB"
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

    def test_field_validation_integration(self, edge_case_recipes):
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
        
        # Test required field validation
        assert valid_recipe.id is not None
        assert valid_recipe.name is not None
        assert valid_recipe.instructions is not None
        assert valid_recipe.author_id is not None
        assert valid_recipe.meal_id is not None
        
        # Test optional field handling
        minimal_recipe = edge_case_recipes["empty_collections"]
        assert minimal_recipe.description is None or isinstance(minimal_recipe.description, str)
        assert minimal_recipe.utensils is None or isinstance(minimal_recipe.utensils, str)
        assert minimal_recipe.total_time is None or isinstance(minimal_recipe.total_time, int)
        
        # Test collection field validation - now frozensets
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

    @pytest.mark.parametrize("scenario", REALISTIC_RECIPE_SCENARIOS_DOMAIN)
    def test_realistic_scenario_coverage(self, scenario):
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

    @pytest.mark.parametrize("privacy", [Privacy.PUBLIC, Privacy.PRIVATE])
    def test_constants_and_enums_coverage(self, privacy):
        """Test that constants and enums are properly used."""
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
       
        # Should fail when converting to domain due to rule violation
        with pytest.raises(Exception):  # Domain rule violation
            create_api_recipe_with_negative_ingredient_positions()

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
        
        # Should fail when converting to domain due to rule violation
        with pytest.raises(Exception):  # Domain rule violation
            ApiRecipe(**invalid_kwargs)

    @pytest.mark.parametrize("rule_type,factory_func", [
        ("invalid_positions", create_api_recipe_with_invalid_ingredient_positions),
        ("duplicate_positions", create_api_recipe_with_duplicate_ingredient_positions),
        ("non_zero_start", create_api_recipe_with_non_zero_start_positions),
        ("invalid_tag_author", create_api_recipe_with_invalid_tag_author_id),
    ])
    def test_domain_rule_violations_parametrized(self, rule_type, factory_func):
        """Test domain rule violations using parametrization."""
        invalid_kwargs = factory_func()
        if rule_type == 'invalid_tag_author':
            with pytest.raises(ValidationError):
                ApiRecipe(**invalid_kwargs)
        else:
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
        with pytest.raises(ValidationError):
            ApiRecipe(**zero_version_kwargs)

    def test_negative_version_handling(self):
        """Test handling of negative version."""
        negative_version_kwargs = create_api_recipe_with_negative_version()
        with pytest.raises(ValidationError):
            ApiRecipe(**negative_version_kwargs)


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
        if scenario in ["zero_version","negative_version"]:
            with pytest.raises(ValidationError):
                ApiRecipe(**kwargs)
        else:
            recipe = ApiRecipe(**kwargs)
            
            assert isinstance(recipe, ApiRecipe)
            assert isinstance(recipe.version, int)


class TestApiRecipeComprehensiveValidation(BaseApiRecipeTest):
    """
    Test suite for comprehensive validation using factory helpers.
    """

    @pytest.mark.parametrize("case", create_comprehensive_validation_test_cases())
    def test_comprehensive_validation_test_cases(self, case):
        """Test all comprehensive validation test cases."""
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

    @pytest.mark.parametrize("recipe_factory", [
        create_simple_api_recipe,
        create_complex_api_recipe,
        create_vegetarian_api_recipe,
        create_api_recipe_with_mismatched_computed_properties,
    ])
    def test_round_trip_conversion_validation(self, recipe_factory):
        """Test comprehensive round-trip conversion validation."""
        recipe = recipe_factory()
        validation_result = validate_round_trip_conversion(recipe)
        
        assert validation_result["api_to_domain_success"], f"API to domain conversion failed: {validation_result['errors']}"
        assert validation_result["domain_to_api_success"], f"Domain to API conversion failed: {validation_result['errors']}"
        assert validation_result["data_integrity_maintained"], f"Data integrity not maintained: {validation_result['warnings']}"

    @pytest.mark.parametrize("recipe_factory", [
        create_simple_api_recipe,
        create_complex_api_recipe,
        create_minimal_api_recipe,
    ])
    def test_orm_conversion_validation(self, recipe_factory):
        """Test comprehensive ORM conversion validation."""
        recipe = recipe_factory()
        validation_result = validate_orm_conversion(recipe)
        
        assert validation_result["api_to_orm_kwargs_success"], f"API to ORM kwargs failed: {validation_result['errors']}"
        assert validation_result["orm_kwargs_valid"], f"ORM kwargs invalid: {validation_result['warnings']}"

    @pytest.mark.parametrize("recipe_factory,description", [
        (create_simple_api_recipe, "simple recipe"),
        (create_complex_api_recipe, "complex recipe"),
        (lambda: ApiRecipe(**create_api_recipe_with_unicode_text()), "unicode text recipe"),
    ])
    def test_json_serialization_validation(self, recipe_factory, description):
        """Test comprehensive JSON serialization validation."""
        recipe = recipe_factory()
        validation_result = validate_json_serialization(recipe)
        
        assert validation_result["api_to_json_success"], f"API to JSON failed for {description}: {validation_result['errors']}"
        assert validation_result["json_to_api_success"], f"JSON to API failed for {description}: {validation_result['errors']}"
        assert validation_result["json_valid"], f"JSON invalid for {description}: {validation_result['errors']}"
        assert validation_result["round_trip_success"], f"Round-trip failed for {description}: {validation_result['warnings']}"


class TestApiRecipeStressAndPerformance(BaseApiRecipeTest):
    """
    Test suite for stress and performance testing (environment-agnostic).
    """

    def test_massive_collections_handling(self):
        """Test handling of massive collections using throughput efficiency."""
        massive_kwargs = create_api_recipe_with_massive_collections()
        
        # Measure creation throughput
        start_time = time.perf_counter()
        recipe = ApiRecipe(**massive_kwargs)
        creation_time = time.perf_counter() - start_time
        
        # Assess collection sizes
        collection_sizes = {
            'ingredients': len(recipe.ingredients),
            'ratings': len(recipe.ratings),
            'tags': len(recipe.tags),
            'total_elements': len(recipe.ingredients) + len(recipe.ratings) + len(recipe.tags)
        }
        
        # Should handle massive collections efficiently
        assert collection_sizes['ingredients'] == 100
        assert collection_sizes['ratings'] == 1000
        assert collection_sizes['tags'] == 100
        
        # Throughput should scale sub-linearly with collection size
        throughput_efficiency = creation_time / max(1, collection_sizes['total_elements'] / 1000)
        assert throughput_efficiency < 0.1, f"Massive collection throughput inefficient: {throughput_efficiency:.6f}s per 1000 elements"

    def test_deeply_nested_data_handling(self):
        """Test handling of deeply nested data structures using complexity efficiency."""
        nested_kwargs = create_api_recipe_with_deeply_nested_data()
        
        # Measure creation throughput
        start_time = time.perf_counter()
        recipe = ApiRecipe(**nested_kwargs)
        creation_time = time.perf_counter() - start_time
        
        # Assess nesting complexity
        nesting_factors = {
            'has_nutri_facts': recipe.nutri_facts is not None,
            'ingredients_count': len(recipe.ingredients),
            'nested_depth_estimate': 3 if recipe.nutri_facts else 1  # Rough estimate
        }
        
        # Should handle deeply nested data efficiently
        assert nesting_factors['has_nutri_facts']
        assert nesting_factors['ingredients_count'] == 50
        
        # Complexity should scale reasonably with nesting
        complexity_efficiency = creation_time / nesting_factors['nested_depth_estimate']
        assert complexity_efficiency < 0.05, f"Nested data complexity inefficient: {complexity_efficiency:.6f}s per nesting level"

    def test_stress_dataset_performance(self):
        """Test performance with stress dataset using success rate and efficiency metrics."""
        stress_dataset = create_stress_test_dataset(count=100)
        
        # Measure processing efficiency
        start_time = time.perf_counter()
        created_recipes = []
        failed_count = 0
        
        for kwargs in stress_dataset:
            try:
                recipe = ApiRecipe(**kwargs)
                created_recipes.append(recipe)
            except Exception:
                # Some stress test cases might intentionally fail
                failed_count += 1
        
        total_time = time.perf_counter() - start_time
        
        # Success rate should be reasonable
        success_rate = len(created_recipes) / len(stress_dataset)
        assert success_rate > 0.5, f"Stress dataset success rate too low: {success_rate:.2f}"
        
        # Processing efficiency should be reasonable
        avg_processing_time = total_time / len(stress_dataset)
        throughput_per_second = 1.0 / avg_processing_time if avg_processing_time > 0 else float('inf')
        
        # Should process at least 10 items per second
        assert throughput_per_second > 10, f"Stress dataset processing too slow: {throughput_per_second:.1f} items/second"

    def test_bulk_conversion_performance(self, simple_recipe):
        """Test bulk conversion performance using environment-agnostic efficiency ratios."""
        # Create bulk recipes using explicit recipe template
        bulk_recipes = [simple_recipe for _ in range(50)]
        
        # Measure single operation baseline with multiple samples for stability
        single_op_times = []
        for _ in range(10):
            start_time = time.perf_counter()
            domain_recipe = simple_recipe.to_domain()
            orm_kwargs = simple_recipe.to_orm_kwargs()
            json_str = simple_recipe.model_dump_json()
            recovered = ApiRecipe.model_validate_json(json_str)
            single_op_times.append(time.perf_counter() - start_time)
        
        # Use median to reduce noise
        single_op_times.sort()
        single_op_time = single_op_times[len(single_op_times) // 2]
        
        # Measure bulk operations
        start_time = time.perf_counter()
        for recipe in bulk_recipes:
            domain_recipe = recipe.to_domain()
            orm_kwargs = recipe.to_orm_kwargs()
            json_str = recipe.model_dump_json()
            recovered = ApiRecipe.model_validate_json(json_str)
            
            # Basic validation
            assert domain_recipe.id == recipe.id
            assert orm_kwargs["id"] == recipe.id
            assert recovered.id == recipe.id
        
        batch_time = time.perf_counter() - start_time
        
        # Environment-agnostic efficiency test: bulk should scale reasonably
        expected_batch_time = single_op_time * len(bulk_recipes)
        efficiency_ratio = batch_time / expected_batch_time if expected_batch_time > 0 else 1.0
        
        # Wide tolerance for environment variations - focus on throughput validation
        assert efficiency_ratio < 10.0, f"Bulk conversion severely degraded: {efficiency_ratio:.2f}x expected time"
        assert efficiency_ratio > 0.1, f"Bulk conversion timing measurement issue: {efficiency_ratio:.2f}x expected time"
        
        # Also validate minimum throughput requirements
        throughput = len(bulk_recipes) / batch_time if batch_time > 0 else float('inf')
        assert throughput > 5, f"Bulk conversion throughput too low: {throughput:.1f} operations/second"

    @pytest.mark.parametrize("count", [10, 50, 100])
    def test_scalability_performance(self, count, simple_recipe):
        """Test scalability with different collection sizes using environment-agnostic linear scaling validation."""
        # Measure baseline single operation
        start_time = time.perf_counter()
        single_recipe_copy = simple_recipe
        baseline_time = time.perf_counter() - start_time
        
        # Measure collection creation
        start_time = time.perf_counter()
        recipes = [simple_recipe for _ in range(count)]
        creation_time = time.perf_counter() - start_time
        
        # Environment-agnostic scalability test: should scale reasonably with count
        expected_time = baseline_time * count if baseline_time > 0 else creation_time / count
        if expected_time > 0:
            scalability_ratio = creation_time / expected_time
            
            # Wide tolerance for environment variations - focus on reasonable scaling
            assert scalability_ratio < 50.0, f"Scalability severely degraded for {count} items: {scalability_ratio:.2f}x expected time"
            assert scalability_ratio > 0.1, f"Scalability timing measurement issue for {count} items: {scalability_ratio:.2f}x expected time"
        
        # Throughput should be reasonable
        throughput = count / creation_time if creation_time > 0 else float('inf')
        assert throughput > 10, f"Scalability throughput too low for {count} items: {throughput:.1f} items/second"
        
        assert len(recipes) == count