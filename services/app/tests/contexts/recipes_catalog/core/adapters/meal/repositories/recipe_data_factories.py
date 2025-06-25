"""
Data factories for Recipe testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- Parametrized test scenarios for filtering
- Performance test scenarios with dataset expectations
- Specialized factory functions for different recipe types
- ORM equivalents for all domain factory methods
- Comprehensive attribute validation using check_missing_attributes
- Realistic data sets for production-like testing

All data follows the exact structure of Recipe domain entities and their relationships.
Both domain and ORM variants are provided for comprehensive testing scenarios.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import Ingredient
from src.contexts.recipes_catalog.core.domain.meal.value_objects.rating import Rating
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.enums import MeasureUnit, Privacy

# ORM model imports
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import RecipeSaModel
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.ingredient_sa_model import IngredientSaModel
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.rating_sa_model import RatingSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import TagSaModel
from src.contexts.recipes_catalog.core.adapters.name_search import StrProcessor

# Import check_missing_attributes for validation
from tests.utils import check_missing_attributes

# =============================================================================
# REALISTIC DATA SETS FOR PRODUCTION-LIKE TESTING
# =============================================================================

REALISTIC_RECIPES = [
    {
        "name": "Classic Spaghetti Carbonara",
        "description": "Traditional Roman pasta dish with eggs, cheese, pancetta, and black pepper. Creamy without cream, this authentic recipe delivers rich, comforting flavors.",
        "instructions": "1. Bring a large pot of salted water to boil for the pasta. 2. Cut 200g pancetta into small cubes and cook in a large skillet over medium heat until crispy (about 5-7 minutes). 3. In a bowl, whisk together 3 large eggs, 100g grated Pecorino Romano, and plenty of freshly cracked black pepper. 4. Cook 400g spaghetti according to package directions until al dente, reserving 1 cup pasta water before draining. 5. Remove pancetta from heat and immediately add hot, drained pasta to the skillet. 6. Quickly toss pasta with pancetta, then remove from heat completely. 7. Slowly pour egg mixture over pasta while tossing continuously to create a creamy sauce (don't scramble the eggs!). 8. Add pasta water gradually if needed to achieve creamy consistency. 9. Serve immediately with extra Pecorino Romano and black pepper.",
        "utensils": "Large pot, large skillet, whisk, tongs, cheese grater, measuring cups",
        "total_time": 25,
        "notes": "The key is removing the pan from heat before adding eggs to prevent scrambling. Use fresh black pepper for best flavor.",
        "privacy": Privacy.PUBLIC,
        "weight_in_grams": 600,
        "average_taste_rating": 4.8,
        "average_convenience_rating": 3.5,
        "tags": ["pasta", "italian", "traditional", "dinner"]
    },
    {
        "name": "Thai Green Curry Chicken",
        "description": "Aromatic Thai curry with tender chicken, vegetables, and fresh herbs in rich coconut milk. Spicy, fragrant, and deeply satisfying.",
        "instructions": "1. Heat 2 tbsp coconut oil in a large wok or deep skillet over medium-high heat. 2. Add 3 tbsp green curry paste and stir-fry for 1-2 minutes until fragrant. 3. Pour in the thick part of 1 can coconut milk (about 1/2 cup) and simmer until oil separates. 4. Add 500g diced chicken thigh and cook until nearly done (about 8 minutes). 5. Add remaining coconut milk, 2 tbsp fish sauce, 1 tbsp brown sugar, and Thai basil leaves. 6. Add sliced bell peppers, baby eggplants, and bamboo shoots. 7. Simmer for 10-15 minutes until vegetables are tender and chicken is cooked through. 8. Taste and adjust seasoning with more fish sauce, sugar, or curry paste as needed. 9. Garnish with fresh Thai basil, sliced red chilies, and serve with jasmine rice.",
        "utensils": "Large wok or deep skillet, wooden spoon, knife, cutting board",
        "total_time": 35,
        "notes": "Adjust spice level by varying the amount of curry paste. Fresh Thai basil is essential for authentic flavor.",
        "privacy": Privacy.PUBLIC,
        "weight_in_grams": 550,
        "average_taste_rating": 4.6,
        "average_convenience_rating": 3.2,
        "tags": ["curry", "thai", "asian", "spicy", "dinner"]
    },
    {
        "name": "Mediterranean Quinoa Bowl",
        "description": "Nutritious and colorful bowl with fluffy quinoa, roasted vegetables, feta cheese, and tahini dressing. Perfect for healthy lunch or dinner.",
        "instructions": "1. Preheat oven to 220°C (425°F). 2. Rinse 1 cup quinoa until water runs clear, then cook in 2 cups vegetable broth for 15 minutes. 3. Dice zucchini, bell peppers, and red onion into 2cm pieces. 4. Toss vegetables with 2 tbsp olive oil, salt, pepper, and dried oregano. 5. Roast vegetables for 20-25 minutes until tender and lightly caramelized. 6. For tahini dressing: whisk together 3 tbsp tahini, 2 tbsp lemon juice, 1 tbsp olive oil, and 2-3 tbsp water. 7. Season dressing with salt, pepper, and a pinch of garlic powder. 8. Fluff cooked quinoa with a fork and let cool slightly. 9. Assemble bowls with quinoa base, roasted vegetables, cherry tomatoes, cucumber, and crumbled feta. 10. Drizzle with tahini dressing and garnish with fresh parsley and pine nuts.",
        "utensils": "Large baking sheet, saucepan, whisk, knife, cutting board, serving bowls",
        "total_time": 45,
        "notes": "Can be prepared ahead and stored in fridge for up to 3 days. Add dressing just before serving.",
        "privacy": Privacy.PUBLIC,
        "weight_in_grams": 450,
        "average_taste_rating": 4.4,
        "average_convenience_rating": 4.0,
        "tags": ["quinoa", "mediterranean", "vegetarian", "healthy", "lunch"]
    },
    {
        "name": "Chocolate Chip Cookies",
        "description": "Classic homemade chocolate chip cookies with crispy edges and chewy centers. The perfect comfort dessert.",
        "instructions": "1. Preheat oven to 180°C (350°F) and line baking sheets with parchment paper. 2. Cream together 115g softened butter, 75g brown sugar, and 50g white sugar until light and fluffy. 3. Beat in 1 large egg and 1 tsp vanilla extract. 4. In separate bowl, whisk together 150g flour, 1/2 tsp baking soda, and 1/2 tsp salt. 5. Gradually mix dry ingredients into wet ingredients until just combined. 6. Fold in 100g chocolate chips. 7. Drop rounded tablespoons of dough onto prepared baking sheets, spacing 5cm apart. 8. Bake for 9-11 minutes until edges are golden but centers still look slightly underbaked. 9. Cool on baking sheet for 5 minutes before transferring to wire rack.",
        "utensils": "Electric mixer, baking sheets, parchment paper, wire cooling rack, measuring cups",
        "total_time": 30,
        "notes": "Don't overbake - cookies will continue cooking on the hot pan. For chewier cookies, slightly underbake.",
        "privacy": Privacy.PUBLIC,
        "weight_in_grams": 300,
        "average_taste_rating": 4.9,
        "average_convenience_rating": 4.2,
        "tags": ["cookies", "dessert", "baking", "chocolate", "sweet"]
    },
    {
        "name": "Grilled Salmon with Lemon Herbs",
        "description": "Simple yet elegant grilled salmon with fresh herbs and lemon. Light, healthy, and full of flavor.",
        "instructions": "1. Preheat grill to medium-high heat and oil the grates. 2. Pat 4 salmon fillets (150g each) dry and season with salt and pepper. 3. Mix together 2 tbsp olive oil, zest of 1 lemon, 2 tbsp fresh dill, and 1 tbsp fresh parsley. 4. Brush herb mixture over salmon fillets. 5. Grill salmon skin-side down for 4-5 minutes, then flip and grill for 3-4 more minutes until fish flakes easily. 6. Remove from grill and immediately squeeze fresh lemon juice over the top. 7. Garnish with additional fresh herbs and lemon wedges.",
        "utensils": "Grill, grill brush, fish spatula, small mixing bowl",
        "total_time": 15,
        "notes": "Don't overcook salmon - it should still be slightly pink in the center. Great with steamed vegetables or rice.",
        "privacy": Privacy.PUBLIC,
        "weight_in_grams": 200,
        "average_taste_rating": 4.7,
        "average_convenience_rating": 4.5,
        "tags": ["salmon", "grilled", "healthy", "quick", "seafood"]
    }
]

# =============================================================================
# STATIC COUNTERS FOR DETERMINISTIC IDS
# =============================================================================

_RECIPE_COUNTER = 1
_INGREDIENT_COUNTER = 1
_RATING_COUNTER = 1
_TAG_COUNTER = 1


def reset_counters() -> None:
    """Reset all counters for test isolation"""
    global _RECIPE_COUNTER, _INGREDIENT_COUNTER, _RATING_COUNTER, _TAG_COUNTER
    _RECIPE_COUNTER = 1
    _INGREDIENT_COUNTER = 1
    _RATING_COUNTER = 1
    _TAG_COUNTER = 1


# =============================================================================
# RECIPE DATA FACTORIES (DOMAIN)
# =============================================================================

def create_recipe_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create recipe kwargs with deterministic values and comprehensive validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with recipe creation parameters
    """
    global _RECIPE_COUNTER
    
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    # Use realistic recipe data if available
    recipe_index = (_RECIPE_COUNTER - 1) % len(REALISTIC_RECIPES)
    realistic_recipe = REALISTIC_RECIPES[recipe_index]
    
    final_kwargs = {
        "id": kwargs.get("id", f"recipe_{_RECIPE_COUNTER:03d}"),
        "name": kwargs.get("name", realistic_recipe["name"]),
        "author_id": kwargs.get("author_id", f"author_{(_RECIPE_COUNTER % 5) + 1}"),
        "meal_id": kwargs.get("meal_id", f"meal_{(_RECIPE_COUNTER % 10) + 1}"),
        "instructions": kwargs.get("instructions", realistic_recipe["instructions"]),
        "total_time": kwargs.get("total_time", realistic_recipe.get("total_time", (15 + (_RECIPE_COUNTER * 5)) if _RECIPE_COUNTER % 4 != 0 else None)),
        "description": kwargs.get("description", realistic_recipe.get("description", f"Test recipe description {_RECIPE_COUNTER}" if _RECIPE_COUNTER % 3 != 0 else None)),
        "utensils": kwargs.get("utensils", realistic_recipe.get("utensils", f"pot, pan, spoon" if _RECIPE_COUNTER % 2 == 0 else None)),
        "notes": kwargs.get("notes", realistic_recipe.get("notes", f"Test notes for recipe {_RECIPE_COUNTER}" if _RECIPE_COUNTER % 4 != 0 else None)),
        "privacy": kwargs.get("privacy", realistic_recipe.get("privacy", Privacy.PUBLIC if _RECIPE_COUNTER % 3 == 0 else Privacy.PRIVATE)),
        "weight_in_grams": kwargs.get("weight_in_grams", realistic_recipe.get("weight_in_grams", (200 + (_RECIPE_COUNTER * 50)) if _RECIPE_COUNTER % 3 != 0 else None)),
        "image_url": kwargs.get("image_url", f"https://example.com/recipe_{_RECIPE_COUNTER}.jpg" if _RECIPE_COUNTER % 2 == 0 else None),
        
        # Constructor-accepted attributes
        "nutri_facts": kwargs.get("nutri_facts", None),  # Will be created separately if needed
        "ratings": kwargs.get("ratings", []),  # List of rating objects
        "ingredients": kwargs.get("ingredients", []),  # List of ingredient objects
        "tags": kwargs.get("tags", set()),  # Set of tag objects
        
        # Standard entity fields
        "created_at": kwargs.get("created_at", base_time + timedelta(hours=_RECIPE_COUNTER)),
        "updated_at": kwargs.get("updated_at", base_time + timedelta(hours=_RECIPE_COUNTER, minutes=15)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Note: We don't use check_missing_attributes here because Recipe has many 
    # calculated/derived properties (like average_convenience_rating, calorie_density, etc.)
    # that are not constructor parameters but are computed from other data
    
    # Increment counter for next call
    _RECIPE_COUNTER += 1
    
    return final_kwargs


def create_recipe(**kwargs) -> _Recipe:
    """
    Create a Recipe domain entity with deterministic data and validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity with comprehensive validation
    """
    recipe_kwargs = create_recipe_kwargs(**kwargs)
    return _Recipe(**recipe_kwargs)


# =============================================================================
# RECIPE DATA FACTORIES (ORM)
# =============================================================================

def create_recipe_orm_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create recipe ORM kwargs with deterministic values.
    
    Similar to create_recipe_kwargs but includes ORM-specific fields like preprocessed_name
    and nutritional calculation fields.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required ORM recipe creation parameters
    """
    global _RECIPE_COUNTER
    
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    final_kwargs = {
        "id": kwargs.get("id", f"recipe_{_RECIPE_COUNTER:03d}"),
        "name": kwargs.get("name", f"Test Recipe {_RECIPE_COUNTER}"),
        "preprocessed_name": kwargs.get("preprocessed_name", StrProcessor(f"Test Recipe {_RECIPE_COUNTER}").output),
        "author_id": kwargs.get("author_id", f"author_{(_RECIPE_COUNTER % 5) + 1}"),
        "meal_id": kwargs.get("meal_id", f"meal_{(_RECIPE_COUNTER % 10) + 1}"),
        "instructions": kwargs.get("instructions", f"Test instructions for recipe {_RECIPE_COUNTER}. Step 1: Prepare ingredients. Step 2: Cook thoroughly."),
        "total_time": kwargs.get("total_time", (15 + (_RECIPE_COUNTER * 5)) if _RECIPE_COUNTER % 4 != 0 else None),
        "description": kwargs.get("description", f"Test recipe description {_RECIPE_COUNTER}" if _RECIPE_COUNTER % 3 != 0 else None),
        "utensils": kwargs.get("utensils", f"pot, pan, spoon" if _RECIPE_COUNTER % 2 == 0 else None),
        "notes": kwargs.get("notes", f"Test notes for recipe {_RECIPE_COUNTER}" if _RECIPE_COUNTER % 4 != 0 else None),
        "privacy": kwargs.get("privacy", Privacy.PUBLIC.value if _RECIPE_COUNTER % 3 == 0 else Privacy.PRIVATE.value),  # String values for ORM
        "weight_in_grams": kwargs.get("weight_in_grams", (200 + (_RECIPE_COUNTER * 50)) if _RECIPE_COUNTER % 3 != 0 else None),
        "calorie_density": kwargs.get("calorie_density", 1.5 + (_RECIPE_COUNTER % 2)),  # 1.5-3.5 cal/g
        "carbo_percentage": kwargs.get("carbo_percentage", 40.0 + (_RECIPE_COUNTER % 20)),  # 40-60%
        "protein_percentage": kwargs.get("protein_percentage", 15.0 + (_RECIPE_COUNTER % 15)),  # 15-30%
        "total_fat_percentage": kwargs.get("total_fat_percentage", 20.0 + (_RECIPE_COUNTER % 20)),  # 20-40%
        "image_url": kwargs.get("image_url", f"https://example.com/recipe_{_RECIPE_COUNTER}.jpg" if _RECIPE_COUNTER % 2 == 0 else None),
        "created_at": kwargs.get("created_at", base_time + timedelta(hours=_RECIPE_COUNTER)),
        "updated_at": kwargs.get("updated_at", base_time + timedelta(hours=_RECIPE_COUNTER, minutes=30)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
        "average_taste_rating": kwargs.get("average_taste_rating", 3.5 + (_RECIPE_COUNTER % 2)),  # ORM calculated field
        "average_convenience_rating": kwargs.get("average_convenience_rating", 3.0 + (_RECIPE_COUNTER % 3)),  # ORM calculated field
        "nutri_facts": kwargs.get("nutri_facts", None),  # Will be created separately if needed
        "ingredients": kwargs.get("ingredients", []),  # Will be populated separately if needed
        "tags": kwargs.get("tags", []),  # List for ORM relationships
        "ratings": kwargs.get("ratings", []),  # List for ORM relationships
    }
    
    # # Validation logic
    # required_fields = ["id", "name", "author_id", "meal_id", "instructions"]
    # for field in required_fields:
    #     if not final_kwargs.get(field):
    #         raise ValueError(f"Required field '{field}' cannot be empty")
    
    # # Validate author_id format
    # if not isinstance(final_kwargs["author_id"], str) or not final_kwargs["author_id"]:
    #     raise ValueError("author_id must be a non-empty string")
    
    # # Validate meal_id format
    # if not isinstance(final_kwargs["meal_id"], str) or not final_kwargs["meal_id"]:
    #     raise ValueError("meal_id must be a non-empty string")
    
    # Increment counter for next call
    _RECIPE_COUNTER += 1
    
    return final_kwargs


def create_recipe_orm(**kwargs) -> RecipeSaModel:
    """
    Create a RecipeSaModel ORM instance with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        RecipeSaModel ORM instance
    """
    recipe_kwargs = create_recipe_orm_kwargs(**kwargs)
    return RecipeSaModel(**recipe_kwargs)


# =============================================================================
# INGREDIENT DATA FACTORIES (DOMAIN)
# =============================================================================

def create_ingredient_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create ingredient kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with ingredient creation parameters
    """
    global _INGREDIENT_COUNTER
    
    # Cycle through different ingredient types for realism
    ingredient_names = ["Flour", "Sugar", "Salt", "Olive Oil", "Onion", "Garlic", "Tomato", "Chicken Breast", "Rice", "Pasta"]
    units = [MeasureUnit.GRAM, MeasureUnit.MILLILITER, MeasureUnit.PIECE, MeasureUnit.CUP, MeasureUnit.TABLESPOON]
    
    name = kwargs.get("name", ingredient_names[(_INGREDIENT_COUNTER - 1) % len(ingredient_names)])
    unit = kwargs.get("unit", units[(_INGREDIENT_COUNTER - 1) % len(units)])
    
    final_kwargs = {
        "name": name,
        "unit": kwargs.get("unit", unit),
        "quantity": kwargs.get("quantity", 50.0 + (_INGREDIENT_COUNTER * 10)),
        "position": kwargs.get("position", (_INGREDIENT_COUNTER - 1) % 10),  # Keep positions reasonable
        "full_text": kwargs.get("full_text", f"{50 + (_INGREDIENT_COUNTER * 10)}{unit} of {name.lower()}"),
        "product_id": kwargs.get("product_id", f"product_{_INGREDIENT_COUNTER:03d}" if _INGREDIENT_COUNTER % 2 == 0 else None),
    }
    
    _INGREDIENT_COUNTER += 1
    return final_kwargs


def create_ingredient(**kwargs) -> Ingredient:
    """
    Create an Ingredient value object with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Ingredient value object
    """
    ingredient_kwargs = create_ingredient_kwargs(**kwargs)
    return Ingredient(**ingredient_kwargs)


# =============================================================================
# INGREDIENT DATA FACTORIES (ORM)
# =============================================================================

def create_ingredient_orm_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create ingredient ORM kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with ORM ingredient creation parameters
    """
    # Use the same logic as domain ingredients but adapt for ORM fields
    ingredient_kwargs = create_ingredient_kwargs(**kwargs)
    
    # ORM specific adaptations
    final_kwargs = {
        "name": kwargs.get("name", ingredient_kwargs["name"]),
        "unit": kwargs.get("unit", ingredient_kwargs["unit"]),  # Convert enum to string for ORM
        "quantity": kwargs.get("quantity", ingredient_kwargs["quantity"]),
        "position": kwargs.get("position", ingredient_kwargs["position"]),
        "full_text": kwargs.get("full_text", ingredient_kwargs["full_text"]),
        "product_id": kwargs.get("product_id", ingredient_kwargs["product_id"]),
        "recipe_id": kwargs.get("recipe_id", f"recipe_{(_INGREDIENT_COUNTER % 10) + 1}"),
    }
    final_kwargs["preprocessed_name"] = kwargs.get("preprocessed_name", StrProcessor(final_kwargs["name"]).output)
    
    return final_kwargs


def create_ingredient_orm(**kwargs) -> IngredientSaModel:
    """
    Create an IngredientSaModel ORM instance with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        IngredientSaModel ORM instance
    """
    ingredient_kwargs = create_ingredient_orm_kwargs(**kwargs)
    return IngredientSaModel(**ingredient_kwargs)


# =============================================================================
# RATING DATA FACTORIES (DOMAIN)
# =============================================================================

def create_rating_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create rating kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with rating creation parameters
    """
    global _RATING_COUNTER
    
    # Ensure ratings are in valid range (0-5)
    taste_score = (_RATING_COUNTER % 6)  # 0, 1, 2, 3, 4, 5, 0, 1, ...
    convenience_score = ((_RATING_COUNTER + 2) % 6)  # 2, 3, 4, 5, 0, 1, 2, 3, ...
    
    final_kwargs = {
        "user_id": kwargs.get("user_id", f"user_{((_RATING_COUNTER - 1) % 5) + 1}"),  # Cycle through 5 users
        "recipe_id": kwargs.get("recipe_id", f"recipe_{((_RATING_COUNTER - 1) % 10) + 1}"),  # Cycle through 10 recipes
        "taste": kwargs.get("taste", taste_score),
        "convenience": kwargs.get("convenience", convenience_score),
        "comment": kwargs.get("comment", f"Test comment {_RATING_COUNTER}" if _RATING_COUNTER % 3 != 0 else None),
    }
    
    _RATING_COUNTER += 1
    return final_kwargs


def create_rating(**kwargs) -> Rating:
    """
    Create a Rating value object with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Rating value object
    """
    rating_kwargs = create_rating_kwargs(**kwargs)
    return Rating(**rating_kwargs)


# =============================================================================
# RATING DATA FACTORIES (ORM)
# =============================================================================

def create_rating_orm_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create rating ORM kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with ORM rating creation parameters
    """
    # Use the same logic as domain ratings
    rating_kwargs = create_rating_kwargs(**kwargs)
    
    # ORM specific adaptations - add created_at timestamp
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    final_kwargs = {
        "user_id": kwargs.get("user_id", rating_kwargs["user_id"]),
        "recipe_id": kwargs.get("recipe_id", rating_kwargs["recipe_id"]),
        "taste": kwargs.get("taste", rating_kwargs["taste"]),
        "convenience": kwargs.get("convenience", rating_kwargs["convenience"]),
        "comment": kwargs.get("comment", rating_kwargs["comment"]),
        "created_at": kwargs.get("created_at", base_time + timedelta(hours=_RATING_COUNTER)),
    }
    
    return final_kwargs


def create_rating_orm(**kwargs) -> RatingSaModel:
    """
    Create a RatingSaModel ORM instance with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        RatingSaModel ORM instance
    """
    rating_kwargs = create_rating_orm_kwargs(**kwargs)
    return RatingSaModel(**rating_kwargs)


# =============================================================================
# TAG DATA FACTORIES (DOMAIN)
# =============================================================================

def create_tag_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create tag kwargs with deterministic values for recipes.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with tag creation parameters
    """
    global _TAG_COUNTER
    
    # Predefined tag types for realistic recipe test data
    keys = ["cuisine", "diet", "difficulty", "meal_type", "cooking_method"]
    values_by_key = {
        "cuisine": ["italian", "mexican", "asian", "american", "french"],
        "diet": ["vegetarian", "vegan", "keto", "paleo", "gluten-free"],
        "difficulty": ["easy", "medium", "hard"],
        "meal_type": ["breakfast", "lunch", "dinner", "snack", "dessert"],
        "cooking_method": ["baked", "grilled", "fried", "steamed", "raw"]
    }
    
    key = keys[(_TAG_COUNTER - 1) % len(keys)]
    value = values_by_key[key][(_TAG_COUNTER - 1) % len(values_by_key[key])]
    
    final_kwargs = {
        "key": kwargs.get("key", key),
        "value": kwargs.get("value", value),
        "author_id": kwargs.get("author_id", f"author_{((_TAG_COUNTER - 1) % 5) + 1}"),
        "type": kwargs.get("type", "recipe"),  # Always recipe type for recipe tags
    }
    
    _TAG_COUNTER += 1
    return final_kwargs


def create_tag(**kwargs) -> Tag:
    """
    Create a Tag value object with deterministic data for recipes.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Tag value object
    """
    tag_kwargs = create_tag_kwargs(**kwargs)
    return Tag(**tag_kwargs)


# =============================================================================
# TAG DATA FACTORIES (ORM)
# =============================================================================

def create_tag_orm_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create tag ORM kwargs with deterministic values for recipes.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with ORM tag creation parameters
    """
    # Use the same logic as domain tags but without incrementing counter twice
    tag_kwargs = create_tag_kwargs(**kwargs)
    
    # ORM models use auto-increment for id, so we remove it from kwargs if present
    final_kwargs = {
        "key": kwargs.get("key", tag_kwargs["key"]),
        "value": kwargs.get("value", tag_kwargs["value"]),
        "author_id": kwargs.get("author_id", tag_kwargs["author_id"]),
        "type": kwargs.get("type", tag_kwargs["type"]),
    }
    # Keep the id field for testing purposes - TagSaModel has auto-increment but we can override
    
    return final_kwargs


def create_tag_orm(**kwargs) -> TagSaModel:
    """
    Create a TagSaModel ORM instance with deterministic data for recipes.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        TagSaModel ORM instance
    """
    tag_kwargs = create_tag_orm_kwargs(**kwargs)
    return TagSaModel(**tag_kwargs)


# =============================================================================
# PARAMETRIZED TEST SCENARIOS
# =============================================================================

def get_recipe_filter_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for testing recipe filtering.
    
    Returns:
        List of test scenarios with recipe_kwargs, filter, and expected outcome
    """
    return [
        {
            "scenario_id": "total_time_gte_match",
            "recipe_kwargs": {"name": "Long Cooking Recipe", "total_time": 60},
            "filter": {"total_time_gte": 45},
            "should_match": True,
            "description": "Recipe with 60min total_time should match gte filter of 45min"
        },
        {
            "scenario_id": "total_time_lte_match",
            "recipe_kwargs": {"name": "Quick Recipe", "total_time": 15},
            "filter": {"total_time_lte": 30},
            "should_match": True,
            "description": "Recipe with 15min total_time should match lte filter of 30min"
        },
        {
            "scenario_id": "total_time_range_match",
            "recipe_kwargs": {"name": "Medium Recipe", "total_time": 25},
            "filter": {"total_time_gte": 20, "total_time_lte": 30},
            "should_match": True,
            "description": "Recipe with 25min total_time should match range filter 20-30min"
        },
        {
            "scenario_id": "privacy_public_match",
            "recipe_kwargs": {"name": "Public Recipe", "privacy": Privacy.PUBLIC},
            "filter": {"privacy": "public"},
            "should_match": True,
            "description": "Public recipe should match privacy filter"
        },
        {
            "scenario_id": "privacy_private_match",
            "recipe_kwargs": {"name": "Private Recipe", "privacy": Privacy.PRIVATE},
            "filter": {"privacy": "private"},
            "should_match": True,
            "description": "Private recipe should match privacy filter"
        },
        {
            "scenario_id": "author_id_match",
            "recipe_kwargs": {"name": "Author Recipe", "author_id": "test_author_123"},
            "filter": {"author_id": "test_author_123"},
            "should_match": True,
            "description": "Recipe should match author_id filter"
        },
        {
            "scenario_id": "meal_id_match",
            "recipe_kwargs": {"name": "Meal Recipe", "meal_id": "test_meal_456"},
            "filter": {"meal_id": "test_meal_456"},
            "should_match": True,
            "description": "Recipe should match meal_id filter"
        },
        {
            "scenario_id": "calories_gte_match",
            "recipe_kwargs": {
                "name": "High Calorie Recipe",
                "nutri_facts": NutriFacts(calories=500.0, protein=20.0, carbohydrate=40.0, total_fat=15.0)
            },
            "filter": {"calories_gte": 400.0},
            "should_match": True,
            "description": "Recipe with 500 calories should match gte filter of 400"
        },
        {
            "scenario_id": "protein_gte_match", 
            "recipe_kwargs": {
                "name": "High Protein Recipe",
                "nutri_facts": NutriFacts(calories=300.0, protein=30.0, carbohydrate=20.0, total_fat=10.0)
            },
            "filter": {"protein_gte": 25.0},
            "should_match": True,
            "description": "Recipe with 30g protein should match gte filter of 25g"
        },
        {
            "scenario_id": "weight_range_match",
            "recipe_kwargs": {"name": "Medium Weight Recipe", "weight_in_grams": 300},
            "filter": {"weight_in_grams_gte": 200, "weight_in_grams_lte": 400},
            "should_match": True,
            "description": "Recipe with 300g weight should match range filter 200-400g"
        }
    ]


def get_ingredient_relationship_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for testing ingredient relationships.
    
    Returns:
        List of test scenarios for ingredient filtering and relationships
    """
    return [
        {
            "scenario_id": "single_product_ingredient",
            "recipe_kwargs": {
                "name": "Recipe with Product Ingredient",
                "ingredients": [
                    Ingredient(
                        name="Test Flour",
                        unit=MeasureUnit.GRAM,
                        quantity=200.0,
                        position=0,
                        full_text="200g of test flour",
                        product_id="flour_product_123"
                    )
                ]
            },
            "filter": {"products": ["flour_product_123"]},
            "should_match": True,
            "description": "Recipe should match when filtering by ingredient product ID"
        },
        {
            "scenario_id": "multiple_product_ingredients",
            "recipe_kwargs": {
                "name": "Recipe with Multiple Products",
                "ingredients": [
                    Ingredient(name="Flour", unit=MeasureUnit.GRAM, quantity=200.0, position=0, product_id="flour_123"),
                    Ingredient(name="Sugar", unit=MeasureUnit.GRAM, quantity=100.0, position=1, product_id="sugar_456"),
                ]
            },
            "filter": {"products": ["flour_123", "sugar_456"]},
            "should_match": True,
            "description": "Recipe should match when filtering by multiple product IDs"
        },
        {
            "scenario_id": "ingredient_without_product",
            "recipe_kwargs": {
                "name": "Recipe with Generic Ingredient",
                "ingredients": [
                    Ingredient(name="Salt", unit=MeasureUnit.TEASPOON, quantity=1.0, position=0, product_id=None)
                ]
            },
            "filter": {"products": ["salt_product_789"]},
            "should_match": False,
            "description": "Recipe with generic ingredient (no product_id) should not match product filter"
        }
    ]


def get_rating_aggregation_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for testing rating aggregation.
    
    Returns:
        List of test scenarios for rating filtering and aggregation
    """
    return [
        {
            "scenario_id": "high_taste_rating",
            "recipe_kwargs": {
                "name": "Highly Rated Recipe",
                "ratings": [
                    Rating(user_id="user_1", recipe_id="recipe_001", taste=5, convenience=4, comment="Excellent!"),
                    Rating(user_id="user_2", recipe_id="recipe_001", taste=4, convenience=5, comment="Great recipe"),
                ]
            },
            "filter": {"average_taste_rating_gte": 4.0},
            "should_match": True,
            "description": "Recipe with average taste rating 4.5 should match gte filter of 4.0"
        },
        {
            "scenario_id": "high_convenience_rating",
            "recipe_kwargs": {
                "name": "Convenient Recipe",
                "ratings": [
                    Rating(user_id="user_1", recipe_id="recipe_002", taste=3, convenience=5, comment="Easy to make"),
                    Rating(user_id="user_2", recipe_id="recipe_002", taste=4, convenience=5, comment="Quick recipe"),
                ]
            },
            "filter": {"average_convenience_rating_gte": 4.5},
            "should_match": True,
            "description": "Recipe with average convenience rating 5.0 should match gte filter of 4.5"
        },
        {
            "scenario_id": "no_ratings",
            "recipe_kwargs": {
                "name": "Unrated Recipe",
                "ratings": []
            },
            "filter": {"average_taste_rating_gte": 3.0},
            "should_match": False,
            "description": "Recipe with no ratings should not match rating filter"
        }
    ]


def get_tag_filtering_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for testing tag filtering.
    
    Returns:
        List of test scenarios with tag filtering expectations
    """
    return [
        {
            "scenario_id": "single_tag_match",
            "recipe_kwargs": {
                "name": "Italian Recipe",
                "tags": {
                    Tag(key="cuisine", value="italian", author_id="author_1", type="recipe")
                }
            },
            "filter": {"tags": [("cuisine", "italian", "author_1")]},
            "should_match": True,
            "description": "Recipe with Italian cuisine tag should match cuisine filter"
        },
        {
            "scenario_id": "multiple_tags_match",
            "recipe_kwargs": {
                "name": "Easy Vegetarian Recipe",
                "tags": {
                    Tag(key="diet", value="vegetarian", author_id="author_1", type="recipe"),
                    Tag(key="difficulty", value="easy", author_id="author_1", type="recipe")
                }
            },
            "filter": {"tags": [("diet", "vegetarian", "author_1"), ("difficulty", "easy", "author_1")]},
            "should_match": True,
            "description": "Recipe with multiple matching tags should match multi-tag filter"
        },
        {
            "scenario_id": "tag_not_exists",
            "recipe_kwargs": {
                "name": "Simple Recipe",
                "tags": {
                    Tag(key="difficulty", value="easy", author_id="author_1", type="recipe")
                }
            },
            "filter": {"tags_not_exists": [("diet", "vegan", "author_1")]},
            "should_match": True,
            "description": "Recipe without vegan tag should match tags_not_exists filter"
        }
    ]


def get_performance_test_scenarios() -> List[Dict[str, Any]]:
    """
    Get scenarios for performance testing with dataset expectations.
    
    Returns:
        List of performance test scenarios
    """
    return [
        {
            "scenario_id": "bulk_recipe_creation",
            "dataset_size": 100,
            "expected_time_per_entity": 0.005,  # 5ms per recipe
            "description": "Bulk creation of 100 recipes should complete within 500ms total"
        },
        {
            "scenario_id": "complex_filter_query",
            "dataset_size": 1000,
            "filter": {
                "total_time_gte": 30,
                "total_time_lte": 120,
                "privacy": "public",
                "calories_gte": 200,
                "protein_gte": 15
            },
            "expected_query_time": 1.0,  # 1 second max
            "description": "Complex filter query on 1000 recipes should complete within 1 second"
        },
        {
            "scenario_id": "tag_filtering_performance",
            "dataset_size": 500,
            "filter": {"tags": [("cuisine", "italian", "author_1")]},
            "expected_query_time": 0.5,  # 500ms max
            "description": "Tag filtering on 500 recipes should complete within 500ms"
        }
    ]


# =============================================================================
# SPECIALIZED RECIPE FACTORIES (DOMAIN)
# =============================================================================

def create_quick_recipe(**kwargs) -> _Recipe:
    """
    Create a quick-cooking recipe (≤20 minutes).
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity optimized for quick cooking
    """
    final_kwargs = {
        "name": kwargs.get("name", "Quick Recipe"),
        "total_time": kwargs.get("total_time", 15),
        "instructions": kwargs.get("instructions", "Quick and easy instructions. Heat, mix, serve."),
        "tags": kwargs.get("tags", {
            Tag(key="difficulty", value="easy", author_id="author_1", type="recipe"),
            Tag(key="cooking_method", value="raw", author_id="author_1", type="recipe")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "total_time", "instructions", "tags"]}
    }
    return create_recipe(**final_kwargs)


def create_high_protein_recipe(**kwargs) -> _Recipe:
    """
    Create a high-protein recipe (≥25g protein).
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity optimized for high protein content
    """
    final_kwargs = {
        "name": kwargs.get("name", "High Protein Recipe"),
        "nutri_facts": kwargs.get("nutri_facts", NutriFacts(
            calories=400.0,
            protein=30.0,  # High protein content
            carbohydrate=15.0,
            total_fat=12.0
        )),
        "ingredients": kwargs.get("ingredients", [
            Ingredient(name="Chicken Breast", unit=MeasureUnit.GRAM, quantity=200.0, position=0, product_id="chicken_123"),
            Ingredient(name="Greek Yogurt", unit=MeasureUnit.GRAM, quantity=100.0, position=1, product_id="yogurt_456"),
        ]),
        "tags": kwargs.get("tags", {
            Tag(key="diet", value="high-protein", author_id="author_1", type="recipe")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "nutri_facts", "ingredients", "tags"]}
    }
    return create_recipe(**final_kwargs)


def create_vegetarian_recipe(**kwargs) -> _Recipe:
    """
    Create a vegetarian recipe.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity suitable for vegetarians
    """
    final_kwargs = {
        "name": kwargs.get("name", "Vegetarian Recipe"),
        "ingredients": kwargs.get("ingredients", [
            Ingredient(name="Vegetables", unit=MeasureUnit.GRAM, quantity=300.0, position=0, product_id="veggies_123"),
            Ingredient(name="Olive Oil", unit=MeasureUnit.TABLESPOON, quantity=2.0, position=1, product_id="oil_456"),
        ]),
        "tags": kwargs.get("tags", {
            Tag(key="diet", value="vegetarian", author_id="author_1", type="recipe")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "ingredients", "tags"]}
    }
    return create_recipe(**final_kwargs)


def create_public_recipe(**kwargs) -> _Recipe:
    """
    Create a public recipe for access control testing.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity with public privacy
    """
    final_kwargs = {
        "name": kwargs.get("name", "Public Recipe"),
        "privacy": kwargs.get("privacy", Privacy.PUBLIC),
        "description": kwargs.get("description", "This is a public recipe available to all users"),
        **{k: v for k, v in kwargs.items() if k not in ["name", "privacy", "description"]}
    }
    return create_recipe(**final_kwargs)


def create_private_recipe(**kwargs) -> _Recipe:
    """
    Create a private recipe for access control testing.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity with private privacy
    """
    final_kwargs = {
        "name": kwargs.get("name", "Private Recipe"),
        "privacy": kwargs.get("privacy", Privacy.PRIVATE),
        "description": kwargs.get("description", "This is a private recipe only visible to the author"),
        **{k: v for k, v in kwargs.items() if k not in ["name", "privacy", "description"]}
    }
    return create_recipe(**final_kwargs)


# =============================================================================
# SPECIALIZED RECIPE FACTORIES (ORM)
# =============================================================================

def create_quick_recipe_orm(**kwargs) -> RecipeSaModel:
    """
    Create a quick-cooking recipe ORM instance (≤20 minutes).
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        RecipeSaModel ORM instance optimized for quick cooking
    """
    final_kwargs = {
        "name": kwargs.get("name", "Quick Recipe"),
        "total_time": kwargs.get("total_time", 15),
        "instructions": kwargs.get("instructions", "Quick and easy instructions. Heat, mix, serve."),
        "tags": kwargs.get("tags", [
            create_tag_orm(key="difficulty", value="easy", author_id="author_1", type="recipe"),
            create_tag_orm(key="cooking_method", value="raw", author_id="author_1", type="recipe")
        ]),
        **{k: v for k, v in kwargs.items() if k not in ["name", "total_time", "instructions", "tags"]}
    }
    return create_recipe_orm(**final_kwargs)


def create_high_protein_recipe_orm(**kwargs) -> RecipeSaModel:
    """
    Create a high-protein recipe ORM instance (≥25g protein).
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        RecipeSaModel ORM instance optimized for high protein content
    """
    final_kwargs = {
        "name": kwargs.get("name", "High Protein Recipe"),
        "protein_percentage": kwargs.get("protein_percentage", 35.0),  # High protein percentage for ORM
        "ingredients": kwargs.get("ingredients", [
            create_ingredient_orm(name="Chicken Breast", unit=MeasureUnit.GRAM.value, quantity=200.0, position=0, product_id="chicken_123"),
            create_ingredient_orm(name="Greek Yogurt", unit=MeasureUnit.GRAM.value, quantity=100.0, position=1, product_id="yogurt_456"),
        ]),
        "tags": kwargs.get("tags", [
            create_tag_orm(key="diet", value="high-protein", author_id="author_1", type="recipe")
        ]),
        **{k: v for k, v in kwargs.items() if k not in ["name", "protein_percentage", "ingredients", "tags"]}
    }
    return create_recipe_orm(**final_kwargs)


def create_vegetarian_recipe_orm(**kwargs) -> RecipeSaModel:
    """
    Create a vegetarian recipe ORM instance.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        RecipeSaModel ORM instance suitable for vegetarians
    """
    final_kwargs = {
        "name": kwargs.get("name", "Vegetarian Recipe"),
        "ingredients": kwargs.get("ingredients", [
            create_ingredient_orm(name="Vegetables", unit=MeasureUnit.GRAM.value, quantity=300.0, position=0, product_id="veggies_123"),
            create_ingredient_orm(name="Olive Oil", unit=MeasureUnit.TABLESPOON.value, quantity=2.0, position=1, product_id="oil_456"),
        ]),
        "tags": kwargs.get("tags", [
            create_tag_orm(key="diet", value="vegetarian", author_id="author_1", type="recipe")
        ]),
        **{k: v for k, v in kwargs.items() if k not in ["name", "ingredients", "tags"]}
    }
    return create_recipe_orm(**final_kwargs)


def create_public_recipe_orm(**kwargs) -> RecipeSaModel:
    """
    Create a public recipe ORM instance for access control testing.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        RecipeSaModel ORM instance with public privacy
    """
    final_kwargs = {
        "name": kwargs.get("name", "Public Recipe"),
        "privacy": kwargs.get("privacy", Privacy.PUBLIC.value),  # String value for ORM
        "description": kwargs.get("description", "This is a public recipe available to all users"),
        **{k: v for k, v in kwargs.items() if k not in ["name", "privacy", "description"]}
    }
    return create_recipe_orm(**final_kwargs)


def create_private_recipe_orm(**kwargs) -> RecipeSaModel:
    """
    Create a private recipe ORM instance for access control testing.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        RecipeSaModel ORM instance with private privacy
    """
    final_kwargs = {
        "name": kwargs.get("name", "Private Recipe"),
        "privacy": kwargs.get("privacy", Privacy.PRIVATE.value),  # String value for ORM
        "description": kwargs.get("description", "This is a private recipe only visible to the author"),
        **{k: v for k, v in kwargs.items() if k not in ["name", "privacy", "description"]}
    }
    return create_recipe_orm(**final_kwargs)


# =============================================================================
# DATASET CREATION UTILITIES (DOMAIN & ORM)
# =============================================================================

def create_recipes_with_ratings(count: int = 3, ratings_per_recipe: int = 2) -> List[_Recipe]:
    """
    Create a list of recipes with ratings for aggregation testing.
    
    Args:
        count: Number of recipes to create
        ratings_per_recipe: Number of ratings per recipe
        
    Returns:
        List of Recipe entities with ratings
    """
    recipes = []
    for i in range(count):
        ratings = []
        for j in range(ratings_per_recipe):
            rating = create_rating(
                recipe_id=f"recipe_{i+1:03d}",
                user_id=f"user_{j+1}",
                taste=(3 + j) % 6,  # Vary ratings
                convenience=(4 + j) % 6
            )
            ratings.append(rating)
        
        recipe = create_recipe(
            id=f"recipe_{i+1:03d}",
            name=f"Recipe with Ratings {i+1}",
            ratings=ratings
        )
        recipes.append(recipe)
    
    return recipes


def create_recipes_with_ratings_orm(count: int = 3, ratings_per_recipe: int = 2) -> List[RecipeSaModel]:
    """
    Create a list of recipe ORM instances with ratings for aggregation testing.
    
    Args:
        count: Number of recipes to create
        ratings_per_recipe: Number of ratings per recipe
        
    Returns:
        List of RecipeSaModel instances with ratings
    """
    recipes = []
    for i in range(count):
        ratings = []
        for j in range(ratings_per_recipe):
            rating = create_rating_orm(
                recipe_id=f"recipe_{i+1:03d}",
                user_id=f"user_{j+1}",
                taste=(3 + j) % 6,  # Vary ratings
                convenience=(4 + j) % 6
            )
            ratings.append(rating)
        
        recipe = create_recipe_orm(
            id=f"recipe_{i+1:03d}",
            name=f"Recipe with Ratings {i+1}",
            ratings=ratings
        )
        recipes.append(recipe)
    
    return recipes


def create_test_dataset(recipe_count: int = 100, tags_per_recipe: int = 0) -> Dict[str, Any]:
    """
    Create a comprehensive test dataset for performance and integration testing.
    
    Args:
        recipe_count: Number of recipes to create
        tags_per_recipe: Number of tags per recipe
        
    Returns:
        Dict containing recipes, ingredients, ratings, and metadata
    """
    reset_counters()
    
    recipes = []
    all_ingredients = []
    all_ratings = []
    all_tags = []
    
    for i in range(recipe_count):
        # Create varied recipes
        if i % 4 == 0:
            recipe = create_quick_recipe()
        elif i % 4 == 1:
            recipe = create_high_protein_recipe()
        elif i % 4 == 2:
            recipe = create_vegetarian_recipe()
        else:
            recipe = create_recipe()
        
        # Add tags if requested
        if tags_per_recipe > 0:
            tags = set()
            for j in range(tags_per_recipe):
                tag = create_tag(type="recipe")
                tags.add(tag)
                all_tags.append(tag)
            recipe._tags = tags
        
        # Add ratings (some recipes have ratings, some don't)
        if i % 3 != 0:  # 2/3 of recipes have ratings
            ratings = []
            num_ratings = (i % 3) + 1  # 1-3 ratings per recipe
            for j in range(num_ratings):
                rating = create_rating(recipe_id=recipe.id)
                ratings.append(rating)
                all_ratings.append(rating)
            recipe._ratings = ratings
        
        # Collect ingredients
        all_ingredients.extend(recipe.ingredients)
        recipes.append(recipe)
    
    return {
        "recipes": recipes,
        "ingredients": all_ingredients,
        "ratings": all_ratings,
        "tags": all_tags,
        "metadata": {
            "recipe_count": len(recipes),
            "ingredient_count": len(all_ingredients),
            "rating_count": len(all_ratings),
            "tag_count": len(all_tags),
            "tags_per_recipe": tags_per_recipe
        }
    }


def create_test_dataset_orm(recipe_count: int = 100, tags_per_recipe: int = 0) -> Dict[str, Any]:
    """
    Create a comprehensive test dataset with ORM instances for performance and integration testing.
    
    Args:
        recipe_count: Number of recipes to create
        tags_per_recipe: Number of tags per recipe
        
    Returns:
        Dict containing ORM recipes, ingredients, ratings, and metadata
    """
    reset_counters()
    
    recipes = []
    all_ingredients = []
    all_ratings = []
    all_tags = []
    
    for i in range(recipe_count):
        # Create varied recipes
        if i % 4 == 0:
            recipe = create_quick_recipe_orm()
        elif i % 4 == 1:
            recipe = create_high_protein_recipe_orm()
        elif i % 4 == 2:
            recipe = create_vegetarian_recipe_orm()
        else:
            recipe = create_recipe_orm()
        
        # Add tags if requested
        if tags_per_recipe > 0:
            tags = []
            for j in range(tags_per_recipe):
                tag = create_tag_orm(type="recipe")
                tags.append(tag)
                all_tags.append(tag)
            recipe.tags = tags
        
        # Add ratings (some recipes have ratings, some don't)
        if i % 3 != 0:  # 2/3 of recipes have ratings
            ratings = []
            num_ratings = (i % 3) + 1  # 1-3 ratings per recipe
            for j in range(num_ratings):
                rating = create_rating_orm(recipe_id=recipe.id)
                ratings.append(rating)
                all_ratings.append(rating)
            recipe.ratings = ratings
        
        # Collect ingredients
        all_ingredients.extend(recipe.ingredients if recipe.ingredients else [])
        recipes.append(recipe)
    
    return {
        "recipes": recipes,
        "ingredients": all_ingredients,
        "ratings": all_ratings,
        "tags": all_tags,
        "metadata": {
            "recipe_count": len(recipes),
            "ingredient_count": len(all_ingredients),
            "rating_count": len(all_ratings),
            "tag_count": len(all_tags),
            "tags_per_recipe": tags_per_recipe
        }
    } 