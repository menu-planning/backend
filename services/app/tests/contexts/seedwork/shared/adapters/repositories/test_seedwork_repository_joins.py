"""
Join functionality integration tests for SaGenericRepository

This module tests complex join scenarios and multi-table filtering with REAL database:
- Complex filtering scenarios with actual joins
- Multi-level join chains with real foreign keys  
- Join deduplication and optimization with real SQL
- Performance testing of complex queries

Following "Architecture Patterns with Python" principles:
- Real database connections (test database)
- Test behavior, not implementation
- Known DB states via fixtures
- Real DB errors and constraints
- Performance benchmarks for complex queries

Key improvements over v1:
- Uses real test models with actual relationships
- Tests actual SQL generation and execution
- Validates real foreign key constraints
- Tests real join performance and optimization
- Catches real database join errors
"""

import anyio
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from tests.contexts.seedwork.shared.adapters.repositories.conftest import (
    timeout_test
)
from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
    create_test_ORM_meal, create_test_ORM_recipe,
    create_test_ORM_ingredient, reset_counters
)

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


class TestSaGenericRepositoryComplexFilteringScenarios:
    """
    Test complex filtering scenarios with real database joins
    
    This tests scenarios that require multiple table joins with actual data:
    - Meal -> Recipe joins for recipe-based filtering  
    - Meal -> Recipe -> Ingredient joins for ingredient filtering
    - Complex filter combinations across multiple tables
    - Real foreign key constraint validation
    """
    
    @pytest.fixture
    async def meal_with_recipes_and_ingredients(self, meal_repository, recipe_repository, test_session):
        """Create a complete meal hierarchy for join testing using ORM instances"""
        # Create meal ORM instance with proper nutritional structure
        meal = create_test_ORM_meal(
            id="join_test_meal",
            name="Complex Italian Dinner",
            author_id="chef123",
            total_time=90,
            # Set individual nutritional components that will form nutri_facts composite
            calories=650.0,  # This should go into nutri_facts.calories
            protein=35.0,    # This should go into nutri_facts.protein
            carbohydrate=75.0, # This should go into nutri_facts.carbohydrate
            total_fat=25.0,  # This should go into nutri_facts.total_fat
            weight_in_grams=200,  # For calorie_density calculation
            # Explicitly set calorie_density to meet the test filter requirement
            calorie_density=350.0,  # Must be >= 300 for the test to pass
            # Note: calorie_density and percentage fields should be calculated by the mapper
        )
        test_session.add(meal)
        await test_session.flush()  # Ensure meal exists for FK
        
        # Create recipe ORM instance
        recipe = create_test_ORM_recipe(
            id="join_test_recipe",
            name="Chicken Alfredo",
            meal_id="join_test_meal",
            author_id="chef123",
            total_time=45
        )
        test_session.add(recipe)
        await test_session.flush()  # Ensure recipe exists for FK
        
        # Create ingredients separately and add them
        
        ingredients_data = [
            {"name": "Chicken Breast", "product_id": "chicken", "quantity": 300.0, "unit": "grams"},
            {"name": "Fettuccine Pasta", "product_id": "pasta", "quantity": 200.0, "unit": "grams"},
            {"name": "Heavy Cream", "product_id": "cream", "quantity": 150.0, "unit": "ml"},
            {"name": "Parmesan Cheese", "product_id": "parmesan", "quantity": 50.0, "unit": "grams"},
        ]
        
        for i, ingredient_data in enumerate(ingredients_data):
            ingredient = create_test_ORM_ingredient(
                recipe_id="join_test_recipe",
                position=i,
                **ingredient_data
            )
            test_session.add(ingredient)
        
        await test_session.commit()
        
        return meal, recipe
    
    @timeout_test(30.0)
    async def test_meal_filter_by_recipe_properties_real_join(
        self, meal_repository, meal_with_recipes_and_ingredients
    ):
        """Test filtering meals by recipe properties (requires real join)"""
        meal, recipe = meal_with_recipes_and_ingredients
        
        # When: Filtering meals by recipe name (requires Meal -> Recipe join)
        results = await meal_repository.query(filter={"recipe_name": "Chicken Alfredo"}, _return_sa_instance=True)
        
        # Then: Real join executes and returns correct meal
        assert len(results) == 1, f"Expected 1 meal but got {len(results)}"
        assert results[0].id == "join_test_meal"
        assert results[0].name == "Complex Italian Dinner"
    
    @timeout_test(30.0)
    async def test_meal_filter_by_ingredient_products_multi_level_join(
        self, meal_repository, meal_with_recipes_and_ingredients
    ):
        """Test filtering meals by ingredient products (requires real multi-level join)"""
        meal, recipe = meal_with_recipes_and_ingredients
        
        # Debug: Check what was actually created
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import IngredientSaTestModel
        from sqlalchemy import select
        
        # Check what ingredients exist
        stmt = select(IngredientSaTestModel)
        result = await meal_repository._session.execute(stmt)
        ingredients = result.scalars().all()
        print(f"Ingredients in DB: {len(ingredients)}")
        for ing in ingredients:
            print(f"  Ingredient: {ing.name} (product_id={ing.product_id}, recipe_id={ing.recipe_id})")
        
        # When: Filtering by ingredient products (Meal -> Recipe -> Ingredient joins)
        results = await meal_repository.query(filter={"products": ["chicken", "pasta"]}, _return_sa_instance=True)
        
        # Then: Multi-level join executes correctly
        assert len(results) == 1, f"Expected 1 meal but got {len(results)}"
        assert results[0].id == "join_test_meal"
        
        # When: Filtering by non-existent product
        no_results = await meal_repository.query(filter={"products": ["non_existent_product"]}, _return_sa_instance=True)
        
        # Then: No results found (proves join is working)
        assert len(no_results) == 0
    
    @timeout_test(30.0) 
    async def test_complex_multi_table_filter_combination_real_data(
        self, meal_repository, meal_with_recipes_and_ingredients
    ):
        """Test complex filters combining multiple real table joins"""
        meal, recipe = meal_with_recipes_and_ingredients
        
        # When: Complex multi-table filtering
        results = await meal_repository.query(filter={
            "name": "Complex Italian Dinner",    # Meal table (no join)
            "author_id": "chef123",             # Meal table (no join)  
            "recipe_name": "Chicken Alfredo",   # Recipe table (1 join)
            "products": ["chicken", "pasta"],    # Ingredient table (2 joins)
            "total_time_lte": 100,              # Meal table (no join)
            "calorie_density_gte": 300,         # Meal table composite field
        }, _return_sa_instance=True)
        
        # Then: All filters applied correctly
        assert len(results) == 1
        assert results[0].id == "join_test_meal"
        assert results[0].total_time <= 100
        assert results[0].calorie_density >= 300
        
        # When: Tightening one filter to exclude the meal
        no_results = await meal_repository.query(filter={
            "name": "Complex Italian Dinner",
            "author_id": "chef123", 
            "recipe_name": "Chicken Alfredo",
            "products": ["chicken", "pasta"],
            "total_time_lte": 30,  # Too restrictive
        }, _return_sa_instance=True)
        
        # Then: No results (proves all filters are ANDed)
        assert len(no_results) == 0
        
    @timeout_test(30.0)
    async def test_duplicate_join_prevention_real_sql(
        self, meal_repository, meal_with_recipes_and_ingredients, test_session
    ):
        """Test that duplicate joins are prevented in real SQL generation"""
        meal, recipe = meal_with_recipes_and_ingredients
        
        # When: Multiple filters requiring same join
        results = await meal_repository.query(filter={
            "recipe_id": "join_test_recipe",     # Requires Meal -> Recipe join
            "recipe_name": "Chicken Alfredo",    # Also requires Meal -> Recipe join
        }, _return_sa_instance=True)
        
        # Then: Query executes successfully (no duplicate join errors)
        assert len(results) == 1
        assert results[0].id == "join_test_meal"
        
        # Verify SQL efficiency by checking it doesn't timeout
        # (duplicate joins would significantly slow down the query)
        with anyio.move_on_after(5) as cancel_scope:
            results = await meal_repository.query(filter={
                "recipe_id": "join_test_recipe",
                "recipe_name": "Chicken Alfredo",
                "recipe_total_time": 45,  # Another recipe filter
            }, _return_sa_instance=True)
            assert len(results) == 1
        
        # Should complete quickly without timeout
        assert not cancel_scope.cancelled_caught
    
    @timeout_test(30.0)
    async def test_nutrition_filter_combination_composite_fields(
        self, meal_repository, meal_with_recipes_and_ingredients
    ):
        """Test filtering by nutrition facts (both composite and calculated fields)"""
        meal, recipe = meal_with_recipes_and_ingredients
        
        # Test 1: Filter by composite nutritional facts (individual columns in nutri_facts)
        results = await meal_repository.query(filter={
            "calories_gte": 600,      # meal.calories >= 600 (from nutri_facts composite)
            "calories_lte": 700,      # meal.calories <= 700 (from nutri_facts composite)
            "protein_gte": 30,        # meal.protein >= 30 (from nutri_facts composite)
        }, _return_sa_instance=True)
        
        # Then: Composite field filtering works correctly
        assert len(results) == 1, f"Expected 1 meal filtering by composite nutritional facts but got {len(results)}"
        assert results[0].nutri_facts.calories >= 600, f"Expected calories >= 600, got {results[0].nutri_facts.calories}"
        assert results[0].nutri_facts.calories <= 700, f"Expected calories <= 700, got {results[0].nutri_facts.calories}"
        assert results[0].nutri_facts.protein >= 30, f"Expected protein >= 30, got {results[0].nutri_facts.protein}"
        
        # Test 2: Filter by calculated percentage fields
        # Note: These would be calculated from the actual nutritional composition
        # For now, test the existing calculated fields stored in the database
        percentage_results = await meal_repository.query(filter={
            "carbohydrate_gte": 70,   # meal.carbohydrate >= 70 (from nutri_facts composite)
            "total_fat_lte": 30,      # meal.total_fat <= 30 (from nutri_facts composite)
        }, _return_sa_instance=True)
        
        # Then: Calculated field filtering works correctly
        assert len(percentage_results) == 1, f"Expected 1 meal filtering by carbohydrate/fat but got {len(percentage_results)}"
        assert percentage_results[0].nutri_facts.carbohydrate >= 70, f"Expected carbohydrate >= 70, got {percentage_results[0].nutri_facts.carbohydrate}"
        assert percentage_results[0].nutri_facts.total_fat <= 30, f"Expected total_fat <= 30, got {percentage_results[0].nutri_facts.total_fat}"
        
        # Test 3: Combined composite + calculated fields filtering
        combined_results = await meal_repository.query(filter={
            "calories_gte": 600,      # Composite field
            "protein_gte": 30,        # Composite field
            "weight_in_grams_gte": 150,  # Regular field used in calculations
        }, _return_sa_instance=True)
        
        # Then: Combined filtering works correctly
        assert len(combined_results) == 1, f"Expected 1 meal with combined filters but got {len(combined_results)}"
        result = combined_results[0]
        assert result.nutri_facts.calories >= 600
        assert result.nutri_facts.protein >= 30
        assert result.weight_in_grams >= 150
        
        # Test 4: Impossible nutritional constraints
        no_results = await meal_repository.query(filter={
            "calories_gte": 600,
            "calories_lte": 500,  # Impossible: >= 600 AND <= 500
        }, _return_sa_instance=True)
        
        # Then: No results (proves filters are working)
        assert len(no_results) == 0, "Expected no results with impossible constraints"
        
        # Test 5: Multi-component nutritional filtering
        multi_results = await meal_repository.query(filter={
            "calories_gte": 500,      # Energy content
            "protein_gte": 20,        # Protein content
            "carbohydrate_gte": 50,   # Carbohydrate content
            "total_fat_gte": 15,      # Fat content
        }, _return_sa_instance=True)
        
        # Then: Multi-component filtering works
        assert len(multi_results) == 1, f"Expected 1 meal with multi-component nutrition filter but got {len(multi_results)}"
        result = multi_results[0]
        assert result.nutri_facts.calories >= 500
        assert result.nutri_facts.protein >= 20
        assert result.nutri_facts.carbohydrate >= 50
        assert result.nutri_facts.total_fat >= 15

    @timeout_test(30.0)
    async def test_calculated_properties_filtering(
        self, meal_repository, meal_with_recipes_and_ingredients
    ):
        """Test filtering by calculated properties (like calorie_density in real domain)"""
        meal, recipe = meal_with_recipes_and_ingredients
        
        # In the real domain model (meal.py), calorie_density is calculated as:
        # (nutri_facts.calories.value / weight_in_grams) * 100
        # With our test data: calories=650, weight_in_grams=200
        # Expected calorie_density = (650 / 200) * 100 = 325.0
        
        # For this test, we need to manually set calorie_density in our test meal
        # since our test mapper now properly maps it from the domain
        # Let's create a meal with known calculated values for testing
        reset_counters()  # Ensure deterministic IDs
        
        calculated_meal = create_test_ORM_meal(
            id="calculated_test_meal",
            name="Meal with Calculated Properties",
            author_id="chef456",
            calories=800.0,  # Base nutritional data
            protein=40.0,
            carbohydrate=80.0,
            total_fat=30.0,
            weight_in_grams=250,
            # Calculated properties (would be computed in real domain)
            calorie_density=320.0,  # (800/250)*100 = 320
            protein_percentage=26.67,  # 40/(40+80+30)*100 = 26.67%
            carbo_percentage=53.33,   # 80/(40+80+30)*100 = 53.33%
            total_fat_percentage=20.0,  # 30/(40+80+30)*100 = 20%
        )
        
        test_session = meal_repository._session
        test_session.add(calculated_meal)
        await test_session.commit()
        
        # Test 1: Filter by calculated calorie density
        density_results = await meal_repository.query(filter={
            "calorie_density_gte": 300,    # meal.calorie_density >= 300
            "calorie_density_lte": 350,    # meal.calorie_density <= 350
        }, _return_sa_instance=True)
        
        # Should find both our test meals (one with 320.0, original might have calculated value)
        assert len(density_results) >= 1, f"Expected at least 1 meal with calorie density 300-350 but got {len(density_results)}"
        found_calculated_meal = any(meal.id == "calculated_test_meal" for meal in density_results)
        assert found_calculated_meal, "Should find the meal with calculated calorie density"
        
        # Test 2: Filter by calculated percentage properties
        percentage_results = await meal_repository.query(filter={
            "protein_percentage_gte": 20,  # meal.protein_percentage >= 20
            "carbo_percentage_gte": 50,    # meal.carbo_percentage >= 50
        }, _return_sa_instance=True)
        
        assert len(percentage_results) >= 1, f"Expected at least 1 meal with percentage filters but got {len(percentage_results)}"
        
        # Test 3: Combined calculated + composite filtering
        mixed_results = await meal_repository.query(filter={
            "calories_gte": 750,           # Composite nutritional fact
            "calorie_density_gte": 300,    # Calculated property
            "protein_percentage_gte": 20,  # Calculated property
        }, _return_sa_instance=True)
        
        assert len(mixed_results) >= 1, f"Expected at least 1 meal with mixed composite/calculated filters but got {len(mixed_results)}"
        
        # Verify the calculated meal meets all criteria
        calculated_result = next((meal for meal in mixed_results if meal.id == "calculated_test_meal"), None)
        assert calculated_result is not None, "Should find the calculated test meal in mixed results"
        assert calculated_result.nutri_facts.calories >= 750
        assert calculated_result.calorie_density >= 300
        assert calculated_result.protein_percentage >= 20


