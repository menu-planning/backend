"""
Data factories for ApiIngredient testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- JSON serialization/deserialization testing with model_validate_json and model_dump_json
- Parametrized test scenarios for ingredient validation
- Performance test scenarios with dataset expectations
- Specialized factory functions for different ingredient types
- Comprehensive attribute validation using check_missing_attributes
- Realistic data sets for production-like testing

All data follows the exact structure of ApiIngredient API entities and their validation rules.
Includes extensive testing for Pydantic model validation, JSON handling, and edge cases.
"""

import json
from typing import Dict, Any, List, Optional
from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import Ingredient
from src.contexts.shared_kernel.domain.enums import MeasureUnit

# Import check_missing_attributes for validation
from tests.utils import check_missing_attributes

# =============================================================================
# REALISTIC DATA SETS FOR PRODUCTION-LIKE TESTING
# =============================================================================

REALISTIC_INGREDIENTS = [
    {
        "name": "Extra Virgin Olive Oil",
        "quantity": 2.0,
        "unit": MeasureUnit.TABLESPOON,
        "position": 1,
        "full_text": "2 tablespoons extra virgin olive oil, cold-pressed",
        "product_id": None
    },
    {
        "name": "Fresh Garlic",
        "quantity": 3.0,
        "unit": MeasureUnit.UNIT,
        "position": 2,
        "full_text": "3 cloves fresh garlic, minced",
        "product_id": None
    },
    {
        "name": "Yellow Onion",
        "quantity": 1.0,
        "unit": MeasureUnit.UNIT,
        "position": 3,
        "full_text": "1 large yellow onion, diced",
        "product_id": None
    },
    {
        "name": "Crushed Tomatoes",
        "quantity": 400.0,
        "unit": MeasureUnit.GRAM,
        "position": 4,
        "full_text": "400g can crushed tomatoes, San Marzano preferred",
        "product_id": None
    },
    {
        "name": "Fresh Basil",
        "quantity": 1.0,
        "unit": MeasureUnit.HANDFUL,
        "position": 5,
        "full_text": "1 handful fresh basil leaves, torn",
        "product_id": None
    },
    {
        "name": "Sea Salt",
        "quantity": 1.0,
        "unit": MeasureUnit.TEASPOON,
        "position": 6,
        "full_text": "1 teaspoon sea salt, to taste",
        "product_id": None
    },
    {
        "name": "Black Pepper",
        "quantity": 0.5,
        "unit": MeasureUnit.TEASPOON,
        "position": 7,
        "full_text": "1/2 teaspoon freshly ground black pepper",
        "product_id": None
    },
    {
        "name": "Pasta",
        "quantity": 500.0,
        "unit": MeasureUnit.GRAM,
        "position": 8,
        "full_text": "500g spaghetti or linguine pasta",
        "product_id": None
    },
    {
        "name": "Parmesan Cheese",
        "quantity": 100.0,
        "unit": MeasureUnit.GRAM,
        "position": 9,
        "full_text": "100g Parmigiano-Reggiano, freshly grated",
        "product_id": None
    },
    {
        "name": "Chicken Breast",
        "quantity": 600.0,
        "unit": MeasureUnit.GRAM,
        "position": 10,
        "full_text": "600g boneless, skinless chicken breast",
        "product_id": None
    },
    {
        "name": "Flour",
        "quantity": 2.0,
        "unit": MeasureUnit.CUP,
        "position": 11,
        "full_text": "2 cups all-purpose flour, sifted",
        "product_id": None
    },
    {
        "name": "Milk",
        "quantity": 250.0,
        "unit": MeasureUnit.MILLILITER,
        "position": 12,
        "full_text": "250ml whole milk, room temperature",
        "product_id": None
    },
    {
        "name": "Butter",
        "quantity": 50.0,
        "unit": MeasureUnit.GRAM,
        "position": 13,
        "full_text": "50g unsalted butter, room temperature",
        "product_id": None
    },
    {
        "name": "Lemon",
        "quantity": 1.0,
        "unit": MeasureUnit.UNIT,
        "position": 14,
        "full_text": "1 fresh lemon, juiced and zested",
        "product_id": None
    },
    {
        "name": "Rice",
        "quantity": 1.5,
        "unit": MeasureUnit.CUP,
        "position": 15,
        "full_text": "1 1/2 cups basmati rice, rinsed",
        "product_id": None
    }
]

