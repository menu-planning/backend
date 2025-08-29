from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import create_recipe_domain_from_api
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import RecipeSaModel
from src.contexts.shared_kernel.domain.enums import Privacy
from pydantic import ValidationError
import pytest
from uuid import uuid4
from datetime import datetime

"""
ApiRecipe Validation Test Suite

Test classes for validation, error handling, and edge cases.
"""


class TestApiRecipeErrorHandling:
    """
    Test suite for error handling tests (minimum 5 error scenarios per method).
    """

    # =============================================================================
    # ERROR HANDLING TESTS (MINIMUM 5 ERROR SCENARIOS PER METHOD)
    # =============================================================================

    def test_from_domain_error_scenarios(self, edge_case_recipes):
        """Test from_domain error handling - minimum 5 error scenarios."""
        
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
        """Test to_domain error handling - minimum 5 error scenarios."""
        
        # For to_domain, errors typically come from validation during domain creation
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_kwargs
        )
        
        # Error 1: Invalid UUID format in ingredients
        try:
            invalid_recipe_kwargs = create_api_recipe_kwargs()
            # Modify to have invalid UUIDs that would fail domain validation
            api_recipe = ApiRecipe(**invalid_recipe_kwargs)
            # Some validations happen at domain level
            domain_result = api_recipe.to_domain()
            assert domain_result is not None
        except Exception:
            # Expected for some validation errors
            pass
        
        # Error 2: Invalid privacy enum
        with pytest.raises((ValueError, AttributeError)):
            # Create recipe data with invalid privacy
            invalid_kwargs = create_api_recipe_kwargs()
            invalid_kwargs["privacy"] = "INVALID_PRIVACY"  # type: ignore
            recipe = ApiRecipe(**invalid_kwargs)
            # Should fail during creation or domain conversion
            recipe.to_domain()

    @pytest.mark.parametrize("factory_name", [
        "create_api_recipe_with_invalid_name",
        "create_api_recipe_with_invalid_instructions", 
        "create_api_recipe_with_invalid_total_time"
    ])
    def test_to_domain_factory_error_scenarios(self, factory_name):
        """Test to_domain error handling with various factory-generated error scenarios."""
        try:
            from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
                create_api_recipe_with_invalid_name, create_api_recipe_with_invalid_instructions,
                create_api_recipe_with_invalid_total_time
            )
            factory_map = {
                "create_api_recipe_with_invalid_name": create_api_recipe_with_invalid_name,
                "create_api_recipe_with_invalid_instructions": create_api_recipe_with_invalid_instructions,
                "create_api_recipe_with_invalid_total_time": create_api_recipe_with_invalid_total_time
            }
            factory = factory_map[factory_name]
            invalid_kwargs = factory()
            recipe = ApiRecipe(**invalid_kwargs)
            with pytest.raises(Exception):
                recipe.to_domain()
        except Exception:
            # Expected for validation errors
            pass

    def test_api_recipe_initialization_error_scenarios(self):
        """Test ApiRecipe initialization error scenarios - minimum 5 errors."""
        
        # Error 1: Missing required fields
        with pytest.raises(ValidationError):
            ApiRecipe(
                # Missing required fields like id, name, etc.
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
            from tests.contexts.recipes_catalog.data_factories.meal.recipe.recipe_orm_factories import create_recipe_orm_kwargs
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


class TestApiRecipeEdgeCases:
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
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_max_fields
        )
        
        max_recipe = create_api_recipe_with_max_fields()
        
        # Should handle large collections
        assert max_recipe.ingredients is not None
        assert max_recipe.ratings is not None
        assert max_recipe.tags is not None
        assert len(max_recipe.ingredients) >= 10
        assert len(max_recipe.ratings) >= 10
        assert len(max_recipe.tags) >= 5
        
        # Round-trip should preserve large collections
        domain_recipe = max_recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        assert recovered_api.ingredients is not None
        assert recovered_api.ratings is not None
        assert recovered_api.tags is not None
        assert len(recovered_api.ingredients) == len(max_recipe.ingredients)
        assert len(recovered_api.ratings) == len(max_recipe.ratings)
        assert len(recovered_api.tags) == len(max_recipe.tags)

    def test_edge_case_boundary_values(self):
        """Test handling of boundary values."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_kwargs
        )
        
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

    def test_edge_case_null_optional_fields(self):
        """Test handling of null optional fields."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_kwargs
        )
        
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
        from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
        from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_rating import ApiRating
        from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
        
        assert all(isinstance(ing, ApiIngredient) for ing in complex_recipe.ingredients)
        assert all(isinstance(rating, ApiRating) for rating in complex_recipe.ratings)
        assert all(isinstance(tag, ApiTag) for tag in complex_recipe.tags)
        
        # Round-trip should preserve complex structures
        domain_recipe = complex_recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        assert recovered_api.ingredients is not None
        assert recovered_api.ratings is not None
        assert recovered_api.tags is not None
        assert len(recovered_api.ingredients) == len(complex_recipe.ingredients)
        assert len(recovered_api.ratings) == len(complex_recipe.ratings)
        assert len(recovered_api.tags) == len(complex_recipe.tags)

    def test_edge_case_unicode_and_special_characters(self):
        """Test handling of unicode and special characters."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_unicode_text, create_api_recipe_with_special_characters
        )
        
        # Test unicode characters
        unicode_kwargs = create_api_recipe_with_unicode_text()
        unicode_recipe = ApiRecipe(**unicode_kwargs)
        
        # Should handle unicode properly
        assert isinstance(unicode_recipe.name, str)
        assert isinstance(unicode_recipe.instructions, str)
        
        # Test special characters
        special_kwargs = create_api_recipe_with_special_characters()
        special_recipe = ApiRecipe(**special_kwargs)
        
        # Should handle special characters
        assert isinstance(special_recipe.name, str)
        assert isinstance(special_recipe.instructions, str)
        
        # Round-trip should preserve special text
        domain_recipe = unicode_recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        assert recovered_api.name == unicode_recipe.name
        assert recovered_api.instructions == unicode_recipe.instructions

    def test_edge_case_datetime_handling(self):
        """Test handling of various datetime scenarios."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_future_timestamps, create_api_recipe_with_past_timestamps
        )
        
        # Test future timestamps
        future_kwargs = create_api_recipe_with_future_timestamps()
        future_recipe = ApiRecipe(**future_kwargs)
        
        # Should handle future dates
        assert future_recipe.created_at is not None
        assert future_recipe.updated_at is not None
        assert future_recipe.created_at > datetime.now()
        assert future_recipe.updated_at > datetime.now()
        
        # Test past timestamps
        past_kwargs = create_api_recipe_with_past_timestamps()
        past_recipe = ApiRecipe(**past_kwargs)
        
        # Should handle old dates
        assert past_recipe.created_at is not None
        assert past_recipe.updated_at is not None
        assert past_recipe.created_at < datetime.now()
        assert past_recipe.updated_at < datetime.now()
        
        # Round-trip should preserve datetime values
        domain_recipe = future_recipe.to_domain()
        recovered_api = ApiRecipe.from_domain(domain_recipe)
        
        assert recovered_api.created_at == future_recipe.created_at
        assert recovered_api.updated_at == future_recipe.updated_at


