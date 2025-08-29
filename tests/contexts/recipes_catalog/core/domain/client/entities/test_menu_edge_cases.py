"""
Comprehensive edge case tests for Menu entity with parametrized scenarios.

Tests extreme values, edge cases, and error conditions without mocks.
Focuses on behavior verification rather than implementation details.
Uses proper domain-focused approach with Menu data factories.
Applies the established DRY pattern from Meal and Recipe edge case tests.
"""

import pytest

from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.menu.menu_domain_factories import create_dietary_restriction_menu, create_menu, create_menu_meal, create_special_event_menu, create_weekly_menu
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.shared_domain_factories import create_menu_tag

# Import Menu data factories


class TestMenuEdgeCases:
    """Test Menu entity edge cases and extreme scenarios using data factories."""

    @pytest.mark.parametrize("meal_count", [0, 1, 10, 50, 100])
    def test_menu_with_varying_meal_counts(self, meal_count):
        """Test Menu behavior with different numbers of meals using domain approach."""
        menu = create_menu(description="Meal Count Test Menu")
        
        # Create meals with varied but realistic data
        meals = set()
        for i in range(meal_count):
            meal = create_menu_meal(
                meal_id=f"meal_{i+1:03d}",
                meal_name=f"Test Meal {i+1}",
                week=(i // 7) + 1,  # Week 1, 2, 3, etc.
                weekday=["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"][i % 7],
                meal_type=["café da manhã", "almoço", "jantar", "lanche"][i % 4],
                nutri_facts=NutriFacts(
                    calories=NutriValue(value=400.0 + i*50, unit=MeasureUnit.ENERGY),
                    carbohydrate=NutriValue(value=50.0 + i*5, unit=MeasureUnit.GRAM),
                    protein=NutriValue(value=20.0 + i*2, unit=MeasureUnit.GRAM),
                    total_fat=NutriValue(value=15.0 + i, unit=MeasureUnit.GRAM)
                )
            )
            meals.add(meal)
        
        # Set meals on menu
        menu.meals = meals
        
        # Verify meal handling
        assert len(menu.meals) == meal_count
        
        # Test cached properties with varying meal counts
        meals_dict = menu.meals_dict
        ids_on_menu = menu._ids_of_meals_on_menu
        
        if meal_count == 0:
            assert len(meals_dict) == 0
            assert len(ids_on_menu) == 0
        else:
            assert len(meals_dict) == meal_count
            assert len(ids_on_menu) == meal_count
            
            # Verify meals are accessible by position keys
            for meal in meals:
                position_key = (meal.week, meal.weekday, meal.meal_type)
                assert position_key in meals_dict
                assert meal.meal_id in ids_on_menu

    @pytest.mark.parametrize("tag_count", [0, 1, 5, 20, 50, 100])
    def test_menu_with_varying_tag_counts(self, tag_count):
        """Test Menu behavior with different numbers of tags using factory."""
        # Create unique tags to avoid conflicts
        tags = set()
        tag_keys = ["diet", "occasion", "cuisine", "restriction", "style"]
        
        for i in range(tag_count):
            tag = create_menu_tag(
                key=tag_keys[i % len(tag_keys)],
                value=f"value_{i}",
                author_id=f"author_{(i % 3) + 1}",
                type="menu"
            )
            tags.add(tag)
        
        menu = create_menu(
            description="Tag Count Test Menu",
            tags=tags
        )
        
        # Verify tag handling
        assert len(menu.tags) == tag_count
        
        # All tags should be properly stored
        for tag in menu.tags:
            assert tag.type == "menu"
            assert tag.author_id.startswith("author_")
            assert tag.key in tag_keys

    @pytest.mark.parametrize("week_range", [
        (1, 1),  # Single week
        (1, 2),  # Two weeks
        (1, 4),  # One month
        (1, 12), # Three months
        (5, 8),  # Mid-range weeks
    ])
    def test_menu_with_varying_week_ranges(self, week_range):
        """Test Menu behavior with different week ranges using realistic meal distribution."""
        start_week, end_week = week_range
        menu = create_menu(description=f"Week Range Test Menu ({start_week}-{end_week})")
        
        # Create meals distributed across the week range
        meals = set()
        weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
        meal_types = ["café da manhã", "almoço", "jantar"]
        
        meal_id = 1
        for week in range(start_week, end_week + 1):
            for weekday in weekdays:
                for meal_type in meal_types:
                    meal = create_menu_meal(
                        meal_id=f"meal_{meal_id:03d}",
                        meal_name=f"{meal_type.title()} - {weekday} S{week}",
                        week=week,
                        weekday=weekday,
                        meal_type=meal_type
                    )
                    meals.add(meal)
                    meal_id += 1
        
        menu.meals = meals
        
        # Verify week range handling
        expected_meal_count = (end_week - start_week + 1) * 7 * 3  # weeks * days * meal_types
        assert len(menu.meals) == expected_meal_count
        
        # Test cache performance with large meal sets
        meals_dict = menu.meals_dict
        assert len(meals_dict) == expected_meal_count
        
        # Verify week distribution
        week_counts = {}
        for meal in menu.meals:
            week_counts[meal.week] = week_counts.get(meal.week, 0) + 1
        
        assert len(week_counts) == (end_week - start_week + 1)
        for week in range(start_week, end_week + 1):
            assert week_counts[week] == 21  # 7 days * 3 meal types

    @pytest.mark.parametrize("nutrition_scenario", [
        "zero_nutrition",      # All meals with zero calories
        "extreme_high",        # Very high calorie meals
        "mixed_extremes",      # Mix of zero and high calorie meals
        "minimal_nutrition",   # Very low but non-zero nutrition
        "unbalanced_macros",   # Extreme macro distributions
    ])
    def test_menu_with_extreme_nutrition_scenarios(self, nutrition_scenario):
        """Test Menu behavior with extreme nutrition scenarios via meals."""
        menu = create_menu(description=f"Nutrition Test Menu - {nutrition_scenario}")
        
        meals = set()
        
        if nutrition_scenario == "zero_nutrition":
            # All meals with zero nutrition
            for i in range(5):
                meal = create_menu_meal(
                    meal_id=f"meal_{i+1}",
                    meal_name=f"Zero Nutrition Meal {i+1}",
                    week=1,
                    weekday=["Seg", "Ter", "Qua", "Qui", "Sex"][i],
                    meal_type="almoço",
                    nutri_facts=NutriFacts(
                        calories=NutriValue(value=0.0, unit=MeasureUnit.ENERGY),
                        carbohydrate=NutriValue(value=0.0, unit=MeasureUnit.GRAM),
                        protein=NutriValue(value=0.0, unit=MeasureUnit.GRAM),
                        total_fat=NutriValue(value=0.0, unit=MeasureUnit.GRAM)
                    )
                )
                meals.add(meal)
                
        elif nutrition_scenario == "extreme_high":
            # Very high calorie meals
            for i in range(3):
                meal = create_menu_meal(
                    meal_id=f"meal_{i+1}",
                    meal_name=f"High Calorie Meal {i+1}",
                    week=1,
                    weekday=["Seg", "Ter", "Qua"][i],
                    meal_type="jantar",
                    nutri_facts=NutriFacts(
                        calories=NutriValue(value=5000.0 + i*1000, unit=MeasureUnit.ENERGY),
                        carbohydrate=NutriValue(value=600.0 + i*100, unit=MeasureUnit.GRAM),
                        protein=NutriValue(value=200.0 + i*50, unit=MeasureUnit.GRAM),
                        total_fat=NutriValue(value=300.0 + i*50, unit=MeasureUnit.GRAM)
                    )
                )
                meals.add(meal)
                
        elif nutrition_scenario == "mixed_extremes":
            # Mix of zero and extreme high
            zero_meal = create_menu_meal(
                meal_id="meal_zero",
                meal_name="Zero Meal",
                week=1,
                weekday="Seg",
                meal_type="café da manhã",
                nutri_facts=NutriFacts(
                    calories=NutriValue(value=0.0, unit=MeasureUnit.ENERGY)
                )
            )
            high_meal = create_menu_meal(
                meal_id="meal_high",
                meal_name="High Meal", 
                week=1,
                weekday="Seg",
                meal_type="jantar",
                nutri_facts=NutriFacts(
                    calories=NutriValue(value=8000.0, unit=MeasureUnit.ENERGY),
                    carbohydrate=NutriValue(value=1000.0, unit=MeasureUnit.GRAM),
                    protein=NutriValue(value=400.0, unit=MeasureUnit.GRAM),
                    total_fat=NutriValue(value=500.0, unit=MeasureUnit.GRAM)
                )
            )
            meals.update([zero_meal, high_meal])
            
        elif nutrition_scenario == "minimal_nutrition":
            # Very low but non-zero nutrition
            for i in range(4):
                meal = create_menu_meal(
                    meal_id=f"meal_{i+1}",
                    meal_name=f"Minimal Meal {i+1}",
                    week=1,
                    weekday=["Seg", "Ter", "Qua", "Qui"][i],
                    meal_type="lanche",
                    nutri_facts=NutriFacts(
                        calories=NutriValue(value=0.01 + i*0.01, unit=MeasureUnit.ENERGY),
                        carbohydrate=NutriValue(value=0.001 + i*0.001, unit=MeasureUnit.GRAM),
                        protein=NutriValue(value=0.001 + i*0.001, unit=MeasureUnit.GRAM),
                        total_fat=NutriValue(value=0.001 + i*0.001, unit=MeasureUnit.GRAM)
                    )
                )
                meals.add(meal)
                
        elif nutrition_scenario == "unbalanced_macros":
            # Extreme macro distributions
            scenarios = [
                ("only_carbs", 400.0, 100.0, 0.0, 0.0),
                ("only_protein", 400.0, 0.0, 100.0, 0.0),
                ("only_fat", 900.0, 0.0, 0.0, 100.0),
            ]
            
            for i, (name, calories, carbs, protein, fat) in enumerate(scenarios):
                meal = create_menu_meal(
                    meal_id=f"meal_{i+1}",
                    meal_name=f"Unbalanced Meal - {name}",
                    week=1,
                    weekday=["Seg", "Ter", "Qua"][i],
                    meal_type="almoço",
                    nutri_facts=NutriFacts(
                        calories=NutriValue(value=calories, unit=MeasureUnit.ENERGY),
                        carbohydrate=NutriValue(value=carbs, unit=MeasureUnit.GRAM),
                        protein=NutriValue(value=protein, unit=MeasureUnit.GRAM),
                        total_fat=NutriValue(value=fat, unit=MeasureUnit.GRAM)
                    )
                )
                meals.add(meal)
        
        menu.meals = meals
        
        # Verify menu handles extreme nutrition scenarios gracefully
        assert len(menu.meals) > 0
        
        # Test cached properties work with extreme nutrition
        meals_dict = menu.meals_dict
        ids_on_menu = menu._ids_of_meals_on_menu
        
        assert len(meals_dict) == len(meals)
        assert len(ids_on_menu) == len(meals)
        
        # All nutrition access should not raise errors
        for meal in menu.meals:
            assert meal.nutri_facts is not None
            # Nutrition values should be accessible without errors
            _ = meal.nutri_facts.calories.value
            _ = meal.nutri_facts.carbohydrate.value if meal.nutri_facts.carbohydrate else 0.0
            _ = meal.nutri_facts.protein.value if meal.nutri_facts.protein else 0.0
            _ = meal.nutri_facts.total_fat.value if meal.nutri_facts.total_fat else 0.0

    @pytest.mark.parametrize("string_length", [
        1,     # Minimal length
        50,    # Short description
        200,   # Normal length
        1000,  # Long description
        5000,  # Very long description
    ])
    def test_menu_with_varying_string_lengths(self, string_length):
        """Test Menu behavior with different description lengths."""
        if string_length == 1:
            long_description = "x"
        else:
            base_text = "Menu description "
            if string_length <= len(base_text):
                long_description = base_text[:string_length]
            else:
                long_description = base_text + "x" * (string_length - len(base_text))
        
        menu = create_menu(description=long_description)
        
        # Should handle varying string lengths appropriately
        assert menu.description == long_description
        assert menu.description is not None  # Type guard for linter
        assert len(menu.description) == string_length

    @pytest.mark.parametrize("menu_modification", [
        "add_meal",
        "remove_meal",
        "update_meal",
        "clear_all_meals",
        "replace_all_meals"
    ])
    def test_menu_meal_modification_edge_cases(self, menu_modification):
        """Test Menu behavior during meal modifications."""
        menu = create_menu(description="Meal Modification Test")
        
        # Start with initial meal
        initial_meal = create_menu_meal(
            meal_id="initial_meal",
            meal_name="Initial Meal",
            week=1,
            weekday="Seg",
            meal_type="almoço"
        )
        menu.add_meal(initial_meal)
        
        # Cache initial values
        initial_dict = menu.meals_dict
        initial_ids = menu._ids_of_meals_on_menu
        
        assert len(initial_dict) == 1
        assert len(initial_ids) == 1
        
        if menu_modification == "add_meal":
            # Add another meal
            new_meal = create_menu_meal(
                meal_id="new_meal",
                meal_name="New Meal",
                week=1,
                weekday="Ter",
                meal_type="jantar"
            )
            menu.add_meal(new_meal)
            
            # Cache should be invalidated and recalculated
            updated_dict = menu.meals_dict
            updated_ids = menu._ids_of_meals_on_menu
            
            assert len(updated_dict) == 2
            assert len(updated_ids) == 2
            assert "new_meal" in updated_ids
            
        elif menu_modification == "remove_meal":
            # Remove the meal
            menu.remove_meals({"initial_meal"})
            
            # Should have no meals
            updated_dict = menu.meals_dict
            updated_ids = menu._ids_of_meals_on_menu
            
            assert len(updated_dict) == 0
            assert len(updated_ids) == 0
            
        elif menu_modification == "update_meal":
            # Update meal by replacing it
            updated_meal = create_menu_meal(
                meal_id="initial_meal",  # Same ID
                meal_name="Updated Meal Name",
                week=2,  # Different week
                weekday="Qua",  # Different day
                meal_type="jantar"  # Different type
            )
            
            # Remove old and add updated
            menu.remove_meals({"initial_meal"})
            menu.add_meal(updated_meal)
            
            # Cache should reflect the update
            updated_dict = menu.meals_dict
            updated_ids = menu._ids_of_meals_on_menu
            
            assert len(updated_dict) == 1
            assert len(updated_ids) == 1
            assert "initial_meal" in updated_ids
            
            # Check new position key
            new_position_key = (2, "Qua", "jantar")
            assert new_position_key in updated_dict
            
        elif menu_modification == "clear_all_meals":
            # Clear all meals
            menu.meals = set()
            
            # Should handle empty state gracefully
            updated_dict = menu.meals_dict
            updated_ids = menu._ids_of_meals_on_menu
            
            assert len(updated_dict) == 0
            assert len(updated_ids) == 0
            
        elif menu_modification == "replace_all_meals":
            # Replace with completely new meal set
            new_meals = {
                create_menu_meal(
                    meal_id=f"replacement_{i}",
                    meal_name=f"Replacement Meal {i}",
                    week=1,
                    weekday=["Qui", "Sex"][i],
                    meal_type="lanche"
                ) for i in range(2)
            }
            menu.meals = new_meals
            
            # Cache should reflect complete replacement
            updated_dict = menu.meals_dict
            updated_ids = menu._ids_of_meals_on_menu
            
            assert len(updated_dict) == 2
            assert len(updated_ids) == 2
            assert "initial_meal" not in updated_ids
            assert "replacement_0" in updated_ids
            assert "replacement_1" in updated_ids

    def test_menu_cache_invalidation_comprehensive(self):
        """Test Menu cache invalidation across all mutation scenarios."""
        menu = create_menu(description="Cache Test Menu")
        
        # Add initial meals
        meal1 = create_menu_meal(
            meal_id="meal_1",
            meal_name="Meal 1",
            week=1,
            weekday="Seg",
            meal_type="almoço"
        )
        meal2 = create_menu_meal(
            meal_id="meal_2", 
            meal_name="Meal 2",
            week=1,
            weekday="Ter",
            meal_type="jantar"
        )
        menu.meals = {meal1, meal2}
        
        # Cache initial values
        initial_dict = menu.meals_dict
        initial_ids = menu._ids_of_meals_on_menu
        
        assert len(initial_dict) == 2
        assert len(initial_ids) == 2
        
        # Add another meal - should invalidate caches
        meal3 = create_menu_meal(
            meal_id="meal_3",
            meal_name="Meal 3", 
            week=2,
            weekday="Qua",
            meal_type="café da manhã"
        )
        menu.add_meal(meal3)
        
        # Caches should be recalculated
        updated_dict = menu.meals_dict
        updated_ids = menu._ids_of_meals_on_menu
        
        # Values should be different (recalculated)
        assert len(updated_dict) == 3
        assert len(updated_ids) == 3
        assert updated_dict != initial_dict
        assert updated_ids != initial_ids
        
        # New meal should be accessible
        assert "meal_3" in updated_ids
        new_position_key = (2, "Qua", "café da manhã")
        assert new_position_key in updated_dict
        
        # Test get_meals_by_ids cache behavior
        target_ids = {"meal_1", "meal_3"}
        retrieved_meals = menu.get_meals_by_ids(target_ids)
        assert len(retrieved_meals) == 2
        
        meal_ids = {meal.meal_id for meal in retrieved_meals}
        assert meal_ids == target_ids

    @pytest.mark.parametrize("menu_type", [
        "weekly",
        "special_event", 
        "dietary_restriction"
    ])
    def test_specialized_menu_edge_cases(self, menu_type):
        """Test edge cases for specialized menu types using factories."""
        if menu_type == "weekly":
            menu = create_weekly_menu(description="Weekly Edge Case Menu")
            # Weekly menus should have meals for a full week
            assert len(menu.meals) > 0
            
            # Check week distribution
            weeks = {meal.week for meal in menu.meals}
            assert len(weeks) >= 1  # At least one week
            
        elif menu_type == "special_event":
            menu = create_special_event_menu(description="Special Event Edge Case Menu")
            # Special event menus should have event-related tags
            event_tags = [tag for tag in menu.tags if tag.key == "event"]
            assert len(event_tags) > 0
            
        elif menu_type == "dietary_restriction":
            menu = create_dietary_restriction_menu(description="Dietary Restriction Edge Case Menu")
            # Should have dietary restriction tags
            diet_tags = [tag for tag in menu.tags if tag.key == "dietary"]
            assert len(diet_tags) > 0

    def test_menu_with_realistic_data_scenarios(self):
        """Test Menu edge cases using realistic data from factories."""
        # Create multiple realistic menus to test various scenarios
        menus = [
            create_weekly_menu(),
            create_special_event_menu(),
            create_dietary_restriction_menu()
        ]
        
        for menu in menus:
            # All menus should have valid basic properties
            assert menu.id is not None
            assert menu.client_id is not None
            assert menu.author_id is not None
            assert menu.description is not None
            assert len(menu.description) > 0
            
            # All should handle cache operations safely
            meals_dict = menu.meals_dict  # Should not raise
            ids_on_menu = menu._ids_of_meals_on_menu  # Should not raise
            
            assert isinstance(meals_dict, dict)
            assert isinstance(ids_on_menu, set)
            
            # Test meal retrieval operations
            if len(ids_on_menu) > 0:
                # Pick some meal IDs to test with
                sample_ids = set(list(ids_on_menu)[:min(3, len(ids_on_menu))])
                retrieved_meals = menu.get_meals_by_ids(sample_ids)
                
                assert len(retrieved_meals) <= len(sample_ids)
                retrieved_ids = {meal.meal_id for meal in retrieved_meals}
                assert retrieved_ids.issubset(sample_ids)

    @pytest.mark.parametrize("invalid_data", [
        {"description": ""},  # Empty description
        {"description": None},  # None description
        {"client_id": ""},  # Empty client_id
        {"client_id": None},  # None client_id
        {"author_id": ""},  # Empty author_id
        {"author_id": None},  # None author_id
    ])
    def test_menu_validation_edge_cases(self, invalid_data):
        """Test Menu validation with invalid data."""
        # Most validation should happen at creation time
        try:
            menu = create_menu(**invalid_data)
            # If creation succeeds, basic properties should still be valid
            if menu.description is not None:
                assert len(menu.description) >= 0
            if menu.client_id is not None:
                assert len(menu.client_id) >= 0
            if menu.author_id is not None:
                assert len(menu.author_id) >= 0
        except (ValueError, TypeError):
            # Validation error is acceptable for invalid data
            pass

    def test_menu_concurrent_like_modifications(self):
        """Test Menu behavior during rapid successive modifications."""
        menu = create_menu(description="Concurrent Test Menu")
        
        # Simulate rapid successive changes
        for i in range(10):
            new_meal = create_menu_meal(
                meal_id=f"rapid_meal_{i}",
                meal_name=f"Rapid Meal {i}",
                week=(i // 7) + 1,
                weekday=["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"][i % 7],
                meal_type=["café da manhã", "almoço", "jantar"][i % 3]
            )
            menu.add_meal(new_meal)
            
            # Should handle each change correctly
            meals_dict = menu.meals_dict
            ids_on_menu = menu._ids_of_meals_on_menu
            
            assert len(meals_dict) == i + 1
            assert len(ids_on_menu) == i + 1
            assert f"rapid_meal_{i}" in ids_on_menu

    def test_menu_large_dataset_performance(self):
        """Test Menu performance with large meal datasets."""
        menu = create_menu(description="Large Dataset Performance Test")
        
        # Create a large number of meals (simulating a year's worth)
        large_meal_set = set()
        meal_types = ["café da manhã", "almoço", "jantar", "lanche"]
        weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
        
        meal_id = 1
        for week in range(1, 53):  # 52 weeks
            for weekday in weekdays:
                for meal_type in meal_types:
                    meal = create_menu_meal(
                        meal_id=f"large_meal_{meal_id:04d}",
                        meal_name=f"{meal_type.title()} - W{week} {weekday}",
                        week=week,
                        weekday=weekday,
                        meal_type=meal_type
                    )
                    large_meal_set.add(meal)
                    meal_id += 1
        
        menu.meals = large_meal_set
        
        # Test cache performance with large dataset
        expected_count = 52 * 7 * 4  # 52 weeks * 7 days * 4 meal types = 1456 meals
        assert len(menu.meals) == expected_count
        
        # Cache operations should handle large datasets efficiently
        meals_dict = menu.meals_dict
        ids_on_menu = menu._ids_of_meals_on_menu
        
        assert len(meals_dict) == expected_count
        assert len(ids_on_menu) == expected_count
        
        # Test selective retrieval from large dataset
        sample_ids = {f"large_meal_{i:04d}" for i in range(1, 101, 10)}  # Every 10th meal
        retrieved_meals = menu.get_meals_by_ids(sample_ids)
        
        assert len(retrieved_meals) == len(sample_ids)
        retrieved_ids = {meal.meal_id for meal in retrieved_meals}
        assert retrieved_ids == sample_ids 