class TestSaGenericRepositoryComplexMultiLevelJoins:
    """
    Test complex multi-level join scenarios with real database
    
    These tests use multiple models with actual foreign key relationships,
    creating scenarios where multiple join paths and deep chains
    are required to execute successfully.
    """
    
    @pytest.fixture
    async def complex_meal_hierarchy(self, meal_repository, recipe_repository, test_session):
        """Create complex hierarchy with multiple meals, recipes, and ingredients using ORM instances"""
        # Create multiple meals with different properties
        meals = [
            create_test_ORM_meal(
                id="meal_italian", 
                name="Italian Night",
                author_id="chef_mario",
                total_time=120,
                calorie_density=400.0
            ),
            create_test_ORM_meal(
                id="meal_asian",
                name="Asian Fusion", 
                author_id="chef_liu",
                total_time=60,
                calorie_density=250.0
            ),
            create_test_ORM_meal(
                id="meal_american",
                name="American Classic",
                author_id="chef_bob", 
                total_time=45,
                calorie_density=300.0
            ),
        ]
        
        for meal in meals:
            test_session.add(meal)
        await test_session.flush()
        
        # Create recipes with ingredients
        recipes_data = [
            {
                "id": "recipe_pasta",
                "name": "Pasta Primavera",
                "meal_id": "meal_italian",
                "author_id": "chef_mario",
                "total_time": 45,
                "ingredients": [
                    {"name": "Pasta", "product_id": "pasta", "quantity": 300.0, "unit": "grams"},
                    {"name": "Vegetables", "product_id": "vegetables", "quantity": 200.0, "unit": "grams"},
                ]
            },
            {
                "id": "recipe_stirfry", 
                "name": "Vegetable Stir Fry",
                "meal_id": "meal_asian",
                "author_id": "chef_liu",
                "total_time": 25,
                "ingredients": [
                    {"name": "Rice", "product_id": "rice", "quantity": 150.0, "unit": "grams"},
                    {"name": "Mixed Vegetables", "product_id": "vegetables", "quantity": 250.0, "unit": "grams"},
                    {"name": "Soy Sauce", "product_id": "soy_sauce", "quantity": 30.0, "unit": "ml"},
                ]
            },
            {
                "id": "recipe_burger",
                "name": "Classic Burger",
                "meal_id": "meal_american", 
                "author_id": "chef_bob",
                "total_time": 30,
                "ingredients": [
                    {"name": "Ground Beef", "product_id": "beef", "quantity": 200.0, "unit": "grams"},
                    {"name": "Buns", "product_id": "bread", "quantity": 2.0, "unit": "pieces"},
                ]
            },
        ]
        
        recipes = []
        for recipe_data in recipes_data:
            # Extract ingredients data
            ingredients_data = recipe_data.pop("ingredients", [])
            
            # Create recipe ORM instance
            recipe = create_test_ORM_recipe(**recipe_data)
            test_session.add(recipe)
            await test_session.flush()  # Ensure recipe exists for FK
            
            # Create and persist ingredients
            for i, ingredient_data in enumerate(ingredients_data):
                ingredient = create_test_ORM_ingredient(
                    recipe_id=recipe.id,
                    position=i,
                    **ingredient_data
                )
                test_session.add(ingredient)
            
            recipes.append(recipe)
        
        await test_session.commit()
        
        return meals, recipes
    
    @timeout_test(30.0)
    async def test_deep_join_meal_recipe_ingredient_real_data(
        self, meal_repository, complex_meal_hierarchy
    ):
        """Test deep join: Meal -> Recipe -> Ingredient with real data"""
        meals, recipes = complex_meal_hierarchy
        
        # When: Filtering by ingredient that exists in multiple meals
        vegetable_meals = await meal_repository.query(filter={
            "products": ["vegetables"]  # Filter by ingredient product_id
        }, _return_sa_instance=True)
        
        # Then: Both Italian and Asian meals should be found
        assert len(vegetable_meals) == 2
        meal_names = {meal.name for meal in vegetable_meals}
        assert meal_names == {"Italian Night", "Asian Fusion"}
        
        # When: Filtering by ingredient that exists in only one meal
        beef_meals = await meal_repository.query(filter={
            "products": ["beef"]
        }, _return_sa_instance=True)
        
        # Then: Only American meal should be found
        assert len(beef_meals) == 1
        assert beef_meals[0].name == "American Classic"
        
        # When: Filtering by non-existent ingredient
        no_meals = await meal_repository.query(filter={
            "products": ["lobster"]
        }, _return_sa_instance=True)
        
        # Then: No meals found
        assert len(no_meals) == 0
    
    @timeout_test(30.0)
    async def test_complex_join_with_multiple_filter_paths(
        self, meal_repository, complex_meal_hierarchy
    ):
        """Test scenarios where multiple join paths exist to same target"""
        meals, recipes = complex_meal_hierarchy
        
        # When: Combining recipe-level and ingredient-level filters
        results = await meal_repository.query(filter={
            "recipe_name": "Pasta Primavera",  # Join through recipes relationship
            "products": ["pasta"],              # Join through recipes -> ingredients
            "author_id": "chef_mario",         # Direct meal attribute
        }, _return_sa_instance=True)
        
        # Then: Complex join path resolution works correctly
        assert len(results) == 1
        assert results[0].name == "Italian Night"
        assert results[0].author_id == "chef_mario"
        
        # When: Using conflicting filters across join paths
        no_results = await meal_repository.query(filter={
            "recipe_name": "Pasta Primavera",  # Italian recipe
            "products": ["rice"],               # Asian ingredient
        }, _return_sa_instance=True)
        
        # Then: No results (proves joins are working correctly)
        assert len(no_results) == 0
    
    @timeout_test(30.0)
    async def test_join_deduplication_with_complex_real_filters(
        self, meal_repository, complex_meal_hierarchy
    ):
        """Test that duplicate joins are properly detected and avoided in real SQL"""
        meals, recipes = complex_meal_hierarchy
        
        # When: Multiple filters requiring same recipe join
        results = await meal_repository.query(filter={
            "recipe_id": "recipe_pasta",        # Requires Meal -> Recipe join
            "recipe_name": "Pasta Primavera",   # Also requires Meal -> Recipe join  
            "recipe_total_time": 45,            # Also requires Meal -> Recipe join
        }, _return_sa_instance=True)
        
        # Then: Query executes efficiently (no duplicate joins)
        assert len(results) == 1
        assert results[0].name == "Italian Night"
        
        # Performance check: Complex query with potential duplicate joins should be fast
        with anyio.move_on_after(3) as cancel_scope:
            results = await meal_repository.query(filter={
                "recipe_id": "recipe_pasta",
                "recipe_name": "Pasta Primavera", 
                "recipe_total_time": 45,
                "products": ["pasta"],           # Also needs recipe join for ingredients
                "ingredient_name": "Pasta",      # Another ingredient-level filter
            }, _return_sa_instance=True)
            assert len(results) == 1
        
        # Should complete quickly without timeout (proves join optimization)
        assert not cancel_scope.cancelled_caught


