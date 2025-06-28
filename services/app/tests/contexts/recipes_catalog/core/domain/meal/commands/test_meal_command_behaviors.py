"""
Comprehensive behavior-focused tests for Meal domain commands.

Tests focus on command creation behaviors, field validation, defaults,
and domain rule compliance. No mocks - only actual command behaviors.
"""

import pytest
from uuid import UUID
import attrs

from src.contexts.recipes_catalog.core.domain.meal.commands.create_meal import CreateMeal
from src.contexts.recipes_catalog.core.domain.meal.commands.create_recipe import CreateRecipe
from src.contexts.recipes_catalog.core.domain.meal.commands.update_meal import UpdateMeal
from src.contexts.recipes_catalog.core.domain.meal.commands.delete_meal import DeleteMeal
from src.contexts.recipes_catalog.core.domain.meal.commands.rate_recipe import RateRecipe
from src.contexts.recipes_catalog.core.domain.meal.commands.copy_recipe import CopyRecipe
from src.contexts.recipes_catalog.core.domain.meal.commands.copy_meal import CopyMeal
from src.contexts.recipes_catalog.core.domain.meal.commands.delete_recipe import DeleteRecipe
from src.contexts.recipes_catalog.core.domain.meal.commands.update_recipe import UpdateRecipe

from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import Ingredient
from src.contexts.recipes_catalog.core.domain.meal.value_objects.rating import Rating
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.enums import Privacy, MeasureUnit


class TestCreateMealCommandBehaviors:
    """Test CreateMeal command instantiation and validation behaviors."""
    
    def test_create_meal_with_minimal_required_fields(self):
        """CreateMeal should accept minimal required fields and generate UUID."""
        command = CreateMeal(
            name="Breakfast Special",
            author_id="user-123", 
            menu_id="menu-456",
            recipes=[],
            tags=set()
        )
        
        assert command.name == "Breakfast Special"
        assert command.author_id == "user-123"
        assert command.menu_id == "menu-456"
        assert command.recipes == []
        assert command.tags == set()
        assert command.description is None
        assert command.notes is None
        assert command.image_url is None
        # Verify UUID generation
        assert isinstance(command.meal_id, str)
        UUID(command.meal_id)  # Should not raise exception
    
    def test_create_meal_with_all_optional_fields(self):
        """CreateMeal should accept all optional fields."""
        nutri_facts = NutriFacts(calories=250, protein=10.0, carbohydrate=30.0, total_fat=5.0)
        recipe = _Recipe(
            id="recipe-456",
            name="Test Recipe",
            ingredients=[],
            instructions="Mix well",
            author_id="user-123",
            meal_id="meal-123",
            nutri_facts=nutri_facts,
            description="Recipe description",
            notes="Recipe notes",
            image_url="https://example.com/recipe.jpg"
        )
        tag = Tag(key="diet", value="healthy", author_id="user-123", type="dietary")
        
        command = CreateMeal(
            name="Complete Meal",
            author_id="user-123",
            menu_id="menu-456", 
            recipes=[recipe],
            tags={tag},
            description="A complete meal description",
            notes="Some notes",
            image_url="https://example.com/image.jpg",
            meal_id="custom-meal-id"
        )
        
        assert command.description == "A complete meal description"
        assert command.notes == "Some notes"
        assert command.image_url == "https://example.com/image.jpg"
        assert command.meal_id == "custom-meal-id"
        assert len(command.recipes) == 1
        assert len(command.tags) == 1
    
    def test_create_meal_command_is_immutable(self):
        """CreateMeal should be immutable (frozen)."""
        command = CreateMeal(
            name="Test Meal",
            author_id="user-123",
            menu_id="menu-456",
            recipes=[],
            tags=set()
        )
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            command.name = "Modified Name" # type: ignore


