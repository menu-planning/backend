"""
Domain Rule Behavior Tests for Recipe Entity

Tests focus on domain business rules and their enforcement behaviors,
not implementation details. These tests ensure domain integrity and
proper business rule validation.
"""

import pytest
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import Ingredient
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.domain.enums import Privacy, MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.exceptions import BusinessRuleValidationException


class TestRecipeBusinessRuleValidation:
    """Test domain business rule enforcement behaviors."""
    
    def test_recipe_enforces_ingredient_position_consecutiveness(self):
        """Domain should prevent ingredients with non-consecutive positions."""
        # Arrange: Create ingredients with gaps in positions (violates domain rule)
        invalid_ingredients = [
            Ingredient(
                name="Flour",
                position=0,  # Valid
                quantity=2.0,
                unit=MeasureUnit.CUP
            ),
            Ingredient(
                name="Sugar", 
                position=2,  # Invalid - gap! Should be 1
                quantity=1.0,
                unit=MeasureUnit.CUP
            )
        ]
        
        # Act & Assert: Domain should reject invalid ingredient positions
        with pytest.raises(BusinessRuleValidationException):
            _Recipe.create_recipe(
                name="Test Recipe",
                ingredients=invalid_ingredients,
                instructions="Mix ingredients",
                author_id="user123",
                meal_id="meal123",
                nutri_facts=NutriFacts(calories=100)
            )
    
    def test_recipe_enforces_ingredient_positions_start_from_zero(self):
        """Domain should enforce ingredients positions start from 0."""
        # Arrange: Create ingredients starting from position 1 (violates domain rule)
        invalid_ingredients = [
            Ingredient(
                name="Flour",
                position=1,  # Invalid - should start from 0
                quantity=2.0,
                unit=MeasureUnit.CUP
            ),
            Ingredient(
                name="Sugar",
                position=2,  # Invalid - should be 1 if first is 0
                quantity=1.0,
                unit=MeasureUnit.CUP
            )
        ]
        
        # Act & Assert: Domain should reject positions not starting from 0
        with pytest.raises(BusinessRuleValidationException):
            _Recipe.create_recipe(
                name="Test Recipe",
                ingredients=invalid_ingredients,
                instructions="Mix ingredients",
                author_id="user123",
                meal_id="meal123",
                nutri_facts=NutriFacts(calories=100)
            )
    
    def test_recipe_accepts_valid_consecutive_ingredient_positions(self):
        """Domain should accept properly positioned ingredients."""
        # Arrange: Create ingredients with valid consecutive positions
        valid_ingredients = [
            Ingredient(
                name="Flour",
                position=0,  # Valid start
                quantity=2.0,
                unit=MeasureUnit.CUP
            ),
            Ingredient(
                name="Sugar",
                position=1,  # Valid consecutive
                quantity=1.0,
                unit=MeasureUnit.CUP
            ),
            Ingredient(
                name="Salt",
                position=2,  # Valid consecutive
                quantity=0.5,
                unit=MeasureUnit.TEASPOON
            )
        ]
        
        # Act: Create recipe with valid ingredients
        recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=valid_ingredients,
            instructions="Mix ingredients",
            author_id="user123",
            meal_id="meal123",
            nutri_facts=NutriFacts(calories=100)
        )
        
        # Assert: Recipe should be created successfully
        assert recipe.name == "Test Recipe"
        assert len(recipe.ingredients) == 3
        # Verify domain maintained ingredient order
        assert recipe.ingredients[0].position == 0
        assert recipe.ingredients[1].position == 1
        assert recipe.ingredients[2].position == 2
    
    def test_recipe_enforces_tag_author_matches_recipe_author(self):
        """Domain should enforce tag author_id matches recipe author_id."""
        # Arrange: Create tag with different author_id than recipe
        recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Mix ingredients",
            author_id="recipe_author_123",
            meal_id="meal123",
            nutri_facts=NutriFacts(calories=100)
        )
        
        invalid_tag = Tag(
            key="diet",
            value="vegetarian",
            author_id="different_author_456",  # Different from recipe author!
            type="diet"
        )
        
        # Act & Assert: Domain should reject tags with mismatched author_id
        with pytest.raises(BusinessRuleValidationException):
            recipe.update_properties(tags={invalid_tag})
    
    def test_recipe_accepts_tags_with_matching_author_id(self):
        """Domain should accept tags when author_id matches recipe author."""
        # Arrange: Create recipe and tag with matching author_id
        recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Mix ingredients",
            author_id="author_123",
            meal_id="meal123",
            nutri_facts=NutriFacts(calories=100)
        )
        
        valid_tag = Tag(
            key="diet",
            value="vegetarian",
            author_id="author_123",  # Matches recipe author
            type="diet"
        )
        
        # Act: Update recipe with valid tag
        recipe.update_properties(tags={valid_tag})
        
        # Assert: Domain should accept the tag
        assert len(recipe.tags) == 1
        assert list(recipe.tags)[0].value == "vegetarian"
        assert list(recipe.tags)[0].author_id == "author_123"


