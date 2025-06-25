"""
Test data creation utilities following seedwork patterns and best practices

This module provides factory functions for creating test entities and data
with deterministic attributes. Following the patterns from meal_benchmark_data_factories.py,
these factories ensure:

- Consistent test data generation with deterministic counters
- Comprehensive attribute validation using check_missing_attributes
- Flexible parameter overrides via kwargs
- Realistic data relationships and constraints
- Support for edge cases and performance testing
- Both domain and ORM variants for complete coverage

Key principles:
- Always validate required attributes are present using check_missing_attributes
- Provide sensible defaults for optional attributes  
- Allow easy override of any attribute via kwargs
- Generate realistic data that respects business constraints
- Support both individual entity creation and bulk dataset generation
- Use deterministic counters for consistent test behavior
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from .entities import (
    TestMealEntity, TestRecipeEntity, TestCircularEntityA, TestCircularEntityB,
    TestSelfReferentialEntity, TestTagEntity, TestRatingEntity, TestIngredientEntity
)

# Import ORM models
from .models import (
    MealSaTestModel, RecipeSaTestModel, TagSaTestModel, RatingSaTestModel,
    IngredientSaTestModel, CircularTestModelA, CircularTestModelB,
    SelfReferentialTestModel, SupplierSaTestModel, CategorySaTestModel,
    ProductSaTestModel, CustomerSaTestModel, OrderSaTestModel,
    NutriFactsTestSaModel
)

# Import comprehensive validation utility
from tests.utils import check_missing_attributes

# =============================================================================
# UTILITY FUNCTIONS (inspired by random_refs.py)
# =============================================================================

# Static counters for deterministic IDs
_MEAL_COUNTER = 1
_RECIPE_COUNTER = 1
_TAG_COUNTER = 1
_RATING_COUNTER = 1
_INGREDIENT_COUNTER = 1
_SUPPLIER_COUNTER = 1
_CATEGORY_COUNTER = 1
_PRODUCT_COUNTER = 1
_CUSTOMER_COUNTER = 1
_ORDER_COUNTER = 1
_GENERAL_COUNTER = 1

def deterministic_suffix(module_name: str = "") -> str:
    """Generate deterministic suffix for test data"""
    global _GENERAL_COUNTER
    suffix = f"{_GENERAL_COUNTER:06d}{module_name}"
    _GENERAL_COUNTER += 1
    return suffix

def deterministic_attr(attr: str = "") -> str:
    """Generate deterministic attribute with prefix"""
    return f"{attr}-{deterministic_suffix()}"

# =============================================================================
# MAIN ENTITY FACTORIES
# =============================================================================

def create_test_meal_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create test meal kwargs with deterministic values and comprehensive validation.
    
    Generates all required attributes for TestMealEntity with realistic defaults.
    Uses check_missing_attributes to ensure all required fields are present.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required meal creation parameters
    """
    global _MEAL_COUNTER
    
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    # Default to positive percentages that add up correctly
    default_carbo = 50.0
    default_protein = 25.0
    default_fat = 25.0
    
    # Create basic nutri_facts for meal testing
    default_nutri_facts = NutriFacts(
        calories=250.0,  # Base calories for 250g serving
        protein=62.5,    # 25% of 250g
        carbohydrate=125.0,  # 50% of 250g 
        total_fat=62.5,  # 25% of 250g
        saturated_fat=20.8,  # 1/3 of total fat
        trans_fat=0.0,
        dietary_fiber=25.0,
        sodium=2.0,
        sugar=10.0
    )
    
    final_kwargs = {
        "id": kwargs.get("id", f"test_meal_{_MEAL_COUNTER:03d}"),
        "name": kwargs.get("name", f"Test Meal {_MEAL_COUNTER}"),
        "author_id": kwargs.get("author_id", f"test_author_{(_MEAL_COUNTER % 5) + 1}"),
        "description": kwargs.get("description", f"Test meal description {_MEAL_COUNTER}"),
        "notes": kwargs.get("notes", f"Test notes for meal {_MEAL_COUNTER}"),
        "like": kwargs.get("like", _MEAL_COUNTER % 3 == 0),  # Every 3rd meal is liked
        "weight_in_grams": kwargs.get("weight_in_grams", 250.0),
        "calorie_density": kwargs.get("calorie_density", 250.0),  # 250 cal per 100g
        "carbo_percentage": kwargs.get("carbo_percentage", default_carbo),
        "protein_percentage": kwargs.get("protein_percentage", default_protein),
        "total_fat_percentage": kwargs.get("total_fat_percentage", default_fat),
        "total_time": kwargs.get("total_time", 30),
        "image_url": kwargs.get("image_url", f"https://example.com/test_meal_{_MEAL_COUNTER}.jpg" if _MEAL_COUNTER % 2 == 0 else None),
        "recipes": kwargs.get("recipes", []),
        "tags": kwargs.get("tags", set()),
        "nutri_facts": kwargs.get("nutri_facts", default_nutri_facts),
        "created_at": kwargs.get("created_at", base_time + timedelta(hours=_MEAL_COUNTER)),
        "updated_at": kwargs.get("updated_at", base_time + timedelta(hours=_MEAL_COUNTER, minutes=30)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
    }
    final_kwargs["preprocessed_name"] = final_kwargs["name"].lower()
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(TestMealEntity, final_kwargs)
    assert not missing, f"Missing attributes for TestMealEntity: {missing}"
    
    # Increment counter for next call
    _MEAL_COUNTER += 1
    
    return final_kwargs

def create_test_meal(**kwargs) -> TestMealEntity:
    """
    Create test meal entity with deterministic data and comprehensive validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        TestMealEntity with all required attributes validated
    """
    return TestMealEntity(**create_test_meal_kwargs(**kwargs))

def create_test_recipe_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create test recipe kwargs with deterministic values and comprehensive validation.
    
    Generates all required attributes for TestRecipeEntity with realistic defaults.
    Includes complex nutritional data and rating information.
    Uses check_missing_attributes to ensure completeness.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required recipe creation parameters
    """
    global _RECIPE_COUNTER
    base_name = kwargs.get("name", f"recipe_name-{_RECIPE_COUNTER:06d}")
    
    final_kwargs = {
        "id": kwargs.get("id", f"recipe-{_RECIPE_COUNTER:06d}"),
        "name": base_name,
        "author_id": kwargs.get("author_id", f"author-{_RECIPE_COUNTER:06d}"),
        "meal_id": kwargs.get("meal_id", None),
        "instructions": kwargs.get("instructions", f"instructions-{_RECIPE_COUNTER:06d}"),
        "preprocessed_name": kwargs.get("preprocessed_name", base_name.lower()),
        "description": kwargs.get("description", f"recipe_description-{_RECIPE_COUNTER:06d}"),
        "utensils": kwargs.get("utensils", f"utensils-{_RECIPE_COUNTER:06d}"),
        "total_time": kwargs.get("total_time", 30),  # Default cooking time
        "notes": kwargs.get("notes", f"recipe_notes-{_RECIPE_COUNTER:06d}"),
        "privacy": kwargs.get("privacy", "PUBLIC"),  # Default public
        "weight_in_grams": kwargs.get("weight_in_grams", 200),  # Default recipe portion
        "calorie_density": kwargs.get("calorie_density", 300.0),  # Default calorie density
        "carbo_percentage": kwargs.get("carbo_percentage", 45.0),  # Default balanced macro
        "protein_percentage": kwargs.get("protein_percentage", 25.0),  # Default balanced macro
        "total_fat_percentage": kwargs.get("total_fat_percentage", 30.0),  # Default balanced macro
        "image_url": kwargs.get("image_url", f"recipe_image-{_RECIPE_COUNTER:06d}"),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc).replace(tzinfo=None)),
        "updated_at": kwargs.get("updated_at", datetime.now(timezone.utc).replace(tzinfo=None)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
        "average_taste_rating": kwargs.get("average_taste_rating", 4.0),  # Default good rating
        "average_convenience_rating": kwargs.get("average_convenience_rating", 3.5),  # Default moderate convenience
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(TestRecipeEntity, final_kwargs)
    assert not missing, f"Missing attributes for TestRecipeEntity: {missing}"
    
    # Increment counter for next call
    _RECIPE_COUNTER += 1
    
    return final_kwargs

def create_test_recipe(**kwargs) -> TestRecipeEntity:
    """
    Create test recipe entity with deterministic data and comprehensive validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        TestRecipeEntity with all required attributes validated
    """
    return TestRecipeEntity(**create_test_recipe_kwargs(**kwargs))

# =============================================================================
# RELATIONSHIP ENTITY FACTORIES
# =============================================================================

def create_test_tag_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test tag kwargs with validation"""
    global _TAG_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", _TAG_COUNTER),
        "key": kwargs.get("key", "cuisine"),  # Default key
        "value": kwargs.get("value", f"tag_value-{_TAG_COUNTER:06d}"),
        "author_id": kwargs.get("author_id", f"author-{_TAG_COUNTER:06d}"),
        "type": kwargs.get("type", "meal"),  # Default type
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Increment counter for next call
    _TAG_COUNTER += 1
    
    # Validate all required attributes are present
    missing = check_missing_attributes(TestTagEntity, final_kwargs)
    assert not missing, f"Missing attributes for TestTagEntity: {missing}"
    
    return final_kwargs

def create_test_tag(**kwargs) -> TestTagEntity:
    """Create test tag entity with random data"""
    return TestTagEntity(**create_test_tag_kwargs(**kwargs))

def create_test_rating_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test rating kwargs with constraint validation"""
    global _RATING_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", _RATING_COUNTER),
        "user_id": kwargs.get("user_id", f"user-{_RATING_COUNTER:06d}"),
        "recipe_id": kwargs.get("recipe_id", f"recipe-{_RATING_COUNTER:06d}"),
        "taste": kwargs.get("taste", 4),  # Default good taste rating
        "convenience": kwargs.get("convenience", 3),  # Default moderate convenience
        "comment": kwargs.get("comment", f"rating_comment-{_RATING_COUNTER:06d}"),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc).replace(tzinfo=None)),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Increment counter for next call
    _RATING_COUNTER += 1
    
    # Validate constraint bounds
    assert 0 <= final_kwargs["taste"] <= 5, f"Taste rating must be 0-5, got {final_kwargs['taste']}"
    assert 0 <= final_kwargs["convenience"] <= 5, f"Convenience rating must be 0-5, got {final_kwargs['convenience']}"
    
    # Validate all required attributes are present
    missing = check_missing_attributes(TestRatingEntity, final_kwargs)
    assert not missing, f"Missing attributes for TestRatingEntity: {missing}"
    
    return final_kwargs

def create_test_rating(**kwargs) -> TestRatingEntity:
    """Create test rating entity with random data"""
    return TestRatingEntity(**create_test_rating_kwargs(**kwargs))

def create_test_ingredient_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test ingredient entity kwargs with realistic data"""
    global _INGREDIENT_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", _INGREDIENT_COUNTER),
        "name": kwargs.get("name", f"Ingredient-{_INGREDIENT_COUNTER:06d}"),
        "quantity": kwargs.get("quantity", 100.0),  # Default quantity
        "unit": kwargs.get("unit", "grams"),  # Default unit
        "recipe_id": kwargs.get("recipe_id", f"recipe-{_INGREDIENT_COUNTER:06d}"),
        "position": kwargs.get("position", 0),
        "product_id": kwargs.get("product_id", None),
        # Entity base class attributes
        "created_at": kwargs.get("created_at", None),
        "discarded": kwargs.get("discarded", False),
        "updated_at": kwargs.get("updated_at", None),
        "version": kwargs.get("version", 1),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Increment counter for next call
    _INGREDIENT_COUNTER += 1
    
    # Validate constraint bounds
    assert final_kwargs["quantity"] > 0, f"Quantity must be positive, got {final_kwargs['quantity']}"
    
    # Validate all required attributes are present
    missing = check_missing_attributes(TestIngredientEntity, final_kwargs)
    assert not missing, f"Missing attributes for TestIngredientEntity: {missing}"
    
    return final_kwargs

def create_test_ingredient(**kwargs) -> TestIngredientEntity:
    """Create test ingredient entity with random data"""
    return TestIngredientEntity(**create_test_ingredient_kwargs(**kwargs))

# =============================================================================
# EDGE CASE ENTITY FACTORIES
# =============================================================================

def create_test_circular_a_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test circular entity A kwargs"""
    global _GENERAL_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", f"circular_a-{_GENERAL_COUNTER:06d}"),
        "name": kwargs.get("name", f"circular_a_name-{_GENERAL_COUNTER:06d}"),
        "b_ref_id": kwargs.get("b_ref_id", None),  # Can reference circular B
    }
    _GENERAL_COUNTER += 1
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_circular_a(**kwargs) -> TestCircularEntityA:
    """Create test circular entity A with random data"""
    return TestCircularEntityA(**create_test_circular_a_kwargs(**kwargs))

def create_test_circular_b_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test circular entity B kwargs"""
    global _GENERAL_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", f"circular_b-{_GENERAL_COUNTER:06d}"),
        "name": kwargs.get("name", f"circular_b_name-{_GENERAL_COUNTER:06d}"),
    }
    _GENERAL_COUNTER += 1
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_circular_b(**kwargs) -> TestCircularEntityB:
    """Create test circular entity B with random data"""
    return TestCircularEntityB(**create_test_circular_b_kwargs(**kwargs))

