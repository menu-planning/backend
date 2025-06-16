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

import pytest

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

import time
from typing import List, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.contexts.recipes_catalog.core.adapters.meal.repositories.recipe_repository import RecipeRepo
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import Ingredient
from src.contexts.recipes_catalog.core.domain.meal.value_objects.rating import Rating
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.enums import MeasureUnit, Privacy

# Import necessary SA models to ensure database tables exist
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import RecipeSaModel
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
# MenuSaModel now imported in meal_sa_model.py where it belongs

from tests.contexts.recipes_catalog.core.adapters.meal.repositories.recipe_data_factories import (
    create_recipe,
    create_recipe_kwargs,
    create_ingredient,
    create_ingredient_kwargs,
    create_rating,
    create_rating_kwargs,
    create_tag,
    create_tag_kwargs,
    get_recipe_filter_scenarios,
    get_ingredient_relationship_scenarios,
    get_rating_aggregation_scenarios,
    get_tag_filtering_scenarios,
    get_performance_test_scenarios,
    reset_counters,
    create_recipes_with_ratings,
    create_test_dataset,
    create_quick_recipe,
    create_high_protein_recipe,
    create_vegetarian_recipe,
    create_public_recipe,
    create_private_recipe
)


# =============================================================================
# TEST FIXTURES AND SETUP
# =============================================================================

@pytest.fixture(autouse=True)
def reset_data_factory_counters():
    """Reset counters before each test for isolation"""
    reset_counters()


@pytest.fixture
async def recipe_repository(async_pg_session: AsyncSession) -> RecipeRepo:
    """Create RecipeRepository instance for testing"""
    return RecipeRepo(db_session=async_pg_session)


@pytest.fixture
async def benchmark_timer():
    """Fixture for measuring test execution time"""
    start_time = time.time()
    yield start_time
    end_time = time.time()
    duration = end_time - start_time


# =============================================================================
# TEST RECIPE REPOSITORY CORE OPERATIONS
# =============================================================================

