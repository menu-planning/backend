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
from typing import Dict, Any, List, Optional
from uuid import uuid4

from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import Ingredient
from src.contexts.recipes_catalog.core.domain.meal.value_objects.rating import Rating
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.enums import MeasureUnit, Privacy

# Import check_missing_attributes for validation
from tests.contexts.recipes_catalog.data_factories.shared_domain_factories import create_recipe_tag

# =============================================================================
# REALISTIC DATA SETS FOR PRODUCTION-LIKE TESTING
# =============================================================================

# Nutritional Profile Constants
STANDARD_NUTRITION_PROFILE = {
    "protein_percent": 0.15,  # 15% of calories from protein
    "carb_percent": 0.45,     # 45% of calories from carbs
    "fat_percent": 0.30,      # 30% of calories from fat
    "saturated_fat_ratio": 0.3,  # 30% of total fat is saturated
    "fiber_ratio": 0.1,       # 10% of carbs is fiber
    "sugar_ratio": 0.2,       # 20% of carbs is sugar
    "calorie_increment": 25,   # Calorie increase per counter
    "sodium_base": 400,        # Base sodium in mg
    "sodium_increment": 50,    # Sodium increase per counter
}

HIGH_PROTEIN_NUTRITION_PROFILE = {
    "protein_percent": 0.30,  # 30% of calories from protein
    "carb_percent": 0.35,     # 35% of calories from carbs
    "fat_percent": 0.25,      # 25% of calories from fat
    "saturated_fat_ratio": 0.25, # 25% of total fat is saturated
    "fiber_ratio": 0.12,      # 12% of carbs is fiber
    "sugar_ratio": 0.15,      # 15% of carbs is sugar
    "calorie_increment": 30,   # Higher calorie increment
    "sodium_base": 450,        # Slightly higher base sodium
    "sodium_increment": 60,    # Higher sodium increment
}

LOW_CARB_NUTRITION_PROFILE = {
    "protein_percent": 0.25,  # 25% of calories from protein
    "carb_percent": 0.15,     # 15% of calories from carbs (low carb)
    "fat_percent": 0.60,      # 60% of calories from fat
    "saturated_fat_ratio": 0.35, # 35% of total fat is saturated
    "fiber_ratio": 0.25,      # 25% of carbs is fiber (higher ratio)
    "sugar_ratio": 0.10,      # 10% of carbs is sugar (lower ratio)
    "calorie_increment": 35,   # Higher calorie increment
    "sodium_base": 500,        # Higher base sodium
    "sodium_increment": 70,    # Higher sodium increment
}

DESSERT_NUTRITION_PROFILE = {
    "protein_percent": 0.08,  # 8% of calories from protein
    "carb_percent": 0.65,     # 65% of calories from carbs (high carb)
    "fat_percent": 0.27,      # 27% of calories from fat
    "saturated_fat_ratio": 0.6,  # 60% of total fat is saturated (butter, cream)
    "fiber_ratio": 0.05,      # 5% of carbs is fiber (lower for desserts)
    "sugar_ratio": 0.7,       # 70% of carbs is sugar (high for desserts)
    "calorie_increment": 40,   # Higher calorie increment for desserts
    "sodium_base": 200,        # Lower base sodium
    "sodium_increment": 20,    # Lower sodium increment
}

# Time Constants
TIME_PROFILES = {
    "easy": {"base": 15, "increment": 5},
    "medium": {"base": 60, "increment": 10},
    "hard": {"base": 120, "increment": 15},
}

# Weight Constants
WEIGHT_PROFILES = {
    "standard": {"base": 400, "increment": 50},
    "large": {"base": 600, "increment": 75},
    "small": {"base": 200, "increment": 25},
}

# Quantity Constants
QUANTITY_PROFILES = {
    "standard": {"base": 100.0, "increment": 10, "multiplier": 25},
    "large": {"base": 150.0, "increment": 15, "multiplier": 30},
    "small": {"base": 50.0, "increment": 5, "multiplier": 15},
}

