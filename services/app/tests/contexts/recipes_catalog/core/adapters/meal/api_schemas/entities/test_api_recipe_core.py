from tests.contexts.recipes_catalog.data_factories.recipe.recipe_domain_factories import create_minimal_recipe
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
import pytest
import json

"""
ApiRecipe Core Functionality Test Suite

Test classes for core ApiRecipe functionality including basic conversions,
round-trip validations, and computed properties.
"""


class TestApiRecipeBasics:
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
        minimal_domain = create_minimal_recipe()
        
        api_recipe = ApiRecipe.from_domain(minimal_domain)
        
        # Should handle empty collections gracefully
        assert isinstance(api_recipe.ingredients, frozenset)
        assert isinstance(api_recipe.ratings, frozenset)
        assert isinstance(api_recipe.tags, frozenset)

    def test_from_domain_with_nutrition_facts(self, domain_recipe_with_nutri_facts):
        """Test from_domain handles nutrition facts correctly."""
        api_recipe = ApiRecipe.from_domain(domain_recipe_with_nutri_facts)
        
        # Should convert nutrition facts properly
        assert api_recipe.nutri_facts is not None
        for name in api_recipe.nutri_facts.__class__.model_fields.keys():
            value = getattr(api_recipe.nutri_facts, name)
            assert value.value == getattr(domain_recipe_with_nutri_facts.nutri_facts, name).value
            assert value.unit == getattr(domain_recipe_with_nutri_facts.nutri_facts, name).unit.value
    
    def test_to_domain_basic_conversion(self, simple_recipe):
        """Test to_domain basic conversion functionality."""
        domain_recipe = simple_recipe.to_domain()
        
        assert domain_recipe.id == simple_recipe.id
        assert domain_recipe.name == simple_recipe.name
        assert domain_recipe.meal_id == simple_recipe.meal_id
        assert domain_recipe.description == simple_recipe.description
        assert domain_recipe.instructions == simple_recipe.instructions
        assert domain_recipe.author_id == simple_recipe.author_id
        assert domain_recipe.privacy == simple_recipe.privacy
        assert isinstance(domain_recipe, _Recipe)

    def test_to_domain_collection_type_conversion(self, complex_recipe):
        """Test to_domain properly converts collection types."""
        domain_recipe = complex_recipe.to_domain()
        
        # Collections should be converted to proper domain types
        assert len(domain_recipe.ingredients) == len(complex_recipe.ingredients)
        assert len(domain_recipe.ratings) == len(complex_recipe.ratings)
        assert len(domain_recipe.tags) == len(complex_recipe.tags)
        
        # Domain collections use different types
        assert isinstance(domain_recipe.ingredients, (list, frozenset))
        assert isinstance(domain_recipe.ratings, (list, frozenset, type(None)))
        assert isinstance(domain_recipe.tags, (set, frozenset))

    def test_to_domain_privacy_enum_conversion(self, simple_recipe):
        """Test to_domain correctly converts privacy enum."""
        domain_recipe = simple_recipe.to_domain()
        
        # Privacy should be same enum value
        assert domain_recipe.privacy == simple_recipe.privacy
        assert isinstance(domain_recipe.privacy, Privacy)

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
        """Test from_orm_model properly converts nested objects."""
        api_recipe = ApiRecipe.from_orm_model(real_orm_recipe)
        
        # Test collections conversion from ORM
        assert isinstance(api_recipe.ingredients, frozenset)
        assert isinstance(api_recipe.ratings, frozenset)
        assert isinstance(api_recipe.tags, frozenset)
        
        # Should convert to proper API object types
        assert all(isinstance(ing, ApiIngredient) for ing in api_recipe.ingredients)
        assert all(isinstance(rating, ApiRating) for rating in api_recipe.ratings)
        assert all(isinstance(tag, ApiTag) for tag in api_recipe.tags)

    def test_to_orm_kwargs_basic_conversion(self, simple_recipe):
        """Test to_orm_kwargs basic conversion functionality."""
        orm_kwargs = simple_recipe.to_orm_kwargs()
        
        assert isinstance(orm_kwargs, dict)
        assert orm_kwargs["id"] == simple_recipe.id
        assert orm_kwargs["name"] == simple_recipe.name
        assert orm_kwargs["meal_id"] == simple_recipe.meal_id
        assert orm_kwargs["description"] == simple_recipe.description
        assert orm_kwargs["instructions"] == simple_recipe.instructions
        assert orm_kwargs["author_id"] == simple_recipe.author_id

    def test_to_orm_kwargs_nested_objects_conversion(self, complex_recipe):
        """Test to_orm_kwargs properly converts nested objects."""
        orm_kwargs = complex_recipe.to_orm_kwargs()
        
        # Collections should be converted to lists for ORM
        assert isinstance(orm_kwargs["ingredients"], list)
        assert isinstance(orm_kwargs["ratings"], list)
        assert isinstance(orm_kwargs["tags"], list)
        
        # Should preserve length
        assert len(orm_kwargs["ingredients"]) == len(complex_recipe.ingredients)
        assert len(orm_kwargs["ratings"]) == len(complex_recipe.ratings)
        assert len(orm_kwargs["tags"]) == len(complex_recipe.tags)

    def test_to_orm_kwargs_nutrition_facts_conversion(self, complex_recipe):
        """Test to_orm_kwargs handles nutrition facts correctly."""
        orm_kwargs = complex_recipe.to_orm_kwargs()
        
        if complex_recipe.nutri_facts is not None:
            # Should convert to dict or preserve structure for ORM
            assert "nutri_facts" in orm_kwargs
            # The exact format depends on ORM requirements
            assert orm_kwargs["nutri_facts"] is not None