def create_test_self_ref_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test self-referential entity kwargs"""
    global _GENERAL_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", f"self_ref-{_GENERAL_COUNTER:06d}"),
        "name": kwargs.get("name", f"self_ref_name-{_GENERAL_COUNTER:06d}"),
        "parent_id": kwargs.get("parent_id", None),  # Can reference another self_ref
        "level": kwargs.get("level", 0),
    }
    _GENERAL_COUNTER += 1
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_self_ref(**kwargs) -> TestSelfReferentialEntity:
    """Create test self-referential entity with random data"""
    return TestSelfReferentialEntity(**create_test_self_ref_kwargs(**kwargs))

# =============================================================================
# COMPLEX DATA CREATION UTILITIES
# =============================================================================

def create_test_meal_with_recipes(**kwargs) -> tuple[TestMealEntity, list[TestRecipeEntity]]:
    """
    Create a meal with associated recipes
    
    Returns tuple of (meal, recipes) for testing complex relationships
    """
    meal_kwargs = {k: v for k, v in kwargs.items() if not k.startswith("recipe_")}
    recipe_count = kwargs.get("recipe_count", 2)  # Default 2 recipes per meal
    
    meal = create_test_meal(**meal_kwargs)
    
    recipes = []
    for i in range(recipe_count):
        recipe_kwargs = {
            "meal_id": meal.id,
            "author_id": meal.author_id,
            **{k.replace("recipe_", ""): v for k, v in kwargs.items() if k.startswith("recipe_")}
        }
        recipes.append(create_test_recipe(**recipe_kwargs))
    
    return meal, recipes

def create_test_recipe_with_ingredients(**kwargs):
    """
    Create a recipe with associated ingredients
    
    If 'ingredients' parameter is provided, creates ingredients with those specs
    and returns just the recipe object.
    Otherwise generates random ingredients and returns tuple of (recipe, ingredients).
    """
    # Check if specific ingredients are provided
    ingredient_specs = kwargs.pop("ingredients", None)
    
    recipe_kwargs = {k: v for k, v in kwargs.items() if not k.startswith("ingredient_")}
    
    recipe = create_test_recipe(**recipe_kwargs)
    
    if ingredient_specs:
        # Create specific ingredients based on provided specs
        ingredients = []
        for i, ingredient_spec in enumerate(ingredient_specs):
            ingredient_kwargs = {
                "recipe_id": recipe.id,
                "position": i,
                **ingredient_spec
            }
            ingredients.append(create_test_ingredient(**ingredient_kwargs))
        # Don't assign to recipe.ingredients as it may not exist - just return recipe
        return recipe
    else:
        # Generate deterministic ingredients and return tuple for backward compatibility
        ingredient_count = kwargs.get("ingredient_count", 3)  # Default 3 ingredients per recipe
        
        ingredients = []
        for i in range(ingredient_count):
            ingredient_kwargs = {
                "recipe_id": recipe.id,
                "position": i,
                **{k.replace("ingredient_", ""): v for k, v in kwargs.items() if k.startswith("ingredient_")}
            }
            ingredients.append(create_test_ingredient(**ingredient_kwargs))
        
        return recipe, ingredients

def create_test_recipe_with_ratings(**kwargs) -> tuple[TestRecipeEntity, list[TestRatingEntity]]:
    """
    Create a recipe with associated ratings
    
    Returns tuple of (recipe, ratings) for testing aggregation scenarios
    """
    recipe_kwargs = {k: v for k, v in kwargs.items() if not k.startswith("rating_")}
    rating_count = kwargs.get("rating_count", 2)  # Default 2 ratings per recipe
    
    recipe = create_test_recipe(**recipe_kwargs)
    
    ratings = []
    for i in range(rating_count):
        rating_kwargs = {
            "recipe_id": recipe.id,
            **{k.replace("rating_", ""): v for k, v in kwargs.items() if k.startswith("rating_")}
        }
        ratings.append(create_test_rating(**rating_kwargs))
    
    return recipe, ratings

def create_test_self_ref_hierarchy(**kwargs) -> list[TestSelfReferentialEntity]:
    """
    Create a hierarchy of self-referential entities
    
    Returns list of entities with parent-child relationships for testing recursion
    """
    depth = kwargs.get("depth", 3)
    base_name = kwargs.get("base_name", "hierarchy")
    
    entities = []
    parent_id = None
    
    for level in range(depth):
        entity_kwargs = {
            "name": f"{base_name}_level_{level}",
            "level": level,
            "parent_id": parent_id,
            **{k: v for k, v in kwargs.items() if k not in ["depth", "base_name"]}
        }
        entity = create_test_self_ref(**entity_kwargs)
        entities.append(entity)
        parent_id = entity.id  # Next entity will be child of this one
    
    return entities

def create_test_friends_network(**kwargs) -> list[TestSelfReferentialEntity]:
    """
    Create a network of self-referential entities with friend relationships
    
    Returns list of entities for testing many-to-many self-relationships
    """
    count = kwargs.get("count", 4)
    base_name = kwargs.get("base_name", "friend")
    
    entities = []
    for i in range(count):
        entity_kwargs = {
            "name": f"{base_name}_{i}",
            "level": 0,
            **{k: v for k, v in kwargs.items() if k not in ["count", "base_name"]}
        }
        entities.append(create_test_self_ref(**entity_kwargs))
    
    return entities

# =============================================================================
# PERFORMANCE TESTING UTILITIES
# =============================================================================

def create_large_dataset(entity_count: int = 1000, **kwargs) -> list[MealSaTestModel]:
    """
    Create a large dataset for performance testing
    
    Generates realistic data distribution for benchmark scenarios
    """
    meals = []
    
    # Create authors for realistic distribution, ensure at least one author
    author_count = max(1, entity_count // 10)
    authors = [f"author-{i:06d}" for i in range(author_count)]
    
    for i in range(entity_count):
        meal_kwargs = {
            "name": f"Performance Meal {i}",
            "author_id": authors[i % len(authors)],  # Distribute evenly among authors
            "total_time": 30 + (i % 150),  # Vary from 30 to 180
            "calorie_density": round(100.0 + (i % 400), 2),  # Vary from 100 to 500
            "like": [True, False, None][i % 3],  # Cycle through options
            **kwargs
        }
        meals.append(create_test_ORM_meal(**meal_kwargs))
    
    return meals

# =============================================================================
# COMPLEX JOIN MODEL FACTORIES
# =============================================================================

class TestSupplierEntity:
    """Simple entity for test supplier"""
    def __init__(self, id: str, name: str, country: str, active: bool = True, created_at: Optional[datetime] = None):
        self.id = id
        self.name = name
        self.country = country
        self.active = active
        self.created_at = created_at or datetime.now(timezone.utc)

class TestCategoryEntity:
    """Simple entity for test category"""
    def __init__(self, id: str, name: str, description: Optional[str] = None, parent_id: Optional[str] = None):
        self.id = id
        self.name = name
        self.description = description
        self.parent_id = parent_id

class TestProductEntity:
    """Simple entity for test product"""
    def __init__(self, id: str, name: str, category_id: str, supplier_id: str, price: float, active: bool = True, created_at: Optional[datetime] = None):
        self.id = id
        self.name = name
        self.category_id = category_id
        self.supplier_id = supplier_id
        self.price = price
        self.active = active
        self.created_at = created_at or datetime.now(timezone.utc)

class TestCustomerEntity:
    """Simple entity for test customer"""
    def __init__(self, id: str, name: str, email: str, country: str, active: bool = True, created_at: Optional[datetime] = None):
        self.id = id
        self.name = name
        self.email = email
        self.country = country
        self.active = active
        self.created_at = created_at or datetime.now(timezone.utc)

class TestOrderEntity:
    """Simple entity for test order"""
    def __init__(self, id: str, product_id: str, customer_id: str, quantity: int, total_price: float, order_date: Optional[datetime] = None, status: str = "pending"):
        self.id = id
        self.product_id = product_id
        self.customer_id = customer_id
        self.quantity = quantity
        self.total_price = total_price
        self.order_date = order_date or datetime.now(timezone.utc)
        self.status = status

def create_test_supplier_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test supplier kwargs with validation"""
    global _SUPPLIER_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", f"supplier-{_SUPPLIER_COUNTER:06d}"),
        "name": kwargs.get("name", f"supplier_name-{_SUPPLIER_COUNTER:06d}"),
        "country": kwargs.get("country", "USA"),  # Default country
        "active": kwargs.get("active", True),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc)),
    }
    _SUPPLIER_COUNTER += 1
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_supplier(**kwargs) -> TestSupplierEntity:
    """Create test supplier entity with random data"""
    return TestSupplierEntity(**create_test_supplier_kwargs(**kwargs))