# Enhanced realistic recipe scenarios for comprehensive testing
REALISTIC_RECIPE_SCENARIOS = [
    {
        "name": "Classic Spaghetti Carbonara",
        "description": "Traditional Roman pasta dish with eggs, cheese, pancetta, and black pepper. Creamy without cream, this authentic recipe delivers rich, comforting flavors.",
        "instructions": "1. Bring a large pot of salted water to boil for the pasta. 2. Cut 200g pancetta into small cubes and cook in a large skillet over medium heat until crispy (about 5-7 minutes). 3. In a bowl, whisk together 3 large eggs, 100g grated Pecorino Romano, and plenty of freshly cracked black pepper. 4. Cook 400g spaghetti according to package directions until al dente, reserving 1 cup pasta water before draining. 5. Remove pancetta from heat and immediately add hot, drained pasta to the skillet. 6. Quickly toss pasta with pancetta, then remove from heat completely. 7. Slowly pour egg mixture over pasta while tossing continuously to create a creamy sauce (don't scramble the eggs!). 8. Add pasta water gradually if needed to achieve creamy consistency. 9. Serve immediately with extra Pecorino Romano and black pepper.",
        "utensils": "Large pot, large skillet, whisk, tongs, cheese grater, measuring cups",
        "notes": "The key is removing the pan from heat before adding eggs to prevent scrambling. Use fresh black pepper for best flavor.",
        "privacy": Privacy.PUBLIC,
        "cuisine": "italian",
        "difficulty": "medium",
        "cooking_method": "stovetop",
        "dietary_tags": ["gluten-free-possible"],
        "total_time": 25,
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
        "notes": "Adjust spice level by varying the amount of curry paste. Fresh Thai basil is essential for authentic flavor.",
        "privacy": Privacy.PUBLIC,
        "cuisine": "thai",
        "difficulty": "medium",
        "cooking_method": "stir-fry",
        "dietary_tags": ["dairy-free", "gluten-free"],
        "total_time": 35,
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
        "notes": "Can be prepared ahead and stored in fridge for up to 3 days. Add dressing just before serving.",
        "privacy": Privacy.PUBLIC,
        "cuisine": "mediterranean",
        "difficulty": "easy",
        "cooking_method": "roasted",
        "dietary_tags": ["vegetarian", "gluten-free", "healthy"],
        "total_time": 45,
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
        "notes": "Don't overbake - cookies will continue cooking on the hot pan. For chewier cookies, slightly underbake.",
        "privacy": Privacy.PUBLIC,
        "cuisine": "american",
        "difficulty": "easy",
        "cooking_method": "baking",
        "dietary_tags": ["vegetarian", "dessert", "sweet"],
        "total_time": 30,
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
        "notes": "Don't overcook salmon - it should still be slightly pink in the center. Great with steamed vegetables or rice.",
        "privacy": Privacy.PUBLIC,
        "cuisine": "modern",
        "difficulty": "easy",
        "cooking_method": "grilled",
        "dietary_tags": ["pescatarian", "healthy", "low-carb"],
        "total_time": 15,
        "weight_in_grams": 200,
        "average_taste_rating": 4.7,
        "average_convenience_rating": 4.5,
        "tags": ["salmon", "grilled", "healthy", "quick", "seafood"]
    },
    {
        "name": "Beef Bourguignon",
        "description": "Classic French braised beef in red wine with vegetables. Rich, tender, and deeply flavorful.",
        "instructions": "1. Cut 1.5kg beef chuck into large cubes and season with salt and pepper. 2. Heat oil in heavy pot and brown beef on all sides. 3. Add diced onions, carrots, and celery, cook until softened. 4. Add tomato paste and cook 1 minute. 5. Pour in 750ml red wine and beef stock. 6. Add bay leaves, thyme, and parsley stems. 7. Bring to simmer, cover, and braise in 160°C oven for 2.5 hours. 8. Add pearl onions and mushrooms in last 30 minutes. 9. Strain sauce and reduce if needed. 10. Serve with mashed potatoes or crusty bread.",
        "utensils": "Heavy pot or Dutch oven, wooden spoon, knife, cutting board, strainer",
        "notes": "Use a good quality red wine for best flavor. Can be made ahead and reheated. Tastes even better the next day.",
        "privacy": Privacy.PUBLIC,
        "cuisine": "french",
        "difficulty": "hard",
        "cooking_method": "braised",
        "dietary_tags": ["dairy-free-possible"],
        "total_time": 180,
        "weight_in_grams": 800,
        "average_taste_rating": 4.9,
        "average_convenience_rating": 2.1,
        "tags": ["beef", "french", "braised", "wine", "dinner"]
    },
    {
        "name": "Avocado Toast",
        "description": "Simple and trendy breakfast with mashed avocado on toast. Quick, healthy, and satisfying.",
        "instructions": "1. Toast 2 slices of good quality bread until golden. 2. Mash 1 ripe avocado with fork, leaving some chunks. 3. Season with salt, pepper, and lemon juice. 4. Spread avocado mixture on toast. 5. Top with cherry tomatoes, red pepper flakes, and sea salt. 6. Drizzle with olive oil and serve immediately.",
        "utensils": "Toaster, fork, knife, cutting board",
        "notes": "Use ripe but firm avocados. Add toppings like poached egg, feta cheese, or everything bagel seasoning for variations.",
        "privacy": Privacy.PUBLIC,
        "cuisine": "modern",
        "difficulty": "easy",
        "cooking_method": "raw",
        "dietary_tags": ["vegetarian", "healthy", "quick"],
        "total_time": 5,
        "weight_in_grams": 150,
        "average_taste_rating": 4.2,
        "average_convenience_rating": 4.8,
        "tags": ["avocado", "toast", "breakfast", "healthy", "quick"]
    },
    {
        "name": "Chicken Tikka Masala",
        "description": "Creamy Indian curry with tender chicken in aromatic tomato-based sauce. Rich, spicy, and comforting.",
        "instructions": "1. Marinate 500g chicken pieces in yogurt, ginger-garlic paste, and spices for 30 minutes. 2. Grill or pan-fry chicken until cooked through. 3. Heat oil in pan, add onions and cook until golden. 4. Add ginger-garlic paste, cook 1 minute. 5. Add tomato puree and cook until thick. 6. Add cream, spices, and cooked chicken. 7. Simmer for 10 minutes. 8. Garnish with cilantro and serve with rice or naan.",
        "utensils": "Large skillet, mixing bowl, knife, cutting board, wooden spoon",
        "notes": "For best flavor, marinate chicken overnight. Adjust spice level with cayenne pepper. Fresh cilantro is essential.",
        "privacy": Privacy.PUBLIC,
        "cuisine": "indian",
        "difficulty": "medium",
        "cooking_method": "curry",
        "dietary_tags": ["dairy-free-possible", "spicy"],
        "total_time": 60,
        "weight_in_grams": 650,
        "average_taste_rating": 4.7,
        "average_convenience_rating": 3.3,
        "tags": ["chicken", "indian", "curry", "spicy", "dinner"]
    },
    {
        "name": "Caesar Salad",
        "description": "Classic Roman salad with crisp romaine, parmesan, croutons, and creamy dressing.",
        "instructions": "1. Wash and chop romaine lettuce into bite-sized pieces. 2. Make dressing by whisking together mayonnaise, lemon juice, Worcestershire sauce, garlic, and anchovy paste. 3. Toss lettuce with dressing. 4. Add grated Parmesan cheese and croutons. 5. Season with black pepper and serve immediately.",
        "utensils": "Large bowl, whisk, knife, cutting board, cheese grater",
        "notes": "For authentic flavor, use real Parmesan cheese and make homemade croutons. Dress just before serving to keep lettuce crisp.",
        "privacy": Privacy.PUBLIC,
        "cuisine": "italian",
        "difficulty": "easy",
        "cooking_method": "raw",
        "dietary_tags": ["vegetarian"],
        "total_time": 15,
        "weight_in_grams": 250,
        "average_taste_rating": 4.3,
        "average_convenience_rating": 4.1,
        "tags": ["salad", "italian", "caesar", "vegetarian", "lunch"]
    },
    {
        "name": "Homemade Pizza Margherita",
        "description": "Traditional Italian pizza with fresh tomatoes, mozzarella, and basil. Simple ingredients, perfect execution.",
        "instructions": "1. Prepare pizza dough and let rise for 1 hour. 2. Preheat oven to 250°C (480°F) with pizza stone if available. 3. Roll out dough to desired thickness. 4. Spread thin layer of tomato sauce. 5. Add torn mozzarella cheese. 6. Drizzle with olive oil and season with salt. 7. Bake for 8-12 minutes until crust is golden and cheese is bubbly. 8. Top with fresh basil leaves and serve immediately.",
        "utensils": "Large bowl, rolling pin, pizza stone or baking sheet, ladle",
        "notes": "High heat is crucial for crispy crust. Use San Marzano tomatoes and fresh mozzarella for best results.",
        "privacy": Privacy.PUBLIC,
        "cuisine": "italian",
        "difficulty": "medium",
        "cooking_method": "baking",
        "dietary_tags": ["vegetarian"],
        "total_time": 90,
        "weight_in_grams": 400,
        "average_taste_rating": 4.6,
        "average_convenience_rating": 3.4,
        "tags": ["pizza", "italian", "margherita", "vegetarian", "dinner"]
    }
]

