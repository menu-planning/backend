"""
Comprehensive Domain Rules Validation Tests

Tests focus on business rule enforcement behaviors across all domain entities,
ensuring domain integrity and proper validation of business constraints.
"""


from src.contexts.recipes_catalog.core.domain.rules import (
    OnlyAdminUserCanCreatePublicTag,
    PositionsMustBeConsecutiveStartingFromZero,
    RecipeMustHaveCorrectMealIdAndAuthorId,
    AuthorIdOnTagMustMachRootAggregateAuthor,
    MealMustAlreadyExistInTheMenu
)
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.recipes_catalog.core.domain.client.entities.menu import Menu
from src.contexts.recipes_catalog.core.domain.client.value_objects.menu_meal import MenuMeal
from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import Ingredient
from src.contexts.recipes_catalog.core.domain.shared.value_objects.user import User
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.domain.enums import Privacy, MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.recipes_catalog.core.domain.shared.value_objects.role import Role


class TestAdminTagCreationRule:
    """Test domain rule for admin-only public tag creation."""
    
    def test_admin_can_create_public_tag(self):
        """Domain should allow admin users to create public tags."""
        # Arrange: Create admin user using proper Role factory
        admin_role = Role.administrator()
        admin_user = User(id="admin_123", roles=frozenset({admin_role}))
        rule = OnlyAdminUserCanCreatePublicTag(user=admin_user, privacy=Privacy.PUBLIC)
        
        # Act & Assert: Domain should allow admin to create public tags
        assert not rule.is_broken()
        assert "Only administrators can create public tags" in rule.get_message()
    
    def test_non_admin_cannot_create_public_tag(self):
        """Domain should prevent non-admin users from creating public tags."""
        # Arrange: Create regular user using proper Role factory
        user_role = Role.user()
        regular_user = User(id="user_123", roles=frozenset({user_role}))
        rule = OnlyAdminUserCanCreatePublicTag(user=regular_user, privacy=Privacy.PUBLIC)
        
        # Act & Assert: Domain should prevent non-admin from creating public tags
        assert rule.is_broken()
        assert "Only administrators can create public tags" in rule.get_message()
    
    def test_any_user_can_create_private_tag(self):
        """Domain should allow any user to create private tags."""
        # Arrange: Create regular user with private privacy using proper Role factory
        user_role = Role.user()
        regular_user = User(id="user_123", roles=frozenset({user_role}))
        rule = OnlyAdminUserCanCreatePublicTag(user=regular_user, privacy=Privacy.PRIVATE)
        
        # Act & Assert: Domain should allow any user to create private tags
        assert not rule.is_broken()


class TestIngredientPositionRule:
    """Test domain rule for consecutive ingredient positions."""
    
    def test_valid_consecutive_positions_pass_validation(self):
        """Domain should accept ingredients with valid consecutive positions."""
        # Arrange: Create ingredients with valid positions
        ingredients = [
            Ingredient(name="Flour", position=0, quantity=1.0, unit=MeasureUnit.CUP),
            Ingredient(name="Sugar", position=1, quantity=0.5, unit=MeasureUnit.CUP),
            Ingredient(name="Salt", position=2, quantity=0.25, unit=MeasureUnit.TEASPOON)
        ]
        rule = PositionsMustBeConsecutiveStartingFromZero(ingredients=ingredients)
        
        # Act & Assert: Domain should accept valid positions
        assert not rule.is_broken()
        assert "Positions must be consecutive and start from 0" in rule.get_message()
    
    def test_gap_in_positions_fails_validation(self):
        """Domain should reject ingredients with gaps in positions."""
        # Arrange: Create ingredients with position gap
        ingredients = [
            Ingredient(name="Flour", position=0, quantity=1.0, unit=MeasureUnit.CUP),
            Ingredient(name="Sugar", position=2, quantity=0.5, unit=MeasureUnit.CUP)  # Gap! Missing position 1
        ]
        rule = PositionsMustBeConsecutiveStartingFromZero(ingredients=ingredients)
        
        # Act & Assert: Domain should reject gaps in positions
        assert rule.is_broken()
        assert "Positions must be consecutive and start from 0" in rule.get_message()
    
    def test_positions_not_starting_from_zero_fail_validation(self):
        """Domain should reject ingredients not starting from position 0."""
        # Arrange: Create ingredients starting from position 1
        ingredients = [
            Ingredient(name="Flour", position=1, quantity=1.0, unit=MeasureUnit.CUP),
            Ingredient(name="Sugar", position=2, quantity=0.5, unit=MeasureUnit.CUP)
        ]
        rule = PositionsMustBeConsecutiveStartingFromZero(ingredients=ingredients)
        
        # Act & Assert: Domain should reject positions not starting from 0
        assert rule.is_broken()
    
    def test_empty_ingredients_pass_validation(self):
        """Domain should accept empty ingredients list."""
        # Arrange: Empty ingredients list
        ingredients = []
        rule = PositionsMustBeConsecutiveStartingFromZero(ingredients=ingredients)
        
        # Act & Assert: Domain should accept empty list
        assert not rule.is_broken()


