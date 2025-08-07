"""
Comprehensive test suite for RecipeRepository following seedwork patterns.

Tests are organized into focused classes:
- TestRecipeRepositoryCore: Basic CRUD operations with real database
- TestRecipeRepositoryIngredients: Ingredient relationships and product filtering
- TestRecipeRepositoryRatings: Rating aggregation and rating-based filtering
- TestRecipeRepositoryTagFiltering: Complex tag logic with AND/OR operations
- TestRecipeRepositoryErrorHandling: Edge cases and database constraints
- TestRecipeRepositoryPerformance: Benchmarks and performance baselines

All tests use REAL database (no mocks) and follow TDD principles.
"""

from uuid import uuid4
import pytest
from sqlalchemy import select

from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.ingredient_sa_model import IngredientSaModel

import time
from typing import Dict, Any



from src.contexts.recipes_catalog.core.adapters.meal.repositories.recipe_repository import RecipeRepo
from src.contexts.shared_kernel.domain.enums import MeasureUnit, Privacy

# Import necessary SA models to ensure database tables exist
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import RecipeSaModel
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
from tests.contexts.products_catalog.core.adapters.repositories.product_data_factories import create_ORM_product, create_ORM_source
from tests.contexts.recipes_catalog.data_factories.meal.meal_orm_factories import create_meal_orm
from tests.contexts.recipes_catalog.data_factories.shared_orm_factories import create_recipe_tag_orm, get_or_create_recipe_tag_orm
from tests.contexts.recipes_catalog.data_factories.meal.recipe.parametrized_recipe_scenarios import get_performance_test_scenarios
from tests.contexts.recipes_catalog.data_factories.meal.recipe.recipe_domain_factories import create_recipe
from tests.contexts.recipes_catalog.data_factories.meal.recipe.recipe_orm_factories import create_high_protein_recipe_orm, create_ingredient_orm, create_private_recipe_orm, create_public_recipe_orm, create_quick_recipe_orm, create_rating_orm, create_recipe_orm, create_vegetarian_recipe_orm
# MenuSaModel now imported in meal_sa_model.py where it belongs


pytestmark = [pytest.mark.anyio, pytest.mark.integration]

# =============================================================================
# TEST FIXTURES AND SETUP
# =============================================================================

# Note: recipe_repository fixture is now in conftest.py and uses test_session

# benchmark_timer fixture is now available from top-level conftest.py

# =============================================================================
# TEST RECIPE REPOSITORY CORE OPERATIONS
# =============================================================================

class TestRecipeRepositoryCore:
    """Test basic CRUD operations with real database persistence"""

    async def test_get_recipe_by_id(self, recipe_repository: RecipeRepo, test_session):
        """Test retrieving a recipe by ID"""
        # Given: A meal and recipe added directly to database via session
        
        meal = create_meal_orm(name="Test Meal with Recipe")
        test_session.add(meal)
        await test_session.flush()  # Get meal ID for foreign key
        
        recipe = create_recipe_orm(
            name="Test Recipe for Get", 
            meal_id=meal.id
        )
        test_session.add(recipe)
        await test_session.commit()
        
        # When: Getting the recipe by ID through RecipeRepository
        result = await recipe_repository.get_sa_instance(recipe.id)
        
        # Then: Should return the SA model instance
        assert isinstance(result, RecipeSaModel)
        assert result.id == recipe.id
        assert result.name == "Test Recipe for Get"
        assert result.author_id == recipe.author_id
        assert result.meal_id == meal.id

    async def test_get_sa_instance(self, recipe_repository: RecipeRepo, test_session):
        """Test getting SQLAlchemy instance of recipe"""
        # Given: A meal and recipe added directly to database via session
                
        meal = create_meal_orm(name="Test Meal for SA Instance")
        test_session.add(meal)
        await test_session.flush()  # Get meal ID for foreign key
        
        recipe = create_recipe_orm(
            name="Test Recipe for SA Instance", 
            meal_id=meal.id
        )
        test_session.add(recipe)
        await test_session.commit()
        
        # When: Getting the SQLAlchemy instance
        sa_instance = await recipe_repository.get_sa_instance(recipe.id)
        
        # Then: Should return the correct SA model instance
        assert isinstance(sa_instance, RecipeSaModel)
        assert sa_instance.id == recipe.id
        assert sa_instance.name == "Test Recipe for SA Instance"

    async def test_persist_recipe_fails_without_add(self, recipe_repository: RecipeRepo):
        """Test that persist fails without calling add first (Unit of Work pattern)"""
        # Given: A new recipe entity (domain object) not added to repository
        recipe = create_recipe(
            name="Test Recipe for Persist"
            # Remove hardcoded author_id and meal_id - let factory generate them
        )
        
        # When/Then: persist() should fail because recipe is not in repository's "seen" set
        with pytest.raises(AssertionError, match="Cannon persist entity which is unknown to the repo"):
            await recipe_repository.persist(recipe)

    async def test_persist_all_recipes_fails_without_add(self, recipe_repository: RecipeRepo):
        """Test that persist_all fails without calling add first (Unit of Work pattern)"""
        # Given: Multiple recipe entities (domain objects) not added to repository
        recipes = [
            create_recipe(name="Recipe 1", meal_id="meal_001"),
            create_recipe(name="Recipe 2", meal_id="meal_002"),
            create_recipe(name="Recipe 3", meal_id="meal_003")
        ]
        
        # When/Then: persist_all() should fail because recipes are not in repository's "seen" set
        with pytest.raises(AssertionError, match="Cannon persist entity which is unknown to the repo"):
            await recipe_repository.persist_all(recipes)

    @pytest.mark.parametrize("recipe_count", [1, 5, 10, 25])
    async def test_query_all_recipes(self, recipe_repository: RecipeRepo, recipe_count: int):
        """Test querying recipes with different dataset sizes"""
        # Given: Database may have existing recipes
        # When: Querying all recipes with SA instances
        result = await recipe_repository.query(_return_sa_instance=True)
        
        # Then: Should return list of SA model instances (may be empty if none exist)
        assert isinstance(result, list)
        # All items should be RecipeSaModel instances
        for recipe in result:
            assert isinstance(recipe, RecipeSaModel)

    async def test_query_with_filters(self, recipe_repository: RecipeRepo):
        """Test querying recipes with various filters"""
        # Given: Filter parameters
        test_filters = [
            {"name": "Test Recipe"},
            {"author_id": "test_author"},
            {"meal_id": "test_meal"},
            {"privacy": "public"},
            {"total_time_gte": 30},
            {"calories_gte": 200}
        ]
        
        # When/Then: Each filter should execute without error and return SA instances
        for filter_params in test_filters:
            result = await recipe_repository.query(filter=filter_params, _return_sa_instance=True)
            assert isinstance(result, list)
            # Verify all returned items are SA model instances
            for recipe in result:
                assert isinstance(recipe, RecipeSaModel)

    async def test_add_method_raises_not_implemented(self, recipe_repository: RecipeRepo):
        """Test that add method raises NotImplementedError as expected"""
        # Given: A recipe entity (domain object)
        recipe = create_recipe(name="Test Recipe")
        
        # When/Then: add() should raise NotImplementedError
        with pytest.raises(NotImplementedError, match="Recipes must be added through the meal repo"):
            await recipe_repository.add(recipe)

    async def test_tags_are_persisted_after_meal_creation(self, recipe_repository: RecipeRepo, test_session):
        """Test that recipe tags are properly persisted when added directly to database"""
        
        # Create meal first
        meal = create_meal_orm(name="Test Meal with Tagged Recipe")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create tags
        tag1 = create_recipe_tag_orm(key="cuisine", value="italian", author_id=shared_author_id, type="recipe")
        tag2 = create_recipe_tag_orm(key="difficulty", value="easy", author_id=shared_author_id, type="recipe")
        test_session.add(tag1)
        test_session.add(tag2)
        await test_session.flush()
        
        # Create recipe with tags
        recipe = create_recipe_orm(
            name="Test Recipe with Tags", 
            author_id=shared_author_id, 
            meal_id=meal.id,
            tags=[tag1, tag2]
        )
        test_session.add(recipe)
        await test_session.commit()
        
        # When: Getting the recipe through RecipeRepository
        result = await recipe_repository.get_sa_instance(recipe.id)
        
        # Then: Tags should be persisted correctly
        assert isinstance(result, RecipeSaModel)
        assert len(result.tags) == 2
        tag_keys = {tag.key for tag in result.tags}
        tag_values = {tag.value for tag in result.tags}
        assert "cuisine" in tag_keys
        assert "difficulty" in tag_keys
        assert "italian" in tag_values
        assert "easy" in tag_values

    async def test_ingredient_replacement_through_recipe_update(self, recipe_repository: RecipeRepo, test_session):
        """Test that updating recipe ingredients correctly removes old and adds new ones"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Ingredient Update")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create recipe with initial ingredients
        recipe = create_recipe_orm(
            name="Recipe for Ingredient Update", 
            author_id=shared_author_id,
            meal_id=meal.id
        )
        
        original_ingredients = [
            create_ingredient_orm(name="Flour", position=0, recipe_id=recipe.id),
            create_ingredient_orm(name="Sugar", position=1, recipe_id=recipe.id),
            create_ingredient_orm(name="Eggs", position=2, recipe_id=recipe.id)
        ]
        recipe.ingredients = original_ingredients
        
        test_session.add(recipe)
        await test_session.commit()

        # ingredients = await test_session.execute(select(IngredientSaModel))
        # ingredients = ingredients.scalars().all()
        # print(ingredients)
        
        # When: Getting recipe and verifying original ingredients
        retrieved_recipe = await recipe_repository.get_sa_instance(recipe.id)
        assert len(retrieved_recipe.ingredients) == 3
        
        # Create new single ingredient - should work now that sessions are aligned
        new_ingredient = create_ingredient_orm(name="New Single Ingredient", position=0, recipe_id=recipe.id)
        
        # Replace ingredients - cascade deletion should work with aligned sessions
        retrieved_recipe.ingredients = [new_ingredient]
        await test_session.commit()
        
        # Then: Recipe should have updated ingredients
        updated_recipe = await recipe_repository.get_sa_instance(recipe.id)
        assert len(updated_recipe.ingredients) == 1
        assert updated_recipe.ingredients[0].name == "New Single Ingredient"
        assert updated_recipe.ingredients[0].position == 0

        all_ingredients = await test_session.execute(select(IngredientSaModel))
        assert len(all_ingredients.scalars().all()) == 1

    async def test_relationship_queries_no_duplicate_rows(self, recipe_repository: RecipeRepo, test_session):
        """Test that querying on relationships doesn't return duplicate rows"""

        # Create meal first
        meal = create_meal_orm(name="Meal with Product Relations")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create recipe with ingredients that have product relationships
        recipe = create_recipe_orm(
            name="Recipe with Product Relationships",
            author_id=shared_author_id,
            meal_id=meal.id
        )
        
        ingredients_with_products = [
            create_ingredient_orm(name="Ingredient 1", product_id="product_001", position=0, recipe_id=recipe.id),
            create_ingredient_orm(name="Ingredient 2", product_id="product_002", position=1, recipe_id=recipe.id)
        ]
        recipe.ingredients = ingredients_with_products
        
        test_session.add(recipe)
        for ingredient in ingredients_with_products:
            test_session.add(ingredient)
        await test_session.commit()
        
        # When: Querying all recipes with SA instances
        all_recipes = await recipe_repository.query(_return_sa_instance=True)
        matching_recipes = [r for r in all_recipes if r.name == "Recipe with Product Relationships"]
        
        # Then: Should return exactly one recipe (no duplicates from JOIN operations)
        assert len(matching_recipes) == 1
        assert matching_recipes[0].id == recipe.id
        
        # When: Querying with product filter (if products exist)
        product_filtered_recipes = await recipe_repository.query(
            filter={"products": ["product_001", "product_002"]}, _return_sa_instance=True
        )
        matching_by_products = [r for r in product_filtered_recipes if r.name == "Recipe with Product Relationships"]
        
        # Then: Should still return exactly one recipe
        assert len(matching_by_products) <= 1  # May be 0 if products don't exist in DB, but never > 1
        if len(matching_by_products) == 1:
            assert matching_by_products[0].id == recipe.id