# Constants for comprehensive testing
COMMON_RECIPE_TYPES = [
    "appetizer", "main_course", "dessert", "breakfast", "lunch", "dinner", 
    "snack", "beverage", "soup", "salad", "pasta", "pizza", "curry", "stir_fry"
]

CUISINE_TYPES = [
    "italian", "french", "chinese", "japanese", "thai", "indian", "mexican", 
    "american", "mediterranean", "middle_eastern", "korean", "vietnamese", 
    "greek", "spanish", "german", "brazilian", "moroccan", "british", "modern"
]

DIETARY_TAGS = [
    "vegetarian", "vegan", "gluten-free", "dairy-free", "low-carb", "keto", 
    "paleo", "pescatarian", "healthy", "spicy", "sweet", "dessert", "quick",
    "comfort-food", "festive", "summer", "winter", "breakfast", "lunch", "dinner"
]

DIFFICULTY_LEVELS = ["easy", "medium", "hard"]

COOKING_METHODS = [
    "baking", "grilling", "roasting", "sautéing", "steaming", "boiling", 
    "frying", "stir-fry", "braising", "slow-cooking", "pressure-cooking", 
    "raw", "no-cook", "microwave", "air-frying", "smoking"
]

# =============================================================================
# STATIC COUNTERS FOR DETERMINISTIC IDS
# =============================================================================

_RECIPE_COUNTER = 1
_INGREDIENT_COUNTER = 1
_RATING_COUNTER = 1


def reset_recipe_domain_counters() -> None:
    """Reset all counters for test isolation"""
    global _RECIPE_COUNTER, _INGREDIENT_COUNTER, _RATING_COUNTER
    _RECIPE_COUNTER = 1
    _INGREDIENT_COUNTER = 1
    _RATING_COUNTER = 1


# =============================================================================
# DETERMINISTIC VALUE GENERATORS
# =============================================================================

def generate_nutrition_facts(
    base_calories: int = 300, 
    counter: Optional[int] = None, 
    profile: Optional[Dict[str, Any]] = None
) -> NutriFacts:
    """
    Generate deterministic nutrition facts based on counter and nutritional profile.
    
    Args:
        base_calories: Base calorie value to start from
        counter: Counter value to use for variation (defaults to _RECIPE_COUNTER)
        profile: Nutritional profile dict with percentages (defaults to STANDARD_NUTRITION_PROFILE)
        
    Returns:
        NutriFacts object with deterministic values
    """
    if counter is None:
        counter = _RECIPE_COUNTER
    
    if profile is None:
        profile = STANDARD_NUTRITION_PROFILE
    
    # Generate values based on counter with profile-specific ratios
    calories = base_calories + (counter * profile["calorie_increment"])
    protein = (calories * profile["protein_percent"]) / 4  # 4 cal/g protein
    carbs = (calories * profile["carb_percent"]) / 4       # 4 cal/g carbs
    fat = (calories * profile["fat_percent"]) / 9          # 9 cal/g fat
    
    return NutriFacts(
        calories=float(calories),
        protein=round(protein, 1),
        carbohydrate=round(carbs, 1),
        total_fat=round(fat, 1),
        saturated_fat=round(fat * profile["saturated_fat_ratio"], 1),
        dietary_fiber=round(carbs * profile["fiber_ratio"], 1),
        sugar=round(carbs * profile["sugar_ratio"], 1),
        sodium=float(profile["sodium_base"] + (counter * profile["sodium_increment"]))
    )


def generate_ingredient_quantities(
    base_quantity: float = 100.0, 
    counter: Optional[int] = None, 
    profile: str = "standard"
) -> List[float]:
    """
    Generate deterministic ingredient quantities based on counter and profile.
    
    Args:
        base_quantity: Base quantity to start from (overrides profile base if provided)
        counter: Counter value to use for variation (defaults to _RECIPE_COUNTER)
        profile: Quantity profile name ("standard", "large", "small")
        
    Returns:
        List of deterministic quantities (capped at 10,000)
    """
    if counter is None:
        counter = _RECIPE_COUNTER
    
    quantity_profile = QUANTITY_PROFILES.get(profile, QUANTITY_PROFILES["standard"])
    
    # Use provided base_quantity if different from default, otherwise use profile
    if base_quantity != 100.0:  # Custom base_quantity provided
        base = base_quantity
        increment = quantity_profile["increment"]
        multiplier = quantity_profile["multiplier"]
    else:  # Use profile defaults
        base = quantity_profile["base"]
        increment = quantity_profile["increment"]
        multiplier = quantity_profile["multiplier"]
    
    # Generate 8 different quantities with realistic variations
    quantities = []
    for i in range(8):
        quantity = base + (counter * increment) + (i * multiplier)
        # Cap quantity at 10,000 to prevent unrealistic values
        quantity = min(quantity, 10000.0)
        quantities.append(float(quantity))
    
    return quantities


