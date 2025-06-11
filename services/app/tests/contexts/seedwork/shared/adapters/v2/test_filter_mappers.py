"""
Filter column mapper configurations for repository testing

This module contains FilterColumnMapper configurations that define how
filter parameters in repository queries are mapped to actual database
columns and relationships. These configurations enable the SaGenericRepository
to build complex SQL queries with joins, filters, and aggregations.

Key testing scenarios covered:
- Simple column filtering (direct attribute mapping)
- Join-based filtering (filtering by related entity attributes)
- Multi-level joins (filtering through multiple relationship hops)
- Composite field filtering (filtering by parts of composite types)
- Edge case relationships (circular, self-referential)

Each filter mapper specifies:
- Which SQLAlchemy model contains the target column
- How filter keys map to actual column names
- Join paths needed to reach the target column
"""

from src.contexts.seedwork.shared.adapters.repositories.seedwork_repository import FilterColumnMapper

from .test_models import (
    TestMealSaModel, TestRecipeSaModel, TestIngredientSaModel, TestTagSaModel,
    TestRatingSaModel, TestCircularModelA, TestCircularModelB, TestSelfReferentialModel
)

# =============================================================================
# MEAL FILTER MAPPERS - Test meal filtering scenarios
# =============================================================================

TEST_MEAL_FILTER_MAPPERS: list[FilterColumnMapper] = [
    # Direct meal attribute filtering
    FilterColumnMapper(
        sa_model_type=TestMealSaModel,
        filter_key_to_column_name={"name": "name"}
    ),
    FilterColumnMapper(
        sa_model_type=TestMealSaModel,
        filter_key_to_column_name={"author_id": "author_id"}
    ),
    FilterColumnMapper(
        sa_model_type=TestMealSaModel,
        filter_key_to_column_name={"total_time": "total_time"}
    ),
    FilterColumnMapper(
        sa_model_type=TestMealSaModel,
        filter_key_to_column_name={"calorie_density": "calorie_density"}
    ),
    FilterColumnMapper(
        sa_model_type=TestMealSaModel,
        filter_key_to_column_name={"like": "like"}
    ),
    FilterColumnMapper(
        sa_model_type=TestMealSaModel,
        filter_key_to_column_name={"menu_id": "menu_id"}
    ),
    FilterColumnMapper(
        sa_model_type=TestMealSaModel,
        filter_key_to_column_name={"weight_in_grams": "weight_in_grams"}
    ),
    FilterColumnMapper(
        sa_model_type=TestMealSaModel,
        filter_key_to_column_name={"discarded": "discarded"}
    ),
    
    # Composite field filtering (nutritional facts)
    FilterColumnMapper(
        sa_model_type=TestMealSaModel,
        filter_key_to_column_name={"protein": "protein"}
    ),
    FilterColumnMapper(
        sa_model_type=TestMealSaModel,
        filter_key_to_column_name={"calories": "calories"}
    ),
    FilterColumnMapper(
        sa_model_type=TestMealSaModel,
        filter_key_to_column_name={"carbohydrate": "carbohydrate"}
    ),
    FilterColumnMapper(
        sa_model_type=TestMealSaModel,
        filter_key_to_column_name={"total_fat": "total_fat"}
    ),
    
    # Single-level join filtering (meal -> recipe)
    FilterColumnMapper(
        sa_model_type=TestRecipeSaModel,
        filter_key_to_column_name={"recipe_name": "name"},
        join_target_and_on_clause=[(TestRecipeSaModel, TestMealSaModel.recipes)]
    ),
    FilterColumnMapper(
        sa_model_type=TestRecipeSaModel,
        filter_key_to_column_name={"recipe_id": "id"},
        join_target_and_on_clause=[(TestRecipeSaModel, TestMealSaModel.recipes)]
    ),
    FilterColumnMapper(
        sa_model_type=TestRecipeSaModel,
        filter_key_to_column_name={"recipe_total_time": "total_time"},
        join_target_and_on_clause=[(TestRecipeSaModel, TestMealSaModel.recipes)]
    ),
    FilterColumnMapper(
        sa_model_type=TestRecipeSaModel,
        filter_key_to_column_name={"recipe_instructions": "instructions"},
        join_target_and_on_clause=[(TestRecipeSaModel, TestMealSaModel.recipes)]
    ),
    
    # Multi-level join filtering (meal -> recipe -> ingredient)
    FilterColumnMapper(
        sa_model_type=TestIngredientSaModel,
        filter_key_to_column_name={"products": "product_id"},
        join_target_and_on_clause=[
            (TestRecipeSaModel, TestMealSaModel.recipes),
            (TestIngredientSaModel, TestRecipeSaModel.ingredients)
        ]
    ),
    FilterColumnMapper(
        sa_model_type=TestIngredientSaModel,
        filter_key_to_column_name={"ingredient_name": "name"},
        join_target_and_on_clause=[
            (TestRecipeSaModel, TestMealSaModel.recipes),
            (TestIngredientSaModel, TestRecipeSaModel.ingredients)
        ]
    ),
    FilterColumnMapper(
        sa_model_type=TestIngredientSaModel,
        filter_key_to_column_name={"ingredient_quantity": "quantity"},
        join_target_and_on_clause=[
            (TestRecipeSaModel, TestMealSaModel.recipes),
            (TestIngredientSaModel, TestRecipeSaModel.ingredients)
        ]
    ),
    
    # Multi-level join filtering (meal -> recipe -> rating)
    FilterColumnMapper(
        sa_model_type=TestRatingSaModel,
        filter_key_to_column_name={"rating_taste": "taste"},
        join_target_and_on_clause=[
            (TestRecipeSaModel, TestMealSaModel.recipes),
            (TestRatingSaModel, TestRecipeSaModel.ratings)
        ]
    ),
    FilterColumnMapper(
        sa_model_type=TestRatingSaModel,
        filter_key_to_column_name={"rating_user_id": "user_id"},
        join_target_and_on_clause=[
            (TestRecipeSaModel, TestMealSaModel.recipes),
            (TestRatingSaModel, TestRecipeSaModel.ratings)
        ]
    ),
    
    # Many-to-many relationship filtering (meal -> tags)
    FilterColumnMapper(
        sa_model_type=TestTagSaModel,
        filter_key_to_column_name={"tag_key": "key"},
        join_target_and_on_clause=[(TestTagSaModel, TestMealSaModel.tags)]
    ),
    FilterColumnMapper(
        sa_model_type=TestTagSaModel,
        filter_key_to_column_name={"tag_value": "value"},
        join_target_and_on_clause=[(TestTagSaModel, TestMealSaModel.tags)]
    ),
    FilterColumnMapper(
        sa_model_type=TestTagSaModel,
        filter_key_to_column_name={"tag_type": "type"},
        join_target_and_on_clause=[(TestTagSaModel, TestMealSaModel.tags)]
    ),
]