class TestRecipeMealIdRule:
    """Test domain rule for recipe-meal ID matching."""
    
    def test_matching_meal_and_author_ids_pass_validation(self):
        """Domain should accept recipes with matching meal_id and author_id."""
        # Arrange: Create meal and recipe with matching IDs
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123",
            menu_id="menu_123"
        )
        
        recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Mix",
            author_id="author_123",  # Matches meal
            meal_id="meal_123",     # Matches meal
            nutri_facts=NutriFacts(calories=100)
        )
        
        rule = RecipeMustHaveCorrectMealIdAndAuthorId(meal=meal, recipe=recipe)
        
        # Act & Assert: Domain should accept matching IDs
        assert not rule.is_broken()
        assert "Recipe must have the correct meal id and author id" in rule.get_message()
    
    def test_mismatched_meal_id_fails_validation(self):
        """Domain should reject recipes with wrong meal_id."""
        # Arrange: Create meal and recipe with mismatched meal_id
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123",
            menu_id="menu_123"
        )
        
        recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Mix",
            author_id="author_123",
            meal_id="wrong_meal_456",  # Wrong meal_id!
            nutri_facts=NutriFacts(calories=100)
        )
        
        rule = RecipeMustHaveCorrectMealIdAndAuthorId(meal=meal, recipe=recipe)
        
        # Act & Assert: Domain should reject wrong meal_id
        assert rule.is_broken()
    
    def test_mismatched_author_id_fails_validation(self):
        """Domain should reject recipes with wrong author_id."""
        # Arrange: Create meal and recipe with mismatched author_id
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123",
            menu_id="menu_123"
        )
        
        recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Mix",
            author_id="wrong_author_456",  # Wrong author_id!
            meal_id="meal_123",
            nutri_facts=NutriFacts(calories=100)
        )
        
        rule = RecipeMustHaveCorrectMealIdAndAuthorId(meal=meal, recipe=recipe)
        
        # Act & Assert: Domain should reject wrong author_id
        assert rule.is_broken()


class TestTagAuthorRule:
    """Test domain rule for tag author matching."""
    
    def test_matching_tag_author_passes_validation(self):
        """Domain should accept tags with matching author_id."""
        # Arrange: Create recipe and tag with matching author_id
        recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Mix",
            author_id="author_123",
            meal_id="meal_123",
            nutri_facts=NutriFacts(calories=100)
        )
        
        tag = Tag(
            key="diet",
            value="vegetarian",
            author_id="author_123",  # Matches recipe
            type="diet"
        )
        
        rule = AuthorIdOnTagMustMachRootAggregateAuthor(tag=tag, root_aggregate=recipe)
        
        # Act & Assert: Domain should accept matching author_id
        assert not rule.is_broken()
        assert "Author id on tag must match root aggregate author" in rule.get_message()
    
    def test_mismatched_tag_author_fails_validation(self):
        """Domain should reject tags with wrong author_id."""
        # Arrange: Create recipe and tag with mismatched author_id
        recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Mix",
            author_id="recipe_author_123",
            meal_id="meal_123",
            nutri_facts=NutriFacts(calories=100)
        )
        
        tag = Tag(
            key="diet",
            value="vegetarian",
            author_id="different_author_456",  # Wrong author_id!
            type="diet"
        )
        
        rule = AuthorIdOnTagMustMachRootAggregateAuthor(tag=tag, root_aggregate=recipe)
        
        # Act & Assert: Domain should reject wrong author_id
        assert rule.is_broken()


class TestMenuMealExistenceRule:
    """Test domain rule for meal existence in menu."""
    
    def test_existing_meal_passes_validation(self):
        """Domain should accept updates to existing meals in menu."""
        # Arrange: Create menu with meal
        menu = Menu(
            id="menu_123",
            author_id="author_123",
            client_id="client_123"
        )
        
        # Add a meal to the menu first
        meal_to_add = MenuMeal(
            meal_id="meal_123",
            meal_name="Test Meal",
            week=1,
            weekday="Seg",
            meal_type="almoço"
        )
        menu.add_meal(meal_to_add)
        
        # Create update for the same meal position
        meal_update = MenuMeal(
            meal_id="meal_123",  # Same meal_id
            meal_name="Updated Meal",
            week=1,
            weekday="Seg",
            meal_type="almoço"
        )
        
        rule = MealMustAlreadyExistInTheMenu(menu_meal=meal_update, menu=menu)
        
        # Act & Assert: Domain should accept updates to existing meals
        assert not rule.is_broken()
        assert "Meal must already exist in the menu" in rule.get_message()
    
    def test_nonexistent_meal_fails_validation(self):
        """Domain should reject updates to non-existent meals."""
        # Arrange: Create empty menu
        menu = Menu(
            id="menu_123",
            author_id="author_123",
            client_id="client_123"
        )
        
        # Try to update a meal that doesn't exist
        nonexistent_meal = MenuMeal(
            meal_id="nonexistent_meal_456",
            meal_name="Nonexistent Meal",
            week=1,
            weekday="Seg",
            meal_type="almoço"
        )
        
        rule = MealMustAlreadyExistInTheMenu(menu_meal=nonexistent_meal, menu=menu)
        
        # Act & Assert: Domain should reject updates to non-existent meals
        assert rule.is_broken()
    
    def test_wrong_meal_id_at_position_fails_validation(self):
        """Domain should reject updates with wrong meal_id at position."""
        # Arrange: Create menu with meal
        menu = Menu(
            id="menu_123",
            author_id="author_123",
            client_id="client_123"
        )
        
        # Add meal with meal_id "meal_123"
        existing_meal = MenuMeal(
            meal_id="meal_123",
            meal_name="Existing Meal",
            week=1,
            weekday="Seg",
            meal_type="almoço"
        )
        menu.add_meal(existing_meal)
        
        # Try to update with different meal_id at same position
        wrong_meal = MenuMeal(
            meal_id="different_meal_456",  # Wrong meal_id!
            meal_name="Wrong Meal",
            week=1,
            weekday="Seg",
            meal_type="almoço"
        )
        
        rule = MealMustAlreadyExistInTheMenu(menu_meal=wrong_meal, menu=menu)
        
        # Act & Assert: Domain should reject wrong meal_id at position
        assert rule.is_broken() 