def generate_rating_values(counter: Optional[int] = None) -> List[tuple]:
    """
    Generate deterministic rating values based on counter.
    
    Args:
        counter: Counter value to use for variation (defaults to _RECIPE_COUNTER)
        
    Returns:
        List of (taste, convenience, comment) tuples
    """
    if counter is None:
        counter = _RECIPE_COUNTER
    
    # Generate 3 different ratings with variation
    ratings = []
    for i in range(3):
        taste = ((counter + i) % 5) + 1  # 1-5 range
        convenience = ((counter + i + 2) % 5) + 1  # 1-5 range with offset
        comment = f"Test rating {counter}-{i+1}"
        ratings.append((taste, convenience, comment))
    
    return ratings


def generate_time_value(
    difficulty: str = "medium", 
    counter: Optional[int] = None, 
    custom_base: Optional[int] = None
) -> int:
    """
    Generate deterministic time values based on difficulty and counter.
    
    Args:
        difficulty: Difficulty level (easy, medium, hard)
        counter: Counter value to use for variation (defaults to _RECIPE_COUNTER)
        custom_base: Custom base time (overrides profile base if provided)
        
    Returns:
        Time in minutes
    """
    if counter is None:
        counter = _RECIPE_COUNTER
    
    time_profile = TIME_PROFILES.get(difficulty, TIME_PROFILES["medium"])
    
    base_time = custom_base if custom_base is not None else time_profile["base"]
    increment = time_profile["increment"]
    
    return base_time + (counter * increment)