# =============================================================================
# RECIPE FILTER MAPPERS - Test recipe filtering scenarios
# =============================================================================

TEST_RECIPE_FILTER_MAPPERS: list[FilterColumnMapper] = [
    # Direct recipe attribute filtering
    FilterColumnMapper(
        sa_model_type=TestRecipeSaModel,
        filter_key_to_column_name={"name": "name"}
    ),
    FilterColumnMapper(
        sa_model_type=TestRecipeSaModel,
        filter_key_to_column_name={"author_id": "author_id"}
    ),
    FilterColumnMapper(
        sa_model_type=TestRecipeSaModel,
        filter_key_to_column_name={"meal_id": "meal_id"}
    ),
    FilterColumnMapper(
        sa_model_type=TestRecipeSaModel,
        filter_key_to_column_name={"total_time": "total_time"}
    ),
    FilterColumnMapper(
        sa_model_type=TestRecipeSaModel,
        filter_key_to_column_name={"instructions": "instructions"}
    ),
    FilterColumnMapper(
        sa_model_type=TestRecipeSaModel,
        filter_key_to_column_name={"privacy": "privacy"}
    ),
    FilterColumnMapper(
        sa_model_type=TestRecipeSaModel,
        filter_key_to_column_name={"discarded": "discarded"}
    ),
    FilterColumnMapper(
        sa_model_type=TestRecipeSaModel,
        filter_key_to_column_name={"average_taste_rating": "average_taste_rating"}
    ),
    
    # Composite field filtering for recipes
    FilterColumnMapper(
        sa_model_type=TestRecipeSaModel,
        filter_key_to_column_name={"recipe_protein": "protein"}
    ),
    FilterColumnMapper(
        sa_model_type=TestRecipeSaModel,
        filter_key_to_column_name={"recipe_calories": "calories"}
    ),
    FilterColumnMapper(
        sa_model_type=TestRecipeSaModel,
        filter_key_to_column_name={"calorie_density": "calorie_density"}
    ),
    
    # Single-level join filtering (recipe -> ingredient)
    FilterColumnMapper(
        sa_model_type=TestIngredientSaModel,
        filter_key_to_column_name={"ingredient_name": "name"},
        join_target_and_on_clause=[(TestIngredientSaModel, TestRecipeSaModel.ingredients)]
    ),
    FilterColumnMapper(
        sa_model_type=TestIngredientSaModel,
        filter_key_to_column_name={"ingredient_product_id": "product_id"},
        join_target_and_on_clause=[(TestIngredientSaModel, TestRecipeSaModel.ingredients)]
    ),
    FilterColumnMapper(
        sa_model_type=TestIngredientSaModel,
        filter_key_to_column_name={"ingredient_unit": "unit"},
        join_target_and_on_clause=[(TestIngredientSaModel, TestRecipeSaModel.ingredients)]
    ),
    FilterColumnMapper(
        sa_model_type=TestIngredientSaModel,
        filter_key_to_column_name={"ingredient_position": "position"},
        join_target_and_on_clause=[(TestIngredientSaModel, TestRecipeSaModel.ingredients)]
    ),
    
    # Single-level join filtering (recipe -> rating)
    FilterColumnMapper(
        sa_model_type=TestRatingSaModel,
        filter_key_to_column_name={"rating_taste": "taste"},
        join_target_and_on_clause=[(TestRatingSaModel, TestRecipeSaModel.ratings)]
    ),
    FilterColumnMapper(
        sa_model_type=TestRatingSaModel,
        filter_key_to_column_name={"rating_convenience": "convenience"},
        join_target_and_on_clause=[(TestRatingSaModel, TestRecipeSaModel.ratings)]
    ),
    FilterColumnMapper(
        sa_model_type=TestRatingSaModel,
        filter_key_to_column_name={"rating_user_id": "user_id"},
        join_target_and_on_clause=[(TestRatingSaModel, TestRecipeSaModel.ratings)]
    ),
    
    # Many-to-many relationship filtering (recipe -> tags)
    FilterColumnMapper(
        sa_model_type=TestTagSaModel,
        filter_key_to_column_name={"tag_key": "key"},
        join_target_and_on_clause=[(TestTagSaModel, TestRecipeSaModel.tags)]
    ),
    FilterColumnMapper(
        sa_model_type=TestTagSaModel,
        filter_key_to_column_name={"tag_value": "value"},
        join_target_and_on_clause=[(TestTagSaModel, TestRecipeSaModel.tags)]
    ),
]

