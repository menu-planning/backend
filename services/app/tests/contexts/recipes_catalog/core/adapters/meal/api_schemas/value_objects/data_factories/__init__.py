# Test package for meal repositories 

# Data factories for API value objects testing
from .api_rating_data_factories import (
    # Rating factory functions
    create_api_rating,
    create_api_rating_kwargs,
    create_api_rating_from_json,
    create_api_rating_json,
    reset_api_rating_counters,
    
    # Specialized rating factories
    create_excellent_rating,
    create_poor_rating,
    create_mixed_rating,
    create_rating_without_comment,
    create_rating_with_empty_comment,
    create_rating_with_max_comment,
    create_quick_easy_rating,
    create_gourmet_rating,
    
    # Rating test helpers
    create_api_ratings_with_different_users,
    create_api_ratings_for_different_recipes,
    create_rating_range_dataset,
    create_test_rating_dataset,
    
    # Rating conversion helpers
    create_rating_domain_from_api,
    create_api_rating_from_domain,
    create_rating_orm_kwargs_from_api,
    
    # Rating JSON validation
    create_valid_json_test_cases as create_valid_rating_json_test_cases,
    create_invalid_json_test_cases as create_invalid_rating_json_test_cases,
    check_json_serialization_roundtrip as test_rating_json_serialization_roundtrip,
)

from .api_ingredient_data_factories import (
    # Ingredient factory functions
    create_api_ingredient,
    create_api_ingredient_kwargs,
    create_api_ingredient_from_json,
    create_api_ingredient_json,
    reset_api_ingredient_counters,
    
    # Specialized ingredient factories
    create_spice_ingredient,
    create_vegetable_ingredient,
    create_meat_ingredient,
    create_liquid_ingredient,
    create_baking_ingredient,
    create_minimal_ingredient,
    create_ingredient_with_product_id,
    create_ingredient_with_max_name,
    create_ingredient_with_max_full_text,
    create_ingredient_with_max_quantity,
    create_ingredient_with_max_position,
    
    # Ingredient test helpers
    create_recipe_ingredients,
    create_ingredients_with_all_units,
    create_ingredients_with_different_quantities,
    create_test_ingredient_dataset,
    
    # Ingredient conversion helpers
    create_ingredient_domain_from_api,
    create_api_ingredient_from_domain,
    create_ingredient_orm_kwargs_from_api,
    
    # Ingredient JSON validation
    create_valid_json_test_cases as create_valid_ingredient_json_test_cases,
    create_invalid_json_test_cases as create_invalid_ingredient_json_test_cases,
    check_json_serialization_roundtrip as test_ingredient_json_serialization_roundtrip,
)

__all__ = [
    # Rating factory functions
    "create_api_rating",
    "create_api_rating_kwargs",
    "create_api_rating_from_json",
    "create_api_rating_json",
    "reset_api_rating_counters",
    
    # Specialized rating factories
    "create_excellent_rating",
    "create_poor_rating",
    "create_mixed_rating",
    "create_rating_without_comment",
    "create_rating_with_empty_comment",
    "create_rating_with_max_comment",
    "create_quick_easy_rating",
    "create_gourmet_rating",
    
    # Rating test helpers
    "create_api_ratings_with_different_users",
    "create_api_ratings_for_different_recipes",
    "create_rating_range_dataset",
    "create_test_rating_dataset",
    
    # Rating conversion helpers
    "create_rating_domain_from_api",
    "create_api_rating_from_domain",
    "create_rating_orm_kwargs_from_api",
    
    # Rating JSON validation
    "create_valid_rating_json_test_cases",
    "create_invalid_rating_json_test_cases",
    "test_rating_json_serialization_roundtrip",
    
    # Ingredient factory functions
    "create_api_ingredient",
    "create_api_ingredient_kwargs",
    "create_api_ingredient_from_json",
    "create_api_ingredient_json",
    "reset_api_ingredient_counters",
    
    # Specialized ingredient factories
    "create_spice_ingredient",
    "create_vegetable_ingredient",
    "create_meat_ingredient",
    "create_liquid_ingredient",
    "create_baking_ingredient",
    "create_minimal_ingredient",
    "create_ingredient_with_product_id",
    "create_ingredient_with_max_name",
    "create_ingredient_with_max_full_text",
    "create_ingredient_with_max_quantity",
    "create_ingredient_with_max_position",
    
    # Ingredient test helpers
    "create_recipe_ingredients",
    "create_ingredients_with_all_units",
    "create_ingredients_with_different_quantities",
    "create_test_ingredient_dataset",
    
    # Ingredient conversion helpers
    "create_ingredient_domain_from_api",
    "create_api_ingredient_from_domain",
    "create_ingredient_orm_kwargs_from_api",
    
    # Ingredient JSON validation
    "create_valid_ingredient_json_test_cases",
    "create_invalid_ingredient_json_test_cases",
    "test_ingredient_json_serialization_roundtrip",
] 