def create_test_ORM_supplier_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test supplier ORM kwargs with validation"""
    global _SUPPLIER_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", f"supplier-{_SUPPLIER_COUNTER:06d}"),
        "name": kwargs.get("name", f"supplier_name-{_SUPPLIER_COUNTER:06d}"),
        "country": kwargs.get("country", "USA"),  # Default country
        "active": kwargs.get("active", True),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc).replace(tzinfo=None)),
    }
    _SUPPLIER_COUNTER += 1
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_ORM_supplier(**kwargs) -> SupplierSaTestModel:
    """Create test supplier ORM model with random data"""
    return SupplierSaTestModel(**create_test_ORM_supplier_kwargs(**kwargs))

def create_test_category_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test category kwargs with validation"""
    global _CATEGORY_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", f"category-{_CATEGORY_COUNTER:06d}"),
        "name": kwargs.get("name", f"category_name-{_CATEGORY_COUNTER:06d}"),
        "description": kwargs.get("description", f"description-{_CATEGORY_COUNTER:06d}"),
        "parent_id": kwargs.get("parent_id", None),
    }
    _CATEGORY_COUNTER += 1
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_category(**kwargs) -> TestCategoryEntity:
    """Create test category entity with random data"""
    return TestCategoryEntity(**create_test_category_kwargs(**kwargs))

