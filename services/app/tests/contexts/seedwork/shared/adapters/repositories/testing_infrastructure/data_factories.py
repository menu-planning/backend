"""
Test data creation utilities following random_refs.py patterns

This module provides factory functions for creating test entities and data
with randomized attributes. Following the patterns from random_refs.py,
these factories ensure:

- Consistent test data generation
- Proper attribute validation 
- Flexible parameter overrides
- Realistic data relationships
- Support for edge cases and constraints

Key principles:
- Always validate required attributes are present
- Provide sensible defaults for optional attributes  
- Allow easy override of any attribute via kwargs
- Generate realistic data that respects constraints
- Support both kwargs generation and entity creation
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .entities import (
    TestMealEntity, TestRecipeEntity, TestCircularEntityA, TestCircularEntityB,
    TestSelfReferentialEntity, TestTagEntity, TestRatingEntity, TestIngredientEntity
)

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

def check_missing_attributes(cls_or_method, kwargs) -> list[str]:
    """Check for missing attributes in kwargs (from random_refs.py)"""
    import inspect
    if inspect.isclass(cls_or_method):
        attributes = [
            attr for attr in dir(cls_or_method) 
            if not attr.startswith("_") and not callable(getattr(cls_or_method, attr))
        ]
    else:
        sig = inspect.signature(cls_or_method)
        attributes = [param.name for param in sig.parameters.values() if param.name != "cls"]
    
    return [attr for attr in attributes if attr not in kwargs]

# =============================================================================
# MAIN ENTITY FACTORIES
# =============================================================================

def create_test_meal_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create test meal kwargs with validation (following random_refs.py pattern)
    
    Generates all required attributes for TestMealEntity with realistic defaults.
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
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Increment counter for next call
    _MEAL_COUNTER += 1
    
    # Validate all required attributes are present
    missing = check_missing_attributes(TestMealEntity, final_kwargs)
    assert not missing, f"Missing attributes for TestMealEntity: {missing}"
    
    return final_kwargs

def create_test_meal(**kwargs) -> TestMealEntity:
    """Create test meal entity with random data"""
    return TestMealEntity(**create_test_meal_kwargs(**kwargs))

def create_test_recipe_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create test recipe kwargs with validation
    
    Generates all required attributes for TestRecipeEntity with realistic defaults.
    Includes complex nutritional data and rating information.
    """
    base_name = kwargs.get("name", random_attr("recipe_name"))
    
    final_kwargs = {
        "id": kwargs.get("id", random_attr("recipe")),
        "name": base_name,
        "author_id": kwargs.get("author_id", random_attr("author")),
        "meal_id": kwargs.get("meal_id", None),
        "instructions": kwargs.get("instructions", random_attr("instructions")),
        "preprocessed_name": kwargs.get("preprocessed_name", base_name.lower()),
        "description": kwargs.get("description", random_attr("recipe_description")),
        "utensils": kwargs.get("utensils", random_attr("utensils")),
        "total_time": kwargs.get("total_time", random.randint(5, 120)),
        "notes": kwargs.get("notes", random_attr("recipe_notes")),
        "privacy": kwargs.get("privacy", random.choice(["PRIVATE", "PUBLIC", "SHARED"])),
        "weight_in_grams": kwargs.get("weight_in_grams", random.randint(50, 800)),
        "calorie_density": kwargs.get("calorie_density", round(random.uniform(80.0, 600.0), 2)),
        "carbo_percentage": kwargs.get("carbo_percentage", round(random.uniform(15.0, 75.0), 2)),
        "protein_percentage": kwargs.get("protein_percentage", round(random.uniform(5.0, 45.0), 2)),
        "total_fat_percentage": kwargs.get("total_fat_percentage", round(random.uniform(5.0, 55.0), 2)),
        "image_url": kwargs.get("image_url", random_attr("recipe_image")),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc).replace(tzinfo=None)),
        "updated_at": kwargs.get("updated_at", datetime.now(timezone.utc).replace(tzinfo=None)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
        "average_taste_rating": kwargs.get("average_taste_rating", round(random.uniform(1.0, 5.0), 1)),
        "average_convenience_rating": kwargs.get("average_convenience_rating", round(random.uniform(1.0, 5.0), 1)),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Validate all required attributes are present
    missing = check_missing_attributes(TestRecipeEntity, final_kwargs)
    assert not missing, f"Missing attributes for TestRecipeEntity: {missing}"
    
    return final_kwargs

def create_test_recipe(**kwargs) -> TestRecipeEntity:
    """Create test recipe entity with random data"""
    return TestRecipeEntity(**create_test_recipe_kwargs(**kwargs))

# =============================================================================
# RELATIONSHIP ENTITY FACTORIES
# =============================================================================

def create_test_tag_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test tag kwargs with validation"""
    final_kwargs = {
        "id": kwargs.get("id", random.randint(1, 999999)),
        "key": kwargs.get("key", random.choice(["cuisine", "diet", "flavor", "texture", "planning"])),
        "value": kwargs.get("value", random_attr("tag_value")),
        "author_id": kwargs.get("author_id", random_attr("author")),
        "type": kwargs.get("type", random.choice(["meal", "recipe", "menu"])),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Validate all required attributes are present
    missing = check_missing_attributes(TestTagEntity, final_kwargs)
    assert not missing, f"Missing attributes for TestTagEntity: {missing}"
    
    return final_kwargs

def create_test_tag(**kwargs) -> TestTagEntity:
    """Create test tag entity with random data"""
    return TestTagEntity(**create_test_tag_kwargs(**kwargs))

def create_test_rating_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test rating kwargs with constraint validation"""
    final_kwargs = {
        "id": kwargs.get("id", random.randint(1, 999999)),
        "user_id": kwargs.get("user_id", random_attr("user")),
        "recipe_id": kwargs.get("recipe_id", random_attr("recipe")),
        "taste": kwargs.get("taste", random.randint(0, 5)),
        "convenience": kwargs.get("convenience", random.randint(0, 5)),
        "comment": kwargs.get("comment", random_attr("rating_comment")),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc).replace(tzinfo=None)),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
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
    final_kwargs = {
        "id": kwargs.get("id", random.randint(1, 999999)),
        "name": kwargs.get("name", f"Ingredient {random_attr('ingredient')}"),
        "quantity": kwargs.get("quantity", random.uniform(50.0, 500.0)),
        "unit": kwargs.get("unit", random.choice(["grams", "ml", "cups", "pieces", "tbsp", "tsp"])),
        "recipe_id": kwargs.get("recipe_id", random_attr("recipe")),
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
    final_kwargs = {
        "id": kwargs.get("id", random_attr("circular_a")),
        "name": kwargs.get("name", random_attr("circular_a_name")),
        "b_ref_id": kwargs.get("b_ref_id", None),  # Can reference circular B
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_circular_a(**kwargs) -> TestCircularEntityA:
    """Create test circular entity A with random data"""
    return TestCircularEntityA(**create_test_circular_a_kwargs(**kwargs))

def create_test_circular_b_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test circular entity B kwargs"""
    final_kwargs = {
        "id": kwargs.get("id", random_attr("circular_b")),
        "name": kwargs.get("name", random_attr("circular_b_name")),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_circular_b(**kwargs) -> TestCircularEntityB:
    """Create test circular entity B with random data"""
    return TestCircularEntityB(**create_test_circular_b_kwargs(**kwargs))

def create_test_self_ref_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test self-referential entity kwargs"""
    final_kwargs = {
        "id": kwargs.get("id", random_attr("self_ref")),
        "name": kwargs.get("name", random_attr("self_ref_name")),
        "parent_id": kwargs.get("parent_id", None),  # Can reference another self_ref
        "level": kwargs.get("level", 0),
    }
    
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
    recipe_count = kwargs.get("recipe_count", random.randint(1, 4))
    
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
        # Generate random ingredients and return tuple for backward compatibility
        ingredient_count = kwargs.get("ingredient_count", random.randint(2, 6))
        
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
    rating_count = kwargs.get("rating_count", random.randint(1, 5))
    
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

def create_large_dataset(entity_count: int = 1000, **kwargs) -> list[TestMealEntity]:
    """
    Create a large dataset for performance testing
    
    Generates realistic data distribution for benchmark scenarios
    """
    meals = []
    
    # Create authors for realistic distribution
    authors = [random_attr("author") for _ in range(entity_count // 10)]
    
    for i in range(entity_count):
        meal_kwargs = {
            "name": f"Performance Meal {i}",
            "author_id": random.choice(authors),
            "total_time": random.randint(5, 180),
            "calorie_density": round(random.uniform(50.0, 800.0), 2),
            "like": random.choice([True, False, None]),
            **kwargs
        }
        meals.append(create_test_meal(**meal_kwargs))
    
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
    final_kwargs = {
        "id": kwargs.get("id", random_attr("supplier")),
        "name": kwargs.get("name", random_attr("supplier_name")),
        "country": kwargs.get("country", random.choice(["USA", "Canada", "UK", "Germany", "France", "Japan"])),
        "active": kwargs.get("active", True),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc)),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_supplier(**kwargs) -> TestSupplierEntity:
    """Create test supplier entity with random data"""
    return TestSupplierEntity(**create_test_supplier_kwargs(**kwargs))

def create_test_category_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test category kwargs with validation"""
    final_kwargs = {
        "id": kwargs.get("id", random_attr("category")),
        "name": kwargs.get("name", random_attr("category_name")),
        "description": kwargs.get("description", random_attr("description")),
        "parent_id": kwargs.get("parent_id", None),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_category(**kwargs) -> TestCategoryEntity:
    """Create test category entity with random data"""
    return TestCategoryEntity(**create_test_category_kwargs(**kwargs))

def create_test_product_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test product kwargs with validation"""
    final_kwargs = {
        "id": kwargs.get("id", random_attr("product")),
        "name": kwargs.get("name", random_attr("product_name")),
        "category_id": kwargs.get("category_id", random_attr("category")),
        "supplier_id": kwargs.get("supplier_id", random_attr("supplier")),
        "price": kwargs.get("price", round(random.uniform(10.0, 1000.0), 2)),
        "active": kwargs.get("active", True),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc)),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Validate constraint bounds
    assert final_kwargs["price"] > 0, f"Price must be positive, got {final_kwargs['price']}"
    
    return final_kwargs

def create_test_product(**kwargs) -> TestProductEntity:
    """Create test product entity with random data"""
    return TestProductEntity(**create_test_product_kwargs(**kwargs))

def create_test_customer_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test customer kwargs with validation"""
    final_kwargs = {
        "id": kwargs.get("id", random_attr("customer")),
        "name": kwargs.get("name", random_attr("customer_name")),
        "email": kwargs.get("email", f"{random_attr('user')}@example.com"),
        "country": kwargs.get("country", random.choice(["USA", "Canada", "UK", "Germany", "France", "Japan"])),
        "active": kwargs.get("active", True),
        "created_at": kwargs.get("created_at", datetime.now(timezone.utc)),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    return final_kwargs

def create_test_customer(**kwargs) -> TestCustomerEntity:
    """Create test customer entity with random data"""
    return TestCustomerEntity(**create_test_customer_kwargs(**kwargs))

def create_test_order_kwargs(**kwargs) -> Dict[str, Any]:
    """Create test order kwargs with validation"""
    final_kwargs = {
        "id": kwargs.get("id", random_attr("order")),
        "product_id": kwargs.get("product_id", random_attr("product")),
        "customer_id": kwargs.get("customer_id", random_attr("customer")),
        "quantity": kwargs.get("quantity", random.randint(1, 10)),
        "total_price": kwargs.get("total_price", round(random.uniform(10.0, 1000.0), 2)),
        "order_date": kwargs.get("order_date", datetime.now(timezone.utc)),
        "status": kwargs.get("status", random.choice(["pending", "processing", "shipped", "delivered"])),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Validate constraint bounds
    assert final_kwargs["quantity"] > 0, f"Quantity must be positive, got {final_kwargs['quantity']}"
    assert final_kwargs["total_price"] > 0, f"Total price must be positive, got {final_kwargs['total_price']}"
    
    return final_kwargs

def create_test_order(**kwargs) -> TestOrderEntity:
    """Create test order entity with random data"""
    return TestOrderEntity(**create_test_order_kwargs(**kwargs))