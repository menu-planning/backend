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

from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
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
        filter_key_to_column_name={
            "id": "id",
            "name": "name",
            "description": "description",
            "author_id": "author_id",
            "total_time": "total_time",
            "calorie_density": "calorie_density",
            "like": "like",
            "menu_id": "menu_id",
            "weight_in_grams": "weight_in_grams",
            "discarded": "discarded",
            # Composite field filtering (nutritional facts)
            "protein": "protein",
            "calories": "calories",
            "carbohydrate": "carbohydrate",
            "total_fat": "total_fat",
            "saturated_fat": "saturated_fat",
            "trans_fat": "trans_fat",
            "dietary_fiber": "dietary_fiber",
            "sodium": "sodium",
            "sugar": "sugar",
            "vitamin_a": "vitamin_a",
            "vitamin_c": "vitamin_c",
            "iron": "iron",
            "calcium": "calcium",
            # Percentage field filtering
            "protein_percentage": "protein_percentage",
            "carbo_percentage": "carbo_percentage", 
            "total_fat_percentage": "total_fat_percentage",
        }
    ),
    
    # Single-level join filtering (meal -> recipe)
    FilterColumnMapper(
        sa_model_type=TestRecipeSaModel,
        filter_key_to_column_name={
            "recipe_name": "name",
            "recipe_id": "id",
            "recipe_total_time": "total_time",
            "recipe_instructions": "instructions",
        },
        join_target_and_on_clause=[(TestRecipeSaModel, TestMealSaModel.recipes)]
    ),
    
    # Multi-level join filtering (meal -> recipe -> ingredient)
    FilterColumnMapper(
        sa_model_type=TestIngredientSaModel,
        filter_key_to_column_name={
            "products": "product_id",
            "ingredient_name": "name",
            "ingredient_quantity": "quantity",
        },
        join_target_and_on_clause=[
            (TestRecipeSaModel, TestMealSaModel.recipes),
            (TestIngredientSaModel, TestRecipeSaModel.ingredients)
        ]
    ),
    
    # Multi-level join filtering (meal -> recipe -> rating)
    FilterColumnMapper(
        sa_model_type=TestRatingSaModel,
        filter_key_to_column_name={
            "rating_taste": "taste",
            "rating_user_id": "user_id",
        },
        join_target_and_on_clause=[
            (TestRecipeSaModel, TestMealSaModel.recipes),
            (TestRatingSaModel, TestRecipeSaModel.ratings)
        ]
    ),
    
    # Many-to-many relationship filtering (meal -> tags)
    FilterColumnMapper(
        sa_model_type=TestTagSaModel,
        filter_key_to_column_name={
            "tag_key": "key",
            "tag_value": "value",
            "tag_type": "type",
        },
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
        filter_key_to_column_name={
            "name": "name",
            "author_id": "author_id",
            "meal_id": "meal_id",
            "total_time": "total_time",
            "instructions": "instructions",
            "privacy": "privacy",
            "discarded": "discarded",
            "average_taste_rating": "average_taste_rating",
            # Composite field filtering for recipes
            "recipe_protein": "protein",
            "recipe_calories": "calories",
            "calorie_density": "calorie_density",
        }
    ),
    
    # Single-level join filtering (recipe -> ingredient)
    FilterColumnMapper(
        sa_model_type=TestIngredientSaModel,
        filter_key_to_column_name={
            "ingredient_name": "name",
            "ingredient_product_id": "product_id",
            "ingredient_unit": "unit",
            "ingredient_position": "position",
        },
        join_target_and_on_clause=[(TestIngredientSaModel, TestRecipeSaModel.ingredients)]
    ),
    
    # Single-level join filtering (recipe -> rating)
    FilterColumnMapper(
        sa_model_type=TestRatingSaModel,
        filter_key_to_column_name={
            "rating_taste": "taste",
            "rating_convenience": "convenience",
            "rating_user_id": "user_id",
        },
        join_target_and_on_clause=[(TestRatingSaModel, TestRecipeSaModel.ratings)]
    ),
    
    # Many-to-many relationship filtering (recipe -> tags)
    FilterColumnMapper(
        sa_model_type=TestTagSaModel,
        filter_key_to_column_name={
            "tag_key": "key",
            "tag_value": "value",
        },
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
        filter_key_to_column_name={
            "circular_a_name": "name",
            "circular_a_id": "id",
            "b_ref_id": "b_ref_id",
        }
    ),
    
    # Circular relationship filtering (A -> B)
    FilterColumnMapper(
        sa_model_type=TestCircularModelB,
        filter_key_to_column_name={
            "circular_b_name": "name",
            "circular_b_id": "id",
        },
        join_target_and_on_clause=[(TestCircularModelB, TestCircularModelA.b_ref)]
    ),
    
    # Self-referential model filtering
    FilterColumnMapper(
        sa_model_type=TestSelfReferentialModel,
        filter_key_to_column_name={
            "self_ref_name": "name",
            "self_ref_id": "id",
            "self_ref_level": "level",
            "parent_id": "parent_id",
        }
    ),
    
    # Self-referential join filtering (parent relationship)
    FilterColumnMapper(
        sa_model_type=TestSelfReferentialModel,
        filter_key_to_column_name={
            "parent_name": "name",
            "parent_level": "level",
        },
        join_target_and_on_clause=[(TestSelfReferentialModel, TestSelfReferentialModel.parent)]
    ),
    
    # Self-referential many-to-many filtering (friends relationship)
    FilterColumnMapper(
        sa_model_type=TestSelfReferentialModel,
        filter_key_to_column_name={
            "friend_name": "name",
            "friend_level": "level",
        },
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
        filter_key_to_column_name={
            "name": "name",
            "author_id": "author_id",
            "total_time": "total_time",
        }
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
        filter_key_to_column_name={
            "taste": "taste",
            "convenience": "convenience",
        },
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
        filter_key_to_column_name={
            "key": "key",
            "value": "value",
            "author_id": "author_id",
            "type": "type",
        }
    ),
]