def create_test_ORM_category_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test category ORM kwargs with validation"""
    global _CATEGORY_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", f"category-{_CATEGORY_COUNTER:06d}"),
        "name": kwargs.get("name", f"category_name-{_CATEGORY_COUNTER:06d}"),
        "description": kwargs.get("description", f"description-{_CATEGORY_COUNTER:06d}"),
        "parent_id": kwargs.get("parent_id", None),
    }
    _CATEGORY_COUNTER += 1
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_ORM_category(**kwargs) -> CategorySaTestModel:
    """Create test category ORM model with random data"""
    return CategorySaTestModel(**create_test_ORM_category_kwargs(**kwargs))

def create_test_product_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test product kwargs with validation"""
    global _PRODUCT_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", f"product-{_PRODUCT_COUNTER:06d}"),
        "name": kwargs.get("name", f"product_name-{_PRODUCT_COUNTER:06d}"),
        "category_id": kwargs.get("category_id", f"category-{_PRODUCT_COUNTER:06d}"),
        "supplier_id": kwargs.get("supplier_id", f"supplier-{_PRODUCT_COUNTER:06d}"),
        "price": kwargs.get("price", 50.0),  # Default price
        "active": kwargs.get("active", True),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc)),
    }
    _PRODUCT_COUNTER += 1
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Validate constraint bounds
    assert final_kwargs["price"] > 0, f"Price must be positive, got {final_kwargs['price']}"
    
    return final_kwargs

def create_test_product(**kwargs) -> TestProductEntity:
    """Create test product entity with random data"""
    return TestProductEntity(**create_test_product_kwargs(**kwargs))

def create_test_ORM_product_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test product ORM kwargs with validation"""
    global _PRODUCT_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", f"product-{_PRODUCT_COUNTER:06d}"),
        "name": kwargs.get("name", f"product_name-{_PRODUCT_COUNTER:06d}"),
        "category_id": kwargs.get("category_id", f"category-{_PRODUCT_COUNTER:06d}"),
        "supplier_id": kwargs.get("supplier_id", f"supplier-{_PRODUCT_COUNTER:06d}"),
        "price": kwargs.get("price", 50.0),  # Default price
        "active": kwargs.get("active", True),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc).replace(tzinfo=None)),
    }
    _PRODUCT_COUNTER += 1
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Validate constraint bounds
    assert final_kwargs["price"] > 0, f"Price must be positive, got {final_kwargs['price']}"
    
    return final_kwargs

def create_test_ORM_product(**kwargs) -> ProductSaTestModel:
    """Create test product ORM model with random data"""
    return ProductSaTestModel(**create_test_ORM_product_kwargs(**kwargs))

def create_test_customer_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test customer kwargs with validation"""
    global _CUSTOMER_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", f"customer-{_CUSTOMER_COUNTER:06d}"),
        "name": kwargs.get("name", f"customer_name-{_CUSTOMER_COUNTER:06d}"),
        "email": kwargs.get("email", f"user-{_CUSTOMER_COUNTER:06d}@example.com"),
        "country": kwargs.get("country", "USA"),  # Default country
        "active": kwargs.get("active", True),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc)),
    }
    _CUSTOMER_COUNTER += 1
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_customer(**kwargs) -> TestCustomerEntity:
    """Create test customer entity with random data"""
    return TestCustomerEntity(**create_test_customer_kwargs(**kwargs))