class TestCreateRecipeCommandBehaviors:
    """Test CreateRecipe command instantiation and validation behaviors."""
    
    def test_create_recipe_with_minimal_required_fields(self):
        """CreateRecipe should accept minimal required fields with defaults."""
        ingredient = Ingredient(name="flour", quantity=100, unit=MeasureUnit.GRAM, position=0)
        
        command = CreateRecipe(
            name="Simple Recipe",
            ingredients=[ingredient],
            instructions="Mix and bake",
            author_id="user-123",
            meal_id="meal-456"
        )
        
        assert command.name == "Simple Recipe"
        assert len(command.ingredients) == 1
        assert command.instructions == "Mix and bake"
        assert command.author_id == "user-123"
        assert command.meal_id == "meal-456"
        # Test defaults
        assert command.description is None
        assert command.utensils is None
        assert command.total_time is None
        assert command.notes is None
        assert command.tags is None
        assert command.privacy == Privacy.PRIVATE
        assert command.nutri_facts is None
        assert command.weight_in_grams is None
        assert command.image_url is None
        # Verify UUID generation
        assert isinstance(command.recipe_id, str)
        UUID(command.recipe_id)  # Should not raise exception
    
    def test_create_recipe_with_all_optional_fields(self):
        """CreateRecipe should accept all optional fields."""
        ingredient = Ingredient(name="flour", quantity=100, unit=MeasureUnit.GRAM, position=0)
        tag = Tag(key="diet", value="vegan", author_id="user-123", type="dietary")
        nutri_facts = NutriFacts(calories=250, protein=10.0, carbohydrate=30.0, total_fat=5.0)
        
        command = CreateRecipe(
            name="Complete Recipe",
            ingredients=[ingredient],
            instructions="Detailed instructions",
            author_id="user-123",
            meal_id="meal-456",
            description="Recipe description",
            utensils="Oven, mixer",
            total_time=45,
            notes="Special notes",
            tags={tag},
            privacy=Privacy.PUBLIC,
            nutri_facts=nutri_facts,
            weight_in_grams=300,
            image_url="https://example.com/recipe.jpg",
            recipe_id="custom-recipe-id"
        )
        
        assert command.description == "Recipe description"
        assert command.utensils == "Oven, mixer"
        assert command.total_time == 45
        assert command.notes == "Special notes"
        assert command.tags is not None and len(command.tags) == 1
        assert command.privacy == Privacy.PUBLIC
        assert command.nutri_facts is not None and command.nutri_facts.calories.value == 250
        assert command.weight_in_grams == 300
        assert command.image_url == "https://example.com/recipe.jpg"
        assert command.recipe_id == "custom-recipe-id"
    
    def test_create_recipe_privacy_default_behavior(self):
        """CreateRecipe should default privacy to PRIVATE."""
        ingredient = Ingredient(name="flour", quantity=100, unit=MeasureUnit.GRAM, position=0)
        
        command = CreateRecipe(
            name="Private Recipe",
            ingredients=[ingredient],
            instructions="Secret instructions",
            author_id="user-123",
            meal_id="meal-456"
        )
        
        assert command.privacy == Privacy.PRIVATE
    
    def test_create_recipe_command_is_immutable(self):
        """CreateRecipe should be immutable (frozen)."""
        ingredient = Ingredient(name="flour", quantity=100, unit=MeasureUnit.GRAM, position=0)
        
        command = CreateRecipe(
            name="Test Recipe",
            ingredients=[ingredient],
            instructions="Test instructions",
            author_id="user-123",
            meal_id="meal-456"
        )
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            command.name = "Modified Recipe" # type: ignore


class TestUpdateMealCommandBehaviors:
    """Test UpdateMeal command behaviors."""
    
    def test_update_meal_with_updates_dict(self):
        """UpdateMeal should accept meal_id and updates dictionary."""
        updates = {
            "name": "Updated Meal Name",
            "description": "Updated description",
            "notes": "Updated notes"
        }
        
        command = UpdateMeal(
            meal_id="meal-123",
            updates=updates
        )
        
        assert command.meal_id == "meal-123"
        assert command.updates["name"] == "Updated Meal Name"
        assert command.updates["description"] == "Updated description"
        assert command.updates["notes"] == "Updated notes"
        assert len(command.updates) == 3
    
    def test_update_meal_with_empty_updates(self):
        """UpdateMeal should accept empty updates dictionary."""
        command = UpdateMeal(
            meal_id="meal-123",
            updates={}
        )
        
        assert command.meal_id == "meal-123"
        assert command.updates == {}
    
    def test_update_meal_command_is_immutable(self):
        """UpdateMeal should be immutable (frozen)."""
        command = UpdateMeal(
            meal_id="meal-123",
            updates={"name": "Test"}
        )
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            command.meal_id = "modified-meal-id" # type: ignore