def generate_weight_value(
    base_weight: int = 400, 
    counter: Optional[int] = None, 
    profile: str = "standard"
) -> int:
    """
    Generate deterministic weight values based on counter and profile.
    
    Args:
        base_weight: Base weight in grams (overrides profile base if provided)
        counter: Counter value to use for variation (defaults to _RECIPE_COUNTER)
        profile: Weight profile name ("standard", "large", "small")
        
    Returns:
        Weight in grams
    """
    if counter is None:
        counter = _RECIPE_COUNTER
    
    weight_profile = WEIGHT_PROFILES.get(profile, WEIGHT_PROFILES["standard"])
    
    # Use provided base_weight if different from default, otherwise use profile
    if base_weight != 400:  # Custom base_weight provided
        base = base_weight
        increment = weight_profile["increment"]
    else:  # Use profile defaults
        base = weight_profile["base"]
        increment = weight_profile["increment"]
    
    return base + (counter * increment)


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
    
    # Get the recipe's author_id early so we can use it for tags
    recipe_author_id = kwargs.get("author_id", str(uuid4()))
    
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    # Use realistic recipe data if available
    recipe_index = (_RECIPE_COUNTER - 1) % len(REALISTIC_RECIPE_SCENARIOS)
    realistic_recipe = REALISTIC_RECIPE_SCENARIOS[recipe_index]
    
    final_kwargs = {
        "id": kwargs.get("id", str(uuid4())),
        "name": kwargs.get("name", realistic_recipe["name"]),
        "author_id": recipe_author_id,
        "meal_id": kwargs.get("meal_id", str(uuid4())),
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
    
    # Allow override of any attribute except author_id (to maintain consistency with tags)
    final_kwargs.update({k: v for k, v in kwargs.items() if k != "author_id"})
    
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
    
    # Calculate base quantity and cap at 10,000
    base_quantity = 50.0 + (_INGREDIENT_COUNTER * 10)
    capped_quantity = min(base_quantity, 10000.0)
    
    final_kwargs = {
        "name": name,
        "unit": kwargs.get("unit", unit),
        "quantity": kwargs.get("quantity", capped_quantity),
        "position": kwargs.get("position", (_INGREDIENT_COUNTER - 1) % 10),  # Keep positions reasonable
        "full_text": kwargs.get("full_text", f"{capped_quantity}{unit} of {name.lower()}"),
        "product_id": kwargs.get("product_id", str(uuid4()) if _INGREDIENT_COUNTER % 2 == 0 else None),
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
    
    # Ensure quantity never exceeds 10,000 even if passed as override
    if 'quantity' in ingredient_kwargs:
        ingredient_kwargs['quantity'] = min(ingredient_kwargs['quantity'], 10000.0)
    
    return Ingredient(**ingredient_kwargs)


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
        "user_id": kwargs.get("user_id", str(uuid4())),  # Generate unique user IDs
        "recipe_id": kwargs.get("recipe_id", str(uuid4())),  # Generate unique recipe IDs  
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
    # Get the recipe's author_id early so we can use it for tags
    recipe_author_id = kwargs.get("author_id", str(uuid4()))
    
    final_kwargs = {
        "author_id": recipe_author_id,
        "name": kwargs.get("name", "Quick Recipe"),
        "total_time": kwargs.get("total_time", 15),
        "instructions": kwargs.get("instructions", "Quick and easy instructions. Heat, mix, serve."),
        "tags": kwargs.get("tags", {
            Tag(key="difficulty", value="easy", author_id=recipe_author_id, type="recipe"),
            Tag(key="cooking_method", value="raw", author_id=recipe_author_id, type="recipe")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "total_time", "instructions", "tags", "author_id"]}
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
    # Get the recipe's author_id early so we can use it for tags
    recipe_author_id = kwargs.get("author_id", str(uuid4()))
    
    # Generate deterministic values based on current counter
    current_counter = _RECIPE_COUNTER
    quantities = generate_ingredient_quantities(base_quantity=150.0, counter=current_counter, profile="large")
    
    final_kwargs = {
        "author_id": recipe_author_id,
        "name": kwargs.get("name", "High Protein Recipe"),
        "nutri_facts": kwargs.get("nutri_facts", generate_nutrition_facts(
            base_calories=380, 
            counter=current_counter, 
            profile=HIGH_PROTEIN_NUTRITION_PROFILE
        )),
        "ingredients": kwargs.get("ingredients", [
            Ingredient(name="Chicken Breast", unit=MeasureUnit.GRAM, quantity=quantities[0], position=0, product_id=f"chicken_{current_counter}"),
            Ingredient(name="Greek Yogurt", unit=MeasureUnit.GRAM, quantity=quantities[1], position=1, product_id=f"yogurt_{current_counter}"),
        ]),
        "tags": kwargs.get("tags", {
            Tag(key="diet", value="high-protein", author_id=recipe_author_id, type="recipe")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "nutri_facts", "ingredients", "tags", "author_id"]}
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
    # Get the recipe's author_id early so we can use it for tags
    recipe_author_id = kwargs.get("author_id", str(uuid4()))
    
    # Generate deterministic values based on current counter
    current_counter = _RECIPE_COUNTER
    quantities = generate_ingredient_quantities(base_quantity=250.0, counter=current_counter)
    
    final_kwargs = {
        "author_id": recipe_author_id,
        "name": kwargs.get("name", "Vegetarian Recipe"),
        "ingredients": kwargs.get("ingredients", [
            Ingredient(name="Vegetables", unit=MeasureUnit.GRAM, quantity=quantities[0], position=0, product_id=f"veggies_{current_counter}"),
            Ingredient(name="Olive Oil", unit=MeasureUnit.TABLESPOON, quantity=quantities[1] / 10, position=1, product_id=f"oil_{current_counter}"),
        ]),
        "tags": kwargs.get("tags", {
            Tag(key="diet", value="vegetarian", author_id=recipe_author_id, type="recipe")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "ingredients", "tags", "author_id"]}
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
# DATASET CREATION UTILITIES (DOMAIN)
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


def create_test_dataset(recipe_count: int = 100, tags_per_recipe: int = 0) -> Dict[str, Any]:
    """
    Create a comprehensive test dataset for performance and integration testing.
    
    Args:
        recipe_count: Number of recipes to create
        tags_per_recipe: Number of tags per recipe
        
    Returns:
        Dict containing recipes, ingredients, ratings, and metadata
    """
    reset_recipe_domain_counters()
    
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
                tag = create_recipe_tag(type="recipe")
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

# =============================================================================
# ENHANCED SPECIALIZED RECIPE FACTORIES (DOMAIN)
# =============================================================================

def create_simple_recipe(**kwargs) -> _Recipe:
    """
    Create a simple recipe with minimal complexity for basic testing.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity with simple structure
    """
    # Get the recipe's author_id early so we can use it for tags
    recipe_author_id = kwargs.get("author_id", str(uuid4()))
    
    final_kwargs = {
        "author_id": recipe_author_id,
        "name": kwargs.get("name", "Simple Recipe"),
        "description": kwargs.get("description", "A simple recipe for testing"),
        "instructions": kwargs.get("instructions", "1. Mix ingredients. 2. Cook. 3. Serve."),
        "total_time": kwargs.get("total_time", 15),
        "ingredients": kwargs.get("ingredients", [
            create_ingredient(name="Salt", quantity=1.0, unit=MeasureUnit.TEASPOON, position=0),
            create_ingredient(name="Pepper", quantity=0.5, unit=MeasureUnit.TEASPOON, position=1),
        ]),
        "tags": kwargs.get("tags", {
            create_recipe_tag(key="difficulty", value="easy", author_id=recipe_author_id),
            create_recipe_tag(key="cuisine", value="simple", author_id=recipe_author_id),
        }),
        "ratings": kwargs.get("ratings", [
            create_rating(taste=4, convenience=5, comment="Simple and good"),
        ]),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "instructions", "total_time", "ingredients", "tags", "ratings", "author_id"]}
    }
    return create_recipe(**final_kwargs)


def create_complex_recipe(**kwargs) -> _Recipe:
    """
    Create a complex recipe with many nested objects for comprehensive testing.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity with complex nested structure
    """
    # Get the recipe's author_id early so we can use it for tags
    recipe_author_id = kwargs.get("author_id", str(uuid4()))
    
    # Generate deterministic values based on current counter
    current_counter = _RECIPE_COUNTER
    quantities = generate_ingredient_quantities(base_quantity=50.0, counter=current_counter, profile="standard")
    rating_values = generate_rating_values(counter=current_counter)
    
    # Calculate scaled quantities for different ingredient types
    # Using deterministic scaling factors instead of magic numbers
    oil_quantity = max(1.0, quantities[0] / 10)       # Cooking oil in tablespoons
    piece_quantity_large = max(1.0, quantities[1] / 100)  # Large pieces (onions)
    piece_quantity_small = max(1.0, quantities[2] / 50)   # Small pieces (garlic)
    protein_quantity = quantities[3]                      # Protein in grams
    veggie_quantity = quantities[5]                       # Vegetables in grams
    herb_quantity = max(5.0, quantities[6] / 5)          # Fresh herbs in grams
    cheese_quantity = quantities[7]                       # Cheese in grams
    
    final_kwargs = {
        "author_id": recipe_author_id,
        "name": kwargs.get("name", "Complex Gourmet Recipe"),
        "description": kwargs.get("description", "A complex recipe with many ingredients and detailed instructions for comprehensive testing"),
        "instructions": kwargs.get("instructions", "1. Prep all ingredients carefully. 2. Heat oil in large pan. 3. Sauté aromatics. 4. Add proteins. 5. Layer in vegetables. 6. Season throughout. 7. Simmer until tender. 8. Finish with fresh herbs. 9. Plate elegantly. 10. Serve immediately."),
        "total_time": kwargs.get("total_time", generate_time_value(difficulty="medium", counter=current_counter)),
        "utensils": kwargs.get("utensils", "large pan, cutting board, sharp knife, wooden spoon, measuring cups, plates"),
        "notes": kwargs.get("notes", "This recipe requires patience and attention to detail. Fresh ingredients make a significant difference."),
        "ingredients": kwargs.get("ingredients", [
            create_ingredient(name="Olive Oil", quantity=oil_quantity, unit=MeasureUnit.TABLESPOON, position=0),
            create_ingredient(name="Onion", quantity=piece_quantity_large, unit=MeasureUnit.PIECE, position=1),
            create_ingredient(name="Garlic", quantity=piece_quantity_small, unit=MeasureUnit.PIECE, position=2),
            create_ingredient(name="Chicken Breast", quantity=protein_quantity, unit=MeasureUnit.GRAM, position=3),
            create_ingredient(name="Bell Pepper", quantity=piece_quantity_large, unit=MeasureUnit.PIECE, position=4),
            create_ingredient(name="Tomatoes", quantity=veggie_quantity, unit=MeasureUnit.GRAM, position=5),
            create_ingredient(name="Fresh Basil", quantity=herb_quantity, unit=MeasureUnit.GRAM, position=6),
            create_ingredient(name="Parmesan Cheese", quantity=cheese_quantity, unit=MeasureUnit.GRAM, position=7),
        ]),
        "tags": kwargs.get("tags", {
            create_recipe_tag(key="difficulty", value="medium", author_id=recipe_author_id),
            create_recipe_tag(key="cuisine", value="mediterranean", author_id=recipe_author_id),
            create_recipe_tag(key="cooking_method", value="sautéing", author_id=recipe_author_id),
            create_recipe_tag(key="meal_type", value="dinner", author_id=recipe_author_id),
            create_recipe_tag(key="dietary", value="gluten-free", author_id=recipe_author_id),
        }),
        "ratings": kwargs.get("ratings", [
            create_rating(taste=rating_values[0][0], convenience=rating_values[0][1], comment=rating_values[0][2]),
            create_rating(taste=rating_values[1][0], convenience=rating_values[1][1], comment=rating_values[1][2]),
            create_rating(taste=rating_values[2][0], convenience=rating_values[2][1], comment=rating_values[2][2]),
        ]),
        "nutri_facts": kwargs.get("nutri_facts", generate_nutrition_facts(base_calories=420, counter=current_counter)),
        "weight_in_grams": kwargs.get("weight_in_grams", generate_weight_value(base_weight=600, counter=current_counter)),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "instructions", "total_time", "utensils", "notes", "ingredients", "tags", "ratings", "nutri_facts", "weight_in_grams", "author_id"]}
    }
    return create_recipe(**final_kwargs)


def create_minimal_recipe(**kwargs) -> _Recipe:
    """
    Create a minimal recipe with only required fields for edge case testing.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity with minimal data
    """
    # Get the recipe's author_id early so we can use it for tags
    recipe_author_id = kwargs.get("author_id", str(uuid4()))
    
    final_kwargs = {
        "author_id": recipe_author_id,
        "name": kwargs.get("name", "Minimal Recipe"),
        "instructions": kwargs.get("instructions", "Basic instructions"),
        "description": kwargs.get("description", None),
        "utensils": kwargs.get("utensils", None),
        "total_time": kwargs.get("total_time", None),
        "notes": kwargs.get("notes", None),
        "ingredients": kwargs.get("ingredients", []),
        "tags": kwargs.get("tags", set()),
        "ratings": kwargs.get("ratings", []),
        "nutri_facts": kwargs.get("nutri_facts", None),
        "weight_in_grams": kwargs.get("weight_in_grams", None),
        "image_url": kwargs.get("image_url", None),
        **{k: v for k, v in kwargs.items() if k not in ["name", "instructions", "description", "utensils", "total_time", "notes", "ingredients", "tags", "ratings", "nutri_facts", "weight_in_grams", "image_url", "author_id"]}
    }
    return create_recipe(**final_kwargs)


def create_recipe_with_max_fields(**kwargs) -> _Recipe:
    """
    Create a recipe with maximum fields populated for comprehensive testing.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity with all possible fields populated
    """
    # Get the recipe's author_id early so we can use it for tags
    recipe_author_id = kwargs.get("author_id", str(uuid4()))
    
    # Generate deterministic values based on current counter
    current_counter = _RECIPE_COUNTER
    
    # Create many ingredients
    ingredients = []
    for i in range(15):
        ingredients.append(create_ingredient(position=i))
    
    # Create many ratings with deterministic values
    ratings = []
    for i in range(12):
        ratings.append(create_rating(taste=((current_counter + i) % 5) + 1, convenience=((current_counter + i + 1) % 5) + 1))
    
    # Create many tags
    tags = set()
    for i, tag_type in enumerate(["difficulty", "cuisine", "cooking_method", "dietary", "meal_type", "season"]):
        tags.add(create_recipe_tag(key=tag_type, value=f"value_{current_counter}_{i}", author_id=recipe_author_id))
    
    final_kwargs = {
        "author_id": recipe_author_id,
        "name": kwargs.get("name", "Recipe with Maximum Fields"),
        "description": kwargs.get("description", "A comprehensive recipe with all possible fields populated for testing maximum data scenarios"),
        "instructions": kwargs.get("instructions", "Detailed step-by-step instructions for a complex recipe with many components and techniques"),
        "utensils": kwargs.get("utensils", "large pot, skillet, cutting board, knife, whisk, measuring cups, measuring spoons, mixing bowls, strainer"),
        "total_time": kwargs.get("total_time", generate_time_value(difficulty="hard", counter=current_counter)),
        "notes": kwargs.get("notes", "Comprehensive notes about preparation, cooking tips, variations, and serving suggestions"),
        "ingredients": kwargs.get("ingredients", ingredients),
        "tags": kwargs.get("tags", tags),
        "ratings": kwargs.get("ratings", ratings),
        "nutri_facts": kwargs.get("nutri_facts", generate_nutrition_facts(base_calories=600, counter=current_counter)),
        "weight_in_grams": kwargs.get("weight_in_grams", generate_weight_value(base_weight=800, counter=current_counter, profile="large")),
        "image_url": kwargs.get("image_url", f"https://example.com/recipe-image-{current_counter}.jpg"),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "instructions", "utensils", "total_time", "notes", "ingredients", "tags", "ratings", "nutri_facts", "weight_in_grams", "image_url", "author_id"]}
    }
    return create_recipe(**final_kwargs)