class TestRecipeDiscardedBehavior:
    """Test domain behavior for discarded (deleted) recipes."""
    
    def test_discarded_recipe_prevents_property_access(self):
        """Domain should prevent accessing properties of discarded recipes."""
        # Arrange: Create and discard a recipe
        recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Mix ingredients",
            author_id="author_123",
            meal_id="meal123",
            nutri_facts=NutriFacts(calories=100)
        )
        recipe.delete()  # Mark as discarded
        
        # Act & Assert: Domain should prevent access to discarded entity
        with pytest.raises(Exception):  # Should raise discarded entity exception
            _ = recipe.name
    
    def test_discarded_recipe_prevents_mutation_operations(self):
        """Domain should prevent mutations on discarded recipes."""
        # Arrange: Create and discard a recipe
        recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Mix ingredients",
            author_id="author_123",
            meal_id="meal123",
            nutri_facts=NutriFacts(calories=100)
        )
        recipe.delete()  # Mark as discarded
        
        # Act & Assert: Domain should prevent rating discarded recipes
        with pytest.raises(Exception):  # Should raise discarded entity exception
            recipe.rate(user_id="user123", taste=5, convenience=4)


class TestRecipeProtectedSetterBehavior:
    """Test aggregate boundary protection through protected setters."""
    
    def test_recipe_handles_none_ingredients_gracefully(self):
        """Domain should handle None ingredients by converting to empty list."""
        # Arrange: Create recipe
        recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Mix ingredients", 
            author_id="author_123",
            meal_id="meal123",
            nutri_facts=NutriFacts(calories=100)
        )
        
        # Act: Update with None ingredients (tests protected setter behavior)
        recipe.update_properties(ingredients=None)
        
        # Assert: Domain should convert None to empty list
        assert recipe.ingredients == []
    
    def test_recipe_handles_none_tags_gracefully(self):
        """Domain should handle None tags by converting to empty set."""
        # Arrange: Create recipe
        recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Mix ingredients",
            author_id="author_123", 
            meal_id="meal123",
            nutri_facts=NutriFacts(calories=100)
        )
        
        # Act: Update with None tags (tests protected setter behavior)
        recipe.update_properties(tags=None)
        
        # Assert: Domain should convert None to empty set
        assert recipe.tags == set()
    
    def test_recipe_version_increments_on_property_changes(self):
        """Domain should track changes through version increments."""
        # Arrange: Create recipe
        recipe = _Recipe.create_recipe(
            name="Original Name",
            ingredients=[],
            instructions="Mix ingredients",
            author_id="author_123",
            meal_id="meal123", 
            nutri_facts=NutriFacts(calories=100)
        )
        initial_version = recipe.version
        
        # Act: Update recipe property
        recipe.update_properties(name="Updated Name")
        
        # Assert: Domain should increment version
        assert recipe.version > initial_version
        assert recipe.name == "Updated Name"
    
    def test_recipe_version_increments_even_when_setting_same_value(self):
        """Domain behavior: Recipe increments version on update calls even with identical values."""
        # Arrange: Create recipe
        recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Mix ingredients",
            author_id="author_123",
            meal_id="meal123",
            nutri_facts=NutriFacts(calories=100)
        )
        initial_version = recipe.version
        
        # Act: Update with same value (tests actual domain behavior)
        recipe.update_properties(name="Test Recipe")  # Same name
        
        # Assert: Domain increments version even for identical values (actual behavior)
        assert recipe.version > initial_version 