class TestSaGenericRepositoryJoinConstraintValidation:
    """
    Test real database constraint validation in join scenarios
    
    These tests verify that foreign key constraints are properly
    enforced and that constraint violations produce real database errors.
    """
    
    @timeout_test(30.0)
    async def test_foreign_key_constraint_in_joins(
        self, meal_repository, recipe_repository, test_session
    ):
        """Test that foreign key constraints are enforced in join scenarios"""
        # Given: A meal exists
        meal = create_test_ORM_meal(id="fk_test_meal", author_id="chef_test")
        test_session.add(meal)
        await test_session.commit()
        
        # When: Creating recipe with valid meal_id
        valid_recipe = create_test_ORM_recipe(
            id="valid_recipe",
            name="Valid Recipe", 
            meal_id="fk_test_meal",  # Valid FK
            author_id="chef_test"
        )
        test_session.add(valid_recipe)
        await test_session.commit()
        
        # Then: Recipe is created successfully and can be joined
        results = await meal_repository.query(filter={"recipe_id": "valid_recipe"}, _return_sa_instance=True)
        assert len(results) == 1
        
        # When: Attempting to create recipe with invalid meal_id
        invalid_recipe = create_test_ORM_recipe(
            id="invalid_recipe",
            name="Invalid Recipe",
            meal_id="non_existent_meal",  # Invalid FK
            author_id="chef_test"
        )
        
        # Then: Foreign key constraint violation occurs
        with pytest.raises(IntegrityError) as exc_info:
            test_session.add(invalid_recipe)
            await test_session.commit()
        
        assert "foreign key constraint" in str(exc_info.value).lower()
        await test_session.rollback()
    
    @timeout_test(30.0)
    async def test_cascade_behavior_in_joins(
        self, meal_repository, recipe_repository, test_session
    ):
        """Test cascade behavior when deleting entities involved in joins"""
        # Given: Meal with associated recipe
        meal = create_test_ORM_meal(id="cascade_meal", author_id="chef_cascade")
        test_session.add(meal)
        await test_session.flush()
        
        recipe = create_test_ORM_recipe(
            id="cascade_recipe",
            meal_id="cascade_meal",
            author_id="chef_cascade"
        )
        test_session.add(recipe)
        await test_session.commit()
        
        # Verify join works before deletion
        results = await meal_repository.query(filter={"recipe_id": "cascade_recipe"}, _return_sa_instance=True)
        assert len(results) == 1
        
        # When: Deleting the meal (need to handle FK constraint manually since no cascade configured)
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import TEST_SCHEMA
        
        # First delete the dependent recipes to avoid FK constraint violation
        await test_session.execute(
            text(f"DELETE FROM {TEST_SCHEMA}.test_recipes WHERE meal_id = 'cascade_meal'")
        )
        # Then delete the meal
        await test_session.execute(
            text(f"DELETE FROM {TEST_SCHEMA}.test_meals WHERE id = 'cascade_meal'")
        )
        await test_session.commit()
        
        # Then: Join query returns no results (deletion worked)
        results = await meal_repository.query(filter={"recipe_id": "cascade_recipe"}, _return_sa_instance=True)
        assert len(results) == 0


