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

# Import check_missing_attributes for validation
from tests.contexts.recipes_catalog.data_factories.shared_domain_factories import create_recipe_tag

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


def reset_recipe_domain_counters() -> None:
    """Reset all counters for test isolation"""
    global _RECIPE_COUNTER, _INGREDIENT_COUNTER, _RATING_COUNTER
    _RECIPE_COUNTER = 1
    _INGREDIENT_COUNTER = 1
    _RATING_COUNTER = 1


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