class TestDeleteMealCommandBehaviors:
    """Test DeleteMeal command behaviors."""
    
    def test_delete_meal_with_meal_id(self):
        """DeleteMeal should accept meal_id."""
        command = DeleteMeal(meal_id="meal-123")
        
        assert command.meal_id == "meal-123"
    
    def test_delete_meal_command_is_immutable(self):
        """DeleteMeal should be immutable (frozen)."""
        command = DeleteMeal(meal_id="meal-123")
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            command.meal_id = "modified-meal-id" # type: ignore


class TestRateRecipeCommandBehaviors:
    """Test RateRecipe command behaviors."""
    
    def test_rate_recipe_with_rating(self):
        """RateRecipe should accept Rating value object."""
        rating = Rating(user_id="user-123", recipe_id="recipe-456", taste=5, convenience=4)
        
        command = RateRecipe(rating=rating)
        
        assert command.rating.taste == 5
        assert command.rating.convenience == 4
        assert command.rating.user_id == "user-123"
        assert command.rating.recipe_id == "recipe-456"
    
    def test_rate_recipe_command_is_immutable(self):
        """RateRecipe should be immutable (frozen)."""
        rating = Rating(user_id="user-123", recipe_id="recipe-456", taste=4, convenience=3)
        command = RateRecipe(rating=rating)
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            command.rating = Rating(user_id="user-456", recipe_id="recipe-789", taste=3, convenience=2) # type: ignore


class TestCopyRecipeCommandBehaviors:
    """Test CopyRecipe command behaviors."""
    
    def test_copy_recipe_with_required_fields(self):
        """CopyRecipe should accept user_id, recipe_id, and meal_id."""
        command = CopyRecipe(
            user_id="user-123",
            recipe_id="recipe-456", 
            meal_id="meal-789"
        )
        
        assert command.user_id == "user-123"
        assert command.recipe_id == "recipe-456"
        assert command.meal_id == "meal-789"
    
    def test_copy_recipe_command_is_immutable(self):
        """CopyRecipe should be immutable (frozen)."""
        command = CopyRecipe(
            user_id="user-123",
            recipe_id="recipe-456",
            meal_id="meal-789"
        )
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            command.user_id = "modified-user-id" # type: ignore


class TestCopyMealCommandBehaviors:
    """Test CopyMeal command behaviors."""
    
    def test_copy_meal_creation(self):
        """CopyMeal should be creatable (testing import and basic functionality)."""
        # This ensures the command can be imported and instantiated
        command = CopyMeal(
            id_of_user_coping_meal="user-123",
            meal_id="meal-456"
        )
        
        assert command.id_of_user_coping_meal == "user-123"
        assert command.meal_id == "meal-456"
        assert command.id_of_target_menu is None  # Default value
    
    def test_copy_meal_with_target_menu(self):
        """CopyMeal should accept optional target menu."""
        command = CopyMeal(
            id_of_user_coping_meal="user-123",
            meal_id="meal-456",
            id_of_target_menu="menu-789"
        )
        
        assert command.id_of_user_coping_meal == "user-123"
        assert command.meal_id == "meal-456"
        assert command.id_of_target_menu == "menu-789"
    
    def test_copy_meal_command_is_immutable(self):
        """CopyMeal should be immutable (frozen)."""
        command = CopyMeal(
            id_of_user_coping_meal="user-123", 
            meal_id="meal-456"
        )
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            command.id_of_user_coping_meal = "modified-user-id" # type: ignore


class TestDeleteRecipeCommandBehaviors:
    """Test DeleteRecipe command behaviors."""
    
    def test_delete_recipe_creation(self):
        """DeleteRecipe should accept recipe_id."""
        command = DeleteRecipe(recipe_id="recipe-123")
        
        assert command.recipe_id == "recipe-123"
    
    def test_delete_recipe_command_is_immutable(self):
        """DeleteRecipe should be immutable (frozen)."""
        command = DeleteRecipe(recipe_id="recipe-123")
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            command.recipe_id = "modified-recipe-id" # type: ignore


