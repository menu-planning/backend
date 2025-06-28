"""
Characterisation tests for _Recipe entity.

These tests document current behavior before refactoring, including:
- Heavy computed properties (average_taste_rating, average_convenience_rating, macro_division)
- Current @lru_cache behavior and shared cache bugs
- Direct mutation restrictions (should be enforced by root aggregate)
- Rating computation behavior

Tests marked with xfail document known bugs to be fixed during refactoring.
"""

import pytest


from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.recipe.recipe_domain_factories import create_rating, create_recipe


class TestRecipeCharacterisation:
    """Characterisation tests documenting current _Recipe behavior."""
    
    def test_recipe_creation_basic(self):
        """Document basic recipe creation."""
        recipe = create_recipe(name="Test Recipe")
        assert recipe.name == "Test Recipe"
        assert recipe.ratings == []
        assert recipe.average_taste_rating is None  # No ratings = no average
        assert recipe.average_convenience_rating is None
        
    def test_recipe_with_ratings_average_computation(self):
        """Document current rating average computation."""
        ratings = []
        for i in range(5):
            rating = create_rating(
                taste=i + 1,  # 1, 2, 3, 4, 5
                convenience=(i + 1) * 2 if (i + 1) * 2 <= 5 else 5  # 2, 4, 5, 5, 5
            )
            ratings.append(rating)
            
        recipe = create_recipe(ratings=ratings)
        
        # Document expected averages
        taste_avg = recipe.average_taste_rating
        convenience_avg = recipe.average_convenience_rating
        
        assert taste_avg is not None
        assert convenience_avg is not None
        assert abs(taste_avg - 3.0) < 0.01  # (1+2+3+4+5)/5 = 3.0
        assert abs(convenience_avg - 4.2) < 0.01  # (2+4+5+5+5)/5 = 4.2
        
    def test_recipe_macro_division_computation(self):
        """Document current recipe macro_division computation."""
        nutri_facts = NutriFacts(
            calories=400.0,
            carbohydrate=60.0,  # Should be 60% of macros
            protein=30.0,       # Should be 30% of macros  
            total_fat=10.0,     # Should be 10% of macros
            saturated_fat=5.0,
            trans_fat=0.0,
            dietary_fiber=5.0,
            sodium=500.0,
            sugar=8.0
        )
        recipe = create_recipe(nutri_facts=nutri_facts)
        
        result = recipe.macro_division
        assert result is not None
        assert abs(result.carbohydrate - 60.0) < 0.01
        assert abs(result.protein - 30.0) < 0.01  
        assert abs(result.fat - 10.0) < 0.01
        
    def test_recipe_calorie_density_computation(self):
        """Document current calorie density computation."""
        nutri_facts = NutriFacts(
            calories=200.0,
            carbohydrate=30.0,
            protein=20.0,
            total_fat=10.0,
            saturated_fat=3.0,
            trans_fat=0.0,
            dietary_fiber=5.0,
            sodium=300.0,
            sugar=6.0
        )
        recipe = create_recipe(nutri_facts=nutri_facts, weight_in_grams=100)
        
        density = recipe.calorie_density
        assert density is not None
        assert abs(density - 200.0) < 0.01  # (200 calories / 100g) * 100 = 200
        
    @pytest.mark.xfail(reason="Shared @lru_cache bug - different recipes may share cache")
    def test_recipe_cache_isolation_bug(self):
        """Document known shared cache bug between different recipe instances."""
        # Create two recipes with different ratings
        ratings1 = [create_rating(taste=1, convenience=1)]
        ratings2 = [create_rating(taste=5, convenience=5)]
        
        recipe1 = create_recipe(ratings=ratings1)
        recipe2 = create_recipe(ratings=ratings2)
        
        # Access properties to populate cache
        avg1_first = recipe1.average_taste_rating
        avg2 = recipe2.average_taste_rating
        avg1_second = recipe1.average_taste_rating
        
        # With proper instance-level caching, these should be different
        # With shared @lru_cache, they might be incorrectly shared
        assert avg1_first == 1.0
        assert avg2 == 5.0
        assert avg1_second == 1.0  # This may fail due to shared cache
        
    def test_recipe_update_properties_behavior(self):
        """Document current update_properties behavior."""
        recipe = create_recipe(name="Original Name", description="Original Description")
        
        # Document current behavior
        original_version = recipe.version
        recipe.update_properties(name="New Name", description="New Description")
        
        assert recipe.name == "New Name"
        assert recipe.description == "New Description"
        assert recipe.version == original_version + 1
        
    def test_recipe_rating_management(self):
        """Document current rating management behavior."""
        recipe = create_recipe()
        
        # Add rating
        original_version = recipe.version
        recipe.rate(user_id="user1", taste=4, convenience=3, comment="Good recipe")
        
        assert recipe.ratings is not None
        assert len(recipe.ratings) == 1
        assert recipe.ratings[0].taste == 4
        assert recipe.ratings[0].convenience == 3
        assert recipe.version == original_version + 1
        
        # Update existing rating
        current_version = recipe.version
        recipe.rate(user_id="user1", taste=5, convenience=4, comment="Great recipe")
        
        assert recipe.ratings is not None
        assert len(recipe.ratings) == 1  # Should replace, not add
        assert recipe.ratings[0].taste == 5
        assert recipe.ratings[0].convenience == 4
        assert recipe.version == current_version + 1
        
    def test_recipe_rating_deletion(self):
        """Document current rating deletion behavior."""
        rating = create_rating(user_id="user1", taste=3, convenience=2)
        recipe = create_recipe(ratings=[rating])
        
        original_version = recipe.version
        recipe.delete_rate(user_id="user1")
        
        assert recipe.ratings is not None
        assert len(recipe.ratings) == 0
        assert recipe.version == original_version + 1
        
    def test_recipe_nutrition_facts_behavior(self):
        """Test recipe nutrition facts can be updated and accessed correctly."""
        # Create a recipe with initial nutrition facts
        initial_nutri = NutriFacts(
            calories=500.0,
            protein=25.0,
            carbohydrate=50.0,
            total_fat=15.0,
        )
        
        # Create meal first to manage recipe properly
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="user123",
            meal_id="meal123",
            menu_id="menu123"
        )
        
        recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Test instructions",
            author_id="user123",
            meal_id=meal.id,
            nutri_facts=initial_nutri,
        )
        
        # Add recipe to meal
        meal._recipes = [recipe]
        
        # Test initial state
        assert recipe.nutri_facts == initial_nutri
        assert recipe.nutri_facts.calories.value == 500.0 # type: ignore
        
        # Update nutrition facts through proper aggregate boundary (via Meal)
        new_nutri = NutriFacts(
            calories=600.0,
            protein=30.0,
            carbohydrate=60.0,
            total_fat=20.0,
        )
        
        # Use Meal's update_recipes method to properly update recipe nutrition
        meal.update_recipes({recipe.id: {"nutri_facts": new_nutri}})
        
        # Verify the update worked
        assert recipe.nutri_facts == new_nutri
        assert recipe.nutri_facts.calories.value == 600.0 # type: ignore
        assert recipe.nutri_facts.protein.value == 30.0 # type: ignore


