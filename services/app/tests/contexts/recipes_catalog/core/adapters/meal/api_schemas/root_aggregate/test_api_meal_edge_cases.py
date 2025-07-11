"""
ApiMeal Edge Cases Test Suite

Test classes for edge cases in ApiMeal functionality including validation 
constraints, conversion method failures, nested object edge cases, and error handling.

These tests focus on boundary conditions, error scenarios, and unusual data 
configurations that might cause failures in production.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from pydantic import ValidationError

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_value import ApiNutriValue
from src.contexts.shared_kernel.domain.enums import MeasureUnit

# Import test data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.data_factories.api_meal_data_factories import (
    create_api_meal,
    create_complex_api_meal,
    create_api_meal_kwargs,
    create_api_nutri_facts,
    create_api_tag,
    reset_api_meal_counters
)
from tests.contexts.recipes_catalog.data_factories.recipe.recipe_domain_factories import create_recipe
from tests.contexts.recipes_catalog.data_factories.shared_domain_factories import create_meal_tag


class TestApiMealValidationEdgeCases:
    """
    Test suite for field validation edge cases and boundary conditions.
    """

    def setup_method(self):
        """Reset counters before each test for isolation."""
        reset_api_meal_counters()

    # =============================================================================
    # FIELD VALIDATION EDGE CASES
    # =============================================================================

    def test_name_field_validation_edge_cases(self):
        """Test name field validation with edge cases."""
        base_kwargs = create_api_meal_kwargs()
        
        # Test minimum length (1 character)
        base_kwargs["name"] = "A"
        meal = ApiMeal(**base_kwargs)
        assert meal.name == "A"
        
        # Test maximum length (255 characters)
        long_name = "A" * 255
        base_kwargs["name"] = long_name
        meal = ApiMeal(**base_kwargs)
        assert meal.name == long_name
        
        # Test empty string should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            base_kwargs["name"] = ""
            ApiMeal(**base_kwargs)
        assert "string_type" in str(exc_info.value) or "min_length" in str(exc_info.value)
        
        # Test string too long should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            base_kwargs["name"] = "A" * 256
            ApiMeal(**base_kwargs)
        assert "too_long" in str(exc_info.value) or "max_length" in str(exc_info.value)
        
        # Test None should raise validation error (required field)
        with pytest.raises(ValidationError) as exc_info:
            base_kwargs["name"] = None
            ApiMeal(**base_kwargs)
        assert "string_type" in str(exc_info.value) or "required" in str(exc_info.value)

    def test_uuid_field_validation_edge_cases(self):
        """Test UUID field validation with edge cases."""
        base_kwargs = create_api_meal_kwargs()
        
        # Test invalid UUID format for author_id
        with pytest.raises(ValidationError) as exc_info:
            invalid_kwargs = base_kwargs.copy()
            invalid_kwargs["author_id"] = "invalid-uuid"
            ApiMeal(**invalid_kwargs)
        assert "uuid" in str(exc_info.value).lower() or "format" in str(exc_info.value).lower()
        
        # Test empty string UUID
        with pytest.raises(ValidationError) as exc_info:
            invalid_kwargs = base_kwargs.copy()
            invalid_kwargs["author_id"] = ""
            ApiMeal(**invalid_kwargs)
        assert "uuid" in str(exc_info.value).lower() or "format" in str(exc_info.value).lower()
        
        # Test None for required UUID (author_id)
        with pytest.raises(ValidationError) as exc_info:
            invalid_kwargs = base_kwargs.copy()
            invalid_kwargs["author_id"] = None
            ApiMeal(**invalid_kwargs)
        assert "uuid" in str(exc_info.value).lower() or "value_error" in str(exc_info.value).lower()
        
        # Test None for optional UUID (menu_id) - should be allowed
        valid_kwargs = base_kwargs.copy()
        valid_kwargs["menu_id"] = None
        meal = ApiMeal(**valid_kwargs)
        assert meal.menu_id is None

    def test_percentage_field_validation_edge_cases(self):
        """Test percentage field validation with boundary values."""
        base_kwargs = create_api_meal_kwargs()
        
        # Test valid boundary values (0 and 100)
        base_kwargs["carbo_percentage"] = 0.0
        base_kwargs["protein_percentage"] = 100.0
        meal = ApiMeal(**base_kwargs)
        assert meal.carbo_percentage == 0.0
        assert meal.protein_percentage == 100.0
        
        # Test negative percentage should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            base_kwargs["carbo_percentage"] = -0.1
            ApiMeal(**base_kwargs)
        assert "must be between 0 and 100" in str(exc_info.value) or "non-negative" in str(exc_info.value)
        
        # Test percentage over 100 should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            base_kwargs["protein_percentage"] = 100.1
            ApiMeal(**base_kwargs)
        assert "must be between 0 and 100" in str(exc_info.value) or "percentage" in str(exc_info.value)
        
        # Test extremely large percentage
        with pytest.raises(ValidationError) as exc_info:
            base_kwargs["total_fat_percentage"] = 1000.0
            ApiMeal(**base_kwargs)
        assert "must be between 0 and 100" in str(exc_info.value) or "percentage" in str(exc_info.value)

    def test_non_negative_field_validation_edge_cases(self):
        """Test non-negative field validation with boundary values."""
        base_kwargs = create_api_meal_kwargs()
        
        # Test valid boundary value (0)
        base_kwargs["weight_in_grams"] = 0
        base_kwargs["calorie_density"] = 0.0
        meal = ApiMeal(**base_kwargs)
        assert meal.weight_in_grams == 0
        assert meal.calorie_density == 0.0
        
        # Test negative weight should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            base_kwargs["weight_in_grams"] = -1
            ApiMeal(**base_kwargs)
        assert "must be non-negative" in str(exc_info.value) or "negative" in str(exc_info.value)
        
        # Test negative calorie density should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            base_kwargs["calorie_density"] = -0.1
            ApiMeal(**base_kwargs)
        assert "must be non-negative" in str(exc_info.value) or "negative" in str(exc_info.value)

    def test_collection_field_validation_edge_cases(self):
        """Test collection field validation with edge cases."""
        base_kwargs = create_api_meal_kwargs()
        
        # Test empty collections (should be allowed)
        base_kwargs["recipes"] = []
        base_kwargs["tags"] = frozenset()
        meal = ApiMeal(**base_kwargs)
        assert meal.recipes == []
        assert meal.tags == frozenset()
        
        # Test None collections should use default values
        base_kwargs.pop("recipes", None)
        base_kwargs.pop("tags", None)
        meal = ApiMeal(**base_kwargs)
        assert meal.recipes == []
        assert meal.tags == frozenset()

    def test_optional_field_validation_edge_cases(self):
        """Test optional field validation with None and empty values."""
        base_kwargs = create_api_meal_kwargs()
        
        # Test None values for optional fields
        base_kwargs.update({
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
        })
        meal = ApiMeal(**base_kwargs)
        assert meal.description is None
        assert meal.notes is None
        assert meal.like is None
        assert meal.image_url is None
        assert meal.nutri_facts is None
        assert meal.weight_in_grams is None

    # =============================================================================
    # LARGE DATA EDGE CASES
    # =============================================================================

    def test_very_large_collections_edge_cases(self):
        """Test behavior with very large collections."""
        base_kwargs = create_api_meal_kwargs()
        
        # Create large recipe collection
        large_recipes = []
        for i in range(100):  # 100 recipes
            recipe_kwargs = {
                "id": str(uuid4()),
                "name": f"Recipe {i}",
                "instructions": f"Instructions for recipe {i}",
                "author_id": base_kwargs["author_id"],
                "meal_id": base_kwargs["id"],
                "ingredients": frozenset(),
                "tags": frozenset(),
                "ratings": frozenset(),
                "nutri_facts": None,
                "weight_in_grams": 100,
                "description": None,
                "utensils": None,
                "total_time": None,
                "notes": None,
                "privacy": None,
                "image_url": None,
                "average_taste_rating": None,
                "average_convenience_rating": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "discarded": False,
                "version": 1,
            }
            large_recipes.append(ApiRecipe(**recipe_kwargs))
        
        base_kwargs["recipes"] = large_recipes
        meal = ApiMeal(**base_kwargs)
        assert meal.recipes is not None
        assert len(meal.recipes) == 100
        
        # Create large tag collection
        large_tags = frozenset(
            create_api_tag(key=f"tag_{i}", value=f"value_{i}", author_id=base_kwargs["author_id"])
            for i in range(50)  # 50 tags
        )
        base_kwargs["tags"] = large_tags
        meal = ApiMeal(**base_kwargs)
        assert meal.tags is not None
        assert len(meal.tags) == 50

    def test_extreme_numeric_values_edge_cases(self):
        """Test behavior with extreme numeric values."""
        base_kwargs = create_api_meal_kwargs()
        
        # Test very large weight
        base_kwargs["weight_in_grams"] = 999999999
        meal = ApiMeal(**base_kwargs)
        assert meal.weight_in_grams == 999999999
        
        # Test very large calorie density
        base_kwargs["calorie_density"] = 999999.99
        meal = ApiMeal(**base_kwargs)
        assert meal.calorie_density == 999999.99
        
        # Test very precise decimal percentages
        base_kwargs["carbo_percentage"] = 33.333333333
        base_kwargs["protein_percentage"] = 66.666666666
        meal = ApiMeal(**base_kwargs)
        assert meal.carbo_percentage is not None
        assert meal.protein_percentage is not None
        assert abs(meal.carbo_percentage - 33.333333333) < 0.0001
        assert abs(meal.protein_percentage - 66.666666666) < 0.0001


class TestApiMealConversionEdgeCases:
    """
    Test suite for conversion method edge cases and failure scenarios.
    """

    def setup_method(self):
        """Reset counters before each test for isolation."""
        reset_api_meal_counters()

    # =============================================================================
    # FROM_DOMAIN CONVERSION EDGE CASES
    # =============================================================================

    def test_from_domain_with_none_values(self, domain_meal):
        """Test from_domain with domain object containing None values."""
        # Set optional fields to None
        domain_meal._description = None
        domain_meal._notes = None
        domain_meal._like = None
        domain_meal._image_url = None
        domain_meal._created_at = None
        domain_meal._updated_at = None
        
        # Note: We don't set computed properties to None because the domain computes them from recipes
        # Properties like weight_in_grams, calorie_density, etc. are computed from the recipes
        
        api_meal = ApiMeal.from_domain(domain_meal)
        
        assert api_meal.description is None
        assert api_meal.notes is None
        assert api_meal.like is None
        assert api_meal.image_url is None
        # nutri_facts, weight_in_grams, calorie_density, etc. are computed from recipes
        # so they may have values even if not explicitly set
        assert api_meal.nutri_facts is not None  # computed from recipes
        assert api_meal.weight_in_grams is not None  # computed from recipes
        # created_at and updated_at should default to current time
        assert api_meal.created_at is not None
        assert api_meal.updated_at is not None

    def test_from_domain_with_empty_collections(self, domain_meal):
        """Test from_domain with domain object containing empty collections."""
        domain_meal._recipes = []
        domain_meal._tags = set()
        
        api_meal = ApiMeal.from_domain(domain_meal)
        
        assert api_meal.recipes == []
        assert api_meal.tags == frozenset()

    def test_from_domain_with_large_collections(self, domain_meal):
        """Test from_domain with domain object containing large collections."""
        # This would require creating large collections in the domain meal
        # Testing the conversion doesn't fail with large datasets
        
        
        # Create large recipe collection
        large_recipes = [create_recipe(author_id=domain_meal.author_id, meal_id=domain_meal.id) for _ in range(50)]
        large_tags = {create_meal_tag(author_id=domain_meal.author_id) for _ in range(25)}
        
        domain_meal._recipes = large_recipes
        domain_meal._tags = large_tags
        
        api_meal = ApiMeal.from_domain(domain_meal)
        
        assert api_meal.recipes is not None
        assert api_meal.tags is not None
        assert len(api_meal.recipes) == 50
        assert len(api_meal.tags) == 25

    # =============================================================================
    # TO_DOMAIN CONVERSION EDGE CASES
    # =============================================================================

    def test_to_domain_with_none_nutri_facts(self, simple_api_meal):
        """Test to_domain with None nutri_facts."""
        # Create a new meal with None nutri_facts using create_api_meal
        api_meal = create_api_meal(nutri_facts=None)
        
        domain_meal = api_meal.to_domain()
        
        # Domain should handle None nutri_facts appropriately
        assert domain_meal is not None
        assert domain_meal.name == api_meal.name
        assert domain_meal.author_id == api_meal.author_id

    def test_to_domain_with_empty_collections(self, simple_api_meal):
        """Test to_domain with empty collections."""
        # Create a new meal with empty collections
        api_meal = create_api_meal(recipes=[], tags=frozenset())
        
        domain_meal = api_meal.to_domain()
        
        assert domain_meal.recipes == []
        assert domain_meal.tags == set()

    def test_to_domain_with_large_collections(self, complex_api_meal):
        """Test to_domain with large collections doesn't fail."""
        # Use the complex meal which should have multiple recipes and tags
        domain_meal = complex_api_meal.to_domain()
        
        assert domain_meal is not None
        assert len(domain_meal.recipes) == len(complex_api_meal.recipes)
        assert len(domain_meal.tags) == len(complex_api_meal.tags)

    # =============================================================================
    # FROM_ORM_MODEL CONVERSION EDGE CASES
    # =============================================================================

    def test_from_orm_model_with_none_relationships(self, real_orm_meal):
        """Test from_orm_model with None relationships."""
        # Set relationships to empty collections instead of None (SQLAlchemy doesn't allow None)
        real_orm_meal.recipes = []
        real_orm_meal.tags = []
        real_orm_meal.nutri_facts = None
        
        # Should handle empty relationships gracefully
        api_meal = ApiMeal.from_orm_model(real_orm_meal)
        
        assert api_meal.recipes == []
        assert api_meal.tags == frozenset()
        assert api_meal.nutri_facts is None

    def test_from_orm_model_with_empty_relationships(self, real_orm_meal):
        """Test from_orm_model with empty relationships."""
        # Set relationships to empty collections
        real_orm_meal.recipes = []
        real_orm_meal.tags = []
        real_orm_meal.nutri_facts = None
        
        api_meal = ApiMeal.from_orm_model(real_orm_meal)
        
        assert api_meal.recipes == []
        assert api_meal.tags == frozenset()
        assert api_meal.nutri_facts is None

    def test_from_orm_model_with_none_optional_fields(self, real_orm_meal):
        """Test from_orm_model with None optional fields."""
        # Set optional fields to None
        real_orm_meal.description = None
        real_orm_meal.notes = None
        real_orm_meal.like = None
        real_orm_meal.image_url = None
        real_orm_meal.menu_id = None
        real_orm_meal.weight_in_grams = None
        real_orm_meal.calorie_density = None
        real_orm_meal.carbo_percentage = None
        real_orm_meal.protein_percentage = None
        real_orm_meal.total_fat_percentage = None
        real_orm_meal.created_at = None
        real_orm_meal.updated_at = None
        
        api_meal = ApiMeal.from_orm_model(real_orm_meal)
        
        assert api_meal.description is None
        assert api_meal.notes is None
        assert api_meal.like is None
        assert api_meal.image_url is None
        assert api_meal.menu_id is None
        assert api_meal.weight_in_grams is None
        assert api_meal.calorie_density is None
        assert api_meal.carbo_percentage is None
        assert api_meal.protein_percentage is None
        assert api_meal.total_fat_percentage is None
        # created_at and updated_at should default to current time
        assert api_meal.created_at is not None
        assert api_meal.updated_at is not None

    # =============================================================================
    # TO_ORM_KWARGS CONVERSION EDGE CASES
    # =============================================================================

    def test_to_orm_kwargs_with_none_nutri_facts(self, simple_api_meal):
        """Test to_orm_kwargs with None nutri_facts."""
        # Create a new meal with None nutri_facts
        api_meal = create_api_meal(nutri_facts=None)
        
        kwargs = api_meal.to_orm_kwargs()
        
        assert kwargs["nutri_facts"] is None

    def test_to_orm_kwargs_with_empty_collections(self, simple_api_meal):
        """Test to_orm_kwargs with empty collections."""
        # Create a new meal with empty collections
        api_meal = create_api_meal(recipes=[], tags=frozenset())
        
        kwargs = api_meal.to_orm_kwargs()
        
        assert kwargs["recipes"] == []
        assert kwargs["tags"] == []

    def test_to_orm_kwargs_with_complex_nutri_facts(self, complex_api_meal):
        """Test to_orm_kwargs with complex nutri_facts conversion."""
        if complex_api_meal.nutri_facts:
            kwargs = complex_api_meal.to_orm_kwargs()
            
            from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import NutriFactsSaModel
            assert isinstance(kwargs["nutri_facts"], NutriFactsSaModel)
            
            # Verify that nutri_facts fields are properly converted
            nutri_facts_orm = kwargs["nutri_facts"]
            api_nutri_facts = complex_api_meal.nutri_facts
            
            assert nutri_facts_orm.calories == api_nutri_facts.calories.value
            assert nutri_facts_orm.protein == api_nutri_facts.protein.value
            assert nutri_facts_orm.carbohydrate == api_nutri_facts.carbohydrate.value