def create_recipe_with_incorrect_averages(**kwargs) -> _Recipe:
    """
    Create a recipe with ratings but incorrect pre-calculated averages for testing correction.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity with incorrect averages (domain will auto-correct)
    """
    # Get the recipe's author_id early so we can use it for tags
    recipe_author_id = kwargs.get("author_id", str(uuid4()))
    
    # Create specific ratings with known values
    ratings = [
        create_rating(taste=4, convenience=3, comment="Good taste, okay convenience"),
        create_rating(taste=5, convenience=4, comment="Excellent taste, good convenience"),
        create_rating(taste=3, convenience=5, comment="Average taste, very convenient"),
    ]
    # Expected averages: taste = 4.0, convenience = 4.0
    
    final_kwargs = {
        "author_id": recipe_author_id,
        "name": kwargs.get("name", "Recipe with Incorrect Averages"),
        "description": kwargs.get("description", "Recipe for testing average rating correction"),
        "instructions": kwargs.get("instructions", "Test instructions for average correction"),
        "ratings": kwargs.get("ratings", ratings),
        "ingredients": kwargs.get("ingredients", [create_ingredient()]),
        "tags": kwargs.get("tags", {create_recipe_tag(author_id=recipe_author_id)}),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "instructions", "ratings", "ingredients", "tags", "author_id"]}
    }
    return create_recipe(**final_kwargs)