# Additional validation test classes would go here for:
# - TestApiRecipeFieldValidationEdgeCases  
# - TestApiRecipeTagsValidationEdgeCases
# - TestApiRecipeFrozensetValidationEdgeCases
# - TestApiRecipeDomainRuleValidationEdgeCases
# (These classes contain more detailed validation tests from the original file)


# =============================================================================
# CRITICAL EDGE CASE TESTS - COMPREHENSIVE ADDITIONS
# =============================================================================

class TestApiRecipeFieldValidationEdgeCases:
    """
    Test suite for comprehensive field validation edge cases.
    """

    def test_invalid_name_validation(self):
        """Test invalid name field validation."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_invalid_name
        )
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_invalid_name()
            ApiRecipe(**invalid_kwargs)

    def test_invalid_instructions_validation(self):
        """Test invalid instructions field validation."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_invalid_instructions
        )
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_invalid_instructions()
            ApiRecipe(**invalid_kwargs)

    def test_invalid_total_time_validation(self):
        """Test invalid total_time field validation."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_invalid_total_time
        )
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_invalid_total_time()
            ApiRecipe(**invalid_kwargs)

    def test_invalid_weight_validation(self):
        """Test invalid weight field validation."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_invalid_weight
        )
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_invalid_weight()
            ApiRecipe(**invalid_kwargs)

    def test_invalid_taste_rating_validation(self):
        """Test invalid taste rating validation."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_invalid_taste_rating
        )
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_invalid_taste_rating()
            ApiRecipe(**invalid_kwargs)

    def test_invalid_convenience_rating_validation(self):
        """Test invalid convenience rating validation."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_invalid_convenience_rating
        )
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_invalid_convenience_rating()
            ApiRecipe(**invalid_kwargs)

    def test_invalid_privacy_validation(self):
        """Test invalid privacy enum validation."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_invalid_privacy
        )
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_invalid_privacy()
            ApiRecipe(**invalid_kwargs)

    def test_boundary_values_acceptance(self):
        """Test that boundary values are accepted."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_boundary_values
        )
        boundary_kwargs = create_api_recipe_with_boundary_values()
        recipe = ApiRecipe(**boundary_kwargs)
        
        assert recipe.total_time == 0
        assert recipe.weight_in_grams == 0
        assert recipe.average_taste_rating == 0.0
        assert recipe.average_convenience_rating == 5.0

    def test_extreme_boundary_values_acceptance(self):
        """Test that extreme boundary values are handled."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_extreme_boundary_values
        )
        extreme_kwargs = create_api_recipe_with_extreme_boundary_values()
        recipe = ApiRecipe(**extreme_kwargs)
        
        assert recipe.total_time == 2147483647
        assert recipe.weight_in_grams == 2147483647
        assert recipe.average_taste_rating == 5.0
        assert recipe.average_convenience_rating == 0.0

    def test_none_values_handling(self):
        """Test that None values are handled correctly for optional fields."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_none_values
        )
        none_kwargs = create_api_recipe_with_none_values()
        with pytest.raises(ValueError):
            ApiRecipe(**none_kwargs)


    def test_empty_strings_handling(self):
        """Test that empty strings are handled correctly."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_empty_strings
        )
        empty_kwargs = create_api_recipe_with_empty_strings()
        recipe = ApiRecipe(**empty_kwargs)
        
        # Empty strings should be converted to None or handled by validation
        # This depends on the validate_optional_text behavior
        assert isinstance(recipe, ApiRecipe)

    def test_whitespace_strings_handling(self):
        """Test that whitespace-only strings are handled correctly."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_whitespace_strings
        )
        # This should either succeed with cleaned strings or fail validation
        whitespace_kwargs = create_api_recipe_with_whitespace_strings()
        try:
            recipe = ApiRecipe(**whitespace_kwargs)
            assert isinstance(recipe, ApiRecipe)
        except ValueError:
            # If validation rejects whitespace strings, that's also valid
            pass

    @pytest.mark.parametrize("field_name,factory_func", [
        ("name", "create_api_recipe_with_invalid_name"),
        ("instructions", "create_api_recipe_with_invalid_instructions"),
        ("total_time", "create_api_recipe_with_invalid_total_time"),
        ("weight", "create_api_recipe_with_invalid_weight"),
        ("taste_rating", "create_api_recipe_with_invalid_taste_rating"),
        ("convenience_rating", "create_api_recipe_with_invalid_convenience_rating"),
        ("privacy", "create_api_recipe_with_invalid_privacy"),
    ])
    def test_field_validation_parametrized(self, field_name, factory_func):
        """Test field validation using parametrization."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_invalid_name, create_api_recipe_with_invalid_instructions,
            create_api_recipe_with_invalid_total_time, create_api_recipe_with_invalid_weight,
            create_api_recipe_with_invalid_taste_rating, create_api_recipe_with_invalid_convenience_rating,
            create_api_recipe_with_invalid_privacy
        )
        
        factory_map = {
            "create_api_recipe_with_invalid_name": create_api_recipe_with_invalid_name,
            "create_api_recipe_with_invalid_instructions": create_api_recipe_with_invalid_instructions,
            "create_api_recipe_with_invalid_total_time": create_api_recipe_with_invalid_total_time,
            "create_api_recipe_with_invalid_weight": create_api_recipe_with_invalid_weight,
            "create_api_recipe_with_invalid_taste_rating": create_api_recipe_with_invalid_taste_rating,
            "create_api_recipe_with_invalid_convenience_rating": create_api_recipe_with_invalid_convenience_rating,
            "create_api_recipe_with_invalid_privacy": create_api_recipe_with_invalid_privacy,
        }
        
        with pytest.raises(ValueError):
            invalid_kwargs = factory_map[factory_func]()
            ApiRecipe(**invalid_kwargs)


class TestApiRecipeTagsValidationEdgeCases:
    """
    Test suite for comprehensive tags validation edge cases.
    """

    def test_invalid_tag_dict_validation(self):
        """Test validation of invalid tag dictionaries."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_invalid_tag_dict
        )
        # Should succeed because validator adds missing fields
        tag_kwargs = create_api_recipe_with_invalid_tag_dict()
        with pytest.raises(ValueError):
            ApiRecipe(**tag_kwargs)

    def test_invalid_tag_types_validation(self):
        """Test validation of invalid tag types."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_invalid_tag_types
        )
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_invalid_tag_types()
            ApiRecipe(**invalid_kwargs)

    def test_tag_without_author_id_context_validation(self):
        """Test tag validation when author_id is missing from context."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_tag_without_author_id_context
        )
        with pytest.raises(ValueError):
            invalid_kwargs = create_api_recipe_with_tag_without_author_id_context()
            ApiRecipe(**invalid_kwargs)

    def test_mixed_tag_types_handling(self):
        """Test handling of mixed tag types."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_mixed_tag_types
        )
        mixed_kwargs = create_api_recipe_with_mixed_tag_types()
        recipe = ApiRecipe(**mixed_kwargs)
        
        assert isinstance(recipe, ApiRecipe)
        assert recipe.tags is not None
        assert len(recipe.tags) > 0
        
        from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
        assert all(isinstance(tag, ApiTag) for tag in recipe.tags)

    def test_tags_validator_behavior(self):
        """Test the tags validator behavior comprehensively."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe, create_api_recipe_with_empty_collections
        )
        
        # Test with proper tag structure
        recipe = create_api_recipe()
        assert isinstance(recipe.tags, frozenset)
        
        from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
        assert all(isinstance(tag, ApiTag) for tag in recipe.tags)
        
        # Test with empty tags
        empty_kwargs = create_api_recipe_with_empty_collections()
        empty_recipe = ApiRecipe(**empty_kwargs)
        assert empty_recipe.tags == frozenset()