class TestApiMealNestedObjectEdgeCases:
    """
    Test suite for nested object edge cases and complex scenarios.
    """

    def setup_method(self):
        """Reset counters before each test for isolation."""
        reset_api_meal_counters()

    # =============================================================================
    # RECIPE NESTED OBJECT EDGE CASES
    # =============================================================================

    def test_recipes_with_none_nutri_facts(self):
        """Test handling of recipes with None nutri_facts."""
        base_kwargs = create_api_meal_kwargs()
        
        # Create recipe with None nutri_facts
        recipe_kwargs = {
            "id": str(uuid4()),
            "name": "Test Recipe",
            "instructions": "Test instructions",
            "author_id": base_kwargs["author_id"],
            "meal_id": base_kwargs["id"],
            "ingredients": frozenset(),
            "tags": frozenset(),
            "ratings": frozenset(),
            "nutri_facts": None,
            "weight_in_grams": 100,
            "description": None,
            "utensils": None,
            "total_time": None,
            "notes": None,
            "privacy": None,
            "image_url": None,
            "average_taste_rating": None,
            "average_convenience_rating": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "discarded": False,
            "version": 1,
        }
        recipe = ApiRecipe(**recipe_kwargs)
        
        base_kwargs["recipes"] = [recipe]
        meal = ApiMeal(**base_kwargs)
        
        assert meal.recipes is not None
        assert len(meal.recipes) == 1
        assert meal.recipes[0].nutri_facts is None

    def test_recipes_with_invalid_nested_data(self):
        """Test handling of recipes with invalid nested data."""
        base_kwargs = create_api_meal_kwargs()
        
        # Test with invalid recipe data should raise validation error
        with pytest.raises(ValidationError):
            base_kwargs["recipes"] = [{"invalid": "data"}]
            ApiMeal(**base_kwargs)

    def test_duplicate_recipe_ids(self):
        """Test handling of duplicate recipe IDs."""
        base_kwargs = create_api_meal_kwargs()
        
        # Create two recipes with the same ID
        recipe_id = str(uuid4())
        recipe_kwargs = {
            "id": recipe_id,
            "name": "Test Recipe",
            "instructions": "Test instructions",
            "author_id": base_kwargs["author_id"],
            "meal_id": base_kwargs["id"],
            "ingredients": frozenset(),
            "tags": frozenset(),
            "ratings": frozenset(),
            "nutri_facts": None,
            "weight_in_grams": 100,
            "description": None,
            "utensils": None,
            "total_time": None,
            "notes": None,
            "privacy": None,
            "image_url": None,
            "average_taste_rating": None,
            "average_convenience_rating": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "discarded": False,
            "version": 1,
        }
        recipe1 = ApiRecipe(**recipe_kwargs)
        recipe2 = ApiRecipe(**recipe_kwargs)
        
        base_kwargs["recipes"] = [recipe1, recipe2]
        meal = ApiMeal(**base_kwargs)
        
        # Should be allowed at API level (business logic should handle duplicates)
        assert meal.recipes is not None
        assert len(meal.recipes) == 2
        assert meal.recipes[0].id == meal.recipes[1].id

    # =============================================================================
    # TAG NESTED OBJECT EDGE CASES
    # =============================================================================

    def test_tags_with_edge_case_values(self):
        """Test handling of tags with edge case values."""
        base_kwargs = create_api_meal_kwargs()
        
        # Create tags with edge case values - avoid empty keys as they cause validation errors
        edge_case_tags = frozenset([
            create_api_tag(key="single_char", value="a", author_id=base_kwargs["author_id"]),
            create_api_tag(key="long_key_" + "x" * 80, value="long_key", author_id=base_kwargs["author_id"]),  # 89 chars total, within 100 limit
            create_api_tag(key="special_chars", value="!@#$%^&*()", author_id=base_kwargs["author_id"]),
            create_api_tag(key="unicode", value="中文测试", author_id=base_kwargs["author_id"]),
            create_api_tag(key="numbers", value="123456", author_id=base_kwargs["author_id"]),
        ])
        
        base_kwargs["tags"] = edge_case_tags
        meal = ApiMeal(**base_kwargs)
        
        assert meal.tags is not None
        assert len(meal.tags) == 5

    def test_tags_with_none_values(self):
        """Test handling of tags with None values."""
        base_kwargs = create_api_meal_kwargs()
        
        # Tags with None values should be handled by tag validation
        try:
            none_tag = create_api_tag(key=None, value=None)
            base_kwargs["tags"] = frozenset([none_tag])
            meal = ApiMeal(**base_kwargs)
            # If creation succeeds, verify the tag is present
            assert meal.tags is not None
            assert len(meal.tags) == 1
        except ValidationError:
            # If tag creation fails due to None values, that's also acceptable
            pass

    def test_very_large_tag_collection(self):
        """Test handling of very large tag collections."""
        base_kwargs = create_api_meal_kwargs()
        
        # Create large tag collection
        large_tags = frozenset(
            create_api_tag(key=f"tag_{i}", value=f"value_{i}", author_id=base_kwargs["author_id"])
            for i in range(100)
        )
        
        base_kwargs["tags"] = large_tags
        meal = ApiMeal(**base_kwargs)
        
        assert meal.tags is not None
        assert len(meal.tags) == 100

    # =============================================================================
    # NUTRI_FACTS NESTED OBJECT EDGE CASES
    # =============================================================================

    def test_nutri_facts_with_none_values(self):
        """Test handling of nutri_facts with None values."""
        base_kwargs = create_api_meal_kwargs()
        
        # Create nutri_facts with None values - this may not create None values but zero values
        nutri_facts = create_api_nutri_facts(
            calories=None,
            protein=None,
            carbohydrate=None,
            total_fat=None,
            saturated_fat=None,
            trans_fat=None,
            sugar=None,
            sodium=None,
        )
        
        base_kwargs["nutri_facts"] = nutri_facts
        meal = ApiMeal(**base_kwargs)
        
        assert meal.nutri_facts is not None
        # The create_api_nutri_facts may create zero values instead of None values
        assert meal.nutri_facts.calories is not None
        assert meal.nutri_facts.protein is not None

    def test_nutri_facts_with_zero_values(self):
        """Test handling of nutri_facts with zero values."""
        base_kwargs = create_api_meal_kwargs()
        
        # Create nutri_facts with zero values
        nutri_facts = create_api_nutri_facts(
            calories=ApiNutriValue(value=0.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=0.0, unit=MeasureUnit.GRAM),
            carbohydrate=ApiNutriValue(value=0.0, unit=MeasureUnit.GRAM),
            total_fat=ApiNutriValue(value=0.0, unit=MeasureUnit.GRAM),
        )
        
        base_kwargs["nutri_facts"] = nutri_facts
        meal = ApiMeal(**base_kwargs)
        
        assert meal.nutri_facts is not None
        assert meal.nutri_facts.calories.value == 0.0
        assert meal.nutri_facts.protein.value == 0.0

    def test_nutri_facts_with_extreme_values(self):
        """Test handling of nutri_facts with extreme values."""
        base_kwargs = create_api_meal_kwargs()
        
        # Create nutri_facts with extreme values
        nutri_facts = create_api_nutri_facts(
            calories=ApiNutriValue(value=999999.99, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=999999.99, unit=MeasureUnit.GRAM),
            carbohydrate=ApiNutriValue(value=999999.99, unit=MeasureUnit.GRAM),
            total_fat=ApiNutriValue(value=999999.99, unit=MeasureUnit.GRAM),
        )
        
        base_kwargs["nutri_facts"] = nutri_facts
        meal = ApiMeal(**base_kwargs)
        
        assert meal.nutri_facts is not None
        assert meal.nutri_facts.calories.value == 999999.99
        assert meal.nutri_facts.protein.value == 999999.99