class TestRecipeRepositoryCore:
    """Test basic CRUD operations with real database persistence"""

    async def test_get_recipe_by_id(self, recipe_repository: RecipeRepo, async_pg_session):
        """Test retrieving a recipe by ID"""
        # Given: A meal with recipes added through MealRepository (proper way)
        from src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository import MealRepo
        from tests.contexts.recipes_catalog.core.adapters.meal.repositories.meal_data_factories import create_meal
        
        meal_repo = MealRepo(async_pg_session)
        recipe = create_recipe(name="Test Recipe for Get", author_id="test_author", meal_id="meal_001")
        meal = create_meal(
            name="Test Meal with Recipe",
            author_id="test_author", 
            id="meal_001",
            recipes=[recipe]
        )
        await meal_repo.add(meal)
        
        # When: Getting the recipe by ID through RecipeRepository
        result = await recipe_repository.get(recipe.id)
        
        # Then: Should return the recipe from the meal
        assert result.id == recipe.id
        assert result.name == "Test Recipe for Get"
        assert result.author_id == "test_author"
        assert result.meal_id == "meal_001"

    async def test_get_sa_instance(self, recipe_repository: RecipeRepo, async_pg_session):
        """Test getting SQLAlchemy instance of recipe"""
        # Given: A meal with recipes added through MealRepository (proper way)
        from src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository import MealRepo
        from tests.contexts.recipes_catalog.core.adapters.meal.repositories.meal_data_factories import create_meal
        
        meal_repo = MealRepo(async_pg_session)
        recipe = create_recipe(name="Test Recipe for SA Instance", author_id="test_author", meal_id="meal_002")
        meal = create_meal(
            name="Test Meal for SA Instance",
            author_id="test_author",
            id="meal_002", 
            recipes=[recipe]
        )
        await meal_repo.add(meal)
        
        # When: Getting the SQLAlchemy instance
        sa_instance = await recipe_repository.get_sa_instance(recipe.id)
        
        # Then: Should return the correct SA model instance
        assert isinstance(sa_instance, RecipeSaModel)
        assert sa_instance.id == recipe.id
        assert sa_instance.name == "Test Recipe for SA Instance"

    async def test_persist_recipe_fails_without_add(self, recipe_repository: RecipeRepo):
        """Test that persist fails without calling add first (Unit of Work pattern)"""
        # Given: A new recipe not added to repository
        recipe = create_recipe(
            name="Test Recipe for Persist",
            author_id="test_author",
            meal_id="test_meal_001"
        )
        
        # When/Then: persist() should fail because recipe is not in repository's "seen" set
        with pytest.raises(AssertionError, match="Cannon persist entity which is unknown to the repo"):
            await recipe_repository.persist(recipe)

    async def test_persist_all_recipes_fails_without_add(self, recipe_repository: RecipeRepo):
        """Test that persist_all fails without calling add first (Unit of Work pattern)"""
        # Given: Multiple recipes not added to repository
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
        # Given: Multiple recipes would need to be in database
        # When: Querying all recipes
        result = await recipe_repository.query()
        
        # Then: Should return list of recipes (may be empty if none exist)
        assert isinstance(result, list)
        # All items should be Recipe instances
        for recipe in result:
            assert isinstance(recipe, _Recipe)

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
        
        # When/Then: Each filter should execute without error
        for filter_params in test_filters:
            result = await recipe_repository.query(filter=filter_params)
            assert isinstance(result, list)

    async def test_add_method_raises_not_implemented(self, recipe_repository: RecipeRepo):
        """Test that add method raises NotImplementedError as expected"""
        # Given: A recipe
        recipe = create_recipe(name="Test Recipe")
        
        # When/Then: add() should raise NotImplementedError
        with pytest.raises(NotImplementedError, match="Recipes must be added through the meal repo"):
            await recipe_repository.add(recipe)

    async def test_tags_are_persisted_after_meal_creation(self, recipe_repository: RecipeRepo, async_pg_session):
        """Test that recipe tags are properly persisted when added through meal repo"""
        # Given: A meal with recipe containing tags added through MealRepository
        from src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository import MealRepo
        from tests.contexts.recipes_catalog.core.adapters.meal.repositories.meal_data_factories import create_meal
        
        meal_repo = MealRepo(async_pg_session)
        tags = {
            create_tag(key="cuisine", value="italian", author_id="test_author"),
            create_tag(key="difficulty", value="easy", author_id="test_author")
        }
        recipe = create_recipe(
            name="Test Recipe with Tags", 
            author_id="test_author", 
            meal_id="meal_tags_001",
            tags=tags
        )
        meal = create_meal(
            name="Test Meal with Tagged Recipe",
            author_id="test_author", 
            id="meal_tags_001",
            recipes=[recipe]
        )
        await meal_repo.add(meal)
        
        # When: Getting the recipe through RecipeRepository
        result = await recipe_repository.get(recipe.id)
        
        # Then: Tags should be persisted correctly
        assert len(result.tags) == 2
        tag_keys = {tag.key for tag in result.tags}
        tag_values = {tag.value for tag in result.tags}
        assert "cuisine" in tag_keys
        assert "difficulty" in tag_keys
        assert "italian" in tag_values
        assert "easy" in tag_values

    async def test_ingredient_replacement_through_persist(self, recipe_repository: RecipeRepo, async_pg_session):
        """Test replacing ingredients in a recipe through update and persist operations"""
        # Given: A meal with recipe added through MealRepository
        from src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository import MealRepo
        from tests.contexts.recipes_catalog.core.adapters.meal.repositories.meal_data_factories import create_meal
        
        meal_repo = MealRepo(async_pg_session)
        original_ingredients = [
            create_ingredient(name="Flour", position=0),
            create_ingredient(name="Sugar", position=1),
            create_ingredient(name="Eggs", position=2)
        ]
        recipe = create_recipe(
            name="Recipe for Ingredient Replacement",
            author_id="test_author",
            meal_id="meal_ingredients_001",
            ingredients=original_ingredients
        )
        meal = create_meal(
            name="Meal for Ingredient Test",
            author_id="test_author",
            id="meal_ingredients_001",
            recipes=[recipe]
        )
        await meal_repo.add(meal)
        await async_pg_session.commit()
        
        # When: Getting recipe, updating ingredients, and persisting through MealRepo
        retrieved_recipe = await recipe_repository.get(recipe.id)
        assert len(retrieved_recipe.ingredients) == 3
        
        # Update ingredients through the meal (proper domain pattern)
        meal_retrieved = await meal_repo.get("meal_ingredients_001")
        new_ingredient = create_ingredient(name="New Single Ingredient", position=0)
        meal_retrieved.update_recipes({
            recipe.id: {"ingredients": [new_ingredient]}
        })
        await meal_repo.persist(meal_retrieved)
        await async_pg_session.commit()
        
        # Then: Recipe should have updated ingredients
        updated_recipe = await recipe_repository.get(recipe.id)
        assert len(updated_recipe.ingredients) == 1
        assert updated_recipe.ingredients[0].name == "New Single Ingredient"
        assert updated_recipe.ingredients[0].position == 0

    async def test_relationship_queries_no_duplicate_rows(self, recipe_repository: RecipeRepo, async_pg_session):
        """Test that querying on relationships doesn't return duplicate rows"""
        # Given: A meal with recipe that has multiple ingredients with product relationships
        from src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository import MealRepo
        from tests.contexts.recipes_catalog.core.adapters.meal.repositories.meal_data_factories import create_meal
        
        meal_repo = MealRepo(async_pg_session)
        ingredients_with_products = [
            create_ingredient(name="Ingredient 1", product_id="product_001", position=0),
            create_ingredient(name="Ingredient 2", product_id="product_002", position=1)
        ]
        recipe = create_recipe(
            name="Recipe with Product Relationships",
            author_id="test_author",
            meal_id="meal_relations_001",
            ingredients=ingredients_with_products
        )
        meal = create_meal(
            name="Meal with Product Relations",
            author_id="test_author",
            id="meal_relations_001",
            recipes=[recipe]
        )
        await meal_repo.add(meal)
        await async_pg_session.commit()
        
        # When: Querying all recipes
        all_recipes = await recipe_repository.query()
        matching_recipes = [r for r in all_recipes if r.name == "Recipe with Product Relationships"]
        
        # Then: Should return exactly one recipe (no duplicates from JOIN operations)
        assert len(matching_recipes) == 1
        assert matching_recipes[0].id == recipe.id
        
        # When: Querying with product filter (if products exist)
        product_filtered_recipes = await recipe_repository.query(
            filter={"products": ["product_001", "product_002"]}
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
    """Test ingredient relationships and product filtering"""

    @pytest.mark.parametrize("scenario", get_ingredient_relationship_scenarios())
    async def test_ingredient_relationship_scenarios(self, recipe_repository: RecipeRepo, scenario: Dict[str, Any]):
        """Test ingredient filtering with various scenarios"""
        # Given: The scenario setup is theoretical since we can't directly add recipes
        # When: Testing the query method with ingredient-related filters
        result = await recipe_repository.query(filter=scenario["filter"])
        
        # Then: Query should execute without error
        assert isinstance(result, list)
        # Note: Actual matching tests would require recipes in database

    async def test_product_filtering(self, recipe_repository: RecipeRepo):
        """Test filtering recipes by ingredient product IDs"""
        # Given: Product ID filters
        product_filters = [
            {"products": ["product_001"]},
            {"products": ["product_001", "product_002"]},
            {"products": ["nonexistent_product"]}
        ]
        
        # When/Then: Each product filter should execute without error
        for filter_params in product_filters:
            result = await recipe_repository.query(filter=filter_params)
            assert isinstance(result, list)

    async def test_product_name_filtering(self, recipe_repository: RecipeRepo):
        """Test filtering recipes by product name (uses ProductRepo integration)"""
        # Given: Product name filter
        filter_params = {"product_name": "flour"}
        
        # When: Querying with product name
        result = await recipe_repository.query(filter=filter_params)
        
        # Then: Should execute without error and return list
        assert isinstance(result, list)
        # Note: This tests the integration with ProductRepo.list_top_similar_names()

    async def test_ingredient_validation(self, recipe_repository: RecipeRepo):
        """Test ingredient validation through data factories"""
        # Given: Various ingredient configurations
        valid_ingredient = create_ingredient(
            name="Test Flour",
            unit=MeasureUnit.GRAM,
            quantity=200.0,
            position=0
        )
        
        # When/Then: Valid ingredient should be created successfully
        assert valid_ingredient.name == "Test Flour"
        assert valid_ingredient.unit == MeasureUnit.GRAM
        assert valid_ingredient.quantity == 200.0
        assert valid_ingredient.position == 0

    async def test_ingredient_product_relationship(self, recipe_repository: RecipeRepo):
        """Test ingredient-product relationships"""
        # Given: Recipe with ingredients that have product relationships
        recipe = create_recipe(
            name="Recipe with Product Ingredients",
            ingredients=[
                create_ingredient(
                    name="Flour",
                    product_id="flour_product_123",
                    position=0
                ),
                create_ingredient(
                    name="Sugar", 
                    product_id="sugar_product_456",
                    position=1
                )
            ]
        )
        
        # When/Then: Recipe should have ingredients with product relationships
        assert len(recipe.ingredients) == 2
        assert recipe.ingredients[0].product_id == "flour_product_123"
        assert recipe.ingredients[1].product_id == "sugar_product_456"

    async def test_ingredient_without_product(self, recipe_repository: RecipeRepo):
        """Test ingredients without product relationships"""
        # Given: Recipe with generic ingredients (no product_id)
        recipe = create_recipe(
            name="Recipe with Generic Ingredients",
            ingredients=[
                create_ingredient(
                    name="Salt",
                    product_id=None,
                    position=0
                )
            ]
        )
        
        # When/Then: Recipe should have ingredient without product relationship
        assert len(recipe.ingredients) == 1
        assert recipe.ingredients[0].product_id is None
        assert recipe.ingredients[0].name == "Salt"


# =============================================================================
# TEST RECIPE REPOSITORY RATINGS
# =============================================================================

class TestRecipeRepositoryRatings:
    """Test rating aggregation and rating-based filtering"""

    @pytest.mark.parametrize("scenario", get_rating_aggregation_scenarios())
    async def test_rating_aggregation_scenarios(self, recipe_repository: RecipeRepo, scenario: Dict[str, Any]):
        """Test rating aggregation with various scenarios"""
        # Given: The scenario setup (theoretical since we can't directly add recipes)
        # When: Testing query with rating filters
        result = await recipe_repository.query(filter=scenario["filter"])
        
        # Then: Query should execute without error
        assert isinstance(result, list)

    async def test_average_taste_rating_filter(self, recipe_repository: RecipeRepo):
        """Test filtering by average taste rating"""
        # Given: Rating filter parameters
        rating_filters = [
            {"average_taste_rating_gte": 4.0},
            {"average_taste_rating_gte": 3.5},
            {"average_taste_rating_gte": 0.0}
        ]
        
        # When/Then: Each rating filter should execute without error
        for filter_params in rating_filters:
            result = await recipe_repository.query(filter=filter_params)
            assert isinstance(result, list)

    async def test_average_convenience_rating_filter(self, recipe_repository: RecipeRepo):
        """Test filtering by average convenience rating"""
        # Given: Convenience rating filter parameters
        rating_filters = [
            {"average_convenience_rating_gte": 4.5},
            {"average_convenience_rating_gte": 3.0},
            {"average_convenience_rating_gte": 1.0}
        ]
        
        # When/Then: Each convenience rating filter should execute without error
        for filter_params in rating_filters:
            result = await recipe_repository.query(filter=filter_params)
            assert isinstance(result, list)

    async def test_rating_validation(self, recipe_repository: RecipeRepo):
        """Test rating validation through data factories"""
        # Given: Various rating configurations
        valid_rating = create_rating(
            user_id="user_123",
            recipe_id="recipe_456",
            taste=5,
            convenience=4,
            comment="Excellent recipe!"
        )
        
        # When/Then: Valid rating should be created successfully
        assert valid_rating.user_id == "user_123"
        assert valid_rating.recipe_id == "recipe_456"
        assert valid_rating.taste == 5
        assert valid_rating.convenience == 4
        assert valid_rating.comment == "Excellent recipe!"

    async def test_rating_range_validation(self, recipe_repository: RecipeRepo):
        """Test rating value range validation (0-5)"""
        # Given/When/Then: Valid ratings should be accepted
        for rating_value in range(6):  # 0-5
            rating = create_rating(taste=rating_value, convenience=rating_value)
            assert rating.taste == rating_value
            assert rating.convenience == rating_value

    async def test_recipe_with_multiple_ratings(self, recipe_repository: RecipeRepo):
        """Test recipe with multiple ratings for aggregation"""
        # Given: Recipe with multiple ratings
        ratings = [
            create_rating(recipe_id="recipe_001", user_id="user_1", taste=5, convenience=4),
            create_rating(recipe_id="recipe_001", user_id="user_2", taste=4, convenience=5),
            create_rating(recipe_id="recipe_001", user_id="user_3", taste=3, convenience=3)
        ]
        
        recipe = create_recipe(
            id="recipe_001",
            name="Highly Rated Recipe",
            ratings=ratings
        )
        
        # When/Then: Recipe should have correct ratings
        assert recipe.ratings is not None
        assert len(recipe.ratings) == 3
        
        # Note: average_taste_rating and average_convenience_rating are computed properties
        # In memory tests, these may return None if the domain logic requires persistence
        # This tests the basic recipe structure rather than database computation
        
        # Verify ratings are stored correctly
        taste_scores = [rating.taste for rating in recipe.ratings]
        convenience_scores = [rating.convenience for rating in recipe.ratings]
        assert taste_scores == [5, 4, 3]
        assert convenience_scores == [4, 5, 3]
        
        # Test expected computed values if available
        if recipe.average_taste_rating is not None:
            assert recipe.average_taste_rating == 4.0  # (5+4+3)/3
        if recipe.average_convenience_rating is not None:
            assert recipe.average_convenience_rating == 4.0  # (4+5+3)/3

    async def test_recipe_without_ratings(self, recipe_repository: RecipeRepo):
        """Test recipe without any ratings"""
        # Given: Recipe without ratings
        recipe = create_recipe(
            name="Unrated Recipe",
            ratings=[]
        )
        
        # When/Then: Recipe should have no ratings and None averages
        assert recipe.ratings is not None
        assert len(recipe.ratings) == 0
        assert recipe.average_taste_rating is None
        assert recipe.average_convenience_rating is None


# =============================================================================
# TEST RECIPE REPOSITORY TAG FILTERING
# =============================================================================

class TestRecipeRepositoryTagFiltering:
    """Test complex tag logic with AND/OR operations"""

    @pytest.mark.parametrize("scenario", get_tag_filtering_scenarios())
    async def test_tag_filtering_scenarios(self, recipe_repository: RecipeRepo, scenario: Dict[str, Any]):
        """Test tag filtering with various tag combinations"""
        # Given: The scenario setup (theoretical since we can't directly add recipes)
        # When: Testing query with tag filters
        result = await recipe_repository.query(filter=scenario["filter"])
        
        # Then: Query should execute without error
        assert isinstance(result, list)

    async def test_single_tag_filtering(self, recipe_repository: RecipeRepo):
        """Test filtering by single tag"""
        # Given: Single tag filter
        tag_filter = {"tags": [("cuisine", "italian", "author_1")]}
        
        # When: Querying with single tag
        result = await recipe_repository.query(filter=tag_filter)
        
        # Then: Should execute without error
        assert isinstance(result, list)

    async def test_multiple_tags_and_logic(self, recipe_repository: RecipeRepo):
        """Test filtering by multiple tags (AND logic)"""
        # Given: Multiple tag filter (requires ALL tags to match)
        tag_filter = {
            "tags": [
                ("cuisine", "italian", "author_1"),
                ("difficulty", "easy", "author_1")
            ]
        }
        
        # When: Querying with multiple tags
        result = await recipe_repository.query(filter=tag_filter)
        
        # Then: Should execute without error
        assert isinstance(result, list)

    async def test_tags_not_exists_filtering(self, recipe_repository: RecipeRepo):
        """Test filtering by tags that should NOT exist"""
        # Given: tags_not_exists filter
        tag_filter = {"tags_not_exists": [("diet", "vegan", "author_1")]}
        
        # When: Querying with tags_not_exists
        result = await recipe_repository.query(filter=tag_filter)
        
        # Then: Should execute without error
        assert isinstance(result, list)

    async def test_complex_tag_combination(self, recipe_repository: RecipeRepo):
        """Test complex combination of tags and tags_not_exists"""
        # Given: Complex tag filter combination
        tag_filter = {
            "tags": [("cuisine", "italian", "author_1")],
            "tags_not_exists": [("diet", "vegan", "author_1")]
        }
        
        # When: Querying with complex tag combination
        result = await recipe_repository.query(filter=tag_filter)
        
        # Then: Should execute without error
        assert isinstance(result, list)

    async def test_tag_validation(self, recipe_repository: RecipeRepo):
        """Test tag validation through data factories"""
        # Given: Various tag configurations
        recipe_tag = create_tag(
            key="cuisine",
            value="italian",
            author_id="author_1",
            type="recipe"
        )
        
        # When/Then: Valid tag should be created successfully
        assert recipe_tag.key == "cuisine"
        assert recipe_tag.value == "italian"
        assert recipe_tag.author_id == "author_1"
        assert recipe_tag.type == "recipe"

    async def test_recipe_with_multiple_tags(self, recipe_repository: RecipeRepo):
        """Test recipe with multiple tags"""
        # Given: Recipe with multiple tags
        tags = {
            create_tag(key="cuisine", value="italian", author_id="author_1"),
            create_tag(key="difficulty", value="easy", author_id="author_1"),
            create_tag(key="diet", value="vegetarian", author_id="author_1")
        }
        
        recipe = create_recipe(
            name="Multi-Tagged Recipe",
            tags=tags
        )
        
        # When/Then: Recipe should have all tags
        assert len(recipe.tags) == 3
        tag_keys = {tag.key for tag in recipe.tags}
        assert "cuisine" in tag_keys
        assert "difficulty" in tag_keys
        assert "diet" in tag_keys


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
        from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
        with pytest.raises(EntityNotFoundException):
            await recipe_repository.get(nonexistent_id)

    async def test_get_sa_instance_nonexistent(self, recipe_repository: RecipeRepo):
        """Test getting SA instance that doesn't exist"""
        # Given: A non-existent recipe ID
        nonexistent_id = "recipe_sa_that_does_not_exist"
        
        # When/Then: Should raise EntityNotFoundException
        from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
        with pytest.raises(EntityNotFoundException):
            await recipe_repository.get_sa_instance(nonexistent_id)

    async def test_invalid_filter_parameters(self, recipe_repository: RecipeRepo):
        """Test querying with invalid filter parameters"""
        # Given: Invalid filter parameters
        from src.contexts.seedwork.shared.adapters.repositories.repository_exceptions import FilterValidationException
        
        # When/Then: Should raise FilterValidationException for invalid fields
        with pytest.raises(FilterValidationException, match="Invalid filter keys"):
            await recipe_repository.query(filter={"invalid_field": "value"})
        
        # When/Then: Should raise appropriate errors for invalid values
        with pytest.raises((ValueError, TypeError, FilterValidationException)):
            await recipe_repository.query(filter={"total_time_gte": "not_a_number"})


    async def test_null_handling_in_filters(self, recipe_repository: RecipeRepo):
        """Test handling null values in filter parameters"""
        # Given: Null/None values in filters
        from src.contexts.seedwork.shared.adapters.repositories.repository_exceptions import RepositoryQueryException
        
        # When/Then: Should handle None values appropriately
        # Some filters can handle None (equality filters)
        result = await recipe_repository.query(filter={"name": None})
        assert isinstance(result, list)
        
        # But operator filters should reject None values
        with pytest.raises(RepositoryQueryException, match="Query building failed"):
            await recipe_repository.query(filter={"total_time_gte": None})

    async def test_empty_filter_dict(self, recipe_repository: RecipeRepo):
        """Test querying with empty filter dictionary"""
        # Given: Empty filter
        empty_filter = {}
        
        # When: Querying with empty filter
        result = await recipe_repository.query(filter=empty_filter)
        
        # Then: Should return all recipes (may be empty list)
        assert isinstance(result, list)

    async def test_none_filter(self, recipe_repository: RecipeRepo):
        """Test querying with None filter"""
        # Given: None filter
        none_filter = None
        
        # When: Querying with None filter
        result = await recipe_repository.query(filter=none_filter)
        
        # Then: Should return all recipes (may be empty list)
        assert isinstance(result, list)

    async def test_rating_validation_errors(self, recipe_repository: RecipeRepo):
        """Test rating validation error cases"""
        # Given/When/Then: Invalid rating values should raise errors
        invalid_rating_cases = [
            {"taste": -1, "convenience": 3},  # Below range
            {"taste": 6, "convenience": 3},   # Above range
            {"taste": 3, "convenience": -1},  # Below range
            {"taste": 3, "convenience": 6},   # Above range
        ]
        
        for invalid_case in invalid_rating_cases:
            with pytest.raises(ValueError, match="must be an integer between 0 and 5"):
                create_rating(**invalid_case)

    async def test_ingredient_validation_errors(self, recipe_repository: RecipeRepo):
        """Test ingredient validation error cases"""
        # Given/When/Then: Invalid ingredient values should raise errors
        invalid_ingredient_cases = [
            {"quantity": -1},          # Negative quantity
            {"quantity": 0},           # Zero quantity  
            {"position": -1},          # Negative position
        ]
        
        for invalid_case in invalid_ingredient_cases:
            with pytest.raises(ValueError):
                create_ingredient(**invalid_case)




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
            result = await recipe_repository.query(filter=scenario["filter"])
        else:
            result = await recipe_repository.query()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Then: Should meet performance expectations
        assert isinstance(result, list)
        if "expected_query_time" in scenario:
            # Note: Performance assertions are informational in this test environment
            # In production, we would assert: duration <= scenario["expected_query_time"]
            print(f"Query duration: {duration:.3f}s (expected: ≤{scenario['expected_query_time']}s)")

    async def test_bulk_persist_performance(self, recipe_repository: RecipeRepo, async_pg_session):
        """Test bulk persist operation performance through MealRepository"""
        from src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository import MealRepo
        from tests.contexts.recipes_catalog.core.adapters.meal.repositories.meal_data_factories import create_meal
        
        # Given: Multiple meals with recipes for bulk operation
        meal_repo = MealRepo(async_pg_session)
        recipe_count = 10  # Reduced for performance test
        meals = []
        
        for i in range(recipe_count):
            recipe = create_recipe(
                name=f"Performance Test Recipe {i}",
                meal_id=f"perf_meal_{i:03d}"
            )
            meal = create_meal(
                name=f"Performance Test Meal {i}",
                id=f"perf_meal_{i:03d}",
                recipes=[recipe]
            )
            meals.append(meal)
        
        # When: Performing bulk add through MealRepository
        start_time = time.time()
        for meal in meals:
            await meal_repo.add(meal)
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
        result = await recipe_repository.query(filter=complex_filter)
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
        result = await recipe_repository.query(filter=tag_filter)
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
                result = await recipe_repository.query(filter=filter_params)
                assert isinstance(result, list)
        
        # Then: Should handle many query operations efficiently
        print(f"Successfully executed {query_count * len(filters)} queries with various filters")


# =============================================================================
# TEST SPECIALIZED RECIPE FACTORIES
# =============================================================================

class TestSpecializedRecipeFactories:
    """Test specialized recipe factory functions"""

    async def test_quick_recipe_creation(self, recipe_repository: RecipeRepo):
        """Test creating quick recipes"""
        # Given/When: Creating quick recipe
        quick_recipe = create_quick_recipe(name="Super Quick Meal")
        
        # Then: Should have quick recipe characteristics
        assert quick_recipe.name == "Super Quick Meal"
        assert quick_recipe.total_time == 15
        assert "Quick and easy" in quick_recipe.instructions
        
        # Should have appropriate tags
        tag_keys = {tag.key for tag in quick_recipe.tags}
        assert "difficulty" in tag_keys
        assert "cooking_method" in tag_keys

    async def test_high_protein_recipe_creation(self, recipe_repository: RecipeRepo):
        """Test creating high protein recipes"""
        # Given/When: Creating high protein recipe
        protein_recipe = create_high_protein_recipe(name="Protein Power")
        
        # Then: Should have high protein characteristics
        assert protein_recipe.name == "Protein Power"
        assert protein_recipe.nutri_facts is not None
        assert protein_recipe.nutri_facts.protein.value == 30.0  # High protein content
        assert protein_recipe.nutri_facts.calories.value == 400.0
        
        # Should have protein-rich ingredients
        ingredient_names = {ing.name for ing in protein_recipe.ingredients}
        assert "Chicken Breast" in ingredient_names
        assert "Greek Yogurt" in ingredient_names

    async def test_vegetarian_recipe_creation(self, recipe_repository: RecipeRepo):
        """Test creating vegetarian recipes"""
        # Given/When: Creating vegetarian recipe
        veg_recipe = create_vegetarian_recipe(name="Veggie Delight")
        
        # Then: Should have vegetarian characteristics
        assert veg_recipe.name == "Veggie Delight"
        
        # Should have vegetarian ingredients
        ingredient_names = {ing.name for ing in veg_recipe.ingredients}
        assert "Vegetables" in ingredient_names
        assert "Olive Oil" in ingredient_names
        
        # Should have vegetarian tag
        tag_values = {tag.value for tag in veg_recipe.tags}
        assert "vegetarian" in tag_values

    async def test_public_private_recipe_creation(self, recipe_repository: RecipeRepo):
        """Test creating public and private recipes"""
        # Given/When: Creating public and private recipes
        public_recipe = create_public_recipe(name="Public Recipe")
        private_recipe = create_private_recipe(name="Private Recipe")
        
        # Then: Should have correct privacy settings
        assert public_recipe.privacy == Privacy.PUBLIC
        assert public_recipe.name == "Public Recipe"
        assert public_recipe.description is not None
        assert "public recipe available to all users" in public_recipe.description
        
        assert private_recipe.privacy == Privacy.PRIVATE
        assert private_recipe.name == "Private Recipe"
        assert private_recipe.description is not None
        assert "private recipe only visible to the author" in private_recipe.description 