def create_test_ORM_customer_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test customer ORM kwargs with validation"""
    global _CUSTOMER_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", f"customer-{_CUSTOMER_COUNTER:06d}"),
        "name": kwargs.get("name", f"customer_name-{_CUSTOMER_COUNTER:06d}"),
        "email": kwargs.get("email", f"user-{_CUSTOMER_COUNTER:06d}@example.com"),
        "country": kwargs.get("country", "USA"),  # Default country
        "active": kwargs.get("active", True),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc).replace(tzinfo=None)),
    }
    _CUSTOMER_COUNTER += 1
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_ORM_customer(**kwargs) -> CustomerSaTestModel:
    """Create test customer ORM model with random data"""
    return CustomerSaTestModel(**create_test_ORM_customer_kwargs(**kwargs))

def create_test_order_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test order kwargs with validation"""
    global _ORDER_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", f"order-{_ORDER_COUNTER:06d}"),
        "product_id": kwargs.get("product_id", f"product-{_ORDER_COUNTER:06d}"),
        "customer_id": kwargs.get("customer_id", f"customer-{_ORDER_COUNTER:06d}"),
        "quantity": kwargs.get("quantity", 1),  # Default quantity
        "total_price": kwargs.get("total_price", 100.0),  # Default price
        "order_date": kwargs.get("order_date", datetime.now(timezone.utc)),
        "status": kwargs.get("status", "pending"),  # Default status
    }
    _ORDER_COUNTER += 1
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Validate constraint bounds
    assert final_kwargs["quantity"] > 0, f"Quantity must be positive, got {final_kwargs['quantity']}"
    assert final_kwargs["total_price"] > 0, f"Total price must be positive, got {final_kwargs['total_price']}"
    
    return final_kwargs

def create_test_order(**kwargs) -> TestOrderEntity:
    """Create test order entity with random data"""
    return TestOrderEntity(**create_test_order_kwargs(**kwargs))