# =============================================================================
# EDGE CASE FILTER MAPPERS - Test complex relationship scenarios
# =============================================================================

TEST_EDGE_CASE_FILTER_MAPPERS: list[FilterColumnMapper] = [
    # Circular model A filtering
    FilterColumnMapper(
        sa_model_type=TestCircularModelA,
        filter_key_to_column_name={"circular_a_name": "name"}
    ),
    FilterColumnMapper(
        sa_model_type=TestCircularModelA,
        filter_key_to_column_name={"circular_a_id": "id"}
    ),
    FilterColumnMapper(
        sa_model_type=TestCircularModelA,
        filter_key_to_column_name={"b_ref_id": "b_ref_id"}
    ),
    
    # Circular relationship filtering (A -> B)
    FilterColumnMapper(
        sa_model_type=TestCircularModelB,
        filter_key_to_column_name={"circular_b_name": "name"},
        join_target_and_on_clause=[(TestCircularModelB, TestCircularModelA.b_ref)]
    ),
    FilterColumnMapper(
        sa_model_type=TestCircularModelB,
        filter_key_to_column_name={"circular_b_id": "id"},
        join_target_and_on_clause=[(TestCircularModelB, TestCircularModelA.b_ref)]
    ),
    
    # Self-referential model filtering
    FilterColumnMapper(
        sa_model_type=TestSelfReferentialModel,
        filter_key_to_column_name={"self_ref_name": "name"}
    ),
    FilterColumnMapper(
        sa_model_type=TestSelfReferentialModel,
        filter_key_to_column_name={"self_ref_id": "id"}
    ),
    FilterColumnMapper(
        sa_model_type=TestSelfReferentialModel,
        filter_key_to_column_name={"self_ref_level": "level"}
    ),
    FilterColumnMapper(
        sa_model_type=TestSelfReferentialModel,
        filter_key_to_column_name={"parent_id": "parent_id"}
    ),
    
    # Self-referential join filtering (parent relationship)
    FilterColumnMapper(
        sa_model_type=TestSelfReferentialModel,
        filter_key_to_column_name={"parent_name": "name"},
        join_target_and_on_clause=[(TestSelfReferentialModel, TestSelfReferentialModel.parent)]
    ),
    FilterColumnMapper(
        sa_model_type=TestSelfReferentialModel,
        filter_key_to_column_name={"parent_level": "level"},
        join_target_and_on_clause=[(TestSelfReferentialModel, TestSelfReferentialModel.parent)]
    ),
    
    # Self-referential many-to-many filtering (friends relationship)
    FilterColumnMapper(
        sa_model_type=TestSelfReferentialModel,
        filter_key_to_column_name={"friend_name": "name"},
        join_target_and_on_clause=[(TestSelfReferentialModel, TestSelfReferentialModel.friends)]
    ),
    FilterColumnMapper(
        sa_model_type=TestSelfReferentialModel,
        filter_key_to_column_name={"friend_level": "level"},
        join_target_and_on_clause=[(TestSelfReferentialModel, TestSelfReferentialModel.friends)]
    ),
]