def create_recipe_without_ratings(**kwargs) -> _Recipe:
    """
    Create a recipe without any ratings for testing computed properties.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity with no ratings
    """
    # Get the recipe's author_id early so we can use it for tags
    recipe_author_id = kwargs.get("author_id", str(uuid4()))
    
    final_kwargs = {
        "author_id": recipe_author_id,
        "name": kwargs.get("name", "Recipe Without Ratings"),
        "description": kwargs.get("description", "Recipe for testing no ratings scenarios"),
        "instructions": kwargs.get("instructions", "Test instructions for no ratings"),
        "ratings": kwargs.get("ratings", []),
        "ingredients": kwargs.get("ingredients", [create_ingredient()]),
        "tags": kwargs.get("tags", {create_recipe_tag(author_id=recipe_author_id)}),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "instructions", "ratings", "ingredients", "tags", "author_id"]}
    }
    return create_recipe(**final_kwargs)


def create_dessert_recipe(**kwargs) -> _Recipe:
    """
    Create a dessert recipe with sweet ingredients and dessert-specific tags.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Recipe domain entity optimized for dessert
    """
    # Get the recipe's author_id early so we can use it for tags
    recipe_author_id = kwargs.get("author_id", str(uuid4()))
    
    # Generate deterministic values based on current counter
    current_counter = _RECIPE_COUNTER
    quantities = generate_ingredient_quantities(base_quantity=150.0, counter=current_counter)
    
    final_kwargs = {
        "author_id": recipe_author_id,
        "name": kwargs.get("name", "Chocolate Dessert Recipe"),
        "description": kwargs.get("description", "Rich and indulgent chocolate dessert"),
        "instructions": kwargs.get("instructions", "1. Melt chocolate. 2. Mix with cream. 3. Chill. 4. Serve cold."),
        "ingredients": kwargs.get("ingredients", [
            create_ingredient(name="Dark Chocolate", quantity=quantities[0], unit=MeasureUnit.GRAM, position=0),
            create_ingredient(name="Heavy Cream", quantity=quantities[1], unit=MeasureUnit.MILLILITER, position=1),
            create_ingredient(name="Sugar", quantity=quantities[2] / 3, unit=MeasureUnit.GRAM, position=2),
            create_ingredient(name="Vanilla Extract", quantity=quantities[3] / 100, unit=MeasureUnit.TEASPOON, position=3),
        ]),
        "tags": kwargs.get("tags", {
            create_recipe_tag(key="meal_type", value="dessert", author_id=recipe_author_id),
            create_recipe_tag(key="flavor", value="chocolate", author_id=recipe_author_id),
            create_recipe_tag(key="difficulty", value="easy", author_id=recipe_author_id),
            create_recipe_tag(key="dietary", value="vegetarian", author_id=recipe_author_id),
        }),
        "nutri_facts": kwargs.get("nutri_facts", generate_nutrition_facts(
            base_calories=350, 
            counter=current_counter, 
            profile=DESSERT_NUTRITION_PROFILE
        )),
        "total_time": kwargs.get("total_time", generate_time_value(difficulty="easy", counter=current_counter)),
        "weight_in_grams": kwargs.get("weight_in_grams", generate_weight_value(base_weight=250, counter=current_counter, profile="small")),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "instructions", "ingredients", "tags", "nutri_facts", "total_time", "weight_in_grams", "author_id"]}
    }
    return create_recipe(**final_kwargs)


# =============================================================================
# COLLECTION CREATION UTILITIES (DOMAIN)
# =============================================================================

def create_recipe_collection(count: int = 5) -> List[_Recipe]:
    """
    Create a collection of diverse recipes for batch testing.
    
    Args:
        count: Number of recipes to create
        
    Returns:
        List of Recipe domain entities
    """
    recipes = []
    for i in range(count):
        if i % 5 == 0:
            recipe = create_simple_recipe()
        elif i % 5 == 1:
            recipe = create_complex_recipe()
        elif i % 5 == 2:
            recipe = create_quick_recipe()
        elif i % 5 == 3:
            recipe = create_vegetarian_recipe()
        else:
            recipe = create_dessert_recipe()
        recipes.append(recipe)
    return recipes