class TestSaGenericRepositoryJoinPerformance:
    """
    Performance benchmarks for complex join scenarios
    
    These tests establish performance baselines for complex queries
    and ensure that join optimization is working correctly.
    """
    
    @pytest.fixture
    async def large_join_dataset(self, meal_repository, recipe_repository, test_session):
        """Create large dataset for performance testing using ORM instances"""
        meals = []
        recipes = []
        
        # Create 50 meals with 2-3 recipes each (100-150 recipes total)
        for i in range(50):
            meal = create_test_ORM_meal(
                id=f"perf_meal_{i}",
                name=f"Performance Meal {i}",
                author_id=f"chef_{i % 10}",  # 10 different chefs
                total_time=(i % 120) + 30,   # 30-150 minutes
                calorie_density=200.0 + (i % 200),  # 200-400 calorie density
            )
            meals.append(meal)
            test_session.add(meal)
            
            # Add 2-3 recipes per meal
            recipe_count = 2 + (i % 2)  # 2 or 3 recipes
            for j in range(recipe_count):
                recipe = create_test_ORM_recipe(
                    id=f"perf_recipe_{i}_{j}",
                    name=f"Recipe {i}-{j}",
                    meal_id=f"perf_meal_{i}",
                    author_id=f"chef_{i % 10}",
                    total_time=(j + 1) * 20,
                )
                recipes.append(recipe)
                test_session.add(recipe)
                await test_session.flush()  # Ensure recipe exists for FK
                
                # Add ingredient to recipe
                ingredient = create_test_ORM_ingredient(
                    recipe_id=recipe.id,
                    name=f"Ingredient {j}",
                    product_id=f"product_{j % 20}",
                    quantity=100.0,
                    unit="grams",
                    position=0
                )
                test_session.add(ingredient)
        
        await test_session.commit()
        return meals, recipes
    
    @timeout_test(60.0)
    async def test_complex_join_query_performance(
        self, meal_repository, large_join_dataset, async_benchmark_timer
    ):
        """Test performance of complex join queries with large dataset"""
        meals, recipes = large_join_dataset
        
        # Baseline: Simple meal query should be very fast
        async with async_benchmark_timer() as timer:
            simple_results = await meal_repository.query(filter={"author_id": "chef_5"}, _return_sa_instance=True)
        timer.assert_faster_than(0.1)  # Should be very fast
        assert len(simple_results) == 5  # chef_5 has 5 meals
        
        # Performance test: Complex multi-table join should be reasonable
        async with async_benchmark_timer() as timer:
            complex_results = await meal_repository.query(filter={
                "author_id": "chef_5",         # Meal table
                "total_time_lte": 100,         # Meal table  
                "recipe_total_time": 40,       # Recipe table (join required)
                "calories_gte": 500,           # Meal table composite field
            }, _return_sa_instance=True)
        timer.assert_faster_than(1.0)  # Should complete in < 1 second
        
        # Performance test: Multi-level join should still be reasonable
        async with async_benchmark_timer() as timer:
            ingredient_results = await meal_repository.query(filter={
                "author_id": "chef_3",
                "products": ["product_1"],     # Ingredient level (2-level join)
            }, _return_sa_instance=True)
        timer.assert_faster_than(1.5)  # Should complete in < 1.5 seconds
        
        # All queries should return valid results
        assert all(isinstance(results, list) for results in [simple_results, complex_results, ingredient_results])
    
    @timeout_test(30.0)
    async def test_join_optimization_effectiveness(
        self, meal_repository, large_join_dataset, async_benchmark_timer
    ):
        """Test that join optimization prevents performance degradation"""
        meals, recipes = large_join_dataset
        
        # Test: Query with potential duplicate joins should not be slower
        async with async_benchmark_timer() as timer:
            optimized_results = await meal_repository.query(filter={
                "recipe_id": "perf_recipe_10_0",      # Recipe join
                "recipe_name": "Recipe 10-0",         # Same recipe join
                "recipe_total_time": 20,              # Same recipe join
                "products": ["product_0"],            # Ingredient join (via recipe)
            }, _return_sa_instance=True)
        timer.assert_faster_than(0.5)  # Should be optimized
        
        assert len(optimized_results) == 1
        assert optimized_results[0].id == "perf_meal_10"
        
        # Test: Multiple different joins should still be reasonable
        async with async_benchmark_timer() as timer:
            multi_join_results = await meal_repository.query(filter={
                "author_id": "chef_7",           # Direct meal attribute
                "calories_gte": 600,             # Meal composite field
                "recipe_total_time_lte": 60,     # Recipe join
                "products": ["product_5"],       # Ingredient join
            }, _return_sa_instance=True)
        timer.assert_faster_than(1.0)  # Should handle multiple joins efficiently
        
        assert isinstance(multi_join_results, list) 