COMMON_MEASURE_UNITS = [
    MeasureUnit.UNIT,
    MeasureUnit.GRAM,
    MeasureUnit.KILOGRAM,
    MeasureUnit.MILLILITER,
    MeasureUnit.LITER,
    MeasureUnit.TABLESPOON,
    MeasureUnit.TEASPOON,
    MeasureUnit.CUP,
    MeasureUnit.PINCH,
    MeasureUnit.HANDFUL,
    MeasureUnit.SLICE,
    MeasureUnit.PIECE
]

# =============================================================================
# STATIC COUNTERS FOR DETERMINISTIC IDS
# =============================================================================

_INGREDIENT_COUNTER = 1


def reset_api_ingredient_counters() -> None:
    """Reset all counters for test isolation"""
    global _INGREDIENT_COUNTER
    _INGREDIENT_COUNTER = 1


# =============================================================================
# API INGREDIENT DATA FACTORIES
# =============================================================================

def create_api_ingredient_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create ApiIngredient kwargs with deterministic values and comprehensive validation.
    
    Uses check_missing_attributes to ensure completeness and generates
    realistic test data for comprehensive API testing.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required ApiIngredient creation parameters
    """
    global _INGREDIENT_COUNTER
    
    # Get realistic ingredient data for deterministic values
    ingredient_data = REALISTIC_INGREDIENTS[(_INGREDIENT_COUNTER - 1) % len(REALISTIC_INGREDIENTS)]
    
    final_kwargs = {
        "name": kwargs.get("name", ingredient_data["name"]),
        "quantity": kwargs.get("quantity", ingredient_data["quantity"]),
        "unit": kwargs.get("unit", ingredient_data["unit"]),
        "position": kwargs.get("position", ingredient_data["position"]),
        "full_text": kwargs.get("full_text", ingredient_data["full_text"]),
        "product_id": kwargs.get("product_id", str(uuid4()) if _INGREDIENT_COUNTER % 3 == 0 else None),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(ApiIngredient, final_kwargs)
    missing = set(missing) - {'convert', 'model_computed_fields', 'model_config', 'model_fields'}
    assert not missing, f"Missing attributes for ApiIngredient: {missing}"
    
    # Increment counter for next call
    _INGREDIENT_COUNTER += 1
    
    return final_kwargs


def create_api_ingredient(**kwargs) -> ApiIngredient:
    """
    Create an ApiIngredient instance with deterministic data and validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiIngredient instance with comprehensive validation
    """
    ingredient_kwargs = create_api_ingredient_kwargs(**kwargs)
    return ApiIngredient(**ingredient_kwargs)


def create_api_ingredient_from_json(json_data: Optional[str] = None, **kwargs) -> ApiIngredient:
    """
    Create an ApiIngredient instance from JSON using model_validate_json.
    
    This tests Pydantic's JSON validation and parsing capabilities.
    
    Args:
        json_data: JSON string to parse (if None, generates from kwargs)
        **kwargs: Override any default values
        
    Returns:
        ApiIngredient instance created from JSON
    """
    if json_data is None:
        ingredient_kwargs = create_api_ingredient_kwargs(**kwargs)
        # Convert enum to string for JSON serialization
        if isinstance(ingredient_kwargs.get("unit"), MeasureUnit):
            ingredient_kwargs["unit"] = ingredient_kwargs["unit"].value
        json_data = json.dumps(ingredient_kwargs)
    
    return ApiIngredient.model_validate_json(json_data)


def create_api_ingredient_json(**kwargs) -> str:
    """
    Create JSON representation of ApiIngredient using model_dump_json.
    
    This tests Pydantic's JSON serialization capabilities.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        JSON string representation of ApiIngredient
    """
    ingredient = create_api_ingredient(**kwargs)
    return ingredient.model_dump_json()


# =============================================================================
# SPECIALIZED FACTORY FUNCTIONS
# =============================================================================

def create_spice_ingredient(**kwargs) -> ApiIngredient:
    """
    Create a spice ingredient with small quantities and teaspoon/pinch units.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiIngredient representing a spice
    """
    final_kwargs = {
        "name": kwargs.get("name", "Paprika"),
        "quantity": kwargs.get("quantity", 0.5),
        "unit": kwargs.get("unit", MeasureUnit.TEASPOON),
        "full_text": kwargs.get("full_text", "1/2 teaspoon sweet paprika"),
        "product_id": kwargs.get("product_id", None),
        **{k: v for k, v in kwargs.items() if k not in ["name", "quantity", "unit", "full_text", "product_id"]}
    }
    return create_api_ingredient(**final_kwargs)


def create_vegetable_ingredient(**kwargs) -> ApiIngredient:
    """
    Create a vegetable ingredient with unit-based quantities.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiIngredient representing a vegetable
    """
    final_kwargs = {
        "name": kwargs.get("name", "Red Bell Pepper"),
        "quantity": kwargs.get("quantity", 2.0),
        "unit": kwargs.get("unit", MeasureUnit.UNIT),
        "full_text": kwargs.get("full_text", "2 large red bell peppers, diced"),
        "product_id": kwargs.get("product_id", None),
        **{k: v for k, v in kwargs.items() if k not in ["name", "quantity", "unit", "full_text", "product_id"]}
    }
    return create_api_ingredient(**final_kwargs)


def create_meat_ingredient(**kwargs) -> ApiIngredient:
    """
    Create a meat ingredient with gram-based quantities.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiIngredient representing meat
    """
    final_kwargs = {
        "name": kwargs.get("name", "Beef Sirloin"),
        "quantity": kwargs.get("quantity", 800.0),
        "unit": kwargs.get("unit", MeasureUnit.GRAM),
        "full_text": kwargs.get("full_text", "800g beef sirloin, cut into strips"),
        "product_id": kwargs.get("product_id", str(uuid4())),  # Meat likely has product ID
        **{k: v for k, v in kwargs.items() if k not in ["name", "quantity", "unit", "full_text", "product_id"]}
    }
    return create_api_ingredient(**final_kwargs)


def create_liquid_ingredient(**kwargs) -> ApiIngredient:
    """
    Create a liquid ingredient with milliliter-based quantities.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiIngredient representing a liquid
    """
    final_kwargs = {
        "name": kwargs.get("name", "Vegetable Stock"),
        "quantity": kwargs.get("quantity", 500.0),
        "unit": kwargs.get("unit", MeasureUnit.MILLILITER),
        "full_text": kwargs.get("full_text", "500ml vegetable stock, low sodium"),
        "product_id": kwargs.get("product_id", None),
        **{k: v for k, v in kwargs.items() if k not in ["name", "quantity", "unit", "full_text", "product_id"]}
    }
    return create_api_ingredient(**final_kwargs)


def create_baking_ingredient(**kwargs) -> ApiIngredient:
    """
    Create a baking ingredient with cup-based quantities.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiIngredient representing a baking ingredient
    """
    final_kwargs = {
        "name": kwargs.get("name", "All-Purpose Flour"),
        "quantity": kwargs.get("quantity", 2.5),
        "unit": kwargs.get("unit", MeasureUnit.CUP),
        "full_text": kwargs.get("full_text", "2 1/2 cups all-purpose flour, sifted"),
        "product_id": kwargs.get("product_id", None),
        **{k: v for k, v in kwargs.items() if k not in ["name", "quantity", "unit", "full_text", "product_id"]}
    }
    return create_api_ingredient(**final_kwargs)


def create_minimal_ingredient(**kwargs) -> ApiIngredient:
    """
    Create an ingredient with only required fields (no full_text or product_id).
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiIngredient with minimal required fields
    """
    final_kwargs = {
        "name": kwargs.get("name", "Salt"),
        "quantity": kwargs.get("quantity", 1.0),
        "unit": kwargs.get("unit", MeasureUnit.PINCH),
        "full_text": kwargs.get("full_text", None),
        "product_id": kwargs.get("product_id", None),
        **{k: v for k, v in kwargs.items() if k not in ["name", "quantity", "unit", "full_text", "product_id"]}
    }
    return create_api_ingredient(**final_kwargs)


def create_ingredient_with_product_id(**kwargs) -> ApiIngredient:
    """
    Create an ingredient with a product_id for testing product linking.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiIngredient with product_id set
    """
    final_kwargs = {
        "name": kwargs.get("name", "Organic Quinoa"),
        "quantity": kwargs.get("quantity", 200.0),
        "unit": kwargs.get("unit", MeasureUnit.GRAM),
        "full_text": kwargs.get("full_text", "200g organic quinoa, rinsed"),
        "product_id": kwargs.get("product_id", str(uuid4())),
        **{k: v for k, v in kwargs.items() if k not in ["name", "quantity", "unit", "full_text", "product_id"]}
    }
    return create_api_ingredient(**final_kwargs)


def create_ingredient_with_max_name(**kwargs) -> ApiIngredient:
    """
    Create an ingredient with maximum allowed name length (255 chars).
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiIngredient with maximum length name
    """
    max_name = "Extra Super Premium Organic Free-Range Grass-Fed Antibiotic-Free Hormone-Free Locally-Sourced Artisanal Handcrafted Small-Batch Heirloom Heritage Variety Traditional Recipe Slow-Cooked Authentic Italian San Marzano Tomatoes"
    max_name = max_name[:255]  # Ensure exactly 255 chars
    
    final_kwargs = {
        "name": kwargs.get("name", max_name),
        "quantity": kwargs.get("quantity", 1.0),
        "unit": kwargs.get("unit", MeasureUnit.UNIT),
        "full_text": kwargs.get("full_text", f"{max_name} - premium quality"),
        "product_id": kwargs.get("product_id", None),
        **{k: v for k, v in kwargs.items() if k not in ["name", "quantity", "unit", "full_text", "product_id"]}
    }
    return create_api_ingredient(**final_kwargs)


def create_ingredient_with_max_full_text(**kwargs) -> ApiIngredient:
    """
    Create an ingredient with maximum allowed full_text length (1000 chars).
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiIngredient with maximum length full_text
    """
    max_full_text = "This is an extremely detailed ingredient description that includes preparation instructions, quality specifications, sourcing information, and cooking notes. " * 8  # Creates ~992 chars
    max_full_text = max_full_text[:1000]  # Ensure exactly 1000 chars
    
    final_kwargs = {
        "name": kwargs.get("name", "Premium Ingredient"),
        "quantity": kwargs.get("quantity", 1.0),
        "unit": kwargs.get("unit", MeasureUnit.UNIT),
        "full_text": kwargs.get("full_text", max_full_text),
        "product_id": kwargs.get("product_id", None),
        **{k: v for k, v in kwargs.items() if k not in ["name", "quantity", "unit", "full_text", "product_id"]}
    }
    return create_api_ingredient(**final_kwargs)


def create_ingredient_with_max_quantity(**kwargs) -> ApiIngredient:
    """
    Create an ingredient with maximum allowed quantity (10000).
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiIngredient with maximum quantity
    """
    final_kwargs = {
        "name": kwargs.get("name", "Bulk Rice"),
        "quantity": kwargs.get("quantity", 10000.0),
        "unit": kwargs.get("unit", MeasureUnit.GRAM),
        "full_text": kwargs.get("full_text", "10kg bulk rice for large batch cooking"),
        "product_id": kwargs.get("product_id", None),
        **{k: v for k, v in kwargs.items() if k not in ["name", "quantity", "unit", "full_text", "product_id"]}
    }
    return create_api_ingredient(**final_kwargs)


def create_ingredient_with_max_position(**kwargs) -> ApiIngredient:
    """
    Create an ingredient with maximum allowed position (100).
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiIngredient with maximum position
    """
    final_kwargs = {
        "name": kwargs.get("name", "Final Garnish"),
        "quantity": kwargs.get("quantity", 1.0),
        "unit": kwargs.get("unit", MeasureUnit.PINCH),
        "position": kwargs.get("position", 100),
        "full_text": kwargs.get("full_text", "Final garnish for presentation"),
        "product_id": kwargs.get("product_id", None),
        **{k: v for k, v in kwargs.items() if k not in ["name", "quantity", "unit", "position", "full_text", "product_id"]}
    }
    return create_api_ingredient(**final_kwargs)


# =============================================================================
# HELPER FUNCTIONS FOR TEST SETUP
# =============================================================================

def create_recipe_ingredients(count: int = 8) -> List[ApiIngredient]:
    """Create multiple ingredients for a single recipe with sequential positions"""
    ingredients = []
    
    for i in range(count):
        ingredient_kwargs = create_api_ingredient_kwargs()
        ingredient_kwargs["position"] = i + 1  # Sequential positions
        ingredient = create_api_ingredient(**ingredient_kwargs)
        ingredients.append(ingredient)
    
    return ingredients


def create_ingredients_with_all_units() -> List[ApiIngredient]:
    """Create ingredients using all available MeasureUnit values"""
    ingredients = []
    
    for i, unit in enumerate(COMMON_MEASURE_UNITS):
        ingredient_kwargs = create_api_ingredient_kwargs()
        ingredient_kwargs["unit"] = unit
        ingredient_kwargs["position"] = i + 1
        ingredient_kwargs["name"] = f"Ingredient {i+1}"
        ingredient_kwargs["full_text"] = f"Test ingredient with {unit.value} unit"
        ingredient = create_api_ingredient(**ingredient_kwargs)
        ingredients.append(ingredient)
    
    return ingredients


def create_ingredients_with_different_quantities() -> List[ApiIngredient]:
    """Create ingredients with various quantity ranges for testing"""
    quantities = [0.1, 0.5, 1.0, 2.5, 10.0, 50.0, 100.0, 500.0, 1000.0, 5000.0]
    ingredients = []
    
    for i, quantity in enumerate(quantities):
        ingredient_kwargs = create_api_ingredient_kwargs()
        ingredient_kwargs["quantity"] = quantity
        ingredient_kwargs["position"] = i + 1
        ingredient_kwargs["name"] = f"Ingredient {quantity}g"
        ingredient = create_api_ingredient(**ingredient_kwargs)
        ingredients.append(ingredient)
    
    return ingredients


def create_test_ingredient_dataset(ingredient_count: int = 100) -> Dict[str, Any]:
    """Create a dataset of ingredients for performance testing"""
    ingredients = []
    json_strings = []
    
    for i in range(ingredient_count):
        # Create API ingredient
        ingredient_kwargs = create_api_ingredient_kwargs()
        ingredient = create_api_ingredient(**ingredient_kwargs)
        ingredients.append(ingredient)
        
        # Create JSON representation
        json_string = ingredient.model_dump_json()
        json_strings.append(json_string)
    
    return {
        "ingredients": ingredients,
        "json_strings": json_strings,
        "total_ingredients": len(ingredients)
    }


# =============================================================================
# DOMAIN AND ORM CONVERSION HELPERS
# =============================================================================

def create_ingredient_domain_from_api(api_ingredient: ApiIngredient) -> Ingredient:
    """Convert ApiIngredient to domain Ingredient using to_domain method"""
    return api_ingredient.to_domain()


def create_api_ingredient_from_domain(domain_ingredient: Ingredient) -> ApiIngredient:
    """Convert domain Ingredient to ApiIngredient using from_domain method"""
    return ApiIngredient.from_domain(domain_ingredient)


def create_ingredient_orm_kwargs_from_api(api_ingredient: ApiIngredient) -> Dict[str, Any]:
    """Convert ApiIngredient to ORM kwargs using to_orm_kwargs method"""
    return api_ingredient.to_orm_kwargs()


# =============================================================================
# JSON VALIDATION AND EDGE CASE TESTING
# =============================================================================

def create_valid_json_test_cases() -> List[Dict[str, Any]]:
    """Create various valid JSON test cases for model_validate_json testing"""
    return [
        # Standard case
        {
            "name": "Olive Oil",
            "quantity": 2.0,
            "unit": MeasureUnit.TABLESPOON.value,
            "position": 1,
            "full_text": "2 tablespoons extra virgin olive oil",
            "product_id": str(uuid4())
        },
        # Minimal case (no full_text, no product_id)
        {
            "name": "Salt",
            "quantity": 1.0,
            "unit": MeasureUnit.PINCH.value,
            "position": 2,
            "full_text": None,
            "product_id": None
        },
        # Empty full_text
        {
            "name": "Pepper",
            "quantity": 0.5,
            "unit": MeasureUnit.TEASPOON.value,
            "position": 3,
            "full_text": "",
            "product_id": None
        },
        # Edge quantities
        {
            "name": "Vanilla Extract",
            "quantity": 0.1,
            "unit": MeasureUnit.TEASPOON.value,
            "position": 4,
            "full_text": "1/10 teaspoon vanilla extract",
            "product_id": None
        },
        # Maximum values
        {
            "name": "A" * 255,  # Max name length
            "quantity": 10000.0,  # Max quantity
            "unit": MeasureUnit.GRAM.value,
            "position": 100,  # Max position
            "full_text": "B" * 1000,  # Max full_text length
            "product_id": str(uuid4())
        }
    ]


def create_invalid_json_test_cases() -> List[Dict[str, Any]]:
    """Create various invalid JSON test cases for validation error testing"""
    return [
        # Invalid quantity (negative)
        {
            "name": "Invalid Ingredient",
            "quantity": -1.0,  # Invalid
            "unit": MeasureUnit.GRAM.value,
            "position": 1,
            "full_text": "Invalid negative quantity",
            "product_id": None
        },
        # Invalid quantity (zero)
        {
            "name": "Zero Quantity",
            "quantity": 0.0,  # Invalid
            "unit": MeasureUnit.GRAM.value,
            "position": 1,
            "full_text": "Zero quantity ingredient",
            "product_id": None
        },
        # Invalid quantity (too large)
        {
            "name": "Too Much",
            "quantity": 10001.0,  # Invalid
            "unit": MeasureUnit.GRAM.value,
            "position": 1,
            "full_text": "Too much quantity",
            "product_id": None
        },
        # Invalid position (negative)
        {
            "name": "Negative Position",
            "quantity": 1.0,
            "unit": MeasureUnit.GRAM.value,
            "position": -1,  # Invalid
            "full_text": "Negative position",
            "product_id": None
        },
        # Invalid position (too large)
        {
            "name": "High Position",
            "quantity": 1.0,
            "unit": MeasureUnit.GRAM.value,
            "position": 101,  # Invalid
            "full_text": "Position too high",
            "product_id": None
        },
        # Invalid name (empty)
        {
            "name": "",  # Invalid
            "quantity": 1.0,
            "unit": MeasureUnit.GRAM.value,
            "position": 1,
            "full_text": "Empty name",
            "product_id": None
        },
        # Invalid name (too long)
        {
            "name": "A" * 256,  # Invalid
            "quantity": 1.0,
            "unit": MeasureUnit.GRAM.value,
            "position": 1,
            "full_text": "Name too long",
            "product_id": None
        },
        # Invalid full_text (too long)
        {
            "name": "Long Description",
            "quantity": 1.0,
            "unit": MeasureUnit.GRAM.value,
            "position": 1,
            "full_text": "A" * 1001,  # Invalid
            "product_id": None
        },
        # Invalid product_id (not UUID format)
        {
            "name": "Invalid Product",
            "quantity": 1.0,
            "unit": MeasureUnit.GRAM.value,
            "position": 1,
            "full_text": "Invalid product ID",
            "product_id": "not-a-uuid"  # Invalid
        },
        # Invalid unit (not in enum)
        {
            "name": "Invalid Unit",
            "quantity": 1.0,
            "unit": "invalid-unit",  # Invalid
            "position": 1,
            "full_text": "Invalid unit",
            "product_id": None
        },
        # Missing required fields
        {
            "name": "Incomplete",
            # Missing quantity, unit, position
            "full_text": "Missing required fields",
            "product_id": None
        }
    ]


def check_json_serialization_roundtrip(api_ingredient: ApiIngredient) -> bool:
    """Test that JSON serialization and deserialization preserves data integrity"""
    # Serialize to JSON
    json_str = api_ingredient.model_dump_json()
    
    # Deserialize from JSON
    restored_ingredient = ApiIngredient.model_validate_json(json_str)
    
    # Compare original and restored
    return api_ingredient == restored_ingredient 