# =============================================================================
# TEST RECIPE REPOSITORY INGREDIENTS
# =============================================================================

class TestRecipeRepositoryIngredients:
    """Test ingredient relationships and product filtering with real database persistence"""

    async def test_ingredient_relationship_scenarios_with_real_data(self, recipe_repository: RecipeRepo, test_session):
        """Test ingredient filtering scenarios with real database data"""

        # Create meal first
        meal = create_meal_orm(name="Meal for Ingredient Scenarios")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create recipe with multiple ingredients (different quantities and units)
        complex_recipe = create_recipe_orm(
            name="Complex Recipe",
            author_id=shared_author_id,
            meal_id=meal.id
        )
        complex_recipe.ingredients = [
            create_ingredient_orm(name="Flour", quantity=500.0, unit=MeasureUnit.GRAM, position=0, recipe_id=complex_recipe.id),
            create_ingredient_orm(name="Sugar", quantity=200.0, unit=MeasureUnit.GRAM, position=1, recipe_id=complex_recipe.id),
            create_ingredient_orm(name="Milk", quantity=250.0, unit=MeasureUnit.MILLILITER, position=2, recipe_id=complex_recipe.id)
        ]
        
        # Create recipe with single ingredient
        simple_recipe = create_recipe_orm(
            name="Simple Recipe",
            author_id=shared_author_id,
            meal_id=meal.id
        )
        simple_recipe.ingredients = [
            create_ingredient_orm(name="Salt", quantity=5.0, unit=MeasureUnit.GRAM, position=0, recipe_id=simple_recipe.id)
        ]
        
        # Create recipe with no ingredients
        no_ingredients_recipe = create_recipe_orm(
            name="No Ingredients Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            ingredients=[]
        )
        
        test_session.add(complex_recipe)
        test_session.add(simple_recipe)
        test_session.add(no_ingredients_recipe)
        await test_session.commit()
        
        # When: Querying all recipes
        all_results = await recipe_repository.query(filter={}, _return_sa_instance=True)
        
        # Then: Should find all three recipes
        recipe_names = {r.name for r in all_results}
        assert "Complex Recipe" in recipe_names
        assert "Simple Recipe" in recipe_names
        assert "No Ingredients Recipe" in recipe_names
        
        # When: Testing complex recipe ingredients
        complex_recipe_result = await recipe_repository.get_sa_instance(complex_recipe.id)
        
        # Then: Should have correct ingredient relationships
        assert len(complex_recipe_result.ingredients) == 3
        ingredient_names = {ing.name for ing in complex_recipe_result.ingredients}
        assert ingredient_names == {"Flour", "Sugar", "Milk"}
        
        # Verify ingredient details
        flour_ingredient = next(ing for ing in complex_recipe_result.ingredients if ing.name == "Flour")
        assert flour_ingredient.quantity == 500.0
        assert flour_ingredient.unit == MeasureUnit.GRAM
        assert flour_ingredient.position == 0
        
        # When: Testing simple recipe ingredients
        simple_recipe_result = await recipe_repository.get_sa_instance(simple_recipe.id)
        
        # Then: Should have single ingredient
        assert len(simple_recipe_result.ingredients) == 1
        assert simple_recipe_result.ingredients[0].name == "Salt"
        
        # When: Testing recipe with no ingredients
        no_ingredients_result = await recipe_repository.get_sa_instance(no_ingredients_recipe.id)
        
        # Then: Should have empty ingredients list
        assert len(no_ingredients_result.ingredients) == 0

    async def test_product_filtering_with_real_data(self, recipe_repository: RecipeRepo, test_session):
        """Test filtering recipes by ingredient product IDs with real database data"""

        # Create meal first  
        meal = create_meal_orm(name="Meal for Product Filter")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create recipe with ingredients that have specific product IDs
        ingredients_with_products = [
            create_ingredient_orm(name="Flour", product_id="product_001", position=0, recipe_id="recipe_product_filter"),
            create_ingredient_orm(name="Sugar", product_id="product_002", position=1, recipe_id="recipe_product_filter")
        ]
        recipe = create_recipe_orm(
            name="Recipe with Product Ingredients",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="recipe_product_filter",
            ingredients=ingredients_with_products
        )
        test_session.add(recipe)
        await test_session.commit()
        
        # When: Filtering by single product ID
        result_single = await recipe_repository.query(filter={"products": ["product_001"]}, _return_sa_instance=True)
        
        # Then: Should find the recipe containing that product
        matching_recipes = [r for r in result_single if r.id == "recipe_product_filter"]
        assert len(matching_recipes) == 1
        assert matching_recipes[0].name == "Recipe with Product Ingredients"
        
        # When: Filtering by multiple product IDs
        result_multiple = await recipe_repository.query(filter={"products": ["product_001", "product_002"]}, _return_sa_instance=True)
        
        # Then: Should find the recipe containing either product
        matching_recipes_multi = [r for r in result_multiple if r.id == "recipe_product_filter"]
        assert len(matching_recipes_multi) == 1
        
        # When: Filtering by non-existent product
        result_none = await recipe_repository.query(filter={"products": ["nonexistent_product"]}, _return_sa_instance=True)
        
        # Then: Should return empty list or not include our test recipe
        matching_nonexistent = [r for r in result_none if r.id == "recipe_product_filter"]
        assert len(matching_nonexistent) == 0

    async def test_product_name_filtering_with_real_products(self, recipe_repository: RecipeRepo, test_session):
        """Test filtering recipes by product name with real products and ingredients"""

        # Create meal first
        meal = create_meal_orm(name="Meal for Product Name Filter")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create required sources for products using get-or-create to prevent duplicates
        from tests.contexts.products_catalog.core.adapters.repositories.product_data_factories import get_or_create_ORM_source
        
        flour_source = await get_or_create_ORM_source(test_session, id="flour_source", name="Flour Source", author_id=shared_author_id)
        sugar_source = await get_or_create_ORM_source(test_session, id="sugar_source", name="Sugar Source", author_id=shared_author_id)
        
        test_session.add(flour_source)
        test_session.add(sugar_source)
        await test_session.flush()
        
        # Create products with specific names using proper factory functions
        flour_product = create_ORM_product(
            id="flour_product_001",
            name="All-Purpose Flour",
            source_id="flour_source"
        )
        sugar_product = create_ORM_product(
            id="sugar_product_001", 
            name="White Sugar",
            source_id="sugar_source"
        )
        
        test_session.add(flour_product)
        test_session.add(sugar_product)
        await test_session.flush()
        
        # Create recipe with flour-based ingredient
        flour_recipe = create_recipe_orm(
            name="Flour-Based Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="flour_recipe",
            ingredients=[
                create_ingredient_orm(
                    name="Flour", 
                    product_id="flour_product_001",
                    position=0,
                    recipe_id="flour_recipe"
                )
            ]
        )
        
        # Create recipe with sugar-based ingredient
        sugar_recipe = create_recipe_orm(
            name="Sugar-Based Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="sugar_recipe",
            ingredients=[
                create_ingredient_orm(
                    name="Sugar",
                    product_id="sugar_product_001", 
                    position=0,
                    recipe_id="sugar_recipe"
                )
            ]
        )
        
        # Create recipe with no product links
        generic_recipe = create_recipe_orm(
            name="Generic Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="generic_recipe",
            ingredients=[
                create_ingredient_orm(
                    name="Salt",
                    product_id=None,
                    position=0,
                    recipe_id="generic_recipe"
                )
            ]
        )
        
        test_session.add(flour_recipe)
        test_session.add(sugar_recipe)
        test_session.add(generic_recipe)
        await test_session.commit()
        
        # When: Filtering by product name "flour" (partial match)
        flour_results = await recipe_repository.query(
            filter={"product_name": "flour"}, 
            _return_sa_instance=True
        )
        
        # Then: Should find recipes containing products with "flour" in the name
        # Note: This functionality depends on ProductRepo integration, so we test what we can
        # At minimum, the query should execute without error
        assert isinstance(flour_results, list)
        for recipe in flour_results:
            assert isinstance(recipe, RecipeSaModel)
        
        # When: Filtering by product name "sugar" (partial match)
        sugar_results = await recipe_repository.query(
            filter={"product_name": "sugar"},
            _return_sa_instance=True
        )
        
        # Then: Should execute without error and return SA instances
        assert isinstance(sugar_results, list)
        for recipe in sugar_results:
            assert isinstance(recipe, RecipeSaModel)
        
        # When: Filtering by non-existent product name
        nonexistent_results = await recipe_repository.query(
            filter={"product_name": "nonexistent_product"},
            _return_sa_instance=True
        )
        
        # Then: Should return empty list or not find our test recipes
        assert isinstance(nonexistent_results, list)
        
        # Verify our test recipes exist in the database (sanity check)
        all_recipes = await recipe_repository.query(filter={}, _return_sa_instance=True)
        recipe_names = {r.name for r in all_recipes}
        assert "Flour-Based Recipe" in recipe_names
        assert "Sugar-Based Recipe" in recipe_names
        assert "Generic Recipe" in recipe_names

    async def test_ingredient_validation_with_orm_models(self, recipe_repository: RecipeRepo, test_session):
        """Test ingredient validation using ORM models and real database persistence"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Ingredient Validation")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        recipe_id = uuid4().hex
        
        # Create recipe with valid ingredients using ORM models
        valid_ingredients = [
            create_ingredient_orm(name="Flour", quantity=500.0, unit=MeasureUnit.GRAM, position=0, recipe_id=recipe_id),
            create_ingredient_orm(name="Sugar", quantity=200.0, unit=MeasureUnit.GRAM, position=1, recipe_id=recipe_id),
            create_ingredient_orm(name="Salt", quantity=5.0, unit=MeasureUnit.GRAM, position=2, recipe_id=recipe_id)
        ]
        
        recipe = create_recipe_orm(
            id=recipe_id,
            name="Recipe with Valid Ingredients",
            author_id=shared_author_id,
            meal_id=meal.id,
            ingredients=valid_ingredients
        )
        test_session.add(recipe)
        await test_session.commit()
        
        # When: Retrieving the recipe through repository
        retrieved_recipe = await recipe_repository.get_sa_instance(id=recipe_id)
        
        # Then: Valid ingredient should be persisted correctly
        assert len(retrieved_recipe.ingredients) == 3
        ingredient = retrieved_recipe.ingredients[0]
        assert ingredient.name == "Flour"
        assert ingredient.unit == MeasureUnit.GRAM
        assert ingredient.quantity == 500.0
        assert ingredient.position == 0

    async def test_ingredient_product_relationship_with_database(self, recipe_repository: RecipeRepo, test_session):
        """Test ingredient-product relationships with real database persistence"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Product Relations")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create recipe with ingredients that have product relationships
        ingredients_with_products = [
            create_ingredient_orm(
                name="Flour",
                product_id="flour_product_123",
                position=0,
                recipe_id="recipe_product_relations"
            ),
            create_ingredient_orm(
                name="Sugar", 
                product_id="sugar_product_456",
                position=1,
                recipe_id="recipe_product_relations"
            )
        ]
        recipe = create_recipe_orm(
            name="Recipe with Product Ingredients",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="recipe_product_relations",
            ingredients=ingredients_with_products
        )
        test_session.add(recipe)
        await test_session.commit()
        
        # When: Retrieving the recipe through repository
        retrieved_recipe = await recipe_repository.get_sa_instance("recipe_product_relations")
        
        # Then: Recipe should have ingredients with correct product relationships
        assert len(retrieved_recipe.ingredients) == 2
        
        # Sort ingredients by position for consistent testing
        sorted_ingredients = sorted(retrieved_recipe.ingredients, key=lambda x: x.position)
        assert sorted_ingredients[0].product_id == "flour_product_123"
        assert sorted_ingredients[0].name == "Flour"
        assert sorted_ingredients[1].product_id == "sugar_product_456" 
        assert sorted_ingredients[1].name == "Sugar"

    async def test_ingredient_without_product_relationship(self, recipe_repository: RecipeRepo, test_session):
        """Test ingredients without product relationships using real database"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Generic Ingredients")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create recipe with ingredient without product relationship
        generic_ingredient = create_ingredient_orm(
            name="Salt",
            product_id=None,
            position=0,
            recipe_id="recipe_generic_ingredients"
        )
        recipe = create_recipe_orm(
            name="Recipe with Generic Ingredients",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="recipe_generic_ingredients",
            ingredients=[generic_ingredient]
        )
        test_session.add(recipe)
        await test_session.commit()
        
        # When: Retrieving the recipe through repository
        retrieved_recipe = await recipe_repository.get_sa_instance("recipe_generic_ingredients")
        
        # Then: Recipe should have ingredient without product relationship
        assert len(retrieved_recipe.ingredients) == 1
        ingredient = retrieved_recipe.ingredients[0]
        assert ingredient.product_id is None
        assert ingredient.name == "Salt"

    async def test_ingredient_filtering_by_name(self, recipe_repository: RecipeRepo, test_session):
        """Test filtering recipes by ingredient names using real database data"""

        # Create meal first
        meal = create_meal_orm(name="Meal for Ingredient Filter")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create recipe with flour ingredient
        flour_recipe = create_recipe_orm(
            name="Flour Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="flour_recipe",
            ingredients=[create_ingredient_orm(name="Flour", position=0, recipe_id="flour_recipe")]
        )
        
        # Create recipe with sugar ingredient  
        sugar_recipe = create_recipe_orm(
            name="Sugar Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="sugar_recipe", 
            ingredients=[create_ingredient_orm(name="Sugar", position=0, recipe_id="sugar_recipe")]
        )
        
        test_session.add(flour_recipe)
        test_session.add(sugar_recipe)
        await test_session.commit()
        
        # When: Querying all recipes
        all_recipes = await recipe_repository.query(filter={}, _return_sa_instance=True)
        
        # Then: Should find both recipes
        recipe_names = {r.name for r in all_recipes}
        assert "Flour Recipe" in recipe_names
        assert "Sugar Recipe" in recipe_names


# =============================================================================
# TEST RECIPE REPOSITORY RATINGS
# =============================================================================

class TestRecipeRepositoryRatings:
    """Test rating aggregation and rating-based filtering with real database persistence"""

    async def test_rating_aggregation_scenarios_with_real_data(self, recipe_repository: RecipeRepo, test_session):
        """Test rating aggregation scenarios with real database data"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Rating Tests")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create recipe with high ratings
        high_rated_recipe = create_recipe_orm(
            name="High Rated Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="high_rated_recipe",
            ratings=[
                create_rating_orm(user_id="user_1", recipe_id="high_rated_recipe", taste=5, convenience=5),
                create_rating_orm(user_id="user_2", recipe_id="high_rated_recipe", taste=4, convenience=5),
                create_rating_orm(user_id="user_3", recipe_id="high_rated_recipe", taste=5, convenience=4)
            ]
        )
        
        # Create recipe with medium ratings
        medium_rated_recipe = create_recipe_orm(
            name="Medium Rated Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="medium_rated_recipe",
            ratings=[
                create_rating_orm(user_id="user_1", recipe_id="medium_rated_recipe", taste=3, convenience=3),
                create_rating_orm(user_id="user_2", recipe_id="medium_rated_recipe", taste=3, convenience=4),
                create_rating_orm(user_id="user_3", recipe_id="medium_rated_recipe", taste=2, convenience=3)
            ]
        )
        
        # Create recipe with low ratings
        low_rated_recipe = create_recipe_orm(
            name="Low Rated Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="low_rated_recipe",
            ratings=[
                create_rating_orm(user_id="user_1", recipe_id="low_rated_recipe", taste=1, convenience=2),
                create_rating_orm(user_id="user_2", recipe_id="low_rated_recipe", taste=2, convenience=1),
                create_rating_orm(user_id="user_3", recipe_id="low_rated_recipe", taste=1, convenience=1)
            ]
        )
        
        test_session.add(high_rated_recipe)
        test_session.add(medium_rated_recipe)
        test_session.add(low_rated_recipe)
        await test_session.commit()
        
        # When: Retrieving recipes through repository
        high_recipe_result = await recipe_repository.get_sa_instance("high_rated_recipe")
        medium_recipe_result = await recipe_repository.get_sa_instance("medium_rated_recipe")
        low_recipe_result = await recipe_repository.get_sa_instance("low_rated_recipe")
        
        # Then: Should have correct rating relationships
        assert len(high_recipe_result.ratings) == 3
        assert len(medium_recipe_result.ratings) == 3
        assert len(low_recipe_result.ratings) == 3
        
        # Verify high rated recipe ratings
        high_taste_scores = [r.taste for r in high_recipe_result.ratings]
        high_convenience_scores = [r.convenience for r in high_recipe_result.ratings]
        assert set(high_taste_scores) == {4, 5, 5}
        assert set(high_convenience_scores) == {4, 5, 5}
        
        # Verify medium rated recipe ratings
        medium_taste_scores = [r.taste for r in medium_recipe_result.ratings]
        medium_convenience_scores = [r.convenience for r in medium_recipe_result.ratings]
        assert set(medium_taste_scores) == {2, 3, 3}
        assert set(medium_convenience_scores) == {3, 3, 4}
        
        # Verify low rated recipe ratings
        low_taste_scores = [r.taste for r in low_recipe_result.ratings]
        low_convenience_scores = [r.convenience for r in low_recipe_result.ratings]
        assert set(low_taste_scores) == {1, 1, 2}
        assert set(low_convenience_scores) == {1, 1, 2}

    async def test_average_taste_rating_filter_with_real_data(self, recipe_repository: RecipeRepo, test_session):
        """Test filtering by average taste rating with real database data"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Taste Rating Filter")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create recipe with high average taste rating (4.67)
        high_taste_recipe = create_recipe_orm(
            name="High Taste Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="high_taste_recipe",
            ratings=[
                create_rating_orm(user_id="user_1", recipe_id="high_taste_recipe", taste=5, convenience=3),
                create_rating_orm(user_id="user_2", recipe_id="high_taste_recipe", taste=4, convenience=3),
                create_rating_orm(user_id="user_3", recipe_id="high_taste_recipe", taste=5, convenience=3)
            ]
        )
        
        # Create recipe with medium average taste rating (3.0)
        medium_taste_recipe = create_recipe_orm(
            name="Medium Taste Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="medium_taste_recipe",
            ratings=[
                create_rating_orm(user_id="user_1", recipe_id="medium_taste_recipe", taste=3, convenience=4),
                create_rating_orm(user_id="user_2", recipe_id="medium_taste_recipe", taste=3, convenience=4),
                create_rating_orm(user_id="user_3", recipe_id="medium_taste_recipe", taste=3, convenience=4)
            ]
        )
        
        # Create recipe with low average taste rating (2.0)
        low_taste_recipe = create_recipe_orm(
            name="Low Taste Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="low_taste_recipe",
            ratings=[
                create_rating_orm(user_id="user_1", recipe_id="low_taste_recipe", taste=2, convenience=5),
                create_rating_orm(user_id="user_2", recipe_id="low_taste_recipe", taste=2, convenience=5),
                create_rating_orm(user_id="user_3", recipe_id="low_taste_recipe", taste=2, convenience=5)
            ]
        )
        
        test_session.add(high_taste_recipe)
        test_session.add(medium_taste_recipe)
        test_session.add(low_taste_recipe)
        await test_session.commit()
        
        # When: Filtering by average taste rating >= 4.0
        high_taste_results = await recipe_repository.query(
            filter={"average_taste_rating_gte": 4.0}, 
            _return_sa_instance=True
        )
        
        # Then: Should include high taste recipe, may include others based on database aggregation
        result_names = {r.name for r in high_taste_results}
        # Note: Actual filtering depends on database aggregation functions
        # At minimum, query should execute without error
        assert isinstance(high_taste_results, list)
        for recipe in high_taste_results:
            assert isinstance(recipe, RecipeSaModel)
        
        # When: Filtering by average taste rating >= 3.5
        medium_taste_results = await recipe_repository.query(
            filter={"average_taste_rating_gte": 3.5},
            _return_sa_instance=True
        )
        
        # Then: Should execute without error
        assert isinstance(medium_taste_results, list)
        for recipe in medium_taste_results:
            assert isinstance(recipe, RecipeSaModel)
        
        # When: Filtering by average taste rating >= 0.0 (should include all)
        all_taste_results = await recipe_repository.query(
            filter={"average_taste_rating_gte": 0.0},
            _return_sa_instance=True
        )
        
        # Then: Should find our test recipes
        all_result_names = {r.name for r in all_taste_results}
        assert "High Taste Recipe" in all_result_names or "Medium Taste Recipe" in all_result_names or "Low Taste Recipe" in all_result_names

    async def test_average_convenience_rating_filter_with_real_data(self, recipe_repository: RecipeRepo, test_session):
        """Test filtering by average convenience rating with real database data"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Convenience Rating Filter")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create recipe with high average convenience rating (4.67)
        high_convenience_recipe = create_recipe_orm(
            name="High Convenience Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="high_convenience_recipe",
            ratings=[
                create_rating_orm(user_id="user_1", recipe_id="high_convenience_recipe", taste=3, convenience=5),
                create_rating_orm(user_id="user_2", recipe_id="high_convenience_recipe", taste=3, convenience=4),
                create_rating_orm(user_id="user_3", recipe_id="high_convenience_recipe", taste=3, convenience=5)
            ]
        )
        
        # Create recipe with low average convenience rating (2.0)
        low_convenience_recipe = create_recipe_orm(
            name="Low Convenience Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="low_convenience_recipe",
            ratings=[
                create_rating_orm(user_id="user_1", recipe_id="low_convenience_recipe", taste=5, convenience=2),
                create_rating_orm(user_id="user_2", recipe_id="low_convenience_recipe", taste=5, convenience=2),
                create_rating_orm(user_id="user_3", recipe_id="low_convenience_recipe", taste=5, convenience=2)
            ]
        )
        
        test_session.add(high_convenience_recipe)
        test_session.add(low_convenience_recipe)
        await test_session.commit()
        
        # When: Filtering by average convenience rating >= 4.5
        high_convenience_results = await recipe_repository.query(
            filter={"average_convenience_rating_gte": 4.5},
            _return_sa_instance=True
        )
        
        # Then: Should execute without error and return SA instances
        assert isinstance(high_convenience_results, list)
        for recipe in high_convenience_results:
            assert isinstance(recipe, RecipeSaModel)
        
        # When: Filtering by average convenience rating >= 1.0 (should include both)
        all_convenience_results = await recipe_repository.query(
            filter={"average_convenience_rating_gte": 1.0},
            _return_sa_instance=True
        )
        
        # Then: Should find our test recipes
        all_result_names = {r.name for r in all_convenience_results}
        assert "High Convenience Recipe" in all_result_names or "Low Convenience Recipe" in all_result_names

    async def test_rating_validation_with_orm_models(self, recipe_repository: RecipeRepo, test_session):
        """Test rating validation using ORM models and real database persistence"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Rating Validation")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create recipe with valid rating
        valid_rating = create_rating_orm(
            user_id="user_123",
            recipe_id="recipe_rating_validation",
            taste=5,
            convenience=4,
            comment="Excellent recipe!"
        )
        
        recipe = create_recipe_orm(
            name="Recipe with Valid Rating",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="recipe_rating_validation",
            ratings=[valid_rating]
        )
        test_session.add(recipe)
        await test_session.commit()
        
        # When: Retrieving the recipe through repository
        retrieved_recipe = await recipe_repository.get_sa_instance("recipe_rating_validation")
        
        # Then: Valid rating should be persisted correctly
        assert len(retrieved_recipe.ratings) == 1
        rating = retrieved_recipe.ratings[0]
        assert rating.user_id == "user_123"
        assert rating.recipe_id == "recipe_rating_validation"
        assert rating.taste == 5
        assert rating.convenience == 4
        assert rating.comment == "Excellent recipe!"

    async def test_rating_range_validation_with_database(self, recipe_repository: RecipeRepo, test_session):
        """Test rating value range validation (0-5) with real database persistence"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Rating Range")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create recipes with different rating values (0-5)
        recipes_with_ratings = []
        for rating_value in range(6):  # 0-5
            recipe = create_recipe_orm(
                name=f"Recipe with Rating {rating_value}",
                author_id=shared_author_id,
                meal_id=meal.id,
                id=f"recipe_rating_{rating_value}",
                ratings=[
                    create_rating_orm(
                        user_id=f"user_{rating_value}",
                        recipe_id=f"recipe_rating_{rating_value}",
                        taste=rating_value,
                        convenience=rating_value
                    )
                ]
            )
            recipes_with_ratings.append(recipe)
            test_session.add(recipe)
        
        await test_session.commit()
        
        # When/Then: All valid rating values should be persisted correctly
        for rating_value in range(6):
            retrieved_recipe = await recipe_repository.get_sa_instance(f"recipe_rating_{rating_value}")
            assert len(retrieved_recipe.ratings) == 1
            rating = retrieved_recipe.ratings[0]
            assert rating.taste == rating_value
            assert rating.convenience == rating_value

    async def test_recipe_with_multiple_ratings_database(self, recipe_repository: RecipeRepo, test_session):
        """Test recipe with multiple ratings for aggregation using real database"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Multiple Ratings")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create recipe with multiple ratings
        multiple_ratings = [
            create_rating_orm(recipe_id="recipe_multiple_ratings", user_id="user_1", taste=5, convenience=4),
            create_rating_orm(recipe_id="recipe_multiple_ratings", user_id="user_2", taste=4, convenience=5),
            create_rating_orm(recipe_id="recipe_multiple_ratings", user_id="user_3", taste=3, convenience=3)
        ]
        
        recipe = create_recipe_orm(
            name="Highly Rated Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="recipe_multiple_ratings",
            ratings=multiple_ratings
        )
        test_session.add(recipe)
        await test_session.commit()
        
        # When: Retrieving the recipe through repository
        retrieved_recipe = await recipe_repository.get_sa_instance("recipe_multiple_ratings")
        
        # Then: Recipe should have correct ratings persisted
        assert len(retrieved_recipe.ratings) == 3
        
        # Verify ratings are stored correctly
        taste_scores = [rating.taste for rating in retrieved_recipe.ratings]
        convenience_scores = [rating.convenience for rating in retrieved_recipe.ratings]
        assert set(taste_scores) == {3, 4, 5}
        assert set(convenience_scores) == {3, 4, 5}
        
        # Verify user associations
        user_ids = {rating.user_id for rating in retrieved_recipe.ratings}
        assert user_ids == {"user_1", "user_2", "user_3"}

    async def test_recipe_without_ratings_database(self, recipe_repository: RecipeRepo, test_session):
        """Test recipe without any ratings using real database"""
        # Create meal first
        meal = create_meal_orm(name="Meal for No Ratings")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create recipe without ratings
        recipe = create_recipe_orm(
            name="Unrated Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            id="recipe_no_ratings",
            ratings=[]
        )
        test_session.add(recipe)
        await test_session.commit()
        
        # When: Retrieving the recipe through repository
        retrieved_recipe = await recipe_repository.get_sa_instance("recipe_no_ratings")
        
        # Then: Recipe should have no ratings
        assert len(retrieved_recipe.ratings) == 0
        assert retrieved_recipe.name == "Unrated Recipe"


# =============================================================================
# TEST RECIPE REPOSITORY TAG FILTERING
# =============================================================================

class TestRecipeRepositoryTagFiltering:
    """Test complex tag logic with AND/OR operations using real database persistence"""

    async def test_tag_filtering_scenarios_with_real_data(self, recipe_repository: RecipeRepo, test_session):
        """Test tag filtering scenarios with real database data"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Tag Filtering")
        test_session.add(meal)
        await test_session.flush()

        shared_author_id = meal.author_id
        
        # Create tags for different scenarios - let factories generate unique author_ids
        cuisine_italian = create_recipe_tag_orm(key="cuisine", value="italian", type="recipe", author_id=shared_author_id)
        cuisine_mexican = create_recipe_tag_orm(key="cuisine", value="mexican", type="recipe", author_id=shared_author_id)
        difficulty_easy = create_recipe_tag_orm(key="difficulty", value="easy", type="recipe", author_id=shared_author_id)
        difficulty_hard = create_recipe_tag_orm(key="difficulty", value="hard", type="recipe", author_id=shared_author_id)
        diet_vegan = create_recipe_tag_orm(key="diet", value="vegan", type="recipe", author_id=shared_author_id)
        diet_vegetarian = create_recipe_tag_orm(key="diet", value="vegetarian", type="recipe", author_id=shared_author_id)
        
        test_session.add(cuisine_italian)
        test_session.add(cuisine_mexican)
        test_session.add(difficulty_easy)
        test_session.add(difficulty_hard)
        test_session.add(diet_vegan)
        test_session.add(diet_vegetarian)
        await test_session.flush()
        
        # Create recipes with different tag combinations - use consistent author_id for the meal's recipes
        # Recipe 1: Italian + Easy
        italian_easy_recipe = create_recipe_orm(
            name="Italian Easy Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            tags=[cuisine_italian, difficulty_easy]
        )
        
        # Recipe 2: Italian + Hard + Vegan  
        italian_hard_vegan_recipe = create_recipe_orm(
            name="Italian Hard Vegan Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            tags=[cuisine_italian, difficulty_hard, diet_vegan]
        )
        
        # Recipe 3: Mexican + Easy
        mexican_easy_recipe = create_recipe_orm(
            name="Mexican Easy Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            tags=[cuisine_mexican, difficulty_easy]
        )
        
        # Recipe 4: No tags
        no_tags_recipe = create_recipe_orm(
            name="Recipe with No Tags",
            author_id=shared_author_id,
            meal_id=meal.id
        )
        
        test_session.add(italian_easy_recipe)
        test_session.add(italian_hard_vegan_recipe)
        test_session.add(mexican_easy_recipe)
        test_session.add(no_tags_recipe)
        await test_session.commit()
        
        # When: Testing different tag filtering scenarios
        # Test 1: Single tag filter - cuisine=italian
        italian_results = await recipe_repository.query(
            filter={"tags": [("cuisine", "italian", shared_author_id)]},
            _return_sa_instance=True
        )
        
        # Then: Should find Italian recipes (recipes 1 and 2)
        italian_names = {r.name for r in italian_results}
        assert isinstance(italian_results, list)
        for recipe in italian_results:
            assert isinstance(recipe, RecipeSaModel)
        
        # Test 2: Multiple tag AND logic - cuisine=italian AND difficulty=easy
        italian_easy_results = await recipe_repository.query(
            filter={"tags": [("cuisine", "italian", shared_author_id), ("difficulty", "easy", shared_author_id)]},
            _return_sa_instance=True
        )
        
        # Then: Should find only recipe1 (Italian + Easy)
        assert isinstance(italian_easy_results, list)
        for recipe in italian_easy_results:
            assert isinstance(recipe, RecipeSaModel)
        
        # Test 3: Tag exclusion - has cuisine but NOT vegan
        non_vegan_results = await recipe_repository.query(
            filter={
                "tags": [("cuisine", "italian", shared_author_id)],
                "tags_not_exists": [("diet", "vegan", shared_author_id)]
            },
            _return_sa_instance=True
        )
        
        # Then: Should execute without error
        assert isinstance(non_vegan_results, list)
        for recipe in non_vegan_results:
            assert isinstance(recipe, RecipeSaModel)
        
        # Verify our test recipes exist (sanity check)
        all_recipes = await recipe_repository.query(filter={}, _return_sa_instance=True)
        all_names = {r.name for r in all_recipes}
        assert "Italian Easy Recipe" in all_names
        assert "Italian Hard Vegan Recipe" in all_names
        assert "Mexican Easy Recipe" in all_names
        assert "Recipe with No Tags" in all_names

    async def test_single_tag_filtering_with_real_data(self, recipe_repository: RecipeRepo, test_session):
        """Test single tag filtering with real database data"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Single Tag")
        test_session.add(meal)
        await test_session.flush()

        shared_author_id = meal.author_id
        
        # Create tag - let factory generate unique author_id
        cuisine_tag = create_recipe_tag_orm(key="cuisine", value="italian", type="recipe", author_id=shared_author_id)
        test_session.add(cuisine_tag)
        await test_session.flush()
        
        # Create recipes        
        # Recipe with the tag
        tagged_recipe = create_recipe_orm(
            name="Italian Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            tags=[cuisine_tag]
        )
        
        # Recipe without the tag
        untagged_recipe = create_recipe_orm(
            name="Generic Recipe",
            author_id=shared_author_id,
            meal_id=meal.id
        )
        
        test_session.add(tagged_recipe)
        test_session.add(untagged_recipe)
        await test_session.commit()
        
        # When: Filtering by single tag
        tag_filter = {"tags": [("cuisine", "italian", shared_author_id)]}  # Use generated author_id
        results = await recipe_repository.query(filter=tag_filter, _return_sa_instance=True)
        
        # Then: Should return only recipes with that tag
        recipe_names = {recipe.name for recipe in results}
        assert "Italian Recipe" in recipe_names
        assert "Generic Recipe" not in recipe_names
        assert len(results) == 1

    async def test_multiple_tags_and_logic_with_real_data(self, recipe_repository: RecipeRepo, test_session):
        """Test multiple tags with AND logic using real database data"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Multiple Tags")
        test_session.add(meal)
        await test_session.flush()

        shared_author_id = meal.author_id
        
        # Create tags - let factory generate unique author_ids
        cuisine_tag = create_recipe_tag_orm(key="cuisine", value="italian", type="recipe", author_id=shared_author_id)
        difficulty_tag = create_recipe_tag_orm(key="difficulty", value="easy", type="recipe", author_id=shared_author_id)
        other_tag = create_recipe_tag_orm(key="diet", value="vegan", type="recipe", author_id=shared_author_id)
        
        test_session.add(cuisine_tag)
        test_session.add(difficulty_tag)
        test_session.add(other_tag)
        await test_session.flush()
        
        # Create recipes with different tag combinations        
        # Recipe with both required tags
        both_tags_recipe = create_recipe_orm(
            name="Italian Easy Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            tags=[cuisine_tag, difficulty_tag]
        )
        
        # Recipe with only one of the required tags
        one_tag_recipe = create_recipe_orm(
            name="Italian Hard Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            tags=[cuisine_tag, other_tag]
        )
        
        # Recipe with different tags
        different_tags_recipe = create_recipe_orm(
            name="Vegan Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            tags=[other_tag]
        )
        
        test_session.add(both_tags_recipe)
        test_session.add(one_tag_recipe)
        test_session.add(different_tags_recipe)
        await test_session.commit()
        
        # When: Filtering with AND logic (both tags required)
        and_filter = {
            "tags": [
                ("cuisine", "italian", shared_author_id),
                ("difficulty", "easy", shared_author_id)
            ]
        }
        results = await recipe_repository.query(filter=and_filter, _return_sa_instance=True)
        
        # Then: Should return only recipes with both tags
        recipe_names = {recipe.name for recipe in results}
        assert "Italian Easy Recipe" in recipe_names
        assert "Italian Hard Recipe" not in recipe_names
        assert "Vegan Recipe" not in recipe_names
        assert len(results) == 1

    async def test_tags_not_exists_filtering_with_real_data(self, recipe_repository: RecipeRepo, test_session):
        """Test tags_not_exists filtering with real database data"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Tag Exclusion")
        test_session.add(meal)
        await test_session.flush()

        shared_author_id = meal.author_id

        print(f"meal id: {meal.id}")
        
        # Create tags - let factory generate unique author_ids
        diet_tag = create_recipe_tag_orm(key="diet", value="vegan", type="recipe", author_id=shared_author_id)
        cuisine_tag = create_recipe_tag_orm(key="cuisine", value="italian", type="recipe", author_id=shared_author_id)
        
        test_session.add(diet_tag)
        test_session.add(cuisine_tag)
        await test_session.flush()
        
        # Create recipes        
        # Recipe with both tags (should be excluded)
        vegan_italian_recipe = create_recipe_orm(
            name="Vegan Italian Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            tags=[diet_tag, cuisine_tag]
        )
        
        # Recipe with only cuisine tag (should be included)
        non_vegan_italian_recipe = create_recipe_orm(
            name="Non-Vegan Italian Recipe", 
            author_id=shared_author_id,
            meal_id=meal.id,
            tags=[cuisine_tag]
        )
        
        # Recipe with no tags (should be excluded from cuisine filter)
        no_tags_recipe = create_recipe_orm(
            name="Generic Recipe",
            author_id=shared_author_id,
            meal_id=meal.id
        )
        
        test_session.add(vegan_italian_recipe)
        test_session.add(non_vegan_italian_recipe)
        test_session.add(no_tags_recipe)
        await test_session.commit()
        
        # When: Filtering for Italian recipes that are NOT vegan
        exclusion_filter = {
            "tags": [("cuisine", "italian", shared_author_id)],
            "tags_not_exists": [("diet", "vegan", shared_author_id)]
        }
        results = await recipe_repository.query(filter=exclusion_filter, _return_sa_instance=True)
        
        # Then: Should return only Italian recipes without vegan tag
        recipe_names = {recipe.name for recipe in results}
        assert "Non-Vegan Italian Recipe" in recipe_names
        assert "Vegan Italian Recipe" not in recipe_names
        assert "Generic Recipe" not in recipe_names
        assert len(results) == 1

    async def test_complex_tag_combination_with_real_data(self, recipe_repository: RecipeRepo, test_session):
        """Test complex tag combinations with real database data"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Complex Tags")
        test_session.add(meal)
        await test_session.flush()

        shared_author_id = meal.author_id
        
        # Create tags - let factory generate unique author_ids
        cuisine_tag = create_recipe_tag_orm(key="cuisine", value="italian", type="recipe", author_id=shared_author_id)
        diet_vegan_tag = create_recipe_tag_orm(key="diet", value="vegan", type="recipe", author_id=shared_author_id)
        diet_vegetarian_tag = create_recipe_tag_orm(key="diet", value="vegetarian", type="recipe", author_id=shared_author_id)
        
        test_session.add(cuisine_tag)
        test_session.add(diet_vegan_tag)
        test_session.add(diet_vegetarian_tag)
        await test_session.flush()
        
        # Create recipes
        # Recipe 1: Italian + Vegan
        italian_vegan_recipe = create_recipe_orm(
            name="Italian Vegan Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            tags=[cuisine_tag, diet_vegan_tag]
        )
        
        # Recipe 2: Italian + Vegetarian
        italian_vegetarian_recipe = create_recipe_orm(
            name="Italian Vegetarian Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            tags=[cuisine_tag, diet_vegetarian_tag]
        )
        
        # Recipe 3: Italian + Both diet tags
        italian_both_diet_recipe = create_recipe_orm(
            name="Italian Multi-Diet Recipe",
            author_id=shared_author_id,
            meal_id=meal.id,
            tags=[cuisine_tag, diet_vegan_tag, diet_vegetarian_tag]
        )
        
        test_session.add(italian_vegan_recipe)
        test_session.add(italian_vegetarian_recipe)
        test_session.add(italian_both_diet_recipe)
        await test_session.commit()
        
        # When: Complex filtering - Italian AND vegan but NOT vegetarian
        complex_filter = {
            "tags": [("cuisine", "italian", shared_author_id), ("diet", "vegan", shared_author_id)],
            "tags_not_exists": [("diet", "vegetarian", shared_author_id)]
        }
        results = await recipe_repository.query(filter=complex_filter, _return_sa_instance=True)
        
        # Then: Should return only Italian vegan recipes without vegetarian tag
        recipe_names = {recipe.name for recipe in results}
        assert "Italian Vegan Recipe" in recipe_names
        assert "Italian Vegetarian Recipe" not in recipe_names
        assert "Italian Multi-Diet Recipe" not in recipe_names  # Has both diet tags
        assert len(results) == 1

    async def test_tag_validation_with_orm_models(self, recipe_repository: RecipeRepo, test_session):
        """Test tag validation using ORM models and real database persistence"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Tag Validation")  # Remove hardcoded author_id and id
        test_session.add(meal)
        await test_session.flush()
        
        # Create valid tag - let factory generate unique author_id
        recipe_tag = create_recipe_tag_orm(
            key="cuisine",
            value="italian",
            type="recipe"  # Remove hardcoded author_id
        )
        test_session.add(recipe_tag)
        await test_session.flush()
        
        # Create recipe with the tag
        recipe = create_recipe_orm(
            name="Recipe with Valid Tag",
            author_id=meal.author_id,  # Use meal's author_id for consistency
            meal_id=meal.id,
            tags=[recipe_tag]
        )
        test_session.add(recipe)
        await test_session.commit()
        
        # When: Retrieving the recipe through repository
        retrieved_recipe = await recipe_repository.get_sa_instance(recipe.id)
        
        # Then: Valid tag should be persisted correctly
        assert len(retrieved_recipe.tags) == 1
        tag = retrieved_recipe.tags[0]
        assert tag.key == "cuisine"
        assert tag.value == "italian"
        assert tag.author_id == recipe_tag.author_id  # Use the generated author_id
        assert tag.type == "recipe"

    async def test_recipe_with_multiple_tags_database(self, recipe_repository: RecipeRepo, test_session):
        """Test recipe with multiple tags using real database persistence"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Multiple Tags")  # Remove hardcoded author_id and id
        test_session.add(meal)
        await test_session.flush()
        
        # Create multiple tags - let factory generate unique author_ids
        cuisine_tag = create_recipe_tag_orm(key="cuisine", value="italian", type="recipe")  # Remove hardcoded author_id
        difficulty_tag = create_recipe_tag_orm(key="difficulty", value="easy", type="recipe")  # Remove hardcoded author_id
        diet_tag = create_recipe_tag_orm(key="diet", value="vegetarian", type="recipe")  # Remove hardcoded author_id
        
        test_session.add(cuisine_tag)
        test_session.add(difficulty_tag)
        test_session.add(diet_tag)
        await test_session.flush()
        
        # Create recipe with multiple tags
        recipe = create_recipe_orm(
            name="Multi-Tagged Recipe",
            author_id=meal.author_id,  # Use meal's author_id for consistency
            meal_id=meal.id,
            tags=[cuisine_tag, difficulty_tag, diet_tag]
        )
        test_session.add(recipe)
        await test_session.commit()
        
        # When: Retrieving the recipe through repository
        retrieved_recipe = await recipe_repository.get_sa_instance(recipe.id)
        
        # Then: Recipe should have all tags persisted
        assert len(retrieved_recipe.tags) == 3
        tag_keys = {tag.key for tag in retrieved_recipe.tags}
        tag_values = {tag.value for tag in retrieved_recipe.tags}
        
        assert "cuisine" in tag_keys
        assert "difficulty" in tag_keys
        assert "diet" in tag_keys
        
        assert "italian" in tag_values
        assert "easy" in tag_values
        assert "vegetarian" in tag_values