class TestUpdateRecipeCommandBehaviors:
    """Test UpdateRecipe command behaviors."""
    
    def test_update_recipe_creation(self):
        """UpdateRecipe should accept recipe_id and updates."""
        updates = {
            "name": "Updated Recipe Name",
            "instructions": "Updated instructions"
        }
        
        command = UpdateRecipe(
            recipe_id="recipe-123",
            updates=updates
        )
        
        assert command.recipe_id == "recipe-123"
        assert command.updates["name"] == "Updated Recipe Name"
        assert command.updates["instructions"] == "Updated instructions"
    
    def test_update_recipe_with_empty_updates(self):
        """UpdateRecipe should accept empty updates dictionary."""
        command = UpdateRecipe(
            recipe_id="recipe-123",
            updates={}
        )
        
        assert command.recipe_id == "recipe-123"
        assert command.updates == {}
    
    def test_update_recipe_command_is_immutable(self):
        """UpdateRecipe should be immutable (frozen)."""
        command = UpdateRecipe(
            recipe_id="recipe-123",
            updates={"name": "Test"}
        )
        
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            command.recipe_id = "modified-recipe-id" # type: ignore 


class TestCommandFieldValidationBehaviors:
    """Test command field validation and edge cases."""
    
    def test_create_meal_requires_essential_fields(self):
        """CreateMeal should require name, author_id, menu_id, recipes, and tags."""
        # Test missing required fields raise appropriate errors
        with pytest.raises(TypeError):  # Missing required arguments
            CreateMeal() # type: ignore
        
        with pytest.raises(TypeError):  # Missing some required arguments  
            CreateMeal(name="Test Meal") # type: ignore
    
    def test_create_recipe_requires_essential_fields(self):
        """CreateRecipe should require name, ingredients, instructions, author_id, and meal_id."""
        with pytest.raises(TypeError):  # Missing required arguments
            CreateRecipe() # type: ignore
        
        with pytest.raises(TypeError):  # Missing some required arguments
            CreateRecipe(name="Test Recipe") # type: ignore
    
    def test_command_uuid_generation_uniqueness(self):
        """Command UUID generation should produce unique IDs."""
        ingredient = Ingredient(name="flour", quantity=100, unit=MeasureUnit.GRAM, position=0)
        
        command1 = CreateRecipe(
            name="Recipe 1",
            ingredients=[ingredient],
            instructions="Instructions 1",
            author_id="user-123",
            meal_id="meal-456"
        )
        
        command2 = CreateRecipe(
            name="Recipe 2", 
            ingredients=[ingredient],
            instructions="Instructions 2",
            author_id="user-123",
            meal_id="meal-456"
        )
        
        # UUIDs should be different
        assert command1.recipe_id != command2.recipe_id
        
        # Both should be valid UUIDs
        UUID(command1.recipe_id)
        UUID(command2.recipe_id)
    
    def test_commands_with_complex_data_structures(self):
        """Commands should handle complex nested data structures correctly."""
        # Create complex recipe with multiple ingredients and tags
        ingredients = [
            Ingredient(name="flour", quantity=200, unit=MeasureUnit.GRAM, position=0),
            Ingredient(name="sugar", quantity=100, unit=MeasureUnit.GRAM, position=1),
            Ingredient(name="eggs", quantity=2, unit=MeasureUnit.UNIT, position=2)
        ]
        
        tags = {
            Tag(key="type", value="dessert", author_id="user-123", type="category"),
            Tag(key="timing", value="quick", author_id="user-123", type="preparation")
        }
        
        nutri_facts = NutriFacts(calories=450, protein=12.0, carbohydrate=65.0, total_fat=8.0)
        
        command = CreateRecipe(
            name="Complex Recipe",
            ingredients=ingredients,
            instructions="Complex multi-step instructions",
            author_id="user-123",
            meal_id="meal-456",
            tags=tags,
            nutri_facts=nutri_facts,
            total_time=120
        )
        
        assert len(command.ingredients) == 3
        assert command.tags is not None and len(command.tags) == 2
        assert command.nutri_facts is not None and command.nutri_facts.calories.value == 450
        assert command.total_time == 120
        
        # Verify ingredient order is preserved
        assert command.ingredients[0].name == "flour"
        assert command.ingredients[1].name == "sugar"
        assert command.ingredients[2].name == "eggs" 