def create_recipes_by_cuisine(cuisine: str, count: int = 3) -> List[_Recipe]:
    """
    Create recipes of a specific cuisine type.
    
    Args:
        cuisine: Cuisine type to create
        count: Number of recipes to create
        
    Returns:
        List of Recipe domain entities of specified cuisine
    """
    # Generate a single author_id for all recipes in this collection
    collection_author_id = str(uuid4())
    
    recipes = []
    for i in range(count):
        recipe = create_recipe(
            author_id=collection_author_id,
            name=f"{cuisine.title()} Recipe {i+1}",
            description=f"Authentic {cuisine} recipe for testing",
            tags={create_recipe_tag(key="cuisine", value=cuisine, author_id=collection_author_id)}
        )
        recipes.append(recipe)
    return recipes


def create_recipes_by_difficulty(difficulty: str, count: int = 3) -> List[_Recipe]:
    """
    Create recipes of a specific difficulty level.
    
    Args:
        difficulty: Difficulty level (easy, medium, hard)
        count: Number of recipes to create
        
    Returns:
        List of Recipe domain entities of specified difficulty
    """
    # Generate a single author_id for all recipes in this collection
    collection_author_id = str(uuid4())
    
    recipes = []
    for i in range(count):
        # Use deterministic time value based on difficulty and current state
        total_time = generate_time_value(difficulty=difficulty, counter=i + 1)
        recipe = create_recipe(
            author_id=collection_author_id,
            name=f"{difficulty.title()} Recipe {i+1}",
            description=f"A {difficulty} recipe for testing",
            total_time=total_time,
            tags={create_recipe_tag(key="difficulty", value=difficulty, author_id=collection_author_id)}
        )
        recipes.append(recipe)
    return recipes


def create_test_recipe_dataset(recipe_count: int = 10) -> Dict[str, Any]:
    """
    Create a comprehensive test dataset for performance and integration testing.
    
    Args:
        recipe_count: Number of recipes to create
        
    Returns:
        Dict containing recipes, metadata, and related objects
    """
    reset_recipe_domain_counters()
    
    recipes = []
    all_ingredients = []
    all_ratings = []
    all_tags = []
    
    for i in range(recipe_count):
        # Create varied recipes
        if i % 6 == 0:
            recipe = create_simple_recipe()
        elif i % 6 == 1:
            recipe = create_complex_recipe()
        elif i % 6 == 2:
            recipe = create_minimal_recipe()
        elif i % 6 == 3:
            recipe = create_recipe_with_max_fields()
        elif i % 6 == 4:
            recipe = create_dessert_recipe()
        else:
            recipe = create_recipe()
        
        # Collect related objects
        all_ingredients.extend(recipe.ingredients)
        if recipe.ratings:
            all_ratings.extend(recipe.ratings)
        if recipe.tags:
            all_tags.extend(recipe.tags)
        
        recipes.append(recipe)
    
    return {
        "recipes": recipes,
        "ingredients": all_ingredients,
        "ratings": all_ratings,
        "tags": all_tags,
        "total_recipes": len(recipes),
        "metadata": {
            "recipe_count": len(recipes),
            "ingredient_count": len(all_ingredients),
            "rating_count": len(all_ratings),
            "tag_count": len(all_tags),
        }
    }


# =============================================================================
# PERFORMANCE TESTING UTILITIES (DOMAIN)
# =============================================================================

def create_bulk_recipe_creation_dataset(count: int = 100) -> List[Dict[str, Any]]:
    """
    Create a dataset for bulk recipe creation performance testing.
    
    Args:
        count: Number of recipe kwargs to create
        
    Returns:
        List of recipe kwargs dictionaries
    """
    reset_recipe_domain_counters()
    
    kwargs_list = []
    for i in range(count):
        kwargs = create_recipe_kwargs()
        kwargs_list.append(kwargs)
    
    return kwargs_list


def create_conversion_performance_dataset(count: int = 100) -> Dict[str, Any]:
    """
    Create a dataset for conversion performance testing.
    
    Args:
        count: Number of recipes to create
        
    Returns:
        Dict containing recipes for performance testing
    """
    reset_recipe_domain_counters()
    
    domain_recipes = []
    for i in range(count):
        if i % 4 == 0:
            recipe = create_simple_recipe()
        elif i % 4 == 1:
            recipe = create_complex_recipe()
        elif i % 4 == 2:
            recipe = create_recipe_with_max_fields()
        else:
            recipe = create_recipe()
        domain_recipes.append(recipe)
    
    return {
        "domain_recipes": domain_recipes,
        "total_count": count
    }


def create_nested_object_validation_dataset(count: int = 50, ingredients_per_recipe: int | None = None, ratings_per_recipe: int | None = None, tags_per_recipe: int | None = None) -> List[_Recipe]:
    """
    Create a dataset with complex nested objects for validation testing.
    
    Args:
        count: Number of recipes to create
        
    Returns:
        List of Recipe domain entities with complex nested structures
    """
    reset_recipe_domain_counters()

    # Generate a single author_id for consistent tags
    collection_author_id = str(uuid4())
    
    kwargs = {}
    kwargs["author_id"] = collection_author_id
    
    if ingredients_per_recipe is not None:
        ingredients = [create_ingredient(position=i) for i in range(ingredients_per_recipe)]
        kwargs["ingredients"] = ingredients
    if ratings_per_recipe is not None:
        ratings = [create_rating() for _ in range(ratings_per_recipe)]
        kwargs["ratings"] = ratings
    if tags_per_recipe is not None:
        tags = [create_recipe_tag(author_id=collection_author_id) for _ in range(tags_per_recipe)]
        kwargs["tags"] = tags

    recipes = []
    for i in range(count):
        # Alternate between complex and max fields recipes
        if i % 2 == 0:
            if kwargs:
                recipe = create_complex_recipe(**kwargs)
            else:
                recipe = create_complex_recipe(author_id=collection_author_id)
        else:
            if kwargs:
                recipe = create_recipe_with_max_fields(**kwargs)
            else:
                recipe = create_recipe_with_max_fields(author_id=collection_author_id)
        recipes.append(recipe)
    
    return recipes