def create_test_ORM_order_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test order ORM kwargs with validation"""
    global _ORDER_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", f"order-{_ORDER_COUNTER:06d}"),
        "product_id": kwargs.get("product_id", f"product-{_ORDER_COUNTER:06d}"),
        "customer_id": kwargs.get("customer_id", f"customer-{_ORDER_COUNTER:06d}"),
        "quantity": kwargs.get("quantity", 1),  # Default quantity
        "total_price": kwargs.get("total_price", 100.0),  # Default price
        "order_date": kwargs.get("order_date", datetime.now(timezone.utc).replace(tzinfo=None)),
        "status": kwargs.get("status", "pending"),  # Default status
    }
    _ORDER_COUNTER += 1
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Validate constraint bounds
    assert final_kwargs["quantity"] > 0, f"Quantity must be positive, got {final_kwargs['quantity']}"
    assert final_kwargs["total_price"] > 0, f"Total price must be positive, got {final_kwargs['total_price']}"
    
    return final_kwargs

def create_test_ORM_order(**kwargs) -> OrderSaTestModel:
    """Create test order ORM model with random data"""
    return OrderSaTestModel(**create_test_ORM_order_kwargs(**kwargs))

# =============================================================================
# DETERMINISTIC FACTORY VARIANTS FOR TESTING EDGE CASES
# =============================================================================

def create_low_calorie_meal(**kwargs) -> TestMealEntity:
    """Create a low calorie meal for testing"""
    defaults = {
        "calorie_density": 150.0,
        "carbo_percentage": 60.0,
        "protein_percentage": 30.0,
        "total_fat_percentage": 10.0,
        "total_time": 15,
    }
    defaults.update(kwargs)
    return create_test_meal(**defaults)

def create_test_ORM_low_calorie_meal(**kwargs) -> MealSaTestModel:
    """Create a low calorie meal ORM model for testing"""
    defaults = {
        "calorie_density": 150.0,
        "carbo_percentage": 60.0,
        "protein_percentage": 30.0,
        "total_fat_percentage": 10.0,
        "total_time": 15,
        # Adjust nutritional values for low calorie
        "calories": kwargs.get("calories", 375.0),  # 250g * 150 cal/100g
        "protein": kwargs.get("protein", 75.0),  # 30% of 250g
        "carbohydrate": kwargs.get("carbohydrate", 150.0),  # 60% of 250g
        "total_fat": kwargs.get("total_fat", 25.0),  # 10% of 250g
    }
    defaults.update(kwargs)
    return create_test_ORM_meal(**defaults)

def create_high_calorie_meal(**kwargs) -> TestMealEntity:
    """Create a high calorie meal for testing"""
    defaults = {
        "calorie_density": 450.0,
        "carbo_percentage": 30.0,
        "protein_percentage": 20.0,
        "total_fat_percentage": 50.0,
        "total_time": 90,
    }
    defaults.update(kwargs)
    return create_test_meal(**defaults)

def create_test_ORM_high_calorie_meal(**kwargs) -> MealSaTestModel:
    """Create a high calorie meal ORM model for testing"""
    defaults = {
        "calorie_density": 450.0,
        "carbo_percentage": 30.0,
        "protein_percentage": 20.0,
        "total_fat_percentage": 50.0,
        "total_time": 90,
        # Adjust nutritional values for high calorie
        "calories": kwargs.get("calories", 1125.0),  # 250g * 450 cal/100g
        "protein": kwargs.get("protein", 50.0),  # 20% of 250g
        "carbohydrate": kwargs.get("carbohydrate", 75.0),  # 30% of 250g
        "total_fat": kwargs.get("total_fat", 125.0),  # 50% of 250g
    }
    defaults.update(kwargs)
    return create_test_ORM_meal(**defaults)

def create_quick_meal(**kwargs) -> TestMealEntity:
    """Create a quick meal for testing time filters"""
    defaults = {
        "total_time": 10,
        "like": True,
    }
    defaults.update(kwargs)
    return create_test_meal(**defaults)

def create_test_ORM_quick_meal(**kwargs) -> MealSaTestModel:
    """Create a quick meal ORM model for testing time filters"""
    defaults = {
        "total_time": 10,
        "like": True,
    }
    defaults.update(kwargs)
    return create_test_ORM_meal(**defaults)

def create_long_meal(**kwargs) -> TestMealEntity:
    """Create a long cooking time meal for testing"""
    defaults = {
        "total_time": 180,
        "like": None,
    }
    defaults.update(kwargs)
    return create_test_meal(**defaults)

def create_test_ORM_long_meal(**kwargs) -> MealSaTestModel:
    """Create a long cooking time meal ORM model for testing"""
    defaults = {
        "total_time": 180,
        "like": None,
    }
    defaults.update(kwargs)
    return create_test_ORM_meal(**defaults)

def create_disliked_meal(**kwargs) -> TestMealEntity:
    """Create a disliked meal for testing like filters"""
    defaults = {
        "like": False,
        "calorie_density": 200.0,
    }
    defaults.update(kwargs)
    return create_test_meal(**defaults)

def create_test_ORM_disliked_meal(**kwargs) -> MealSaTestModel:
    """Create a disliked meal ORM model for testing like filters"""
    defaults = {
        "like": False,
        "calorie_density": 200.0,
    }
    defaults.update(kwargs)
    return create_test_ORM_meal(**defaults)

def create_lightweight_meal(**kwargs) -> TestMealEntity:
    """Create a lightweight meal for testing weight filters"""
    defaults = {
        "weight_in_grams": 150,
        "calorie_density": 100.0,
    }
    defaults.update(kwargs)
    return create_test_meal(**defaults)

def create_test_ORM_lightweight_meal(**kwargs) -> MealSaTestModel:
    """Create a lightweight meal ORM model for testing weight filters"""
    defaults = {
        "weight_in_grams": 150,
        "calorie_density": 100.0,
        # Adjust nutritional values for lightweight meal
        "calories": kwargs.get("calories", 150.0),  # 150g * 100 cal/100g
    }
    defaults.update(kwargs)
    return create_test_ORM_meal(**defaults)

def create_heavy_meal(**kwargs) -> TestMealEntity:
    """Create a heavy meal for testing weight filters"""
    defaults = {
        "weight_in_grams": 800,
        "calorie_density": 400.0,
    }
    defaults.update(kwargs)
    return create_test_meal(**defaults)

def create_test_ORM_heavy_meal(**kwargs) -> MealSaTestModel:
    """Create a heavy meal ORM model for testing weight filters"""
    defaults = {
        "weight_in_grams": 800,
        "calorie_density": 400.0,
        # Adjust nutritional values for heavy meal
        "calories": kwargs.get("calories", 3200.0),  # 800g * 400 cal/100g
    }
    defaults.update(kwargs)
    return create_test_ORM_meal(**defaults)

def create_private_recipe(**kwargs) -> TestRecipeEntity:
    """Create a private recipe for testing privacy filters"""
    defaults = {
        "privacy": "PRIVATE",
        "average_taste_rating": 5.0,
    }
    defaults.update(kwargs)
    return create_test_recipe(**defaults)

def create_test_ORM_private_recipe(**kwargs) -> RecipeSaTestModel:
    """Create a private recipe ORM model for testing privacy filters"""
    defaults = {
        "privacy": "PRIVATE",
        "average_taste_rating": 5.0,
    }
    defaults.update(kwargs)
    return create_test_ORM_recipe(**defaults)

def create_public_recipe(**kwargs) -> TestRecipeEntity:
    """Create a public recipe for testing privacy filters"""
    defaults = {
        "privacy": "PUBLIC",
        "average_taste_rating": 3.0,
    }
    defaults.update(kwargs)
    return create_test_recipe(**defaults)

def create_test_ORM_public_recipe(**kwargs) -> RecipeSaTestModel:
    """Create a public recipe ORM model for testing privacy filters"""
    defaults = {
        "privacy": "PUBLIC",
        "average_taste_rating": 3.0,
    }
    defaults.update(kwargs)
    return create_test_ORM_recipe(**defaults)

def create_highly_rated_recipe(**kwargs) -> TestRecipeEntity:
    """Create a highly rated recipe for testing rating filters"""
    defaults = {
        "average_taste_rating": 5.0,
        "average_convenience_rating": 4.5,
    }
    defaults.update(kwargs)
    return create_test_recipe(**defaults)

def create_test_ORM_highly_rated_recipe(**kwargs) -> RecipeSaTestModel:
    """Create a highly rated recipe ORM model for testing rating filters"""
    defaults = {
        "average_taste_rating": 5.0,
        "average_convenience_rating": 4.5,
    }
    defaults.update(kwargs)
    return create_test_ORM_recipe(**defaults)

def create_poorly_rated_recipe(**kwargs) -> TestRecipeEntity:
    """Create a poorly rated recipe for testing rating filters"""
    defaults = {
        "average_taste_rating": 1.5,
        "average_convenience_rating": 2.0,
    }
    defaults.update(kwargs)
    return create_test_recipe(**defaults)

def create_test_ORM_poorly_rated_recipe(**kwargs) -> RecipeSaTestModel:
    """Create a poorly rated recipe ORM model for testing rating filters"""
    defaults = {
        "average_taste_rating": 1.5,
        "average_convenience_rating": 2.0,
    }
    defaults.update(kwargs)
    return create_test_ORM_recipe(**defaults)

def reset_counters():
    """Reset all counters for test isolation"""
    global _MEAL_COUNTER, _RECIPE_COUNTER, _TAG_COUNTER, _RATING_COUNTER
    global _INGREDIENT_COUNTER, _SUPPLIER_COUNTER, _CATEGORY_COUNTER
    global _PRODUCT_COUNTER, _CUSTOMER_COUNTER, _ORDER_COUNTER, _GENERAL_COUNTER
    
    _MEAL_COUNTER = 1
    _RECIPE_COUNTER = 1
    _TAG_COUNTER = 1
    _RATING_COUNTER = 1
    _INGREDIENT_COUNTER = 1
    _SUPPLIER_COUNTER = 1
    _CATEGORY_COUNTER = 1
    _PRODUCT_COUNTER = 1
    _CUSTOMER_COUNTER = 1
    _ORDER_COUNTER = 1
    _GENERAL_COUNTER = 1

def create_test_ORM_meal_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create test meal ORM kwargs with validation (following random_refs.py pattern)
    
    Generates all required attributes for MealSaTestModel with realistic defaults.
    Allows override of any attribute via kwargs.
    """
    global _MEAL_COUNTER
    base_name = kwargs.get("name", f"meal_name-{_MEAL_COUNTER:06d}")
    
    final_kwargs = {
        "id": kwargs.get("id", f"meal-{_MEAL_COUNTER:06d}"),
        "name": base_name,
        "author_id": kwargs.get("author_id", f"author-{_MEAL_COUNTER:06d}"),
        "description": kwargs.get("description", f"meal_description-{_MEAL_COUNTER:06d}"),
        "preprocessed_name": kwargs.get("preprocessed_name", base_name.lower()),
        "menu_id": kwargs.get("menu_id", None),
        "notes": kwargs.get("notes", f"meal_notes-{_MEAL_COUNTER:06d}"),
        "total_time": kwargs.get("total_time", 45),  # Default medium cooking time
        "like": kwargs.get("like", True),  # Default positive preference
        "weight_in_grams": kwargs.get("weight_in_grams", 250),  # Default portion size
        "calorie_density": kwargs.get("calorie_density", 250.0),  # Default moderate calorie density
        "carbo_percentage": kwargs.get("carbo_percentage", 50.0),  # Default balanced macro
        "protein_percentage": kwargs.get("protein_percentage", 25.0),  # Default balanced macro
        "total_fat_percentage": kwargs.get("total_fat_percentage", 25.0),  # Default balanced macro
        "image_url": kwargs.get("image_url", f"image_url-{_MEAL_COUNTER:06d}"),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc).replace(tzinfo=None)),
        "updated_at": kwargs.get("updated_at", datetime.now(timezone.utc).replace(tzinfo=None)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
        # Nutritional facts individual columns for composite
        "calories": kwargs.get("calories", 625.0),  # 250g * 250 cal/100g
        "protein": kwargs.get("protein", 62.5),  # 25% of 250g
        "carbohydrate": kwargs.get("carbohydrate", 125.0),  # 50% of 250g
        "total_fat": kwargs.get("total_fat", 62.5),  # 25% of 250g
        "saturated_fat": kwargs.get("saturated_fat", 20.8),  # 1/3 of total fat
        "trans_fat": kwargs.get("trans_fat", 0.0),
        "dietary_fiber": kwargs.get("dietary_fiber", 25.0),
        "sodium": kwargs.get("sodium", 2.0),
        "sugar": kwargs.get("sugar", 10.0),
        "vitamin_a": kwargs.get("vitamin_a", 0.8),
        "vitamin_c": kwargs.get("vitamin_c", 60.0),
        "iron": kwargs.get("iron", 12.0),
        "calcium": kwargs.get("calcium", 800.0),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Increment counter for next call
    _MEAL_COUNTER += 1
    
    return final_kwargs

def create_test_ORM_meal(**kwargs) -> MealSaTestModel:
    """Create test meal ORM model with random data"""
    meal_kwargs = create_test_ORM_meal_kwargs(**kwargs)
    
    # Create nutri_facts composite if individual nutrition values are provided
    nutri_facts = NutriFactsTestSaModel(
        calories=meal_kwargs.pop("calories", None),
        protein=meal_kwargs.pop("protein", None),
        carbohydrate=meal_kwargs.pop("carbohydrate", None),
        total_fat=meal_kwargs.pop("total_fat", None),
        saturated_fat=meal_kwargs.pop("saturated_fat", None),
        trans_fat=meal_kwargs.pop("trans_fat", None),
        dietary_fiber=meal_kwargs.pop("dietary_fiber", None),
        sodium=meal_kwargs.pop("sodium", None),
        sugar=meal_kwargs.pop("sugar", None),
        vitamin_a=meal_kwargs.pop("vitamin_a", None),
        vitamin_c=meal_kwargs.pop("vitamin_c", None),
        iron=meal_kwargs.pop("iron", None),
        calcium=meal_kwargs.pop("calcium", None),
    )
    meal_kwargs["nutri_facts"] = nutri_facts
    
    return MealSaTestModel(**meal_kwargs)

def create_test_ORM_recipe_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create test recipe ORM kwargs with validation
    
    Generates all required attributes for RecipeSaTestModel with realistic defaults.
    Includes complex nutritional data and rating information.
    """
    global _RECIPE_COUNTER
    base_name = kwargs.get("name", f"recipe_name-{_RECIPE_COUNTER:06d}")
    
    final_kwargs = {
        "id": kwargs.get("id", f"recipe-{_RECIPE_COUNTER:06d}"),
        "name": base_name,
        "author_id": kwargs.get("author_id", f"author-{_RECIPE_COUNTER:06d}"),
        "meal_id": kwargs.get("meal_id", None),
        "instructions": kwargs.get("instructions", f"instructions-{_RECIPE_COUNTER:06d}"),
        "preprocessed_name": kwargs.get("preprocessed_name", base_name.lower()),
        "description": kwargs.get("description", f"recipe_description-{_RECIPE_COUNTER:06d}"),
        "utensils": kwargs.get("utensils", f"utensils-{_RECIPE_COUNTER:06d}"),
        "total_time": kwargs.get("total_time", 30),  # Default cooking time
        "notes": kwargs.get("notes", f"recipe_notes-{_RECIPE_COUNTER:06d}"),
        "privacy": kwargs.get("privacy", "PUBLIC"),  # Default public
        "weight_in_grams": kwargs.get("weight_in_grams", 200),  # Default recipe portion
        "calorie_density": kwargs.get("calorie_density", 300.0),  # Default calorie density
        "carbo_percentage": kwargs.get("carbo_percentage", 45.0),  # Default balanced macro
        "protein_percentage": kwargs.get("protein_percentage", 25.0),  # Default balanced macro
        "total_fat_percentage": kwargs.get("total_fat_percentage", 30.0),  # Default balanced macro
        "image_url": kwargs.get("image_url", f"recipe_image-{_RECIPE_COUNTER:06d}"),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc).replace(tzinfo=None)),
        "updated_at": kwargs.get("updated_at", datetime.now(timezone.utc).replace(tzinfo=None)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
        "average_taste_rating": kwargs.get("average_taste_rating", 4.0),  # Default good rating
        "average_convenience_rating": kwargs.get("average_convenience_rating", 3.5),  # Default moderate convenience
        # Nutritional facts individual columns for composite
        "calories": kwargs.get("calories", 600.0),  # 200g * 300 cal/100g
        "protein": kwargs.get("protein", 50.0),  # 25% of 200g
        "carbohydrate": kwargs.get("carbohydrate", 90.0),  # 45% of 200g
        "total_fat": kwargs.get("total_fat", 60.0),  # 30% of 200g
        "saturated_fat": kwargs.get("saturated_fat", 20.0),  # 1/3 of total fat
        "trans_fat": kwargs.get("trans_fat", 0.0),
        "dietary_fiber": kwargs.get("dietary_fiber", 20.0),
        "sodium": kwargs.get("sodium", 1.8),
        "sugar": kwargs.get("sugar", 8.0),
        "vitamin_a": kwargs.get("vitamin_a", 0.6),
        "vitamin_c": kwargs.get("vitamin_c", 50.0),
        "iron": kwargs.get("iron", 10.0),
        "calcium": kwargs.get("calcium", 600.0),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Increment counter for next call
    _RECIPE_COUNTER += 1
    
    return final_kwargs

def create_test_ORM_recipe(**kwargs) -> RecipeSaTestModel:
    """Create test recipe ORM model with random data"""
    recipe_kwargs = create_test_ORM_recipe_kwargs(**kwargs)
    
    # Create nutri_facts composite if individual nutrition values are provided
    nutri_facts = NutriFactsTestSaModel(
        calories=recipe_kwargs.pop("calories", None),
        protein=recipe_kwargs.pop("protein", None),
        carbohydrate=recipe_kwargs.pop("carbohydrate", None),
        total_fat=recipe_kwargs.pop("total_fat", None),
        saturated_fat=recipe_kwargs.pop("saturated_fat", None),
        trans_fat=recipe_kwargs.pop("trans_fat", None),
        dietary_fiber=recipe_kwargs.pop("dietary_fiber", None),
        sodium=recipe_kwargs.pop("sodium", None),
        sugar=recipe_kwargs.pop("sugar", None),
        vitamin_a=recipe_kwargs.pop("vitamin_a", None),
        vitamin_c=recipe_kwargs.pop("vitamin_c", None),
        iron=recipe_kwargs.pop("iron", None),
        calcium=recipe_kwargs.pop("calcium", None),
    )
    recipe_kwargs["nutri_facts"] = nutri_facts
    
    return RecipeSaTestModel(**recipe_kwargs)

def create_test_ORM_tag_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test tag ORM kwargs with validation"""
    global _TAG_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", _TAG_COUNTER),
        "key": kwargs.get("key", "cuisine"),  # Default key
        "value": kwargs.get("value", f"tag_value-{_TAG_COUNTER:06d}"),
        "author_id": kwargs.get("author_id", f"author-{_TAG_COUNTER:06d}"),
        "type": kwargs.get("type", "meal"),  # Default type
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Increment counter for next call
    _TAG_COUNTER += 1
    
    return final_kwargs

def create_test_ORM_tag(**kwargs) -> TagSaTestModel:
    """Create test tag ORM model with random data"""
    return TagSaTestModel(**create_test_ORM_tag_kwargs(**kwargs))

def create_test_ORM_rating_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test rating ORM kwargs with constraint validation"""
    global _RATING_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", _RATING_COUNTER),
        "user_id": kwargs.get("user_id", f"user-{_RATING_COUNTER:06d}"),
        "recipe_id": kwargs.get("recipe_id", f"recipe-{_RATING_COUNTER:06d}"),
        "taste": kwargs.get("taste", 4),  # Default good taste rating
        "convenience": kwargs.get("convenience", 3),  # Default moderate convenience
        "comment": kwargs.get("comment", f"rating_comment-{_RATING_COUNTER:06d}"),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc).replace(tzinfo=None)),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Increment counter for next call
    _RATING_COUNTER += 1
    
    # Validate constraint bounds
    assert 0 <= final_kwargs["taste"] <= 5, f"Taste rating must be 0-5, got {final_kwargs['taste']}"
    assert 0 <= final_kwargs["convenience"] <= 5, f"Convenience rating must be 0-5, got {final_kwargs['convenience']}"
    
    return final_kwargs

def create_test_ORM_rating(**kwargs) -> RatingSaTestModel:
    """Create test rating ORM model with random data"""
    return RatingSaTestModel(**create_test_ORM_rating_kwargs(**kwargs))

def create_test_ORM_ingredient_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test ingredient ORM entity kwargs with realistic data"""
    global _INGREDIENT_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", _INGREDIENT_COUNTER),
        "name": kwargs.get("name", f"Ingredient-{_INGREDIENT_COUNTER:06d}"),
        "quantity": kwargs.get("quantity", 100.0),  # Default quantity
        "unit": kwargs.get("unit", "grams"),  # Default unit
        "recipe_id": kwargs.get("recipe_id", f"recipe-{_INGREDIENT_COUNTER:06d}"),
        "position": kwargs.get("position", 0),
        "product_id": kwargs.get("product_id", None),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Increment counter for next call
    _INGREDIENT_COUNTER += 1
    
    # Validate constraint bounds
    assert final_kwargs["quantity"] > 0, f"Quantity must be positive, got {final_kwargs['quantity']}"
    
    return final_kwargs

def create_test_ORM_ingredient(**kwargs) -> IngredientSaTestModel:
    """Create test ingredient ORM model with random data"""
    return IngredientSaTestModel(**create_test_ORM_ingredient_kwargs(**kwargs))

def create_test_ORM_circular_a_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test circular entity A ORM kwargs"""
    global _GENERAL_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", f"circular_a-{_GENERAL_COUNTER:06d}"),
        "name": kwargs.get("name", f"circular_a_name-{_GENERAL_COUNTER:06d}"),
        "b_ref_id": kwargs.get("b_ref_id", None),  # Can reference circular B
    }
    _GENERAL_COUNTER += 1
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_ORM_circular_a(**kwargs) -> CircularTestModelA:
    """Create test circular entity A ORM model with random data"""
    return CircularTestModelA(**create_test_ORM_circular_a_kwargs(**kwargs))

def create_test_ORM_circular_b_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test circular entity B ORM kwargs"""
    global _GENERAL_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", f"circular_b-{_GENERAL_COUNTER:06d}"),
        "name": kwargs.get("name", f"circular_b_name-{_GENERAL_COUNTER:06d}"),
    }
    _GENERAL_COUNTER += 1
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_ORM_circular_b(**kwargs) -> CircularTestModelB:
    """Create test circular entity B ORM model with random data"""
    return CircularTestModelB(**create_test_ORM_circular_b_kwargs(**kwargs))

def create_test_ORM_self_ref_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test self-referential entity ORM kwargs"""
    global _GENERAL_COUNTER
    final_kwargs = {
        "id": kwargs.get("id", f"self_ref-{_GENERAL_COUNTER:06d}"),
        "name": kwargs.get("name", f"self_ref_name-{_GENERAL_COUNTER:06d}"),
        "parent_id": kwargs.get("parent_id", None),  # Can reference another self_ref
        "level": kwargs.get("level", 0),
    }
    _GENERAL_COUNTER += 1
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_ORM_self_ref(**kwargs) -> SelfReferentialTestModel:
    """Create test self-referential entity ORM model with random data"""
    return SelfReferentialTestModel(**create_test_ORM_self_ref_kwargs(**kwargs))