class TestApiRecipeRoundTrip:
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
        """Test round-trip conversions with edge case recipes."""
        edge_case_recipe = edge_case_recipes[case_name]
        
        # Test API → Domain → API round-trip
        domain_recipe = edge_case_recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        # Key fields should be preserved
        assert recovered_api.id == edge_case_recipe.id
        assert recovered_api.name == edge_case_recipe.name
        assert recovered_api.meal_id == edge_case_recipe.meal_id
        assert len(recovered_api.ingredients) == len(edge_case_recipe.ingredients)
        assert len(recovered_api.ratings) == len(edge_case_recipe.ratings)
        assert len(recovered_api.tags) == len(edge_case_recipe.tags)


class TestApiRecipeComputedProperties:
    """
    Test suite for computed properties functionality.
    """

    # =============================================================================
    # COMPUTED PROPERTIES TESTS
    # =============================================================================

    def test_average_rating_correction_round_trip(self):
        """Test that incorrect computed properties are corrected during round-trip."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_incorrect_averages, validate_average_rating_correction_roundtrip
        )
        
        # Create recipe with incorrect averages
        incorrect_recipe = create_api_recipe_with_incorrect_averages()
        
        # Use the validation helper for round-trip correction test
        success, details = validate_average_rating_correction_roundtrip(incorrect_recipe)
        
        assert success, f"Average rating correction failed: {details}"
        assert details["taste_corrected"], "Taste rating not corrected"
        assert details["convenience_corrected"], "Convenience rating not corrected"

    def test_computed_properties_with_no_ratings(self):
        """Test computed properties when recipe has no ratings."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_without_ratings
        )
        
        no_ratings_recipe = create_api_recipe_without_ratings()
        
        # With no ratings, computed properties should be None
        assert no_ratings_recipe.average_taste_rating is None
        assert no_ratings_recipe.average_convenience_rating is None
        assert len(no_ratings_recipe.ratings) == 0

    def test_computed_properties_with_multiple_ratings(self, complex_recipe):
        """Test computed properties with multiple ratings."""
        if len(complex_recipe.ratings) > 1:
            # Calculate expected averages manually
            total_taste = sum(rating.taste for rating in complex_recipe.ratings)
            total_convenience = sum(rating.convenience for rating in complex_recipe.ratings)
            count = len(complex_recipe.ratings)
            
            expected_taste_avg = total_taste / count
            expected_convenience_avg = total_convenience / count
            
            # Computed properties should match calculated averages
            assert abs(complex_recipe.average_taste_rating - expected_taste_avg) < 0.01
            assert abs(complex_recipe.average_convenience_rating - expected_convenience_avg) < 0.01

    def test_json_with_incorrect_averages_correction(self):
        """Test JSON round-trip with incorrect computed properties correction."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_incorrect_averages
        )
        
        # Create recipe with incorrect averages
        incorrect_average = create_api_recipe_with_incorrect_averages()
        
        # Round-trip through domain to get corrected values
        domain_recipe = incorrect_average.to_domain()
        corrected_recipe = ApiRecipe.from_domain(domain_recipe)
        
        # JSON round-trip should preserve corrected values
        json_str = corrected_recipe.model_dump_json()
        restored_recipe = ApiRecipe.model_validate_json(json_str)
        
        assert restored_recipe.average_taste_rating == corrected_recipe.average_taste_rating
        assert restored_recipe.average_convenience_rating == corrected_recipe.average_convenience_rating

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
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_invalid_json_test_cases
        )
        
        # Create invalid JSON test cases
        invalid_json_cases = create_invalid_json_test_cases()
        
        for case in invalid_json_cases:
            json_str = json.dumps(case["data"])
            
            with pytest.raises(ValueError):
                ApiRecipe.model_validate_json(json_str) 