class TestRecipeCacheInvalidation:
    """Document current recipe cache invalidation behavior."""
    
    @pytest.mark.xfail(reason="Cache invalidation bug - @lru_cache not invalidated on ratings change")
    def test_cache_invalidation_on_ratings_change(self):
        """Document how rating cache behaves when ratings are changed."""
        rating = create_rating(taste=3, convenience=2)
        recipe = create_recipe(ratings=[rating])
        
        # Get initial cached average
        initial_avg = recipe.average_taste_rating
        assert initial_avg == 3.0
        
        # Add new rating (should invalidate cache)
        recipe.rate(user_id="user2", taste=5, convenience=4)
        
        # Check if cache was invalidated
        updated_avg = recipe.average_taste_rating
        # With proper cache invalidation, average should change
        assert updated_avg is not None
        assert abs(updated_avg - 4.0) < 0.01  # (3+5)/2 = 4.0
        
    @pytest.mark.xfail(reason="Cache invalidation bug - @lru_cache not invalidated on nutrition change")
    def test_cache_invalidation_on_nutrition_change(self):
        """Document how macro_division cache behaves when nutrition changes."""
        nutri_facts = NutriFacts(
            calories=300.0,
            carbohydrate=30.0,  # 50% of macros
            protein=20.0,       # 33.33% of macros
            total_fat=10.0,     # 16.67% of macros
            saturated_fat=3.0,
            trans_fat=0.0,
            dietary_fiber=5.0,
            sodium=400.0,
            sugar=7.0
        )
        recipe = create_recipe(nutri_facts=nutri_facts)
        
        # Get initial cached macro division
        initial_macro = recipe.macro_division
        assert initial_macro is not None
        assert abs(initial_macro.carbohydrate - 50.0) < 0.01
        
        # Change nutrition facts
        new_nutri = NutriFacts(
            calories=400.0,
            carbohydrate=20.0,  # Now 25% of macros
            protein=30.0,       # Now 37.5% of macros
            total_fat=30.0,     # Now 37.5% of macros
            saturated_fat=10.0,
            trans_fat=0.0,
            dietary_fiber=8.0,
            sodium=500.0,
            sugar=5.0
        )
        recipe.nutri_facts = new_nutri # type: ignore
        
        # Check if cache was invalidated
        updated_macro = recipe.macro_division
        assert updated_macro is not None
        # With proper cache invalidation, percentages should change
        assert abs(updated_macro.carbohydrate - 25.0) < 0.01 