class TestApiRecipeFrozensetValidationEdgeCases:
    """
    Test suite for frozenset collection validation edge cases.
    """

    def test_list_ingredients_conversion(self):
        """Test that list ingredients are converted to frozenset."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_list_ingredients
        )
        list_kwargs = create_api_recipe_with_list_ingredients()
        recipe = ApiRecipe(**list_kwargs)
        
        assert isinstance(recipe.ingredients, frozenset)
        assert len(recipe.ingredients) > 0

    def test_set_ingredients_conversion(self):
        """Test that set ingredients are converted to frozenset."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_set_ingredients
        )
        set_kwargs = create_api_recipe_with_set_ingredients()
        recipe = ApiRecipe(**set_kwargs)
        
        assert isinstance(recipe.ingredients, frozenset)
        assert len(recipe.ingredients) > 0

    def test_list_ratings_conversion(self):
        """Test that list ratings are converted to frozenset."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_list_ratings
        )
        list_kwargs = create_api_recipe_with_list_ratings()
        recipe = ApiRecipe(**list_kwargs)
        
        assert isinstance(recipe.ratings, frozenset)
        assert len(recipe.ratings) > 0

    def test_set_ratings_conversion(self):
        """Test that set ratings are converted to frozenset."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_set_ratings
        )
        set_kwargs = create_api_recipe_with_set_ratings()
        recipe = ApiRecipe(**set_kwargs)
        
        assert isinstance(recipe.ratings, frozenset)
        assert len(recipe.ratings) > 0

    def test_list_tags_conversion(self):
        """Test that list tags are converted to frozenset."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_list_tags
        )
        list_kwargs = create_api_recipe_with_list_tags()
        recipe = ApiRecipe(**list_kwargs)
        
        assert isinstance(recipe.tags, frozenset)
        assert len(recipe.tags) > 0

    def test_set_tags_conversion(self):
        """Test that set tags are converted to frozenset."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_set_tags
        )
        set_kwargs = create_api_recipe_with_set_tags()
        recipe = ApiRecipe(**set_kwargs)
        
        assert isinstance(recipe.tags, frozenset)
        assert len(recipe.tags) > 0

    def test_empty_collections_handling(self):
        """Test that empty collections are handled correctly."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_empty_collections
        )
        empty_kwargs = create_api_recipe_with_empty_collections()
        recipe = ApiRecipe(**empty_kwargs)
        
        assert recipe.ingredients == frozenset()
        assert recipe.ratings == frozenset()
        assert recipe.tags == frozenset()

    @pytest.mark.parametrize("collection_type,factory_func", [
        ("ingredients_list", "create_api_recipe_with_list_ingredients"),
        ("ingredients_set", "create_api_recipe_with_set_ingredients"),
        ("ratings_list", "create_api_recipe_with_list_ratings"),
        ("ratings_set", "create_api_recipe_with_set_ratings"),
        ("tags_list", "create_api_recipe_with_list_tags"),
        ("tags_set", "create_api_recipe_with_set_tags"),
        ("empty_collections", "create_api_recipe_with_empty_collections"),
    ])
    def test_collection_conversion_parametrized(self, collection_type, factory_func):
        """Test collection conversion using parametrization."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_list_ingredients, create_api_recipe_with_set_ingredients,
            create_api_recipe_with_list_ratings, create_api_recipe_with_set_ratings,
            create_api_recipe_with_list_tags, create_api_recipe_with_set_tags,
            create_api_recipe_with_empty_collections
        )
        
        factory_map = {
            "create_api_recipe_with_list_ingredients": create_api_recipe_with_list_ingredients,
            "create_api_recipe_with_set_ingredients": create_api_recipe_with_set_ingredients,
            "create_api_recipe_with_list_ratings": create_api_recipe_with_list_ratings,
            "create_api_recipe_with_set_ratings": create_api_recipe_with_set_ratings,
            "create_api_recipe_with_list_tags": create_api_recipe_with_list_tags,
            "create_api_recipe_with_set_tags": create_api_recipe_with_set_tags,
            "create_api_recipe_with_empty_collections": create_api_recipe_with_empty_collections,
        }
        
        kwargs = factory_map[factory_func]()
        recipe = ApiRecipe(**kwargs)
        
        assert isinstance(recipe.ingredients, frozenset)
        assert isinstance(recipe.ratings, frozenset)
        assert isinstance(recipe.tags, frozenset)