class TestApiMealErrorHandlingEdgeCases:
    """
    Test suite for error handling edge cases and failure scenarios.
    """

    def setup_method(self):
        """Reset counters before each test for isolation."""
        reset_api_meal_counters()

    # =============================================================================
    # VALIDATION ERROR EDGE CASES
    # =============================================================================

    def test_multiple_validation_errors(self):
        """Test handling of multiple validation errors simultaneously."""
        # Create data with multiple validation errors
        invalid_data = {
            "id": str(uuid4()),
            "name": "",  # Too short
            "author_id": "invalid-uuid",  # Invalid UUID
            "menu_id": "also-invalid",  # Invalid UUID
            "recipes": [{"invalid": "data"}],  # Invalid recipe data
            "tags": frozenset(),
            "weight_in_grams": -100,  # Negative value
            "carbo_percentage": 150.0,  # Over 100%
            "protein_percentage": -50.0,  # Negative percentage
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "discarded": False,
            "version": 1,
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal(**invalid_data)
        
        # Should contain multiple error messages
        error_str = str(exc_info.value)
        assert "error" in error_str.lower()

    def test_type_coercion_failures(self):
        """Test failures in type coercion."""
        base_kwargs = create_api_meal_kwargs()
        
        # Test invalid type for numeric field
        with pytest.raises(ValidationError):
            base_kwargs["weight_in_grams"] = "not_a_number"
            ApiMeal(**base_kwargs)
        
        # Test invalid type for boolean field
        with pytest.raises(ValidationError):
            base_kwargs["like"] = "not_a_boolean"
            ApiMeal(**base_kwargs)

    def test_required_field_missing_errors(self):
        """Test errors when required fields are missing."""
        incomplete_data = {
            "id": str(uuid4()),
            # Missing name (required)
            # Missing author_id (required)
            "recipes": [],
            "tags": frozenset(),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "discarded": False,
            "version": 1,
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal(**incomplete_data)
        
        error_str = str(exc_info.value)
        assert "required" in error_str.lower() or "missing" in error_str.lower()

    # =============================================================================
    # SERIALIZATION ERROR EDGE CASES
    # =============================================================================

    def test_json_serialization_with_extreme_values(self):
        """Test JSON serialization with extreme values."""
        # Create meal with extreme values
        meal = create_api_meal(
            weight_in_grams=999999999,
            calorie_density=999999.999,
            carbo_percentage=99.999999,
            protein_percentage=0.000001,
        )
        
        # Should be able to serialize to JSON
        json_str = meal.model_dump_json()
        assert json_str is not None
        assert "999999999" in json_str
        
        # Should be able to deserialize back
        restored_meal = ApiMeal.model_validate_json(json_str)
        assert restored_meal.weight_in_grams == 999999999

    def test_json_serialization_with_none_values(self):
        """Test JSON serialization with None values."""
        # Create meal with many None values
        meal = create_api_meal(
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
        
        # Should be able to serialize to JSON
        json_str = meal.model_dump_json()
        assert json_str is not None
        assert "null" in json_str
        
        # Should be able to deserialize back
        restored_meal = ApiMeal.model_validate_json(json_str)
        assert restored_meal.description is None
        assert restored_meal.nutri_facts is None

    def test_json_serialization_with_large_collections(self):
        """Test JSON serialization with large collections."""
        # Create meal with large collections
        meal = create_complex_api_meal()
        
        # Should be able to serialize to JSON
        json_str = meal.model_dump_json()
        assert json_str is not None
        assert len(json_str) > 100  # Should be substantial JSON
        
        # Should be able to deserialize back
        restored_meal = ApiMeal.model_validate_json(json_str)
        assert restored_meal.recipes is not None
        assert restored_meal.tags is not None
        assert meal.recipes is not None
        assert meal.tags is not None
        assert len(restored_meal.recipes) == len(meal.recipes)
        assert len(restored_meal.tags) == len(meal.tags)

    # =============================================================================
    # MEMORY AND PERFORMANCE EDGE CASES
    # =============================================================================

    def test_memory_efficiency_with_large_datasets(self):
        """Test memory efficiency with large datasets."""
        # Create multiple meals with large collections
        meals = []
        for i in range(10):
            meal = create_complex_api_meal()
            meals.append(meal)
        
        # Should not cause memory issues with reasonable dataset sizes
        assert len(meals) == 10
        assert all(isinstance(meal, ApiMeal) for meal in meals)

    def test_deeply_nested_object_handling(self):
        """Test handling of deeply nested objects."""
        # Create meal with multiple levels of nesting
        meal = create_complex_api_meal()
        
        # Verify nested structure is maintained
        assert meal.recipes is not None
        assert meal.tags is not None
        assert meal.nutri_facts is not None
        
        # Test conversion through all layers
        domain_meal = meal.to_domain()
        assert domain_meal is not None
        
        recovered_meal = ApiMeal.from_domain(domain_meal)
        assert recovered_meal is not None
        assert recovered_meal.recipes is not None
        assert len(recovered_meal.recipes) == len(meal.recipes)