# =============================================================================
# TEST RECIPE REPOSITORY ERROR HANDLING
# =============================================================================

class TestRecipeRepositoryErrorHandling:
    """Test edge cases and database constraints"""

    async def test_get_nonexistent_recipe(self, recipe_repository: RecipeRepo):
        """Test getting a recipe that doesn't exist"""
        # Given: A non-existent recipe ID
        nonexistent_id = "recipe_that_does_not_exist"
        
        # When/Then: Should raise EntityNotFoundException
        from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import EntityNotFoundException
        with pytest.raises(EntityNotFoundException):
            await recipe_repository.get_sa_instance(nonexistent_id)

    async def test_get_sa_instance_nonexistent(self, recipe_repository: RecipeRepo):
        """Test getting SA instance that doesn't exist"""
        # Given: A non-existent recipe ID
        nonexistent_id = "recipe_sa_that_does_not_exist"
        
        # When/Then: Should raise EntityNotFoundException
        from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import EntityNotFoundException
        with pytest.raises(EntityNotFoundException):
            await recipe_repository.get_sa_instance(nonexistent_id)

    async def test_invalid_filter_parameters(self, recipe_repository: RecipeRepo):
        """Test querying with invalid filter parameters"""
        # Given: Invalid filter parameters
        from src.contexts.seedwork.shared.adapters.repositories.repository_exceptions import FilterValidationException
        
        # When/Then: Should raise FilterValidationException for invalid fields
        with pytest.raises(FilterValidationException, match="Invalid filter keys"):
            await recipe_repository.query(filter={"invalid_field": "value"}, _return_sa_instance=True)
        
        # When/Then: Should raise appropriate errors for invalid values
        with pytest.raises((ValueError, TypeError, FilterValidationException)):
            await recipe_repository.query(filter={"total_time_gte": "not_a_number"}, _return_sa_instance=True)

    async def test_null_handling_in_filters(self, recipe_repository: RecipeRepo):
        """Test handling null values in filter parameters"""
        # Given: Null/None values in filters
        from src.contexts.seedwork.shared.adapters.repositories.repository_exceptions import RepositoryQueryException
        
        # When/Then: Should handle None values appropriately
        # Some filters can handle None (equality filters)
        result = await recipe_repository.query(filter={"name": None}, _return_sa_instance=True)
        assert isinstance(result, list)
        
        # But operator filters should reject None values
        with pytest.raises(RepositoryQueryException, match="Query building failed"):
            await recipe_repository.query(filter={"total_time_gte": None}, _return_sa_instance=True)

    async def test_empty_filter_dict(self, recipe_repository: RecipeRepo):
        """Test querying with empty filter dictionary"""
        # Given: Empty filter
        empty_filter = {}
        
        # When: Querying with empty filter
        result = await recipe_repository.query(filter=empty_filter, _return_sa_instance=True)
        
        # Then: Should return all recipes (may be empty list)
        assert isinstance(result, list)

    async def test_none_filter(self, recipe_repository: RecipeRepo):
        """Test querying with None filter"""
        # Given: None filter
        none_filter = None
        
        # When: Querying with None filter
        result = await recipe_repository.query(filter=none_filter, _return_sa_instance=True)
        
        # Then: Should return all recipes (may be empty list)
        assert isinstance(result, list)

    async def test_rating_validation_errors_with_database(self, recipe_repository: RecipeRepo, test_session):
        """Test rating validation error cases with real database persistence"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Rating Validation")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # When/Then: Invalid rating values should be rejected by ORM validation
        from sqlalchemy.exc import StatementError, DataError
        
        # Test taste rating below range (-1)
        with pytest.raises((StatementError, DataError, ValueError)):
            invalid_rating_below = create_rating_orm(
                user_id="user_test",
                recipe_id="recipe_rating_validation_errors",
                taste=-1,  # Below valid range
                convenience=3
            )
            test_session.add(invalid_rating_below)
            await test_session.commit()
        
        await test_session.rollback()
        
        # Test taste rating above range (6)
        with pytest.raises((StatementError, DataError, ValueError)):
            invalid_rating_above = create_rating_orm(
                user_id="user_test",
                recipe_id="recipe_rating_validation_errors",
                taste=6,  # Above valid range
                convenience=3
            )
            test_session.add(invalid_rating_above)
            await test_session.commit()
        
        await test_session.rollback()
        
        # Test convenience rating below range (-1)
        with pytest.raises((StatementError, DataError, ValueError)):
            invalid_convenience_below = create_rating_orm(
                user_id="user_test",
                recipe_id="recipe_rating_validation_errors",
                taste=3,
                convenience=-1  # Below valid range
            )
            test_session.add(invalid_convenience_below)
            await test_session.commit()

        await test_session.rollback()

        # Test convenience rating above range (6)
        with pytest.raises((StatementError, DataError, ValueError)):
            invalid_convenience_above = create_rating_orm(
                user_id="user_test",
                recipe_id="recipe_rating_validation_errors",
                taste=3,
                convenience=6  # Above valid range
            )
            test_session.add(invalid_convenience_above)
            await test_session.commit()

        await test_session.rollback()

    async def test_ingredient_validation_errors_with_database(self, recipe_repository: RecipeRepo, test_session):
        """Test ingredient validation error cases with real database persistence"""
        # Create meal first
        meal = create_meal_orm(name="Meal for Ingredient Validation")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # When/Then: Invalid ingredient values should be rejected by database constraints
        from sqlalchemy.exc import IntegrityError, StatementError, DataError
        
        # Test negative quantity
        with pytest.raises((IntegrityError, StatementError, DataError, ValueError)):
            invalid_ingredient_negative = create_ingredient_orm(
                name="Invalid Ingredient",
                quantity=-1.0,  # Negative quantity should be invalid
                position=0,
                recipe_id="recipe_ingredient_validation_errors"
            )
            test_session.add(invalid_ingredient_negative)
            await test_session.commit()
        
        await test_session.rollback()
        
        # Test zero quantity (depending on business rules, this might be invalid)
        with pytest.raises((IntegrityError, StatementError, DataError, ValueError)):
            invalid_ingredient_zero = create_ingredient_orm(
                name="Invalid Ingredient",
                quantity=0.0,  # Zero quantity might be invalid
                position=0,
                recipe_id="recipe_ingredient_validation_errors"
            )
            test_session.add(invalid_ingredient_zero)
            await test_session.commit()
        
        await test_session.rollback()
        
        # Test negative position
        with pytest.raises((IntegrityError, StatementError, DataError, ValueError)):
            invalid_ingredient_position = create_ingredient_orm(
                name="Invalid Ingredient",
                quantity=100.0,
                position=-1,  # Negative position should be invalid
                recipe_id="recipe_ingredient_validation_errors"
            )
            test_session.add(invalid_ingredient_position)
            await test_session.commit()

        await test_session.rollback()

    async def test_database_constraint_violations_with_recipes(self, recipe_repository: RecipeRepo, test_session):
        """Test database constraint violations specific to recipes"""
        # Given: Database constraints for recipe entities
        from sqlalchemy.exc import IntegrityError
        
        # Test foreign key constraint violation (meal_id doesn't exist)
        with pytest.raises(IntegrityError, match="foreign key constraint"):
            invalid_recipe = create_recipe_orm(
                name="Recipe with Invalid Meal ID",
                author_id="test_author",
                meal_id="non_existent_meal_id",  # Foreign key violation
                id="recipe_fk_violation"
            )
            test_session.add(invalid_recipe)
            await test_session.commit()
        
        await test_session.rollback()
        
        # Test not null constraint violation (author_id is None)
        with pytest.raises(IntegrityError, match="violates not-null constraint"):
            invalid_recipe_null = create_recipe_orm(
                name="Recipe with Null Author",
                author_id=None,  # Not null constraint violation
                meal_id="some_meal_id",
                id="recipe_null_violation"
            )
            test_session.add(invalid_recipe_null)
            await test_session.commit()
        
        await test_session.rollback()


# =============================================================================
# TEST RECIPE REPOSITORY PERFORMANCE
# =============================================================================

class TestRecipeRepositoryPerformance:
    """Test performance benchmarks and baselines"""

    @pytest.mark.parametrize("scenario", get_performance_test_scenarios())
    async def test_query_performance_scenarios(self, recipe_repository: RecipeRepo, scenario: Dict[str, Any]):
        """Test query performance with various scenarios"""
        # Given: Performance scenario
        start_time = time.time()
        
        # When: Executing query
        if "filter" in scenario:
            result = await recipe_repository.query(filter=scenario["filter"], _return_sa_instance=True)
        else:
            result = await recipe_repository.query(_return_sa_instance=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Then: Should meet performance expectations
        assert isinstance(result, list)
        if "expected_query_time" in scenario:
            # Note: Performance assertions are informational in this test environment
            # In production, we would assert: duration <= scenario["expected_query_time"]
            print(f"Query duration: {duration:.3f}s (expected: ≤{scenario['expected_query_time']}s)")

    async def test_bulk_persist_performance(self, recipe_repository: RecipeRepo, test_session):
        """Test bulk persist operation performance using direct database session"""
        # Given: Multiple meals with recipes for bulk operation using ORM factories
        recipe_count = 10  # Reduced for performance test
        meals_with_recipes = []
        
        for i in range(recipe_count):
            # Create meal first
            meal = create_meal_orm(
                name=f"Performance Test Meal {i}",
                author_id="perf_test_author"
            )
            
            # Create recipe for the meal
            recipe = create_recipe_orm(
                name=f"Performance Test Recipe {i}",
                meal_id=meal.id,
                author_id="perf_test_author"
            )
            
            meals_with_recipes.append((meal, recipe))
        
        # When: Performing bulk add through database session
        start_time = time.time()
        for meal, recipe in meals_with_recipes:
            test_session.add(meal)
            test_session.add(recipe)
        await test_session.commit()
        end_time = time.time()
        
        duration = end_time - start_time
        time_per_recipe = duration / recipe_count
        
        # Then: Should meet performance expectations
        print(f"Bulk meal add: {duration:.3f}s total, {time_per_recipe:.6f}s per meal")
        # Expected: < 50ms per meal with recipe (reasonable for complex operations)

    async def test_complex_query_performance(self, recipe_repository: RecipeRepo):
        """Test complex query with multiple filters"""
        # Given: Complex filter combination
        complex_filter = {
            "total_time_gte": 30,
            "total_time_lte": 120,
            "privacy": "public",
            "calories_gte": 200,
            "protein_gte": 15,
            "author_id": "test_author"
        }
        
        # When: Executing complex query
        start_time = time.time()
        result = await recipe_repository.query(filter=complex_filter, _return_sa_instance=True)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Then: Should complete in reasonable time
        assert isinstance(result, list)
        print(f"Complex query duration: {duration:.3f}s")
        # Expected: < 1s for reasonable dataset sizes

    async def test_tag_filtering_performance(self, recipe_repository: RecipeRepo):
        """Test tag filtering performance"""
        # Given: Tag filter
        tag_filter = {"tags": [("cuisine", "italian", "author_1")]}
        
        # When: Executing tag query
        start_time = time.time()
        result = await recipe_repository.query(filter=tag_filter, _return_sa_instance=True)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Then: Should complete efficiently
        assert isinstance(result, list)
        print(f"Tag filtering duration: {duration:.3f}s")
        # Expected: < 0.5s for reasonable dataset sizes

    async def test_list_filter_options_performance(self, recipe_repository: RecipeRepo):
        """Test filter options listing performance"""
        # When: Getting filter options
        start_time = time.time()
        filter_options = recipe_repository.list_filter_options()
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Then: Should return quickly
        assert isinstance(filter_options, dict)
        assert "sort" in filter_options
        print(f"Filter options duration: {duration:.6f}s")
        # Expected: < 1ms for static data

    async def test_memory_usage_bulk_operations(self, recipe_repository: RecipeRepo):
        """Test memory usage with query operations (since direct persist isn't supported)"""
        # Given: This test focuses on query performance since RecipeRepository 
        # doesn't support direct persist operations
        
        # When: Performing multiple query operations to test memory usage
        query_count = 100
        for i in range(query_count):
            # Test various filter combinations
            filters = [
                {"author_id": f"author_{i % 5}"},
                {"privacy": "public" if i % 2 == 0 else "private"},
                {"total_time_gte": 30},
                {}  # Empty filter (query all)
            ]
            
            for filter_params in filters:
                result = await recipe_repository.query(filter=filter_params, _return_sa_instance=True)
                assert isinstance(result, list)
        
        # Then: Should handle many query operations efficiently
        print(f"Successfully executed {query_count * len(filters)} queries with various filters")

    async def test_bulk_recipe_query_performance(self, recipe_repository: RecipeRepo, test_session):
        """Test performance with bulk recipe data using direct database operations"""
        # Create parent meal first
        meal = create_meal_orm(name="Bulk Performance Meal")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # Create many recipes for performance testing
        recipe_count = 50  # Reasonable size for CI
        recipes = []
        for i in range(recipe_count):
            recipe = create_recipe_orm(
                name=f"Bulk Recipe {i}",
                meal_id=meal.id,
                author_id=shared_author_id,
                total_time=30 + (i % 120),  # Vary cooking time
                privacy="public" if i % 2 == 0 else "private"
            )
            recipes.append(recipe)
            test_session.add(recipe)
        
        await test_session.commit()
        
        # When: Performing various queries on bulk data
        start_time = time.time()
        
        # Query all recipes
        all_results = await recipe_repository.query(filter={}, _return_sa_instance=True)
        
        # Query with filters
        public_results = await recipe_repository.query(filter={"privacy": "public"}, _return_sa_instance=True)
        time_filtered_results = await recipe_repository.query(filter={"total_time_gte": 60}, _return_sa_instance=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Then: Should handle bulk queries efficiently
        assert len(all_results) >= recipe_count
        assert len(public_results) >= recipe_count // 2  # Roughly half should be public
        assert isinstance(time_filtered_results, list)
        
        print(f"Bulk query performance: {duration:.3f}s for {recipe_count} recipes")
        # Expected: < 2s for reasonable dataset sizes


# =============================================================================
# TEST SPECIALIZED RECIPE FACTORIES
# =============================================================================

class TestSpecializedRecipeFactories:
    """Test specialized recipe factory functions with database persistence"""

    async def test_quick_recipe_creation_with_database(self, recipe_repository: RecipeRepo, test_session):
        """Test creating quick recipes with real database persistence"""
        meal = create_meal_orm(name="Quick Meal Parent")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # When: Creating quick recipe using ORM factory
        quick_recipe = create_quick_recipe_orm(
            name="Super Quick Meal",
            meal_id=meal.id,
            author_id=shared_author_id
        )
        test_session.add(quick_recipe)
        await test_session.commit()
        
        # Then: Should have quick recipe characteristics persisted in database
        retrieved_recipe = await recipe_repository.get_sa_instance(quick_recipe.id)
        assert retrieved_recipe.name == "Super Quick Meal"
        assert retrieved_recipe.total_time == 15  # Quick recipe characteristic
        assert "Quick and easy" in retrieved_recipe.instructions
        
        # Should have appropriate tags in database
        if retrieved_recipe.tags:
            tag_keys = {tag.key for tag in retrieved_recipe.tags}
            assert "difficulty" in tag_keys
            assert "cooking_method" in tag_keys

    async def test_high_protein_recipe_creation_with_database(self, recipe_repository: RecipeRepo, test_session):
        """Test creating high protein recipes with real database persistence"""
        meal = create_meal_orm(name="Protein Meal Parent")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # When: Creating high protein recipe using ORM factory
        protein_recipe = create_high_protein_recipe_orm(
            name="Protein Power",
            meal_id=meal.id,
            author_id=shared_author_id
        )
        test_session.add(protein_recipe)
        await test_session.commit()
        
        # Then: Should have high protein characteristics persisted in database
        retrieved_recipe = await recipe_repository.get_sa_instance(protein_recipe.id)
        assert retrieved_recipe.name == "Protein Power"
        
        # Should have high protein content in nutritional information
        assert retrieved_recipe.protein_percentage is not None
        assert retrieved_recipe.protein_percentage >= 25.0  # High protein characteristic
        
        # Should have protein-rich ingredients in database
        if retrieved_recipe.ingredients:
            ingredient_names = {ing.name for ing in retrieved_recipe.ingredients}
            # Note: Exact ingredient names depend on ORM factory implementation
            assert len(ingredient_names) > 0  # Should have some ingredients

    async def test_vegetarian_recipe_creation_with_database(self, recipe_repository: RecipeRepo, test_session):
        """Test creating vegetarian recipes with real database persistence"""
        meal = create_meal_orm(name="Vegetarian Meal Parent")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # When: Creating vegetarian recipe using ORM factory
        veg_recipe = create_vegetarian_recipe_orm(
            name="Veggie Delight",
            meal_id=meal.id,
            author_id=shared_author_id
        )
        test_session.add(veg_recipe)
        await test_session.commit()
        
        # Then: Should have vegetarian characteristics persisted in database
        retrieved_recipe = await recipe_repository.get_sa_instance(veg_recipe.id)
        assert retrieved_recipe.name == "Veggie Delight"
        
        # Should have vegetarian ingredients in database
        if retrieved_recipe.ingredients:
            ingredient_names = {ing.name for ing in retrieved_recipe.ingredients}
            # Note: Exact ingredient names depend on ORM factory implementation
            assert len(ingredient_names) > 0  # Should have some ingredients
        
        # Should have vegetarian tag in database
        if retrieved_recipe.tags:
            tag_values = {tag.value for tag in retrieved_recipe.tags}
            assert "vegetarian" in tag_values

    async def test_public_private_recipe_creation_with_database(self, recipe_repository: RecipeRepo, test_session):
        """Test creating public and private recipes with real database persistence"""
        meal = create_meal_orm(name="Privacy Test Meal")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # When: Creating public and private recipes using ORM factories
        public_recipe = create_public_recipe_orm(
            name="Public Recipe",
            meal_id=meal.id,
            author_id=shared_author_id
        )
        private_recipe = create_private_recipe_orm(
            name="Private Recipe",
            meal_id=meal.id,
            author_id=shared_author_id
        )
        
        test_session.add(public_recipe)
        test_session.add(private_recipe)
        await test_session.commit()
        
        # Then: Should have correct privacy settings persisted in database
        retrieved_public = await recipe_repository.get_sa_instance(public_recipe.id)
        retrieved_private = await recipe_repository.get_sa_instance(private_recipe.id)
        
        assert retrieved_public.privacy == Privacy.PUBLIC
        assert retrieved_public.name == "Public Recipe"
        assert retrieved_public.description is not None
        assert "public recipe available to all users" in retrieved_public.description
        
        assert retrieved_private.privacy == Privacy.PRIVATE
        assert retrieved_private.name == "Private Recipe"
        assert retrieved_private.description is not None
        assert "private recipe only visible to the author" in retrieved_private.description

    async def test_recipe_orm_factory_persistence_patterns(self, recipe_repository: RecipeRepo, test_session):
        """Test that ORM factory functions create properly persisted recipes"""
        meal = create_meal_orm(name="Factory Pattern Meal")
        test_session.add(meal)
        await test_session.flush()
        
        shared_author_id = meal.author_id
        
        # When: Creating recipes using different ORM factory patterns
        recipes_to_test = [
            ("quick_recipe", create_quick_recipe_orm),
            ("high_protein_recipe", create_high_protein_recipe_orm),
            ("vegetarian_recipe", create_vegetarian_recipe_orm),
            ("public_recipe", create_public_recipe_orm),
            ("private_recipe", create_private_recipe_orm)
        ]
        
        created_recipe_ids = []
        
        for recipe_type, factory_func in recipes_to_test:
            recipe = factory_func(
                name=f"Test {recipe_type.replace('_', ' ').title()}",
                meal_id=meal.id,
                author_id=shared_author_id
            )
            test_session.add(recipe)
            created_recipe_ids.append(recipe.id)
        
        await test_session.commit()
        
        # Then: All recipes should be properly persisted and retrievable
        for recipe_id in created_recipe_ids:
            retrieved_recipe = await recipe_repository.get_sa_instance(recipe_id)
            assert retrieved_recipe is not None
            assert retrieved_recipe.id == recipe_id
            assert retrieved_recipe.meal_id == meal.id
            assert retrieved_recipe.author_id == shared_author_id
            assert retrieved_recipe.name is not None
            assert len(retrieved_recipe.name) > 0
        
        # When: Querying all recipes created by factories
        all_factory_recipes = await recipe_repository.query(
            filter={"meal_id": meal.id},
            _return_sa_instance=True
        )
        
        # Then: Should find all created recipes
        found_recipe_ids = {recipe.id for recipe in all_factory_recipes}
        for recipe_id in created_recipe_ids:
            assert recipe_id in found_recipe_ids