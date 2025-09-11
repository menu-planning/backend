"""
Tests for instance-level caching behavior in Menu entity.

These tests verify the correct per-instance caching behavior using @cached_property.
The conversion from @lru_cache to @cached_property has been completed, ensuring
proper instance-level cache isolation and invalidation.

All tests should PASS as they verify the working instance-level caching implementation.
"""

import pytest


from src.contexts.recipes_catalog.core.domain.client.entities.menu import Menu
from src.contexts.recipes_catalog.core.domain.client.value_objects.menu_meal import MenuMeal


class TestMenuInstanceLevelCaching:
    """Test per-instance caching for Menu computed properties."""

    @pytest.fixture
    def sample_menu_meals(self):
        """Sample menu meals for testing."""
        return {
            MenuMeal(meal_id="meal-1", meal_name="Frango Grelhado", week=1, weekday="Seg", meal_type="almoço"),
            MenuMeal(meal_id="meal-2", meal_name="Salmão Assado", week=1, weekday="Ter", meal_type="jantar"),
            MenuMeal(meal_id="meal-3", meal_name="Salada Caesar", week=2, weekday="Qua", meal_type="almoço"),
            MenuMeal(meal_id="meal-4", meal_name="Risotto de Camarão", week=2, weekday="Qui", meal_type="jantar"),
        }

    @pytest.fixture
    def menu_1(self, sample_menu_meals):
        """First menu instance for testing."""
        return Menu.create_menu(
            author_id="user-1",
            client_id="client-1", 
            menu_id="menu-1"
        )

    @pytest.fixture
    def menu_2(self):
        """Second menu instance for testing."""
        different_meals = {
            MenuMeal(meal_id="meal-5", meal_name="Café da Manhã", week=1, weekday="Sex", meal_type="café"),
            MenuMeal(meal_id="meal-6", meal_name="Almoço Fitness", week=1, weekday="Sab", meal_type="almoço"),
        }
        menu = Menu.create_menu(
            author_id="user-2",
            client_id="client-2",
            menu_id="menu-2"
        )
        menu.meals = different_meals
        return menu

    def test_meals_dict_per_instance_caching(self, menu_1, menu_2, sample_menu_meals):
        """Test that meals_dict provides consistent caching behavior."""
        # Set up meals for menu_1
        menu_1.meals = sample_menu_meals
        
        # Get meals dict for menu_1
        meals_dict_1 = menu_1.meals_dict
        
        # Menu_1 should have 4 meals
        assert len(meals_dict_1) == 4
        assert (1, "Seg", "almoço") in meals_dict_1
        assert (2, "Qui", "jantar") in meals_dict_1
        
        # Cache should provide consistent results
        meals_dict_1_cached = menu_1.meals_dict
        assert meals_dict_1 == meals_dict_1_cached
        
        # Get meals dict for menu_2 (has different meals)
        meals_dict_2 = menu_2.meals_dict
        
        # Menu_2 should have 2 different meals
        assert len(meals_dict_2) == 2
        assert (1, "Sex", "café") in meals_dict_2
        assert (1, "Sab", "almoço") in meals_dict_2
        
        # Should be completely different datasets
        assert meals_dict_1 != meals_dict_2

    def test_ids_of_meals_on_menu_per_instance_caching(self, menu_1, menu_2, sample_menu_meals):
        """Test that _ids_of_meals_on_menu provides consistent caching behavior."""
        # Set up meals for menu_1
        menu_1.meals = sample_menu_meals
        
        # Get meal IDs for menu_1
        ids_1 = menu_1._ids_of_meals_on_menu
        expected_ids_1 = {"meal-1", "meal-2", "meal-3", "meal-4"}
        assert ids_1 == expected_ids_1
        
        # Cache should provide consistent results
        ids_1_cached = menu_1._ids_of_meals_on_menu
        assert ids_1 == ids_1_cached
        
        # Get meal IDs for menu_2 (has different meals)
        ids_2 = menu_2._ids_of_meals_on_menu
        expected_ids_2 = {"meal-5", "meal-6"}
        assert ids_2 == expected_ids_2
        
        # Should be completely different datasets
        assert ids_1 != ids_2

    def test_get_meals_by_ids_per_instance_caching(self, menu_1, menu_2, sample_menu_meals):
        """Test that get_meals_by_ids provides consistent caching behavior."""
        # Set up meals for menu_1
        menu_1.meals = sample_menu_meals
        
        # Get specific meals from menu_1
        target_ids_1 = {"meal-1", "meal-3"}
        meals_1 = menu_1.get_meals_by_ids(target_ids_1)
        assert len(meals_1) == 2
        meal_ids_1 = {meal.meal_id for meal in meals_1}
        assert meal_ids_1 == target_ids_1
        
        # Cache should provide consistent results  
        meals_1_cached = menu_1.get_meals_by_ids(target_ids_1)
        assert meals_1 == meals_1_cached
        
        # Get specific meals from menu_2
        target_ids_2 = {"meal-5"}
        meals_2 = menu_2.get_meals_by_ids(target_ids_2)
        assert len(meals_2) == 1
        meal_ids_2 = {meal.meal_id for meal in meals_2}
        assert meal_ids_2 == target_ids_2
        
        # Should be different results
        assert meals_1 != meals_2

    def test_cache_invalidation_on_meals_change(self, menu_1, sample_menu_meals):
        """Test that cached methods are invalidated when meals change."""
        # Set initial meals
        menu_1.meals = sample_menu_meals
        
        # Access cached methods to populate cache
        initial_dict = menu_1.meals_dict
        initial_ids = menu_1._ids_of_meals_on_menu
        
        # Verify initial state
        assert len(initial_dict) == 4
        assert len(initial_ids) == 4
        
        # Add a new meal
        new_meal = MenuMeal(meal_id="meal-new", meal_name="Jantar Especial", week=3, weekday="Dom", meal_type="jantar")
        menu_1.add_meal(new_meal)
        
        # Cached values should be invalidated and recalculated
        updated_dict = menu_1.meals_dict
        updated_ids = menu_1._ids_of_meals_on_menu
        
        # Should now include the new meal
        assert len(updated_dict) == 5
        assert len(updated_ids) == 5
        assert "meal-new" in updated_ids
        assert (3, "Dom", "jantar") in updated_dict

    def test_cache_invalidation_on_meal_update(self, menu_1, sample_menu_meals):
        """Test that cached methods are invalidated when a meal is updated."""
        # Set initial meals
        menu_1.meals = sample_menu_meals
        
        # Access cached method to populate cache
        initial_dict = menu_1.meals_dict
        
        # Update an existing meal (same position, different properties)
        # Find the original meal at this position
        original_meal = initial_dict[(1, "Seg", "almoço")]
        
        # Create updated meal with same position but different name
        updated_meal = MenuMeal(
            meal_id="meal-1", 
            meal_name="Frango Grelhado Atualizado",  # Changed name
            week=1, 
            weekday="Seg", 
            meal_type="almoço"  # Same position
        )
        menu_1.update_meal(updated_meal)
        
        # Cache should be invalidated and recalculated
        updated_dict = menu_1.meals_dict
        
        # Should have the updated meal at the same position
        assert (1, "Seg", "almoço") in updated_dict
        updated_meal_in_dict = updated_dict[(1, "Seg", "almoço")]
        assert updated_meal_in_dict.meal_name == "Frango Grelhado Atualizado"
        assert updated_meal_in_dict.meal_id == "meal-1"

    def test_cache_invalidation_behavior_verification(self, menu_1):
        """Test that cache invalidation works correctly through behavioral verification."""
        # Add initial meal
        initial_meal = MenuMeal(meal_id="initial", meal_name="Initial Meal", week=1, weekday="Seg", meal_type="almoço")
        menu_1.add_meal(initial_meal)
        
        # Verify initial state
        assert len(menu_1.meals_dict) == 1
        assert len(menu_1._ids_of_meals_on_menu) == 1
        assert len(menu_1.get_meals_by_ids({"initial"})) == 1
        
        # Add another meal
        second_meal = MenuMeal(meal_id="second", meal_name="Second Meal", week=1, weekday="Ter", meal_type="jantar")
        menu_1.add_meal(second_meal)
        
        # Verify cache was invalidated by checking current state
        assert len(menu_1.meals_dict) == 2
        assert len(menu_1._ids_of_meals_on_menu) == 2
        assert len(menu_1.get_meals_by_ids({"initial", "second"})) == 2
        
        # Remove a meal
        menu_1.remove_meals({"initial"})
        
        # Verify cache was invalidated again
        assert len(menu_1.meals_dict) == 1
        assert len(menu_1._ids_of_meals_on_menu) == 1
        assert len(menu_1.get_meals_by_ids({"second"})) == 1
        assert len(menu_1.get_meals_by_ids({"initial"})) == 0

    def test_cache_performance_through_behavior(self, menu_1, sample_menu_meals):
        """Test that caching provides expected performance through behavioral verification."""
        # Set up meals
        menu_1.meals = sample_menu_meals
        
        # Multiple calls should return identical objects (behavior verification)
        dict_call_1 = menu_1.meals_dict
        dict_call_2 = menu_1.meals_dict
        dict_call_3 = menu_1.meals_dict
        
        # Should be the same dictionary object due to caching
        assert dict_call_1 is dict_call_2 is dict_call_3
        
        # Test ID lookup consistency
        ids_call_1 = menu_1._ids_of_meals_on_menu
        ids_call_2 = menu_1._ids_of_meals_on_menu
        
        # Should be the same set object due to caching
        assert ids_call_1 is ids_call_2
        
        # Test that get_meals_by_ids returns equivalent results
        target_ids = {"meal-1", "meal-2"}
        meals_1 = menu_1.get_meals_by_ids(target_ids)
        meals_2 = menu_1.get_meals_by_ids(target_ids)
        
        # Results should be equal (same meals)
        assert meals_1 == meals_2 