# =============================================================================
# PERFORMANCE TEST FILTER MAPPERS - For benchmark testing
# =============================================================================

TEST_PERFORMANCE_FILTER_MAPPERS: list[FilterColumnMapper] = [
    # Simple filters for performance baseline
    FilterColumnMapper(
        sa_model_type=TestMealSaModel,
        filter_key_to_column_name={"name": "name"}
    ),
    FilterColumnMapper(
        sa_model_type=TestMealSaModel,
        filter_key_to_column_name={"author_id": "author_id"}
    ),
    FilterColumnMapper(
        sa_model_type=TestMealSaModel,
        filter_key_to_column_name={"total_time": "total_time"}
    ),
    
    # Complex joins for performance stress testing
    FilterColumnMapper(
        sa_model_type=TestIngredientSaModel,
        filter_key_to_column_name={"products": "product_id"},
        join_target_and_on_clause=[
            (TestRecipeSaModel, TestMealSaModel.recipes),
            (TestIngredientSaModel, TestRecipeSaModel.ingredients)
        ]
    ),
    FilterColumnMapper(
        sa_model_type=TestRatingSaModel,
        filter_key_to_column_name={"rating_taste": "taste"},
        join_target_and_on_clause=[
            (TestRecipeSaModel, TestMealSaModel.recipes),
            (TestRatingSaModel, TestRecipeSaModel.ratings)
        ]
    ),
]

# =============================================================================
# SPECIALIZED FILTER MAPPERS - For specific test scenarios
# =============================================================================

# Filter mappers for testing constraint validation
TEST_CONSTRAINT_FILTER_MAPPERS: list[FilterColumnMapper] = [
    # Test check constraints
    FilterColumnMapper(
        sa_model_type=TestRatingSaModel,
        filter_key_to_column_name={"taste": "taste"},
        join_target_and_on_clause=[(TestRatingSaModel, TestRecipeSaModel.ratings)]
    ),
    FilterColumnMapper(
        sa_model_type=TestRatingSaModel,
        filter_key_to_column_name={"convenience": "convenience"},
        join_target_and_on_clause=[(TestRatingSaModel, TestRecipeSaModel.ratings)]
    ),
    
    # Test positive quantity constraints
    FilterColumnMapper(
        sa_model_type=TestIngredientSaModel,
        filter_key_to_column_name={"quantity": "quantity"},
        join_target_and_on_clause=[(TestIngredientSaModel, TestRecipeSaModel.ingredients)]
    ),
    FilterColumnMapper(
        sa_model_type=TestMealSaModel,
        filter_key_to_column_name={"weight_in_grams": "weight_in_grams"}
    ),
]

# Filter mappers for testing unique constraints
TEST_UNIQUE_CONSTRAINT_FILTER_MAPPERS: list[FilterColumnMapper] = [
    # Test unique tag constraints
    FilterColumnMapper(
        sa_model_type=TestTagSaModel,
        filter_key_to_column_name={"key": "key"}
    ),
    FilterColumnMapper(
        sa_model_type=TestTagSaModel,
        filter_key_to_column_name={"value": "value"}
    ),
    FilterColumnMapper(
        sa_model_type=TestTagSaModel,
        filter_key_to_column_name={"author_id": "author_id"}
    ),
    FilterColumnMapper(
        sa_model_type=TestTagSaModel,
        filter_key_to_column_name={"type": "type"}
    ),
]