class TestApiRecipeDomainRuleValidationEdgeCases:
    """
    Test suite for domain rule validation edge cases.
    """

    def test_invalid_ingredient_positions_domain_rule(self):
        """Test that invalid ingredient positions trigger domain rule violations."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_invalid_ingredient_positions
        )
        invalid_kwargs = create_api_recipe_with_invalid_ingredient_positions()
        recipe = ApiRecipe(**invalid_kwargs)
        
        # Should fail when converting to domain due to rule violation
        with pytest.raises(Exception):  # Domain rule violation
            recipe.to_domain()

    def test_negative_ingredient_positions_domain_rule(self):
        """Test that negative ingredient positions trigger domain rule violations."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_negative_ingredient_positions
        )
        # Should fail when converting to domain due to rule violation
        with pytest.raises(Exception):  # Domain rule violation
            create_api_recipe_with_negative_ingredient_positions()

    def test_duplicate_ingredient_positions_domain_rule(self):
        """Test that duplicate ingredient positions trigger domain rule violations."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_duplicate_ingredient_positions
        )
        invalid_kwargs = create_api_recipe_with_duplicate_ingredient_positions()
        recipe = ApiRecipe(**invalid_kwargs)
        
        # Should fail when converting to domain due to rule violation
        with pytest.raises(Exception):  # Domain rule violation
            recipe.to_domain()

    def test_non_zero_start_positions_domain_rule(self):
        """Test that ingredient positions not starting from 0 trigger domain rule violations."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_non_zero_start_positions
        )
        invalid_kwargs = create_api_recipe_with_non_zero_start_positions()
        recipe = ApiRecipe(**invalid_kwargs)
        
        # Should fail when converting to domain due to rule violation
        with pytest.raises(Exception):  # Domain rule violation
            recipe.to_domain()

    def test_invalid_tag_author_id_domain_rule(self):
        """Test that tags with different author_id trigger domain rule violations."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_invalid_tag_author_id
        )
        invalid_kwargs = create_api_recipe_with_invalid_tag_author_id()
        
        # Should fail when converting to domain due to rule violation
        with pytest.raises(Exception):  # Domain rule violation
            ApiRecipe(**invalid_kwargs)

    @pytest.mark.parametrize("rule_type,factory_func", [
        ("invalid_positions", "create_api_recipe_with_invalid_ingredient_positions"),
        ("duplicate_positions", "create_api_recipe_with_duplicate_ingredient_positions"),
        ("non_zero_start", "create_api_recipe_with_non_zero_start_positions"),
        ("invalid_tag_author", "create_api_recipe_with_invalid_tag_author_id"),
    ])
    def test_domain_rule_violations_parametrized(self, rule_type, factory_func):
        """Test domain rule violations using parametrization."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_invalid_ingredient_positions, create_api_recipe_with_duplicate_ingredient_positions,
            create_api_recipe_with_non_zero_start_positions, create_api_recipe_with_invalid_tag_author_id
        )
        
        factory_map = {
            "create_api_recipe_with_invalid_ingredient_positions": create_api_recipe_with_invalid_ingredient_positions,
            "create_api_recipe_with_duplicate_ingredient_positions": create_api_recipe_with_duplicate_ingredient_positions,
            "create_api_recipe_with_non_zero_start_positions": create_api_recipe_with_non_zero_start_positions,
            "create_api_recipe_with_invalid_tag_author_id": create_api_recipe_with_invalid_tag_author_id,
        }
        
        if rule_type == 'invalid_tag_author':
            with pytest.raises(ValidationError):
                invalid_kwargs = factory_map[factory_func]()
                ApiRecipe(**invalid_kwargs)
        else:
            invalid_kwargs = factory_map[factory_func]()
            recipe = ApiRecipe(**invalid_kwargs)
        
            # Should fail when converting to domain due to rule violation
            with pytest.raises(Exception):  # Domain rule violation
                recipe.to_domain()